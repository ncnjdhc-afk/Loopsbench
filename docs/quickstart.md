# Quick Start

## Requirements

- Python 3.12 or newer
- Docker, for Docker-backed harness runs
- A model runtime configuration for non-Oracle agents

## Install

Use `uv` for the full development environment:

```bash
uv sync --dev
uv run loopsbench --help
```

Or install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
loopsbench --help
```

## Inspect Tasks

List tasks from the checked-in `tasks/` directory:

```bash
loopsbench tasks list --tasks-dir tasks
```

Validate task manifests and required files:

```bash
loopsbench tasks validate --tasks-dir tasks
```

## Run the Oracle Baseline

The Oracle agent applies the task solution and is useful for validating task packaging:

```bash
loopsbench run \
  --dataset-path tasks \
  --task-id task_tcp_course_stack \
  --agent oracle \
  --docker-image-strategy local-build
```

## Run a Model-Backed Agent

Provide model credentials through a model runtime file instead of hard-coding secrets in run configs:

```yaml
env_files:
  - .env
env:
  OPENAI_MODEL: gpt-5
```

Then run an agent:

```bash
loopsbench run \
  --dataset-path tasks \
  --task-id task_tcp_course_stack \
  --agent codex \
  --model provider/model-name \
  --model-config model-env.yaml \
  --docker-image-strategy local-build
```

## Review Results

By default, run artifacts are written under `runs/<run-id>/`. Use:

```bash
loopsbench runs list --runs-dir runs
loopsbench runs status --run-id <run-id> --runs-dir runs
loopsbench runs summarize --run-id <run-id> --runs-dir runs
```
