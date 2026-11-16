# Role 3 – Graph neural network results

Notebook: [`notebooks/role3_gnn_elliptic_final.ipynb`](../notebooks/role3_gnn_elliptic_final.ipynb) (Colab, T4 GPU, about 10–15 min).
How this fits with the other roles: [PROJECT_PIPELINE.md](PROJECT_PIPELINE.md).

## Research question

Does learning on the Bitcoin transaction graph with GNNs work better than models that look at each transaction on its own?

**Short answer:**
- **Compared with the same network without the graph, yes.** GCN and GraphSAGE beat an MLP of the same size by about 5 F1 points, and GCN raises PR-AUC from 0.35 to 0.54.
- **Compared with a Random Forest on the raw features, no.** The Random Forest reaches F1 0.81. The best GNN reaches 0.56.
- **After the dark-market shutdown at time step 43, every model stops working.**

## Setup

| Item | Value |
|---|---|
| Data | Elliptic, as described in the Role 1 [data card](../data/Final%20Data%20Card.html): 203,769 nodes, 234,355 edges made undirected, 165 features |
| Split | Role 1 boundary: train on time steps 1–34, test on 35–49. Inside training, GNNs train on 1–29 and use 30–34 for **validation** |
| Labelled nodes | train 26,381 (10.9% illicit) · validation 3,513 (16.8%) · test **16,670** (6.5%). The 16,670 test nodes are the same set Role 4 evaluates |
| Leakage control | Each period is a separate subgraph, so the model never sees test nodes during training. Features are standardised with training statistics only. Elliptic has no edges between time steps, so no edges are lost |
| Models | MLP (control, no graph) · GCN · GraphSAGE · GAT. All have 2 layers of width 64, dropout 0.3 |
| Training | Adam, learning rate 5e-3, weight decay 5e-4. Weighted cross-entropy (licit ≈0.56, illicit ≈4.59). Early stopping on validation PR-AUC with patience 50 and at most 500 epochs |
| Threshold | GNNs and MLP: the threshold that maximises F1 on validation, kept fixed for the test set. Random Forest: 0.5 |
| Metrics | Illicit-class F1, precision and recall. PR-AUC is computed with `average_precision_score`, the same AP that Role 4 uses |
| Seeds | 0–4. Results are mean ± std |

## Results: GNNs vs MLP (test set, 5 seeds)

| Model | Illicit F1 | Precision | Recall | PR-AUC |
|---|---|---|---|---|
| MLP (no graph) | 0.507 ± 0.026 | 0.493 | 0.525 | 0.352 ± 0.039 |
| **GCN** | **0.558 ± 0.040** | **0.681** | 0.474 | **0.541 ± 0.044** |
| **GraphSAGE** | 0.555 ± 0.022 | 0.557 | **0.557** | 0.491 ± 0.017 |
| GAT | 0.484 ± 0.030 | 0.487 | 0.484 | 0.417 ± 0.093 |

- **The graph adds value.** The gap between GCN or GraphSAGE and the MLP is larger than the standard deviation across seeds.
- **GCN and GraphSAGE make different trade-offs.** GCN gives the most precise alerts. GraphSAGE catches more illicit transactions and varies least across seeds. Which one is better depends on how many cases investigators can review.
- **GAT is the weakest and least stable model.** Its PR-AUC ranges from 0.30 to 0.52 across seeds, and it would need its own tuning.

## Results by time step

Time steps 35–42 give F1 of about 0.3–0.8, with GCN and SAGE usually above the MLP. **From time step 43 onwards, every model drops to F1 ≈ 0**, with one partial recovery at step 46. This repeats the main finding of Weber et al. (2019): illicit behaviour changes after the dark-market shutdown. The overall test F1 therefore mixes a period when the models work with a period when they fail.

## Random Forest and GNN embeddings

| Model | Illicit F1 | PR-AUC |
|---|---|---|
| RF on raw features (`rf_raw`) | **0.814 ± 0.002** | **0.783 ± 0.002** |
| RF on raw features + GCN embeddings | 0.758 ± 0.015 | 0.740 ± 0.013 |

The RF has 100 trees and `max_features=50`. It trains on all of 1–34 with threshold 0.5. The GCN embeddings make the RF **worse**. The likely reason is that the GCN was fitted on the same training labels, so its embeddings look more reliable on training nodes than they are on test nodes. Out-of-fold embeddings would make this comparison fair.

## Comparison with Weber et al. (2019)

| Model | Paper F1 | Our F1 |
|---|---|---|
| Random Forest (all features) | 0.788 | **0.814 ± 0.002** |
| Random Forest + GCN embeddings | 0.796 | 0.758 ± 0.015 |
| MLP | 0.653 | 0.507 ± 0.026 |
| GCN | 0.628 | 0.558 ± 0.040 |
| Skip-GCN / EvolveGCN | 0.705 / 0.720 | not run |

**Where we agree with the paper:** the RF wins, all models collapse after step 43, and GCN has higher precision than recall. Our RF result is close to the paper's, which suggests the pipeline and split are correct.
**Where we differ:** our neural networks score lower than the paper's. Possible reasons:
- They train on 1–29 instead of 1–34.
- The threshold is tuned on validation, where 16.8% of nodes are illicit, but only 6.5% of test nodes are.
- The hyperparameters differ from the paper's.

## Limitations

- Little hyperparameter tuning. All architectures share the same settings.
- GNNs see 29 training time steps and the RF sees 34, which puts the GNNs at a small disadvantage.
- GPU non-determinism means exact numbers can vary slightly between runs.
- The features are anonymised, so the predictions cannot be explained in economic terms.
- **The metrics were computed inside the notebook, not yet with the Role 4 evaluator.** See the next section.

## Exported files and Role 4 evaluation

Section 10 of the notebook writes `role3_gnn_results.csv`, `role3_gnn_per_timestep.csv`, `role3_rf_embeddings_results.csv` and `role3_comparison_with_weber2019.csv`. These are summary tables, not the per-transaction score files that the [Role 4 evaluator](ROLE4_EVALUATION.md) needs.

To evaluate with Role 4, add this cell after Section 5 and re-run the notebook:

```python
from pathlib import Path
out = Path("role4_predictions"); out.mkdir(exist_ok=True)
# make_graph keeps df's node order, so these are the 16,670 labelled test IDs
test_ids = df.loc[df["time_step"] >= TEST_START, "txId"].astype(str).values[test_g.labeled.cpu().numpy()]
for (kind, s), m in trained.items():
    p, _, _ = predict(m, test_g)
    pd.DataFrame({"txId": test_ids, "score_illicit": p}).to_csv(out / f"{kind}_seed{s}_predictions.csv", index=False)
res_df[["model", "seed", "threshold"]].to_csv(out / "thresholds.csv", index=False)
```

Then evaluate each file with its own validation threshold from `thresholds.csv`. The evaluator also uses `score >= threshold`:

```bash
python -m src.role4_evaluation --split-file tests/elliptic_split.csv --predictions role4_predictions/gcn_seed0_predictions.csv --model GCN --seed 0 --threshold <threshold> --outdir outputs/role4/gcn_seed0
```

## Next steps, most useful first

1. Retrain the GNNs on all of 1–34, using the number of epochs found by early stopping.
2. Use local features only (`FEATURES = LOCAL_FEATS`), where message passing should help more.
3. Try Skip-GCN, which gained about 8 points in the paper.
4. Compute out-of-fold GNN embeddings for the RF.
5. Tune the class weights and the threshold.
6. Try temporal GNNs such as EvolveGCN.
7. Report F1 separately for steps 35–42 and 43–49, together with Role 4.
