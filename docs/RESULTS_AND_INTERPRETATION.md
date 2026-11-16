# Results and interpretation (Role 4)

This is the final comparison of every model the team trained, with explanations and an AML reading of the results. It covers 6 models × 5 seeds, 30 runs in total, all scored by the [Role 4 evaluator](ROLE4_EVALUATION.md) on the same test set.

**Sources:**
- Numbers: [`results/final_comparison/`](../results/final_comparison).
- Explanations: [`notebooks/role4_explainability.ipynb`](../notebooks/role4_explainability.ipynb).
- Per-role detail: [Role 2](ROLE2_BASELINE_RESULTS.md) and [Role 3](ROLE3_GNN_RESULTS.md).

## Summary

1. **Tree models on the transaction features are the best models.** Both Random Forests reach AP ≈ 0.79. The best GNN, a GCN, reaches 0.53.
2. **Training on the graph helps a neural network, but the trained GNN barely uses the edges at prediction time.** GCN beats an identical MLP (AP 0.53 vs 0.33). Yet removing every edge from the test graph does not lower its AP, and for GraphSAGE it raises it (Section 5).
3. **Every model fails after the dark-market shutdown at step 43.** F1 drops from 0.55–0.91 on steps 35–42 to 0.01–0.03 on steps 43–49. SHAP shows why: after the shutdown, the features that used to flag illicit activity point towards licit.
4. **How many alerts a model raises depends on calibration as much as on the model.** The two Random Forests catch about the same number of illicit transactions (791 vs 783), but at the same 0.50 threshold one raises 230 false alarms and the other 50.

## 1. What was compared

| | |
|---|---|
| Test set | Time steps 35–49, the 16,670 labelled transactions (1,083 illicit, 6.5%). Unknown labels are excluded. Every run has `manifest_sha256` `1116ca4b…1449` |
| Runs | Role 2 Random Forest; Role 3 Random Forest, GCN, GraphSAGE, GAT and MLP. Seeds 0–4 each |
| Training data | Random Forests: steps 1–34. GNNs and MLP: steps 1–29, with 30–34 used for early stopping and the threshold |
| Threshold policy | Each model keeps the rule it fixed **before** seeing test labels. The Random Forests use 0.50; the neural networks use the threshold that maximised F1 on validation. No threshold was tuned on test data. Thresholds differ between models, so **AP**, which needs no threshold, is the headline comparison. F1 is reported as each model's operating point |
| Where it ran | Role 2: locally, from the notebook. Role 3: re-run on the Bocconi HPC (`hpc/`). Evaluation and comparison: `src/role4_evaluation.py`, `src/role4_compare.py` |

## 2. Final comparison (test set, mean ± std over 5 seeds)

| Model | AP | Illicit F1 | Precision | Recall | Alerts | False alarms | Missed illicit | F1 35–42 | F1 43–49 |
|---|---|---|---|---|---|---|---|---|---|
| Random Forest (Role 2) | **0.788 ± 0.002** | 0.752 ± 0.005 | 0.775 | **0.730** | 1,021 | 230 | 292 | 0.874 | 0.020 |
| Random Forest (Role 3) | 0.783 ± 0.002 | **0.817 ± 0.002** | **0.940** | 0.723 | 833 | **50** | 300 | **0.906** | 0.031 |
| GCN | 0.532 ± 0.057 | 0.547 ± 0.029 | 0.685 | 0.456 | 721 | 228 | 590 | 0.630 | 0.013 |
| GraphSAGE | 0.471 ± 0.034 | 0.534 ± 0.016 | 0.523 | 0.548 | 1,139 | 546 | 490 | 0.615 | 0.017 |
| GAT | 0.446 ± 0.075 | 0.477 ± 0.045 | 0.506 | 0.459 | 997 | 500 | 586 | 0.545 | 0.022 |
| MLP (no graph) | 0.330 ± 0.042 | 0.503 ± 0.032 | 0.495 | 0.513 | 1,132 | 576 | 527 | 0.586 | 0.020 |

Alerts, false alarms and missed illicit are mean counts per run. "F1 35–42" and "F1 43–49" are pooled over those time steps. Per-run rows are in `runs.csv`.

**How this compares with Weber et al. (2019):** their Random Forest reached F1 0.788, against our 0.817 and 0.752. Their GCN reached 0.628, against our 0.547. They found the same collapse after step 43.

## 3. Reading the comparison

- **The Random Forests win on every measure that matters.** They give the best ranking (AP), the best F1 and the fewest missed illicit transactions, with very little seed-to-seed variation (std ≤ 0.005).
- **The two Random Forests rank transactions equally well but need different thresholds.** Their AP is almost the same, so the difference in F1 and false alarms comes from where 0.50 cuts each model's scores. The Role 2 model uses balanced class weights, which push its scores upwards. In deployment the threshold would be set from the number of cases investigators can review, not fixed at 0.50.
- **Among the neural networks, the graph helps.** All three GNNs beat the MLP on AP, and GCN does so by 0.20. GCN gives the most precise alerts, while GraphSAGE catches more illicit transactions at the cost of more false alarms. GAT is the least stable (AP std 0.075).

## 4. Why the models fail after step 43

SHAP values for the Role 2 Random Forest (seed 0). The sample is every illicit test transaction plus an equal number of licit ones.

- **Most of the signal comes from the transaction's own features.** Local features account for 75% of the total |SHAP|, although they are only 93 of the 165 features. The most important features are `feature_55`, `feature_53`, `feature_47`, `feature_41` and `feature_49`; the notebook has the chart.
- **After the shutdown, illicit transactions look licit to the model:**

