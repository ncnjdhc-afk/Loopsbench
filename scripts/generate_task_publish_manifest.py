#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loopsbench.handlers.trial_handler import Task  # noqa: E402

DEFAULT_REPO_HTML_URL = "https://github.com/microsoft/Loopsbench"


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _instruction_preview(instruction: str) -> str:
    blocks = [block.strip() for block in instruction.split("\n\n") if block.strip()]
    for block in blocks:
        normalized = _normalize_text(block)
        if normalized:
            return normalized
    return _normalize_text(instruction)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(
        candidate for candidate in root.rglob("*") if candidate.is_file()
    ):
        relative_path = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative_path)
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def _bundle_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = ""
    tarinfo.gname = ""
    tarinfo.mtime = 0
    tarinfo.mode = 0o644 if tarinfo.isfile() else 0o755
    return tarinfo


def _write_bundle(task_dir: Path, bundle_path: Path) -> None:
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle_path, "w:gz") as archive:
        archive.add(
            task_dir,
            arcname=f"tasks/{task_dir.name}",
            recursive=True,
            filter=_bundle_filter,
        )


def _git_sha(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload or {}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must decode to a JSON object")
    return payload


def _provenance(raw_task: dict[str, Any]) -> dict[str, str | None]:
    def _value(key: str) -> str | None:
        raw = str(raw_task.get(key) or "").strip()
        return raw or None

    return {
        "sourceUrl": _value("source_url"),
        "sourceRepositoryUrl": _value("source_repository_url"),
        "sourceBaseRevision": _value("source_base_revision"),
        "proposalUrl": _value("proposal_url"),
        "licenseStatus": _value("license_status"),
    }


def _contributor_metadata(
    raw_task: dict[str, Any], task: Task
) -> dict[str, str | None]:
    def _value(key: str) -> str | None:
        raw = str(raw_task.get(key) or "").strip()
        return raw or None

    return {
        "github": _value("contributor_github"),
        "organization": _value("contributor_organization"),
        "name": _value("contributor_name") or task.author_name,
        "email": _value("contributor_email") or task.author_email,
    }


def build_publish_record(
    task_dir: Path,
    *,
    output_dir: Path,
    git_sha: str,
    repo_html_url: str = DEFAULT_REPO_HTML_URL,
) -> dict[str, Any]:
    resolved_task_dir = task_dir.resolve()
    raw_task = _read_yaml(resolved_task_dir / "task.yaml")
    task = Task.model_validate(raw_task)
    module_dag = _read_yaml(resolved_task_dir / "module_dag.yaml")
    unit_dag = _read_json(resolved_task_dir / "unit_dag.json")

    bundle_name = f"{resolved_task_dir.name}-{git_sha[:12]}.tar.gz"
    bundle_path = output_dir / "bundles" / bundle_name
    _write_bundle(resolved_task_dir, bundle_path)

    title = _normalize_text(str(module_dag.get("project") or resolved_task_dir.name))
    summary = _normalize_text(
        str(module_dag.get("description") or "")
    ) or _instruction_preview(task.instruction)
    module_nodes = list(module_dag.get("nodes") or [])
    module_edges = list(module_dag.get("edges") or [])
    unit_nodes = list(unit_dag.get("nodes") or [])
    unit_edges = list(unit_dag.get("edges") or [])

    return {
        "taskId": resolved_task_dir.name,
        "title": title,
        "summary": summary,
        "difficulty": task.difficulty.value,
        "category": task.category,
        "authorName": task.author_name,
        "authorEmail": task.author_email,
        "contributor": _contributor_metadata(raw_task, task),
        "version": git_sha,
        "sourceCommit": git_sha,
        "publishedAt": datetime.now(UTC).isoformat(),
        "repoUrl": f"{repo_html_url}/tree/{git_sha}/tasks/{resolved_task_dir.name}",
        "taskPath": f"tasks/{resolved_task_dir.name}",
        "bundle": {
            "path": str(bundle_path.relative_to(output_dir)),
            "sha256": _file_sha256(bundle_path),
            "treeSha256": _tree_sha256(resolved_task_dir),
        },
        "moduleDag": {
            "nodeCount": len(module_nodes),
            "edgeCount": len(module_edges),
        },
        "unitDag": {
            "nodeCount": len(unit_nodes),
            "edgeCount": len(unit_edges),
            "testedUnits": sum(1 for node in unit_nodes if bool(node.get("has_tests"))),
        },
        "provenance": _provenance(raw_task),
    }


def _collect_task_dirs(task_dirs: list[Path], tasks_file: Path | None) -> list[Path]:
    collected = [path.resolve() for path in task_dirs]
    if tasks_file is not None:
        for line in tasks_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                collected.append(Path(stripped).resolve())
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in collected:
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def generate_publish_manifest(
    *,
    task_dirs: list[Path],
    output_dir: Path,
    git_sha: str,
    repo_html_url: str = DEFAULT_REPO_HTML_URL,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir = output_dir / "tasks"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    records = [
        build_publish_record(
            task_dir,
            output_dir=output_dir,
            git_sha=git_sha,
            repo_html_url=repo_html_url,
        )
        for task_dir in task_dirs
    ]
    records.sort(key=lambda item: item["taskId"])

    for record in records:
        path = metadata_dir / f"{record['taskId']}.json"
        path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    index = {
        "version": git_sha,
        "generatedAt": datetime.now(UTC).isoformat(),
        "taskCount": len(records),
        "tasks": records,
    }
    (output_dir / "index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return index


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate publish metadata and deterministic task bundles."
    )
    parser.add_argument(
        "--task-dir",
        action="append",
        type=Path,
        default=[],
        help="Task directory to publish.",
    )
    parser.add_argument(
        "--tasks-file",
        type=Path,
        help="File containing task directories, one per line.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory for publish metadata and bundles.",
    )
    parser.add_argument(
        "--git-sha", help="Version SHA to record. Defaults to `git rev-parse HEAD`."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root used when inferring git SHA.",
    )
    parser.add_argument(
        "--repo-html-url",
        default=DEFAULT_REPO_HTML_URL,
        help="Repository HTML URL for task links.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to also write the generated index JSON.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    task_dirs = _collect_task_dirs(args.task_dir, args.tasks_file)
    if not task_dirs:
        raise SystemExit("No task directories provided.")

    git_sha = args.git_sha or _git_sha(args.repo_root.resolve())
    index = generate_publish_manifest(
        task_dirs=task_dirs,
        output_dir=args.output_dir.resolve(),
        git_sha=git_sha,
        repo_html_url=args.repo_html_url,
    )
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(index, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
