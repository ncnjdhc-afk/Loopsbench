from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loopsbench.task_images import (
    build_manifest_records,
    discover_nonseg_task_images,
    discover_task_images,
)


def _write_task(task_dir: Path) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        yaml.safe_dump(
            {
                "instruction": "Run the task.",
                "author_name": "test",
                "difficulty": "medium",
                "docker": {"compose_file": "docker-compose.yaml"},
            },
            sort_keys=False,
        )
    )
    (task_dir / "docker-compose.yaml").write_text(
        yaml.safe_dump(
            {
                "services": {
                    "client": {
                        "build": {
                            "context": ".",
                            "dockerfile": "Dockerfile",
                        }
                    }
                }
            },
            sort_keys=False,
        )
    )
    (task_dir / "Dockerfile").write_text("FROM scratch\n")


def test_build_manifest_records_includes_seg_tasks(tmp_path: Path) -> None:
    tasks_root = tmp_path / "tasks"
    tasks_root.mkdir()
    _write_task(tasks_root / "task_compiler")
    _write_task(tasks_root / "task_hadoop_seg05")

    records = build_manifest_records(
        tasks_root=tasks_root,
        namespace="exampleorg",
        tag="latest",
        platform="linux/amd64",
        source_ref="abc123",
    )

    assert [record.task_id for record in records] == [
        "task_compiler",
        "task_hadoop_seg05",
    ]

    seg_record = next(
        record for record in records if record.task_id == "task_hadoop_seg05"
    )
    assert seg_record.image_ref == "exampleorg/loopsbench-task-hadoop-seg05:latest"
    assert seg_record.compose_file == "tasks/task_hadoop_seg05/docker-compose.yaml"
    assert seg_record.dockerfile_path == "tasks/task_hadoop_seg05/Dockerfile"


def test_discover_nonseg_task_images_alias_includes_seg_tasks(
    tmp_path: Path,
) -> None:
    tasks_root = tmp_path / "tasks"
    tasks_root.mkdir()
    _write_task(tasks_root / "task_compiler")
    _write_task(tasks_root / "task_hadoop_seg05")

    assert [source.task_id for source in discover_task_images(tasks_root)] == [
        "task_compiler",
        "task_hadoop_seg05",
    ]
    assert [
        source.task_id for source in discover_nonseg_task_images(tasks_root)
    ] == [
        "task_compiler",
        "task_hadoop_seg05",
    ]
