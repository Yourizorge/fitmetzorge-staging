# Parallel staging results, 26 October 2026

Status: private application CI PASS; 6E-11 endchain and owner phone test NO-GO.
Four agents assisted with budget, failure handling, application integration and
independent review. Main alone integrated and pushed. No hosted attempt was used.

## Working user actions, proven in disposable CI

Source `06b9ac0ad961705a3f7fc8de2fb80d3cf82637a4`,
[app CI40354972820](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/40354972820):

- Actual local GoTrue login, server session/actor/workspace validation and RLS.
- Edit a catalogue-bound plan; separate member confirmation, Route A trainer
  approval and application; Route B has no trainer step. Restore as a new version.
- Applying a new plan expires current comparison facts and notices, preserves
  comparison history, and permits a new comparison bound to the new version.
- Start a historical workout, record a partial workout, explicitly finish it,
  retain its snapshot and view it after reload and re-login.
- Send an offline draft explicitly; reject conflicting newer state without
  overwriting it; a lost response does not duplicate the applied change.
- Consent withdrawal blocks new processing. Package21 remains default-off and
  its full-day command is denied in the composed accepted-scope flow.

These actions are not newly released on hosted Supabase or the public app.
The existing public runtime and earlier demos remain unchanged. Screenshots and
mobile checks are browser emulation, not an additional physical owner test.

| Verified group | Result |
|---|---:|
| Canonical migrations plus private app candidates | 45 -> 46 -> 47, clean |
| SQL regressions | 12/12 |
| Registration12 | 25 database, 15 browser, 4 Auth |
| Private registration transport | 46 database, 4 Auth |
| Combined integration | 74 database, 209 browser, 4 Auth |
| Composed user journey | 191 browser |
| Account centre / offline shell | 79 / 73 browser |
| Eight selected-release checks | 359 |
| CI-profile unit tests | 16 |
| Source binding before and after | 198 sources, PASS |
| Four local CLI steps | 47/2/22/2 protocol commands; 8 observers each |
| Final local dry-run | EMPTY |

Groups are reported separately; they are not summed into an application-readiness
percentage. The 616-file artifact was hash-verified, archive SHA256
`d2c4719cac92a74d9005d01fa606e840ea8df1258bdc8f554607a982128171f5`.
Selected byte-identical receipts are retained in
`_offline/phase6e_server_v1/receipts/ci-40354972820/`; the full original archive
and screenshots remain in the ignored CI evidence folder.

Platform: Supabase CLI2.117.0, PostgreSQL17.6 (170006), container
`supabase/postgres:17.6.1.167`, repository digest
`sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb`.
This is not a hosted migration47 claim.

## Remaining endchain blocker

[Endchain CI40354914899](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/40354914899)
cleanly rebuilt45/45 and passed the recorded ACL/RLS/request checks, but stopped
before guard installation, Auth issuance and workflow mutation. The new numeric
failure receipt binds exact source hashes to query families:

| Read-only metadata query | WAL bytes | WAL records | Full-page images |
|---|---:|---:|---:|
| ACCESS | 108 | 2 | 0 |
| CATALOG | 836 | 15 | 0 |
| MIGRATIONS, ABSENCE, statistics reader | 0 | 0 | 0 |

All expected call deltas match. Temporary writes and background temp-byte delta
are zero; no IO-wait or long active query was observed at the sample times.
Reset/deallocation identifiers are unchanged. Query-family attribution is not
exclusive backend attribution, and these numbers do not identify the WAL record
types or affected objects. No harmless-cause or hint-bit claim is inferred.

