import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import typer

from minisweagent.contrib.discovery import rank_opportunities
from minisweagent.contrib.evidence import GateError, load_run_result
from minisweagent.contrib.github import GitHubClient, GitHubCommandError
from minisweagent.contrib.models import RepositoryCandidate
from minisweagent.contrib.publisher import DraftPRPublisher

app = typer.Typer(
    name="oss-contrib",
    help="Discover and publish meaningful open-source contributions behind TC Flow gates.",
    no_args_is_help=True,
    add_completion=False,
)


def build_repository_queries(*, min_stars: int, pushed_after: str, languages: list[str]) -> list[str]:
    base = f"stars:>={min_stars} archived:false fork:false pushed:>={pushed_after}"
    return [f"{base} language:{language}" for language in languages] if languages else [base]


def _json_output(value: object) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2))


def _abort(error: Exception) -> None:
    typer.echo(f"Blocked: {error}", err=True)
    raise typer.Exit(2)


@app.command()
def discover(
    min_stars: int = typer.Option(100, min=1, help="Minimum repository stars."),
    active_days: int = typer.Option(30, min=1, max=365, help="Require a push within this many days."),
    max_repositories: int = typer.Option(10, min=1, max=50),
    issues_per_repository: int = typer.Option(10, min=1, max=50),
    max_comments: int = typer.Option(10, min=0),
    language: list[str] | None = typer.Option(None, "--language", "-l"),
) -> None:
    """Search active repositories and unassigned good-first issues without writing to GitHub."""
    now = datetime.now(UTC)
    queries = build_repository_queries(
        min_stars=min_stars,
        pushed_after=(now - timedelta(days=active_days)).date().isoformat(),
        languages=language or [],
    )
    github = GitHubClient()
    try:
        repositories_by_name: dict[str, RepositoryCandidate] = {}
        for query in queries:
            for repository in github.search_repositories(query, limit=max_repositories):
                repositories_by_name[repository.full_name] = repository
        repositories = list(repositories_by_name.values())
        author = github.viewer_login()
        issues = {
            repository.full_name: github.search_good_first_issues(
                repository.full_name,
                limit=issues_per_repository,
            )
            for repository in repositories
        }
        prior_prs = {
            repository.full_name: github.prior_pull_request_text(repository.full_name, author)
            for repository in repositories
        }
        opportunities = rank_opportunities(
            repositories,
            issues,
            prior_pull_request_text=prior_prs,
            now=now,
            min_stars=min_stars,
            active_within_days=active_days,
            max_comments=max_comments,
        )
    except (GitHubCommandError, KeyError, ValueError) as error:
        _abort(error)
    _json_output([opportunity.model_dump(mode="json") for opportunity in opportunities])


@app.command()
def validate(
    evidence_file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    repository: str = typer.Option(..., "--repo"),
    issue_number: int = typer.Option(..., "--issue", min=1),
) -> None:
    """Validate TC Flow evidence for one exact repository issue."""
    try:
        evidence = load_run_result(evidence_file)
        evidence.assert_publishable(repository, issue_number)
    except GateError as error:
        _abort(error)
    _json_output({"status": "pass", "run_id": evidence.run_id, "contract_hash": evidence.contract_hash})


@app.command("draft-pr")
def draft_pr(
    evidence_file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    body_file: Path = typer.Option(..., "--body-file", exists=True, dir_okay=False, readable=True),
    repository: str = typer.Option(..., "--repo"),
    issue_number: int = typer.Option(..., "--issue", min=1),
    base: str = typer.Option("main", "--base"),
    head: str = typer.Option(..., "--head"),
    title: str = typer.Option(..., "--title"),
    publish: bool = typer.Option(False, "--publish", help="Create the Draft PR after all gates pass."),
) -> None:
    """Plan a Draft PR, or publish it when --publish is explicitly supplied."""
    try:
        evidence = load_run_result(evidence_file)
        result = DraftPRPublisher(GitHubClient()).publish(
            repository=repository,
            issue_number=issue_number,
            base=base,
            head=head,
            title=title,
            body_file=body_file,
            evidence=evidence,
            publish=publish,
        )
    except (GateError, GitHubCommandError) as error:
        _abort(error)
    _json_output(result.model_dump(mode="json"))


if __name__ == "__main__":
    app()
