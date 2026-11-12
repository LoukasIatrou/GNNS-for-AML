"""Evaluate model predictions against the team's chronological Elliptic split.

Public notebook API:
    prepare_test_manifest(split_table) -> known-label test transactions
    evaluate_predictions(truth, predictions, ...) -> summary, periods, transactions

Command line, from the repository root:
    python -m src.role4_evaluation --split-file tests/elliptic_split.csv \
        --predictions predictions.csv --model RandomForest --seed 0 \
        --threshold 0.50 --outdir outputs/role4/random_forest_seed0

Read docs/ROLE4_EVALUATION.md for input formats and metric conventions.
"""

from __future__ import annotations

import argparse
from contextlib import suppress
import csv
from datetime import datetime, timezone
import hashlib
import json
from numbers import Integral, Real
import os
from pathlib import Path
import platform
import tempfile
import warnings

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import average_precision_score


TEST_PERIODS = range(35, 50)
MANIFEST_COLUMNS = ("transaction_id", "time_step", "y_true")
PREDICTION_COLUMNS = ("transaction_id", "score_illicit")
LABEL_MAP = {"illicit": 1, "licit": 0, "1": 1, "2": 0}
# The integer code 2 * known_class + predicted_class indexes these outcomes.
OUTCOMES = np.array(["TN", "FP", "FN", "TP"])
EXPORT_NAMES = (
    "overall_metrics.csv",
    "metrics_per_time_step.csv",
    "evaluated_predictions.csv",
    "run_metadata.json",
)


