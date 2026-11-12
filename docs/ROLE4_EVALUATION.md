# Shared model evaluation

For a complete plain-language explanation in Italian, see [ROLE4_RIASSUNTO_IT.md](ROLE4_RIASSUNTO_IT.md).

## What this contribution does

Role 4 provides the program that checks model predictions against the known answers. Roles 2 and 3 can use it to compare their models fairly. The program does not train a model.

This version is adapted to the team's existing file **`tests/elliptic_split.csv`**. That file stays in its current location.

| Person | What they provide |
|---|---|
| Role 1 | The shared split file, transaction IDs and known classes. |
| Roles 2 and 3 | One file of illicit-class prediction scores per model and training run. |
| Role 4 | Common scoring rules, evaluation code, tests and later comparison of results. |

## What is already in the shared data

Inspection of the supplied repository snapshot found:

| Part of the split | All transactions | Known illicit | Known licit | Unknown class |
|---|---:|---:|---:|---:|
| Train, periods 1-34 | 136,265 | 3,462 | 26,432 | 106,371 |
| Test, periods 35-49 | 67,504 | 1,083 | 15,587 | 50,834 |

**Evaluation uses the 16,670 test transactions whose class is known.** Unknown does not mean licit. Unknown transactions can remain graph context under the team's modelling rules, but they are excluded from supervised metrics.

The shared CSV has columns `txId`, `time_step`, `class` and `split`. Its labels are the words `illicit`, `licit` and `unknown`. The adapter maps illicit to evaluation class 1 and licit to 0. It also accepts raw Elliptic class codes 1/2, but rejects binary class 0 in the native split format to avoid ambiguous conversions. The already-converted `--truth` format described below uses 0/1.

## 1 Install the libraries

Run commands from the repository root, where `README.md`, `src/` and `tests/` are located. Python 3.12 is the verified version.

```bash
python -m pip install -r requirements-evaluation.txt
```

The file pins the tested core library versions. Supporting dependencies are resolved by pip. Input CSV files must use UTF-8, optionally with a BOM. Empty or duplicated headers, malformed row widths and invalid numeric values are rejected rather than silently corrected.

## 2 Try the invented example

This command runs without training a model:

```bash
python -m src.role4_evaluation --truth tests/fixtures/role4/simulated_test_manifest.csv --predictions tests/fixtures/role4/simulated_predictions.csv --model SIMULATED_DEMO --seed 0 --threshold 0.50 --outdir outputs/role4/simulated_demo
```

The inputs are invented. Expected results are TP=2, FP=1, FN=1, TN=4, precision/recall/F1=0.6667 and AP=0.8056. These values check the software and are not findings about the dataset.

Use a new output folder for every run. The program refuses to overwrite an existing folder. It writes all results to a temporary location first, then reserves a new destination. A recoverable write or move error removes this run's partial outputs. The metadata file is moved last as the completion record. `outputs/` is already excluded by the repository's existing ignore rules.

## 3 Prepare real model predictions

Roles 2 and 3 produce one CSV per model and training seed:

| Column | Required content |
|---|---|
| `txId` **or** `transaction_id` | Exactly the 16,670 known-class test IDs from the supplied snapshot, once each. Use one ID-column name, not both. If the shared dataset changes, use the adapter's updated list. |
| `score_illicit` | Estimated probability of the illicit class between 0 and 1. Higher means more illicit. |

Verify the model's class order when exporting probabilities. The illicit score is not automatically the second output column. Estimates are not assumed to be calibrated.

Get the exact evaluation IDs from the split table rather than typing counts or IDs by hand:

```python
import pandas as pd
from src.role4_evaluation import prepare_test_manifest

split = pd.read_csv("tests/elliptic_split.csv", dtype={"txId": str, "class": str})
truth = prepare_test_manifest(split)
# truth contains transaction_id, time_step and y_true.
# Export predictions for these IDs using the model's actual illicit-class score.
```

If a model scores all test nodes, filter its export to these known-class IDs before evaluating. The evaluator rejects extra or missing IDs instead of silently dropping them. Row order can differ because it matches IDs explicitly. It also rejects duplicate IDs, surrounding ID whitespace, missing values, invalid class values, invalid periods and invalid probabilities. Read IDs as text to preserve leading zeros. Floating-point or boolean IDs are rejected because they can lose the original identifier.

## 4 Evaluate the model

Replace the prediction filename, model name and seed with the actual values. The model name must be nonempty text, the seed an integer or unspecified, and the threshold a finite number from 0 to 1:

```bash
python -m src.role4_evaluation --split-file tests/elliptic_split.csv --predictions outputs/role4/random_forest_seed0_predictions.csv --model RandomForest --seed 0 --threshold 0.50 --outdir outputs/role4/random_forest_seed0
```

The split-file adapter validates the declared time split and excludes unknown test labels. It does not alter the shared CSV.

A model notebook can instead use the functions directly:

```python
import pandas as pd
from src.role4_evaluation import prepare_test_manifest, evaluate_predictions

split = pd.read_csv("tests/elliptic_split.csv", dtype={"txId": str, "class": str})
truth = prepare_test_manifest(split)
predictions = pd.read_csv("outputs/role4/random_forest_seed0_predictions.csv", dtype={"txId": str})
summary, per_step, aligned = evaluate_predictions(
    truth, predictions, threshold=0.50, model_name="RandomForest", seed=0
)
```

