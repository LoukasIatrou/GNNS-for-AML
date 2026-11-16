# Role 2 – Baseline model results

Notebook: [`notebooks/role2_baseline_models.ipynb`](../notebooks/role2_baseline_models.ipynb). It runs in Google Colab, with the repository copied to Drive as `MyDrive/ML-project-main`, or locally from a clone.
How this fits with the other roles: [PROJECT_PIPELINE.md](PROJECT_PIPELINE.md). The combined comparison is in [RESULTS_AND_INTERPRETATION.md](RESULTS_AND_INTERPRETATION.md).

The saved outputs in the notebook come from running it top to bottom locally on 2026-11-16. Libraries: Python 3.11, scikit-learn 1.8.0, XGBoost 3.2.0, pandas 2.2.3, NumPy 2.3.5. The test metrics come from the **Role 4 evaluator**.

## Setup

| Item | Value |
|---|---|
| Split | Read from [`tests/elliptic_split.csv`](../tests/elliptic_split.csv). Model selection: train on 1–29 (26,381 labelled) and validate on 30–34 (3,513). The final model is retrained on 1–34 (29,894 labelled) |
| Features | The 165 original features. One experiment adds the node's degree within its own time step |
| Models | Logistic regression (balanced class weights, standardised) · Random Forest (100 trees, depth 12, balanced class weights) · XGBoost (150 trees, depth 5, learning rate 0.1) |
| Threshold | Fixed at 0.50, the same for every model and seed |
| Seeds | Model selection: seed 0. Final Random Forest: seeds 0–4, the same seeds as Role 3 |

## Validation (time steps 30–34, seed 0)

| Model | Precision | Recall | F1 | AP |
|---|---|---|---|---|
| Logistic regression | 0.357 | 0.980 | 0.523 | 0.585 |
| **Random Forest** | 0.968 | 0.961 | **0.964** | **0.987** |
| XGBoost | 0.977 | 0.799 | 0.879 | 0.984 |
| Random Forest + degree | 0.961 | 0.963 | 0.962 | 0.985 |

The Random Forest is selected. Adding the degree feature does not help, because the 72 aggregated features already describe each transaction's neighbourhood. Validation scores are much higher than test scores because validation falls before the step-43 shift and has a high share of illicit transactions (16.8%).

## Test (time steps 35–49), Role 4 evaluator, 5 seeds

| Seed | Precision | Recall | F1 | AP | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| 0 | 0.769 | 0.732 | 0.750 | 0.786 | 793 | 238 | 290 |
| 1 | 0.773 | 0.728 | 0.750 | 0.785 | 788 | 231 | 295 |
| 2 | 0.796 | 0.728 | 0.760 | 0.788 | 788 | 202 | 295 |
| 3 | 0.768 | 0.727 | 0.747 | 0.788 | 787 | 238 | 296 |
| 4 | 0.769 | 0.736 | 0.752 | 0.791 | 797 | 239 | 286 |
| **Mean ± std** | 0.775 ± 0.012 | 0.730 ± 0.004 | **0.752 ± 0.005** | **0.788 ± 0.002** | | | |

Every run was scored on the same 16,670 labelled test transactions (1,083 illicit). `manifest_sha256` = `1116ca4b51a72ecf72bdc7577d8f305f7f65e52ab6610b5d5dfc458f51771449`, the same value as every Role 3 run.

### Before and after the dark-market shutdown

| Time steps | F1 (pooled, mean of 5 seeds) |
|---|---|
| 35–42 | **0.874 ± 0.005** |
| 43–49 | **0.020 ± 0.001** |

Before step 43 the model works well. After it, the model misses almost every illicit transaction. The SHAP analysis in [RESULTS_AND_INTERPRETATION.md](RESULTS_AND_INTERPRETATION.md#4-why-the-models-fail-after-step-43) shows why: the features that flagged illicit activity before the shutdown point the other way afterwards.

## Notes

- Role 3 also trains a Random Forest, with different settings (`max_features=50`, no class weights, standardised inputs), and gets AP 0.783 and F1 0.817. The two Random Forests rank transactions about equally well (AP 0.788 vs 0.783). At threshold 0.50, though, the Role 2 model raises 4–5 times as many false alarms (≈230 vs ≈50) for the same recall. The balanced class weights push its scores upwards.
- The degree feature assumes the whole graph of each time step is available at prediction time. This is a batch setting.