def _required_table(
    frame: pd.DataFrame, columns: tuple[str, ...], name: str
) -> pd.DataFrame:
    """Select required columns, normalise the ID name and validate identifiers."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame.")
    if not frame.columns.is_unique:
        raise ValueError(f"{name} contains duplicate column names.")
    if "txId" in frame.columns and "transaction_id" in frame.columns:
        raise ValueError(f"{name} must use either txId or transaction_id, not both.")

    id_column = "txId" if "txId" in frame.columns else "transaction_id"
    source_columns = [id_column if col == "transaction_id" else col for col in columns]
    missing = set(source_columns) - set(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")
    # Copy only the relevant columns; never modify the caller's table.
    table = frame.loc[:, source_columns].copy()
    table.columns = list(columns)
    if table.isna().any().any():
        raise ValueError(f"{name} contains missing required values.")

    ids = table["transaction_id"]
    kind = pd.api.types.infer_dtype(ids)
    if kind not in {"string", "unicode", "integer", "empty"}:
        valid_types = ids.map(
            lambda value: isinstance(value, (str, Integral))
            and not isinstance(value, (bool, np.bool_))
        )
        if not valid_types.all():
            raise ValueError(f"{name} IDs must be text or integers, never floats.")
    ids = ids.astype(str)
    if ids.str.strip().eq("").any():
        raise ValueError(f"{name} transaction IDs must not be empty.")
    if not ids.eq(ids.str.strip()).all():
        raise ValueError(f"{name} transaction IDs contain surrounding whitespace.")
    if ids.duplicated().any():
        raise ValueError(f"{name} transaction IDs must be unique.")
    table["transaction_id"] = ids
    return table


def _numeric_column(values: pd.Series, name: str) -> pd.Series:
    """Reject boolean, complex, missing and nonfinite numeric inputs explicitly."""
    inferred = pd.api.types.infer_dtype(values)
    contains_boolean = pd.api.types.is_bool_dtype(values.dtype)
    if inferred in {"mixed", "mixed-integer"}:
        contains_boolean = values.map(lambda value: isinstance(value, (bool, np.bool_))).any()
    if contains_boolean:
        raise ValueError(f"{name} must contain numbers, not boolean values.")
    try:
        numeric = pd.to_numeric(values, errors="raise")
    except (ValueError, TypeError) as error:
        raise ValueError(f"{name} must contain valid numbers.") from error
    if np.iscomplexobj(numeric.to_numpy()):
        raise ValueError(f"{name} must contain real numbers, not complex values.")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError(f"{name} must contain finite numbers with no missing values.")
    return numeric


def _run_settings(
    threshold: float, model_name: str, seed: int | None
) -> tuple[float, str, int | None]:
    """Normalise scalar settings before calculating or saving any results."""
    if (
        isinstance(threshold, (bool, np.bool_))
        or not isinstance(threshold, Real)
        or not np.isfinite(threshold)
        or not 0 <= threshold <= 1
    ):
        raise ValueError("threshold must be a finite scalar number from 0 to 1.")
    if not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("model_name must be nonempty text.")
    if seed is not None and (
        isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral)
    ):
        raise ValueError("seed must be an integer or None when unspecified.")
    return float(threshold), model_name.strip(), None if seed is None else int(seed)


def prepare_test_manifest(split_table: pd.DataFrame) -> pd.DataFrame:
    """Select known-label test rows from the team's split without changing it.

    Required columns are txId (or transaction_id), time_step, class and split.
    Accepted classes are illicit/licit/unknown or raw Elliptic 1/2/unknown.
    Validate every supplied row against train periods 1-34 and test 35-49.
    Return transaction_id, time_step and y_true, with 1 illicit and 0 licit.
    """
    table = _required_table(
        split_table, ("transaction_id", "time_step", "class", "split"), "split table"
    )
    if table.empty:
        raise ValueError("Split table must be nonempty.")
    steps = _numeric_column(table["time_step"], "time_step")
    if not steps.isin(range(1, 50)).all():
        raise ValueError("Split table time steps must be integers from 1 to 49.")
    table["time_step"] = steps.astype(int)
    labels = table["class"].astype(str).str.strip().str.lower()
    if not labels.isin([*LABEL_MAP, "unknown"]).all():
        raise ValueError("Split classes must be illicit, licit, unknown, or raw Elliptic 1/2.")
    declared = table["split"].astype(str).str.strip().str.lower()
    if not declared.isin(["train", "test"]).all():
        raise ValueError("Split values must be train or test; validate within development periods.")
    expected = np.where(table["time_step"] <= 34, "train", "test")
    if not np.array_equal(declared.to_numpy(), expected):
        raise ValueError("Declared split disagrees with periods 1-34 train and 35-49 test.")

    selected = declared.eq("test") & labels.ne("unknown")
    manifest = table.loc[selected, ["transaction_id", "time_step"]].copy()
    manifest["y_true"] = labels.loc[selected].map(LABEL_MAP).astype(int)
    if manifest.empty:
        raise ValueError("The split table contains no known-label test transactions.")
    return manifest.reset_index(drop=True)


def _metrics(
    known: np.ndarray, scores: np.ndarray, predicted: np.ndarray
) -> dict[str, object]:
    """Compute threshold metrics from one confusion-count pass; use sklearn for AP."""
    count = len(known)
    # Codes 0, 1, 2 and 3 represent TN, FP, FN and TP respectively.
    tn, fp, fn, tp = (
        int(value) for value in np.bincount(2 * known + predicted, minlength=4)
    )
    positives = tp + fn
    alerts = tp + fp
    f1_denominator = 2 * tp + fp + fn
    both_classes = 0 < positives < count
    empty_value = np.nan if count == 0 else 0.0
    return {
        "n": count,
        "n_illicit": positives,
        "n_licit": tn + fp,
        "n_alerts": alerts,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "prevalence": positives / count if count else np.nan,
        "precision_illicit": tp / alerts if alerts else empty_value,
        "recall_illicit": tp / positives if positives else empty_value,
        "f1_illicit": 2 * tp / f1_denominator if f1_denominator else empty_value,
        "average_precision": (
            float(average_precision_score(known, scores)) if both_classes else np.nan
        ),
        "accuracy": (tp + tn) / count if count else np.nan,
        "precision_defined": alerts > 0,
        "recall_defined": positives > 0,
        "f1_defined": f1_denominator > 0,
        "ap_defined": both_classes,
    }


def _manifest_fingerprint(manifest: pd.DataFrame) -> str:
    """Identify the same IDs and labels regardless of input row order."""
    canonical = manifest.loc[:, list(MANIFEST_COLUMNS)].sort_values("transaction_id")
    text = canonical.to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evaluate_predictions(
    truth: pd.DataFrame,
    predictions: pd.DataFrame,
    *,
    threshold: float = 0.50,
    model_name: str = "model",
    seed: int | None = None,
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    """Evaluate one model/run and return overall, per-period and per-ID results.

    truth: transaction_id (or txId), time_step and binary y_true (1 illicit).
    predictions: transaction_id (or txId) and score_illicit in [0, 1].
    IDs must match exactly. Known labels must cover final-test periods only.
    Undefined threshold metrics use 0 plus definition flags for nonempty groups;
    empty periods have missing metrics. AP requires both classes by project policy.
    """
    threshold, model_name, seed = _run_settings(threshold, model_name, seed)
    manifest = _required_table(truth, MANIFEST_COLUMNS, "truth")
    scores = _required_table(predictions, PREDICTION_COLUMNS, "predictions")
    if manifest.empty:
        raise ValueError("The labeled test manifest is empty.")

    labels = _numeric_column(manifest["y_true"], "y_true")
    if not labels.isin([0, 1]).all():
        raise ValueError("y_true must be recoded: 1 illicit, 0 licit. Exclude unknown labels.")
    manifest["y_true"] = labels.astype(int)
    steps = _numeric_column(manifest["time_step"], "time_step")
    if not steps.isin(TEST_PERIODS).all():
        raise ValueError("This final-test evaluator requires integer time steps 35-49.")
    manifest["time_step"] = steps.astype(int)
    probabilities = _numeric_column(scores["score_illicit"], "score_illicit").to_numpy(dtype=float)
    if not ((probabilities >= 0) & (probabilities <= 1)).all():
        raise ValueError("score_illicit must contain probability estimates from 0 to 1.")

    # Find each score by its ID. Uniqueness was checked before building the index.
    score_ids = pd.Index(scores["transaction_id"])
    positions = score_ids.get_indexer(manifest["transaction_id"])
    missing = int((positions < 0).sum())
    extra = len(scores) - (len(manifest) - missing)
    if missing or extra:
        raise ValueError(
            f"Test ID mismatch: {missing} missing predictions; {extra} unexpected predictions."
        )
    aligned = manifest.copy()
    aligned["score_illicit"] = probabilities[positions]
    known = aligned["y_true"].to_numpy(dtype=int)
    probability = aligned["score_illicit"].to_numpy(dtype=float)
    predicted = (probability >= threshold).astype(int)
    aligned["y_pred"] = predicted
    aligned["outcome"] = OUTCOMES[2 * known + predicted]

    identity = {
        "model": model_name,
        "seed": seed,
        "threshold": threshold,
        "manifest_sha256": _manifest_fingerprint(manifest),
    }
    summary = {**identity, **_metrics(known, probability, predicted)}
    # Group once instead of scanning all transactions separately for each period.
    grouped_positions = aligned.groupby("time_step", sort=False).indices
    empty = np.empty(0, dtype=np.intp)
    rows = []
    for period in TEST_PERIODS:
        group = grouped_positions.get(period, empty)
        rows.append({
            **identity,
            "time_step": period,
            **_metrics(known[group], probability[group], predicted[group]),
        })
    return summary, pd.DataFrame(rows), aligned


def _read_table(path: Path) -> pd.DataFrame:
    """Read a strict UTF-8 CSV without dropping fields or altering literal IDs."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle), [])
    if not header or any(not value.strip() for value in header):
        raise ValueError(f"CSV must have nonempty column headers: {path.name}")
    if len(header) != len(set(header)):
        raise ValueError(f"Duplicate CSV column headers: {path.name}")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", pd.errors.ParserWarning)
            return pd.read_csv(
                path,
                encoding="utf-8-sig",
                dtype=str,
                keep_default_na=False,
                index_col=False,
                on_bad_lines="error",
            )
    except pd.errors.ParserWarning as error:
        raise ValueError(f"CSV row width does not match its headers: {path.name}") from error


