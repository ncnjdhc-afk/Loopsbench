#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class RepoLabel:
    name: str
    color: str
    description: str


REQUIRED_LABELS = (
    RepoLabel(
        "task-proposal",
        "1d76db",
        "Task proposal issues for benchmark contributions",
    ),
    RepoLabel(
        "proposal: pending",
        "d4c5f9",
        "Proposal received and awaiting maintainer review",
    ),
    RepoLabel(
        "proposal: needs-information",
        "fbca04",
        "Proposal needs additional contributor information",
    ),
    RepoLabel(
        "proposal: approved",
        "0e8a16",
        "Proposal approved for task implementation",
    ),
    RepoLabel(
        "proposal: rejected",
        "b60205",
        "Proposal rejected and should not proceed",
    ),
    RepoLabel(
        "proposal: duplicate",
        "cfd3d7",
        "Proposal duplicates an existing task or proposal",
    ),
    RepoLabel(
        "proposal: implemented",
        "5319e7",
        "Proposal has been implemented in a merged task PR",
    ),
)

DEFAULT_REQUIRED_CHECKS = ("validate-task-pr", "validate-task-pr-full")


def _run(command: list[str], *, dry_run: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", shlex.join(command))
    if dry_run:
        return subprocess.CompletedProcess(command, returncode=0, stdout="", stderr="")
    return subprocess.run(command, check=True, capture_output=True, text=True)


def ensure_labels(repo: str, *, dry_run: bool) -> None:
    for label in REQUIRED_LABELS:
        _run(
            [
                "gh",
                "label",
                "create",
                label.name,
                "-R",
                repo,
                "--color",
                label.color,
                "--description",
                label.description,
                "--force",
            ],
            dry_run=dry_run,
        )


def configure_branch_protection(
    repo: str,
    *,
    default_branch: str,
    required_checks: tuple[str, ...],
    dry_run: bool,
) -> None:
    checks_json = ", ".join(f'"{context}"' for context in required_checks)
    payload = f"""{{
  "required_status_checks": {{
    "strict": true,
    "contexts": [{checks_json}]
  }},
  "enforce_admins": false,
  "required_pull_request_reviews": {{
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  }},
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "lock_branch": false,
  "allow_fork_syncing": true
}}"""
    command = [
        "gh",
        "api",
        "-X",
        "PUT",
        f"repos/{repo}/branches/{default_branch}/protection",
        "--input",
        "-",
    ]
    print("+", shlex.join(command))
    if dry_run:
        return
    subprocess.run(command, check=True, input=payload, text=True)


def check_runner_visibility(repo: str, *, dry_run: bool) -> None:
    _run(
        ["gh", "api", f"repos/{repo}/actions/runners"],
        dry_run=dry_run,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap GitHub labels and branch protection for LoopsBench."
    )
    parser.add_argument("--repo", default="microsoft/Loopsbench")
    parser.add_argument("--default-branch", default="main")
    parser.add_argument(
        "--configure-branch-protection",
        action="store_true",
        help="Configure required status checks on the default branch.",
    )
    parser.add_argument(
        "--check-runner",
        action="store_true",
        help="Verify whether the current token can view self-hosted runners for the repository.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    ensure_labels(args.repo, dry_run=args.dry_run)

    if args.configure_branch_protection:
        configure_branch_protection(
            args.repo,
            default_branch=args.default_branch,
            required_checks=DEFAULT_REQUIRED_CHECKS,
            dry_run=args.dry_run,
        )

    if args.check_runner:
        check_runner_visibility(args.repo, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
