# Check against the Role 4 assignment

## Conclusion

The package meets the upfront requirement to provide a shared evaluation script. It also contains initial AML background and a plan for the final analysis. **It does not yet complete the entire Role 4 assignment.** Real model comparison, model explanations and the final report/presentation remain to be produced.

This check uses the supplied GraphML_roles.pdf, the user's Word/PowerPoint reference files and the CONTRIBUTING.md rules in the supplied repository snapshot. It does not certify the live GitHub state or work performed outside that snapshot.

## Original assignment requirements

| Requirement | Current evidence | Status |
|---|---|---|
| Build the shared evaluation script early | src/role4_evaluation.py; command-line and notebook interfaces; actual Role 1 schema supported. | Implemented and locally tested. |
| Illicit-class F1 | f1_illicit with explicit positive class 1 and definition flags. | Implemented. |
| A precision-recall summary | average_precision calculated by scikit-learn from original scores. The brief lists PR-AUC as an example and explicitly leaves metric choice open. | AP is the documented choice; trapezoidal PR-AUC is not implemented and must not be claimed. |
| Results per time step | Periods 35-49 with counts, missing values and definition flags. | Implemented. |
| Make model results comparable | Shared IDs and labels, fixed test boundary, manifest fingerprints and per-run seed/threshold metadata. | Technical framework ready; team must agree the still-proposed settings and apply the same rules. |
| Explain what drives model predictions | docs/ROLE4_AML_CONTEXT.md defines the methods, required model artefacts and case-selection plan. | Plan prepared. Actual SHAP/PyG explanations are not implemented or run yet. |
| Bring in the money-laundering context | Initial sourced introduction and error trade-off in docs/ROLE4_AML_CONTEXT.md. | Background prepared; interpretation of actual results remains pending. |
| Lead the final write-up | Outline and allocation of contributions in docs/ROLE4_AML_CONTEXT.md. | Outline prepared; final report and slides are not produced. |
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
| Branch, issue and pull request | Instructions are supplied in ROLE4_GITHUB_UPLOAD.md. Actual creation/linking cannot be verified from the ZIP. |
| Review before merge | Required by CONTRIBUTING.md. No approval or merge is claimed. |
| CI execution | Workflow is supplied and structurally checked. A hosted GitHub run is not verified. |

## What can be handed over now

The evaluator, input contract, simulated example, tests and supporting documentation are ready for review by Roles 1-3. The adapter has already been exercised on all 16,670 known-label test rows in the supplied dataset. The prediction scores used for that integration check were invented.

## What completes the full role later

1. Obtain each model's actual predictions, training details and fitted model artefacts.
2. Compare the real results and repeated runs, and create the relevant figures.
3. Run and interpret explanations of selected predictions.
4. Write evidence-based AML conclusions and complete the final report and slides in the supplied formats.
5. Complete the repository review and hosted checks through the team's workflow.
