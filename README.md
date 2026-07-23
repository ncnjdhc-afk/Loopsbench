# LoopsBench

`LoopsBench` is currently a trimmed-down working copy of the LoopsBench harness/core codebase.

This repository contains:
- the Python package under `loopsbench/`
- repository-level tests under `tests/`
- packaging metadata such as `pyproject.toml`, `uv.lock`, and `registry.json`

This repository does **not** currently include the full benchmark dataset checkout. In particular, there is no top-level `tasks/`, `docs/`, `examples/`, `runs/`, or other benchmark asset directories in this copy.

## Current Layout

```text
LoopsBench/
  loopsbench/   # Core package, CLI, harness, Docker helpers
  tests/        # Repository-level harness-focused tests
  pyproject.toml
  registry.json
  uv.lock
  README.md
```

The current retained test suite is focused on core harness and Docker behavior:
- `tests/test_docker_compose_manager.py`
- `tests/test_harness_docker_image_metadata.py`
- `tests/test_repo_profiles.py`
- `tests/test_run_docker_image_strategy.py`

## Naming

The repository, Python package, and CLI now use the LoopsBench name consistently:
- Repository: `LoopsBench`
- Python package: `loopsbench`
- CLI command: `loopsbench`

## Installation

### Option A: `uv`

Create the development environment with `uv`:

```bash
uv sync --dev
uv run loopsbench --help
```

### Option B: editable `pip` install

If you prefer a standard virtual environment plus editable install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
loopsbench --help
```

If you want to invoke the CLI as a module instead of using the installed entry point:

```bash
python -m loopsbench.cli.main --help
```

## External task checkout

This checkout does not ship with a top-level `tasks/` directory, so real harness runs need an external task checkout.

Example:

```bash
git clone https://huggingface.co/datasets/forcel48/LoopsBench ../LoopsBench-dataset
```

You can then point the CLI at that checkout with `--dataset-path` or `--tasks-dir`.

## Running LoopsBench

Basic examples:

```bash
uv run loopsbench --help
uv run loopsbench tasks list --tasks-dir /path/to/tasks
uv run loopsbench tasks validate --tasks-dir /path/to/tasks
uv run loopsbench run --dataset-path /path/to/tasks --agent oracle
```

Or, if you installed with `pip install -e .`:

```bash
loopsbench --help
loopsbench tasks list --tasks-dir /path/to/tasks
loopsbench run --dataset-path /path/to/tasks --agent oracle
```

Actual harness runs still require a compatible task checkout and a working Docker setup.

## Docker image strategies

The harness supports three Docker image modes through `loopsbench run` / `loopsbench runs create`:

- `--docker-image-strategy remote`
  - pull prebuilt task images from a remote registry
- `--docker-image-strategy local-build`
  - build task images locally from each task's `docker-compose.yaml`
- `--docker-image-strategy local-existing`
  - use already-present local images without rebuilding

### Remote mode

Remote mode is the default strategy, but it requires a namespace:

```bash
uv run loopsbench run \
  --dataset-path /path/to/tasks \
  --task-id task_compiler \
  --agent oracle \
  --docker-image-strategy remote \
  --docker-image-namespace dolischwer \
  --docker-image-tag latest
```

Important details:
- `--docker-image-namespace` is required in `remote` mode.
- `--docker-image-tag` is optional; if omitted, it defaults to `latest`.
- Remote task images are resolved as:

```text
<namespace>/loopsbench-<normalized-task-id>:<tag>
```

For example:

```text
dolischwer/loopsbench-task-compiler:latest
```

### Local build mode

Use local build mode when you want the harness to build images directly from the external task checkout:

```bash
uv run loopsbench run \
  --dataset-path /path/to/tasks \
  --task-id task_compiler \
  --agent oracle \
  --docker-image-strategy local-build
```

### Local existing mode

Use local existing mode when the correct task image is already present locally:

```bash
uv run loopsbench run \
  --dataset-path /path/to/tasks \
  --task-id task_compiler \
  --agent oracle \
  --docker-image-strategy local-existing
