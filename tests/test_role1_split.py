"""Checks for rebuilding the shared split, using invented transactions only."""
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.role1_split import build_split


class SplitTests(unittest.TestCase):
    def test_labels_boundary_and_order(self):
        features = pd.DataFrame([[30, 34, 0.1], [10, 1, 0.2], [20, 35, 0.3], [40, 49, 0.4]])
        classes = pd.DataFrame({'txId': [10, 20, 30, 40], 'class': ['1', '2', 'unknown', '1']})
        split = build_split(features, classes)
        self.assertEqual(split['txId'].tolist(), [30, 10, 20, 40])  # raw features-file order
        self.assertEqual(split['class'].tolist(), ['unknown', 'illicit', 'licit', 'illicit'])
        self.assertEqual(split['split'].tolist(), ['train', 'train', 'test', 'test'])

    def test_missing_or_unknown_class_is_rejected(self):
        features = pd.DataFrame([[10, 1, 0.0], [20, 2, 0.0]])
        for classes in (pd.DataFrame({'txId': [10], 'class': ['1']}),
                        pd.DataFrame({'txId': [10, 20], 'class': ['1', '3']})):
            with self.subTest(classes=classes.to_dict('list')), self.assertRaises(ValueError):
                build_split(features, classes)

    def test_committed_split_invariants(self):
        split = pd.read_csv(ROOT / 'tests/elliptic_split.csv', dtype={'txId': str, 'class': str})
        self.assertEqual(len(split), 203769)
        self.assertTrue(split['txId'].is_unique)
        self.assertTrue((split['split'] == split['time_step'].le(34).map({True: 'train', False: 'test'})).all())
        counts = split.groupby(['split', 'class']).size()
        self.assertEqual((counts['train', 'illicit'], counts['test', 'illicit']), (3462, 1083))


if __name__ == '__main__':
    unittest.main()
