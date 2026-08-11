import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta

from minisweagent.contrib.models import IssueCandidate, Opportunity, RepositoryCandidate

DEFAULT_LICENSES = frozenset({"Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MIT", "MPL-2.0"})


def references_issue(text: str, issue_number: int) -> bool:
    return bool(re.search(rf"(?<!\d)#{issue_number}\b|/issues/{issue_number}\b", text, flags=re.IGNORECASE))


def rank_opportunities(
    repositories: Sequence[RepositoryCandidate],
    issues_by_repository: Mapping[str, Sequence[IssueCandidate]],
    *,
    prior_pull_request_text: Mapping[str, Sequence[str]],
    now: datetime,
    min_stars: int = 100,
    active_within_days: int = 30,
    max_comments: int = 10,
    allowed_licenses: frozenset[str] = DEFAULT_LICENSES,
) -> list[Opportunity]:
    active_after = now - timedelta(days=active_within_days)
    opportunities: list[Opportunity] = []
    for repository in repositories:
        if (
            repository.stars < min_stars
            or repository.pushed_at < active_after
            or repository.license_spdx not in allowed_licenses
        ):
            continue
        prior_text = prior_pull_request_text.get(repository.full_name, ())
        for issue in issues_by_repository.get(repository.full_name, ()):
            if (
                issue.assignees
                or issue.comments > max_comments
                or "good first issue" not in {label.lower() for label in issue.labels}
                or any(references_issue(text, issue.number) for text in prior_text)
            ):
                continue
            freshness = max(0.0, 1 - (now - repository.pushed_at).days / active_within_days)
            popularity = min(repository.stars / 1_000, 10)
            score = round(popularity + freshness - issue.comments / 100, 4)
            opportunities.append(Opportunity(repository=repository, issue=issue, score=score))
    return sorted(opportunities, key=lambda item: (-item.score, item.repository.full_name, item.issue.number))
