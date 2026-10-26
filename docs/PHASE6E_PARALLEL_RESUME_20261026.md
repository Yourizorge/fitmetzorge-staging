# Parallel integration resumed, 26 October 2026

Status: LOCAL/CI ADMISSION IN PROGRESS; HOSTED NO-GO.
This checkpoint does not replace any historical result or owner acceptance.

## Scope and source

The owner asked to resume with multiple agents. Local and remote staging main
were both `6a1fb803dd73348728db24102560c82e30f6284e` at the resumed preflight.
The repository is the existing `phase4fb-staging-deploy` checkout. Older dirty
files and historical receipts remain in place; no reset or cleanup was used.

The sole reserved hosted run remains
`6f8c8909-9b79-4011-a9d1-db5e23c6b6c1`, authorized by
`PHASE6E11_PARALLEL_RUN_AUTHORIZATION_20261018.md`. Its maximum is 2349 SQL
commands, with the existing time, stream, row, IO and safety limits. No hosted
attempt has been started during this resumed work. The last proven hosted
history is 44; candidate45 is not claimed applied. An eight-day-old observation
is not presented as a fresh hosted measurement.

## Integrated work and separate responsibilities

Official documentation was rechecked on resume: the [changelog](https://supabase.com/changelog.md)
adds the knowledge-base beta since the previous checkpoint; no new connection
repair is inferred from that announcement. The [CBC notice](https://supabase.com/changelog/cbc-tls-ciphers-deprecated)
concerns project HTTP APIs from10 November at the earliest, not PostgreSQL,
pooler or Management API connections. TLS verification is not weakened.
[Temporary access](https://supabase.com/docs/guides/platform/temporary-access)
still requires SSL enforcement and does not authorize Auth HTTP calls.
[Logout](https://supabase.com/docs/reference/javascript/auth-signout) is not
immediate cryptographic invalidation of existing access JWTs; server session
checks remain mandatory. The [PG17.11 notice](https://supabase.com/changelog/postgres-15-19-17-11-breaking-changes)
does not authorize an upgrade, reindex or alteration of protected data here.

- Main: manual integration, source inventory, tests and eventual CI dispatch.
- Agent A/B: combined command register, prefix reserves and failure accounting.
- Agent D: Auth safety suffix and worker completion/failure paths.
- Agent E: private application12-21 tests, CI profile and release boundaries.
- Agent F: independent source, security, preservation and admission review.

The previously reviewed A/B final-before/after checks and E canonical45+2 app
profile are retained. The reviewed D Auth safety patch is integrated without
its obsolete final-cleanup call site or its older IO implementation. The main
read-WAL checks and A/B final metadata ordering remain authoritative.

The Auth reserve is held before token issuance and released only after validated
independent session-zero metadata. Exact guard/observer removal is prepaid and
not replayed after an uncertain response. Stopped-run revocation has a separately
metered suffix; unknown minting and partial normal logout remain explicit NO-GO
paths, not claims of confirmed revocation. Historical records are not promoted.

## Verification boundary

Independent review found an additional P2: control restoration released its
safety reserve before the returned read was validated. This is corrected with
an explicit post-validation confirmation and a separate trace marker. A lost,
mismatched or wrong-phase response retains the reserve. Five new regression
tests cover those paths and unconfirmed prefixes. The resulting full local
Python suite passes315 tests; the unchanged Node sources pass138 tests.
Command costs and the approved limit are unchanged.

After the focused scheduling-regression correction, the complete local suite
passed310 Python tests and138 Node tests. The new in-memory counterfactual uses
the current three CLI slots and final pre/post ordering:2338 normal,2349 worst,
2339 prefixes. Late Auth reserve release still fails at2367. It does not claim
that historical CI executed the new metadata query, nor replace fresh real CI.

The resumed preservation check passed1376 retained entries:1372 byte-identical,
four explicitly authorized existing documentation/attributes differences, zero
unexpected differences. Baseline SHA256 remains
`213673e2a04f04b715f247efe3f27263c0dc998859d5d7e54685a356412f8fef`.

The first merged local check passed 138 Node tests. Python discovery ran309
tests with one error in the counterfactual historical-budget replay: its old
final-phase allocation did not match the new pre/post sequence. That initial
failure is preserved here; the focused correction above did not edit historical
receipts. Neither local suite result is a fresh PostgreSQL/Auth CI result.

A local-only source bundle passed the existing source scanner:274 files,
SHA256 `f96d1de32b5884ef0bb5474d3e8b94fc16416c8954198cea1d4f182e6f932971`.
That intermediate bundle is retained, not dispatched or reused as final source
admission. A new exact-commit bundle and fresh complete PG17/GoTrue CI are
mandatory before any hosted run.

The application integration stays private and synthetic. Package21 remains
unaccepted and default-off. No application runtime, frozen contract, migration
1-44, real account or hosted fixture is modified by this local merge.

## Final local corrections before fresh CI

The worker no longer treats a `complete` message as completion before the child
exits successfully. Nonzero exit, timeout, missing checks and unconfirmed removal
retain the incomplete/abort path. Five new mocked-process regressions cover this;
they do not substitute for the real CI child process.

The private application now expires current comparison facts after a newly
approved plan is applied, including cadence-only changes. Historical comparisons
remain immutable, both routes retain their approval order, and a new comparison
must bind to the new plan version. Persistence and browser scenarios are added
to fresh CI, not claimed executed locally without PostgreSQL/Auth.

The existing GitHub source fetch truncated the 11.16 MB app envelope at 8 MB.
It now accepts a bounded 16 MiB envelope and at most 12 MiB decoded payload,
checks declared length, encoding and SHA256, and rejects truncation or overflow.
This changes only private CI transport, not hosted SQL/time/row budgets. Its
exact LF-normalized harness hash is pinned. Five parser regressions pass.

After integration: endchain Python325 PASS; private app Python138 PASS and
Node147 PASS, all without skips. The prior endchain Node138 PASS remains valid
because these later changes do not alter its Node source. These are local tests,
not new clean database, real Auth, browser or hosted results. Fresh source-bound
CI remains mandatory. The reserved hosted attempt is still unused.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
Owner phone test: NO-GO until the complete hosted chain passes.
