const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");
const files = {
  runtime: read("assets/phase6c-private-ai-chat.js"),
  app: read("app.js"),
  index: read("index.html"),
  migration: read("supabase/migrations/20260904230850_phase6d_read_only_ai_analyses.sql"),
  edge: read("supabase/functions/youri-ai/phase6d-handler.ts"),
  edgeIndex: read("supabase/functions/youri-ai/index.ts"),
  edgeTest: read("supabase/functions/youri-ai/phase6d-handler.test.ts"),
};
const checks = [];
const check = (name, pass) => checks.push({ name, pass: Boolean(pass) });
const all = (text, needles) => needles.every((needle) => text.includes(needle));

check("cache and runtime version", all(files.runtime + files.app + files.index, [
  "20260904-phase6d-analyses1",
  "assets/phase6c-private-ai-chat.js?v=20260904-phase6d-analyses1",
  "app.js?v=20260904-phase6d-analyses1",
]));
check("frontend analyses tab", all(files.runtime, [
  'tabAnalyses:"Analyses"',
  'data-p6c-tab="analyses"',
  "renderAnalysisView",
  "readOnlyAnalyses:true",
]));
check("frontend RPC surface", all(files.runtime, [
  "fmz_phase6d_get_status",
  "fmz_phase6d_read_analysis_contract",
  "fmz_phase6d_record_analysis_consent",
  "fmz_phase6d_update_preferences",
  "fmz_phase6d_list_analyses",
  "fmz_phase6d_export_analyses",
  "fmz_phase6d_delete_analysis",
]));
check("frontend edge request bounded", all(files.runtime, [
  "/youri-ai/phase6d/analyze",
  "request_id:uuid()",
  "analysis_kind:kind",
  "locale:lang()",
]) && !/analysis_kind:kind[\s\S]{0,140}(model|provider|fixture|entitlement|user_id)/.test(files.runtime));
check("consent separated", all(files.migration, [
  "'ai_analysis'",
  "fmz_phase6d_read_analysis_contract",
  "fmz_phase6d_record_analysis_consent",
  "phase6d-analysis-v1",
]) && !/fmz_phase6d_record_analysis_consent[\s\S]{0,4000}ai_processing/.test(files.migration));
check("result and preference tables", all(files.migration, [
  "create table if not exists public.ai_analysis_preferences",
  "create table if not exists public.ai_analysis_results",
  "create table if not exists public.ai_analysis_lifecycle_requests",
  "ai_analysis_results_user_request_unique",
  "ai_analysis_results_user_event_unique",
]));
check("RLS and RPC-only table grants", all(files.migration, [
  "alter table public.ai_analysis_preferences enable row level security",
  "alter table public.ai_analysis_results enable row level security",
  "revoke all on table public.ai_analysis_preferences from public, anon, authenticated",
  "revoke all on table public.ai_analysis_results from public, anon, authenticated",
]));
check("model routing", all(files.migration + files.edgeTest, [
  "if p_analysis_kind = 'weekly' then return 'terra'",
  "if p_analysis_kind in ('daily', 'post_workout') then return 'luna'",
  "weekly mock keeps Terra feature contract",
]));
check("budget and zero cost", all(files.migration + files.edge, [
  "ai_private.evaluate_budget",
  "budget_accounts",
  "usage_ledger",
  "p_actual_cost_micros: 0",
  "external_ai_cost_eur: 0",
]));
check("retention 90 and 180 days", all(files.migration, [
  "interval '90 days'",
  "interval '180 days'",
  "phase6d_retention_sweep",
  "fmz-phase6d-analysis-retention-sweep",
]));
check("context minimization", all(files.migration + files.edge, [
  "max_lookback_days', 30",
  "'private_chat_included', false",
  "'raw_prompts_included', false",
  "'raw_notes_included', false",
  "chat_history_used_as_context: false",
  "domain_writes_allowed",
]));
check("data quality stop before provider", all(files.migration + files.edgeTest, [
  "'stop_before_provider', not v_reliable",
  "'insufficient_data'",
  "insufficient data stops before service run",
]));
check("service RPCs service-only", all(files.migration, [
  "grant execute on function public.fmz_phase6d_service_begin_analysis",
  "grant execute on function public.fmz_phase6d_service_complete_analysis",
  "grant execute on function public.fmz_phase6d_service_fail_analysis",
  "to service_role",
]));
check("edge route and safe errors", all(files.edgeIndex + files.edge, [
  "createPhase6dHandler",
  "/phase6d/analyze",
  "analysis_[a-z0-9_]+",
  "validatePhase6dAnalysisOutput",
]) && !files.edge.includes("OPENAI_API_KEY"));
check("provider is disabled for member data", all(files.migration + files.edge, [
  "external_provider_enabled boolean not null default false",
  "phase6d_runtime_provider_off_check",
  "external_provider_forbidden",
  "external_ai_calls: 0",
]));
check("no action proposals", all(files.migration + files.edge, [
  "jsonb_array_length(p_payload -> 'actions') <> 0",
  "actions: []",
  "domain_writes_allowed: false",
]));
check("tests cover handler", all(files.edgeTest, [
  "analysis request is exact",
  "authenticated request prepares",
  "controlled failure is sanitized",
  "auth and origin fail closed",
]));

const failed = checks.filter((item) => !item.pass);
console.log(JSON.stringify({
  scope: "phase6d_read_only_ai_analyses_static",
  pass_count: checks.length - failed.length,
  fail_count: failed.length,
  overall_pass: failed.length === 0,
  failed,
}, null, 2));
if (failed.length) process.exit(1);
