# 6E-11 Controlled Resumption Report
2026-10-12. **TECHNICAL NO-GO for hosted workflow and owner phone test.**
Native connection restored/proven; corrected Edge diagnostic proven locally only.
SU-487979 remains open, but a support answer is no longer an admission prerequisite.
No6E-11 acceptance/freeze;6E-21 remains READY FOR OWNER REVIEW.

## Baseline And Permission

Repository Yourizorge/fitmetzorge-staging/main, starting local/direct remote HEAD
36ba0d43c46ffc93637cc22282f9adb63ce7f4d7, project mokxyyullfhkfalopbzd only.
AGENTS and project config read; on-request/auto_review/workspace-write, managed
restrictions respected. Existing six tracked dirty files and older untracked
6E-11 work preserved, not staged or overwritten. New snapshot protects1340 files
and58 previously indexed historical evidence files.

The new owner instruction permits bounded diagnosis and later synthetic integration,
but explicitly caps transport probes at THREE. All three slots have been used.
No fourth connection, migration CLI reconnect, Auth action or workflow mutation
was performed. A Support response is NOT the reason for stopping.

## Three Probes

| Probe | Result | Exact boundary |
| --- | --- | --- |
| 1 native | Connected/authenticated in2531ms, TLS/CA/hostname and exact database instance bound; NO-GO for additional metadata step | Query SQLSTATE22P02: text-to-bytea cast in statement hashing. Old adapter did not drain failed result before rollback; explicit rollback unconfirmed, connection closed. Original failure kept |
| 2 Edge | One socket; TCP and TLS handshake validated within THIS attempt; driver reserve reached5000ms DEADLINE;0 SQL | Waiting for driver startup reservation; not a query timeout. Original result correctly reports no driver-confirmed authenticated session |
| 3 corrected native | PASS;1422ms; explicit READ ONLY, identity,42 migration identities, synthetic counts and confirmed ROLLBACK |6 commands; UTF8 convert_to hashing and drain-before-rollback independently tested on local PG17 |

Probe1 used5 command attempts, probe3 used6, Edge used0:11 total SQL/control
command attempts,0 rowhash/fingerprint cycles. No automatic connection retry.
No whole-table member-data scans, member/chat/health content, provider or Auth
workflow calls. Management JIT grants/revokes and the temporary Edge deployment/
deletion are separate control-plane changes, not falsely described as zero writes.

## Root Cause And Limits Of Attribution

A local TLS/PG17 reproduction with the EXACT pinned Deno-native Postgres.js3.4.7
configuration (fetch_types:false, first operation reserve()) receives server
parameter messages but its reservation promise never resolves. The driver's
ReadyForQuery initial-reservation branch returns without resolving/opening it.
The identical client configuration with the first explicit
BEGIN TRANSACTION READ ONLY completes the guard and ROLLBACK.

The new shared read_only.mjs helper implements that locally proven sequence:
BEGIN before substantive queries, exact read-only guard, same backend/instance,
bounded commands, rollback attempted on every error, no COMMIT, no reserve,
no weaker TLS. An offline-only corrected Edge candidate uses this helper.
It has NOT been deployed or hosted-verified. Existing workflow transport uses
begin(), not reserve(), and is preserved byte-for-byte.

Narrow read-only Supavisor metadata for07:45:15-07:46:00UTC finds authentication-
success records under the EXACT application label of probe2, beginning
07:45:39.202070UTC. The logged client-facing authentication success contradicts
an inference that a five-second driver timeout alone means a wrong secret.
It does not prove backend allocation or the driver consuming ReadyForQuery.
Three hashed internal process IDs are NOT three observed client sockets.
[Sanitized log metadata](PHASE6E11_RESUMPTION_LOG_METADATA.json) contains no raw
messages, IPs, credential values or personal contents.

Thus the local startup-reservation defect is proven and the current Edge symptom
is strongly consistent with it. Complete hosted causal confirmation awaits ONE
corrected Edge probe. It is not honest to retroactively attribute every
September28 failure or the old Disk-IO warning to this defect.

Two separate native diagnostic defects were also repaired in NEW local files:
UTF8 hashing avoids bytea escape interpretation, and failed libpq results are
drained before ROLLBACK. Probe1 remains a failure, not rewritten as a pass.
Local harness setup issues (module collision, asynchronous SSL reload and denied
empty-environment read) were fixed without a hosted retry.

## Current Hosted Facts And Access Closure

Native project binding: expected database/role, exact instance fingerprint and
PG17.6; management image17.6.1.155; ACTIVE_HEALTHY. Official saved Connect
session-pooler endpoint, IPv4, port5432; official CA and verify-full with hostname.
Native uses existing owner PAT from Windows credential storage in memory, JIT
jit=true with short mappings. Edge uses its existing injected server-local
configuration; no secret exported, reset or rotated.

