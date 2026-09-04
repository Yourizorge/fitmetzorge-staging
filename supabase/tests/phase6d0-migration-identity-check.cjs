const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { execFileSync } = require("node:child_process");

const project = "mokxyyullfhkfalopbzd";
const version = "20260904105918";
const name = "phase6d0_legacy_authorization_gate";
const expectedHash = "5b91b22f823a30f86e329b381fe797fd28655d237ad977d6b80d2c99af5485b3";
const filename = version + "_" + name + ".sql";
const sha = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const query = `select jsonb_build_object(
 'history',(select jsonb_agg(jsonb_build_object('version',version,'name',name,
   'statement_count',cardinality(statements),
   'sha256',encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex'))
   order by version) from supabase_migrations.schema_migrations),
 'functions',(select jsonb_agg(jsonb_build_object('name',p.proname,'body',p.prosrc,
   'security_definer',p.prosecdef,'config',p.proconfig) order by p.proname)
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and (p.proname like 'fmz_phase6d0_%' or p.proname in (
   'fmz_bootstrap_trainer_profile','accept_client_invite','fmz_handle_new_auth_user',
   'fmz_current_profile_role','fmz_current_profile_trainer_id','fmz_is_trainer',
   'fmz_can_select_profile','fmz_can_access_workspace')))
 ) as identity_snapshot;`;

function audit(files, snapshot) {
 const history = snapshot.history || [], functions = snapshot.functions || [];
 const local = files.map(file => {
  const match = /^(\d+)_(.+)\.sql$/.exec(file.filename);
  if (!match) throw new Error("invalid_migration_filename");
  return { ...file, version: match[1], name: match[2] };
 });
 const candidates = local.filter(file => file.name === name);
 const live = history.filter(row => row.name === name);
 const file = candidates[0];
 const bodyChecks = file ? [...file.bytes.toString("utf8").matchAll(
  /create or replace function public\.(\w+)\([\s\S]*?\bas \$fn\$([\s\S]*?)\$fn\$;/g
 )].map(match => ({
  name: match[1],
  pass: functions.filter(f => f.name === match[1]).length === 1 &&
   functions.find(f => f.name === match[1])?.body === match[2]
 })) : [];
 const checks = {
  one_canonical_git_file: candidates.length === 1 && file.filename === filename,
  no_obsolete_git_version: !local.some(f => f.version === "20260904093300"),
  git_bytes_exact: !!file && sha(file.bytes) === expectedHash,
  one_canonical_live_record: live.length === 1 && live[0].version === version,
  no_obsolete_live_version: !history.some(row => row.version === "20260904093300"),
  live_bytes_exact: live.length === 1 && live[0].statement_count === 1 && live[0].sha256 === expectedHash,
  eight_function_bodies_exact: bodyChecks.length === 8 && bodyChecks.every(c => c.pass),
  thirteen_safe_functions: functions.length === 13 && functions.every(f =>
   f.security_definer === true && f.config?.includes("search_path=pg_catalog, pg_temp"))
 };
 const localOnly = local.filter(f => !history.some(h => h.version === f.version))
  .map(f => ({ filename: f.filename, matching_name_live_version: history.find(h => h.name === f.name)?.version || null }));
 const remoteOnly = history.filter(h => !local.some(f => f.version === h.version))
  .map(h => ({ version: h.version, name: h.name }));
 const duplicateVersions = [...new Set(local.map(f => f.version))]
  .filter(v => local.filter(f => f.version === v).length > 1);
 const packagePass = Object.values(checks).every(Boolean);
 const historyPass = !localOnly.length && !remoteOnly.length && !duplicateVersions.length;
 return {
  target: project, canonical_version: version, migration_sha256: file ? sha(file.bytes) : null,
  package_identity_pass: packagePass, checks, function_body_checks: bodyChecks,
  full_history_synchronized: historyPass, broad_db_push_allowed: packagePass && historyPass,
  local_only: localOnly, remote_only: remoteOnly, duplicate_local_versions: duplicateVersions,
  database_changed: false
 };
}

if (require.main === module) {
 try {
  // Fixed SELECT only; this command cannot repair history or apply a migration.
  if (process.argv.slice(2).some(arg => !["--live", "--package-only"].includes(arg)) ||
      !process.argv.includes("--live")) throw new Error("use_live_read_only_mode");
  if (!process.env.FMZ_PYTHON) throw new Error("FMZ_PYTHON_required");
  const result = JSON.parse(execFileSync(process.env.FMZ_PYTHON,
   [path.join(__dirname, "phase6d0-staging-query.py")],
   { input: query, encoding: "utf8", windowsHide: true, timeout: 60000, maxBuffer: 1000000 }));
  if (!result.ok || result.rows?.length !== 1) throw new Error("read_only_snapshot_failed");
  const dir = path.resolve(__dirname, "../migrations");
  const files = fs.readdirSync(dir).filter(f => f.endsWith(".sql"))
   .map(filename => ({ filename, bytes: fs.readFileSync(path.join(dir, filename)) }));
  const report = audit(files, result.rows[0].identity_snapshot);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = report.package_identity_pass &&
   (process.argv.includes("--package-only") || report.full_history_synchronized) ? 0 : 2;
 } catch {
  console.error("migration_identity_check_failed");
  process.exitCode = 1;
 }
}
module.exports = { audit, query, filename, expectedHash };
