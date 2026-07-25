# LoopsBench

LoopsBench is the canonical source for both the harness and the benchmark task definitions.

This repository now includes:
- the Python package under `loopsbench/`
- checked-in task assets under `tasks/`
- GitHub-native contribution workflows under `.github/`
- repository tests under `tests/`
- packaging metadata such as `pyproject.toml`, `uv.lock`, and `registry.json`

## Repository Layout

```text
LoopsBench/
  .github/
    ISSUE_TEMPLATE/
    workflows/
    pull_request_template.md
  loopsbench/   # Core package, CLI, harness, Docker helpers
  scripts/      # Contribution validation, publish, and sync helpers
  tasks/
    _template/  # Starting point for new tasks
    task_tcp_course_stack/
  tests/
  pyproject.toml
  registry.json
  uv.lock
```

## Installation

### Option A: `uv`

```bash
uv sync --dev
uv run loopsbench --help
```

### Option B: editable `pip` install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
loopsbench --help
```

Module-style invocation also works:

```bash
python -m loopsbench.cli.main --help
```

## Submit a Task

LoopsBench uses a GitHub-native contribution flow. The website's `Submit Task` page should link to this repository and the issue form below; contributors do not upload ZIP archives or finished task bundles through the website.

1. Review the task requirements in [CONTRIBUTING.md](CONTRIBUTING.md), `tasks/_template/`, and the example task `tasks/task_tcp_course_stack/`.
2. Open a proposal issue with `.github/ISSUE_TEMPLATE/task-proposal.yml`.
3. Wait for maintainer approval.
4. Build the task in your fork under `tasks/task_<id>/`.
5. Open a pull request using `.github/pull_request_template.md`.
6. Pass static validation, Oracle, and maintainer review before merge.

Create a new task from the checked-in template:

```bash
loopsbench tasks create task_my_new_case
```

Run the expected local validation commands before opening a PR:

```bash
python3 scripts/validate_task_contribution.py --task-dir tasks/task_my_new_case --static-only
loopsbench tasks validate --task-id task_my_new_case
loopsbench run --agent oracle --task-id task_my_new_case --dataset-path tasks --docker-image-strategy local-build
```

## Running LoopsBench

Use the checked-in `tasks/` tree directly:

```bash
loopsbench tasks list --tasks-dir tasks
loopsbench tasks validate --tasks-dir tasks
loopsbench run --dataset-path tasks --task-id task_tcp_course_stack --agent oracle --docker-image-strategy local-build
```

If you prefer `uv`:

```bash
uv run loopsbench tasks list --tasks-dir tasks
uv run loopsbench run --dataset-path tasks --task-id task_tcp_course_stack --agent oracle --docker-image-strategy local-build
```

## Docker Image Strategies

The harness supports three Docker image modes through `loopsbench run` and `loopsbench runs create`:

- `remote`: pull prebuilt task images from a remote registry
- `local-build`: build task images locally from each task's `docker-compose.yaml`
- `local-existing`: use already-present local images without rebuilding

Example remote run:

```bash
loopsbench run \
  --dataset-path tasks \
  --task-id task_tcp_course_stack \
  --agent oracle \
  --docker-image-strategy remote \
  --docker-image-namespace your-namespace \
  --docker-image-tag latest
```

Example local build:

```bash
loopsbench run \
  --dataset-path tasks \
  --task-id task_tcp_course_stack \
  --agent oracle \
  --docker-image-strategy local-build
```

## Publish and Release Model

Merged task contributions remain source-controlled under `tasks/`. After merge, the trusted publish workflow:

- reruns validation on the default branch
- records the task version as the merge commit SHA
- emits deterministic task bundles plus SHA-256 checksums
- can optionally sync published benchmark snapshots into the frontend repository

GitHub Releases remain a distribution channel for published task bundles, but they are not the review entry point. Proposal issues and pull requests are the review entry points.

## Testing Quick Reference

Repository-level harness tests:

```bash
python -m pytest \
  tests/test_docker_compose_manager.py \
  tests/test_harness_docker_image_metadata.py \
  tests/test_repo_profiles.py \
  tests/test_run_docker_image_strategy.py -q
```

Contribution-flow tests:

```bash
python -m pytest \
  tests/test_agent_factory.py \
  tests/test_pr_proposal_check.py \
  tests/test_task_contribution_validation.py \
  tests/test_list_changed_tasks.py \
  tests/test_list_pr_changed_files.py \
  tests/test_task_pr_path_check.py \
  tests/test_publish_workflow_helpers.py \
  tests/test_frontend_sync.py -q
```

Before using Docker-backed runs, make sure Docker is installed, running, and able to build the task images referenced by the selected strategy.
