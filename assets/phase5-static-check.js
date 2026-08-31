const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const files = {
  runtime: fs.readFileSync(path.join(root, "assets/phase5-progress.js"), "utf8"),
  memberUx: fs.readFileSync(path.join(root, "assets/member-ux-consistency.js"), "utf8"),
  app: fs.readFileSync(path.join(root, "app.js"), "utf8"),
  index: fs.readFileSync(path.join(root, "index.html"), "utf8"),
  bundle: fs.readFileSync(path.join(root, "app.bundle.js"), "utf8"),
  phase1: fs.readFileSync(path.join(root, "assets/phase1-foundation.js"), "utf8"),
  phase2: fs.readFileSync(path.join(root, "assets/phase2-home-recovery.js"), "utf8"),
  phase3: fs.readFileSync(path.join(root, "assets/phase3-training-engine.js"), "utf8"),
  phase4Slice2: fs.readFileSync(path.join(root, "assets/phase4-nutrition-slice2.js"), "utf8"),
  phase4Slice3: fs.readFileSync(path.join(root, "assets/phase4-nutrition-slice3.js"), "utf8"),
  migration: fs.readFileSync(path.join(root, "supabase/migrations/20260831153000_phase5_progress_foundation.sql"), "utf8"),
  units: fs.readFileSync(path.join(root, "supabase/migrations/20260831161000_phase5_progress_unit_preference.sql"), "utf8"),
  revisionIndexes: fs.readFileSync(path.join(root, "supabase/migrations/20260831163000_phase5_progress_revision_indexes.sql"), "utf8"),
  verifier: fs.readFileSync(path.join(root, "supabase/verification/20260831153000_phase5_progress_foundation_verification.sql"), "utf8"),
  e2e: fs.readFileSync(path.join(root, "supabase/tests/20260831_phase5_progress_transactional_e2e.sql"), "utf8"),
  agents: fs.readFileSync(path.join(root, "AGENTS.md"), "utf8"),
  master: fs.readFileSync(path.join(root, "docs/MASTER_BUILD_PLAN.md"), "utf8"),
  architecture: fs.readFileSync(path.join(root, "docs/PHASE5_PROGRESS_ARCHITECTURE.md"), "utf8")
};

const checks = [];
function check(name, condition) { checks.push({ name, pass: Boolean(condition) }); }
function includesAll(source, values) { return values.every((value) => source.includes(value)); }

check("runtime duplicate guard", files.runtime.includes("FMZ_PHASE5_PROGRESS_LOADED"));
check("runtime version", files.runtime.includes('20260831-phase5-progress1'));
check("app cache version", files.app.includes('assets/phase5-progress.js?v=20260831-phase5-progress1'));
check("index cache version", files.index.includes('app.js?v=20260831-phase5-progress1'));
check("loader after Member UX", files.app.indexOf("memberUxPatchSource") < files.app.indexOf("phase5ProgressPatchSource"));
check("loader before init", files.app.indexOf("phase5ProgressPatchSource}\\ninit();") > -1);
let combinedBundleParse = false;
try {
  const patches = [files.phase1, files.phase2, files.phase3, files.phase4Slice2, files.phase4Slice3, files.memberUx, files.runtime];
  const combined = files.bundle.replace("\ninit();", `\n${patches.join("\n")}\ninit();`);
  new vm.Script(combined, { filename: "phase5-combined-browser-bundle.js" });
  combinedBundleParse = true;
} catch (_error) {
  combinedBundleParse = false;
}
check("combined seven-patch bundle parses", combinedBundleParse);
check("client Progress nav", includesAll(files.runtime, ['["progress", phase5Text("nav")]', "phase5EnsureNav"]));
check("legacy tracker route exception", files.memberUx.includes('id === "progress" && window.FMZ_PHASE5_PROGRESS'));
check("legacy Progress renderer delegates", files.memberUx.includes('window.FMZ_PHASE5_PROGRESS.render()'));
check("tracker card routes to Progress", files.memberUx.includes('data-member-open-view="progress"'));
check("trainer legacy fallback preserved", files.runtime.includes("phase5OriginalRenderProgress()"));

