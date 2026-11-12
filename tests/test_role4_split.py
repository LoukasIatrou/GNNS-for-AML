"""Checks for the team's native split-file format, using invented rows only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.role4_evaluation import evaluate_predictions, prepare_test_manifest


def native_fixture():
    canonical = pd.read_csv(ROOT / 'tests/fixtures/role4/simulated_test_manifest.csv', dtype={'transaction_id': str})
    table = canonical.rename(columns={'transaction_id': 'txId', 'y_true': 'class'})
    table['class'] = table['class'].map({1: 'illicit', 0: 'licit'})
    table['split'] = 'test'
    extra = pd.DataFrame([
        {'txId': 'TRAIN_UNKNOWN', 'time_step': 1, 'class': 'unknown', 'split': 'train'},
        {'txId': 'TEST_UNKNOWN', 'time_step': 35, 'class': 'unknown', 'split': 'test'},
    ])
    return pd.concat([extra, table], ignore_index=True), canonical


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.native, self.canonical = native_fixture()

    def test_known_test_rows_and_class_direction(self):
        manifest = prepare_test_manifest(self.native)
        assert_frame_equal(manifest, self.canonical)
        self.assertEqual(len(manifest), 8)
        self.assertEqual(manifest.y_true.sum(), 3)
        self.assertNotIn('TEST_UNKNOWN', set(manifest.transaction_id))
        self.assertNotIn('TRAIN_UNKNOWN', set(manifest.transaction_id))

    def test_raw_elliptic_one_two_labels(self):
        raw = self.native.copy()
        raw['class'] = raw['class'].replace({'illicit': '1', 'licit': '2'})
        assert_frame_equal(prepare_test_manifest(raw), self.canonical)

    def test_native_prediction_id_name(self):
        pred = pd.read_csv(ROOT / 'tests/fixtures/role4/simulated_predictions.csv').rename(columns={'transaction_id': 'txId'})
        summary, _, _ = evaluate_predictions(prepare_test_manifest(self.native), pred)
        self.assertEqual((summary['tp'], summary['fp'], summary['fn'], summary['tn']), (2, 1, 1, 4))
        ambiguous = pred.assign(transaction_id=pred.txId)
        with self.assertRaises(ValueError):
            evaluate_predictions(self.canonical, ambiguous)

    def test_original_split_table_is_not_modified(self):
        original = self.native.copy(deep=True)
        prepare_test_manifest(self.native)
        assert_frame_equal(self.native, original)

    def test_declared_split_must_match_period(self):
        for row, split in [(0, 'test'), (2, 'train'), (0, 'validation')]:
            bad = self.native.copy()
            bad.loc[row, 'split'] = split
            with self.subTest(row=row, split=split), self.assertRaises(ValueError):
                prepare_test_manifest(bad)

    def test_unknown_class_values_and_missing_values_are_rejected(self):
        for value in ['fraud', '0', None]:
            bad = self.native.copy()
            bad.loc[2, 'class'] = value
            with self.subTest(label=value), self.assertRaises(ValueError):
                prepare_test_manifest(bad)
        with self.assertRaises(ValueError):
            prepare_test_manifest(self.native.drop(columns='split'))

    def test_duplicate_ids_and_invalid_periods_are_rejected(self):
        for bad in [pd.concat([self.native, self.native.iloc[:1]], ignore_index=True),
                    self.native.assign(time_step=35.5), self.native.assign(time_step=50)]:
            with self.subTest(rows=len(bad)), self.assertRaises(ValueError):
                prepare_test_manifest(bad)

    def test_no_known_test_labels_is_rejected(self):
        with self.assertRaises(ValueError):
            prepare_test_manifest(self.native.assign(**{'class': 'unknown'}))

    def test_split_file_cli_accepts_native_predictions(self):
        with tempfile.TemporaryDirectory(prefix='role4-native-') as d:
            path = Path(d)
            self.native.to_csv(path / 'split.csv', index=False)
            pred = pd.read_csv(ROOT / 'tests/fixtures/role4/simulated_predictions.csv').rename(columns={'transaction_id': 'txId'})
            pred.to_csv(path / 'pred.csv', index=False)
            command = [sys.executable, '-m', 'src.role4_evaluation',
                       '--split-file', str(path / 'split.csv'), '--predictions', str(path / 'pred.csv'),
                       '--model', 'SIMULATED_NATIVE', '--seed', '0', '--threshold', '0.50',
                       '--outdir', str(path / 'results')]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = pd.read_csv(path / 'results/overall_metrics.csv').iloc[0]
            self.assertEqual(summary.n, 8)
            self.assertEqual(summary.tp, 2)
            metadata = json.loads((path / 'results/run_metadata.json').read_text())
            self.assertEqual(metadata['label_input_format'], 'team_split')
            both_inputs = command + ['--truth', str(path / 'unused.csv')]
            rejected = subprocess.run(both_inputs, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)


if __name__ == '__main__':
    unittest.main()
