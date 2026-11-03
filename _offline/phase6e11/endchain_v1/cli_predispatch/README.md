# CLI Predispatch Component

Disposable CI only. This is executable source instrumentation, not the original
release binary, a TLS proxy, hosted authority, or proof of the historical extra
commands. No original migration or historical receipt is changed.

## Exact Source

- Supabase CLI v2.117.0 annotated tag object:
  `cdcb8e4a8bc8d10658f194186d39739f43c04d1b`.
- Peeled source commit: `21db855916f2c2b12f61cde923a27094b8528b23`.
- This release's `db push` uses TypeScript, `pg@8.23.0`, and
  `pg-protocol@1.16.0`, not pgx. Bun is pinned to 1.4.1; pnpm to 12.3.0.
- `prepare.py` checks HEAD, clean tracked sources and five source hashes, copies
  the hook, then changes only upstream `apps/cli/src/main.ts`. The entry installs
  the hook on the upstream `Pg.Client` before dynamically importing the CLI.
- Connection implementation inspected:
  `apps/cli/src/command-internal/legacy-db-connection.sql-pg.layer.ts`.
  Its migration batch calls `Connection.parse/bind/describe/execute/sync`
  directly; wrapping only `Client.query` would miss this path.

## Build Before PG Tests

Parent owns checkout, CI integration, and dispatch. Use a fresh disposable
upstream directory. With exact Bun/pnpm already installed, Linux x64 commands:

```sh
git clone --depth 1 --branch v2.117.0 https://github.com/supabase/cli.git "$UPSTREAM"
pnpm --dir "$UPSTREAM" install --filter 'supabase...' --frozen-lockfile --ignore-scripts --os linux --cpu x64 --libc glibc
python3 -B "$COMPONENT/prepare.py" --upstream "$UPSTREAM"
pnpm --dir "$UPSTREAM/apps/cli/cli_predispatch" install --frozen-lockfile --ignore-scripts
pnpm --dir "$COMPONENT" install --frozen-lockfile --ignore-scripts
node --test "$COMPONENT/test_hook.cjs" "$COMPONENT/test_policy.cjs"
python3 -B -m unittest discover -s "$COMPONENT" -p test_ci.py
python3 -B "$COMPONENT/smoke.py" --upstream "$UPSTREAM" --bun "$(command -v bun)" --receipt "$OUT/cli-predispatch-help.json"
export FMZ_CLI_PREDISPATCH_UPSTREAM="$UPSTREAM"
export FMZ_BUN="$(command -v bun)"
```

This is a source-entry build, not standalone compilation: the PG17 parser's
WASM file must remain next to its dependency. The previous base delivery's
Windows build and patched `db push --help` ran successfully; that does not prove
the new pending-history hook. Fresh preparation, Linux execution and real
PG17/TLS execution remain pending parent CI. Do not claim binary equivalence to
the original release archive.

## Parent Interface

Add this directory's source files (not node_modules) to candidate collection and
the parent's loaded-source checks. Load `ci.py` with a unique importlib spec name,
not `import ci`, then call `run(gate)` after the clean 47-migration app regressions
and outside any live Auth context. The existing candidate `cli_meter`,
`cli_stat_reader`, `native_runtime`, and `cli_isolation` imports must be available.

The entry requires canonical `gate.result['commit']`, matching optional `head`,
candidate SHA, clean47 marker, 45 canonical plus two app source-bound migration
files, existing `fmz-ci-ca.crt`, and the known disposable container. It copies
those 47 files unchanged into a new private work directory. A distinct configured
local port makes the explicit loopback `--db-url` take upstream's verify-full TLS
route; no hosted endpoint or JIT setting is supplied. The password travels only
in private child environment, never URL, arguments, receipt, or output.

`run(gate)` executes one empty `db push --db-url --dry-run --skip-vault`:

- 28 maximum prepaid SQL commands, no retry or reconnect; 5s connect/query,
  1s lock timeout, 45s CLI, 8KiB output.
- Eight separately counted numeric observer commands using existing
  `NativeRuntime.disposable`; utility tracking must be on and track must be all.
- Existing CI-only cron isolation is reused with its own receipt/profile:
  4 bootstrap SQL commands when already off, 8 when changed and restored.
  These are separate CI bootstrap, never charged to the hosted register.
- Equality between protocol SQL and numeric stats remains strict; same-role
  interference, reset, missing counters, nonzero temp, timeout, or uncertainty
  fails closed. This is not independent attribution of cluster-wide activity.