The function returns the overall summary, period table and transaction table in memory. Both the notebook API and the command-line interface now include the manifest fingerprint and each transaction's error category. The command-line version also saves the four files below.

An already-converted table with `transaction_id,time_step,y_true` may be supplied using `--truth` instead of `--split-file`. In that table, `y_true` is 1 for illicit and 0 for licit. Use exactly one input option.

## 5 Understand the results

| Measure | What it tells us |
|---|---|
| Precision | Of the transactions flagged as illicit, how many are actually labelled illicit? |
| Recall | Of all known illicit transactions, how many did the model find? |
| F1 | How well does the model combine precision and recall? |
| Average precision or AP | How well does the original score rank illicit transactions across thresholds? |
| Accuracy | How many predictions were correct overall? This is supplementary because the classes are imbalanced. |

A false positive is a licit transaction flagged as illicit. A false negative is an illicit transaction the model misses. Always report their counts and the number of test examples alongside scores.

| Output file | Contents |
|---|---|
| `overall_metrics.csv` | Overall metrics, confusion counts, class counts, definition flags and manifest fingerprint. |
| `metrics_per_time_step.csv` | All periods 35-49, with counts and metrics. |
| `evaluated_predictions.csv` | Each known class, score, predicted class and TP/FP/FN/TN category. |
| `run_metadata.json` | Model, seed, threshold, input format, library versions, file fingerprints and excluded unknown test-row counts. |

AP uses `sklearn.metrics.average_precision_score`, which differs from trapezoidal PR-AUC. Keep the same calculation across models. Overall F1 pools all test predictions; it is not the mean of the period F1 values.

For nonempty groups, an undefined precision/recall/F1 is stored as 0 by convention and marked with a false `*_defined` flag. Preserve those flags. AP is missing unless both classes occur. Periods with no labelled samples have missing metrics. A placeholder must not be presented as measured model performance.

Compare `manifest_sha256` between exported runs to check that transaction IDs, periods and known labels match. This does not prove that upstream training avoided leakage or that Role 1 included every intended labelled transaction.

## 6 Decisions to agree before training

The train/test boundary is already implemented by Role 1: periods 1-34 versus 35-49. The following remain proposals:

- Train on 1-29 and validate on 30-34 during development. Agree whether to retrain on all of 1-34 after choosing settings.
- Use a headline alert threshold of 0.50. If selecting another threshold, choose it on validation data and freeze it before test evaluation.
- Use seeds 0, 1 and 2 for stochastic models if computing time permits; retain each run separately.
- Treat each period as an observed group and document the permitted graph inputs. Keep later-period information and test labels out of model and feature selection. Fit preprocessing and resampling on permitted training data. Apply the same information-access rules to graph features in baselines and to GNNs.

A threshold is the cutoff used to turn a score into an alert. A seed fixes the starting point of random choices. Validation is a check used to choose model settings before the final test.

This is a batch evaluation. Real-time use would require separate checks about information availability. Anonymous features also limit the meaning of later model explanations. A benchmark prediction is a research output, not proof of criminal intent.

## 7 Run the automated checks

```bash
python -m unittest discover -s tests -p "test_role4*.py" -v
```

These checks use invented examples. The reviewed version passes 51 test methods, including an independent comparison against scikit-learn across 60 combinations of sample size, class balance, tied scores and thresholds. Tests also cover the native split adapter, ID alignment, malformed CSVs, input errors, undefined metrics, file-change detection and failed-export cleanup. The added GitHub workflow runs these checks and the simulated example on Python 3.12. Its first hosted run remains pending until the branch is uploaded.

Local integration with the supplied real split file is documented in [ROLE4_VALIDATION.md](ROLE4_VALIDATION.md). Actual model comparison and explanation still require trained models and their predictions. The [assignment requirements check](ROLE4_REQUIREMENTS_CHECK.md) separates completed preparation from pending final work. The [AML background and analysis plan](ROLE4_AML_CONTEXT.md) provides initial context and the planned report structure.

## 8 How the code is organised

| Part | Purpose |
|---|---|
| `prepare_test_manifest` | Reads the team's label convention, validates the time split and selects known-label test transactions. |
| `evaluate_predictions` | Validates and aligns scores, applies the threshold once and returns the numerical results. |
| `_metrics` | Calculates counts and threshold metrics in one pass; uses scikit-learn for average precision. |
| CSV and export helpers | Reject ambiguous input files, record fingerprints and save complete output sets. |
| `main` | Connects those steps to the command-line arguments. |

Type hints document the public inputs and outputs. Constants define periods, labels and export names in one place. Comments explain the non-obvious steps, including ID alignment and metric conventions.

Efficiency changes avoid repeated calls to several metric functions and repeated scans of all rows for each period. Files are hashed as streams. Correctness takes priority over speed: input fingerprints are checked before and after loading to detect changing files.

## Sources

- The team's `tests/elliptic_split.csv` and `data/Final Data Card.html`, supplied in the repository snapshot. Source for the current schema, time split and transaction counts.
- The supplied `GraphML_roles.pdf` project brief.
- [Elliptic dataset](https://www.kaggle.com/datasets/ellipticco/elliptic-data-set).
- [scikit-learn average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).
- [scikit-learn F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html).
