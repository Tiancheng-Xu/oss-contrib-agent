# Local container suite requires a healthy runtime

Severity: P2 environment
Status: open, not a product blocker

The upstream slow regression suite detects a local Docker executable but container startup exits with status 125. The core non-slow suite is verified separately. CI installs and configures its own container runtime, so the Draft PR should rely on CI for Docker, Singularity, and SWE-bench environment coverage.
