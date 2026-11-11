# Opt-In Disposable Runtime Adapter

This is a versioned **local-only execution route**, not a rollback-only scenario
model. No old module, UUID allowance, M45 byte, canonical migration, Auth helper,
fixture SQL, timeout or hosted permission is changed. Runtime activation still
requires the real full source-bound register; phase totals or an old receipt do
not supply it. Nothing here has been run against PostgreSQL or GoTrue yet.

## Architecture

Preregister 15 global cases (normal + 14 faults), with a separate one-case quota
manifest/catalog in each fresh job. The compiler's per-catalog cardinality is
not a hosted limit and need not change; each SQL cap remains at most 2349. The
15th inventory is checked against 14 previous inventories, within the existing
validator bound. None of these declarations supplies missing fault semantics.

Use one fresh GitHub matrix job/VM per case under the same actual GitHub run and
source (`max-parallel: 1`, `fail-fast: false`, no retry). Each namespace keeps the
existing fixed `supabase_db_fmz-db41-ci` container, `postgres` database, Auth
container and loopback ports. Do not invent IDs, database names or container-name
suffixes. GoTrue must use that case's PG instance, not a shared Auth database.
Preserve `github_run UNIQUE`, retained claims and existing running-slot uniqueness.
No fake GitHub IDs, rollback wrapper, registry deletion, claim reset or retry.
The new quota catalog is installed only after the unchanged baseline migrations.
The pending quota CLI reserves 64 protocol commands plus eight observers before
dispatch; its 17-statement payload is inside that envelope, never charged as 17
and then applied again. Cron isolation is separately labelled disposable setup.

Main must provide a measured isolation inventory with exact case/run/source,
PG/Auth container digests, PG system identifier + database OID, equal technical
PG-target/Auth-target hashes, registry-empty/PG17/SSL checks, and its evidence
hash. This adapter validates that inventory and rejects reuse against the prior
case list. It does not produce inventory or treat offline test data as observation.
Retain existing server/image, 47-history/raw-source, CA and actual SSL evidence;
target validation alone proves neither the image nor migration history. A parent
collector must validate all inventories across jobs (a job alone cannot attest
other jobs), with per-case immutable artifact names and upload on failure. VM
teardown is not a cleanup PASS. Terminal claims/evidence must be collected first.

Use the existing app rebuild intact unless a separate thinner bootstrap is
implemented and tested. Do not call endchain `prepare_registered_database`,
which resets the database. The app migration indices are 0 and 2, with the
actual intermediate dry-run retained; canonical45 requires its separate receipt
at history44/index0. Never synthesize receipts or reset the CLI serial. On an
already-clean47 stack, a pre/post-quota-delta fault is not a canonical-M45 fault.
Build dependencies/baseline before issuing a just-in-time one-case manifest;
never renew an expired shared14case lease. A preregistered case mapping must bind
each manifest to the same actual source/candidate/run without resetting claims.

## API

```python
from quota_candidate_v1.runtime_adapter import source_inputs, prepare_case, CaseComposition, execute_case

# Include source_inputs(root), plus the real plan file, in compiler.prepare sources.
prepared = prepare_case(root, manifest, case_id,
    plan_ref={'path': plan_path, 'sha256': plan_sha256},
    isolation=measured_case_inventory, prior_cases=previous_case_inventories,
    environment=observed_ci_environment, connection=sanitized_native_parameters,
    ca_path=official_local_ci_ca, now=utc_now)
composition = CaseComposition(prepared, runtime=verified_disposable_runtime,
                              phase_faults=phase_faults)
execute_case(gate, composition, registered_lifecycle, existing_registered_config)
```

`prepare_case` performs file/JSON/model checks only, no DB/network operations.
It independently calls the new `admission_budget_current_dag.compile_current_release`
on the source-bound DAG. The historical compiler is not an admission fallback.
Missing or incomplete coverage is `runtime_full_register_*`,
not a true admission flag. It never converts a historical register to the new ID.
The returned context keeps candidate `execution_admitted=False` and hosted false;
the model can authorize a bounded local diagnostic attempt, not a full CI PASS.

The Node workers only accept this trusted private parent context. They verify
actual source files, binding, CI identity, local environment, phase ceilings and
register file hash before the first install request. They do not independently
recompile Python's dispatch DAG: `prepare_case` is a required parent boundary,
not an optional convenience or an API for untrusted/browser input.

`execute_case` calls the existing real runner only after source/expiry, exact
case/lifecycle/IdentitySession, disposable runtime and confirmed metered prefix
checks. Build the existing RegisteredLifecycle with `composition`, case UUID,
measured identities, existing guard/audit/AuthContract/sql and an IdentitySession
bound to that same runtime/composition. The caller supplies verified prefix
receipts through the unchanged admission hooks first. It must not give the Gate
a legacy `apply_endchain_migration` method. Missing prefix is a pre-worker stop.

