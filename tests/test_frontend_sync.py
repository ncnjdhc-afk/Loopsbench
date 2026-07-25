from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.sync_frontend_benchmarks_repo import sync_frontend_benchmarks_repo


def _run(command: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_git_repo(path: Path) -> None:
    _run(["git", "init", "-b", "main"], cwd=path)
    _run(["git", "config", "user.name", "Fixture"], cwd=path)
    _run(["git", "config", "user.email", "fixture@example.com"], cwd=path)


def _commit_all(path: Path, message: str) -> str:
    _run(["git", "add", "."], cwd=path)
    _run(["git", "commit", "-m", message], cwd=path)
    return _run(["git", "rev-parse", "HEAD"], cwd=path)


def _create_frontend_fixture(tmp_path: Path) -> tuple[Path, Path]:
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir()
    _init_git_repo(frontend_dir)
    _write_text(frontend_dir / "public" / "benchmarks-data" / ".gitkeep", "")
    _write_text(
        frontend_dir / "src" / "data" / "generatedContribution.ts",
        "export const generatedTaskStructureExample = '';\n",
    )
    generator_path = frontend_dir / "scripts" / "generate_benchmarks_data.py"
    _write_text(
        generator_path,
        "\n".join(
            [
                "from __future__ import annotations",
                "import json",
                "import os",
                "from pathlib import Path",
                "",
                "tasks_root = Path(os.environ['LOOPSBENCH_BENCHMARK_TASKS_ROOT'])",
                "output_root = Path(os.environ['LOOPSBENCH_BENCHMARK_OUTPUT_ROOT'])",
                "task_ids = sorted(path.name for path in tasks_root.iterdir() if path.is_dir() and path.name.startswith('task_'))",
                "output_root.mkdir(parents=True, exist_ok=True)",
                "(output_root / 'index.json').write_text(json.dumps({'tasks': task_ids}, sort_keys=True), encoding='utf-8')",
            ]
        )
        + "\n",
    )
    _write_text(
        frontend_dir / "scripts" / "generate_contribution_data.py",
        "\n".join(
            [
                "from __future__ import annotations",
                "import os",
                "from pathlib import Path",
                "",
                "template_root = Path(os.environ['LOOPSBENCH_CONTRIBUTION_TEMPLATE_ROOT'])",
                "output_path = Path(os.environ['LOOPSBENCH_CONTRIBUTION_OUTPUT_PATH'])",
                "names = sorted(path.name for path in template_root.iterdir() if path.name != '.gitkeep')",
                "output_path.parent.mkdir(parents=True, exist_ok=True)",
                "output_path.write_text('export const generatedTaskStructureExample = ' + repr('|'.join(names)) + ';\\n', encoding='utf-8')",
            ]
        )
        + "\n",
    )
    _commit_all(frontend_dir, "Initial frontend fixture")
    return frontend_dir, generator_path


def _create_tasks_fixture(tmp_path: Path) -> Path:
    tasks_root = tmp_path / "tasks"
    (tasks_root / "task_alpha").mkdir(parents=True)
    (tasks_root / "task_beta").mkdir(parents=True)
    (tasks_root / "_template").mkdir(parents=True)
    _write_text(tasks_root / "_template" / "task.yaml", "instruction: example\n")
    return tasks_root


def test_sync_frontend_benchmarks_repo_commits_changes(tmp_path: Path) -> None:
    frontend_dir, generator_path = _create_frontend_fixture(tmp_path)
    tasks_root = _create_tasks_fixture(tmp_path)

    result = sync_frontend_benchmarks_repo(
        frontend_repo_dir=frontend_dir,
        generator_script=generator_path,
        tasks_root=tasks_root,
        source_sha="1234567890abcdef",
        python_executable=sys.executable,
    )

    assert result.changed is True
    assert result.commit_sha is not None
    payload = json.loads(
        (frontend_dir / "public" / "benchmarks-data" / "index.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload == {"tasks": ["task_alpha", "task_beta"]}
    assert "public/benchmarks-data/index.json" in result.changed_files
    contribution_text = (
        frontend_dir / "src" / "data" / "generatedContribution.ts"
    ).read_text(encoding="utf-8")
    assert "task.yaml" in contribution_text


def test_sync_frontend_benchmarks_repo_is_noop_when_snapshot_unchanged(
    tmp_path: Path,
) -> None:
    frontend_dir, generator_path = _create_frontend_fixture(tmp_path)
    tasks_root = _create_tasks_fixture(tmp_path)

    first = sync_frontend_benchmarks_repo(
        frontend_repo_dir=frontend_dir,
        generator_script=generator_path,
        tasks_root=tasks_root,
        source_sha="1234567890abcdef",
        python_executable=sys.executable,
    )
    second = sync_frontend_benchmarks_repo(
        frontend_repo_dir=frontend_dir,
        generator_script=generator_path,
        tasks_root=tasks_root,
        source_sha="1234567890abcdef",
        python_executable=sys.executable,
    )

    assert first.changed is True
    assert second.changed is False
    assert second.commit_sha is None


def test_sync_frontend_benchmarks_repo_can_push_to_remote(tmp_path: Path) -> None:
    remote_dir = tmp_path / "frontend-remote.git"
    _run(["git", "init", "--bare", str(remote_dir)], cwd=tmp_path)

    frontend_dir, generator_path = _create_frontend_fixture(tmp_path)
    _run(["git", "remote", "add", "origin", str(remote_dir)], cwd=frontend_dir)
    _run(["git", "push", "-u", "origin", "main"], cwd=frontend_dir)
    tasks_root = _create_tasks_fixture(tmp_path)

    result = sync_frontend_benchmarks_repo(
        frontend_repo_dir=frontend_dir,
        generator_script=generator_path,
        tasks_root=tasks_root,
        source_sha="abcdef1234567890",
        python_executable=sys.executable,
        push=True,
        push_branch="main",
    )

    assert result.changed is True
    assert result.pushed is True
    remote_head = _run(["git", "rev-parse", "main"], cwd=remote_dir)
    assert remote_head == result.commit_sha
