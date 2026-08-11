from typer.testing import CliRunner

from minisweagent.contrib.cli import app, build_repository_queries


def test_build_repository_queries_scopes_activity_and_language() -> None:
    queries = build_repository_queries(
        min_stars=500,
        pushed_after="2026-07-12",
        languages=["Python", "TypeScript"],
    )

    assert queries == [
        "stars:>=500 archived:false fork:false pushed:>=2026-07-12 language:Python",
        "stars:>=500 archived:false fork:false pushed:>=2026-07-12 language:TypeScript",
    ]


def test_cli_help_lists_guarded_workflow() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "discover" in result.stdout
    assert "validate" in result.stdout
    assert "draft-pr" in result.stdout
