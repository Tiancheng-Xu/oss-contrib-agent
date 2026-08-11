# ISSUE-003: GitHub App commit identity differs from repository policy owner name

- Status: mitigated
- Severity: P1 delivery gate
- Detected: 2026-08-11
- Scope: GitHub App fallback delivery path

## Evidence

The GitHub App-created commits on the first delivery branch were correctly associated
with the authenticated `Tiancheng-Xu` account, but their raw Git author and committer
display name was `徐天成`. The shared repository policy requires the raw display name
to equal `tiancheng-Xu`, so the `Repository policy` workflow rejected both commits with
`author-owner-mismatch` and `committer-owner-mismatch`.

## Root cause

GitHub account association and raw Git identity are separate fields. The GitHub App
fallback preserved the account association but generated commits from the profile
display name, while the policy intentionally validates a fixed raw Git identity.

## Mitigation

Do not force-update the first branch. Push the locally verified commit history to a new
branch over normal Git HTTPS so the configured owner identity is preserved, open a new
Draft PR, and close the superseded Draft PR. Retain the App path for emergency delivery
only when its raw identity is compatible with the target repository policy.

## Follow-up

Consider extending the shared policy with an explicit, audited owner-alias mechanism.
Do not weaken the current identity gate or infer ownership only from a display name.