## Actual Path

- `runtime_auth.mjs`: the existing real SyntheticAuth 12-prefix/6-terminal calls,
  guarded issuance, AuthEvidence replies and safetyAuthlogout protocol. Only the
  new grant/store/controller binding and explicit local-only preflight differ.
- `runtime_node.mjs`: original Controller check/command/claim/execute methods,
  original NativeStore claim/before/record/halt SQL. Its close query is the same
  source SQL, with the new exact cap instead of the old identity lookup.
- A handoff can only be emitted after this controller really claimed and stored
  12 validated pairs. The 71-action worker receives their technical hash journal;
  RegisteredLifecycle still independently requires all three Auth contracts at
  step 4. No caller-selected starting step or invented claim is accepted.
- `runtime_workflow.mjs`: the unchanged product loop from `runWorkflow`, including
  45 product actions + revoke +25 cleanup batches, JWT/user checks, actual HTTP
  handler, request.call/COMMIT/seal, preregistered writes and complete pair checks.
- `runtime_parent_workflow.py`: existing native orchestration with the versioned
  worker path, real boundary faults and private HTTP dispatch acknowledgements.
  Setup/restore, QueryIO strict WAL/temp gates and measurement pairs remain.
- `runtime_faults.py`: all 14 named selectors at real migration/Auth/controller,
  Route A/B, restore, committed lost-reply, validated replay, native timeout,
  partial cleanup, removal, final metadata and closure boundaries. A hook not
  reached because an earlier gate stopped is not an observed fault PASS.
- `runtime_dispatch.py`: 72 distinct /user attempt positions tied to the original
  72 prepaid tickets. Response headers are not claimed as verified identities;
  aggregate 360-command confirmation remains separately required.
- `runtime_prefix.py`: one real instrumented pending CLI plus two empty dry-run
  slots, immutable raw ledger/policy references, exact source/history checks,
  strict TLS and the existing 64/28/28 + 8-observer bounds. Unknowns stay consumed.
- `runtime_history.py`: exact historical44 DB hashes plus in-memory source-AST
  validation of M45/app46/app47/local quota. Observed SQL history hashes remain
  distinct from raw source hashes; no raw historical SQL is exported.
- `CaseBudget` inherits the existing charge/confirmation/BudgetStop/safety methods.
  Its initializer consumes the new model-checked capacity. No old constants are
  patched, no meter is reset, and unknown Auth/partial logout stays NO_GO.

## Main Integration Prerequisites

1. Provide the actual new full dispatch DAG + source/case coverage. None is
   manufactured here. Existing 14 component receipts are insufficient.
2. Use `NativeRuntime.disposable`, the existing real RegisteredLifecycle and
   IdentitySession with the new case ID. Gate must not expose legacy
   `apply_endchain_migration`: adapter refuses canonical M45 reapplication.
3. Supply real prefix/CLI receipts and invoke inherited prefix admission only
   after their verification. `counted_close` retains all original checks,
   including the three CLI slots. No fake quota CLI receipt is constructed.
   The executable PendingPrefix exists, but its versioned lifecycle/catalog
   join and complete ordered/recovery DAG remain mandatory unfinished joins.
4. The manifest lease must fit the real guard expiry returned at install.
   Prepare it just in time; guard/worker/session/query timeouts are unchanged.
5. Keep registered_runner's 200 messages/180s and the workflow's existing
   120s worker/125s parent timer. Preserve original failures and parent cleanup.
   No artifact-limit increase. New runtime source files are source inputs, not
   extra per-action evidence; runtime event/artifact production remains the old path.

`case_ci.CASE_NAMES` is exactly `('normal', *admission_budget.CASES)` and its
SOURCES list includes every new package file. READY remains false; run fails
before bootstrap while the current DAG, recovery/fixture, lifecycle/catalog and
case-terminal verifier joins are incomplete. Neither hook source nor unit PASS
is real 14-phase evidence. The collector must receive the measured isolation
dictionary unchanged and reject repeated PG system/container identity across all
15 artifacts. No endchain/hosted PASS is asserted.

## Tests

`test_runtime_adapter.py --source-root <checkout>` runs source-contract checks,
offline missing-register/isolation tests, existing-meter behavior and Node tests.
It uses a clearly synthetic finite graph and fake SQL driver solely for unit
tests. These are not real DB/Auth/fault receipts. In particular, committed versus
lost-result transitions in unit tests do not prove a PostgreSQL commit occurred.
The workflow loop and parent IO/cleanup body are compared to actual source so a
runtime fork cannot silently become rollback-only or omit production checks.
