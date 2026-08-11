# OSS Contribution Agent Personalization Design

## Goal

Turn this fork into a safe contribution assistant for `Tiancheng-Xu`. It should discover active repositories and well-scoped issues, reject duplicate or weak opportunities, require TC Flow evidence, and publish Draft PRs through the existing GitHub CLI login.

## Non-goals

- No green-square farming, synthetic activity, auto-merge, or unsolicited bulk PRs.
- No stored personal access token, model key, or repository scheduler.
- No production changes, paid services, or broad repository write permissions.
- No upstream PR for this fork-specific orchestration layer.

## Architecture

Add an isolated `minisweagent.contrib` package and an `oss-contrib` CLI:

1. `GitHubClient` uses `gh api` and the current authenticated account. It searches recently active, non-archived, non-fork repositories and their open, unassigned `good first issue` issues.
2. Discovery applies deterministic license, activity, popularity, scope, and duplicate filters. Results are ranked and emitted as JSON so an external scheduler can archive decisions.
3. `TCFlowRunResult` is a narrow evidence contract. Draft publication requires passing task review, Feature QA, Stop Hook, repository policy, at least one successful test, no blocker, and an exact repository/issue match.
4. `DraftPRPublisher` checks the authenticated user's existing PRs for the target issue before invoking `gh pr create --draft`.
5. Publishing is explicit (`--publish`). Without it the command returns the exact planned GitHub operation and performs no write.

## Safety boundaries

- All subprocess calls use argument arrays with no shell interpolation.
- GitHub output is parsed as JSON; errors are summarized without credentials.
- The CLI never reads `.env`, credential files, cookies, or token environment variables.
- Discovery is read-only. The only write operation is Draft PR creation after all evidence gates pass.
- Scheduling remains in the existing Codex automation, keeping credentials and policy outside this repository.

## Verification

- Unit tests cover repository filtering, ranking, duplicate detection, TC Flow evidence rejection, dry-run behavior, and Draft PR command construction.
- Ruff validates the added package and tests.
- CLI help and a read-only discovery smoke test validate packaging and GitHub integration.

