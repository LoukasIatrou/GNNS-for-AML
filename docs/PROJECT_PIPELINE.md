# How the four roles connect

One dataset, one split, one scoring program. Each role builds on what the previous role produced.

```text
Role 1  Data & exploration   ->  data card + tests/elliptic_split.csv (train 1-34 / test 35-49)
           |                     rebuilt by src/role1_split.py
           +--> Role 2  Baselines (no message passing)   --+
           |                                               +-->  per-transaction scores (txId, score_illicit)
           +--> Role 3  Graph neural networks            --+     one file per model and seed
                                                           |
Role 4  Evaluation  <--------------------------------------+  src/role4_evaluation.py  (one run)
                                                              src/role4_compare.py     (all runs, same test set)
                                                              notebooks/role4_explainability.ipynb
```

| Role | Produces | Where | Status |
|---|---|---|---|
| 1 – Data | Data card, shared split file (`txId, time_step, class, split`), script that rebuilds the split | [`data/Final Data Card.html`](../data/Final%20Data%20Card.html), [`tests/elliptic_split.csv`](../tests/elliptic_split.csv), [`src/role1_split.py`](../src/role1_split.py) | Done. The rebuilt file is byte-identical to the committed one |
| 2 – Baselines | Logistic regression, Random Forest and XGBoost; RF + graph degree; final RF over 5 seeds | [`notebooks/role2_baseline_models.ipynb`](../notebooks/role2_baseline_models.ipynb), [results](ROLE2_BASELINE_RESULTS.md) | Done; evaluated with Role 4 |
| 3 – GNNs | MLP, GCN, GraphSAGE and GAT; RF with and without GCN embeddings; 5 seeds | [`notebooks/role3_gnn_elliptic.ipynb`](../notebooks/role3_gnn_elliptic.ipynb), [`hpc/`](../hpc), [results](ROLE3_GNN_RESULTS.md) | Done; re-run on the Bocconi HPC and evaluated with Role 4 |
| 4 – Evaluation | Evaluator, comparison tool, explanations, AML interpretation, final report | [`src/`](../src), [`notebooks/role4_explainability.ipynb`](../notebooks/role4_explainability.ipynb), [results and interpretation](RESULTS_AND_INTERPRETATION.md), [`report/`](../report) | Done; report draft ready, slides still to do |

## The common thread

| Decision | Role 1 sets | Role 2 follows | Role 3 follows | Role 4 enforces |
|---|---|---|---|---|
| Time split | 1–34 / 35–49 | Reads the split file | Rebuilds the same split from `time_step`; the counts match | Builds the test set from the split file |
| Validation | – | 1–29 / 30–34, then retrains on 1–34 | 1–29 / 30–34 for the GNNs; the RF trains on 1–34 | Records each model's training window |
| Unknown labels | 77% unlabelled; keep them in the graph, never score them | Dropped | Used for message passing only | Removed from the metrics |
| Test set | 16,670 labelled test transactions | 16,670 scores per seed | 16,670 scores per model and seed | All 30 runs share `manifest_sha256` `1116ca4b…1449` |
| Metrics | Not accuracy; use illicit F1 / AP | P, R, F1, AP | P, R, F1, AP | P, R, F1, AP plus confusion counts, overall and per step, and F1 before and after step 43 |
| Threshold | – | 0.50 | GNNs: tuned on validation and frozen; RF: 0.50 | Fixed before seeing test labels; AP is the headline because it needs no threshold |
| Seeds | – | 0–4 | 0–4 | Mean ± std over seeds |
| Drift at step 43 | Pointed out in the data card | Confirmed (F1 0.87 → 0.02) | Confirmed for every model | Explained with SHAP |

## Results

Full table and interpretation: [RESULTS_AND_INTERPRETATION.md](RESULTS_AND_INTERPRETATION.md). Headline (test set, mean of 5 seeds):

| Model | AP | Illicit F1 |
|---|---|---|
| Random Forest (Role 2) | **0.788** | 0.752 |
| Random Forest (Role 3) | 0.783 | **0.817** |
| GCN | 0.532 | 0.547 |
| GraphSAGE | 0.471 | 0.534 |
| GAT | 0.446 | 0.477 |
| MLP (no graph) | 0.330 | 0.503 |

## Still open

1. **Final report:** the draft in BSFS format is [`report/Graph_ML_Money_Laundering_Report.docx`](../report/Graph_ML_Money_Laundering_Report.docx), rebuilt by `report/build_report.py`. Still to do: fill in the highlighted `[TODO]` items (degree programmes, two optional AML paragraphs) and write the slides.
2. **Optional experiments** suggested by the results:
   - GNNs retrained on 1–34.
   - Local features only.
   - Skip-GCN or EvolveGCN.
   - Out-of-fold GNN embeddings for the RF.
3. **Dataset terms.** Confirm that Elliptic's terms allow republishing `tests/elliptic_split.csv`. If they don't, delete it and let users rebuild it with `src/role1_split.py`.
