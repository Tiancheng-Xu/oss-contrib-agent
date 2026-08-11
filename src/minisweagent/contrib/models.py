from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RepositoryCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    full_name: str
    html_url: str
    description: str = ""
    stars: int
    pushed_at: datetime
    license_spdx: str
    language: str | None = None


class IssueCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    repository: str
    number: int
    title: str
    html_url: str
    body: str = ""
    comments: int
    created_at: datetime
    labels: list[str]
    assignees: int


class Opportunity(BaseModel):
    model_config = ConfigDict(frozen=True)

    repository: RepositoryCandidate
    issue: IssueCandidate
    score: float
