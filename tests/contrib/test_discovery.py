from datetime import UTC, datetime, timedelta

from minisweagent.contrib.discovery import rank_opportunities
from minisweagent.contrib.models import IssueCandidate, RepositoryCandidate

NOW = datetime(2026, 8, 11, tzinfo=UTC)


def repository(**overrides: object) -> RepositoryCandidate:
    values = {
        "full_name": "acme/active",
        "html_url": "https://github.com/acme/active",
        "description": "Maintained developer tool",
        "stars": 2_000,
        "pushed_at": NOW - timedelta(days=2),
        "license_spdx": "MIT",
        "language": "Python",
    }
    values.update(overrides)
    return RepositoryCandidate.model_validate(values)


def issue(**overrides: object) -> IssueCandidate:
    values = {
        "repository": "acme/active",
        "number": 42,
        "title": "Handle malformed configuration",
        "html_url": "https://github.com/acme/active/issues/42",
        "body": "Add validation and regression tests.",
        "comments": 2,
        "created_at": NOW - timedelta(days=10),
        "labels": ["good first issue", "bug"],
        "assignees": 0,
    }
    values.update(overrides)
    return IssueCandidate.model_validate(values)


def test_rank_opportunities_filters_risky_stale_and_duplicate_candidates() -> None:
    repositories = [
        repository(),
        repository(full_name="acme/stale", pushed_at=NOW - timedelta(days=120)),
        repository(full_name="acme/unlicensed", license_spdx="NOASSERTION"),
        repository(full_name="acme/tiny", stars=12),
    ]
    issues = {
        "acme/active": [
            issue(),
            issue(number=43, title="Already being fixed"),
            issue(number=44, assignees=1),
            issue(number=45, comments=30),
        ],
        "acme/stale": [issue(repository="acme/stale", number=1)],
        "acme/unlicensed": [issue(repository="acme/unlicensed", number=1)],
        "acme/tiny": [issue(repository="acme/tiny", number=1)],
    }

    result = rank_opportunities(
        repositories,
        issues,
        prior_pull_request_text={"acme/active": ["Fixes #43"]},
        now=NOW,
        min_stars=100,
        active_within_days=30,
        max_comments=10,
    )

    assert [(item.repository.full_name, item.issue.number) for item in result] == [("acme/active", 42)]


def test_rank_opportunities_is_deterministic() -> None:
    repositories = [repository(full_name="zeta/tool"), repository(full_name="alpha/tool")]
    issues = {
        "zeta/tool": [issue(repository="zeta/tool", number=1)],
        "alpha/tool": [issue(repository="alpha/tool", number=2)],
    }

    result = rank_opportunities(repositories, issues, prior_pull_request_text={}, now=NOW)

    assert [item.repository.full_name for item in result] == ["alpha/tool", "zeta/tool"]
