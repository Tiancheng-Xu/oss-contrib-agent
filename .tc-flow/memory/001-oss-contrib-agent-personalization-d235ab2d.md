# OSS contribution agent personalization

## Decisions

- Keep upstream `mini-swe-agent` intact and place personal orchestration under `minisweagent.contrib`.
- Use the current GitHub CLI keyring login; never read or store a PAT.
- Keep scheduling outside the repository and require explicit `--publish` for the sole write operation.
- Require exact TC Flow repository/issue evidence, passing gates and tests, no blockers, no prior user PR for the issue, and a safe issue-referencing PR body.

## Operational notes

- GitHub Search can return secondary rate limits even below the documented primary quota. Stop immediately and let the next scheduled run try later; do not retry in the same run.
- The local full suite requires a healthy container runtime. Use the non-slow core suite locally and preserve container coverage for the existing CI workflow.
- The central repository policy caller is byte-for-byte canonical and must remain unchanged.