The strict zero-read-WAL check remains intact. PostgreSQL documents that
[READ ONLY does not prevent every physical disk write](https://www.postgresql.org/docs/17/sql-set-transaction.html),
but that general fact is not evidence explaining these specific17 records and
does not authorize a WAL exception. A bounded CI-only WAL-record classification
is the next independent diagnostic step; no new hosted retry is needed for it.

The separate default-off `phase6e11-wal-diagnostic.yml` uses a fresh empty local
45-migration fixture, not the historical Auth fixture. It executes only the four
existing metadata queries with a maximum of16 diagnostic commands, five-second
query/connect limits, loopback TLS/CA validation and explicit READ ONLY/ROLLBACK.
Bootstrap CLI calls are recorded separately with unknown internal SQL totals;
16 is not a claim about total CI setup commands or a hosted budget. It never
invokes the full endchain, JIT or hosted Auth. The result is always
`DIAGNOSTIC_ONLY`, with admission and WAL-zero PASS explicitly false.

Only WAL record types and counts may leave the query; no descriptions or block
data. Flush coverage, bounded intervals, missing extension privileges and
incomplete transport fail closed without retry or forced flush. The empty
fixture cannot retrospectively explain the historical17 WAL records. Local
helper17 and entry15 mock tests pass; live diagnostic results remain separate.
An independent reviewer found and verified the correction for incomplete
flush coverage before this diagnostic was dispatched.

Dedicated diagnostic CI40362576305 at46a5c3b rebuilt45/45 but safely stopped
after7 diagnostic commands: the ACCESS interval ended at `0/282D5B8`, while
flush was only `0/282D478` (320 bytes behind). Its record inspection is
incomplete, not a WAL-zero or causal PASS. Rollback and removal of the fresh
disposable stack are confirmed. No Auth account was created. All91 artifact
hashes verify; archive SHA256
`4deb1b353ee502bcee891a1c2ce74b614f5cb1e48f623d3ece48e1dd935bd248`.
Six byte-identical receipts are in `receipts/ci-40362576305-flush-lag/` under
the endchain source directory.

The bounded CI-only correction captures the end-LSN first, waits once for300ms
inside the same inspection command, then verifies flush coverage. It neither
forces a flush nor retries; lag still stops the diagnostic. Query/connect limits
stay5s, command cap16, maximum aggregate wait1.2s for four queries. The helper's
18 mock tests and PG17 parser check pass. This changes no hosted WAL allowance
and does not retrospectively complete the first diagnostic.

The CI stopped at meter command39 (`gates_before_io_sample`) and confirmed
rollback at40. Exactly40 charged commands are4 preflight plus36 baseline.
The native trace has52 entries:16 disposable-CI bootstrap plus36 baseline;
preflight is separate. Meter `complete=true` describes booked events, not a
complete proofrun. Auth/guard/controller/workflow phases were not reached.

| Phase | Planned capacity | Used in stopped CI chain |
|---|---:|---:|
| Preflight | 4 | 4 |
| Migration | 128 | 0 |
| Baseline | 61 | 36 |
| Setup / guard | 33 / 13 | 0 / 0 |
| Auth / controller | 318 / 286 | 0 / 0 |
| Route A / Route B / restore | 191 / 286 / 54 | 0 / 0 / 0 |
| Measurements / IO | 136 / 97 | 0 / 0 |
| Cleanup / final / closure | 633 / 97 / 1 | 0 / 0 / 0 |
| Normal total / authorized worst case | 2338 / 2349 | 40; full path unexecuted |

Cleanup/final/closure reserve731 remained intact. No existing hosted fixture,
session or account was cleaned up. `guard_audit_removed=true` means no temporary
guard was installed in this stopped chain, not a newly measured global zero.
The 555-file artifact was hash-verified, archive SHA256
`393744749792e27e363667ad9cf28dd3024f86052aabcb4de980cbf595ece695`.
Selected immutable receipts are in
`_offline/phase6e11/endchain_v1/receipts/ci-40354914899-numeric-stop/`.
Historical failed runs,112 historical pairs and incomplete113 are unchanged.

## Source and publication

| Agent role | Integrated outcome |
|---|---|
| Budget and composition | Full2338/2349 model, safe reserve release and worker-exit ordering; no full CI path claimed after the early stop. Dedicated diagnostic entry is separate. |
| Data/IO and safety | Numeric failed-pair receipt, bounded metadata-only diagnostic and flush-coverage correction; strict read-WAL gate unchanged. |
| App integration | New-plan comparison invalidation, exact CI harness/source loading, successful real local app CI and corrected source-bound work-register statuses. |
| Independent reviewer | Checked hashes/claims and the application proof; found incomplete flush coverage, verified its fix, and admitted source-only diagnostic CI, not hosted execution. |

Agent patches were integrated only by main. The final local endchain unit suite
passes359 tests, including the32 new diagnostic helper/entry cases. The updated
work-register/release checks pass17 tests. No agent changed staging data or
published independently.

- `24574c1666e945b2eff410b13971643570e1d6dd`: combined private candidate,
  validated reserve release, safe child completion, app comparison invalidation
  and bounded source transport. Local325 endchain Python,138 app Python and147
  app Node tests passed at that checkpoint.
- `06b9ac0ad961705a3f7fc8de2fb80d3cf82637a4`: retained numeric IO failure evidence
  and corrected checkout/candidate test paths. Local327 endchain Python and141
  app Python tests passed. Independent review found no remaining source blocker
  in those fixes; it explicitly keeps hosted admission NO-GO.

Pages run40354775552 at06b9ac0 succeeded. Archive SHA256
`3b0a16c9b961869556ab3d6b5cd82f31fd9c3c07acaed0119b400d236198ac5c`:
152/152 protected runtime assets byte-identical, private roots absent, seven
HTTP probes404. No runtime, frozen source or migration1-44 changed in this work.
Older dirty files remain outside these commits; the worktree is not claimed clean.

Hosted migrations: last proven44, not remeasured; candidate45 remains unapplied.
The reserved6f8c run is unused. No JIT mapping was opened or changed this turn,
so this report does not claim a new live mappings-zero measurement.

Owner phone test: NO-GO; no new window or expiry.
Phase6E: incomplete. Package21: unaccepted and default-off.
External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
