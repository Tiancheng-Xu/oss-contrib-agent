# OSS Contribution Agent Personalization Plan

## Task 1: Freeze the contribution contract

Create TC Flow requirements, design, tasks, state, and immutable contract files. Confirm the worktree, remote, owner identity, and allowed GitHub operation.

## Task 2: Build read-only GitHub discovery

Write failing tests for active repository filtering, good-first-issue parsing, deterministic ranking, and prior-PR deduplication. Add the smallest GitHub CLI adapter and discovery service that passes them.

## Task 3: Build the evidence gate

Write failing tests for rejected blockers, mismatched targets, missing test evidence, and successful TC Flow results. Implement a strict Pydantic evidence model and validator.

## Task 4: Build Draft PR publication

Write failing tests proving dry-run is the default, duplicate work is rejected, and live publication always uses `--draft`. Implement the publisher and Typer commands.

## Task 5: Integrate and document

Add the `oss-contrib` entry point, focused usage documentation, and repository-policy caller required by TC Flow.

## Task 6: Verify and deliver

Run focused tests, full regression tests, Ruff, CLI smoke tests, secret scanning, repository policy audit, and TC Flow Feature QA. Commit, push the isolated branch, and open a Draft PR in the personal fork.

