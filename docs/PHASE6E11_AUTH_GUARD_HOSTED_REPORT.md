# 6E-11 Temporary Auth Guard: Hosted Evidence

Date: 12 October 2026. Scope: staging main and `mokxyyullfhkfalopbzd` only.
Baseline: `fea115915286d22eae81b1a7cc4637860599ed78`.

**GUARD LIFECYCLE: PASS. COMPLETE 6E-11 / OWNER PHONE TEST: NO-GO.**

This report supersedes only the earlier alias-guard blocker in
`PHASE6E11_M43_HOSTED_FOLLOWUP_REPORT.md`. Historical failed/incomplete attempts
remain unchanged. It is neither owner acceptance nor a freeze.

## Proven Hosted

Run `0dd37225-718b-42bc-9621-5663539b4bee` used the admitted source composition
from [CI 38264824648](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38264824648).
All 362 retrieved evidence files passed their hashes, as did the GitHub archive
digest. Admission included clean 43/43 migrations, 12 SQL regressions, 22 audit
tests, 186 controller/guard Node tests, 34 real PostgreSQL guard checks and 8
artifact-validation tests. The nested 63 controller tests are a subset, not an
additional 63.

- Exact three registered UUID/address pairs; no prefix authorization.
- One native session-pooler connection, official CA/hostname verification,
  `verify-full`, owner JIT, project binding and 43 hosted migration identities.
- One private invoker function, one private schema and three Auth identity
  triggers. No PUBLIC/anon/authenticated/service-role execution grant.
- Immutable 180-second guard lease, below the ten-minute maximum. Installed at
  14:46:36 UTC; removal and JIT closure were confirmed before 14:46:52 UTC.
- 68/128 SQL commands: 54 normal and 14 independently reserved safety commands.
  No retries, parallel collector or full database fingerprint cycles.
- 556 pre-existing catalog objects/ACL/policies matched before and after.
  Exactly five own additions during the test and zero after removal.
- Four monitored metadata reads: zero own temp blocks, zero ambient temp-byte
  increase and zero observed concurrent long queries. Minimal safety reads
  were not included in that query-level IO claim.
- Zero Auth calls, application writes, row mutations, emails or fixture cleanup.
- Guard removed; JIT disabled with zero mappings; SSL enforcement unchanged.

Evidence is retained under
`supabase/.temp/phase6e11-guard-hosted-0dd37225718b42bc96215663539b4bee`.
Its `contract.json` binds exact source hashes, CI receipt, run, deadlines and
query budget. `install-pair.json`, `removal-pair.json`, `closed.json` and the four
`read-*/io-proof.json` files bind the observations. This metadata-only canary
does NOT establish a new full row-fingerprint baseline or a workflow-data PASS.

## Corrected Before Auth Admission

Review of the assembled issuing helper found that verification and refresh also
issue tokens. They now attest the same live guard independently; an earlier
successful link-generation check cannot authorize later token issuance. Raw
credential-bearing request callbacks are private. Eleven added regressions
cover missing/expired/changed protection on all three issuing routes and the
ability to sign out without keeping issuance enabled. Local Node total: 197.

The native guard canary did not invoke the Auth helper; its successful receipt
therefore remains valid for guard lifecycle only. Changed Auth code requires
new CI evidence and cannot reuse that earlier admission.

A disposable real GoTrue CI extension tests the six Auth operations separately
for three synthetic identities. It uses loopback-only requests, random local
credentials, the official `supabase/gotrue:v2.196.0` image and no staging secret.
Image digest:
`sha256:c0c25187a6b835e65a6f6e6c6b39d090e832d40e6de5186f2c038e0411944232`.
CI-only technical observers preserve transaction IDs and row-key/actor hashes,
including DELETE. They are not part of the approved hosted identity guard.

The real service revealed an authentication-method record in
`auth.mfa_amr_claims` even for ordinary magiclink login. Its actor belongs to
the session, not a direct user_id column. The CI adapter now derives that actor
from the observed session row and preserves the link through cascading delete.
Official sources: [AMR model](https://github.com/supabase/auth/blob/v2.196.0/internal/models/amr.go)
and [local logout](https://github.com/supabase/auth/blob/v2.196.0/internal/api/logout.go).
This is not a new MFA feature, a live settings change or medical processing.

## Retained Failed Evidence

- CI 38259437642: disposable Auth-role peer/socket authentication failed;
  corrected to the existing local container's TCP credential route.
- CI 38262806969: successful test status but downloaded log-export hashes did
  not match. Not admitted. Original exports retained; no guessed repair.
- CI 38264128511: isolated artifact-test import failed. Corrected by separating
  pure artifact validation from runner imports.
- CI 38268358342: real-Auth setup failed; original private command diagnostics
  were insufficient to identify its precise subphase. Not retroactively passed.
- CI 38269235374: fixture installation failed. Trainer-first seeding and exact
  SQLSTATE/subphase recording corrected the test setup.
- CI 38270047369: issue succeeded, verify observation failed on missing AMR
  actor binding. The incomplete verify pair remains incomplete.

The current real-Auth CI result and publication receipt are recorded separately;
none of these earlier failures is relabelled PASS. The 112 historical pairs and
historical incomplete step 113 remain unchanged.

## Remaining Authority And Work

**Active offline:** guarded token helper and real-Auth CI admission; source-bound
measurement composition and precise write contracts.

**Blocked hosted:** Auth token/verify/refresh/logout proof, final controller
assembly, fresh fixture prepare/activate binding, Route A/B, apply/restore,
rejection/conflict/duplicate, scoped delete/cleanup and final protected-data
proof. The identity guard alone does not observe all these transactions.

The existing private audit deliberately has no managed-Auth row observers.
Auth request/audit logs do not provide the complete row-operation tombstones
required for all deletes. Scoped before/after differences alone must not be
advertised as complete transaction-bound negative-write evidence. A separate
owner decision was requested and explicitly approved on 12 October for temporary
metadata observers limited to these three synthetic identities and at most ten minutes.
The subsequent scoped observer installation/removal and failed write canaries
are documented in `PHASE6E11_AUTH_METADATA_FOLLOWUP_REPORT.md`; this earlier
guard-only receipt is not proof of hosted HTTP Auth.

Approved next scope: first prove the limited observation/removal composition locally
and in CI, then preregister a fresh bounded hosted Auth canary. No reuse of the
closed guard, expired lease or old admission. Every dependent workflow still
requires its own permitted writeset and complete pair. Until proven, those
routes remain excluded and the owner window stays closed.

No hosted fixture deletion, account modification, migration, Edge deployment or owner
window occurred in the guard-only run above. Migrations remain 43/43. Hosted dry-run was
not repeated for temporary DDL; the last hosted M43 dry-run was EMPTY. CI's
clean-build dry-run is a separate check, not a substitute for hosted proof.

No 6E-12 server integration or 6E-21 acceptance follows. JARVIS remained
untouched and no handoff occurred. Existing dirty worktree files are preserved.

External AI calls/cost: 0 / EUR 0.00

Real-member AI enabled: NO

Production touched: NO
