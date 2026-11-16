"""Combine several role4_evaluation runs into one model comparison.

Command line, from the repository root:
    python -m src.role4_compare outputs/role4/rf_seed0 outputs/role4/gcn_seed0 ... \
        --outdir outputs/role4_comparison

Every run must carry the same manifest_sha256, i.e. be scored on the same known-label test
transactions; otherwise the comparison is refused. Writes runs.csv (one row per run) and
summary.csv (mean and sample std over the runs of each model).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Weber et al. (2019): a dark market closed at time step 43 and every model failed afterwards.
SHIFT_STEP = 43
METRICS = ["precision_illicit", "recall_illicit", "f1_illicit", "average_precision",
           "f1_before_shift", "f1_after_shift"]


def _pooled_f1(steps: pd.DataFrame) -> float:
    tp, fp, fn = steps[["tp", "fp", "fn"]].sum()
    return 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else float("nan")


def run_row(run_dir: Path) -> dict[str, object]:
    """Overall metrics of one evaluator run plus pooled F1 before/after the step-43 shift."""
    overall = pd.read_csv(run_dir / "overall_metrics.csv").iloc[0].to_dict()
    steps = pd.read_csv(run_dir / "metrics_per_time_step.csv")
    overall["f1_before_shift"] = _pooled_f1(steps[steps["time_step"] < SHIFT_STEP])
    overall["f1_after_shift"] = _pooled_f1(steps[steps["time_step"] >= SHIFT_STEP])
    overall["run_dir"] = str(run_dir)
    return overall


def compare(run_dirs: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    runs = pd.DataFrame([run_row(Path(d)) for d in run_dirs])
    if runs["manifest_sha256"].nunique() != 1:
        raise ValueError("Runs were scored on different test sets (manifest_sha256 differs).")
    keep = ["model", "seed", "threshold", "tp", "fp", "fn", "tn", *METRICS, "manifest_sha256", "run_dir"]
    runs = runs[keep].sort_values(["model", "seed"]).reset_index(drop=True)
    summary = runs.groupby("model")[METRICS].agg(["mean", "std"])
    summary.columns = [f"{m}_{stat}" for m, stat in summary.columns]
    summary.insert(0, "n_runs", runs.groupby("model").size())
    return runs, summary.sort_values("average_precision_mean", ascending=False).reset_index()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dirs", nargs="+", type=Path, help="role4_evaluation output directories.")
    parser.add_argument("--outdir", type=Path, required=True, help="New output directory.")
    args = parser.parse_args(argv)
    runs, summary = compare(args.run_dirs)
    args.outdir.mkdir(parents=True, exist_ok=False)
    runs.to_csv(args.outdir / "runs.csv", index=False)
    summary.to_csv(args.outdir / "summary.csv", index=False)
    print(summary.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
