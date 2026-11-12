"""Regression checks and independent numerical references for the reviewed evaluator."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix,
    precision_recall_fscore_support,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import role4_evaluation as evaluation


def small_inputs():
    truth = pd.DataFrame({
        "transaction_id": ["001", "NA", "B", "C"],
        "time_step": [35, 35, 36, 36],
        "y_true": [1, 0, 1, 0],
    })
    scores = pd.DataFrame({
        "transaction_id": ["001", "NA", "B", "C"],
        "score_illicit": [1.0, 0.75, 0.25, 0.0],
    })
    return truth, scores


class NumericalReferenceTests(unittest.TestCase):
    def test_sixty_randomised_cases_match_sklearn(self):
        rng = np.random.default_rng(2026)
        for n in [1, 2, 17, 200]:
            for positive_share in [0.0, 0.02, 0.2, 0.5, 1.0]:
                known = (rng.random(n) < positive_share).astype(int)
                # Include tied scores and exact endpoints.
                probability = rng.choice([0.0, 0.25, 0.5, 0.75, 1.0], size=n)
                truth = pd.DataFrame({
                    "transaction_id": [f"ID{i}" for i in range(n)],
                    "time_step": rng.integers(35, 50, size=n),
                    "y_true": known,
                })
                scores = pd.DataFrame({"transaction_id": truth.transaction_id, "score_illicit": probability})
                for threshold in [0.0, 0.5, 1.0]:
                    with self.subTest(n=n, positive_share=positive_share, threshold=threshold):
                        summary, periods, aligned = evaluation.evaluate_predictions(truth, scores, threshold=threshold)
                        predicted = (probability >= threshold).astype(int)
                        precision, recall, f1, _ = precision_recall_fscore_support(
                            known, predicted, average="binary", pos_label=1, zero_division=0
                        )
                        for key, expected in [
                            ("precision_illicit", precision), ("recall_illicit", recall),
                            ("f1_illicit", f1), ("accuracy", accuracy_score(known, predicted)),
                        ]:
                            self.assertAlmostEqual(summary[key], expected, places=12)
                        self.assertEqual(
                            [summary[k] for k in ["tn", "fp", "fn", "tp"]],
                            confusion_matrix(known, predicted, labels=[0, 1]).ravel().tolist(),
                        )
                        if len(np.unique(known)) == 2:
                            self.assertAlmostEqual(summary["average_precision"], average_precision_score(known, probability))
                        else:
                            self.assertTrue(np.isnan(summary["average_precision"]))
                        for period in periods.itertuples():
                            group = aligned.loc[aligned.time_step == period.time_step]
                            self.assertEqual(period.n, len(group))
                            if not group.empty:
                                expected_f1 = precision_recall_fscore_support(
                                    group.y_true, group.y_pred, average="binary", zero_division=0
                                )[2]
                                self.assertAlmostEqual(period.f1_illicit, expected_f1)

    def test_constant_scores_have_prevalence_ap(self):
        truth, scores = small_inputs()
        result, _, _ = evaluation.evaluate_predictions(truth, scores.assign(score_illicit=0.5))
        self.assertAlmostEqual(result["average_precision"], 0.5)

    def test_lower_threshold_never_reduces_recall_or_alert_count(self):
        truth, scores = small_inputs()
        results = [evaluation.evaluate_predictions(truth, scores, threshold=t)[0] for t in [1, 0.75, 0.5, 0]]
        self.assertEqual([r["n_alerts"] for r in results], sorted(r["n_alerts"] for r in results))
        self.assertEqual([r["recall_illicit"] for r in results], sorted(r["recall_illicit"] for r in results))

    def test_api_returns_error_categories_and_fingerprint(self):
        truth, scores = small_inputs()
        summary, periods, aligned = evaluation.evaluate_predictions(truth, scores)
        self.assertEqual(aligned.outcome.tolist(), ["TP", "FP", "FN", "TN"])
        self.assertEqual(periods.manifest_sha256.nunique(), 1)
        self.assertEqual(periods.manifest_sha256.iloc[0], summary["manifest_sha256"])
        reordered = evaluation.evaluate_predictions(truth.iloc[::-1], scores.iloc[::-1])[0]
        self.assertEqual(summary["manifest_sha256"], reordered["manifest_sha256"])


class ValidationRegressionTests(unittest.TestCase):
    def setUp(self):
        self.truth, self.scores = small_inputs()

    def test_threshold_must_be_a_real_scalar(self):
        for value in [True, False, "0.5", None, [0.5], np.array([0.5]), 0.5 + 0j]:
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                evaluation.evaluate_predictions(self.truth, self.scores, threshold=value)
        result, _, _ = evaluation.evaluate_predictions(self.truth, self.scores, threshold=np.float64(0.5))
        self.assertIs(type(result["threshold"]), float)

    def test_model_name_and_seed_are_checked(self):
        for model in [None, "", " ", 42]:
            with self.subTest(model=model), self.assertRaises(ValueError):
                evaluation.evaluate_predictions(self.truth, self.scores, model_name=model)
        for seed in [True, 0.5, "1"]:
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                evaluation.evaluate_predictions(self.truth, self.scores, seed=seed)
        summary, _, _ = evaluation.evaluate_predictions(self.truth, self.scores, model_name=" Model ", seed=np.int64(3))
        self.assertEqual(summary["model"], "Model")
        self.assertIs(type(summary["seed"]), int)
        json.dumps(summary, allow_nan=False)

    def test_wrong_table_types_raise_clear_errors(self):
        for table in [None, [], {"transaction_id": ["A"]}]:
            with self.subTest(table=type(table).__name__), self.assertRaisesRegex(TypeError, "DataFrame"):
                evaluation.evaluate_predictions(table, self.scores)

    def test_floating_point_and_boolean_ids_are_rejected(self):
        for values in [[1.0, 2.0, 3.0, 4.0], [True, False, "B", "C"]]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                evaluation.evaluate_predictions(self.truth.assign(transaction_id=values), self.scores)

    def test_surrounding_id_whitespace_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "whitespace"):
            evaluation.evaluate_predictions(self.truth.assign(transaction_id=[" 001", "NA", "B", "C"]), self.scores)

    def test_collisions_after_integer_id_conversion_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            evaluation.evaluate_predictions(self.truth.assign(transaction_id=[1, "1", "B", "C"]), self.scores)

    def test_boolean_and_complex_numeric_fields_are_rejected(self):
        for column, values in [
            ("y_true", [True, False, True, False]),
            ("time_step", [True, True, True, True]),
            ("y_true", [1 + 0j, 0 + 0j, 1 + 0j, 0 + 0j]),
        ]:
            with self.subTest(column=column), self.assertRaises(ValueError):
                evaluation.evaluate_predictions(self.truth.assign(**{column: values}), self.scores)
        for values in [[True, False, True, False], [True, 0.5, 0.25, 0.0], [1+0j, 0.75+0j, 0.25+0j, 0j]]:
            with self.subTest(scores=values), self.assertRaises(ValueError):
                evaluation.evaluate_predictions(self.truth, self.scores.assign(score_illicit=values))

    def test_truth_accepts_native_id_name(self):
        summary, _, _ = evaluation.evaluate_predictions(self.truth.rename(columns={"transaction_id": "txId"}), self.scores)
        self.assertEqual(summary["n"], 4)


class FileHandlingRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="role4-review-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.truth, self.scores = small_inputs()
        self.summary, self.periods, self.aligned = evaluation.evaluate_predictions(self.truth, self.scores)

    def write_run(self, metadata=None):
        evaluation._write_outputs(self.summary, self.periods, self.aligned,
                                  {"model": "CHECK"} if metadata is None else metadata,
                                  self.path / "run")

    def test_literal_na_and_leading_zero_ids_are_preserved(self):
        path = self.path / "truth.csv"
        self.truth.to_csv(path, index=False)
        loaded = evaluation._read_table(path)
        self.assertEqual(loaded.transaction_id.tolist(), ["001", "NA", "B", "C"])
        summary, _, _ = evaluation.evaluate_predictions(loaded, self.scores)
        self.assertEqual(summary["n"], 4)

    def test_extra_csv_fields_cannot_silently_change_ids(self):
        for content in [
            "transaction_id,score_illicit\nT1,0.9,0.1\n",
            "transaction_id,score_illicit\nT1,0.9\nT2,0.8,0.1\n",
        ]:
            path = self.path / "scores.csv"
            path.write_text(content)
            with self.subTest(content=content), self.assertRaises(ValueError):
                evaluation._read_table(path)

    def test_blank_headers_and_empty_files_are_rejected(self):
        path = self.path / "scores.csv"
        for content in ["", "transaction_id,\nT1,0.9\n", "transaction_id,   \nT1,0.9\n"]:
            path.write_text(content)
            with self.subTest(content=content), self.assertRaises(ValueError):
                evaluation._read_table(path)

    def test_utf8_bom_is_supported(self):
        path = self.path / "scores.csv"
        path.write_text("transaction_id,score_illicit\n001,0.9\n", encoding="utf-8-sig")
        self.assertEqual(evaluation._read_table(path).transaction_id.tolist(), ["001"])

    def test_missing_csv_cells_are_rejected_by_evaluation(self):
        path = self.path / "scores.csv"
        path.write_text("transaction_id,score_illicit\n001,\nNA,0.75\nB,0.25\nC,0.0\n")
        with self.assertRaises(ValueError):
            evaluation.evaluate_predictions(self.truth, evaluation._read_table(path))

    def test_streamed_hash_matches_direct_sha256(self):
        path = self.path / "bytes.bin"
        path.write_bytes(bytes(range(256)) * 9000)
        self.assertEqual(evaluation._sha256_file(path), hashlib.sha256(path.read_bytes()).hexdigest())

    def test_input_changed_during_read_is_detected(self):
        path = self.path / "truth.csv"
        self.truth.to_csv(path, index=False)
        original_reader = evaluation._read_table
        def change_after_read(source):
            table = original_reader(source)
            source.write_text(source.read_text() + "CHANGED,35,0\n")
            return table
        with patch.object(evaluation, "_read_table", side_effect=change_after_read):
            with self.assertRaisesRegex(ValueError, "Input changed"):
                evaluation._load_csv_snapshot(path)

    def test_failed_csv_write_leaves_no_result_directory(self):
        with patch.object(pd.DataFrame, "to_csv", side_effect=OSError("Simulated full disk")):
            with self.assertRaises(OSError):
                self.write_run()
        self.assertFalse((self.path / "run").exists())
        self.assertEqual(list(self.path.glob(".role4-run-*")), [])

    def test_invalid_metadata_leaves_no_result_directory(self):
        with self.assertRaises(ValueError):
            self.write_run(metadata={"invalid": float("nan")})
        self.assertFalse((self.path / "run").exists())
        self.assertEqual(list(self.path.glob(".role4-run-*")), [])

    def test_failed_publish_removes_this_runs_partial_files(self):
        original_replace = os.replace
        calls = 0
        def fail_second_move(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("Simulated move failure")
            return original_replace(source, target)
        with patch.object(evaluation.os, "replace", side_effect=fail_second_move):
            with self.assertRaises(OSError):
                self.write_run()
        self.assertFalse((self.path / "run").exists())
        self.assertEqual(list(self.path.glob(".role4-run-*")), [])

    def test_concurrent_output_reservation_preserves_other_run(self):
        output = self.path / "run"
        original_mkdir = Path.mkdir
        def reserve_first(path, *args, **kwargs):
            if path == output and not path.exists():
                original_mkdir(path)
                (path / "other-run.txt").write_text("keep")
            return original_mkdir(path, *args, **kwargs)
        with patch.object(Path, "mkdir", reserve_first):
            with self.assertRaises(FileExistsError):
                self.write_run()
        self.assertEqual((output / "other-run.txt").read_text(), "keep")
        self.assertEqual([p.name for p in output.iterdir()], ["other-run.txt"])


if __name__ == "__main__":
    unittest.main()