```

The legacy `--no-rebuild` flag is still accepted, but it is only a compatibility alias for `--docker-image-strategy local-existing`.

## What works in this copy

This checkout is useful for:
- editing and reading the harness, CLI, Docker integration, agent integrations, parsers, and helper utilities
- running the retained harness-focused repository tests
- validating Docker image strategy and task image resolution behavior

Examples:

```bash
uv run python -m pytest tests/test_docker_compose_manager.py -q
uv run python -m pytest tests/test_harness_docker_image_metadata.py -q
uv run python -m pytest tests/test_run_docker_image_strategy.py -q
```

## Missing benchmark data

Many commands in the codebase still assume a full benchmark checkout and look for a top-level `tasks/` directory.

In this trimmed repository:
- `loopsbench tasks ...` and `loopsbench run ...` are still available, but they need an external dataset/task directory to be useful
- some harness flows only make sense when a compatible external task tree is available

If you want to use those workflows, add or mount a compatible `tasks/` tree beside this repository, or pass the task path explicitly via `--tasks-dir` or `--dataset-path`.

## Current limitations

This repository no longer includes the auxiliary top-level `scripts/` directory that existed in broader working copies, so README examples here focus on the packaged CLI and the retained harness-related tests rather than external publishing or maintenance scripts.

If you need task-image publishing or dataset maintenance workflows, run them from a fuller working checkout that still contains those scripts.

## Testing quick reference

The remaining repository tests are intended to validate core harness behavior, not task datasets themselves:

```bash
uv run python -m pytest \
  tests/test_docker_compose_manager.py \
  tests/test_harness_docker_image_metadata.py \
  tests/test_repo_profiles.py \
  tests/test_run_docker_image_strategy.py -q
```

These tests are useful for verifying:
- Docker startup behavior
- remote/local image strategy selection
- task image metadata recording
- supporting harness test-selection helpers

They do **not** replace running the harness against a real external task checkout.

## Useful CLI options for real runs

A few options that are especially relevant in this trimmed checkout:

- `--dataset-path /path/to/tasks`
- `--task-id task_name` (repeatable)
- `--exclude-task-id pattern` (repeatable)
- `--docker-image-strategy remote|local-build|local-existing`
- `--docker-image-namespace <namespace>`
- `--docker-image-tag <tag>`
- `--output-path <runs-dir>`
- `--run-id <custom-id>`

For the full option surface, run:

```bash
uv run loopsbench run --help
```
or
```bash
loopsbench run --help
```
if you used the editable pip install.

## Module invocation examples

If you prefer module-style invocation:

```bash
uv run python -m loopsbench.cli.main --help
uv run python -m loopsbench.cli.main tasks list --tasks-dir /path/to/tasks
uv run python -m loopsbench.cli.main run \
  --dataset-path /path/to/tasks \
  --task-id task_compiler \
  --agent oracle \
  --docker-image-strategy remote \
  --docker-image-namespace dolischwer \
  --docker-image-tag latest
```

This can be convenient when you are working inside a development environment without relying on the installed console script.

## Notes on Docker prerequisites

Before using Docker-backed runs, make sure:
- Docker is installed and running
- the external task checkout contains valid `docker-compose.yaml` files for the tasks you want to run
- if using `remote` mode, the referenced images exist in the chosen namespace and tag
- if using `local-existing`, the expected local task images are already present

If a remote image is missing, the harness will fail during startup when it tries to pull the resolved image reference.

If a local-existing image is missing, the harness will fail before `docker compose up` with a local image inspection error.

Those failure modes are expected and are covered by the retained harness tests.

## Summary

This repository is best treated as a LoopsBench harness/core development checkout with:
- a working packaged CLI
- editable installation support
- documented Docker image strategy controls
- a small retained harness-focused test suite
- no bundled task dataset

For realistic runs, pair it with an external `tasks/` checkout and choose the Docker image strategy that matches your workflow.
