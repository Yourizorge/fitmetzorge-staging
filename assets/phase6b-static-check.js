const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");
const files = {
  migration: read("supabase/migrations/20260901230000_phase6b_provider_privacy_cost_gate.sql"),
  verifier: read("supabase/verification/20260901230000_phase6b_provider_privacy_cost_gate_verification.sql"),
  e2e: read("supabase/tests/20260901230000_phase6b_provider_privacy_cost_gate_transactional_e2e.sql"),
  contracts: read("supabase/functions/youri-ai/provider-contracts.ts"),
  adapter: read("supabase/functions/youri-ai/openai-adapter.ts"),
  handler: read("supabase/functions/youri-ai/phase6b-handler.ts"),
  index: read("supabase/functions/youri-ai/index.ts"),
  providerTests: read("supabase/functions/youri-ai/phase6b-provider.test.ts"),
  package: read("docs/PHASE6B_PROVIDER_PRIVACY_COST_GATE.md"),
  sixA: read("docs/PHASE6A_AI_TRUST_FOUNDATION.md"),
  master: read("docs/MASTER_BUILD_PLAN.md"),
  status: read("docs/BUILD_STATUS.md"),
  architecture: read("docs/ARCHITECTURE.md"),
  decisions: read("docs/DECISIONS.md"),
  tests: read("docs/TEST_MATRIX.md"),
  flow: read("docs/privacy/PHASE6B_DATA_FLOW_INVENTORY.md"),
  processors: read("docs/privacy/PHASE6B_PROCESSOR_SUBPROCESSOR_REGISTER.md"),
  dpa: read("docs/privacy/PHASE6B_DPA_CHECKLIST.md"),
  dpia: read("docs/privacy/PHASE6B_DPIA_DRAFT.md"),
  eu: read("docs/privacy/PHASE6B_TRANSFER_EU_ROUTE_CHECKLIST.md"),
  medical: read("docs/PHASE6B_MEDICAL_SAFETY_COPY.md"),
};

const checks = [];
const check = (name, condition) => checks.push({ name, pass: Boolean(condition) });
const hasAll = (source, values) => values.every((value) => source.includes(value));
const runtime = files.contracts + files.adapter + files.handler + files.index;
const all = Object.values(files).join("\n");

