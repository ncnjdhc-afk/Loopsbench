#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_API_ROOT = "https://api.github.com"
USER_AGENT = "loopsbench-task-contribution-validator"


def pr_context_from_event(event_path: Path) -> tuple[str, int]:
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    pull_request = payload.get("pull_request") or {}
    repo_full_name = (
        str((payload.get("repository") or {}).get("full_name") or "").strip()
        or str(
            ((pull_request.get("base") or {}).get("repo") or {}).get("full_name") or ""
        ).strip()
    )
    pr_number = pull_request.get("number") or payload.get("number")
    if not repo_full_name:
        raise ValueError(f"Could not determine repository full name from {event_path}.")
    if not isinstance(pr_number, int):
        raise ValueError(f"Could not determine pull request number from {event_path}.")
    return repo_full_name, pr_number


def _github_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _github_get_json(*, url: str, token: str | None) -> Any:
    request = urllib.request.Request(url, headers=_github_headers(token))
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def list_pr_changed_files(
    *,
    repo_full_name: str,
    pr_number: int,
    token: str | None = None,
    api_root: str = DEFAULT_API_ROOT,
) -> list[str]:
    page = 1
    filenames: list[str] = []
    while True:
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        url = f"{api_root.rstrip('/')}/repos/{repo_full_name}/pulls/{pr_number}/files?{query}"
        payload = _github_get_json(url=url, token=token)
        if not isinstance(payload, list):
            raise RuntimeError("GitHub PR files response must be a list.")
        if not payload:
            break

        for item in payload:
            if not isinstance(item, dict):
                continue
            filename = str(item.get("filename") or "").strip()
            if filename:
                filenames.append(filename)

        if len(payload) < 100:
            break
        page += 1
    return filenames


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List changed files for a pull request via the GitHub API."
    )
    parser.add_argument(
        "--event-path",
        type=Path,
        help="GitHub event payload containing pull_request context.",
    )
    parser.add_argument(
        "--repo", help="Repository full name, for example microsoft/Loopsbench."
    )
    parser.add_argument("--pr-number", type=int, help="Pull request number.")
    parser.add_argument(
        "--github-token-env",
        default="GITHUB_TOKEN",
        help="Environment variable that stores the GitHub token. Default: GITHUB_TOKEN.",
    )
    parser.add_argument(
        "--api-root", default=DEFAULT_API_ROOT, help="GitHub API root URL."
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    repo_full_name = args.repo
    pr_number = args.pr_number
    if not repo_full_name or pr_number is None:
        if args.event_path is None:
            raise SystemExit("Provide --repo and --pr-number, or provide --event-path.")
        repo_full_name, pr_number = pr_context_from_event(args.event_path.resolve())

    token = os.environ.get(args.github_token_env) or None
    try:
        filenames = list_pr_changed_files(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            token=token,
            api_root=args.api_root,
        )
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"GitHub API request failed with HTTP {exc.code} for PR files."
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"GitHub API request failed: {exc.reason}") from exc

    for filename in filenames:
        print(filename)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
