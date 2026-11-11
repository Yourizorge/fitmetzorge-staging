Public API: from case_stack_v1 import SOURCES, bootstrap
receipt = bootstrap(gate, canonical_migrations)

Matrix entry (NOT READY until D supplies the actual source-bound adapter):
  PYTHONPATH=_offline/phase6e11/endchain_v1 python3 -B -m case_stack_v1.ci
Reads CASE_NAME and the unchanged CANDIDATE_BLOB/CANDIDATE_SHA256/GITHUB_*.
Uses the existing Gate evidence directory fmz-db41-evidence per fresh runner.
Main names uploads per case; this entry never changes GITHUB_RUN_ID or resets.
Fixed integration module quota_candidate_v1.case_ci must export READY=True,
CASE_NAMES (exact tuple15 including normal), SOURCES (explicit tuplepaths) and
run(gate, migrations, case_name, *, bootstrap). D owns real before/after45 hooks,
quota prefix, Auth lifecycle, full phases, cleanup and case proof validation.
run returns status=CASE_PASS with case_name/source_commit/ci_run/candidate_sha256.
Missing/unready adapter stops before Gate construction/install. No fake PASS.
After fetch, the entry binds loaded adapter/entry and verifies all sources before
install. It does not call Gate.run/regressions or repeat the full app suite.
Even CASE_PASS requires Main's complete matrix plus same-source app aggregation;
full_chain_admission and hosted_admitted remain false in this individual entry.

