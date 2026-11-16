# Contributing

This guide is for every contributor, including people new to GitHub. Ask early when unsure; mistakes are easiest to fix before a pull request is merged.

## Team rules

1. Work from a branch, never directly on `main`.
2. One branch and pull request (PR) should address one focused task.
3. Give branches clear names: `feature/graph-loader`, `fix/missing-values`, `docs/data-dictionary`.
4. Keep commits small and descriptive: `Add transaction graph loader`, not `updates`.
5. Do not commit data covered by the data rules in the README, secrets, or generated large files.
6. Do not merge your own PR. Request one teammate review; the project lead handles exceptions.
7. Be constructive in reviews: discuss the work, explain suggestions, and assume good intent.

## Before you start

- Find or create a GitHub Issue for the task. State what “done” means.
- Tell the team which issue you are working on to avoid duplicate work.
- Update `main`, then create your branch:

```bash
git switch main
git pull origin main
git switch -c feature/short-description
# edit, then
git add path/to/file
git commit -m "Add short description"
git push -u origin feature/short-description
```

## Make a pull request

1. Push your branch to GitHub.
2. Open a PR into `main`.
3. Use the PR template. Link the issue with `Closes #123`.
4. Request at least one reviewer; do not approve your own PR.
5. Address feedback with new commits. Keep discussion in the PR so decisions are recorded.
6. Once approved and checks pass, merge using the merge method chosen by the project lead. Delete the branch after merging.

## Quality expectations

- **Code:** use clear names, avoid duplicated logic, and add or update tests when behavior changes.
- **Notebooks:** restart and run all cells before sharing; move reusable functions into `src/`.
- **Experiments:** record dataset version, feature set, split strategy, seed, metrics, and limitations.
- **Documentation:** update the data dictionary or README when an interface, dataset, or decision changes.

## Review expectations

Reviewers check correctness, readability, test coverage, reproducibility, data safety, and possible leakage. A reviewer should either approve, request changes with an explanation, or ask a question promptly.

## If Git goes wrong

Do not panic and do not force-push or delete anything. Copy the output, tell the team, and ask for help. `git status` is always a safe first command.

