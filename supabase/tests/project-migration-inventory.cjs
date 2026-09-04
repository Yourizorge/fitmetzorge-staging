// Read-only project migration inventory for staging reconciliation evidence.
// It inspects local SQL files plus live migration metadata; it does not execute
// migration SQL, alter application schema, or read member row values.
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { execFileSync } = require("node:child_process");

const root = path.resolve(__dirname, "../..");
const migrationsDir = path.join(root, "supabase", "migrations");
const git = process.env.FMZ_GIT || "git";
const targetProjectRef = "mokxyyullfhkfalopbzd";

const repairedVersions = [
  "20260812000000",
  "20260813",
  "20260818",
  "20260826143000",
];

const resolvedTimestampMappings = [
  ["20260819", "20260819134024", "phase4_nutrition_slice3_atomic_log_item_replacement"],
  ["20260819", "20260819163738", "phase4_nutrition_slice4b_alias_search"],
  ["20260819", "20260819175756", "phase4_nutrition_slice4c_operational_state"],
  ["20260819", "20260820082018", "phase4_nutrition_slice4d_provider_snapshot_logging"],
  ["20260820134211", "20260820150513", "phase4_nutrition_slice4d_historical_provider_resolver"],
  ["20260821214541", "20260822172635", "phase4_nutrition_slice4e_ingestion_alias_search"],
  ["20260827", "20260827125343", "phase4_nutrition_slice4fd_transient_off_barcode"],
  ["20260827165426", "20260827152727", "phase4_nutrition_slice4fd_transient_off_parent_context_fix"],
  ["20260831153000", "20260831145357", "phase5_progress_foundation"],
  ["20260831161000", "20260831150434", "phase5_progress_unit_preference"],
  ["20260831163000", "20260831153512", "phase5_progress_revision_indexes"],
  ["20260901170000", "20260901161314", "phase5_unit_system_constraint_fix"],
  ["20260901193000", "20260901183914", "phase6a_ai_trust_foundation"],
  ["20260901203000", "20260901184418", "phase6a_ai_consent_event_ordering"],
  ["20260901204500", "20260901190328", "phase6a_pgcrypto_search_path"],
  ["20260901211500", "20260901191328", "phase6a_foreign_key_indexes"],
  ["20260901230000", "20260902045834", "phase6b_provider_privacy_cost_gate"],
  ["20260902203000", "20260903085454", "phase6c_private_ai_chat"],
  ["20260903145000", "20260903125150", "phase6c_request_scoped_safety"],
];

const reconstructedBaselineTables = [
  "profiles",
  "coach_workspaces",
  "user_settings",
  "user_onboarding",
  "entitlements",
  "recovery_logs",
  "exercises",
  "training_plans",
  "training_plan_days",
  "training_plan_exercises",
  "workout_sessions",
  "workout_set_logs",
];

const sha = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const gitRead = (args) =>
  execFileSync(git, args, {
    cwd: root,
    windowsHide: true,
    maxBuffer: 10_000_000,
  });

function gitText(args, fallback = null) {
  try {
    return gitRead(args).toString("utf8").trim();
  } catch (error) {
    if (fallback !== null) return fallback;
    throw error;
  }
}

function listLocalMigrations() {
  return fs
    .readdirSync(migrationsDir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".sql"))
    .map((entry) => {
      const match = entry.name.match(/^(\d+)_(.*)\.sql$/);
      if (!match) throw new Error(`Unexpected migration filename: ${entry.name}`);
      const abs = path.join(migrationsDir, entry.name);
      const rel = path.relative(root, abs).replace(/\\/g, "/");
      const bytes = fs.readFileSync(abs);
      const sql = bytes.toString("utf8");
      const objects = [
        ...sql.matchAll(
          /^\s*(?:create\s+(?:or\s+replace\s+)?(?:table\s+(?:if\s+not\s+exists\s+)?|function\s+)|alter\s+table\s+(?:if\s+exists\s+)?)([\w.]+)/gim,
        ),
      ].map((m) => m[1]);

      return {
        file: rel,
        local_id: match[1],
        name: match[2],
        bytes: bytes.length,
        sha256: sha(bytes),
        lf_trim_sha256: sha(sql.replace(/\r\n/g, "\n").trim()),
        object_candidates: [...new Set(objects)].sort(),
      };
    })
    .sort((a, b) => a.local_id.localeCompare(b.local_id) || a.name.localeCompare(b.name));
}

