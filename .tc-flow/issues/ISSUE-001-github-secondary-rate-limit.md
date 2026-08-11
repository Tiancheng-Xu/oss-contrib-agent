# GitHub secondary rate limit

Severity: P2 operational
Status: mitigated, monitor

The authenticated Search API returned HTTP 403 with a secondary-rate-limit message during the real discovery smoke test. The tool now classifies this response, stops the run immediately, exposes no raw diagnostic identifier, and performs no retry. A later feature may batch discovery requests if repeated daily evidence shows this is structural rather than transient.
