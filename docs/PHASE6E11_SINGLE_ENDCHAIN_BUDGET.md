# 6E-11 Single Endchain Budget

Status: OFFLINE COMPOSITION IN PROGRESS / HOSTED NO-GO.

## Owner Authority

The owner authorizes one full synthetic endchain with at most 1,280 SQL
commands. This is not a permanent default and does not authorize a retry.
The prior 128-command canaries remain unchanged. Only staging
`mokxyyullfhkfalopbzd` and staging main are in scope.

Reserved run: `32321f17-07f1-4f3d-aa4b-3218bc7368a4`.
No hosted attempt for this run has started. No JIT, Auth, fixture or migration
write was performed during this preparation.

The pending approval noted in PHASE6E11_ENDCHAIN_PREPARATION.md has been
superseded by this explicit owner GO. Its historical results are retained.

## Boundaries

- One collector, no automatic full-run retry, maximum ten-minute authority.
- Ordinary work stops at nine minutes; remaining time is for bounded safety
  closure. Existing connection/query timeouts are not increased.
- Every command, including BEGIN/COMMIT/ROLLBACK, counts. Internal statements
  in an atomic DO are not separate protocol commands; this does not exempt
  their writes, time, WAL or IO from measurement and writeset validation.
- Source-bound phase budgets and lifecycle/cleanup commands must be compiled
  before hosted admission. The phase allocation in budget.mjs is currently
  a draft, not an admitted complete run.
- Missing/extra writes, incomplete pairs, identity mismatch or unexplained
  own IO remain NO-GO. Safety removal is separate from dependent fixture
  cleanup and cannot turn an incomplete pair into PASS.

## Database Candidate

CLI 2.117.0 generated migration
`20261012185121_phase6e11_single_endchain_budget.sql`. It is local only.
Migration 43 and all earlier migration bytes are preserved.

The candidate permits 1,280 only for the reserved run UUID. All other run
rows retain 128. Its private SECURITY INVOKER trigger prevents changing
the exceptional receipt's identity, expiry or source bindings, decreasing
the counter, deleting the receipt or reopening a stopped run.
No client execution/schema grant is added. The existing ten-minute
constraint remains.

Local PG17 database checks: 30 PASS. Evidence:
`C:/Users/Fitme/AppData/Local/Temp/fmz-fingerprint-offline-k650ng02/single-budget-result.json`.
M44 SHA256: `01719a133e732b33fa435be25552f92824acd29ae0f4be2af669a29c3e168d3f`.
The earlier local attempt stopped because the PG17 binary bundle lacks
psql.exe; the installed psql18 client was then used against the PG17 server.

## Actual Command Shape

The unchanged existing adapter trace has a lower bound of 1,323 commands:

| Component | Commands |
| --- | ---: |
| Five durable phases for 63 actions | 315 |
| 45 request transactions plus separate seals | 360 |
| Two four-command read-only snapshots per action | 504 |
| Auth observer arm/disarm for 18 actions | 90 |
| Nine independently guarded issuance operations | 54 |

This excludes setup, lifecycle, cleanup, IO checks and final measurement.
Thus 315 was an evidence-store minimum, not a complete execution budget.
This trace is not a claim that every possible safe implementation needs
1,323 commands. Evidence is retained at
`supabase/.temp/phase6e11-endchain-budget-6215dd41adf94c8482190342799eb99e/`.
It correctly denied hosted admission before command 1; no hosted budget was
spent.

## Local Efficiency Work

1. New native transport avoids reserve(), preserves fetch_types:false and
   explicit request BEGIN/COMMIT. Its seal is a separate autocommit SQL
   transaction, reducing eight protocol commands to six. Missing sealing
   still blocks dependent requests under unchanged M42.
2. A dedicated explicit READ ONLY / READ COMMITTED cycle takes a new
   statement snapshot for every scoped read. It verifies backend, isolation
   and read-only state. It never reuses a historical before-state as fresh
   evidence. No parallel fingerprint collector is introduced.
3. Auth observer arming retains the original guarded DO body, with the same
   transaction-local lock timeout, in one atomic statement instead of four.
   The original renderer remains unchanged.

The scoped reader passed on real local PG17 with the pinned native Deno
driver and a local CA: missing -> insert -> update -> delete were all
visible on the same backend. A write through the reader was refused.
Evidence: `supabase/.temp/phase6e11-cycle-local-8bed335cb131452e86aed5e3bb32a5ca/`.

Compact Auth arming passed all 34 existing local observer/security/concurrency
checks plus the synthetic native insert/update/delete probe. Probe temp
blocks written were zero; this is not hosted IO evidence.
Evidence: `C:/Users/Fitme/AppData/Local/Temp/fmz-fingerprint-offline-3lkvn2t5/metadata-audit.json`.
One preceding local attempt hit a port collision with another owned local
test. It did not connect to staging; its log is retained in
`C:/Users/Fitme/AppData/Local/Temp/fmz-fingerprint-offline-7cavbbqu/postgres.log`.
Database-backed tests are subsequently serialized.

The full native workflow adapter is not yet hosted-admitted. Earlier local process
watchdogs stopped it before completing all 45 cases. Preserve both
`phase6e11-workflow-local-4eddd86408194c0686953f4fdaa0459e` and
`phase6e11-workflow-local-8d54d9eee7ec4ed6bac52dd7208cbb7d` under
`supabase/.temp`. These partial runs are not complete PASS evidence.
With explicit five-second query and two-second close deadlines, the next
local run completed all 45 original cases and complete audit pairs:
`supabase/.temp/phase6e11-workflow-local-acc772cadf0c4e1b96b6841ba9a2e3d2/`.
It used 270 request/seal protocol commands instead of 360, with TLS and the
official pinned native Deno driver. These are local Auth stubs, not hosted
Auth proof. The old watchdogs lacked sufficient captured phase output to
attribute their exact cause; the new PASS does not rewrite those failures.

Current local units: 243 Node tests and 37 Python tests PASS. A separate
immutable receipt binds the 37 Python tests and the 177-test focused Node
subset, not an additional 177 independent tests:
`supabase/.temp/phase6e11-endchain-cf6b6eb1a1b04e6aa5b89b999aea2809/`,
manifest SHA256 `f3bf1eb2ef3a292c095103596b23cf80b8338864ac5d26d2dea0bfff521acb68`.
The 1,376 protected pre-existing files remain byte-identical to the retained
controller baseline.

## CI And Admission

The new CI workflow builds the full empty 44-migration candidate and runs
the existing guard/controller/Auth component checks plus new budget/adapter
checks. It has no staging credentials and cannot deploy or connect hosted.
It expressly sets `full_chain_admission=false`; clean component CI alone
does not prove a complete hosted runner, lifecycle ledger or cleanup.

Before deployment: finish the exact full orchestration, scoped writesets,
failure/safety budget, source-bound CI and preservation checks. The new
composition must not reuse the old 43/43 admission.

## Status

No new hosted call, migration application, owner window or owneracceptance.
6E-11 and the phone test remain NO-GO. 6E-21 remains unaccepted.
No 6E-12 server integration or JARVIS handoff.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
