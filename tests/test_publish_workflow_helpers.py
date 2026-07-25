from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.ensure_publish_context import publish_allowed
from scripts.generate_task_publish_manifest import generate_publish_manifest


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_valid_task(tmp_path: Path, task_id: str = "task_publish_fixture") -> Path:
    task_dir = tmp_path / task_id
    _write_text(
        task_dir / "task.yaml",
        "\n".join(
            [
                "instruction: |-",
                "  Implement the publish fixture.",
                "author_name: Fixture Author",
                "author_email: fixture@example.com",
                "difficulty: medium",
                "category: general",
                "parser_name: pytest",
                "max_agent_timeout_sec: 1200",
                "max_test_timeout_sec: 300",
                "run_tests_in_same_shell: false",
                "source_url: https://github.com/example/upstream/pull/123",
                "source_repository_url: https://github.com/example/upstream",
                "source_base_revision: abcdef1234",
                "proposal_url: https://github.com/microsoft/Loopsbench/issues/42",
                "license_status: MIT",
                "contributor_github: fixture-gh",
                "contributor_organization: Fixture Org",
            ]
        )
        + "\n",
    )
    _write_text(task_dir / "Dockerfile", "FROM python:3.13-slim\nWORKDIR /workspace\n")
    _write_text(
        task_dir / "docker-compose.yaml",
        yaml.safe_dump(
            {
                "services": {
                    "client": {
                        "build": {"dockerfile": "Dockerfile"},
                        "image": "${LHB_TASK_DOCKER_CLIENT_IMAGE_NAME}",
                        "container_name": "${LHB_TASK_DOCKER_CLIENT_CONTAINER_NAME}",
                        "command": ["sh", "-c", "sleep infinity"],
                        "environment": ["TEST_DIR=${LHB_TEST_DIR}"],
                        "volumes": [
                            "${LHB_TASK_LOGS_PATH}:${LHB_CONTAINER_LOGS_PATH}",
                            "${LHB_TASK_AGENT_LOGS_PATH}:${LHB_CONTAINER_AGENT_LOGS_PATH}",
                        ],
                    }
                }
            },
            sort_keys=False,
        ),
    )
    _write_text(task_dir / "solution.sh", "#!/bin/bash\nexit 0\n")
    _write_text(
        task_dir / "run-tests.sh",
        "#!/bin/bash\npython3 -m pytest ${TEST_DIR:-/tests}/test_outputs.py\n",
    )
    _write_text(
        task_dir / "tests" / "test_outputs.py", "def test_ok():\n    assert True\n"
    )
    _write_text(task_dir / "base" / "README.md", "base workspace\n")
    _write_text(
        task_dir / "unit_dag.json",
        json.dumps(
            {
                "repo_id": "fixture",
                "total_units": 1,
                "num_layers": 1,
                "nodes": [{"id": "example_unit", "layer": 0, "has_tests": True}],
                "edges": [],
            },
            indent=2,
        ),
    )
    _write_text(
        task_dir / "module_dag.yaml",
        yaml.safe_dump(
            {
                "project": "Publish Fixture",
                "description": "Fixture task for publish metadata generation.",
                "nodes": [
                    {
                        "id": "example_module",
                        "label": "Example Module",
                        "path": "src/example.py",
                        "description": "Implement example behavior.",
                        "files_count": 1,
                        "loc": 10,
                        "impl_order": 1,
                    }
                ],
                "edges": [],
            },
            sort_keys=False,
        ),
    )
    _write_text(
        task_dir / "requirements" / "example_unit.yaml",
        "\n".join(
            [
                'id: "example_unit"',
                'title: "Example unit"',
                "category: general",
                "requirement: |-",
                "  Implement the example unit.",
            ]
        )
        + "\n",
    )
    _write_text(
        task_dir / "slug_diff_map.json",
        json.dumps({"example_unit.yaml": "gold_patches/example_unit.diff"}, indent=2),
    )
    _write_text(task_dir / "gold_patches" / "example_unit.diff", "# patch\n")
    return task_dir


def test_publish_allowed_accepts_default_branch_push() -> None:
    ok, message = publish_allowed(
        event_name="push", ref_name="main", default_branch="main"
    )

    assert ok is True
    assert "accepted" in message


def test_publish_allowed_rejects_non_default_branch() -> None:
    ok, message = publish_allowed(
        event_name="push", ref_name="feature/test", default_branch="main"
    )

    assert ok is False
    assert "default branch" in message


def test_generate_publish_manifest_writes_metadata_and_bundle(tmp_path: Path) -> None:
    task_dir = _write_valid_task(tmp_path)
    output_dir = tmp_path / "publish-output"

    index = generate_publish_manifest(
        task_dirs=[task_dir],
        output_dir=output_dir,
        git_sha="1234567890abcdef1234567890abcdef12345678",
    )

    assert index["taskCount"] == 1
    task_record = index["tasks"][0]
    assert task_record["taskId"] == "task_publish_fixture"
    assert task_record["authorName"] == "Fixture Author"
    assert task_record["authorEmail"] == "fixture@example.com"
    assert task_record["contributor"]["github"] == "fixture-gh"
    assert task_record["contributor"]["organization"] == "Fixture Org"
    assert task_record["contributor"]["name"] == "Fixture Author"
    assert task_record["version"] == "1234567890abcdef1234567890abcdef12345678"
    assert (
        task_record["provenance"]["proposalUrl"]
        == "https://github.com/microsoft/Loopsbench/issues/42"
    )
    assert len(task_record["bundle"]["sha256"]) == 64
    assert len(task_record["bundle"]["treeSha256"]) == 64

    bundle_path = output_dir / task_record["bundle"]["path"]
    metadata_path = output_dir / "tasks" / "task_publish_fixture.json"
    assert bundle_path.is_file()
    assert metadata_path.is_file()
