# Project-lead setup checklist

Complete these steps after pushing this local repository to GitHub. They use GitHub’s standard collaboration controls and keep accidental changes out of the shared branch.

## 1. Publish the repository

On GitHub, create an empty repository (do not add a README there). Back in this project folder, run:

```powershell
git add .
git commit -m "Initial project setup"
git branch -M main
git remote add origin https://github.com/ORG/REPOSITORY.git
git push -u origin main
```

Replace `ORG/REPOSITORY` with the URL copied from GitHub. Invite students through **Settings → Collaborators and teams**.

## 2. Protect `main`

Go to **Settings → Branches → Add branch protection rule**, set the branch pattern to `main`, and enable:

- Require a pull request before merging
- Require one approval
- Dismiss stale approvals when new commits are pushed
- Require conversation resolution before merging
- Require status checks before merging (add checks later, once CI exists)
- Do not allow force pushes or deletions

If your GitHub plan does not offer all controls for a private repository, keep the written rules in `CONTRIBUTING.md` and make the project lead the only person who merges PRs.

## 3. Set team conventions

- Use the **Issues** tab to assign tasks and link each PR to an issue.
- Add a GitHub Project board with columns: Backlog, Ready, In progress, In review, Done.
- Set one short weekly integration session: merge approved work, check experiments, and update decisions in `docs/`.
- Before data work begins, appoint one person responsible for approving data access and maintaining the data dictionary.

## 4. First sprint suggestion

Create these small starter issues: define the graph schema, document the data source, load a tiny synthetic dataset, create an evaluation-split proposal, and add a baseline model. This gives every student a reviewable first PR without exposing sensitive data.

## Sources consulted

- GitHub Docs, [About pull request reviews](https://docs.github.com/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews)
- GitHub Docs, [Managing a branch protection rule](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- GitHub Docs, [Setting guidelines for repository contributors](https://docs.github.com/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)

