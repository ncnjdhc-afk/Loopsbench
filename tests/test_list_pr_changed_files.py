from __future__ import annotations

import json
from pathlib import Path

from scripts.list_pr_changed_files import list_pr_changed_files, pr_context_from_event


def test_pr_context_from_event_reads_repository_and_number(tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "number": 7,
                "repository": {"full_name": "microsoft/Loopsbench"},
                "pull_request": {"number": 7},
            }
        ),
        encoding="utf-8",
    )

    assert pr_context_from_event(event_path) == ("microsoft/Loopsbench", 7)


def test_list_pr_changed_files_handles_pagination(monkeypatch) -> None:
    responses = {
        "https://api.github.com/repos/microsoft/Loopsbench/pulls/7/files?per_page=100&page=1": [
            {"filename": "tasks/task_alpha/task.yaml"},
            {"filename": "tasks/task_alpha/tests/test_outputs.py"},
        ],
        "https://api.github.com/repos/microsoft/Loopsbench/pulls/7/files?per_page=100&page=2": [],
    }

    def _fake_get_json(*, url: str, token: str | None):
        assert token == "token-value"
        return responses[url]

    monkeypatch.setattr(
        "scripts.list_pr_changed_files._github_get_json", _fake_get_json
    )

    assert list_pr_changed_files(
        repo_full_name="microsoft/Loopsbench",
        pr_number=7,
        token="token-value",
    ) == [
        "tasks/task_alpha/task.yaml",
        "tasks/task_alpha/tests/test_outputs.py",
    ]
