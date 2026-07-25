from scripts.check_pr_proposal_url import validate_proposal_url
from scripts.check_task_pr_template import validate_pr_template_fields


def test_validate_proposal_url_accepts_expected_repo() -> None:
    ok, message = validate_proposal_url(
        "Proposal: https://github.com/microsoft/Loopsbench/issues/42",
        expected_repo="microsoft/Loopsbench",
    )

    assert ok is True
    assert "Proposal issue #42" in message


def test_validate_proposal_url_rejects_missing_url() -> None:
    ok, message = validate_proposal_url(
        "No issue link here.", expected_repo="microsoft/Loopsbench"
    )

    assert ok is False
    assert "must include a GitHub Proposal issue URL" in message


def test_validate_proposal_url_rejects_wrong_repo() -> None:
    ok, message = validate_proposal_url(
        "Proposal: https://github.com/example/project/issues/9",
        expected_repo="microsoft/Loopsbench",
    )

    assert ok is False
    assert "must point to microsoft/Loopsbench" in message


def test_validate_pr_template_fields_accepts_complete_body() -> None:
    ok, errors = validate_pr_template_fields(
        """
- Proposal URL: https://github.com/microsoft/Loopsbench/issues/42
- Proposal approval status: proposal: approved
- Task ID: task_example
- Task title: Example task
- Source URL: https://github.com/example/project/pull/123
- Base revision: abcdef123
- Modules: packet layer, tcp engine
- Units: packet_layer, tcp_engine
- Dependency DAG summary: packet_layer -> tcp_engine
- Source evidence for dependency edges: PR 123 must land before PR 124.
- Gold solution or gold patch strategy: Derived from upstream patch sequence.
- Full-task testing strategy: Hidden end-to-end tests plus protocol checks.
- Unit-level verification strategy: Each unit has its own fail-to-pass requirement file.
- Why the verifier rejects partial / incorrect implementations: Ancestor-only states fail descendant checks.
- License status: MIT, redistributable.
""".strip()
    )

    assert ok is True
    assert errors == []


def test_validate_pr_template_fields_rejects_missing_required_values() -> None:
    ok, errors = validate_pr_template_fields(
        """
- Proposal URL:
- Proposal approval status:
- Task ID: task_example
- Task title: Example task
- Source URL:
- Base revision:
""".strip()
    )

    assert ok is False
    assert any("Proposal URL" in error for error in errors)
    assert any("Proposal approval status" in error for error in errors)
    assert any("Source URL" in error for error in errors)
    assert any("Base revision" in error for error in errors)


def test_validate_pr_template_fields_rejects_placeholder_values() -> None:
    ok, errors = validate_pr_template_fields(
        """
- Proposal URL: https://github.com/microsoft/Loopsbench/issues/42
- Proposal approval status: pending
- Task ID: <task-id>
- Task title: TBD
- Source URL: https://github.com/example/project/pull/123
- Base revision: abcdef123
- Modules: module-a
- Units: unit-a
- Dependency DAG summary: unit-a
- Source evidence for dependency edges: upstream docs
- Gold solution or gold patch strategy: upstream patch
- Full-task testing strategy: hidden tests
- Unit-level verification strategy: one unit
- Why the verifier rejects partial / incorrect implementations: strict tests
- License status: MIT
""".strip()
    )

    assert ok is False
    assert any("approved" in error.casefold() for error in errors)
    assert any("Task ID" in error for error in errors)
    assert any("Task title" in error for error in errors)
