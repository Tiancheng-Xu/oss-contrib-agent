# Design

The implementation lives under `src/minisweagent/contrib` to preserve upstream compatibility. GitHub access is a small injected command runner around `gh`, while ranking and gate logic stay pure and testable. A Pydantic `TCFlowRunResult` normalizes the local multi-gate evidence. Draft PR creation is unavailable unless evidence matches the target repository and issue, all statuses pass, at least one test succeeded, no blocker exists, and no existing user PR references that issue.

