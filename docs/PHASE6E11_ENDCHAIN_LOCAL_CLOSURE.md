# 6E-11 Endchain Local Closure And Remaining Admission

Date: 2026-10-12. Status: LOCAL / CI COMPONENT PASS; HOSTED ENDCHAIN NO-GO.

## Scope And Commits

Only Yourizorge/fitmetzorge-staging main is involved. No JARVIS handoff or
modification, production, APPFMZ, website, real-member AI or external AI call.

Start HEAD: `298f62bb8cc02b13a0a58425ce835225ddd68132`.
Offline budget/CI preparation: `2de855f0143b6ae69fb6987f3751feb67662b4d2`.
Offline error/cleanup corrections: `f3866b21bbcd7bd22ffef91b8e20ab62ee7e0ad6`.

Both commits were pushed to staging main. Only the isolated endchain/controller
tests, source-only CI workflow and documentation changed. Existing dirty runtime
files were not staged. M44 remains an untracked, unapplied local candidate.

The owner-approved one-run allowance of 1,280 has NOT been consumed.
Reserved run: `32321f17-07f1-4f3d-aa4b-3218bc7368a4`.
New hosted attempts / SQL commands / JIT grants / Auth writes: 0 / 0 / 0 / 0.

## Proven Results

| Check | Result and limits |
| --- | --- |
| Complete local unit suites | 263 Node and 47 Python tests PASS; no skipped cases |
| New clean Supabase CI | 44/44 PASS, private ACL/RLS checks PASS, local dry-run EMPTY |
| Existing SQL regressions | 12/12 PASS in the disposable CI database |
| One-run M44 budget/ACL checks | 30 PASS |
| Temporary identity guard | 34 CI database/security/concurrency checks PASS |
| Temporary Auth metadata observer | 34 CI checks PASS |
| Real local GoTrue | 18 exact Auth contracts PASS, not hosted Auth evidence |
| Native local workflow and cleanup | 71 paired actions PASS: 45 workflow, 1 revoke, 25 delete batches |
| Local deletes | 123 rows in 12 fixture tables; exact I/U/D multiset, xid and row-key checks; protected local rows unchanged |
| Preservation | 1,376 pre-existing source/evidence files byte-identical to retained baseline |

Counts overlap where a narrow suite is included in a larger suite; they must
not be added into a purported independent total.

The 71-action run used local Auth stubs, not live Auth. It intentionally leaves
the local window and registered local identities available for separate lifecycle
tests; it does NOT claim complete hosted fixture or account cleanup. Its disposable
PG17 process has been stopped. No historical evidence or retained data files were
deleted. Old incomplete attempts, including historical step 113, remain incomplete.

CI: [38302413021](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38302413021).
Head: `f3866b21bbcd7bd22ffef91b8e20ab62ee7e0ad6`.
Candidate SHA256: `ff9577b75b88a13e65c93e0d24fe3e4241c23aad7866a5154e4f215b70a875c1`.
Artifact archive SHA256: `5e8e02de5d2e0e4dea590ca956377d5a5556e87ebe9a43d82edd40679b36f64d`.
All 463 manifest file hashes verified. The artifact explicitly records
`full_chain_admission=false` and `hosted_admitted=false`.

CLI: 2.117.0. PostgreSQL: 17.6.
Image: `public.ecr.aws/supabase/postgres:17.6.1.167`.
Digest: `sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb`.
Local GoTrue: `supabase/gotrue:v2.196.0`.

## Corrections

- Request/reader errors retain the primary failure phase even if rollback or
  connection close also fails. The durable controller stop stores both sanitized
  cleanup failures, without raw driver messages or secrets.
- A closed/lost native request connection cannot silently reconnect for rollback
  or replay the failed action.
- The existing synthetic operator may perform registered DELETE-only batches in
  its Route B test workspace for this exact run. This is not trainer authority
  over Route B business operations. It requires the explicit operator, revoked
  window gate and at most eight deletes. Existing M42 independently enforces
  operator, window status and scope. Business B actions remain denied.
- The local cleanup harness reads the window revision independently once B state
  is deleted. The old historical version function is not changed or backfilled.
- CI artifact retrieval verifies archive digest, every file hash, source/run/head,
  expiry, paths and duplicates; previous evidence is never overwritten.

The first local cleanup test stopped after 60 good pairs because the harness
expected a revision in the now-absent combined A/B version view. Retain
`phase6e11-workflow-local-86dcef4f8e9f407099e0b44d5ebd24b9` as partial local evidence.
The corrected new run is separate; it does not retroactively fix that result.

