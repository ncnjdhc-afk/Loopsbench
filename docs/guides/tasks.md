# Contributing Tasks

LoopsBench tasks are contributed through GitHub issues and pull requests. The website should send contributors to GitHub rather than accepting ZIP uploads or finished bundles.

## Contribution Flow

1. Read `CONTRIBUTING.md`, `tasks/_template/`, and the example task under `tasks/task_tcp_course_stack/`.
2. Open a Task Proposal issue with `.github/ISSUE_TEMPLATE/task-proposal.yml`.
3. Wait for maintainer approval.
4. Implement the task in a fork under `tasks/task_<id>/`.
5. Open a pull request with `.github/pull_request_template.md`.
6. Pass static validation, Oracle validation, and maintainer review.

## Create a Task

```bash
loopsbench tasks create task_my_new_case
```

This copies `tasks/_template/` into a new task directory.

## Required Files

At minimum, a publishable task contains:

- `task.yaml`
- `Dockerfile`
- `docker-compose.yaml`
- `base/`
- `requirements/*.yaml`
- `unit_dag.json`
- `module_dag.yaml`
- `slug_diff_map.json`
- `solution.sh` or `solution.yaml`
- `run-tests.sh`
- `tests/`

Task PRs should also include source provenance fields in `task.yaml`, including source URL, source repository URL, base revision, proposal URL, license status, and contributor identity.

## Local Validation

Run static validation first:

```bash
python3 scripts/validate_task_contribution.py --task-dir tasks/task_my_new_case --static-only
```

Run task-level validation:

```bash
loopsbench tasks validate --task-id task_my_new_case
```

Run Oracle end to end:

```bash
loopsbench run \
  --agent oracle \
  --task-id task_my_new_case \
  --dataset-path tasks \
  --docker-image-strategy local-build
```

## CI Model

Task pull requests use two validation layers:

- `Task PR Static Checks` runs safe path, proposal, manifest, and static validation checks.
- `Task PR Full Validation` runs full task validation and Oracle on an isolated self-hosted runner.

After merge, the trusted publish workflow reruns validation on the default branch and emits deterministic task bundles plus checksums.
