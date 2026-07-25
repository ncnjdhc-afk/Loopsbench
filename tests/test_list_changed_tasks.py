from __future__ import annotations

from pathlib import Path

from scripts.list_changed_tasks import load_paths_file, task_dirs_from_paths


def test_task_dirs_from_paths_filters_only_task_directories() -> None:
    paths = [
        "README.md",
        "tasks/task_alpha/task.yaml",
        "tasks/task_alpha/tests/test_outputs.py",
        "tasks/task_beta/unit_dag.json",
        "tasks/_template/task.yaml",
        "other/tasks/task_gamma/task.yaml",
    ]

    assert task_dirs_from_paths(paths) == ["tasks/task_alpha", "tasks/task_beta"]


def test_task_dirs_from_paths_deduplicates_and_normalizes() -> None:
    paths = [
        str(Path("tasks") / "task_alpha" / "task.yaml"),
        str(Path("tasks") / "task_alpha" / "Dockerfile"),
        str(Path("tasks") / "task_beta" / "module_dag.yaml"),
    ]

    assert task_dirs_from_paths(paths) == ["tasks/task_alpha", "tasks/task_beta"]


def test_load_paths_file_reads_non_empty_lines(tmp_path: Path) -> None:
    paths_file = tmp_path / "changed_paths.txt"
    paths_file.write_text(
        "\n".join(
            [
                "tasks/task_alpha/task.yaml",
                "",
                "tasks/task_alpha/tests/test_outputs.py",
                "README.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert load_paths_file(paths_file) == [
        "tasks/task_alpha/task.yaml",
        "tasks/task_alpha/tests/test_outputs.py",
        "README.md",
    ]
