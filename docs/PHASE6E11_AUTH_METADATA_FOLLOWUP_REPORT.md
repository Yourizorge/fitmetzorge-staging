# 6E-11 Auth Metadata Follow-up

12 October 2026. Staging `mokxyyullfhkfalopbzd` only. Whole-package and owner
phone test remain **NO-GO**. No acceptance, freeze, or 6E-12 server integration.
6E-21 remains unaccepted. This report does not rewrite historical evidence.

## Implemented And Proven

- Separate private metadata observer, exact three registered UUID/address pairs,
  seven Auth tables, invoker function, fixed search_path and least private grants.
- Transaction/backend/action and SHA-256 actor/session/row bindings. No contents,
  credentials, token payloads, or ordinary account rows are exported.
- Session-to-actor ledger survives cascading deletes; exact operation multisets
  and request-session key linkage are checked rather than only end states.
- Real pinned GoTrue CI: six operations for each of three synthetic actors.
  Issue, verify, get-user, refresh, logout and revoked-session request: 18 cases.
  The extra 18 exact-write validations cover those SAME cases, not 18 new logins.
- CI 38276531839 was PASS with all 419 artifact hashes verified. It used clean
  43 migrations, 197 Node tests, 34 guard and 34 audit database checks, 12 SQL
  regressions, 22 audit tests, 8 artifact tests, 7 probe unit tests, 4 session-hash
  tests and 4 negative Auth-contract tests. The nested 63 tests are not additive.
- Three local read-only adapter regressions retain the old rejection, accept the
  required query marker, and prove the query payload itself did not change.

CI uses Supabase CLI 2.117.0, Postgres image 17.6.1.167 and GoTrue v2.196.0.
Image digests and exact source hashes are stored in each immutable CI artifact.
The disposable CI service has no staging secrets or real account data.

## Historical Hosted Attempts

| Run | Outcome | Commands | Meaning |
| --- | --- | ---: | --- |
| `19239cccf8c244fe9c8845ca1a92c722` | NO-GO, `unregistered_readonly_query` | 8 | Required query marker absent; no DDL or row write; rollback and JIT closure confirmed. |
| `15d85ca72ce2405b93c5918c1801b028` | NO-GO, first EXPLAIN action | 95 | Audit and guard installed/removed exactly; write transaction not committed; action pair incomplete. |

Both consumed their combined 103-command historical budget. The first outer
phase label was misleadingly `tls`; the adapter rejected a read-only query.
The second historical exception retained `Stop` but lost the exact error code.
Neither fact is repaired by editing its evidence or calling it a PASS.

The second run preserved 561 existing catalog objects while removing 23 audit
additions, then restored the original 556 objects while removing the five guard
additions. JIT disabled, zero mappings, SSL enforcement unchanged. All evidence
remains under the original run directories in `supabase/.temp`.

A final single lightweight read confirmed three registered identities, zero
sessions for those identities, zero rows for the attempted session fingerprint,
zero owned guard/audit schemas and 43 migrations. This closure check is separate
from the 103-command consumed attempt budget (one additional read-only command).
It is not a full protected-memberdata fingerprint or hosted workflow PASS.

## Failure Diagnosis And New Admission

Local PG17 with the actual native libpq adapter reproduced `terminal_row_count`
on the old raw EXPLAIN path. EXPLAIN has no ordinary command-tag row count. The
existing immutable Native reader handles it; the runner now uses that reader
with its required `explain (` prefix. The original hosted record proves only
`Stop`; the exact historical protocol code cannot be recovered from it.

The corrected local native I/U/D test passed with one transaction, one key,
three exact audit rows, a retained DELETE and identical scoped before/after.
Execution times were 9.987 / 0.415 / 6.592 ms, with zero temp blocks. These are
LOCAL values, not claimed hosted measurements. Local protocol failure tests
cover missing/duplicate terminal messages, truncated/null responses and limits.

The owner expressly approved one additional probe after fresh CI: 180 seconds,
128 total SQL commands, one collector, one new synthetic session I/U/D, no token
issuance and no workflow writes. A new exclusive marker binds this authority to
the prior cleanup receipts. No retry or automatic extension is implemented.
Forty commands are reserved for exact safety removal independently of NO-GO.

Current source commit: `d14616586747a809ee445a2069fbb3c081974f6b`.
Candidate SHA-256: `b04a111fbdf526a2ac2b4a8cbdd781313b445e6f5a2247d4625e9378a315ee2c`.
Fresh CI: [38278953845](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38278953845).
Fresh CI is **CLEAN_CI_PASS**; all 421 artifact file hashes and archive digest
verified. The same preceding regressions passed, with 10 probe unit tests,
8 native transport tests and 4 explicit budget tests. No staged secrets used.

## New Hosted Probe: PASS

Run `da412c5b-9212-4acc-bb53-dbc0b311c6bc`; action
`3286b996-c126-4926-aac9-1f3de2b7c8eb`; source composition above unchanged.
Native session-pooler with owner JIT, `jit=true`, official CA, `verify-full`
and full hostname validation. Project/migration identity matched staging 43.

- 32.672 seconds; 107/128 commands (75 normal, 32 reserved safety), one collector,
  zero full database cycles, retries, Auth HTTP calls or application writes.