| Illicit test transactions | Steps 35–42 (914) | Steps 43–49 (169) |
|---|---|---|
| Mean model score | 0.806 | **0.096** |
| Share flagged (score ≥ 0.50) | 86.4% | **1.8%** |
| SHAP contribution of `feature_55` | +0.039 | **−0.044** |
| SHAP contribution of `feature_53` | +0.024 | **−0.039** |
| SHAP contribution of `feature_47` | +0.024 | **−0.023** |

Each of the top 8 features changes sign in the same way. This is concept drift rather than a weak model. The illicit activity that remains after the market closed has a different feature profile from the illicit activity the models learned from, so they score it as licit. A model trained only on the past cannot recover that by itself. It needs fresh labels or monitoring that flags the change.

## 5. How the GNNs use the graph

**Graph ablation.** Each trained model scores the test graph twice: once as trained, and once with every edge removed (same weights). Seeds 0–4, trained on CPU with the Role 3 settings:

| Model | Test AP with edges | Test AP, all edges removed | Seeds where removal helped |
|---|---|---|---|
| GCN | 0.477 ± 0.074 | **0.509 ± 0.043** | 4 of 5 |
| GraphSAGE | 0.506 ± 0.015 | **0.564 ± 0.034** | 5 of 5 |

*Per seed: GCN 0.485/0.488, 0.485/0.481, 0.535/0.550, 0.352/0.467, 0.530/0.560; GraphSAGE 0.524/0.572, 0.493/0.579, 0.519/0.567, 0.491/0.506, 0.503/0.597. These CPU-trained models score a little below the HPC runs in Section 2, because training on CPU and GPU is not bit-identical. The comparison within each model is what matters here.*

Removing the edges does not lower AP; for GraphSAGE it raises it on every seed. The networks learned from the graph during training, but when predicting, neighbourhood messages in the test period add noise rather than signal. Test-period neighbourhoods include the post-shutdown drift and many unlabelled transactions.

**GNNExplainer** was run on the 5 illicit test transactions with the highest GCN score (seed 0):
- The explanations keep very few edges. Between 0 and 8 edges have a mask above 0.5, out of 6–1,190 edges in each 3-hop neighbourhood.
- The features with the largest mask weight are a mix of aggregated features (`feature_142`, `feature_143`, `feature_148`, `feature_112`) and local ones (`feature_2`, `feature_91`, `feature_55`).

Both views suggest that **the graph mainly helps during training.** Smoothing over neighbours regularises the network, which is why it beats the MLP. At prediction time the trained network relies on each transaction's own features, which already include 72 neighbourhood aggregates. Messages from neighbours add little or even hurt. This also explains why tree models on the same features do so well. It is consistent with Weber et al., where only Skip-GCN and EvolveGCN, which add structure beyond a plain GCN, came close to the Random Forest.

## 6. What this means for AML

- **A model is a triage tool, not a verdict.** Even the best model misses about 300 of 1,083 illicit transactions. More than half of those misses come after the shutdown. In Elliptic, "illicit" means the transaction belongs to a known illicit category (scams, malware, terrorist organisations, ransomware, Ponzi schemes), not proven laundering, and 77% of transactions have no label at all.
- **Alert volume is the real constraint.** At comparable recall, about 0.72–0.73, the Role 3 Random Forest asks investigators to review 833 transactions, 94% of them correct. The Role 2 Random Forest asks for 1,021, 78% correct. The threshold should be chosen from review capacity on recent validation data and revisited as the data changes.
- **Drift is the main operational risk.** One market closure was enough to make every model useless for the rest of the period. Any real use needs monitoring of score distributions and alert hit rates, plus regular retraining on newly labelled cases. Without them, performance can collapse silently.
- **Graph models need to earn their complexity.** On this dataset, where neighbourhood aggregates are already in the features, plain GNNs add cost without beating trees. They are more likely to help where the raw features are not pre-aggregated, or with temporal or skip-connection architectures. Those were not tested here.

## 7. Limitations

- One public dataset, with anonymised features, so explanations name feature numbers rather than economic quantities.
- Labels exist for 23% of transactions, and the test period contains only 169 illicit transactions after step 43.
- The models trained on different windows: Random Forests on 1–34, neural networks on 1–29. Little hyperparameter tuning was done.
- The degree feature (Role 2) and message passing (Role 3) assume each time step's whole graph is available at prediction time. This is a batch setting, not real time.
- GNNExplainer covers one seed and five transactions, and its masks are approximate. The ablation (`notebooks/role4_graph_ablation.py`) covers 5 seeds but was trained on CPU, which is not bit-identical to the HPC runs.

## Reproduce

```bash
python -m src.role1_split --data-dir <elliptic folder> --out tests/elliptic_split.csv   # Role 1 split (byte-identical)
jupyter nbconvert --execute notebooks/role2_baseline_models.ipynb                     # Role 2, 5 seeds + evaluation
cd hpc && sbatch job_r3.sh                                                             # Role 3 on the Bocconi HPC
python -m src.role4_evaluation --split-file tests/elliptic_split.csv --predictions <file> --model <name> --seed <s> --threshold <t> --outdir <dir>
python -m src.role4_compare <run dirs...> --outdir <dir>
jupyter nbconvert --execute notebooks/role4_explainability.ipynb                      # SHAP, ablation, GNNExplainer
python notebooks/role4_graph_ablation.py                                              # 5-seed graph ablation (~1 h CPU)
```
