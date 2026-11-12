# GRAPH ML for Finding Money Laundering

This repository contains the team project for detecting potential money-laundering patterns with graph machine learning. We model entities and transactions as a graph, build reproducible baselines, and evaluate models responsibly.

> **Project status:** setup phase. Replace the placeholders in [Project plan](#project-plan) before the first sprint.

## Goals

_To be defined by the project lead._

## Repository map

```text
├── data/                 # Local data only; never commit raw or sensitive data
│   ├── raw/              # Immutable source data
│   ├── interim/          # Temporary transformed data
│   └── processed/        # Model-ready data (commit only small, approved examples)
├── docs/                 # Design notes, meeting notes, data dictionary
├── notebooks/            # Exploratory work; promote reusable code into src/
├── src/                  # Reusable project code
├── tests/                # Automated checks for src/
├── .github/              # GitHub templates and contribution workflow
└── README.md
```

## Start here — zero-GitHub setup

1. Create a free account at [github.com](https://github.com) and tell the project lead your GitHub username.
2. Accept the invitation to this repository. In GitHub, click **Code**, then copy the HTTPS URL.
3. Install [Git](https://git-scm.com/downloads) and [VS Code](https://code.visualstudio.com/). During Git installation, accept the default options.
4. Open **PowerShell** (Windows) and run the following, replacing the URL and your details:

   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "your-email@example.com"
   git clone https://github.com/ORG/REPOSITORY.git
   cd REPOSITORY
   code .
   ```

5. Read [CONTRIBUTING.md](CONTRIBUTING.md), then create a small first branch and pull request. If anything looks unfamiliar, ask in the team channel before continuing.

## Everyday workflow

Never work directly on `main`.

```powershell
# Update your local copy before starting work
git switch main
git pull origin main

# Create one branch for one focused task
git switch -c feature/short-description

# After editing files
git status
git add path/to/file
git commit -m "Add short description"
git push -u origin feature/short-description
```

Then open GitHub. It will offer **Compare & pull request**; use it, complete the checklist, request a reviewer, and merge only after approval.

## Project plan

The team should agree on these items in the first meeting and record the decision in `docs/`:

| Topic | Decision to record |
| --- | --- |
| Graph schema | Nodes, edges, direction, timestamps, feature definitions |
| Labels | Source, meaning, coverage, and leakage risks |
| Baseline | Rule-based and/or classical ML baseline |
| Evaluation | Temporal split, precision-recall AUC, recall at review capacity, calibration |
| Privacy | Approved data source, access method, retention, and anonymisation |
| Reproducibility | Python version, dependency file, random seeds, experiment log |

## Data and ethics rules

- Do **not** commit raw transaction data, credentials, personal data, customer identifiers, exports, or `.env` files.
- Use synthetic, public, or explicitly approved data only. Keep a data dictionary and provenance record in `docs/`.
- A predicted label is a triage signal, never an accusation or an automated enforcement decision.
- Check for data leakage: future information, label-derived features, and random splits of time-dependent data can make results look falsely strong.

## Definition of done

A task is complete when the code or documentation is understandable, the relevant checks run successfully, results are recorded where applicable, and the pull request has an approval.

## Helpful links

- [Contributing guide](CONTRIBUTING.md)
- [Pull-request checklist](.github/pull_request_template.md)
- [GitHub Docs: collaborating with pull requests](https://docs.github.com/pull-requests/collaborating-with-pull-requests)
- [GitHub Docs: protected branches](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository)


## Shared evaluation for Roles 2 and 3

Role 4's evaluator now accepts the existing `tests/elliptic_split.csv` file. It keeps the team's time split, excludes unknown labels from metrics and matches predictions by transaction ID.

Start with the plain-language [Role 4 evaluation guide](docs/ROLE4_EVALUATION.md). It includes installation, an invented example, the prediction-file format and commands for real model outputs. Verification details are in [Role 4 validation](docs/ROLE4_VALIDATION.md).
