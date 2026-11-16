# Graph ML for Finding Money Laundering

Can graph machine learning flag illicit Bitcoin transactions? This Bocconi Students Machine Learning (BSML) project uses the public [Elliptic dataset](https://www.kaggle.com/datasets/ellipticco/elliptic-data-set) (203,769 transactions, 234,355 payment flows, 49 time steps). It compares classical baselines with graph neural networks (GNNs) under a strict temporal split and a shared evaluation program.

## Results

Test set: time steps 35–49, 16,670 labelled transactions. The positive class is illicit.

| Model | Illicit F1 | AP | Details |
|---|---|---|---|
| Random Forest, raw features | **0.814 ± 0.002** | 0.783 | [Role 3](docs/ROLE3_GNN_RESULTS.md), 5 seeds |
| Random Forest, final baseline | 0.750 | **0.786** | [Role 2](docs/ROLE2_BASELINE_RESULTS.md), Role 4 evaluator |
| GCN | 0.558 ± 0.040 | 0.541 | Role 3 |
| GraphSAGE | 0.555 ± 0.022 | 0.491 | Role 3 |
| MLP (same network, no graph) | 0.507 ± 0.026 | 0.352 | Role 3 |
| GAT | 0.484 ± 0.030 | 0.417 | Role 3 |

**Findings:**
1. Tree ensembles on the 165 features are the strongest models, as in [Weber et al. (2019)](https://arxiv.org/abs/1908.02591).
2. Message passing does help a neural network: GCN beats an identical MLP by about 5 F1 points. It still does not catch up with the trees.
3. Every model fails after a large dark market shut down at time step 43. For example, the Role 2 RF reaches F1 0.87 on steps 35–42 and 0.02 on steps 43–49. Detecting this kind of change and retraining matter more than the choice of architecture.

The full comparison, the shared rules and the open questions are in [docs/PROJECT_PIPELINE.md](docs/PROJECT_PIPELINE.md).

## How the project is organised

| Role | Contribution | Main files |
|---|---|---|
| 1 – Data & exploration | Data card, shared temporal split (train 1–34 / test 35–49) | [`data/Final Data Card.html`](data/Final%20Data%20Card.html), [`tests/elliptic_split.csv`](tests/elliptic_split.csv) |
| 2 – Baselines | Logistic regression, Random Forest, XGBoost | [`notebooks/Role2_Baseline_Models_FINAL_CORRECTED.ipynb`](notebooks/Role2_Baseline_Models_FINAL_CORRECTED.ipynb) |
| 3 – Graph neural networks | MLP / GCN / GraphSAGE / GAT; RF with GCN embeddings | [`notebooks/role3_gnn_elliptic_final.ipynb`](notebooks/role3_gnn_elliptic_final.ipynb) |
| 4 – Evaluation | Evaluator with overall and per-step metrics, tests, CI | [`src/role4_evaluation.py`](src/role4_evaluation.py), [guide](docs/ROLE4_EVALUATION.md) |

```text
├── data/        # Data card; raw data is downloaded, never committed
├── docs/        # Results, pipeline overview, evaluation guide and validation
├── notebooks/   # Role 2 and Role 3 experiments (Google Colab)
├── src/         # Shared evaluator
└── tests/       # Shared split file, evaluator tests and fixtures
```

## Reproduce

1. **Notebooks.** Open them in Google Colab. Both download the dataset with `kagglehub`, which may ask for a Kaggle login.
   - Role 3 needs a T4 GPU and takes about 10–15 minutes.
   - Role 2 expects this repository at `MyDrive/ML-project-main` on Google Drive.
2. **Evaluator** (Python 3.12):

   ```bash
   python -m pip install -r requirements-evaluation.txt
   python -m unittest discover -s tests -p 'test_role4*.py'
   python -m src.role4_evaluation --split-file tests/elliptic_split.csv --predictions <scores.csv> --model <name> --seed 0 --threshold 0.50 --outdir outputs/<run>
   ```

   The prediction file format is described in [docs/ROLE4_EVALUATION.md](docs/ROLE4_EVALUATION.md).

## Data and ethics

- Raw data is downloaded from Kaggle and never committed. Elliptic's features are anonymised.
- `tests/elliptic_split.csv` contains transaction IDs, time steps and labels from the Elliptic dataset. Labels for the test period were used for evaluation only.
- A predicted label is a signal for human review. It is never an accusation or an automatic enforcement decision.
- Results come from a batch, research setting. Using this in real time would need separate checks of which information is available at prediction time.

## Team

| Member | GitHub | Role and contribution |
|---|---|---|
| Loukas Iatrou | [@LoukasIatrou](https://github.com/LoukasIatrou) | **Project lead.** Started the project, defined its objectives and the team roles, and set up the repository, collaboration rules and pull-request workflow. Coordinates the team, contributes to the baselines and GNNs, and wrote the integration and results documentation. |
| Ahaan Dhawan | [@ahaandhawan](https://github.com/ahaandhawan) | **Role 1 – Data preparation and exploration.** Preprocessed the dataset, did the exploratory analysis, built the chronological train/test split and wrote the data card. |
| Jessica Zainea Pop | [@zaineajessica-commits](https://github.com/zaineajessica-commits) | **Role 2 – Baseline models.** Built the classical machine-learning baselines (logistic regression, Random Forest, XGBoost), following Weber et al. (2019). |
| Gioia Cancian | [@Joey3383](https://github.com/Joey3383) | **Role 3 – Graph neural networks.** Built and trained the GNN architectures (GCN, GraphSAGE, GAT) to test whether graph structure improves illicit-transaction detection. |
| Giulio D'Aversa | [@mistergda06](https://github.com/mistergda06) | **Role 4 – Evaluation, explainability and AML context.** Built the shared evaluator, metrics, automated tests and CI, and wrote the AML background and explanation plan. |

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). The code and documentation are released under the [MIT License](LICENSE). The Elliptic dataset is covered by its own terms on Kaggle.
