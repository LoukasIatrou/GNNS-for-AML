# Graph ML for Finding Money Laundering

Can graph machine learning flag illicit Bitcoin transactions? This Bocconi Students Machine Learning (BSML) project uses the public [Elliptic dataset](https://www.kaggle.com/datasets/ellipticco/elliptic-data-set) (203,769 transactions, 234,355 payment flows, 49 time steps). It compares classical baselines with graph neural networks (GNNs) under a strict temporal split and a shared evaluation program.

## Results

Test set: time steps 35–49, 16,670 labelled transactions, positive class illicit. Every run was scored by the shared Role 4 evaluator on the same test set. Values are means over 5 seeds.

| Model | AP | Illicit F1 | F1, steps 35–42 | F1, steps 43–49 |
|---|---|---|---|---|
| Random Forest (Role 2) | **0.788 ± 0.002** | 0.752 ± 0.005 | 0.874 | 0.020 |
| Random Forest (Role 3) | 0.783 ± 0.002 | **0.817 ± 0.002** | **0.906** | 0.031 |
| GCN | 0.532 ± 0.057 | 0.547 ± 0.029 | 0.630 | 0.013 |
| GraphSAGE | 0.471 ± 0.034 | 0.534 ± 0.016 | 0.615 | 0.017 |
| GAT | 0.446 ± 0.075 | 0.477 ± 0.045 | 0.545 | 0.022 |
| MLP (same network, no graph) | 0.330 ± 0.042 | 0.503 ± 0.032 | 0.586 | 0.020 |

**Findings** (details in [docs/RESULTS_AND_INTERPRETATION.md](docs/RESULTS_AND_INTERPRETATION.md)):
1. Tree ensembles on the 165 transaction features are the strongest models, as in [Weber et al. (2019)](https://arxiv.org/abs/1908.02591).
2. Training on the graph helps a neural network: GCN reaches AP 0.53 vs 0.33 for an identical MLP. The trained GNN, however, does not need the edges at prediction time: removing them from the test graph does not lower its AP.
3. Every model fails after a large dark market shut down at time step 43. SHAP shows that the features that flagged illicit activity before the shutdown point towards licit afterwards. This is concept drift, so monitoring and retraining matter more than the choice of architecture.
4. The two Random Forests catch the same share of illicit transactions, but at threshold 0.50 one raises 230 false alarms per run and the other 50. Calibration and threshold choice decide how much work investigators get.

## How the project is organised

| Role | Contribution | Main files |
|---|---|---|
| 1 – Data & exploration | Data card, shared temporal split (train 1–34 / test 35–49), script that rebuilds the split | [`data/Final Data Card.html`](data/Final%20Data%20Card.html), [`tests/elliptic_split.csv`](tests/elliptic_split.csv), [`src/role1_split.py`](src/role1_split.py) |
| 2 – Baselines | Logistic regression, Random Forest, XGBoost | [`notebooks/role2_baseline_models.ipynb`](notebooks/role2_baseline_models.ipynb), [results](docs/ROLE2_BASELINE_RESULTS.md) |
| 3 – Graph neural networks | MLP / GCN / GraphSAGE / GAT; RF with GCN embeddings | [`notebooks/role3_gnn_elliptic.ipynb`](notebooks/role3_gnn_elliptic.ipynb), [`hpc/`](hpc), [results](docs/ROLE3_GNN_RESULTS.md) |
| 4 – Evaluation & explainability | Evaluator, comparison across runs, SHAP / GNNExplainer, AML interpretation, tests, CI | [`src/role4_evaluation.py`](src/role4_evaluation.py), [`src/role4_compare.py`](src/role4_compare.py), [`notebooks/role4_explainability.ipynb`](notebooks/role4_explainability.ipynb), [results](docs/RESULTS_AND_INTERPRETATION.md) |

How the roles feed into each other: [docs/PROJECT_PIPELINE.md](docs/PROJECT_PIPELINE.md).

```text
├── data/        # Data card; raw data is downloaded, never committed
├── docs/        # Results, interpretation, pipeline overview, evaluation guide
├── hpc/         # SLURM scripts for the Role 3 re-run on the Bocconi HPC
├── notebooks/   # Role 2, Role 3 and Role 4 notebooks (Colab or local)
├── report/      # Final report (BSFS format), its build script and figures
├── results/     # Final comparison and explainability tables
├── src/         # Split builder, evaluator, comparison tool
└── tests/       # Shared split file, tests and fixtures
```

## Reproduce

1. **Split** (optional; the committed file is byte-identical): `python -m src.role1_split --data-dir <elliptic folder> --out tests/elliptic_split.csv`
2. **Notebooks.** Run them in Google Colab or locally. They download the dataset with `kagglehub`, which may ask for a Kaggle login.
   - Role 2 runs on CPU in a few minutes. In Colab it expects this repository at `MyDrive/ML-project-main`.
   - Role 3 needs a GPU: about 10–15 minutes on a Colab T4, or about 3 minutes with [`hpc/job_r3.sh`](hpc/job_r3.sh) on the Bocconi HPC.
   - The Role 4 explainability notebook runs on CPU in about 10 minutes.
3. **Evaluate and compare** (Python 3.12):

   ```bash
   python -m pip install -r requirements-evaluation.txt
   python -m unittest discover -s tests -p 'test_role*.py'
   python -m src.role4_evaluation --split-file tests/elliptic_split.csv --predictions <scores.csv> --model <name> --seed 0 --threshold 0.50 --outdir outputs/<run>
   python -m src.role4_compare outputs/<run> outputs/<other run> ... --outdir outputs/comparison
   ```

   The prediction file format is described in [docs/ROLE4_EVALUATION.md](docs/ROLE4_EVALUATION.md).
4. **Report:** `python report/make_figures.py` then `python report/build_report.py` rebuild [the final report](report/Graph_ML_Money_Laundering_Report.docx) from `results/`.

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