- Exactly one INSERT, UPDATE and DELETE on one new synthetic `auth.sessions`
  row, all in transaction `1092107882`, backend `1050260`. Same actor and key
  hashes; the DELETE record remains in the saved evidence after row removal.
- Both scoped snapshots: `existing_sessions=[]`, `fixture_rows=0`. No partial
  committed fixture remains. All expected observed writes present, no extra
  write in the scoped seven-table observer. This does not claim global audit.
- DML query IDs: `3836171532023688788`, `8692649598522826815`,
  `-2406994597637048383`; respective EXPLAIN execution times 29.183, 0.702,
  25.491 ms. Each plan: zero own temp read/write blocks. Actual trigger work
  is included in those execution times; no separate production-load estimate.
- Monitored admission query/reader/closing witness: 28.731726 / 52.317043 /
  5.816 ms, zero temp blocks; observed ambient temp-byte delta zero and no
  concurrent long queries. Ordinary safety/catalog reads are not included in
  this query-level zero-temp claim. Background attribution is not inferred.
- Exact audit removal preserved 561 catalog objects; guard removal restored
  all original 556 objects, ACLs and policies. Zero own objects remain.
- JIT disabled with zero mappings; SSL enforcement still enabled. No account,
  password, global Auth setting, migration or managed function was changed.

Evidence directory: `supabase/.temp/phase6e11-auth-metadata-hosted-da412c5b92124accbb53dbc0b311c6bc`.
`sealed-manifest.json` binds 219 immutable evidence files and 107 source files
to the CI receipt, action, complete pair, cleanup and measured query IDs.
Manifest SHA-256:
`296799a29985ded784e3d9f0e90cfe32be50d4e268fa7b9a8981c5b6d976cc00`.
The offline seal checker passed 8 positive/negative tests, including missing
delete, wrong key, datadrift, live JIT, temp writes, budget and object-removal
failure. It makes no hosted calls and is not counted as another canary.

The EXPLAIN correction is now hosted-proven. Historical incomplete attempts
remain NO-GO; this new successful pair does not fill their missing measurements.

## IO And Preservation Boundaries

The historical second run's monitored project/observer reads had zero own temp
blocks, zero observed ambient temp-byte increase and zero long queries. Reported
query execution totals were 8.925859 / 13.67373 / 5.375 ms for those read groups.
Its failed DML produced no retained plan; hosted DML overhead was NOT proven.
Minimal safety reads were not included in that query-level load claim.

There were zero Auth HTTP calls and zero application writes in these canaries.
No full database scans, ordinary account changes, migration changes, Edge deploy,
email, owner window or historical fixture cleanup occurred. Old two workspaces,
control accounts and sessions were not treated as disposable new fixtures.
All 1376 protected local files passed preservation, including the historical
112 valid pairs and incomplete step 113; earlier dirty files remain unchanged.

## Remaining Hosted Work

Real hosted Auth request/session/transaction binding is still outstanding.
The action lease is not an unforgeable Auth request identifier. The fully
assembled controller, fixture prepare/activate, Route A/B, apply/restore,
rejection/conflict/duplicate, full negative-write evidence and protected-data
cleanup checks still need their own source-bound admitted execution. The tiny
observer probe cannot replace them. No owner phone test is open.

## Next Prepared Auth Contract

The next assembled controller must bind the existing six operations to the
same three synthetic actors, live guard, request/session response, action lease,
transaction and exact writesets below. No token or session secret is exported.

| Operation | Expected scoped effects per actor | Required gate |
| --- | --- | --- |
| Issue | users UPDATE 1; audit INSERT 1; one-time-token INSERT 1 | Live guard; exact registered UUID/address; no account creation |
| Verify | users UPDATE 3; audit INSERT 1; one-time-token DELETE 1; session/refresh/AMR INSERT 1 each | Same one-time-token key; returned session key bound to row hash |
| Get user | No writes | Same synthetic user/session; no editable metadata authority |
| Refresh | users/session/old-refresh UPDATE 1 each; new-refresh INSERT 1; audit INSERT 2 | Same session, distinct new refresh key; live guard |
| Logout | session/AMR DELETE 1 each; refresh DELETE 2; audit INSERT 1 | Exact previously observed keys, retained delete evidence |
| Revoked request | No writes, denial | No helper-only denial substituted for a hosted server response |

These are pinned real-CI observations, not assumed guarantees about the hosted
service version. A mismatch stops at its first action; no guessed count changes.
Arm, durable before, server response, durable after, transaction validation and
next-step admission remain separate. Missing evidence blocks dependent actions;
exact safety removal still runs. Token issuance stops when protection is not
provably active. The just-approved native probe did not execute this table.
Route A/B and ordinary-data negative-write coverage remain distinct later gates.

## Publication And Migration Boundaries

No migration was added or applied: local clean CI and hosted identity are 43/43.
CI dry-run EMPTY. The hosted dry-run was not repeated during this bounded audit;
the last M43 hosted dry-run remains EMPTY evidence, not a new measurement.
Staging Pages at source commit `d14616586747a809ee445a2069fbb3c081974f6b`
preserved all 152 runtime assets byte-for-byte and the 19 base private paths
returned 404. Final documentation publication receives a separate receipt.
The worktree intentionally retains earlier uncommitted changes; not clean.

External AI calls/cost: 0 / EUR 0.00

Real-member AI enabled: NO

Production touched: NO
