# PG17 And Write-Action Readiness

Offline artifacts only. No function in this directory connects to Supabase or
executes a route. The 6E-11 hosted runner remains paused.

- register.json: 52 reviewed action/outcome categories and exact local source hashes.
- registry.py: generation and fail-closed source/route-contract verification.
- proof_gate.py: synthetic-only evidence ordering and bounded admission checks.
- analyse.py: derives a decision from already retained sanitized metadata.
- test_coverage.py: injected route/evidence/budget failures.
- test_pg17.py: exact PG17.6-only additional canonicalization cases.

Set FMZ_LOCAL_PG_BIN to the isolated official PostgreSQL 17.6 bin directory.
Run the existing fingerprint_v1/test_offline.py (36 cases), then its benchmark.py.
Run unittest discover -s _offline/phase6e11/readiness_v1 -p test_*.py -v separately.

The register binds the retained working tree, including existing uncommitted
migration/Edge/runner sources. These sources are deliberately NOT pushed as part
of this offline follow-up. A fresh checkout without them fails closed instead of
pretending to verify the live runner. Unit tests for evidence transitions remain
fully synthetic; boolean validation inputs are not live data-preservation proof.

A source-bound route list is not a complete proof of Auth-service writes, recursive
triggers/cascades or independent writers. Missing live closure remains explicit.
Do not regenerate register.json automatically after source changes to bypass review.
No new code here is wired into the application or the hosted runner.