Receipts: `cli-predispatch.json`,
`cli-predispatch-cli-isolation-0.json`, plus the parent's prefixed bootstrap
command receipts. The journal is exported as safe structured events plus raw
journal SHA, not SQL or parameter bytes. `hosted_admission` is always false.

## Accounting Semantics And Limits

Before a simple Query or extended Execute reaches the existing transport, each
SQL command receives a durable fsync'd `unknown_consumed` row. Only a backend
CommandComplete confirms it; uncertain commands never receive a refund. A real
PG17 WASM parser counts statements, including quoted semicolons and DO bodies.
Migration policies bind file bytes, statement AST hashes, and the history
INSERT's version/name/statements values in memory. `policy.cjs` compiles such a
policy without any network connection or raw SQL export.

All frontend attempts are separately counted and durably recorded, including
SSLRequest, StartupMessage, authentication payload frames, Q/P/B/D/E/S/H/C/X.
Their contents are not logged. Parse/Bind/Sync frames are not falsely called
executed SQL. `frontend_write_returned_by_type` only means the driver write
returned; it is not a backend acknowledgement. The auxiliary 512-frame local
ceiling is not a new hosted allowance. COPY, cancel, raw-send bypass, unknown
SQL, policy/role/TLS mismatch, second connection, and dry-run mutation are denied.

The 64/28/28 policy roles are preserved; the migration role reserves one of its
64 commands for rollback. Observer credits stay separate. No 2349-wide admission
or budget replacement is implemented here.

The default CI probe does **not** execute a pending migration or modify the
47-row migration history. Do not infer hosted exact counts, historical cause, or
JIT behavior from this empty dry-run. There is no hosted adapter in this component.

## Existing Pending App Apply

`ci.py:run_pending(gate, args, expected_file)` replaces, rather than precedes,
one existing authorized app apply. The parent override is:

```python
def cli(self, *args, timeout=120):
    phase = self.result.get('phase')
    if args == ('migration', 'up', '--local') and phase in (
            'local_app_schema', 'local_app_outbox'):
        name = (app.M45 if phase == 'local_app_schema' else app.M46)
        expected = self.sources / '_offline/phase6e_server_v1/supabase/migrations' / name
        return cli_predispatch.run_pending(self, args, expected)
    return super().cli(*args, timeout=timeout)
```

Here `cli_predispatch` is the parent's uniquely loaded module. Do not additionally
call the old meter, cron-isolation wrapper, or base apply for that invocation.
No M48 is added. The old canonical M45 quota is never an allowed pending target.
The app's historical variable names M45/M46 refer to the files applied as schema
46 and outbox 47 after the canonical 45.

The adapter uses the same private PG17 stack with exact source-bound pending
bytes, 64 total SQL credits including one retained rollback credit, 8 observers,
and the unchanged 5s/45s/8KiB bounds. Existing cron-isolation bootstrap is counted
separately. The existing CLI history SELECT must report exactly the expected 45
or 46 versions before any migration SQL can dispatch. That check adds no query.
The final proof requires every authored statement in order and exactly one
source-bound history insert. Any additional/missing/already-applied version
fails closed before mutation, preventing an accidental reapply.

It appends exactly one old-profile-compatible receipt at `app_0` or `app_2` and
returns a CompletedProcess with raw output withheld. `arguments` denotes the
logical app-profile command; `execution_mode` and `executed_argument_shape`
explicitly identify source-instrumented db-url execution instead of pretending
the original binary/--local route ran. SQL digests are labelled PG17 AST hashes.
The actual upstream source/build proof is in `cli-predispatch-pending-N.json`.
No endchain/global capacity grant is added to the app receipt.

Additional artifacts are `cli-predispatch-pending-N-preregister.json`,
`cli-protocol-N.json`, and `pending-N-cli-predispatch-cli-isolation-0.json`.
`run(gate)` remains the separate final empty dry-run after all 47 migrations.
On numeric mismatch after confirmed migration execution, the receipt keeps
`actual_migration_execution:true` but `complete:false`; never retry the apply.

Run focused tests with the app folder on PYTHONPATH (automatic after integration):

```sh
PYTHONPATH="$SOURCES/_offline/phase6e_server_v1" python3 -B -m unittest discover -s "$COMPONENT" -p 'test_*.py'
node --test "$COMPONENT/test_hook.cjs" "$COMPONENT/test_policy.cjs"
```

