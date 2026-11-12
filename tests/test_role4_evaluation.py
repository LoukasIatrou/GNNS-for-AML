"""Numerical and interface checks using invented transactions only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.role4_evaluation import evaluate_predictions


def fixture():
    return (
        pd.read_csv(ROOT / 'tests/fixtures/role4/simulated_test_manifest.csv', dtype={'transaction_id': str}),
        pd.read_csv(ROOT / 'tests/fixtures/role4/simulated_predictions.csv', dtype={'transaction_id': str}),
    )


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.truth, self.pred = fixture()

    def evaluate(self, truth=None, pred=None, **kwargs):
        return evaluate_predictions(self.truth if truth is None else truth,
                                    self.pred if pred is None else pred, **kwargs)

    def test_hand_calculated_counts_and_metrics(self):
        summary, _, _ = self.evaluate()
        expected = json.loads((ROOT / 'tests/fixtures/role4/expected_demo_metrics.json').read_text())
        for key, value in expected.items():
            if key != 'data_status':
                with self.subTest(metric=key):
                    self.assertAlmostEqual(summary[key], value, places=12)
        self.assertAlmostEqual(summary['average_precision'], (1 + 2/3 + 3/4) / 3)

    def test_id_alignment_with_shuffled_predictions(self):
        summary, _, aligned = self.evaluate(pred=self.pred.sample(frac=1, random_state=17))
        self.assertEqual((summary['tp'], summary['fp'], summary['fn'], summary['tn']), (2, 1, 1, 4))
        self.assertEqual(aligned.set_index('transaction_id').loc['T2', 'score_illicit'], 0.80)

    def test_all_periods_including_empty_periods(self):
        _, periods, _ = self.evaluate()
        self.assertEqual(periods.time_step.tolist(), list(range(35, 50)))
        empty = periods.loc[periods.time_step >= 37]
        self.assertTrue((empty.n == 0).all())
        self.assertTrue(empty.f1_illicit.isna().all())
        self.assertTrue(empty.average_precision.isna().all())
        self.assertFalse(empty.ap_defined.any())
        self.assertAlmostEqual(periods.loc[periods.time_step == 35, 'f1_illicit'].iloc[0], 0.5)

    def test_overall_f1_is_pooled(self):
        summary, periods, _ = self.evaluate()
        self.assertAlmostEqual(summary['f1_illicit'], 2/3)
        self.assertAlmostEqual(periods.loc[periods.n > 0, 'f1_illicit'].mean(), 0.75)

    def test_no_alerts_preserves_undefined_precision_flag(self):
        summary, _, _ = self.evaluate(pred=self.pred.assign(score_illicit=0.0))
        self.assertEqual(summary['n_alerts'], 0)
        self.assertEqual(summary['f1_illicit'], 0.0)
        self.assertFalse(summary['precision_defined'])
        self.assertTrue(summary['recall_defined'])
        self.assertTrue(summary['f1_defined'])

    def test_all_licit_group(self):
        summary, _, _ = self.evaluate(truth=self.truth.assign(y_true=0), pred=self.pred.assign(score_illicit=0.0))
        self.assertTrue(np.isnan(summary['average_precision']))
        self.assertFalse(summary['ap_defined'])
        self.assertFalse(summary['recall_defined'])
        self.assertFalse(summary['f1_defined'])
        self.assertEqual(summary['accuracy'], 1.0)

    def test_all_illicit_group(self):
        summary, _, _ = self.evaluate(truth=self.truth.assign(y_true=1), pred=self.pred.assign(score_illicit=1.0))
        self.assertEqual(summary['f1_illicit'], 1.0)
        self.assertFalse(summary['ap_defined'])
        self.assertTrue(np.isnan(summary['average_precision']))

    def test_threshold_equality_is_flagged(self):
        summary, _, aligned = self.evaluate(pred=self.pred.assign(score_illicit=0.50))
        self.assertEqual(summary['n_alerts'], 8)
        self.assertTrue((aligned.y_pred == 1).all())
        self.assertAlmostEqual(summary['precision_illicit'], 3/8)
        self.assertEqual(summary['recall_illicit'], 1.0)

    def test_inputs_are_not_modified(self):
        before_truth, before_pred = self.truth.copy(deep=True), self.pred.copy(deep=True)
        self.evaluate()
        assert_frame_equal(self.truth, before_truth)
        assert_frame_equal(self.pred, before_pred)

    def test_missing_extra_and_duplicate_ids(self):
        cases = [self.pred.iloc[:-1], pd.concat([self.pred, self.pred.iloc[:1]], ignore_index=True),
                 pd.concat([self.pred, pd.DataFrame({'transaction_id': ['EXTRA'], 'score_illicit': [0.5]})], ignore_index=True)]
        for i, pred in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(ValueError):
                self.evaluate(pred=pred)
        with self.assertRaises(ValueError):
            self.evaluate(truth=pd.concat([self.truth, self.truth.iloc[:1]], ignore_index=True))

    def test_invalid_labels_scores_and_periods(self):
        for column, values, is_truth in [
            ('y_true', [2, 'unknown', np.nan, 0.5], True),
            ('time_step', [34, 50, 35.5, np.inf, np.nan], True),
            ('score_illicit', [-0.1, 1.1, np.inf, -np.inf, np.nan, 'invalid'], False),
        ]:
            for value in values:
                with self.subTest(column=column, value=value), self.assertRaises((ValueError, TypeError)):
                    if is_truth:
                        self.evaluate(truth=self.truth.assign(**{column: value}))
                    else:
                        self.evaluate(pred=self.pred.assign(**{column: value}))

    def test_invalid_thresholds(self):
        for value in [-0.1, 1.1, np.inf, np.nan]:
            with self.subTest(threshold=value), self.assertRaises(ValueError):
                self.evaluate(threshold=value)

    def test_missing_columns_empty_inputs_and_blank_ids(self):
        for truth, pred in [(self.truth.drop(columns='y_true'), self.pred),
                            (self.truth, self.pred.drop(columns='score_illicit')),
                            (self.truth.iloc[:0], self.pred.iloc[:0]),
                            (self.truth.assign(transaction_id=' '), self.pred)]:
            with self.subTest(columns=truth.columns.tolist()), self.assertRaises(ValueError):
                self.evaluate(truth=truth, pred=pred)

    def test_duplicate_dataframe_columns(self):
        bad = pd.concat([self.truth, self.truth[['y_true']]], axis=1)
        with self.assertRaises(ValueError):
            self.evaluate(truth=bad)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='role4-tests-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.truth, self.pred = fixture()
        self.truth.to_csv(self.path / 'truth.csv', index=False)
        self.pred.to_csv(self.path / 'pred.csv', index=False)

    def run_cli(self, name='run'):
        return subprocess.run([
            sys.executable, '-m', 'src.role4_evaluation',
            '--truth', str(self.path / 'truth.csv'), '--predictions', str(self.path / 'pred.csv'),
            '--model', 'SIMULATED_TEST', '--seed', '0', '--threshold', '0.50',
            '--outdir', str(self.path / name),
        ], text=True, capture_output=True, cwd=ROOT)

    def test_four_exports_and_expected_results(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        run = self.path / 'run'
        self.assertEqual({p.name for p in run.iterdir()}, {
            'overall_metrics.csv', 'metrics_per_time_step.csv', 'evaluated_predictions.csv', 'run_metadata.json'})
        summary = pd.read_csv(run / 'overall_metrics.csv').iloc[0]
        self.assertAlmostEqual(summary.f1_illicit, 2/3)
        self.assertAlmostEqual(summary.average_precision, 29/36)
        self.assertEqual(len(pd.read_csv(run / 'metrics_per_time_step.csv')), 15)
        outcomes = pd.read_csv(run / 'evaluated_predictions.csv').outcome.value_counts().to_dict()
        self.assertEqual(outcomes, {'TN': 4, 'TP': 2, 'FP': 1, 'FN': 1})
        metadata = json.loads((run / 'run_metadata.json').read_text())
        self.assertEqual(metadata['manifest_sha256'], summary.manifest_sha256)
        self.assertEqual((metadata['model'], metadata['seed'], metadata['threshold']), ('SIMULATED_TEST', 0, 0.5))

    def test_fingerprint_is_stable_under_row_reordering(self):
        first = self.run_cli('first')
        self.assertEqual(first.returncode, 0, first.stderr)
        self.truth.sample(frac=1, random_state=5).to_csv(self.path / 'truth.csv', index=False)
        self.pred.sample(frac=1, random_state=7).to_csv(self.path / 'pred.csv', index=False)
        second = self.run_cli('second')
        self.assertEqual(second.returncode, 0, second.stderr)
        one = json.loads((self.path / 'first/run_metadata.json').read_text())
        two = json.loads((self.path / 'second/run_metadata.json').read_text())
        self.assertEqual(one['manifest_sha256'], two['manifest_sha256'])
        self.assertNotEqual(one['truth_file_sha256'], two['truth_file_sha256'])

    def test_invalid_input_creates_no_results(self):
        self.pred.iloc[:-1].to_csv(self.path / 'pred.csv', index=False)
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Test ID mismatch', result.stderr)
        self.assertFalse((self.path / 'run').exists())

    def test_previous_results_are_not_overwritten(self):
        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        metadata = (self.path / 'run/run_metadata.json').read_bytes()
        second = self.run_cli()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn('Output directory already exists', second.stderr)
        self.assertEqual((self.path / 'run/run_metadata.json').read_bytes(), metadata)

    def test_duplicate_csv_headers_are_rejected(self):
        (self.path / 'pred.csv').write_text('transaction_id,score_illicit,score_illicit\nT1,0.9,0.1\n')
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Duplicate CSV column headers', result.stderr)
        self.assertFalse((self.path / 'run').exists())


if __name__ == '__main__':
    unittest.main()
