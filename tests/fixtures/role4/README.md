# Invented evaluation examples

These eight transactions and prediction scores are simulated. They are not real Elliptic transactions or model-performance findings.

The known-answer table uses the evaluator's binary convention: 1 illicit, 0 licit. The shared split file at `tests/elliptic_split.csv` instead uses the team's native `txId,time_step,class,split` format. The adapter in `src.role4_evaluation` converts that format explicitly.

At threshold 0.50, the examples give TP=2, FP=1, FN=1 and TN=4. Precision, recall and F1 are 2/3. AP is `(1 + 2/3 + 3/4) / 3 = 29/36`. Expected values are in `expected_demo_metrics.json`.
