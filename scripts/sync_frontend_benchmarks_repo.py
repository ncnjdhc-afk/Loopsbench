#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class SyncResult:
    frontend_repo_dir: str
    changed: bool
    changed_files: list[str]
    commit_sha: str | None
    pushed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _run(
    command: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def _git_changed_files(repo_dir: Path) -> list[str]:
    completed = _run(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "public/benchmarks-data",
            "src/data/generatedContribution.ts",
        ],
        cwd=repo_dir,
    )
    files: list[str] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        files.append(line[3:].strip())
    return files


def _stage_generated_outputs(repo_dir: Path) -> None:
    _run(["git", "add", "-A", "public/benchmarks-data"], cwd=repo_dir)
    contribution_path = repo_dir / "src" / "data" / "generatedContribution.ts"
    if contribution_path.exists():
        _run(["git", "add", "src/data/generatedContribution.ts"], cwd=repo_dir)


def _git_head(repo_dir: Path) -> str:
    return _run(["git", "rev-parse", "HEAD"], cwd=repo_dir).stdout.strip()


def sync_frontend_benchmarks_repo(
    *,
    frontend_repo_dir: Path,
    generator_script: Path,
    tasks_root: Path,
    source_sha: str,
    python_executable: str = sys.executable,
    commit_author_name: str = "LoopsBench Publish Bot",
    commit_author_email: str = "loopsbench-publish-bot@example.com",
    push_branch: str | None = None,
    push: bool = False,
) -> SyncResult:
    repo_dir = frontend_repo_dir.resolve()
    script_path = generator_script.resolve()
    tasks_path = tasks_root.resolve()

    if not (repo_dir / ".git").exists():
        raise RuntimeError(f"Frontend repo is not a git checkout: {repo_dir}")
    if not script_path.is_file():
        raise RuntimeError(f"Benchmark generator script not found: {script_path}")
    if not tasks_path.is_dir():
        raise RuntimeError(f"Tasks root not found: {tasks_path}")

    env = os.environ.copy()
    env["LOOPSBENCH_BENCHMARK_TASKS_ROOT"] = str(tasks_path)
    env["LOOPSBENCH_BENCHMARK_OUTPUT_ROOT"] = str(
        repo_dir / "public" / "benchmarks-data"
    )
    _run([python_executable, str(script_path)], cwd=repo_dir, env=env)

    contribution_script = repo_dir / "scripts" / "generate_contribution_data.py"
    if contribution_script.is_file():
        contribution_env = env.copy()
        contribution_env["LOOPSBENCH_CONTRIBUTION_TEMPLATE_ROOT"] = str(
            tasks_path / "_template"
        )
        contribution_env["LOOPSBENCH_CONTRIBUTION_OUTPUT_PATH"] = str(
            repo_dir / "src" / "data" / "generatedContribution.ts"
        )
        _run(
            [python_executable, str(contribution_script)],
            cwd=repo_dir,
            env=contribution_env,
        )

    changed_files = _git_changed_files(repo_dir)
    if not changed_files:
        return SyncResult(
            frontend_repo_dir=str(repo_dir),
            changed=False,
            changed_files=[],
            commit_sha=None,
            pushed=False,
        )

    _run(["git", "config", "user.name", commit_author_name], cwd=repo_dir)
    _run(["git", "config", "user.email", commit_author_email], cwd=repo_dir)
    _stage_generated_outputs(repo_dir)
    _run(
        ["git", "commit", "-m", f"Update benchmarks data for {source_sha}"],
        cwd=repo_dir,
    )
    commit_sha = _git_head(repo_dir)

    pushed = False
    if push:
        if not push_branch:
            raise RuntimeError("push_branch is required when push=True")
        _run(["git", "push", "origin", f"HEAD:{push_branch}"], cwd=repo_dir)
        pushed = True

    return SyncResult(
        frontend_repo_dir=str(repo_dir),
        changed=True,
        changed_files=changed_files,
        commit_sha=commit_sha,
        pushed=pushed,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate and optionally push frontend benchmarks-data from trusted publish context."
    )
    parser.add_argument(
        "--frontend-repo-dir",
        required=True,
        type=Path,
        help="Checked-out frontend git repository.",
    )
    parser.add_argument(
        "--generator-script",
        required=True,
        type=Path,
        help="Path to the frontend benchmark generator script.",
    )
    parser.add_argument(
        "--tasks-root", required=True, type=Path, help="Tasks directory to publish."
    )
    parser.add_argument(
        "--source-sha", required=True, help="Source commit SHA being published."
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable for the generator script.",
    )
    parser.add_argument(
        "--commit-author-name",
        default="LoopsBench Publish Bot",
        help="Git author name for the sync commit.",
    )
    parser.add_argument(
        "--commit-author-email",
        default="loopsbench-publish-bot@example.com",
        help="Git author email for the sync commit.",
    )
    parser.add_argument(
        "--push-branch", help="Remote branch to update when --push is set."
    )
    parser.add_argument(
        "--push", action="store_true", help="Push the sync commit to origin."
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = sync_frontend_benchmarks_repo(
        frontend_repo_dir=args.frontend_repo_dir,
        generator_script=args.generator_script,
        tasks_root=args.tasks_root,
        source_sha=args.source_sha,
        python_executable=args.python_executable,
        commit_author_name=args.commit_author_name,
        commit_author_email=args.commit_author_email,
        push_branch=args.push_branch,
        push=args.push,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
