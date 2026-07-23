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
  loopsbench/   # Core package and CLI
  tests/        # Repository-level Python tests
  pyproject.toml
  registry.json
  uv.lock
  README.md
```

## Naming

The repository, Python package, and CLI now use the new name consistently:
- Repository: `LoopsBench`
- Python package: `loopsbench`
- CLI command: `loopsbench`

## Setup

Create the project environment with `uv`:

```bash
uv sync --dev
```

Then run the CLI through `uv`:

```bash
uv run loopsbench --help
```

## Download the Dataset

To get the benchmark task checkout, clone the dataset from Hugging Face into a
separate directory:

```bash
git clone https://huggingface.co/datasets/forcel48/LoopsBench ../LoopsBench-dataset
```

## Running LoopsBench

This checkout does not ship with a top-level `tasks/` directory, so to actually run the
harness you should point it at an external tasks checkout.

Examples:

```bash
uv run loopsbench --help
uv run loopsbench tasks list --tasks-dir /path/to/tasks
uv run loopsbench tasks validate --tasks-dir /path/to/tasks
uv run loopsbench run --dataset-path /path/to/tasks --agent oracle
```

If you prefer invoking the module directly, use:

```bash
uv run python -m loopsbench.cli.main --help
uv run python -m loopsbench.cli.main tasks list --tasks-dir /path/to/tasks
uv run python -m loopsbench.cli.main run --dataset-path /path/to/tasks --agent oracle
```

Actual harness runs still require a compatible task checkout and a working Docker setup.

## What Works In This Copy

This checkout is useful for:
- editing and reading the harness, CLI, agent integrations, parsers, and helper utilities
- running self-contained repository tests

Examples:

```bash
uv run python -m pytest tests/test_copilot_agent.py -q
uv run python -m pytest tests/test_run_docker_image_strategy.py -q
uv run python -m pytest tests/test_harness_docker_image_metadata.py -q
```

## Missing Benchmark Data

Many commands in the codebase still assume a full benchmark checkout and look for a top-level `tasks/` directory.

In this trimmed repository:
- `loopsbench tasks ...` and `loopsbench run ...` are still available, but they need an external dataset/task directory to be useful
- some tests and workflows only make sense when a compatible external task tree is available

If you want to use those workflows, add or mount a compatible `tasks/` tree beside this repository, or pass the task path explicitly via `--tasks-dir` or `--dataset-path`.
