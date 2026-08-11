# Requirements

## Acceptance criteria

- [ ] Discover active, popular, non-fork GitHub repositories with an approved SPDX license.
- [ ] Discover open, unassigned `good first issue` issues and emit deterministic JSON.
- [ ] Exclude issues already referenced by a PR from the authenticated user.
- [ ] Validate a strict TC Flow result before any GitHub write.
- [ ] Default Draft PR publication to dry-run and require an explicit publish flag.
- [ ] Use the existing `gh` login without reading or storing credentials.
- [ ] Never auto-merge, schedule itself, or create non-draft PRs.