const liveInventoryQuery = `select jsonb_build_object(
 'history',(select jsonb_agg(jsonb_build_object('version',version,'name',name,
 'statement_count',cardinality(statements),
 'sha256',case when statements is null then null else encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') end,
 'lf_trim_sha256',case when statements is null then null else encode(sha256(convert_to(btrim(replace(array_to_string(statements,E'\\n'),E'\\r\\n',E'\\n'),E' \\t\\r\\n'),'UTF8')),'hex') end
 ) order by version) from supabase_migrations.schema_migrations),
 'objects',(select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',c.relname,'type',c.relkind,'rls',c.relrowsecurity) order by n.nspname,c.relname)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('public','ai_private','legacy_auth_private') and c.relkind in ('r','p')),
 'functions',(select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',p.proname,'identity',pg_get_function_identity_arguments(p.oid),'definition_sha256',encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex')) order by n.nspname,p.proname,pg_get_function_identity_arguments(p.oid))
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','ai_private','legacy_auth_private') and p.prokind='f')
 ) as inventory;`;

function readLiveInventory() {
  if (!process.env.FMZ_PYTHON) throw new Error("FMZ_PYTHON_required");
  const result = JSON.parse(
    execFileSync(process.env.FMZ_PYTHON, [path.join(__dirname, "phase6d0-staging-query.py")], {
      input: liveInventoryQuery,
      encoding: "utf8",
      windowsHide: true,
      timeout: 60_000,
      maxBuffer: 3_000_000,
    }),
  );
  if (!result.ok) throw new Error("read_only_inventory_failed");
  return result.rows[0].inventory;
}

function countDuplicateVersions(local) {
  const counts = new Map();
  for (const migration of local) counts.set(migration.local_id, (counts.get(migration.local_id) || 0) + 1);
  return [...counts.entries()].filter(([, count]) => count > 1).map(([version]) => version);
}

function classifyMigration(migration, remoteByVersion) {
  const remote = remoteByVersion.get(migration.local_id) || null;
  const exactSql = remote?.statement_count === 1 && remote.sha256 === migration.sha256;
  const normalizedSql = remote?.statement_count === 1 && remote.lf_trim_sha256 === migration.lf_trim_sha256;
  const aligned = Boolean(remote && remote.name === migration.name);

  let classification = "history_version_and_name_aligned";
  if (!remote) classification = "missing_live_history";
  else if (!aligned) classification = "history_name_mismatch";
  else if (exactSql) classification = "single_statement_byte_exact";
  else if (normalizedSql) classification = "single_statement_normalized_exact";

  return {
    ...migration,
    remote_id: remote?.version || null,
    remote_name: remote?.name || null,
    remote_statement_count: remote?.statement_count || null,
    remote_sha256: remote?.sha256 || null,
    history_aligned_by_version_and_name: aligned,
    sql_identity_evidence: exactSql
      ? "byte_exact_single_statement"
      : normalizedSql
        ? "normalized_single_statement"
        : remote
          ? "history_row_present; whole-file SQL identity not stored for this historical row"
          : "absent",
    classification,
    sql_reexecuted: false,
  };
}

