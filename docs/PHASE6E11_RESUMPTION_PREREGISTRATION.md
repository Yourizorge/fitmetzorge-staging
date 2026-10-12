# 6E-11 Controlled Resumption
2026-10-12. Owner lifts the support-answer dependency only. SU-487979 remains open.
6E-21 remains READY FOR OWNER REVIEW, not accepted. Exact staging repository/main
and project mokxyyullfhkfalopbzd only. No member processing, provider calls or costs.

## Before Any Probe
Local and fresh remote HEAD: 36ba0d43c46ffc93637cc22282f9adb63ce7f4d7.
All 1340 existing tracked/untracked source files have a new local byte baseline.
Prior evidence, dirty files, frozen contracts and migrations 41/42 are immutable.
Management metadata reports ACTIVE_HEALTHY, PG17.6.1.155, 42 migration identities.
This is not a native/Edge connection, data-preservation or workflow PASS.

## Three-Probe Ceiling
One collector, sequential, no automatic transport retry, no guessed endpoint.
1. Native libpq, existing owner PAT/JIT and saved official Connect session endpoint:
   test whether the previously working native route still authenticates. Five-second
   connect deadline, explicit read-only transaction before metadata, confirmed
   rollback and immediate JIT revocation. Maximum 12 SQL commands; no row stream.
2. Only after reviewing 1: one read-only Edge invocation with exact-run signed
   GitHub OIDC and a ten-minute absolute expiry. Existing server-local secret only.
   Test a specific driver/startup hypothesis, five-second connection deadline,
   two-second command deadline and at most eight metadata/control commands.
3. Reserved for a distinct, locally verified hypothesis derived from 1/2. Record
   it before execution; not an identical retry. The total ceiling remains three.

Separate TLS-only success never advances the phase of another attempt. A driver
deadline without internal stage observations remains driver_open_unresolved.
Connection and SQL deadlines are distinct. No raw error strings, credentials,
connection URLs or personal content are retained. All query results are metadata.
No Auth/fixture/migration mutation in these diagnostic probes. Management JIT and
temporary function lifecycle are recorded separately, not called zero total writes.

## Admission After Diagnosis
Connection PASS does not authorize bypassing existing proof gates. Actual hosted
Auth/request/intent/audit/write-set/apply/restore/delete evidence remains required.
Missing pair blocks dependent mutations and cleanup. No full fingerprint per action.
Use the current M42 and 45-case support-wait contracts, not superseded global scans.
Any currently unavailable Auth route stays denied and outside the owner window.

## Current Official Documentation
Checked changelog, database connections, temporary access, SSL enforcement and
Edge Postgres guidance on 2026-10-12. Session pooler is required here for IPv4 and
retained session/cursor semantics; transaction pooling is not a fallback. Shared
JIT requires explicit jit=true. TLS/CA/hostname validation remain mandatory.
The changelog notes PG security patches, migration of logs.all to ClickHouse logs,
and upcoming Data API exposure defaults. No upgrade, logging change or grant is
made by this diagnosis; none establishes a cause for the old timeout.

References: https://supabase.com/changelog ;
https://supabase.com/docs/guides/database/connecting-to-postgres ;
https://supabase.com/docs/guides/platform/temporary-access ;
https://supabase.com/docs/guides/platform/ssl-enforcement ;
https://supabase.com/docs/guides/functions/connect-to-postgres .
## Preregistered Probe 3
Probes 1/2 have finished. Native authenticated with the exact expected instance;
the additional statement-hash query failed because text was cast to bytea rather
than encoded as UTF8. The old result was not drained before ROLLBACK. Both defects
are reproduced and corrected in a new local PG17 test (9/9 local cases PASS).
Edge probe 2 proves TCP and TLS within that attempt, then times out while waiting
for confirmed authentication, with zero SQL. Its function has been removed.
Probe 3 repeats only native metadata with convert_to(...,'UTF8') and proven result
draining. Same five-second connect/two-second query limits, at most 12 commands.
No fourth transport probe or CLI reconnect is permitted by this preregistration.
