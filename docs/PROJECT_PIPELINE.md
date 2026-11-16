# How the four roles connect

One dataset, one split, one scoring program. Each role builds on what the previous role produced.

```text
Role 1  Data & exploration          ->  data card + tests/elliptic_split.csv (train 1-34 / test 35-49)
           |
           +--> Role 2  Baselines (no message passing)   --+
           |                                               +-->  per-transaction scores (txId, score_illicit)
           +--> Role 3  Graph neural networks            --+
                                                           |
Role 4  Evaluation  <--------------------------------------+  src/role4_evaluation.py: same IDs, metrics, per-step results
```

| Role | Produces | Where | Status |
|---|---|---|---|
| 1 – Data | Data card, shared split file (`txId, time_step, class, split`) | [`data/Final Data Card.html`](../data/Final%20Data%20Card.html), [`tests/elliptic_split.csv`](../tests/elliptic_split.csv) | Done, on `main` |
| 2 – Baselines | Logistic regression, Random Forest and XGBoost; RF + graph degree; final RF scores | `notebooks/Role2_Baseline_Models_FINAL_CORRECTED.ipynb` on branch `role2-baseline-models` | Code ready, **not merged**. Outputs are cleared, so no numbers are recorded yet |
| 3 – GNNs | MLP, GCN, GraphSAGE and GAT over 5 seeds; RF with and without GCN embeddings | [`notebooks/role3_gnn_elliptic_final.ipynb`](../notebooks/role3_gnn_elliptic_final.ipynb), [results](ROLE3_GNN_RESULTS.md) | Done; results are in the notebook. **Not yet run through the Role 4 evaluator** |
| 4 – Evaluation | Evaluator, tests, CI, AML context | [`src/role4_evaluation.py`](../src/role4_evaluation.py), [guide](ROLE4_EVALUATION.md) | Done, on `main` |

## The common thread

| Decision | Role 1 sets | Role 2 follows | Role 3 follows | Role 4 enforces |
|---|---|---|---|---|
| Time split | 1–34 / 35–49 | Reads the split file | Rebuilds the same split from `time_step`; the counts match | Builds the test set from the split file |
| Validation | – | 1–29 / 30–34, then retrains on 1–34 | 1–29 / 30–34 for the GNNs; the RF trains on 1–34 | Recommends this; still an open team decision |
| Unknown labels | 77% unlabelled; keep them in the graph, never score them | Dropped | Used for message passing only | Removed from the metrics |
| Test set | 16,670 labelled test transactions | 16,670 scores, checked with an assert | 16,670 labelled test nodes | Rejects missing or extra IDs |
| Main metrics | Not accuracy; use illicit F1 / PR-AUC | P, R, F1, AP | P, R, F1, AP (labelled "PR-AUC") | P, R, F1, AP plus confusion counts, overall and per step |
| Threshold | – | 0.50 | GNNs: tuned on validation and frozen; RF: 0.50 | `score >= threshold`, the value given on the command line |
| Drift at step 43 | Pointed out in the data card | – | Confirmed: every model drops to F1 ≈ 0 | Per-step output makes this visible |

## Results so far (test set, steps 35–49, illicit class)

| Model | Role | Illicit F1 | PR-AUC / AP | Source |
|---|---|---|---|---|
| Random Forest, raw features | 3 | **0.814 ± 0.002** | **0.783** | Role 3 notebook, 5 seeds |
| Random Forest + GCN embeddings | 3 | 0.758 ± 0.015 | 0.740 | Role 3 notebook |
| GCN | 3 | 0.558 ± 0.040 | 0.541 | Role 3 notebook |
| GraphSAGE | 3 | 0.555 ± 0.022 | 0.491 | Role 3 notebook |
| MLP (no graph) | 3 | 0.507 ± 0.026 | 0.352 | Role 3 notebook |
| GAT | 3 | 0.484 ± 0.030 | 0.417 | Role 3 notebook |
| Random Forest (final baseline) | 2 | pending | pending | Run the notebook, then the Role 4 evaluator |
| Weber et al. (2019): RF / GCN / EvolveGCN | paper | 0.788 / 0.628 / 0.720 | – | arXiv:1908.02591 |

**What the evidence shows so far:**
- Tree models on the 165 features are the strongest models.
- Message passing helps a neural network: GCN beats the MLP by about 5 F1 points and 0.19 PR-AUC. It still does not catch up with the trees.
- Every model fails after the dark-market shutdown at step 43, as the data card warned. Detecting drift and retraining matter more than the choice of architecture.

## What is still needed to compare everything with the Role 4 evaluator

1. **Role 2:** merge `role2-baseline-models` and record the evaluator output (`overall_metrics.csv`).
2. **Role 3:** export per-node scores with the snippet in [ROLE3_GNN_RESULTS.md](ROLE3_GNN_RESULTS.md#exported-files-and-role-4-evaluation), then run the evaluator for each model and seed.
3. **Compare `manifest_sha256`** across all runs to confirm they were scored on the same test set.
4. **Agree on the threshold policy.** Either every model uses 0.50, or every model uses a threshold tuned on validation. AP does not depend on the threshold and is the fairest headline comparison until this is decided.
5. **Agree on the training window.** The Role 3 GNNs train on 1–29, while both RFs train on 1–34. Either retrain the GNNs on 1–34 or report the difference.
6. Note that the Role 2 RF and the Role 3 RF use different settings:
   - Role 2: depth 12, balanced class weights.
   - Role 3: `max_features=50`, no class weights, standardised inputs.
   They are two baselines, not the same model run twice.
7. **Role 4 write-up:** report steps 35–42 and 43–49 separately, using the per-step output.
