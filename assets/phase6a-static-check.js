const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");
const files = {
  migration: read("supabase/migrations/20260901193000_phase6a_ai_trust_foundation.sql"),
  consentOrdering: read("supabase/migrations/20260901203000_phase6a_ai_consent_event_ordering.sql"),
  pgcryptoPath: read("supabase/migrations/20260901204500_phase6a_pgcrypto_search_path.sql"),
  fkIndexes: read("supabase/migrations/20260901211500_phase6a_foreign_key_indexes.sql"),
  verifier: read("supabase/verification/20260901193000_phase6a_ai_trust_foundation_verification.sql"),
  e2e: read("supabase/tests/20260901193000_phase6a_ai_trust_transactional_e2e.sql"),
  contracts: read("supabase/functions/youri-ai/contracts.ts"),
  mock: read("supabase/functions/youri-ai/mock-adapter.ts"),
  handler: read("supabase/functions/youri-ai/handler.ts"),
  index: read("supabase/functions/youri-ai/index.ts"),
  readme: read("supabase/functions/youri-ai/README.md"),
  master: read("docs/MASTER_BUILD_PLAN.md"),
  status: read("docs/BUILD_STATUS.md"),
  architecture: read("docs/PHASE6_AI_CORE_ARCHITECTURE_READINESS.md"),
  package: read("docs/PHASE6A_AI_TRUST_FOUNDATION.md"),
  testMatrix: read("docs/TEST_MATRIX.md"),
  agents: read("AGENTS.md"),
};

const checks = [];
function check(name, condition) { checks.push({ name, pass: Boolean(condition) }); }
function hasAll(source, values) { return values.every((value) => source.includes(value)); }

