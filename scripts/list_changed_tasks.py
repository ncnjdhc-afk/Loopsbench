#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def _is_zero_sha(value: str) -> bool:
    stripped = value.strip()
    return not stripped or set(stripped) == {"0"}


def changed_files(*, repo_root: Path, base_sha: str, head_sha: str) -> list[str]:
    if _is_zero_sha(base_sha):
        completed = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", head_sha, "tasks"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    else:
        completed = subprocess.run(
            ["git", "diff", "--name-only", base_sha, head_sha],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def task_dirs_from_paths(paths: list[str]) -> list[str]:
    task_dirs = {
        str(Path(parts[0]) / parts[1])
        for raw_path in paths
        for parts in [Path(raw_path).parts]
        if len(parts) >= 2 and parts[0] == "tasks" and parts[1].startswith("task_")
    }
    return sorted(task_dirs)


def load_paths_file(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List changed task directories between two git revisions."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to run git diff in.",
    )
    parser.add_argument("--base-sha", help="Base revision for git diff.")
    parser.add_argument("--head-sha", help="Head revision for git diff.")
    parser.add_argument(
        "--paths-file",
        type=Path,
        help="Optional file containing changed paths, one per line. When set, git diff is skipped.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.paths_file is not None:
        paths = load_paths_file(args.paths_file.resolve())
    else:
        if not args.base_sha or not args.head_sha:
            raise SystemExit(
                "--base-sha and --head-sha are required unless --paths-file is provided."
            )
        paths = changed_files(
            repo_root=args.repo_root.resolve(),
            base_sha=args.base_sha,
            head_sha=args.head_sha,
        )

    for task_dir in task_dirs_from_paths(paths):
        print(task_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
