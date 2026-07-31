# LoopsBench Repository Admin Setup

This repository now contains the task contribution workflows and documentation Pages workflow, but several GitHub-side controls still require repository admin access:

- default-branch required checks
- the `loopsbench-sandbox` self-hosted runner
- GitHub Pages publishing for `loopsbench.ai`

## 1. Bootstrap labels

Run:

```bash
python3 scripts/bootstrap_repo_settings.py \
  --repo microsoft/Loopsbench
```

This ensures proposal labels from `.github/ISSUE_TEMPLATE/task-proposal.yml`.

## 2. Configure required checks on `main`

The public task flow expects these checks to be required on pull requests to `main`:

- `validate-task-pr`
- `validate-task-pr-full`

If your GitHub token has repository admin access, you can ask the bootstrap script to configure branch protection:

```bash
python3 scripts/bootstrap_repo_settings.py \
  --repo microsoft/Loopsbench \
  --configure-branch-protection
```

If your organization manages branch protection through rulesets or the API call is blocked, apply the same two required checks in the GitHub UI instead.

## 3. Register the isolated self-hosted runner

The full validation and publish workflows require a self-hosted runner with the label:

- `loopsbench-sandbox`

Run the installer on the sandbox machine with a GitHub account or token that has repository admin access:

```bash
REPO_SLUG=microsoft/Loopsbench \
RUNNER_LABELS=loopsbench-sandbox \
bash scripts/register_loopsbench_runner.sh
```

By default the script:

- downloads the latest `actions/runner` Linux x64 release
- requests a repository runner registration token
- configures the runner with label `loopsbench-sandbox`
- installs and starts it as a service via `svc.sh`

To configure without installing the service:

```bash
INSTALL_SERVICE=false bash scripts/register_loopsbench_runner.sh
```

## 4. Enable GitHub Pages

The documentation site is built by `.github/workflows/pages.yml` and deployed from GitHub Actions. Configure the repository Pages settings as follows:

- Source: GitHub Actions
- Custom domain: `loopsbench.ai`
- Enforce HTTPS: enabled, after DNS verification succeeds

The repository includes `docs/CNAME`, so the generated Pages artifact keeps the custom domain when the workflow deploys.

## 5. Verify the setup

After the admin steps are complete, verify:

- `gh label list -R microsoft/Loopsbench`
- GitHub branch protection or rulesets show `validate-task-pr` and `validate-task-pr-full` as required
- the repository Actions page shows an online self-hosted runner with label `loopsbench-sandbox`
- the `Documentation Pages` workflow deploys successfully and serves `https://loopsbench.ai`
