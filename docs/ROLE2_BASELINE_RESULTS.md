# Role 2 – Baseline model results

Notebook: [`notebooks/Role2_Baseline_Models_FINAL_CORRECTED.ipynb`](../notebooks/Role2_Baseline_Models_FINAL_CORRECTED.ipynb). It is written for Google Colab with the repository copied to Google Drive.
How this fits with the other roles: [PROJECT_PIPELINE.md](PROJECT_PIPELINE.md).

The shared copy of the notebook has its outputs cleared. The numbers below come from running every code cell top to bottom on 2026-11-16. The run was local rather than in Colab: the Drive paths were pointed at a local clone and nothing else in the code changed. Libraries: Python 3.11, scikit-learn 1.8.0, XGBoost 3.2.0, pandas 2.2.3, NumPy 2.3.5. The test metrics come from the **Role 4 evaluator**.

## Setup

| Item | Value |
|---|---|
| Split | Read from [`tests/elliptic_split.csv`](../tests/elliptic_split.csv). Model selection: train on 1–29 (26,381 labelled) and validate on 30–34 (3,513). The final model is retrained on 1–34 (29,894 labelled) |
| Features | The 165 original features. One experiment adds the node's degree within its own time step |
| Models | Logistic regression (balanced class weights, standardised) · Random Forest (100 trees, depth 12, balanced class weights) · XGBoost (150 trees, depth 5, learning rate 0.1) |
| Threshold | Fixed at 0.50 |
| Seed | 0 |

## Validation (time steps 30–34)

| Model | Precision | Recall | F1 | AP |
|---|---|---|---|---|
| Logistic regression | 0.357 | 0.980 | 0.523 | 0.585 |
| **Random Forest** | 0.968 | 0.961 | **0.964** | **0.987** |
| XGBoost | 0.977 | 0.799 | 0.879 | 0.984 |
| Random Forest + degree | 0.961 | 0.963 | 0.962 | 0.985 |

The Random Forest is selected. Adding the degree feature does not help, because the 72 aggregated features already describe each transaction's neighbourhood. Validation scores are much higher than test scores because validation falls before the step-43 shift and has a high share of illicit transactions (16.8%).

## Test (time steps 35–49), Role 4 evaluator

| Model | Precision | Recall | F1 | AP | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|
| Random Forest (final, retrained on 1–34) | 0.769 | 0.732 | **0.750** | **0.786** | 793 | 238 | 290 | 15,349 |

The evaluator scored all 16,670 labelled test transactions (1,083 illicit). `manifest_sha256` = `1116ca4b51a72ecf72bdc7577d8f305f7f65e52ab6610b5d5dfc458f51771449`. Other runs must report this same value to show they used the same test set.

### By time step

| Time steps | TP | FP | FN | F1 (pooled) |
|---|---|---|---|---|
| 35–42 | 790 | 110 | 124 | **0.871** |
| 43–49 (after the dark-market shutdown) | 3 | 128 | 166 | **0.020** |

F1 is 0.72–0.95 at every step from 35 to 42. From step 43 onwards the model misses almost every illicit transaction. This is the same collapse that Role 3 found and that the Role 1 data card warned about.

## Notes

- This is a single seed. The Role 3 RF results suggest that variation across seeds is small (±0.002 F1).
- Role 3 also trains a Random Forest, with different settings, and gets F1 0.814 ± 0.002 and AP 0.783. The two Random Forests reach almost the same AP but clearly different F1 at threshold 0.50. That points to calibration: balanced class weights in Role 2 vs none in Role 3. Ranking quality is about the same.
- The degree feature assumes the whole graph of each time step is available at prediction time. This is a batch setting.