check("dashboard RPC", files.runtime.includes('fmz_phase5_get_progress_dashboard'));
check("timezone RPC", files.runtime.includes('fmz_phase5_set_progress_timezone'));
check("unit RPC", files.runtime.includes('fmz_phase5_set_unit_system'));
check("goal save RPC", files.runtime.includes('fmz_phase5_save_progress_goal'));
check("weight save RPC", files.runtime.includes('fmz_phase5_save_weight_log'));
check("measurement save RPC", files.runtime.includes('fmz_phase5_save_body_measurement'));
check("archive RPCs", includesAll(files.runtime, ['fmz_phase5_archive_weight_log','fmz_phase5_archive_body_measurement']));
check("request identity retained", files.runtime.includes("form.dataset.requestId || phase5Uuid()"));
check("changed draft rotates request", files.runtime.includes('form.dataset.requestId = ""'));
check("stale conflict handled", files.runtime.includes("progress_stale_conflict"));
check("authoritative refresh after writes", files.runtime.includes("await phase5Hydrate({ force: true })"));

check("canonical kg", files.runtime.includes('weight: "kg"'));
check("canonical cm", files.runtime.includes('length: "cm"'));
check("kg to lb conversion", files.runtime.includes("KG_TO_LB"));
check("cm to inch conversion", files.runtime.includes("CM_TO_IN"));
check("Free 30-day contract", files.runtime.includes("freeHistoryDays: 30"));
check("metric and imperial controls", includesAll(files.runtime, ['data-phase5-unit="metric"','data-phase5-unit="imperial"']));
check("IANA browser timezone", files.runtime.includes("resolvedOptions().timeZone"));
check("local calendar date", files.runtime.includes('new Intl.DateTimeFormat("en-CA"'));

check("goal first", files.runtime.indexOf("phase5GoalCard()") < files.runtime.indexOf("phase5WeightCard()"));
check("raw and smoothed chart", includesAll(files.runtime, ['class="raw"','class="trend"','7-entry trend']));
check("accessible chart", files.runtime.includes('role="img" aria-label='));
check("accessible table alternative", includesAll(files.runtime, ['phase5-table','phase5-details']));
check("strength from server payload", files.runtime.includes("estimated_one_rep_max_kg"));
check("consistency surface", includesAll(files.runtime, ["last_7_days","last_30_days"]));
check("truthful running state", files.runtime.includes("runningUnavailable"));
check("BMI contextual disclaimer", files.runtime.includes("bmiDisclaimer"));
check("photo runtime disabled", files.runtime.includes("photosEnabled: false"));
check("no Phase 5 file input", !files.runtime.includes('type="file"'));
check("photo privacy gate copy", files.runtime.includes("photosGate"));

check("NL copy", files.runtime.includes("Je ontwikkeling in een rustig overzicht"));
check("EN copy", files.runtime.includes("Your development in a calm overview"));
check("DE copy", files.runtime.includes("Deine Entwicklung in einer ruhigen Uebersicht"));
check("locale-aware numbers", files.runtime.includes("new Intl.NumberFormat"));
check("locale-aware dates", files.runtime.includes("toLocaleDateString"));
check("mobile 390 compatible CSS", files.runtime.includes("grid-template-columns: 1fr"));
check("narrow 359 fallback", files.runtime.includes("@media (max-width: 359px)"));
check("tablet breakpoint", files.runtime.includes("@media (min-width: 760px)"));
check("safe area padding", files.runtime.includes("env(safe-area-inset-bottom)"));
check("minimum controls", files.runtime.includes("min-height: 44px"));
check("modal semantics", includesAll(files.runtime, ['role="dialog"','aria-modal="true"','aria-labelledby="phase5-modal-title"']));
check("Escape close", files.runtime.includes('event.key === "Escape"'));
check("focus restoration", files.runtime.includes("opener?.focus?.()"));