Migrations:42/42 identities match local order/names. M41 and M42 already existed:
- M41 local SHA256:4d474becdc5c3a7343562602115f9333b5cffc6bed0c323fca3abc560843af7d.
- M42 local SHA256:5eebec968d2dae27d4e1462dbcc9de8d9e5599552ff145ad099e57fffd5f5f7c.

Current stored-statement hashes are retained in probe3 metadata. They use a
newline-joined statements representation, not a falsely equivalent raw-file hash.
No new migration, replay or history repair. A NEW CLI dry-run/advisor/RLS inspection
was NOT run after the three-probe limit; historical results remain historical.

6E-11 metadata:9 historical windows,3 synthetic identities,0 active windows,
0 workspaces,0 request receipts; request/workflow audit controls false.
This is a counts-only read, not proof of all Auth session cleanup or a new
global protected-data fingerprint comparison.

Temporary fmz-phase6e11-proof was removed at07:46:10UTC (management404);
its exact-run CI admission was limited to10 minutes. Final management check:
SSL-enforcement on, JIT disabled,0 active mappings. Existing fmz-phase6e11 v2
and other application Edge functions unchanged. No owner-test window opened.
CI diagnostic run:38219340571; it records the expected unsuccessful Edge result.

## Local Proof And Preservation

-150 targeted tests PASS:141 Node (OIDC/config/TLS/request/transport/new helper/
  integration checklist) and9 Python (native contract/PG17 hash/rollback).
-4947 existing offline frozen regressions PASS, no test failures.
-45 existing Route A/B transaction pairs PASS locally: expected versus observed
  writes, negative routes, conflicts, separate apply/restore and b_reopen.
-12 local cleanup/delete pairs PASS;24 deletes remain in audit; local protected
  fixtures unchanged. No hosted fixtures were cleaned up.
-Local TLS reproduction: old reserve DEADLINE/0SQL; corrected shared helper
  READ ONLY PASS/3commands/ROLLBACK. Deno cached typecheck PASS.
-1340 pre-existing files and58 indexed historical evidence files unchanged.
  Historical112 valid pairs and incomplete113 remain historical, not recounted
  as newly hosted evidence.

The local Auth stubs, request claims and synthetic relationships are not real
Supabase Auth evidence. Six hosted routes (generate_link, verify, refresh, logout,
control-account creation/deletion) were NOT executed in this diagnosis.
No partial hosted workflow PASS, no newly proven durable live apply/restore.

Read-only transaction boundaries prove these executed diagnostic SQL commands
could not write app/member data. No new full protection snapshot was taken, so
concurrent unrelated database activity is not certified absent.
No old heavy fingerprint, stats-text scan or temp-write measurement was rerun.
Observed connection latency and ACTIVE_HEALTHY are NOT a Disk-IO-budget metric;
no claim of measured zero own temp blocks or complete IO recovery is made.

## What Is Ready Next

[Integration register](PHASE6E_SERVER_INTEGRATION_REGISTER.md) accounts for accepted
0-20, with11 explicitly unaccepted and21 excluded. It separates presentation from
private durable storage, RLS, Edge validation, outbox, dependencies and rollback.
The first later slice is accepted12 registration revisions, not bulk publication
of memory demos or expansion into unaccepted21.

Smallest remaining technical step: one freshly bound, short-lived, read-only
Edge invocation using edge_probe_corrected.ts and read_only.mjs, no reserve,
five-second connect/first-command deadline, explicit READ ONLY, exact instance/
backend guard, ROLLBACK and diagnostic removal. This needs an additional probe
allowance because this task's three attempts are exhausted, not a secret or reset.
Only after PASS proceed through existing actual Auth/request/audit pairs,
scoped protection, Route A/B, apply/restore/deny/conflict, delete/cleanup, final
migration/dry-run/advisors and synthetic owner-window gates.

Only self-contained offline helper/tests, integration checklist and sanitized
documentation are committed. Operator harnesses/corrected Edge candidate remain
local with recorded hashes because their older private dependencies remain
unpublished. No unproven runtime, old dirty file or application Edge is published.
Pages verification and final commit are recorded separately after publication.

External AI calls/cost:0 / EUR0.00.
Real-member AI enabled:NO.
Production touched:NO.

References checked on2026-10-12:
[Changelog](https://supabase.com/changelog),
[connections](https://supabase.com/docs/guides/database/connecting-to-postgres),
[temporary access](https://supabase.com/docs/guides/platform/temporary-access),
[SSL enforcement](https://supabase.com/docs/guides/platform/ssl-enforcement),
[Edge Postgres](https://supabase.com/docs/guides/functions/connect-to-postgres),
[log filtering](https://supabase.com/docs/guides/observability/advanced-log-filtering).