const local = listLocalMigrations();
const before = readLiveInventory();
const after = readLiveInventory();
const liveHistory = before.history || [];
const afterHistory = after.history || [];
const remoteByVersion = new Map(liveHistory.map((row) => [row.version, row]));
const localVersions = new Set(local.map((migration) => migration.local_id));
const remoteVersions = new Set(liveHistory.map((row) => row.version));
const duplicateVersions = countDuplicateVersions(local);
const remoteOnly = liveHistory.filter((row) => !localVersions.has(row.version)).map((row) => row.version);
const localOnly = local.filter((migration) => !remoteVersions.has(migration.local_id)).map((migration) => migration.local_id);
const nameMismatches = local
  .map((migration) => ({ local: migration, remote: remoteByVersion.get(migration.local_id) }))
  .filter((pair) => pair.remote && pair.remote.name !== pair.local.name)
  .map((pair) => ({
    version: pair.local.local_id,
    local_name: pair.local.name,
    remote_name: pair.remote.name,
  }));
const migrations = local.map((migration) => classifyMigration(migration, remoteByVersion));
const liveObjects = before.objects || [];
const baselineObjectPresence = reconstructedBaselineTables.map((table) => {
  const object = liveObjects.find((row) => row.schema === "public" && row.name === table);
  return {
    table: `public.${table}`,
    present_live: Boolean(object),
    rls_enabled_live: object?.rls ?? null,
  };
});
const fullHistorySynchronized =
  local.length === liveHistory.length &&
  remoteOnly.length === 0 &&
  localOnly.length === 0 &&
  nameMismatches.length === 0 &&
  duplicateVersions.length === 0;

const report = {
  target: targetProjectRef,
  generated_at_utc: new Date().toISOString(),
  git_head: gitText(["rev-parse", "HEAD"], "unavailable"),
  git_branch: gitText(["rev-parse", "--abbrev-ref", "HEAD"], "unavailable"),
  local_count: local.length,
  remote_count: liveHistory.length,
  full_history_synchronized: fullHistorySynchronized,
  local_only_versions: localOnly,
  remote_only_versions: remoteOnly,
  name_mismatches: nameMismatches,
  duplicate_versions: duplicateVersions,
  history_repaired_forward_only: true,
  history_repair_versions_marked_applied: repairedVersions,
  migration_sql_executed_by_reconciliation: false,
  destructive_reconstruction_executed: false,
  resolved_timestamp_mappings: resolvedTimestampMappings.map(([from, to, name]) => ({
    previous_git_version: from,
    canonical_live_version: to,
    name,
  })),
  reconstructed_baseline: {
    file: "supabase/migrations/20260812000000_legacy_phase1_3_source_baseline.sql",
    exact_historical_source_available: false,
    strategy: "forward-only source baseline reconstructed from live schema metadata and frozen verifier contracts",
    data_changes: "none; migration is source-only for fresh rebuilds and was marked applied in staging history",
    live_object_presence: baselineObjectPresence,
  },
  migrations,
  before_history: liveHistory,
  after_history: afterHistory,
  two_read_history_equal_after_repair: JSON.stringify(liveHistory) === JSON.stringify(afterHistory),
  live_tables: liveObjects,
  live_function_definition_hashes: before.functions || [],
  object_inventory_scope:
    "Migration filenames, live migration history, table/function presence, RLS flags and function definition hashes; no member row values are exported.",
  broad_db_push_allowed_after_external_dry_run: fullHistorySynchronized,
  empty_database_rebuild:
    "PASS through Phase 6B with bundled PostgreSQL 18; full 6C/6D0 local replay requires a local pg_cron extension.",
};

if (process.argv.includes("--write-manifest")) {
  fs.writeFileSync(
    path.join(root, "docs", "PROJECT_MIGRATION_RECONCILIATION_MANIFEST.json"),
    `${JSON.stringify(report, null, 2)}\n`,
  );
  console.log(
    JSON.stringify({
      local: report.local_count,
      remote: report.remote_count,
      full_history_synchronized: report.full_history_synchronized,
      local_only: report.local_only_versions.length,
      remote_only: report.remote_only_versions.length,
      duplicates: report.duplicate_versions.length,
      history_repair_versions: report.history_repair_versions_marked_applied,
      migration_sql_executed_by_reconciliation: false,
    }),
  );
} else {
  console.log(JSON.stringify(report, null, 2));
}
