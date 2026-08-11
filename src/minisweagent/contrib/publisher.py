import re
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from minisweagent.contrib.discovery import references_issue
from minisweagent.contrib.evidence import GateError, TCFlowRunResult
from minisweagent.contrib.github import Command


class ContributionGitHub(Protocol):
    def viewer_login(self) -> str: ...

    def prior_pull_request_text(self, repository: str, author: str) -> list[str]: ...

    def run(self, command: Command) -> str: ...


class DuplicateContributionError(GateError):
    pass


class PublicationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["dry-run", "published"]
    command: Command
    url: str | None = None


_CREDENTIAL_PATTERN = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|BEGIN [A-Z ]*PRIVATE KEY)"
)


def validate_pr_body(body_file: Path, issue_number: int) -> None:
    if not body_file.is_file() or body_file.is_symlink():
        raise GateError(f"PR body must be a regular file: {body_file}")
    if body_file.stat().st_size > 64 * 1024:
        raise GateError("PR body exceeds the 64 KiB safety limit")
    body = body_file.read_text(encoding="utf-8")
    if not references_issue(body, issue_number):
        raise GateError(f"PR body must reference #{issue_number}")
    if _CREDENTIAL_PATTERN.search(body):
        raise GateError("PR body contains credential-like content")


class DraftPRPublisher:
    def __init__(self, github: ContributionGitHub) -> None:
        self._github = github

    def _plan(
        self,
        *,
        repository: str,
        issue_number: int,
        base: str,
        head: str,
        title: str,
        body_file: Path,
        evidence: TCFlowRunResult,
    ) -> Command:
        evidence.assert_publishable(repository, issue_number)
        validate_pr_body(body_file, issue_number)
        author = self._github.viewer_login()
        prior_text = self._github.prior_pull_request_text(repository, author)
        if any(references_issue(text, issue_number) for text in prior_text):
            raise DuplicateContributionError(f"Authenticated user already has a PR referencing #{issue_number}")
        return (
            "pr",
            "create",
            "--repo",
            repository,
            "--base",
            base,
            "--head",
            head,
            "--title",
            title,
            "--body-file",
            str(body_file),
            "--draft",
        )

    def publish(
        self,
        *,
        repository: str,
        issue_number: int,
        base: str,
        head: str,
        title: str,
        body_file: Path,
        evidence: TCFlowRunResult,
        publish: bool = False,
    ) -> PublicationResult:
        command = self._plan(
            repository=repository,
            issue_number=issue_number,
            base=base,
            head=head,
            title=title,
            body_file=body_file,
            evidence=evidence,
        )
        if not publish:
            return PublicationResult(status="dry-run", command=command)
        url = self._github.run(command)
        return PublicationResult(status="published", command=command, url=url)