check("migration transaction", /^--[\s\S]*\nbegin;/.test(files.migration) && /\ncommit;\s*$/.test(files.migration));
check("five private tables", ["provider_configurations","provider_models","provider_payload_fields","provider_test_budget","provider_test_runs"].every((x) => files.migration.includes(`create table if not exists ai_private.${x}`)));
check("RLS all five", (files.migration.match(/alter table ai_private\.provider_[a-z_]+ enable row level security;/g) || []).length === 5);
check("no provider policies", !/create policy[^;]+provider_/i.test(files.migration));
check("browser table ACL revoked", (files.migration.match(/revoke all on table ai_private\.provider_/g) || []).length === 5);
check("OpenAI only", files.migration.includes("provider_code = 'openai'") && !/(anthropic|gemini|mistral)/i.test(runtime));
check("exact Luna model", hasAll(files.migration + runtime, ["gpt-5.6-luna", "model_route = 'luna'"]));
check("exact Terra model", hasAll(files.migration + runtime, ["gpt-5.6-terra", "model_route = 'terra'"]));
check("no model substitution", files.adapter.includes("provider_model_forbidden") && files.adapter.includes("provider_route_conflict"));
check("official price lock", hasAll(files.migration, ["200000,20000,1200000", "2000000,200000,12000000"]));
check("Responses endpoint exact", files.adapter.includes('const FIXED_OPENAI_ENDPOINT = "https://api.openai.com/v1/responses"'));
check("real EU endpoint gated", files.migration.includes("https://eu.api.openai.com/v1/responses"));
check("store false", files.adapter.includes("store: false"));
check("background false", files.adapter.includes("background: false"));
check("tools denied", hasAll(files.adapter, ["tools: []", 'tool_choice: "none"']));
check("strict JSON schema", hasAll(files.adapter, ['type: "json_schema"', "strict: true"]));
check("no hosted tool imports", !/(web_search|file_search|code_interpreter|computer_use|image_generation|mcp_server)/i.test(runtime));
check("no metadata state", hasAll(files.providerTests, ['"metadata" in body', '"previous_response_id" in body']));
check("synthetic fixtures exact", hasAll(files.contracts, ["luna_connectivity_v1", "terra_structured_v1", "synthetic_phase6b_alpha"]));
check("request exact keys", files.contracts.includes('exactKeys(value, ["fixture_code", "request_id"])'));
check("payload nine field ledger", (files.migration.match(/\('phase6b\.synthetic-payload\.v1'/g) || []).length === 9);
check("payload exact object keys", hasAll(files.contracts, ["EXACT_PAYLOAD_KEYS", "EXACT_SNAPSHOT_KEYS", "assertSyntheticPayloadAllowlist"]));
check("payload sensitive scan", files.contracts.includes("provider_payload_sensitive_field_forbidden"));
check("no raw operational prompt", !/\n\s+(prompt|content_text|message_text|email|jwt|secret)\s+[a-z]/i.test(files.migration));
check("strict provider output", hasAll(files.contracts + files.adapter, ["PHASE6B_PROVIDER_OUTPUT_SCHEMA", "assertProviderOutput", "provider_structured_output_invalid"]));
check("no actions in provider test", files.contracts.includes('maxItems: 0'));
check("provider timeout bounded", hasAll(files.adapter, ["20_000", "provider_timeout_invalid", "provider_timeout"]));
check("retry max two", hasAll(files.adapter, ["maxAttempts > 2", "response.status === 429", "response.status >= 500"]));
check("usage exact", hasAll(files.adapter, ["input_tokens", "cached_tokens", "output_tokens", "provider_usage_invalid"]));
check("sanitized provider errors", hasAll(files.adapter, ["provider_authentication_failed", "provider_request_rejected", "provider_network_error"]));
check("no provider body logging", !/(console\.|response\.text\(|providerBody|rawResponse)/.test(files.adapter + files.handler));
check("server-only origin rejection", files.handler.includes('request.headers.get("Origin")') && files.handler.includes("server_only_route"));
check("server secret authorization", hasAll(files.index, ["secretKeys()", "equalSecret", "authorizeServer"]));
check("member provider route absent", !/phase6b\/(chat|member|generate)/.test(files.index + files.handler));
check("explicit test environment flag", hasAll(files.index + files.handler, ["FMZ_PHASE6B_SYNTHETIC_TEST_ENABLED", "providerTestEnvironmentEnabled"]));
check("server OpenAI secret only", hasAll(files.index, ["OPENAI_API_KEY", "Deno.env.get"]));
check("no key returned", !/(openAiApiKey|availableSecretKeys|adminKey)\s*[:,]\s*[^\n]*json/i.test(files.index + files.handler));
check("real member DB off", hasAll(files.migration, ["real_member_processing_enabled boolean not null default false", "owner_real_member_activation boolean not null default false"]));
check("ZDR gate", hasAll(files.migration, ["zdr_status = 'verified'", "execution_mode = 'zdr_verified'"]));
check("DPA gate", files.migration.includes("dpa_status = 'complete'"));
check("DPIA gate", files.migration.includes("dpia_status = 'complete'"));
check("EU route gate", hasAll(files.migration, ["eu_route_status = 'verified'", "https://eu.api.openai.com/v1/responses"]));
check("privacy and consent gates", hasAll(files.migration, ["privacy_notice_status = 'approved'", "consent_copy_status = 'approved'"]));
check("transfer lifecycle gates", hasAll(files.migration, ["transfer_assessment_status = 'complete'", "lifecycle_verification_status = 'complete'"]));
check("real member helper false", hasAll(files.migration, ["phase6b_real_member_gate", "'allowed', false", "real_member_provider_processing_blocked_phase6b"]));
check("global EUR five", hasAll(files.migration, ["max_total_eur_micros bigint not null default 5000000", "max_total_eur_micros = 5000000"]));
check("call cap six", hasAll(files.migration, ["max_external_calls integer not null default 6", "max_external_calls = 6"]));
check("conservative EUR conversion", files.migration.includes("conservative_eur_per_usd_ppm bigint not null default 1250000"));
check("request advisory lock", files.migration.includes("fmz_phase6b_test_request:"));
check("budget advisory lock", (files.migration.match(/fmz_phase6b_test_budget:phase6b-staging-v1/g) || []).length >= 3);
check("reserve before run", files.migration.indexOf("ai_provider_test_budget_exceeded") < files.migration.indexOf("insert into ai_private.provider_test_runs"));
check("exact replay", hasAll(files.migration, ["ai_provider_test_request_conflict", "'replay', true"]));
check("actual reconciliation", hasAll(files.migration, ["ai_provider_test_reservation_exceeded", "consumed_eur_micros = consumed_eur_micros + v_cost.eur_micros"]));
check("unknown cost conservative", hasAll(files.migration, ["p_cost_unknown and p_attempt_count > 0 then v_run.reserved_eur_micros", "v_run.actual_eur_micros <> v_charge"]));
check("four service RPCs", (files.migration.match(/grant execute on function public\.fmz_phase6b_service_/g) || []).length === 4);
check("no public app execute", (files.migration.match(/revoke all on function public\.fmz_phase6b_service_/g) || []).length === 4);
check("safe definer search path", (files.migration.match(/security definer\nset search_path = pg_catalog, extensions, public, ai_private, pg_temp/g) || []).length === 4);
check("private helpers invoker", (files.migration.match(/security invoker\nset search_path = pg_catalog, ai_private, pg_temp/g) || []).length === 2);
check("no domain write", !/(insert into|update|delete from) public\.(training_|nutrition_|progress_|recovery_)/i.test(files.migration));
check("no external SQL", !/(http_post|net\.http|pg_net)/i.test(files.migration));
check("verifier one SELECT CTE", /^with\s/i.test(files.verifier.trim()) && /select verification_result from result;\s*$/i.test(files.verifier.trim()));
const verifierNoStrings = files.verifier.replace(/'(?:''|[^'])*'/g, "''");
check("verifier read only", !/\b(insert|update|delete|alter|create|drop|truncate|grant|revoke|call)\b/i.test(verifierNoStrings));
check("verifier overall pass", files.verifier.includes("'overall_pass',bool_and(pass)"));
check("verifier PUBLIC ACL safe", files.verifier.includes("case when a.grantee=0 then 'PUBLIC'") && !files.verifier.includes("has_function_privilege('PUBLIC'"));
check("verifier typed arrays", files.verifier.includes("::text[]"));
check("verifier frozen guards", hasAll(files.verifier, ["frozen_guard_tables", "frozen_guard_rls", "phase6a_flags_remain_off"]));
check("E2E rollback", /^begin;/.test(files.e2e.trim()) && /rollback;\s*$/.test(files.e2e.trim()));
check("E2E zero provider call", hasAll(files.e2e, ["'synthetic_provider_calls',0", "'external_ai_cost_eur',0"]));
check("E2E real member denied", files.e2e.includes("real member gate did not fail closed"));
check("E2E replay conflict", files.e2e.includes("request replay conflict was accepted"));
check("E2E cost cap", files.e2e.includes("EUR 5 cap was bypassed"));
check("E2E call cap", files.e2e.includes("external-call cap was bypassed"));
check("provider test count", (files.providerTests.match(/test\("/g) || []).length >= 16);
check("adapter no external in unit tests", files.providerTests.includes('apiKey: "test-only"') && files.providerTests.includes("fetchImpl"));
check("6A frozen documented", hasAll(files.sixA + files.status + files.tests, ["COMPLETE / OWNER-ACCEPTED / FROZEN", "055f610eb1a8712910214487d2e2bed96d40111c"]));
check("DPA incomplete", hasAll(files.package + files.dpa, ["DPA: INCOMPLETE", "OWNER ACTION REQUIRED"]));
check("DPIA incomplete", hasAll(files.package + files.dpia, ["DPIA: INCOMPLETE", "INCOMPLETE DRAFT"]));
check("ZDR unverified", hasAll(files.package + files.eu, ["ZDR: UNVERIFIED", "store:false", "not accepted as ZDR proof"]));
check("processor register", hasAll(files.processors, ["OpenAI", "Supabase", "DPA not owner-executed"]));
check("medical NL EN DE", hasAll(files.medical, ["## Nederlands", "## English", "## Deutsch", "NOT MEDICALLY OR LEGALLY APPROVED"]));
check("FR IT unpublished", hasAll(files.medical, ["FR / IT", "No FR/IT text is approved or published"]));
check("Package 6C not started", hasAll(files.package + files.master + files.tests, ["Package 6C", "not started"]));
check("no frontend changes in runtime", !/(document\.|window\.|localStorage|sessionStorage)/.test(runtime));
check("no polling", !/setInterval\s*\(/.test(runtime));
check("no MutationObserver", !runtime.includes("MutationObserver"));
check("staging ref locked", hasAll(files.migration + files.package, ["mokxyyullfhkfalopbzd", "STAGING"]));
check("production runtime absent", !runtime.includes("hgoygcviutmynaihcvpd"));
check("no secrets committed", !/(sk-[a-z0-9]{12,}|sb_secret_[a-z0-9]|eyJhbGciOi)/i.test(all));

let parsePass = true;
try { new vm.Script(fs.readFileSync(__filename, "utf8"), { filename: "phase6b-static-check.js" }); } catch { parsePass = false; }
check("static checker parses", parsePass);

const failed = checks.filter((item) => !item.pass);
console.log(JSON.stringify({
  scope: "phase6b_provider_privacy_cost_gate_static",
  pass_count: checks.length - failed.length,
  fail_count: failed.length,
  overall_pass: failed.length === 0,
  failed,
}, null, 2));
if (failed.length) process.exit(1);