def _sha256_file(path: Path) -> str:
    """Hash a file as a stream rather than loading all bytes into memory."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _load_csv_snapshot(path: Path) -> tuple[pd.DataFrame, str]:
    """Ensure the recorded fingerprint corresponds to the CSV being evaluated."""
    fingerprint = _sha256_file(path)
    table = _read_table(path)
    if fingerprint != _sha256_file(path):
        raise ValueError(
            f"Input changed while it was being read: {path.name}. Retry with a stable file."
        )
    return table, fingerprint


def _write_outputs(
    summary: dict[str, object],
    per_step: pd.DataFrame,
    aligned: pd.DataFrame,
    metadata: dict[str, object],
    outdir: Path,
) -> None:
    """Stage complete results, reserve a new directory, and roll back failed moves."""
    if outdir.exists():
        raise ValueError("Output directory already exists. Choose a new directory.")
    outdir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".role4-run-", dir=outdir.parent) as temporary:
        staged = Path(temporary)
        pd.DataFrame([summary]).to_csv(staged / EXPORT_NAMES[0], index=False)
        per_step.to_csv(staged / EXPORT_NAMES[1], index=False)
        aligned.to_csv(staged / EXPORT_NAMES[2], index=False)
        (staged / EXPORT_NAMES[3]).write_text(
            json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        # mkdir is exclusive: two runs cannot claim the same output directory.
        outdir.mkdir(exist_ok=False)
        published: list[Path] = []
        try:
            for filename in EXPORT_NAMES:
                target = outdir / filename
                os.replace(staged / filename, target)
                published.append(target)
        except OSError:
            # Only remove files created by this run; preserve unrelated additions.
            for target in published:
                target.unlink(missing_ok=True)
            with suppress(OSError):
                outdir.rmdir()
            raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    labels = parser.add_mutually_exclusive_group(required=True)
    labels.add_argument("--truth", type=Path, help="Already recoded test manifest CSV.")
    labels.add_argument(
        "--split-file", type=Path, help="Team split CSV: txId,time_step,class,split."
    )
    parser.add_argument("--predictions", type=Path, required=True, help="One model/run score CSV.")
    parser.add_argument("--model", required=True, help="Model name recorded in the outputs.")
    parser.add_argument("--seed", type=int, default=None, help="Actual training seed, if known.")
    parser.add_argument(
        "--threshold", type=float, required=True, help="Cutoff frozen before test evaluation."
    )
    parser.add_argument("--outdir", type=Path, required=True, help="New output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Load inputs, evaluate, save the run and print a compact result summary."""
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.outdir.exists():
            raise ValueError("Output directory already exists. Choose a new directory.")
        label_source = args.truth if args.truth is not None else args.split_file
        source, label_hash = _load_csv_snapshot(label_source)
        truth = source if args.truth is not None else prepare_test_manifest(source)
        predictions, prediction_hash = _load_csv_snapshot(args.predictions)
        summary, per_step, aligned = evaluate_predictions(
            truth, predictions, threshold=args.threshold, model_name=args.model, seed=args.seed
        )
        metadata = {
            "model": summary["model"],
            "seed": summary["seed"],
            "threshold": summary["threshold"],
            "evaluation_scope": "labeled final-test transactions, time steps 35-49",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "manifest_sha256": summary["manifest_sha256"],
            "truth_file": label_source.name,
            "truth_file_sha256": label_hash,
            "label_input_format": "binary_manifest" if args.truth is not None else "team_split",
            "prediction_file": args.predictions.name,
            "prediction_file_sha256": prediction_hash,
            "evaluation_script_sha256": _sha256_file(Path(__file__)),
            "pr_summary": "sklearn.average_precision_score; not trapezoidal PR-AUC",
            "undefined_metric_policy": (
                "0 with flags for undefined precision/recall/F1; "
                "AP missing unless both classes; empty periods missing"
            ),
        }
        if args.split_file is not None:
            test_rows = source["split"].str.strip().str.lower().eq("test")
            metadata["source_test_rows"] = int(test_rows.sum())
            metadata["excluded_unknown_test_rows"] = int(test_rows.sum()) - len(aligned)
        _write_outputs(summary, per_step, aligned, metadata, args.outdir)
    except (OSError, ValueError, TypeError, csv.Error) as error:
        parser.error(str(error))

    print(
        f"Evaluated {summary['n']} transactions: "
        f"{summary['n_illicit']} illicit, {summary['n_licit']} licit."
    )
    print(
        f"Model: {summary['model']}; seed: {summary['seed']}; "
        f"fixed threshold: {summary['threshold']:g}"
    )
    metrics = ("precision_illicit", "recall_illicit", "f1_illicit", "average_precision", "accuracy")
    print(pd.Series({name: summary[name] for name in metrics}).round(4).to_string())
    print(f"Output directory: {args.outdir}")
    print("Retain the *_defined flags and compare the same manifest_sha256 across models.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