check("migration transaction", /^--[\s\S]*\nbegin;/.test(files.migration) && /\ncommit;\s*$/.test(files.migration));
check("migration one transaction", (files.migration.match(/\nbegin;/g) || []).length === 1 && (files.migration.match(/\ncommit;/g) || []).length === 1);
check("eight public tables", [
  "ai_consent_events", "ai_threads", "ai_messages", "ai_context_manifests",
  "ai_action_proposals", "ai_action_decisions", "ai_member_safety_state",
  "ai_data_lifecycle_requests",
].every((name) => files.migration.includes(`create table if not exists public.${name}`)));
check("twelve private tables", [
  "consent_documents", "feature_flags", "budget_policies", "rate_policies",
  "action_policies", "structured_schemas", "runs", "budget_accounts",
  "usage_ledger", "rate_buckets", "safety_events", "audit_events",
].every((name) => files.migration.includes(`create table if not exists ai_private.${name}`)));
check("public RLS count", (files.migration.match(/alter table public\.ai_[a-z_]+ enable row level security;/g) || []).length === 8);
check("private RLS count", (files.migration.match(/alter table ai_private\.[a-z_]+ enable row level security;/g) || []).length === 12);
check("eight own select policies", (files.migration.match(/create policy ai_[a-z_]+_select_own/g) || []).length === 8);
check("no write policy", !/create policy[\s\S]{0,180}for\s+(insert|update|delete)/i.test(files.migration));
check("no trainer policy", !/create policy[^;]+trainer/is.test(files.migration));
check("all public tables revoked", (files.migration.match(/revoke all on table public\.ai_/g) || []).length === 8);
check("private schema revoked", hasAll(files.migration, [
  "revoke all on schema ai_private from public, anon, authenticated",
  "revoke all on all tables in schema ai_private from public, anon, authenticated",
]));
check("relational owner FKs", hasAll(files.migration, [
  "ai_messages_thread_owner_fk", "ai_action_proposals_context_owner_fk",
  "ai_action_decisions_proposal_owner_fk", "ai_runs_thread_owner_fk", "ai_runs_context_owner_fk",
]));
check("profile ownership", (files.migration.match(/references public\.profiles\(id\)/g) || []).length >= 14);
check("idempotency uniqueness", hasAll(files.migration, [
  "ai_consent_events_user_request_unique", "ai_messages_request_role_unique",
  "ai_action_decisions_user_request_unique", "ai_data_lifecycle_requests_user_request_unique",
  "ai_runs_user_request_unique",
]));
check("idempotent replay equality", hasAll(files.migration + files.e2e, [
  "ai_run_request_conflict", "response_hash", "ai_run_completion_conflict",
  "run replay conflict was accepted", "completion replay conflict was accepted",
]));
check("advisory locks", (files.migration.match(/pg_advisory_xact_lock/g) || []).length >= 8);
check("consent separate", hasAll(files.migration, ["ai_processing", "trainer_summary_sharing", "explicit_confirmation is true"]));
check("consent monotonic ordering", hasAll(files.consentOrdering, [
  "event_sequence bigint generated always as identity",
  "ai_consent_events_event_sequence_idx",
  "order by e.event_sequence desc",
]));
check("pgcrypto fixed search path", hasAll(files.pgcryptoPath, [
  "fmz_phase6a_get_context_manifest",
  "fmz_phase6a_service_begin_run",
  "fmz_phase6a_service_complete_run",
  "set search_path = pg_catalog, extensions, public, ai_private, pg_temp",
]));
check("foreign keys indexed", [
  "ai_messages_thread_owner_idx",
  "ai_action_proposals_context_owner_idx",
  "ai_action_decisions_proposal_owner_idx",
  "ai_runs_thread_owner_idx",
  "ai_runs_context_owner_idx",
  "ai_budget_accounts_policy_idx",
  "ai_safety_events_run_idx",
  "ai_audit_events_run_idx",
].every((name) => files.fkIndexes.includes(name)));
check("consent categories", hasAll(files.migration, [
  "'profile'", "'onboarding'", "'goals'", "'training'", "'nutrition'", "'recovery'",
  "'sleep'", "'activity'", "'progress'", "'workout_performance'", "'health_limitations'",
]));
check("consent locale NL EN DE", (files.migration.match(/phase6a-ai-processing-v1'/g) || []).length >= 3 && (files.migration.match(/phase6a-trainer-summary-v1'/g) || []).length >= 3);
check("withdrawal contract", hasAll(files.migration, ["'granted', 'withdrawn'", "consent_state = 'granted'", "ai_consent_required"]));
check("feature flags off", hasAll(files.migration, [
  "('ai_coach_enabled', false", "('provider_calls_enabled', false", "('staging_mock_enabled', false",
]));
check("AI/PT entitlement only", hasAll(files.migration, [
  "e.entitlement_code in ('ai', 'personal_coaching')", "e.status = 'active'",
  "e.starts_at <= p_at", "e.ends_at is null or e.ends_at > p_at",
]));
check("Free and Pro not entitlement", !files.migration.includes("e.entitlement_code in ('free'") && !files.migration.includes("e.entitlement_code in ('pro'"));
check("budget exact", hasAll(files.migration, [
  "included_micros = 3000000", "warning_micros = 2400000", "grace_micros = 1000000",
  "hard_cap_micros = 4000000", "terra_stop_micros = 3000000",
]));
check("no automatic billing", files.migration.includes("'automatic_billing', false"));
check("fair use not raw cost", hasAll(files.migration, ["fair_use_status", "provider_cost_visible_to_member", "false"]));
check("subscription month", hasAll(files.migration, ["subscription_period", "make_interval(months => v_months + 1)"]));
check("usage ledger", hasAll(files.migration, ["ledger_type in ('reserve', 'actual', 'release')", "ai_usage_ledger_run_type_unique"]));
check("rate policies and atomic buckets", hasAll(files.migration, ["ai_private.rate_policies", "ai_private.rate_buckets", "fmz_phase6a_rate:"]));
check("action allowlist", [
  "training_volume_adjustment", "add_rest_day", "reschedule_training",
  "replace_exercise", "calorie_target_adjustment",
].every((value) => files.migration.includes(value)));
check("training max 20", files.migration.includes("('training_volume_adjustment', 20, 100") && files.migration.includes("v_delta_percent <= 20"));
check("calorie min contract", hasAll(files.migration, ["v_delta_percent <= 10", "v_delta_kcal <= 300", "has_sufficient_new_authoritative_data"]));
check("fatigue and deload reduction", hasAll(files.migration, ["v_delta_percent < -20", "('fatigue', 'deload')"]));
check("compatible exercise", hasAll(files.migration, ["compatible_alternative_required", "compatible_alternative"]));
check("no medical action", !/action_code[^\n]+(medication|diagnos|treatment)/i.test(files.migration));
check("safety hard stop", hasAll(files.migration, ["serious_health", "unclear_health", "hard_stop", "review_required", "automatic_execution_blocked"]));
check("safe safety event only", !/create table if not exists ai_private\.safety_events[\s\S]{0,1000}(prompt|content_text|message_text)/i.test(files.migration));
check("private chat trainer isolation", !/create policy[^;]+trainer/is.test(files.migration) && files.migration.includes("can_share_trainer_summary"));
check("retention 90", hasAll(files.migration, ["interval '90 days'", "retention_state = 'grace'", "content_text = null", "retention_state = 'deleted'"]));
check("reactivation restore", hasAll(files.migration, ["if v_has_entitlement then", "retention_state = 'active'", "retention_due_at = null"]));
check("export lifecycle", hasAll(files.migration, ["fmz_phase6a_request_data_lifecycle", "fmz_phase6a_read_export_manifest", "('export', 'delete')"]));
check("context authority", hasAll(files.migration, [
  "phase6a.context.v1", "'authority', 'user_settings'", "'authority', 'recovery_logs'",
  "'authority', jsonb_build_array('training_plans','workout_sessions')",
  "'authority', jsonb_build_array('nutrition_targets','food_logs')",
  "'authority', jsonb_build_array('progress_goals','weight_logs','body_measurements')",
]));
check("missing sources truthful", hasAll(files.migration, ["health_sync", "running_activity", "progress_photos"]));
check("no copied notes", !/get_context_manifest[\s\S]+recovery_note/i.test(files.migration));
check("strict DB schema", hasAll(files.migration, ["additionalProperties", "validate_structured_response", "structured_output_invalid"]));
check("no partial assistant on fail", files.migration.includes("fmz_phase6a_service_fail_run") && !/fmz_phase6a_service_fail_run[\s\S]+insert into public\.ai_messages/i.test(files.migration));
check("mock must cost zero", hasAll(files.migration, ["v_run.adapter_code = 'mock'", "ai_mock_cost_forbidden"]));
check("provider flag gate", hasAll(files.migration, ["provider_calls_enabled", "provider_disabled"]));
check("eight member RPC grants", (files.migration.match(/grant execute on function public\.fmz_phase6a_(?!service_)/g) || []).length === 8);
check("five service RPC grants", (files.migration.match(/grant execute on function public\.fmz_phase6a_service_/g) || []).length === 5);
check("service role absent frontend", !/service[_-]?role/i.test(files.contracts + files.mock + files.handler + files.index));
check("no paid provider import", !/(openai|anthropic|gemini|chat\/completions|responses\/v1)/i.test(files.contracts + files.mock + files.handler + files.index));
check("no provider credential env", !/(OPENAI|ANTHROPIC|GEMINI|PROVIDER_API_KEY)/.test(files.index));
check("publishable member JWT client", hasAll(files.index, ["SUPABASE_PUBLISHABLE_KEY", "Authorization: `Bearer ${token}`", "auth.getUser(token)"]));
check("mock external calls zero", hasAll(files.mock + files.handler, ["externalCalls = 0", "external_ai_calls: 0", "external_ai_cost_eur: 0"]));
check("mock explicit environment flag", hasAll(files.index + files.handler, ["FMZ_PHASE6A_MOCK_TEST_ENABLED", "mockTestEnabled", "mock_disabled"]));
check("mock fixture matrix", ["success", "failure", "timeout", "malformed", "safety_hard_stop", "action_out_of_bounds"].every((value) => files.contracts.includes(`"${value}"`)));
check("strict request exact keys", hasAll(files.contracts, ["hasExactKeys", '"request_id", "feature_code", "locale", "fixture"']));
check("browser cannot choose provider", !/(provider_code|model_tier|provider_model)/.test(files.handler));
check("strict response exact keys", hasAll(files.contracts, ["validateCoachResponse", "schema_version", "observations", "uncertainties", "recommendations", "actions", "safety"]));
check("context manifest validator", hasAll(files.contracts, ["validateContextManifest", "phase6a.context-manifest.v1", "context_hash"]));
check("TypeScript budget parity", hasAll(files.contracts, ["2_400_000", "3_000_000", "4_000_000", "terra_grace_forbidden"]));
check("staging CORS only", hasAll(files.handler, ["https://yourizorge.github.io", "https://test.appfmz.nl", "origin_forbidden"]));
check("bounded body", hasAll(files.handler, ["8 * 1024", "body_too_large"]));
check("no polling", !/setInterval\s*\(/.test(files.contracts + files.mock + files.handler + files.index));
check("no MutationObserver", !(files.contracts + files.mock + files.handler + files.index).includes("MutationObserver"));
check("no dynamic SQL in Edge", !/(eval\s*\(|new Function|execute_sql|dynamic sql)/i.test(files.contracts + files.mock + files.handler + files.index));
check("README labels mock not coaching", hasAll(files.readme, ["never represents real coaching", "External AI calls: none", "Provider credentials: none"]));

check("verifier SELECT CTE", /^with\s/i.test(files.verifier.trim()) && /select verification_result from result;\s*$/i.test(files.verifier.trim()));
const verifierWithoutStrings = files.verifier.replace(/'(?:''|[^'])*'/g, "''");
check("verifier no mutation", !/\b(insert|update|delete|alter|create|drop|truncate|grant|revoke|call)\b/i.test(verifierWithoutStrings));
check("verifier overall pass", files.verifier.includes("'overall_pass', bool_and(pass)"));
check("verifier PUBLIC ACL safe", files.verifier.includes("case when a.grantee = 0 then 'PUBLIC'") && !files.verifier.includes("has_function_privilege('PUBLIC'"));
check("verifier array casts", hasAll(files.verifier, ["array_agg((a.attname::text", ")::text[] as columns"]));
check("verifier frozen guards", hasAll(files.verifier, ["frozen_guard_tables", "frozen_guard_rls", "Phase 1-5 source tables present"]));
check("transactional E2E rollback", /^begin;/.test(files.e2e.trim()) && /rollback;[\s\S]+fixtures_persisted/.test(files.e2e));
check("E2E zero provider cost", hasAll(files.e2e, ["external_ai_calls', 0", "external_ai_cost_eur', 0"]));
check("E2E entitlement matrix", hasAll(files.e2e, ["phase6a_free", "phase6a_pro", "phase6a_inactive", "phase6a_future", "phase6a_expired", "phase6a_pt"]));
check("E2E consent withdrawal", hasAll(files.e2e, ["'withdrawn'", "withdrawal did not block"]));
check("E2E cross member", hasAll(files.e2e, ["cross-member thread read allowed", "direct AI table read allowed"]));
check("E2E provider off", files.e2e.includes("provider run allowed while provider flag off"));
check("E2E budget boundaries", hasAll(files.e2e, ["2399999", "2400000", "3000000", "4000000"]));
check("E2E retention", hasAll(files.e2e, ["retention grace failed", "interval '91 days'", "retention deletion failed"]));

check("docs Package 6A status", hasAll(files.package, ["TECHNICAL PASS", "OpenAI activated: NO", "External AI calls: 0", "External AI cost: EUR 0"]));
check("docs owner decisions", hasAll(files.package + files.master, ["GPT-5.6 Luna", "GPT-5.6 Terra", "EUR 3", "EUR 4"]) && /90[- ]day/.test(files.package + files.master));
check("docs production lock", hasAll(files.package + files.status, ["hgoygcviutmynaihcvpd", "Production touched: NO"]));
check("docs next package blocked", hasAll(files.package, ["Package 6B", "NOT STARTED"]));
check("agents staging boundary", hasAll(files.agents, ["mokxyyullfhkfalopbzd", "Yourizorge/fitmetzorge-staging", "hgoygcviutmynaihcvpd"]));
check("no production ref runtime", !(files.contracts + files.mock + files.handler + files.index).includes("hgoygcviutmynaihcvpd"));
check("no secrets in artifacts", !/(sk-[a-z0-9]|sb_secret_|eyJhbGciOi)/i.test(Object.values(files).join("\n")));

let parsePass = true;
for (const [name, source] of Object.entries({ staticCheck: fs.readFileSync(__filename, "utf8") })) {
  try { new vm.Script(source, { filename: name }); } catch { parsePass = false; }
}
check("static checker parses", parsePass);

const failed = checks.filter((item) => !item.pass);
console.log(JSON.stringify({
  scope: "phase6a_ai_trust_foundation_static",
  pass_count: checks.length - failed.length,
  fail_count: failed.length,
  overall_pass: failed.length === 0,
  failed,
}, null, 2));
if (failed.length) process.exit(1);
