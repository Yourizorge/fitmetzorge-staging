# Clean Database Gate 41

Current result: clean CI PASS (run 36034533557); hosted application remains NO-GO
because the required secure native database credential is unavailable. Canonical
sources were committed only after CI PASS. See
../../../docs/PHASE6E11_MIGRATION41_CI_REPORT.md and its separate JSON receipt.

Phase 1 infrastructure only. No canonical migration is committed by this bootstrap.
The manual main-only workflow takes an immutable Git blob and independent SHA256.
The blob contains only allowlisted SQL/test source bytes, not staging data or credentials.
It is not a ref, release, Pages file or canonical migration commit.

Standard public Ubuntu runner; no larger runner, cache, artifact upload or paid service.
Evidence is sanitized, hashed and printed in bounded job-log chunks, then downloaded
to the existing local historical evidence area. The runner is discarded by GitHub.
No Supabase access token, linked project, database password or real member input is used.

CLI 2.117.0 is downloaded from the official release and SHA256-verified.
The CLI selects the real Supabase PG17 image; its tag, image ID, digest, server version
and installed/available extensions are recorded. No extension mocks or migration skips.
A clean platform database must have no public application tables or application history.
The canonical files are introduced one by one in original order and applied by the CLI.
A failure immediately prevents the remaining migrations/security stage and all hosted work.

Tests after successful rebuild: exact history order, real extensions, existing SQL
transactional regressions, migration identity tests, unchanged audit tests via local
Docker psql, bridge ACL/RLS/invoker/search-path/default-off checks, official pinned
Splinter security/performance advisors, CLI lint and local db-push dry-run.
An advisor error or bridge warning is not silently waived.
This proves a disposable schema environment, not live Auth/JWT or a hosted workflow.
The unchanged historical 6A fixture lacks the separate private-chat consent and age
context required by the accepted 6D service-completion gate. The separate hash-bound
CI adapter proves that denial first, then adds only those synthetic prerequisites.
Every original test assertion remains; original/executed/adapter hashes are recorded.
The first failing CI run remains historical evidence, not a retroactive pass.
The existing real-Auth/server-transport and bounded hosted proof gates still apply.

The workflow has no push trigger or automatic retry. A failed rebuild is NO-GO.
No owner acceptance, 6E-12 or cleanup of historical local/hosted evidence.
