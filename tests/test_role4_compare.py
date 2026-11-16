"""Checks for combining evaluator runs, using invented transactions only."""
from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.role4_compare import compare
from src.role4_evaluation import main as evaluate

FIXTURES = ROOT / 'tests/fixtures/role4'


class CompareTests(unittest.TestCase):
    def run_eval(self, root, name, seed, truth=FIXTURES / 'simulated_test_manifest.csv'):
        outdir = Path(root) / f'{name}_{seed}'
        evaluate(['--truth', str(truth), '--predictions', str(FIXTURES / 'simulated_predictions.csv'),
                  '--model', name, '--seed', str(seed), '--threshold', '0.5', '--outdir', str(outdir)])
        return outdir

    def test_summary_and_shift_split(self):
        with tempfile.TemporaryDirectory() as root:
            runs, summary = compare([self.run_eval(root, 'A', 0), self.run_eval(root, 'A', 1)])
        self.assertEqual(len(runs), 2)
        row = summary.iloc[0]
        self.assertEqual(row['n_runs'], 2)
        self.assertAlmostEqual(row['f1_illicit_mean'], 2 / 3)
        self.assertAlmostEqual(row['f1_illicit_std'], 0.0)
        # The fixture only covers steps 35-36, so the after-shift period has no labelled data.
        self.assertAlmostEqual(row['f1_before_shift_mean'], 2 / 3)
        self.assertTrue(pd.isna(row['f1_after_shift_mean']))

    def test_rejects_different_test_sets(self):
        with tempfile.TemporaryDirectory() as root:
            truth = pd.read_csv(FIXTURES / 'simulated_test_manifest.csv')
            truth.loc[0, 'y_true'] = 0
            other = Path(root) / 'other_truth.csv'
            truth.to_csv(other, index=False)
            dirs = [self.run_eval(root, 'A', 0), self.run_eval(root, 'B', 0, truth=other)]
            with self.assertRaisesRegex(ValueError, 'different test sets'):
                compare(dirs)


if __name__ == '__main__':
    unittest.main()
