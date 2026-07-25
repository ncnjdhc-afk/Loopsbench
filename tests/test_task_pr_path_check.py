from scripts.check_task_pr_paths import validate_task_pr_paths


def test_validate_task_pr_paths_accepts_single_task_directory() -> None:
    ok, errors = validate_task_pr_paths(
        [
            "tasks/task_alpha/task.yaml",
            "tasks/task_alpha/tests/test_outputs.py",
            "tasks/task_alpha/module_dag.yaml",
        ]
    )

    assert ok is True
    assert errors == []


def test_validate_task_pr_paths_rejects_multiple_task_directories() -> None:
    ok, errors = validate_task_pr_paths(
        [
            "tasks/task_alpha/task.yaml",
            "tasks/task_beta/task.yaml",
        ]
    )

    assert ok is False
    assert any("exactly one task directory" in error for error in errors)


def test_validate_task_pr_paths_rejects_non_task_files_when_task_changes_exist() -> (
    None
):
    ok, errors = validate_task_pr_paths(
        [
            "tasks/task_alpha/task.yaml",
            "README.md",
        ]
    )

    assert ok is False
    assert any("README.md" in error for error in errors)


def test_validate_task_pr_paths_is_noop_for_non_task_prs() -> None:
    ok, errors = validate_task_pr_paths(
        [
            "README.md",
            "docs/notes.md",
        ]
    )

    assert ok is True
    assert errors == []


def test_validate_task_pr_paths_rejects_parent_traversal_segments() -> None:
    ok, errors = validate_task_pr_paths(
        [
            "tasks/task_alpha/../README.md",
        ]
    )

    assert ok is False
    assert any("..` segments are not allowed" in error for error in errors)


def test_validate_task_pr_paths_rejects_absolute_paths() -> None:
    ok, errors = validate_task_pr_paths(
        [
            "/abs/path",
        ]
    )

    assert ok is False
    assert any("absolute paths" in error for error in errors)