## Exact Remaining Budget Gate

The old adapter lower bound was 1,323 commands before lifecycle work. The new
locally proved command shapes reduce the 63 Auth/workflow actions to 801.

The real 25-batch cleanup plus revoke adds another 338 when including five
durable evidence phases, two fresh scoped reads and the six-command request/seal
transport. Thus known actions total 1,139, not 315.

With the current 64-command safety reserve, 77 ordinary commands remain for ALL
other work. This remainder is not yet proven sufficient.

An offline replay of the actual draft phase limiter stops at:
- phase: `cleanup`;
- simulated command: `940`;
- code: `phase_query_budget`;
- action: `delete_b_states`, batch 14.

This is a LOWER-BOUND SIMULATION, not a hosted failure or actual SQL count. Setup,
reader envelopes and final checks are omitted, so 940 must not be presented as a
hosted command number. Simulator zero metrics are not WAL/temp-write evidence.

The provisional cleanup allocation is 240 including 48 reserved safety commands,
leaving only 192 for ordinary cleanup, while the known cleanup needs 338.
The phase distribution therefore cannot be admitted as-is. The global 1,280 cap
and the reserved run stay unchanged; no extra permission or budget was requested.

## Work Still Required Before Hosted Admission

1. Finish source-bound fixture preparation/activation and final window deletion,
   including their exact writesets and controller phases.
2. Compile EVERY protocol command for setup, catalog/object validation, guard and
   observer lifecycle, measurement envelopes, query-level IO, controller claim/
   close, final data preservation and migration checks. Rebalance the draft phase
   allocation only after the complete normal and safety paths fit the fixed cap.
3. Connect the scoped collectors, real Auth, signed controller admission, workflow
   transport and independent IO attribution into one executable composition.
   Do not substitute synthetic zero IO readings for unavailable measurements.
4. Prove the FULL composition and failure cleanup in new source-bound CI, rather
   than treating the present component artifact as full-chain admission.
5. Only then refresh hosted project/source/migration/fixture admission, apply M44
   if all gates pass, and spend the one registered hosted run.

The ten-minute grant does not override Edge worker/request lifetime limits.
The final orchestration must also prove that it fits its actual execution model.
No timeout increase, automatic retry or security relaxation is authorized by this
report.

## Migrations, IO And Publication

Last hosted proof remains 43 migrations. No hosted migration/history/dry-run was
queried or changed during this preparation. CI 44/44 and its empty dry-run are
LOCAL CI results, not a claim that staging is on 44.

M44 local SHA256:
`01719a133e732b33fa435be25552f92824acd29ae0f4be2af669a29c3e168d3f`.

The separate earlier local compact-audit probe proved zero own temporary blocks.
This turn has no new hosted WAL, temporary-write or background-load measurement.
Existing hosted results retain their original narrow scope.

Pages publication of `2de855f` passed; 152 runtime assets matched their frozen
hashes, 19 existing private paths and 32 new endchain paths returned 404.
Final-head Pages and asset receipts are stored separately after this report commit.
No Edge deployment or application-runtime change was performed.

Worktree is intentionally NOT clean: older uncommitted changes and the unapplied
M44 candidate are preserved. Do not reset or include them in an unrelated commit.

## Evidence Locations

All below are retained under `supabase/.temp/`:

- `phase6e11-endchain-ci-aee704968a24413aa32e5e531e0184fb/artifact-run-38302413021/`
- `phase6e11-workflow-local-c1cc53eb401945208f2b7ed83eb06825/`
- `phase6e11-endchain-5c4749c94d93467297daf0db6ff538cb/`
- `phase6e11-endchain-budget-replay-20261012-1/budget-replay.json`

Cleanup-result SHA256:
`3454bf0644e62280cd65b7216c84ed89baed69aef68d08ff3e2adaffd0185964`.
Budget-replay SHA256:
`e723e64f8445e63c6dbcfd577261a7cb272827883bb99103dd94203aef9abca2`.
Unit receipt manifest SHA256:
`5932fda04084b627709d7a42892e50ea20e3f37ced05c97f869b332386de460c`.

## Decision

6E-11 / owner phone test: NO-GO.
No owner window, owner acceptance, freeze, 6E-12 server integration or JARVIS handoff.
The smallest next engineering step is a complete executable lifecycle/IO command
ledger and safe phase allocation, followed by full-composition CI. Existing owner
authority is sufficient for that ordinary work; it is not sufficient to skip proof.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.