The parent's existing hash-pinned admission_tools installation remains the tool
authority. This delta does not replace its Bun/pnpm artifacts or installer.
Actual pending-apply PG receipts remain pending parent CI; offline adapter tests
are not presented as actual database execution.

## Canonical M45 Apply

`run_canonical(gate, args, expected_file)` uses the same apply implementation as
`run_pending`. It requires `local_app`, exact phase `migration_45`, 44 already
applied canonical migrations, no app CLI receipts, and the unchanged canonical
file `supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql`, SHA256
`64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635`.
The existing history SELECT must match exactly the 44 prior source versions
before any mutation. The migration's historical UUIDs are not invoked as runs.

Parent wiring, replacing only the existing canonical apply inside its boundary:

```python
token = boundary.before(self)
result = self.instrumented_cli().run_canonical(
    self, args, self.sources / 'supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql')
boundary.after(self, token, result)
return result
```

Do not call the base apply as well. D must first add its strict instrumented-result
branch: the old `CompletedProcess`/release-binary argv/`serial + 1` contract does
not describe this execution. The fixed result is a dictionary containing only
`instrumented_receipt: "cli-predispatch-canonical-45.json"` and `sha256`, the hash
of that saved file. No legacy receipt or counter adjustment is synthesized.
The inherited rebuild caller ignores the return value and updates its applied
count only after this call returns; phase and migrations_applied stay unchanged
inside this helper and through the parent's after-hook.

The canonical receipt includes source/candidate/build binding, exact migration
hash, policy/history44, invocation ID, ledger events/terminal, numeric coverage,
tracking settings, eight observer commands, and an isolation-receipt reference
with its hash. It never appends to `gate.cli_protocol`, so app_0/1/2/3 remain free.
One process-local attempt plus existing artifact checks prevent reuse; unknown
execution failures retain all 64 reserved credits. SQL cap64 includes the one
rollback credit; query/connect5s, CLI45s and output8KiB remain unchanged.

New fixed artifacts are `cli-predispatch-canonical-45-preregister.json`,
`cli-predispatch-canonical-45.json` and
`canonical-45-cli-predispatch-cli-isolation-0.json`, plus original-byte sidecars
`cli-predispatch-canonical-45.ledger.txt` and
`cli-predispatch-canonical-45.policy.json`. Cron isolation contributes
4 or 8 separately counted bootstrap SQL/numbered receipts. Observer SQL stays
eight, not part of the CLI ledger. The old numbered canonical CLI receipt is
absent: relative to that one old receipt, this adds 8 or 12 artifact files.
These are disposable CI costs, not a changed hosted/global allowance.

The canonical receipt's `ledger_ref` and `policy_ref` each contain exactly
`path` (the direct basename) and `sha256` (the original bytes' hash), matching D's
explicit instrumented confirmation branch. No JSON re-encoding or sorting is
performed on either sidecar. The policy bytes are captured before dispatch and
checked unchanged after restoration. The ledger is copied after restoration,
including an original truncated final record on failure. Missing/oversize input
is reported, not reconstructed or truncated. Bounds are ledger262144,
policy16384 and canonical receipt524288 bytes. No raw SQL, URL or credential is
added: the source-bound hook emits only the existing safe metadata ledger.

Sidecars and the final receipt use exclusive creation, file fsync, and exact-byte
readback. A short write/hash mismatch/storage failure cannot produce a success
dictionary or a false reference. An existing execution failure remains primary;
durability failures are recorded secondarily (or attached as a safe exception
note when the final receipt cannot be persisted). Unknown execution still
consumes64, with no retry. The private originals and any partial copy remain
untouched for local diagnosis. This adds two files and zero SQL/processes.

Include `test_canonical.py` in the parent's candidate source inventory. The
integrated test finds source migrations in its candidate root. For an isolated
delivery, set `FMZ_CLI_TEST_SOURCE_ROOT` to the current source checkout and put
its `_offline/phase6e_server_v1` on `PYTHONPATH`. The unchanged test_ci.py also
expects the existing cli_stat_reader.py beside this component's directory.
Run `python3 -B -m unittest discover -s "$COMPONENT" -p 'test_*.py'`.
All new execution tests mock transport; no canonical CLI or DB invocation is
authorized by running these tests. Actual canonical numeric/frame evidence must
come from the parent's new source-bound CI. Hosted admission remains false.
