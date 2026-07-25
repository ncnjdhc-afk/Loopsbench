#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.list_changed_tasks import load_paths_file, task_dirs_from_paths


def _is_suspicious_path(raw_path: str) -> bool:
    path = Path(raw_path)
    return path.is_absolute() or ".." in path.parts


def validate_task_pr_paths(paths: list[str]) -> tuple[bool, list[str]]:
    normalized_paths = [path.strip() for path in paths if path.strip()]
    errors: list[str] = []

    for path in normalized_paths:
        if _is_suspicious_path(path):
            errors.append(
                f"Changed path `{path}` is invalid; absolute paths and `..` segments are not allowed."
            )

    if errors:
        return False, errors

    task_dirs = task_dirs_from_paths(normalized_paths)
    if not task_dirs:
        return True, []

    if len(task_dirs) != 1:
        errors.append(
            "Task contribution PRs must modify exactly one task directory under tasks/task_<id>/; "
            f"found {len(task_dirs)}: {', '.join(task_dirs)}."
        )

    allowed_prefixes = tuple(f"{task_dir}/" for task_dir in task_dirs)
    for path in normalized_paths:
        if any(path.startswith(prefix) for prefix in allowed_prefixes):
            continue
        errors.append(
            "Task contribution PRs may only modify files inside the contributed task directory; "
            f"found disallowed path `{path}`."
        )

    deduped_errors: list[str] = []
    seen: set[str] = set()
    for error in errors:
        if error not in seen:
            seen.add(error)
            deduped_errors.append(error)
    return not deduped_errors, deduped_errors


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reject task contribution PRs that touch disallowed paths."
    )
    parser.add_argument(
        "--paths-file", type=Path, help="File containing changed paths, one per line."
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Changed path. Can be provided multiple times.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    paths = list(args.path)
    if args.paths_file is not None:
        paths.extend(load_paths_file(args.paths_file.resolve()))

    ok, errors = validate_task_pr_paths(paths)
    if ok:
        print("Changed paths are valid for a task contribution PR.")
        return 0

    for error in errors:
        print(error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
