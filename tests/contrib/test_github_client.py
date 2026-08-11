import json

from minisweagent.contrib.github import GitHubClient, classify_gh_failure


class RecordingRunner:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command: tuple[str, ...]) -> str:
        self.commands.append(command)
        return next(self.responses)


def test_github_client_uses_get_api_and_parses_candidates() -> None:
    runner = RecordingRunner(
        [
            json.dumps(
                {
                    "items": [
                        {
                            "full_name": "acme/tool",
                            "html_url": "https://github.com/acme/tool",
                            "description": "Tool",
                            "stargazers_count": 900,
                            "pushed_at": "2026-08-10T10:00:00Z",
                            "license": {"spdx_id": "Apache-2.0"},
                            "language": "Python",
                        }
                    ]
                }
            )
        ]
    )
    client = GitHubClient(runner=runner)

    repositories = client.search_repositories("stars:>=100", limit=5)

    assert repositories[0].full_name == "acme/tool"
    assert repositories[0].license_spdx == "Apache-2.0"
    assert runner.commands == [
        (
            "api",
            "--method",
            "GET",
            "search/repositories",
            "-f",
            "q=stars:>=100",
            "-f",
            "sort=updated",
            "-f",
            "order=desc",
            "-f",
            "per_page=5",
        )
    ]


def test_github_client_searches_unassigned_good_first_issues() -> None:
    runner = RecordingRunner(
        [
            json.dumps(
                {
                    "items": [
                        {
                            "number": 7,
                            "title": "Add input validation",
                            "html_url": "https://github.com/acme/tool/issues/7",
                            "body": "Regression test included",
                            "comments": 1,
                            "created_at": "2026-08-01T00:00:00Z",
                            "labels": [{"name": "good first issue"}],
                            "assignees": [],
                        }
                    ]
                }
            )
        ]
    )
    client = GitHubClient(runner=runner)

    issues = client.search_good_first_issues("acme/tool", limit=10)

    assert issues[0].repository == "acme/tool"
    assert issues[0].labels == ["good first issue"]
    assert "is:issue is:open no:assignee" in runner.commands[0][5]


def test_classify_gh_failure_stops_on_secondary_rate_limit_without_raw_response() -> None:
    error = classify_gh_failure(
        "You have exceeded a secondary rate limit. Request ID: private-diagnostic-id",
        return_code=1,
        safe_command="api --method GET search/issues",
    )

    assert str(error) == "GitHub secondary rate limit reached; stop this run and retry later"
    assert "private-diagnostic-id" not in str(error)
