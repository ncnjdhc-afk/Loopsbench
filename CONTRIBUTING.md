# Contributing Tasks to LoopsBench

LoopsBench accepts new benchmark tasks through a GitHub-native workflow:

```text
Review the criteria
-> Submit a Task Proposal issue
-> Wait for maintainer approval
-> Build the task in your fork
-> Open a pull request
-> Pass CI and maintainer review
-> Merge
```

The public website should point contributors at this document and the GitHub Issue Form in `.github/ISSUE_TEMPLATE/task-proposal.yml`.

## What You Submit Where

- **Task Proposal**: a GitHub Issue that describes the task idea, source evidence, module/unit plan, and dependency DAG.
- **Complete task implementation**: a GitHub Pull Request that adds or updates files under `tasks/task_<name>/`.

Do **not** upload a ZIP archive, Dockerfile bundle, or finished task through the website. The task repository is the only source of truth.

## Before You Start

Read:

- the existing benchmark tasks under `tasks/`
- the example multi-unit task `tasks/task_tcp_course_stack/`
- the task template under `tasks/_template/`
- the validation commands below

Every accepted LoopsBench task must be:

- **Authentic**: grounded in a real software-development source, with a repository URL and base revision.
- **Long-horizon**: more than a single local edit; it should contain multiple development units.
- **Dependency-aware**: the unit DAG must be justified by real source evidence.
- **Separately testable**: each unit must have a requirement, scope, prerequisites, and acceptance condition.
- **Robustly verified**: base, partial, incorrect, and complete implementations must be distinguishable.
- **Reproducible**: the environment must build consistently.
- **Redistributable**: code, tests, and patches must have a license-compatible provenance.

## Step 1: Submit a Task Proposal

Open the GitHub Issue Form:

- `.github/ISSUE_TEMPLATE/task-proposal.yml`

The proposal is for the task design only. It must include:

- task title
- source type and source URL
- repository URL
- base commit, tag, or revision
- summary and long-horizon justification
- proposed modules and units
- proposed dependency DAG
- dependency evidence
- gold solution or gold patch provenance
- testing strategy
- unit-level verification strategy
- expert effort estimate
- difficulty justification
- license / redistribution status
- contributor identity

Maintainers track proposal state with labels such as:

- `task-proposal`
- `proposal: pending`
- `proposal: needs-information`
- `proposal: approved`
- `proposal: rejected`
- `proposal: duplicate`
- `proposal: implemented`

Wait for `proposal: approved` before investing in the full implementation.

## Step 2: Create the Task in Your Fork

Install the harness:

```bash
pip install -e .
```

Create a new task from the checked-in template:

```bash
loopsbench tasks create task_my_new_case
```

This copies `tasks/_template/` into `tasks/task_my_new_case/`.

At minimum, fill in:

- `task.yaml`
- `Dockerfile`
- `docker-compose.yaml`
- `base/`
- `requirements/*.yaml`
- `unit_dag.json`
- `module_dag.yaml`
- `slug_diff_map.json`
- `gold_patches/*.diff` or `gold-patch.diff`
- `solution.sh`
- `run-tests.sh`
- `tests/`

## Step 3: Local Validation

Run the static contribution validator first:

```bash
python3 scripts/validate_task_contribution.py --task-dir tasks/task_my_new_case --static-only
```

Run the basic harness task validator:

```bash
loopsbench tasks validate --task-id task_my_new_case
```

Run Oracle end-to-end:

```bash
loopsbench run --agent oracle --task-id task_my_new_case --dataset-path tasks --docker-image-strategy local-build
```

Your PR should not be opened until these commands are clean locally.

## Step 4: Open a Pull Request

Use the pull-request template at `.github/pull_request_template.md`.

The PR must link the approved Proposal issue and explain:

- task ID and task name
- source URL and base revision
- module and unit structure
- dependency evidence
- gold solution / gold patch strategy
- testing strategy
- validation commands and results
- license / redistribution status
- known limitations

The final `task.yaml` in the PR must carry the publish-grade provenance fields
(`source_url`, `source_repository_url`, `source_base_revision`, `proposal_url`,
and `license_status`). A merged task without them will fail the trusted publish
workflow and will not be published to Benchmarks.

One PR should introduce or revise one task unless maintainers explicitly ask otherwise.

## CI Structure

This repository ships two CI layers for contributed tasks:

- `task-pr-static-checks.yml`
  - trusted workflow definition from the default branch
  - safe checks on ordinary GitHub runners against the PR files as data
  - proposal URL presence
  - changed-path allowlist enforcement for task-only PRs
  - task manifest / DAG / path validation
- `task-pr-full-validation.yml`
  - trusted workflow definition from the default branch
  - full validation on an isolated self-hosted runner
  - `loopsbench tasks validate`
  - `loopsbench run --agent oracle`

The PR workflows intentionally check out trusted base-revision code for the harness and workflow scripts, then treat the pull-request checkout as untrusted task data. The full workflow intentionally targets a self-hosted runner label. Do not run untrusted task Dockerfiles with repository secrets on a general-purpose runner.

## Review and Merge

Passing CI is necessary but not sufficient. Maintainers still review:

- source authenticity
- DAG evidence quality
- test robustness
- environment safety
- licensing

Only merged tasks are eligible for publication in Benchmarks.

## Trusted Publish Step

After a task PR lands on the default branch, the trusted publish workflow reruns validation on the merged revision, records the task version as the repository commit SHA, creates a deterministic task bundle plus SHA-256 checksum, and emits a publish manifest artifact.