Standalone bootstrap-only smoke entry (ONLY in Main's authorized fresh CI job):
  PYTHONPATH=_offline/phase6e11/endchain_v1 python3 -B -m case_stack_v1
It calls Gate.fetch/install and bootstrap, never Gate.run/regressions/advisors.
BOOTSTRAP_ONLY_PASS is not a case result or app/full-chain admission. For the
actual matrix, Main's entry must invoke the public function in-process and keep
the Gate for D's subsequent adapter; do not instantiate a second Gate afterward.

Optional actual M45 boundaries: bootstrap(gate, migrations, hooks=case_hooks,
run_id=case_uuid). A supplied case UUID must be canonical UUIDv4; standalone
bootstrap creates a fresh UUID. This is never the hosted owner authorization.
case_hooks must expose source-bound instance methods before45(snapshot) and
after45(snapshot); default None keeps the original Gate dispatcher unchanged.
The local rebuild view calls the existing migration_failure_boundaries.before
on the ACTUAL gate, then before45, then exactly one existing instrumented
run_canonical, then existing boundary.after, then after45. The preceding44
migrations use the separate local-only ci_prefix pre-dispatch profile. The
Gate.cli method/serial are never patched. Canonical migration bytes are retained.
Snapshots contain stage, source_commit, ci_run, candidate_sha256, observed
history_count and raw-hash evidence_refs, without SQL/credentials. They are
saved before callbacks. Callback exceptions immediately stop bootstrap and
remain the primary failure; no next migration, automatic retry or reset.
Callbacks must be in Main's explicit candidate inventory and pass bind_modules.
These are real canonical45 boundaries, NOT the appended quota-delta boundary;
the legacy boundary component's own narrow proof flags are not promoted.

Main integration:
- Add all SOURCES to the explicit candidate inventory before fetch.
- Use a NEW fresh-runner entry inheriting admission_ci.Gate without overriding cli.
- After actual fetch() and install(), invoke bootstrap(gate, migrations) instead
  of app.Gate.rebuild(). Never invoke the full Gate.run()/regressions() here.
- Keep the once-per-source full app CI mandatory and independently verified.
- One preregistered case per fresh GitHub runner/cluster; max-parallel 1.
  Keep actual GITHUB_RUN_ID unchanged. No retry/reset/reused claims.
- Main owns a case-specific artifact name/collector. Upload all incomplete
  receipts too. Never upload stack directories, secrets or database images.
- After bootstrap, D owns the newly appended local quota candidate and real
  case orchestration. This bootstrap never applies quota, creates a controller
  claim, starts Auth, executes a worker, or grants admission.

Reuses the existing exact canonical45 dispatcher and instrumented M45 receipt.
Then applies app46, actually executes the minimal empty dry-run, applies app47,
and executes the final empty dry-run. Existing local_app slots 0/1/2/3 remain
intact. No synthetic compatibility receipts or serial resets. Canonical bytes
and history remain unchanged.

Attestation:
- Exact container name and actual Docker ID; pinned image content ID/digest and
  PostgreSQL 17.6 server version.
- NativeRuntime.disposable only; postgres database/user, verify-full, existing
  5-second statement/connect and 1-second lock bounds; read-only metadata.
- Container/DB OID/CA unchanged across bootstrap; empty retained controller
  runs/steps/evidence after exact 47-entry history validation.
- System identifier uses existing disposable supabase_admin through a single
  read-only, 5-second bounded five-statement batch. No new privileges/grants.
- Receipt is PG-only: auth_database_bound=false. D/Main must obtain actual
  Auth container/target binding after their separate Auth startup.
- Full-chain strict WAL/temp0 requirements remain unchanged. These bootstrap
  metadata reads are NOT a new WAL diagnostic or a zero-WAL proof.

Accounting:
- Additional native metadata: 3 commands before, 4 after. Seven total on
  success, with each attempted command recorded before dispatch.
- Three additional history SELECTs use the existing Gate.rows bootstrap path.
- System identifier batch: five reserved commands, five confirmed only on
  success. A failed batch remains reserved; no refund/retry.
- Attempt receipt preregisters at most 15 additional helper SQL dispatches
  (7 native + 3 history + 5 admin); this excludes existing rebuild/CLI work.
- Before any helper SQL, exclusive fsync-backed attempt receipt prepays all15.
  Per-native-transaction exact command reservations include ROLLBACK before
  BEGIN; per-command intents precede dispatch. History and admin reservations
  are likewise persisted before transport. Unknown amounts stay prepaid.
  Lost BEGIN responses still attempt the prepaid ROLLBACK once. If rollback
  intent persistence fails, its already-durable exact reservation permits that
  safety suffix, but the persistence error prevents PASS. No refund or retry.
  Query/BEGIN errors retain precedence over rollback/close/runtime.clear errors;
  without an earlier error, the first cleanup error is raised after both cleanup
  operations were attempted. No SQL or credentials enter these receipts.
- Existing CLI, observer, cron-isolation, canonical setup and TLS receipts
  remain separate CI-bootstrap work, NOT debited/credited as case/hosted2349.
- Canonical1..44 now preserve per-invocation policy, append-only ledger,
  numeric-before/after, observer trace and cron-isolation originals. A durable
  case-stack-canonical-prefix.json is saved BEFORE either M45 fault callback;
  callbacks also receive its immutable reference. A separately prepaid catalog
  dispatch after40/before41 preserves its exact SQL hash and command receipt.
- The empty local migration ledger is provisioned once with8 native commands
  reserved (7 normal plus one rollback). Every intent precedes dispatch; a lost
  commit stays unknown. Provisioning does not register any migration version.
- Local prefix CLI reserves derive from each file's PG17 statement count plus16,
  with a separate frame/statement-size bound. Hosted-equivalent64/28 CLI slots,
  query timeouts and hosted2349 authority remain unchanged. Frozen1..44 contain
  1552 body statements; the sum of prefix CLI reserves is2256, EXCLUDING numeric
  observers, isolation, provisioning, driver/startup and later steps. This is not
  a full-run budget or a measured execution count.
- Exact bootstrap SQL total stays null until independent original-ledger replay,
  numeric reconciliation AND native driver/startup accounting are complete.
  original_refs_complete never implies independent_numeric_validation or PASS.
- Setup isolation/runner disposal never substitutes for measured case cleanup.

Local tests (no DB, CLI, Auth, browser or container execution):
  FMZ_CASE_STACK_SOURCE=<main-repository-root>
  python -B -m unittest discover -s <case_stack_v1-directory> -p test_bootstrap.py -v
This environment variable is ONLY a test dependency source root, never runtime
target authorization. Tests use the actual ci_profile and source_commit rules,
with fake driver/Gate transport. Real PG execution remains pending parent CI.
On restricted Windows sandboxes, set TEMP and TMP to a short writable workspace
directory for test fixtures; no application runtime setting is changed.
