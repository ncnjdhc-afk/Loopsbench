#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ISSUE_URL_RE = re.compile(
    r"https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)/issues/(?P<number>\d+)"
)


def extract_issue_url(text: str) -> re.Match[str] | None:
    return ISSUE_URL_RE.search(text)


def validate_proposal_url(
    text: str, *, expected_repo: str | None = None
) -> tuple[bool, str]:
    match = extract_issue_url(text)
    if match is None:
        return False, "Pull request body must include a GitHub Proposal issue URL."

    owner = match.group("owner")
    repo = match.group("repo")
    issue_number = match.group("number")
    repo_slug = f"{owner}/{repo}"
    if expected_repo and repo_slug.lower() != expected_repo.lower():
        return False, f"Proposal URL must point to {expected_repo}, found {repo_slug}."
    return True, f"Found Proposal issue #{issue_number} in {repo_slug}."


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate that a PR body links to a task proposal issue."
    )
    parser.add_argument("--body", help="Pull request body text.")
    parser.add_argument(
        "--body-file", type=Path, help="Path to a file containing the PR body."
    )
    parser.add_argument(
        "--event-path", type=Path, help="Path to a GitHub event JSON payload."
    )
    parser.add_argument(
        "--expected-repo", help="Optional owner/repo constraint for the issue URL."
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
    ok, message = validate_proposal_url(
        _read_body(args), expected_repo=args.expected_repo
    )
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
