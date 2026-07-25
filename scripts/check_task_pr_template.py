#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_PREFIXES = (
    "- Proposal URL:",
    "- Proposal approval status:",
    "- Task ID:",
    "- Task title:",
    "- Source URL:",
    "- Base revision:",
    "- Modules:",
    "- Units:",
    "- Dependency DAG summary:",
    "- Source evidence for dependency edges:",
    "- Gold solution or gold patch strategy:",
    "- Full-task testing strategy:",
    "- Unit-level verification strategy:",
    "- Why the verifier rejects partial / incorrect implementations:",
    "- License status:",
)

DISALLOWED_VALUES = {
    "tbd",
    "todo",
    "n/a",
    "na",
    "unknown",
    "pending",
    "<fill me>",
}


def validate_pr_template_fields(body: str) -> tuple[bool, list[str]]:
    lines = body.splitlines()
    errors: list[str] = []
    for prefix in REQUIRED_PREFIXES:
        matching = next(
            (line for line in lines if line.strip().startswith(prefix)), None
        )
        if matching is None:
            errors.append(f"Missing required PR field line: {prefix}")
            continue
        value = matching.split(":", 1)[1].strip()
        if not value:
            errors.append(f"PR field must not be empty: {prefix}")
            continue
        normalized = value.casefold()
        if prefix == "- Proposal approval status:" and "approved" not in normalized:
            errors.append(
                "Proposal approval status must indicate that the linked Proposal has been approved."
            )
        if (
            normalized in DISALLOWED_VALUES
            or normalized.startswith("<")
            or normalized.endswith(">")
        ):
            errors.append(f"PR field still contains a placeholder value: {prefix}")
    return not errors, errors


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate required fields from the task PR template."
    )
    parser.add_argument("--body", help="Pull request body text.")
    parser.add_argument(
        "--body-file", type=Path, help="Path to a file containing the PR body."
    )
    parser.add_argument(
        "--event-path", type=Path, help="Path to a GitHub event JSON payload."
    )
    return parser


def _read_body(args: argparse.Namespace) -> str:
    if args.body is not None:
        return args.body
    if args.body_file is not None:
        return args.body_file.read_text(encoding="utf-8")
    if args.event_path is not None:
        payload = json.loads(args.event_path.read_text(encoding="utf-8"))
        return str(payload.get("pull_request", {}).get("body") or "")
    return ""


def main() -> int:
    args = _build_parser().parse_args()
    ok, errors = validate_pr_template_fields(_read_body(args))
    if ok:
        print("Task PR template fields look complete.")
        return 0
    for error in errors:
        print(error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