check("four migration tables", includesAll(files.migration, [
  "create table if not exists public.progress_preferences",
  "create table if not exists public.progress_goals",
  "create table if not exists public.weight_logs",
  "create table if not exists public.body_measurements"
]));
check("RLS all four", (files.migration.match(/enable row level security/g) || []).length === 4);
check("no DELETE policy", !/create policy[^;]+for delete/is.test(files.migration));
check("no trainer policy", !/create policy[^;]+trainer/is.test(files.migration));
check("no authenticated table grants", !/grant\s+.+\s+on\s+table\s+.+\s+to\s+authenticated/i.test(files.migration));
check("auth uid ownership", (files.migration.match(/auth\.uid\(\)/g) || []).length >= 15);
check("advisory locks", (files.migration.match(/pg_advisory_xact_lock/g) || []).length === 3);
check("revision status", includesAll(files.migration, ["supersedes_weight_log_id","supersedes_body_measurement_id","status = 'superseded'"]));
check("no destructive table SQL", !/\b(drop|truncate|delete)\s+(table|from)\b/i.test(files.migration));
check("current entitlements", includesAll(files.migration, ["'pro', 'ai', 'personal_coaching'","e.status = 'active'","e.starts_at <= now()","e.ends_at is null or e.ends_at > now()"]));
check("Free server history", includesAll(files.migration, ["v_today - 29","progress_history_locked"]));
check("unit preference allowlist", includesAll(files.units, ["metric", "imperial", "user_settings"]));
check("revision foreign keys indexed", includesAll(files.revisionIndexes, ["weight_logs_supersedes_idx", "body_measurements_supersedes_idx", "where supersedes_weight_log_id is not null", "where supersedes_body_measurement_id is not null"]));
check("internal functions revoked", files.migration.includes("fmz_phase5_has_full_progress_access(uuid) from public, anon, authenticated"));
check("only eight member RPC grants", (files.migration.match(/grant execute on function/g) || []).length + (files.units.match(/grant execute on function/g) || []).length === 8);

check("verifier SELECT CTE", /^with\s/i.test(files.verifier.trim()) && /select verification_result from result;\s*$/i.test(files.verifier.trim()));
check("verifier no mutation statements", !/\b(insert|update|delete|alter|create|drop|truncate|grant|revoke|call)\b\s+(into|table|policy|function|on|from)?/i.test(files.verifier.replace(/'[^']*'/g, "''")));
check("verifier overall pass", files.verifier.includes("'overall_pass', bool_and(pass)"));
check("transactional E2E rollback", includesAll(files.e2e, ["begin;","rollback;","fixtures_persisted","cross-member isolation failed"]));

check("staging autonomy recorded", includesAll(files.agents, ["mokxyyullfhkfalopbzd","Yourizorge/fitmetzorge-staging","Permanent Staging Autonomy"]));
check("production lock recorded", includesAll(files.agents, ["hgoygcviutmynaihcvpd","Production Lock"]));
check("strategic pricing recorded", includesAll(files.master, ["EUR 9.99 monthly","EUR 19.99 monthly","30 days without payment details"]));
check("international roadmap recorded", includesAll(files.master, ["Belgium/Germany","French and Italian"]));
check("photo gate documented", includesAll(files.architecture, ["private bucket","signed access","AI-analysis opt-in"]));
check("no service role frontend", !/service[_-]?role/i.test(files.runtime));
check("no production ref frontend", !files.runtime.includes("hgoygcviutmynaihcvpd"));
check("no AI call", !/(openai|anthropic|gemini|chat\/completions|responses\/v1)/i.test(files.runtime));
check("no MutationObserver", !files.runtime.includes("MutationObserver"));
check("no polling", !/setInterval\s*\(/.test(files.runtime));
check("no reload workaround", !/location\.reload\s*\(/.test(files.runtime));

const failed = checks.filter((item) => !item.pass);
console.log(JSON.stringify({ scope: "phase5_progress_static", pass_count: checks.length - failed.length, fail_count: failed.length, overall_pass: failed.length === 0, failed }, null, 2));
if (failed.length) process.exit(1);
