#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loopsbench.task_contribution_validation import (  # noqa: E402
    run_task_contribution_checks,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a LoopsBench task contribution."
    )
    parser.add_argument(
        "--task-dir", required=True, type=Path, help="Path to the task directory."
    )
    parser.add_argument(
        "--json-out", type=Path, help="Optional path to write the report JSON."
    )
    parser.add_argument(
        "--static-only", action="store_true", help="Run static checks only."
    )
    parser.add_argument(
        "--run-tasks-validate",
        action="store_true",
        help="Run `loopsbench tasks validate` after static checks.",
    )
    parser.add_argument(
        "--run-oracle",
        action="store_true",
        help="Run `loopsbench run --agent oracle` after static checks.",
    )
    parser.add_argument(
        "--oracle-output-root",
        type=Path,
        help="Optional output root for oracle runs.",
    )
    parser.add_argument(
        "--require-provenance",
        action="store_true",
        help="Require publish-grade provenance fields in task.yaml.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    # This CLI is the same narrow entrypoint used by task contribution workflows.
    report = run_task_contribution_checks(
        args.task_dir,
        run_tasks_validate=False if args.static_only else args.run_tasks_validate,
        run_oracle=False if args.static_only else args.run_oracle,
        oracle_output_root=args.oracle_output_root,
        require_provenance=args.require_provenance,
    )

    payload = report.to_dict()
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
