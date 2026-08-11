import json
import subprocess
from collections.abc import Callable, Mapping
from typing import Any

from minisweagent.contrib.models import IssueCandidate, RepositoryCandidate

Command = tuple[str, ...]
Runner = Callable[[Command], str]


class GitHubCommandError(RuntimeError):
    pass


def classify_gh_failure(stderr: str, *, return_code: int, safe_command: str) -> GitHubCommandError:
    normalized = stderr.lower()
    if "secondary rate limit" in normalized:
        return GitHubCommandError("GitHub secondary rate limit reached; stop this run and retry later")
    if "rate limit exceeded" in normalized:
        return GitHubCommandError("GitHub API rate limit reached; stop this run and retry later")
    if "http 401" in normalized or "authentication" in normalized:
        return GitHubCommandError("GitHub authentication failed; check the existing gh login")
    return GitHubCommandError(f"gh command failed with exit code {return_code}: {safe_command}")


def run_gh(command: Command) -> str:
    result = subprocess.run(("gh", *command), capture_output=True, text=True, check=False)
    if result.returncode:
        safe_command = " ".join(command[:4])
        raise classify_gh_failure(result.stderr, return_code=result.returncode, safe_command=safe_command)
    return result.stdout.strip()


class GitHubClient:
    def __init__(self, runner: Runner = run_gh) -> None:
        self._runner = runner

    def run(self, command: Command) -> str:
        return self._runner(command)

    def _api(self, endpoint: str, parameters: Mapping[str, str] | None = None) -> Any:
        command: list[str] = ["api", "--method", "GET", endpoint]
        for key, value in (parameters or {}).items():
            command.extend(("-f", f"{key}={value}"))
        return json.loads(self.run(tuple(command)))

    def viewer_login(self) -> str:
        payload = self._api("user")
        return str(payload["login"])

    def search_repositories(self, query: str, *, limit: int = 20) -> list[RepositoryCandidate]:
        payload = self._api(
            "search/repositories",
            {"q": query, "sort": "updated", "order": "desc", "per_page": str(limit)},
        )
        return [
            RepositoryCandidate(
                full_name=item["full_name"],
                html_url=item["html_url"],
                description=item.get("description") or "",
                stars=item["stargazers_count"],
                pushed_at=item["pushed_at"],
                license_spdx=(item.get("license") or {}).get("spdx_id") or "NOASSERTION",
                language=item.get("language"),
            )
            for item in payload.get("items", [])
        ]

    def search_good_first_issues(self, repository: str, *, limit: int = 20) -> list[IssueCandidate]:
        query = f'repo:{repository} is:issue is:open no:assignee label:"good first issue"'
        payload = self._api(
            "search/issues",
            {"q": query, "sort": "created", "order": "desc", "per_page": str(limit)},
        )
        return [
            IssueCandidate(
                repository=repository,
                number=item["number"],
                title=item["title"],
                html_url=item["html_url"],
                body=item.get("body") or "",
                comments=item["comments"],
                created_at=item["created_at"],
                labels=[label["name"] for label in item.get("labels", [])],
                assignees=len(item.get("assignees", [])),
            )
            for item in payload.get("items", [])
        ]

    def prior_pull_request_text(self, repository: str, author: str) -> list[str]:
        query = f"repo:{repository} is:pr author:{author}"
        payload = self._api("search/issues", {"q": query, "per_page": "100"})
        return [
            "\n".join((item.get("title") or "", item.get("body") or "", item.get("html_url") or ""))
            for item in payload.get("items", [])
        ]
