from pathlib import Path

import pytest

from minisweagent.contrib.evidence import GateError, TCFlowRunResult
from minisweagent.contrib.publisher import DraftPRPublisher, DuplicateContributionError


class InMemoryGitHub:
    def __init__(self, prior_prs: list[str] | None = None) -> None:
        self.prior_prs = prior_prs or []
        self.executed: list[tuple[str, ...]] = []

    def viewer_login(self) -> str:
        return "Tiancheng-Xu"

    def prior_pull_request_text(self, repository: str, author: str) -> list[str]:
        assert repository == "acme/tool"
        assert author == "Tiancheng-Xu"
        return self.prior_prs

    def run(self, command: tuple[str, ...]) -> str:
        self.executed.append(command)
        return "https://github.com/acme/tool/pull/99"


def evidence() -> TCFlowRunResult:
    return TCFlowRunResult.model_validate(
        {
            "version": "tc-flow-run-result-v1",
            "run_id": "run-1",
            "feature": "fix-config-validation",
            "contract_hash": "a" * 64,
            "target_repository": "acme/tool",
            "target_issue": 42,
            "task_review": "pass",
            "feature_qa": "pass",
            "stop_hook": "ALLOW",
            "repository_policy": "local-pass",
            "tests": [{"command": "pytest", "status": "pass", "summary": "12 passed"}],
            "blockers": [],
        }
    )


def test_publish_defaults_to_dry_run_and_always_plans_draft(tmp_path: Path) -> None:
    body = tmp_path / "body.md"
    body.write_text("Fixes #42", encoding="utf-8")
    github = InMemoryGitHub()

    result = DraftPRPublisher(github).publish(
        repository="acme/tool",
        issue_number=42,
        base="main",
        head="Tiancheng-Xu:fix-42",
        title="fix: validate malformed configuration",
        body_file=body,
        evidence=evidence(),
    )

    assert result.status == "dry-run"
    assert "--draft" in result.command
    assert github.executed == []


def test_publish_rejects_duplicate_issue_reference(tmp_path: Path) -> None:
    body = tmp_path / "body.md"
    body.write_text("Fixes #42", encoding="utf-8")
    github = InMemoryGitHub(prior_prs=["Earlier work closes #42"])

    with pytest.raises(DuplicateContributionError, match="#42"):
        DraftPRPublisher(github).publish(
            repository="acme/tool",
            issue_number=42,
            base="main",
            head="Tiancheng-Xu:fix-42",
            title="fix: validate malformed configuration",
            body_file=body,
            evidence=evidence(),
        )


def test_live_publish_invokes_gh_and_returns_url(tmp_path: Path) -> None:
    body = tmp_path / "body.md"
    body.write_text("Fixes #42", encoding="utf-8")
    github = InMemoryGitHub()

    result = DraftPRPublisher(github).publish(
        repository="acme/tool",
        issue_number=42,
        base="main",
        head="Tiancheng-Xu:fix-42",
        title="fix: validate malformed configuration",
        body_file=body,
        evidence=evidence(),
        publish=True,
    )

    assert result.status == "published"
    assert result.url == "https://github.com/acme/tool/pull/99"
    assert github.executed == [result.command]


@pytest.mark.parametrize(
    ("body_text", "expected_error"),
    [
        ("Useful change, but no issue reference", "must reference #42"),
        ("Fixes #42\nToken: " + "gh" + "p_abcdefghijklmnopqrstuvwxyz123456", "credential-like"),
    ],
)
def test_publish_rejects_unsafe_pr_body(tmp_path: Path, body_text: str, expected_error: str) -> None:
    body = tmp_path / "body.md"
    body.write_text(body_text, encoding="utf-8")

    with pytest.raises(GateError, match=expected_error):
        DraftPRPublisher(InMemoryGitHub()).publish(
            repository="acme/tool",
            issue_number=42,
            base="main",
            head="Tiancheng-Xu:fix-42",
            title="fix: validate malformed configuration",
            body_file=body,
            evidence=evidence(),
        )
