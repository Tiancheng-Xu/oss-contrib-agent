# OSS contribution workflow

`oss-contrib` adds a personal, evidence-gated contribution workflow without changing the upstream `mini` agent.

## Discover candidates

```bash
oss-contrib discover --language Python --language TypeScript --min-stars 500
```

Discovery is read-only. It keeps recently active, licensed, non-fork repositories with unassigned `good first issue` issues, then removes issues already referenced by one of the authenticated user's PRs.

## Validate TC Flow evidence

The Draft PR gate accepts a local JSON result with this shape:

```json
{
  "version": "tc-flow-run-result-v1",
  "run_id": "run-20260811-001",
  "feature": "fix-config-validation",
  "contract_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "target_repository": "owner/repository",
  "target_issue": 42,
  "task_review": "pass",
  "feature_qa": "pass",
  "stop_hook": "ALLOW",
  "repository_policy": "local-pass",
  "tests": [{"command": "pytest", "status": "pass", "summary": "12 passed"}],
  "blockers": []
}
```

Validate it without writing to GitHub:

```bash
oss-contrib validate .tc-flow/run-result.json --repo owner/repository --issue 42
```

## Plan or publish a Draft PR

The default is a dry run. It prints the exact `gh pr create --draft` operation:

```bash
oss-contrib draft-pr .tc-flow/run-result.json \
  --repo owner/repository --issue 42 --base main \
  --head Tiancheng-Xu:fix-42 --title "fix: validate malformed config" \
  --body-file .tc-flow/pr-body.md
```

Add `--publish` only after the local gate output has been archived. The command uses the existing `gh` login, never reads or stores a PAT, never creates a non-draft PR, and never merges.
