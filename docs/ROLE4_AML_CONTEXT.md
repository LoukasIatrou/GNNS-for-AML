# AML background and final analysis plan

This is initial background and a plan for the later Role 4 analysis. It contains no findings about trained models.

## Why this project matters

AML means anti-money laundering. Money laundering disguises where criminal proceeds came from so that they can appear legitimate. UNODC describes it as a process that hides the illegal origin of funds [1].

This project asks whether machine learning can identify transactions labelled illicit in the Elliptic Bitcoin dataset, and whether using transaction connections helps. Weber et al. introduced this benchmark and compared conventional classifiers with graph convolutional methods [2]. Their work motivates our comparison; it does not establish that our graph models will outperform our baselines.

A graph represents transactions as nodes and payment flows as connections. Transaction characteristics describe an individual transaction; graph methods can also use relationships between transactions. The team's experiment will assess whether those relationships improve detection on later time periods.

## What detection errors mean

A false negative is an illicit-labelled transaction the model misses. A false positive is a licit-labelled transaction incorrectly flagged. Better recall finds more of the known illicit cases; better precision reduces incorrect alerts among the flagged cases. Both matter when an investigator has limited time to review alerts.

We will describe this trade-off using the shared evaluation outputs. We do not have review-cost or investigation-outcome data, so we will not claim monetary savings, a measured reduction in crime or a proven operational workload benefit.

The task predicts dataset labels. A prediction does not prove that a particular person committed money laundering. Unknown labels remain unknown, and results on the labelled subset need not represent every unlabelled transaction or a production environment.

## How we will explain predictions after training

The brief asks Role 4 to explain what drives the models' decisions. The evaluator alone does not meet that later requirement.

| Model type | Planned explanation | What it should show |
|---|---|---|
| A selected baseline | A suitable SHAP explainer for the fitted model [3] | Which input features contributed to selected model outputs. |
| A selected GNN | A PyG explanation method such as GNNExplainer, matched to the team's installed version [4] | Which model input features or graph connections influenced selected predictions. |

Select documented examples of correct detections, false alarms and missed cases. Record how cases were chosen and include different test periods where possible. Avoid presenting only the most visually convincing examples.

For SHAP, record the model, feature order and a documented reference sample from training data. For a graph explanation, retain the node ID mapping, graph inputs, target node/class and explanation settings. Keep the trained model and preprocessing fixed while analysing test predictions.

The team's data card says the transaction features are anonymised. When their meaning is unknown, describe contributions using their actual feature identifiers rather than inventing financial meanings. These methods explain model behaviour; predictive contributions alone do not establish causes of criminal activity.

### What Roles 2 and 3 must retain

- The fitted model or checkpoint and the code needed to load it.
- The exact input features and their order, with the fitted preprocessing.
- For a GNN, graph inputs and the mapping from transaction IDs to model node indices.
- Class ordering, split, training seed, package versions and the selected alert threshold.

The predictions CSV is sufficient for scoring but not for these model explanations. Explanation dependencies will be chosen after the actual models and PyG version are available; the evaluation script does not currently install or run SHAP or PyG.

## Final report and presentation outline

Role 4 coordinates the write-up using contributions from the other roles.

| Section | Content and owner |
|---|---|
| Abstract and research question | The comparison question; add the main finding only after obtaining real results. |
| AML background | Adapt this introduction and cite its sources. |
| Data | Role 1's dataset description, unknown labels and chronological split. |
| Models | Roles 2 and 3 describe the baselines, graph information, GNN architectures and training choices. |
| Evaluation | Shared metrics, threshold policy, test population, information access and repeated-run protocol. |
| Results | Actual model comparison, test-period figures and variation across training seeds. |
| Explainability | Selected baseline and GNN examples, with clearly stated interpretation limits. |
| Limitations and conclusions | Label coverage, anonymous features, temporal change, graph access and what the experiment supports. |

Use the supplied BSFS Word and PowerPoint examples for the final report and slides. Their topics, author names and factual claims must be replaced with this project's actual content. The current code/documentation package is not the final report or presentation.

## Sources

[1] UNODC. Organized Crime Module 4, Money Laundering. https://www.unodc.org/e4j/en/organized-crime/module-4/key-issues/money-laundering.html

[2] Weber et al. (2019). Anti-Money Laundering in Bitcoin: Experimenting with Graph Convolutional Networks for Financial Forensics. https://arxiv.org/abs/1908.02591

[3] SHAP documentation. https://shap.readthedocs.io/en/latest/

[4] PyTorch Geometric explanation documentation. https://pytorch-geometric.readthedocs.io/en/latest/modules/explain.html

Project-specific facts and responsibilities also come from the supplied GraphML_roles.pdf and data/Final Data Card.html.
