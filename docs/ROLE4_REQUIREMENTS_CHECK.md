# Check against the Role 4 assignment

## Conclusion

> **Update, 16 November 2026.** All 30 model runs (Roles 2 and 3, 5 seeds each) are now scored with the evaluator and combined with `src/role4_compare.py`. SHAP and GNNExplainer explanations have been run in `notebooks/role4_explainability.ipynb`. Results and the AML interpretation are in [RESULTS_AND_INTERPRETATION.md](RESULTS_AND_INTERPRETATION.md). A draft of the final report in the BSFS format is in `report/`; the slides remain. The status column below reflects this update.

The package met the upfront requirement to provide a shared evaluation script early, together with initial AML background and a plan for the final analysis.

This check uses the supplied GraphML_roles.pdf, the user's Word/PowerPoint reference files and the CONTRIBUTING.md rules in the supplied repository snapshot. It does not certify the live GitHub state or work performed outside that snapshot.

## Original assignment requirements

| Requirement | Current evidence | Status |
|---|---|---|
| Build the shared evaluation script early | src/role4_evaluation.py; command-line and notebook interfaces; actual Role 1 schema supported. | Implemented and locally tested. |
| Illicit-class F1 | f1_illicit with explicit positive class 1 and definition flags. | Implemented. |
| A precision-recall summary | average_precision calculated by scikit-learn from original scores. The brief lists PR-AUC as an example and explicitly leaves metric choice open. | AP is the documented choice; trapezoidal PR-AUC is not implemented and must not be claimed. |
| Results per time step | Periods 35-49 with counts, missing values and definition flags. | Implemented. |
| Make model results comparable | Shared IDs and labels, fixed test boundary, manifest fingerprints and per-run seed/threshold metadata. | Done: 30 runs, one test set (identical `manifest_sha256`), combined with `src/role4_compare.py`. Threshold policy in RESULTS_AND_INTERPRETATION.md. |
| Explain what drives model predictions | docs/ROLE4_AML_CONTEXT.md defines the methods, required model artefacts and case-selection plan. | Done: SHAP for the Role 2 Random Forest, graph ablation and GNNExplainer for the Role 3 GCN (`notebooks/role4_explainability.ipynb`). |
| Bring in the money-laundering context | Initial sourced introduction and error trade-off in docs/ROLE4_AML_CONTEXT.md. | Done: interpretation of the real results in RESULTS_AND_INTERPRETATION.md. |
| Lead the final write-up | Outline and allocation of contributions in docs/ROLE4_AML_CONTEXT.md. | Outline and results write-up prepared; final report and slides are still to be produced. |
| Use Elliptic and shared chronological split | Existing tests/elliptic_split.csv is preserved and validated: train 1-34, test 35-49. Unknown labels are excluded from metrics. | Verified with the supplied split file. |
| Key reference Weber et al. 2019 | Referenced in the background and evaluation guide. | Reference included; personal reading by each team member is outside software verification. |
| Free Google Colab compute | CPU-only evaluator, dependencies and notebook-call examples supplied. | No GPU needed. Execution in a fresh Colab session has not been verified here. |
| User-supplied report and slide templates | The final outline names the supplied BSFS references as the format to follow. | Final formatting remains pending with the final documents. |

The task names SHAP, GNNExplainer, particular metrics and software as examples. It does not require every named method. It does require actual explanations and AML interpretation in the final project, beyond a scoring script.

## Repository requirements

| Rule | Check |
|---|---|
| Reusable code in src and automated checks in tests | Correct locations. 51 local test methods pass, including 60 numerical reference cases. |
| Preserve colleagues' work | Original shared files are unchanged. The main README only gains an evaluation section. |
| Avoid adding real data and generated results | The changes archive excludes the existing dataset and generated outputs. New test inputs are explicitly invented. |
| Record reproducibility and limits | Input and script fingerprints, package versions, threshold and seed are recorded. Actual model feature sets and checkpoints must be supplied by Roles 2 and 3. |
| Branch, issue and pull request | Instructions are in CONTRIBUTING.md. Actual creation/linking cannot be verified from the ZIP. |
| Review before merge | Required by CONTRIBUTING.md. No approval or merge is claimed. |
| CI execution | Workflow is supplied and structurally checked. A hosted GitHub run is not verified. |

## What can be handed over now

The evaluator, input contract, simulated example, tests and supporting documentation are ready for review by Roles 1-3. The adapter has already been exercised on all 16,670 known-label test rows in the supplied dataset. The prediction scores used for that integration check were invented.

## What completes the full role later

1. ~~Obtain each model's actual predictions, training details and fitted model artefacts.~~ Done.
2. ~~Compare the real results and repeated runs, and create the relevant figures.~~ Done: `results/final_comparison/`.
3. ~~Run and interpret explanations of selected predictions.~~ Done.
4. ~~Write evidence-based AML conclusions.~~ Done. Still open: the final report and slides in the supplied formats.
5. Complete the repository review and hosted checks through the team's workflow.
