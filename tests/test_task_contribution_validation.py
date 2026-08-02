from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from loopsbench.task_contribution_validation import validate_task_contribution


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_valid_task(
    tmp_path: Path,
    *,
    task_id: str = "task_valid_fixture",
    unit_ids: list[str] | None = None,
    unit_edges: list[dict[str, str]] | None = None,
) -> Path:
    task_dir = tmp_path / task_id
    unit_ids = unit_ids or ["example_unit"]
    unit_edges = unit_edges or []

    _write_text(
        task_dir / "task.yaml",
        "\n".join(
            [
                "instruction: |-",
                "  Solve the example task.",
                "author_name: Fixture Author",
                "author_email: fixture@example.com",
                "difficulty: medium",
                "category: general",
                "parser_name: pytest",
                "max_agent_timeout_sec: 1200",
                "max_test_timeout_sec: 300",
                "run_tests_in_same_shell: false",
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
                        "image": "${LOOPSBENCH_TASK_DOCKER_CLIENT_IMAGE_NAME}",
                        "container_name": "${LOOPSBENCH_TASK_DOCKER_CLIENT_CONTAINER_NAME}",
                        "command": ["sh", "-c", "sleep infinity"],
                        "environment": ["TEST_DIR=${LOOPSBENCH_TEST_DIR}"],
                        "volumes": [
                            "${LOOPSBENCH_TASK_LOGS_PATH}:${LOOPSBENCH_CONTAINER_LOGS_PATH}",
                            "${LOOPSBENCH_TASK_AGENT_LOGS_PATH}:${LOOPSBENCH_CONTAINER_AGENT_LOGS_PATH}",
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

    unit_dag = {
        "repo_id": "fixture",
        "total_units": len(unit_ids),
        "num_layers": len(unit_ids),
        "nodes": [
            {"id": unit_id, "layer": index, "has_tests": True}
            for index, unit_id in enumerate(unit_ids)
        ],
        "edges": unit_edges,
    }
    _write_text(task_dir / "unit_dag.json", json.dumps(unit_dag, indent=2))

    module_dag = {
        "project": "Fixture",
        "description": "Fixture DAG",
        "nodes": [
            {
                "id": unit_id,
                "label": unit_id.replace("_", " ").title(),
                "path": f"src/{unit_id}.py",
                "description": f"Implement {unit_id}.",
                "files_count": 1,
                "loc": 10,
                "impl_order": index + 1,
            }
            for index, unit_id in enumerate(unit_ids)
        ],
        "edges": unit_edges,
    }
    _write_text(
        task_dir / "module_dag.yaml", yaml.safe_dump(module_dag, sort_keys=False)
    )

    slug_map: dict[str, str] = {}
    for unit_id in unit_ids:
        slug_map[f"{unit_id}.yaml"] = f"gold_patches/{unit_id}.diff"
        _write_text(
            task_dir / "requirements" / f"{unit_id}.yaml",
            "\n".join(
                [
                    f'id: "{unit_id}"',
                    f'title: "{unit_id} title"',
                    "category: general",
                    "requirement: |-",
                    f"  Implement {unit_id}.",
                ]
            )
            + "\n",
        )
        _write_text(
            task_dir / "gold_patches" / f"{unit_id}.diff", f"# diff for {unit_id}\n"
        )
    _write_text(task_dir / "slug_diff_map.json", json.dumps(slug_map, indent=2))

    return task_dir


def test_validate_task_contribution_accepts_valid_task(tmp_path: Path) -> None:
    task_dir = _write_valid_task(
        tmp_path,
        unit_ids=["packet_layer", "tcp_engine"],
        unit_edges=[{"from": "packet_layer", "to": "tcp_engine"}],
    )

    report = validate_task_contribution(task_dir)

    assert report.ok is True
    assert report.issues == []


def test_validate_task_contribution_publish_mode_requires_provenance(
    tmp_path: Path,
) -> None:
    task_dir = _write_valid_task(tmp_path)

    report = validate_task_contribution(task_dir, require_provenance=True)

    assert report.ok is False
    missing_fields = {
        issue.message.split("`")[1]
        for issue in report.issues
        if issue.code == "missing_publish_provenance_field"
    }
    assert missing_fields == {
        "source_url",
        "source_repository_url",
        "source_base_revision",
        "proposal_url",
        "license_status",
    }


def test_validate_task_contribution_fails_missing_required_field(
    tmp_path: Path,
) -> None:
    task_dir = _write_valid_task(tmp_path)
    _write_text(
        task_dir / "task.yaml",
        "\n".join(
            [
                "instruction: |-",
                "  Solve the example task.",
                "difficulty: medium",
                "category: general",
                "parser_name: pytest",
                "max_agent_timeout_sec: 1200",
                "max_test_timeout_sec: 300",
                "run_tests_in_same_shell: false",
            ]
        )
        + "\n",
    )

    report = validate_task_contribution(task_dir)

    assert report.ok is False
    assert {issue.code for issue in report.issues} & {
        "missing_author_name",
        "missing_author_email",
    }


def test_validate_task_contribution_fails_invalid_prerequisite(tmp_path: Path) -> None:
    task_dir = _write_valid_task(
        tmp_path,
        unit_ids=["packet_layer"],
        unit_edges=[{"from": "packet_layer", "to": "tcp_engine"}],
    )

    report = validate_task_contribution(task_dir)

    assert report.ok is False
    assert "invalid_prerequisite" in {issue.code for issue in report.issues}


def test_validate_task_contribution_fails_cyclic_graph(tmp_path: Path) -> None:
    task_dir = _write_valid_task(
        tmp_path,
        unit_ids=["alpha", "beta"],
        unit_edges=[
            {"from": "alpha", "to": "beta"},
            {"from": "beta", "to": "alpha"},
        ],
    )

    report = validate_task_contribution(task_dir)

    assert report.ok is False
    assert "unit_dag_cyclic_graph" in {issue.code for issue in report.issues}
    assert "module_dag_cyclic_graph" in {issue.code for issue in report.issues}


def test_validate_task_contribution_fails_duplicate_unit_id(tmp_path: Path) -> None:
    task_dir = _write_valid_task(tmp_path)
    unit_dag = {
        "repo_id": "fixture",
        "total_units": 2,
        "num_layers": 1,
        "nodes": [
            {"id": "dup", "layer": 0, "has_tests": True},
            {"id": "dup", "layer": 0, "has_tests": True},
        ],
        "edges": [],
    }
    _write_text(task_dir / "unit_dag.json", json.dumps(unit_dag, indent=2))

    report = validate_task_contribution(task_dir)

    assert report.ok is False
    assert "duplicate_unit_id" in {issue.code for issue in report.issues}


def test_validate_task_contribution_fails_exposed_gold(tmp_path: Path) -> None:
    task_dir = _write_valid_task(tmp_path)
    _write_text(task_dir / "base" / "solution.sh", "#!/bin/bash\necho hidden\n")

    report = validate_task_contribution(task_dir)

    assert report.ok is False
    assert "exposed_gold" in {issue.code for issue in report.issues}


def test_validate_task_contribution_fails_exposed_hidden_tests(tmp_path: Path) -> None:
    task_dir = _write_valid_task(tmp_path)
    _write_text(
        task_dir / "base" / "tests" / "test_hidden.py",
        "def test_hidden():\n    assert True\n",
    )

    report = validate_task_contribution(task_dir)

    assert report.ok is False
    assert "exposed_hidden_tests" in {issue.code for issue in report.issues}


def test_validate_task_contribution_fails_path_traversal(tmp_path: Path) -> None:
    task_dir = _write_valid_task(tmp_path)
    _write_text(
        task_dir / "slug_diff_map.json",
        json.dumps({"example_unit.yaml": "../outside/example_unit.diff"}, indent=2),
    )

    report = validate_task_contribution(task_dir)

    assert report.ok is False
    assert "path_traversal" in {issue.code for issue in report.issues}


def test_checked_in_template_is_static_valid(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    template_src = repo_root / "tasks" / "_template"
    task_dir = tmp_path / "task_template_fixture"
    shutil.copytree(template_src, task_dir)

    report = validate_task_contribution(task_dir)

    assert report.ok is True
    assert report.issues == []
