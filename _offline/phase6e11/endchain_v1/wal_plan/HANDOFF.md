# Frozen offline feasibility checkpoint

2026-11-11. No Main changes; no SQL, Docker, hosted, CI dispatch, historical diagnostic rerun, force-flush or limit change. D3 remains unchanged. This directory is not a runtime probe or an admission candidate.

## Actual evidence

`feasibility-r2.json` and `tests-r2.txt`: 10 selected, 10 executed, 0 failures/errors/skips. Exact current lifecycle ACCESS/CATALOG SQL parses with PG17 EXPLAIN options. Tests check source change, multiple statements, SELECT INTO, writable CTE, missing/invalid counters, private text omission and non-summed parent/child counters. The first failed SELECT-INTO check is preserved in `feasibility.json` and `tests.txt`; the narrow correction handles the parser's `intoClause` field. These are syntax/projection tests, not actual PostgreSQL or worker evidence. SELECT parsing alone is not authorization or proof of side-effect freedom.

Main reports component 43095501354 ended startup_failure, zero jobs/artifacts, GitHub internal error request 5f31158b-de0f-11f1-8b55-7e40a64363cb. Not independently queried here. Therefore this attempt supplies NO PG/Auth/worker evidence and proves no application-code cause. No redispatch performed or proposed by this delivery.

## Different WAL method: narrow feasible design, not executed

Use executor instrumentation rather than another pg_walinspect/LSN interval run:
`EXPLAIN (ANALYZE TRUE, BUFFERS TRUE, WAL TRUE, TIMING FALSE, VERBOSE FALSE, COSTS FALSE, SERIALIZE TEXT, FORMAT JSON)`.

Proposed bounded sequence: BEGIN READ ONLY; one identity/TLS/PG17/read-only/timeout attestation; exact ACCESS EXPLAIN; exact CATALOG EXPLAIN; ROLLBACK. Five explicit commands, existing 5000ms statement limit, no retries/warmup/extensions/flush. Driver connection implicit commands are NOT included or bounded by five. Only a separately reviewed disposable-local integration may execute this; no connection code is supplied here.

Exact query hashes:
- ACCESS ad5ff4effb3cdfc8647f1bfa24815040cf3b1b20537b36d4f163ee36ccc8cb23
- CATALOG 5e3cce093162da75aa5133f845bcb11396d67126a4ddec3b0345711dedb950ec

Output projection allows only structural positions and numeric WAL records/FPI/bytes/temp-read/temp-write counters. Missing values are unknown, never zero. No raw plan, SQL text, filters, relation names or rows exported; no parent/child summation.

Limits: ANALYZE actually executes a new query; fixture identities and catalogue context must match before comparison. D3 parent actors/empty clean47 registry do not prove equivalence to original ACCESS actors. Planning, utility, background and network work are not covered by executor counters. SERIALIZE TEXT adds conversion work but PG17 SerializeMetrics contains BufferUsage, not WalUsage: complete serialization-WAL coverage cannot be claimed. No new zero can erase historical nonzero WAL, identify its cause, or repair a historical flush gap. Timeout remains incomplete. WAL0/temp0 unchanged.

Official references:
- https://www.postgresql.org/docs/17/sql-explain.html
- https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/src/backend/commands/explain.c

## Interval gaps retained

Existing D2/D3 wal-intervals.json remains the original 18-interval inventory from three historical runs, not regenerated evidence. ACCESS/CATALOG have observed nonzero intervals. Some inspect ranges were incomplete because flush coverage was missing. Later ACCESS coverage and Heap2/PRUNE_ON_ACCESS classification do not establish causal ownership. Zero migrations/absence/snapshot/rowhash samples cannot prove the unmeasured canonical dispatch, Auth, controller, Route A/B, restore, cleanup or terminal intervals. Continuous background attribution remains absent. The new method addresses executor-local attribution for two new executions only, not the full interval inventory.

## Exact admission gates still open

Paths below are relative to Main `_offline/phase6e11/endchain_v1` and were inspected read-only:

1. `quota_candidate_v1/runtime_case_entry.py:90-116` requires complete core/root bounds, source inventory, hosted scope and empty missing_costs BEFORE bootstrap. Static case_ci MISSING labels are not an adequate description of the implemented joins.
2. `admission_budget_root_runtime.py:656-658` explicitly retains actual recovery-state expansion, conditional Auth cleanup, exact caller hosted projection and transitive import/subprocess source closure. Lines 683-685 still return executable_program=None, incomplete source/bound flags and unknown local/hosted totals. Driver/OCI provenance is independently missing at 463/473. A working source hook is not a measured upper bound.
3. `test_admission_budget_current_release.py:68-70` currently expects normal capacity 2340 and meter-required limit 2352 against cap2349. This is a source regression expectation, NOT a newly executed compiler proof. Removing a three-command arithmetic overrun alone cannot close unknown root/setup/recovery/cleanup costs. No cap increase permitted.
4. Fourteen source fault selectors exist (pre/post migration, mid Auth, controller, routes A/B, restore, lost response, duplicate, timeout, partial cleanup, cleanup failure, final check, closure). Actual normal+14 isolated same-source full-chain original receipts are still missing. Auth/component/rollback tests do not substitute for these. Lost commit/unknown Auth and failed producer-stop evidence must remain uncertain.
5. The failed startup yields no original waited-worker exit/result/export, parent ownership/stop/remove/absence, after-stop counters or actual strict-TLS Auth evidence for D3. Local tests cannot fill these fields.

## Small next step

No further run in this task. Preserve the failed startup as a control-plane result. Before any later Main-authorized component attempt, keep the reviewed source and parent cleanup unchanged. If a later execution exists, first validate the original worker wait/result/export and parent lifecycle/Auth-safety records, then map measured before/after-stop numbers to the exact driver/OCI/conditional-cleanup unknowns. Observations remain observations, not universal cost bounds. Only after fixture equivalence and local connection accounting are explicit is the two-query EXPLAIN diagnostic a defensible separate measurement proposal. Do not invoke the fifteen-case gate while its source preflight remains incomplete.

## Reproduction

Use the existing pinned PG17 parser dependency in PYTHONPATH; no install. `python -B -m unittest discover -s <this-directory> -p test_plan_only.py -v` repeats the ten pure tests. `inspect_only.py --source-root <trusted-Main> --receipt r2` was the source-reading run; receipt files use exclusive creation and intentionally refuse overwriting the preserved result. Source hashes, parser binary hash and query hashes are recorded in feasibility-r2.json. No full452 rerun or root enumeration was performed.

Final state: full_chain_admission=false, actual_pg=false, READY unchanged. Freeze this delivery after hash manifest creation; no integration targets requested.
