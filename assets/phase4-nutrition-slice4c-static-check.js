const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const sha256 = (source) => crypto.createHash("sha256").update(source).digest("hex").toUpperCase();
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const migrationPath = "supabase/migrations/20260819_phase4_nutrition_slice4c_operational_state.sql";
const verifierPath = "supabase/verification/20260819_phase4_nutrition_slice4c_operational_state_verification.sql";
const migration = read(migrationPath);
const verifier = read(verifierPath);
const slice1 = read("supabase/migrations/20260818_phase4_nutrition_schema_slice1.sql");
const replacement = read("supabase/migrations/20260819_phase4_nutrition_slice3_atomic_log_item_replacement.sql");
const slice4b = read("supabase/migrations/20260819_phase4_nutrition_slice4b_alias_search.sql");
const slice4bVerifier = read("supabase/verification/20260819_phase4_nutrition_slice4b_alias_search_verification.sql");
const catalogArchitecture = read("docs/PHASE4_NUTRITION_SLICE4_CATALOG_ARCHITECTURE.md");
const decisions = read("docs/DECISIONS.md");
const buildStatus = read("docs/BUILD_STATUS.md");
const masterPlan = read("docs/MASTER_BUILD_PLAN.md");
const architecture = read("docs/ARCHITECTURE.md");
const testMatrix = read("docs/TEST_MATRIX.md");

const migrationWithoutComments = migration.replace(/^\s*--.*$/gm, "");
const migrationTopLevel = migrationWithoutComments.replace(
  /create\s+or\s+replace\s+function\s+public\.[\s\S]*?\n\$\$;/gi,
  ""
);
const verifierWithoutComments = verifier.replace(/^\s*--.*$/gm, "").trim();
const createTables = [...migration.matchAll(/create\s+table\s+if\s+not\s+exists\s+public\.([a-z0-9_]+)/gi)].map((match) => match[1]);
const createFunctions = [...migration.matchAll(/create\s+(?:or\s+replace\s+)?function\s+public\.([a-z0-9_]+)/gi)].map((match) => match[1]);
const createPolicies = [...migration.matchAll(/create\s+policy\s+[^;]+/gi)];

check("Slice 4C migration review hash is locked", sha256(migration) === "0A2D2CA5B4CAAD30A17B73F66C018A742DC1D9326335AA7C9307D0021CF0AE2F");
check("Slice 4C verifier review hash is locked", sha256(verifier) === "B444C84CA42347E2D637A025CD76141F8C12821262CBD0E110B770BBBA2CA200");
check("migration has staging-only project guard", migration.includes("STAGING ONLY: mokxyyullfhkfalopbzd"));
check("migration is one explicit transaction", (migration.match(/^\s*begin;/gim) || []).length === 1 && (migration.match(/^\s*commit;/gim) || []).length === 1 && /commit;\s*$/i.test(migration));
check("migration creates exactly four operational tables", JSON.stringify(createTables) === JSON.stringify([
  "nutrition_provider_query_cache",
  "nutrition_provider_food_cache",
  "nutrition_provider_rate_buckets",
  "nutrition_provider_runtime_state"
]));
check("migration creates exactly two internal functions", JSON.stringify(createFunctions) === JSON.stringify([
  "fmz_phase4_provider_consume_rate_limits",
  "fmz_phase4_provider_transition_runtime_state"
]));
check("migration dollar-quote pairs are balanced", (migration.match(/\$\$/g) || []).length === 4);
check("migration does not schema-qualify parser-only expressions", !/pg_catalog\.(coalesce|greatest|least|extract|nullif)\b/i.test(migration));
check("migration creates no member policy", createPolicies.length === 0);
check("migration has no top-level data mutation", !/^\s*(insert|update|delete|truncate)\b/im.test(migrationTopLevel));
check("migration has no destructive object removal", !/\b(drop\s+(?:table|column|constraint|index|function|policy|trigger|extension)|truncate\s+table)\b/i.test(migrationWithoutComments));
check("migration contains no seed backfill or canonical write", !/\b(copy\s+public\.|insert\s+into\s+public\.foods\b|update\s+public\.foods\b|insert\s+into\s+public\.food_aliases\b)\b/i.test(migrationWithoutComments));
check("migration has no production reference", !migration.includes("hgoygcviutmynaihcvpd"));
check("migration embeds no credential", !/(USDA_FDC_API_KEY|FMZ_PROVIDER_HMAC_KEY|SUPABASE_SERVICE_ROLE_KEY|eyJ[a-zA-Z0-9_-]{10,})/.test(migration));
check("migration does not alter frozen application tables", !/alter\s+table\s+public\.(foods|food_aliases|food_portions|food_logs|food_log_items|nutrition_targets|profiles|coach_workspaces|recovery_logs|training_plans|workout_sessions)\b/i.test(migration));
check("migration does not replace frozen Nutrition RPCs", !/(fmz_phase4_search_foods\s*\(|fmz_phase4_replace_food_log_item\s*\()/i.test(migration));
check("ingestion ledger is deferred", !migration.includes("nutrition_provider_ingestion_ledger"));

for (const table of createTables) {
  check(`${table} has RLS enabled`, new RegExp(`alter\\s+table\\s+public\\.${table}\\s+enable\\s+row\\s+level\\s+security`, "i").test(migration));
  check(`${table} revokes PUBLIC`, new RegExp(`revoke\\s+all\\s+on\\s+table\\s+public\\.${table}\\s+from\\s+public`, "i").test(migration));
  check(`${table} revokes anon`, new RegExp(`revoke\\s+all\\s+on\\s+table\\s+public\\.${table}\\s+from\\s+anon`, "i").test(migration));
  check(`${table} revokes authenticated`, new RegExp(`revoke\\s+all\\s+on\\s+table\\s+public\\.${table}\\s+from\\s+authenticated`, "i").test(migration));
  check(`${table} resets service_role ACL`, new RegExp(`revoke\\s+all\\s+on\\s+table\\s+public\\.${table}\\s+from\\s+service_role`, "i").test(migration));
}

check("query cache keeps no raw query or auth uid column", !/\n\s*(raw_query|query|user_id|auth_uid)\s+[a-z]/i.test(migration.match(/create table if not exists public\.nutrition_provider_query_cache[\s\S]*?\n\);/i)[0]));
check("query cache HMAC is fixed lowercase hex", migration.includes("query_hmac ~ '^[0-9a-f]{64}$'"));
check("query cache identity includes provider locale country paging filters and mapping", /primary key\s*\(\s*provider_code,\s*query_hmac,\s*locale,\s*country_code,\s*page_number,\s*page_size,\s*filter_key,\s*mapping_version\s*\)/i.test(migration));
check("query cache country code is explicit and bounded", migration.includes("country_code ~ '^[A-Z]{2}$'"));
check("query cache pages are bounded", migration.includes("page_number between 1 and 3 and page_size between 1 and 10"));
check("query cache USDA data types are explicit", migration.includes("data_type_filter = array['Foundation', 'Survey (FNDDS)', 'SR Legacy']::text[]"));
check("query cache filters exclude sensitive identity keys", migration.includes("array['query', 'raw_query', 'user_id', 'auth_uid']"));
check("query cache result payload is a bounded array", migration.includes("jsonb_typeof(result_payload) = 'array'") && migration.includes("octet_length(result_payload::text) <= 131072"));
check("query cache count matches payload and max ten", migration.includes("result_count = jsonb_array_length(result_payload)") && migration.includes("result_count between 0 and 10"));
check("query cache positive empty quarantine states are explicit", migration.includes("cache_status in ('positive', 'empty', 'quarantined')"));
check("query cache expiry remains configurable but capped", migration.includes("expires_at <= fetched_at + interval '7 days'"));

check("food cache stable identity includes provider id and mapping", /nutrition_provider_food_cache_pkey[\s\S]*provider_code,[\s\S]*provider_food_id,[\s\S]*mapping_version/i.test(migration));
check("food cache provider data type is explicit", migration.includes("provider_data_type in ('Foundation', 'Survey (FNDDS)', 'SR Legacy')"));
check("food cache candidate mapping identity is unique", /create\s+unique\s+index[\s\S]*nutrition_provider_food_cache_candidate_mapping_uidx[\s\S]*candidate_id,\s*mapping_version/i.test(migration));
check("food cache normalized payload is a bounded object", migration.includes("jsonb_typeof(normalized_payload) = 'object'") && migration.includes("octet_length(normalized_payload::text) <= 131072"));
check("food cache checksum is fixed lowercase hex", migration.includes("payload_checksum ~ '^[0-9a-f]{64}$'"));
check("food cache quality and rejection states are constrained", migration.includes("quality_state in ('candidate', 'validated', 'quarantined', 'rejected')") && migration.includes("nutrition_provider_food_cache_rejection_check"));
check("food cache provenance and metadata are bounded objects", migration.includes("octet_length(provenance::text) <= 32768") && migration.includes("octet_length(metadata::text) <= 8192"));
check("food cache explicit expiry supports thirty-day config", migration.includes("expires_at <= fetched_at + interval '180 days'"));

check("provider code is constrained text and USDA only now", (migration.match(/check \(provider_code = 'usda_fdc'\)/g) || []).length === 4 && !/create\s+type[\s\S]*enum/i.test(migration));
check("rate buckets store HMAC subjects not user ids", migration.includes("subject_hmac text not null") && !/nutrition_provider_rate_buckets[\s\S]*?user_id\s+uuid/i.test(migration));
check("rate scopes cover all locked budgets", ["user_30_seconds", "user_10_minutes", "user_day", "provider_hour"].every((scope) => migration.includes(scope)));
check("rate table locks exact current hard ceilings", ["window_seconds = 30", "limit_value = 3", "window_seconds = 600", "limit_value = 12", "window_seconds = 86400", "limit_value = 100", "window_seconds = 3600", "limit_value = 800"].every((fragment) => migration.includes(fragment)));
check("rate windows are aligned and explicit", migration.includes("make_interval(secs => window_seconds)") && migration.includes("floor(extract(epoch from window_start) / window_seconds)"));
check("rate request ids support bounded same-window replay", migration.includes("consumed_request_ids uuid[]") && migration.includes("request_count = cardinality(consumed_request_ids)") && migration.includes("cardinality(consumed_request_ids) <= 1000"));

check("runtime circuit states are exact", migration.includes("circuit_state in ('closed', 'open', 'half_open')"));
check("runtime transition shape is constrained", migration.includes("nutrition_provider_runtime_state_transition_shape_check") && migration.includes("next_probe_at >= opened_at"));
check("runtime metadata is a bounded object", migration.includes("jsonb_typeof(metadata) = 'object'") && migration.includes("octet_length(metadata::text) <= 4096"));
const runtimeTable = migration.match(/create table if not exists public\.nutrition_provider_runtime_state[\s\S]*?\n\);/i)?.[0] || "";
check("runtime state is not a general request log", !/request_(body|payload|query)|raw_(body|payload|query)/i.test(runtimeTable));

const rateSource = migration.match(/create or replace function public\.fmz_phase4_provider_consume_rate_limits[\s\S]*?\n\$\$;/i)?.[0] || "";
check("rate function is SECURITY DEFINER with pg_catalog search path", /security\s+definer[\s\S]*set\s+search_path\s*=\s*pg_catalog/i.test(rateSource));
check("rate function accepts no user id role package or entitlement", !/p_(user_id|role|package|entitlement)/i.test(rateSource));
check("rate function accepts backend HMAC and request identity", /p_user_subject_hmac\s+text/i.test(rateSource) && /p_request_id\s+uuid/i.test(rateSource));
check("rate function locks global then user namespace", /fmz_phase4_provider_rate:[\s\S]*:global[\s\S]*fmz_phase4_provider_rate:[\s\S]*:user:/i.test(rateSource));
check("rate function inserts all four bucket identities before decision", rateSource.includes("for v_index in 1..4 loop") && rateSource.includes("on conflict (provider_code, bucket_scope, subject_hmac, window_start) do nothing"));
check("rate function detects all-or-none replay", rateSource.includes("v_replay_count not in (0, 4)") && rateSource.includes("v_replay_count = 4"));
check("rate function checks every bucket before counter writes", rateSource.indexOf("v_failed_until is not null") < rateSource.indexOf("request_count = request_count + 1"));
check("rate function increments all buckets in one transaction", rateSource.includes("request_count = request_count + 1") && rateSource.includes("array_append(consumed_request_ids, p_request_id)"));
check("rate function returns retry timing without partial consume", rateSource.includes("'retry_after_seconds'") && rateSource.includes("'allowed', false"));
check("rate table is RPC-only for service role", !/grant\s+[^;]+on\s+table\s+public\.nutrition_provider_rate_buckets\s+to\s+service_role/i.test(migration));

const runtimeSource = migration.match(/create or replace function public\.fmz_phase4_provider_transition_runtime_state[\s\S]*?\n\$\$;/i)?.[0] || "";
check("runtime function is SECURITY DEFINER with pg_catalog search path", /security\s+definer[\s\S]*set\s+search_path\s*=\s*pg_catalog/i.test(runtimeSource));
check("runtime function serializes provider transitions", runtimeSource.includes("pg_advisory_xact_lock") && runtimeSource.includes("for update"));
check("runtime begin probe allows one half-open probe", runtimeSource.includes("v_event = 'begin_probe'") && runtimeSource.includes("circuit_state = 'half_open'") && runtimeSource.includes("v_probe_allowed := true"));
check("runtime success closes circuit", /v_event\s*=\s*'success'[\s\S]*circuit_state\s*=\s*'closed'[\s\S]*consecutive_failures\s*=\s*0/i.test(runtimeSource));
check("runtime provider rate event opens circuit", /v_event\s*=\s*'rate_limited'[\s\S]*circuit_state\s*=\s*'open'/i.test(runtimeSource));
check("runtime failure threshold is five", runtimeSource.includes("v_failure_count >= 5"));
check("runtime table is transition-RPC write only", /grant\s+select\s+on\s+table\s+public\.nutrition_provider_runtime_state\s+to\s+service_role/i.test(migration) && !/grant\s+(insert|update|delete)[^;]*nutrition_provider_runtime_state/i.test(migration));

for (const fn of ["fmz_phase4_provider_consume_rate_limits", "fmz_phase4_provider_transition_runtime_state"]) {
  check(`${fn} revokes PUBLIC`, new RegExp(`revoke\\s+all\\s+on\\s+function\\s+public\\.${fn}[\\s\\S]*?from\\s+public`, "i").test(migration));
  check(`${fn} revokes anon`, new RegExp(`revoke\\s+all\\s+on\\s+function\\s+public\\.${fn}[\\s\\S]*?from\\s+anon`, "i").test(migration));
  check(`${fn} revokes authenticated`, new RegExp(`revoke\\s+all\\s+on\\s+function\\s+public\\.${fn}[\\s\\S]*?from\\s+authenticated`, "i").test(migration));
  check(`${fn} grants only service_role execution`, new RegExp(`grant\\s+execute\\s+on\\s+function\\s+public\\.${fn}[\\s\\S]*?to\\s+service_role`, "i").test(migration));
}

check("cache service-role ACL is read and upsert only", /grant\s+select,\s*insert,\s*update\s+on\s+table\s+public\.nutrition_provider_query_cache\s+to\s+service_role/i.test(migration) && /grant\s+select,\s*insert,\s*update\s+on\s+table\s+public\.nutrition_provider_food_cache\s+to\s+service_role/i.test(migration));
check("migration grants no table removal or maintenance privilege", !/grant\s+(delete|truncate|references|trigger|maintain|all)\b/i.test(migration));
check("four updated-at triggers reuse frozen helper", (migration.match(/execute function public\.fmz_phase4_touch_updated_at\(\)/g) || []).length === 4);

check("verifier is one SELECT CTE statement", /^with\b/i.test(verifierWithoutComments) && /select\s+jsonb_build_object\(/i.test(verifierWithoutComments) && /from\s+checks;\s*$/i.test(verifierWithoutComments));
check("verifier contains no modifying statement", !/^\s*(insert|update|delete|truncate|create|alter|drop|grant|revoke|comment|call)\b/im.test(verifierWithoutComments));
check("verifier invokes no application RPC", !/select\s+(?:public\.)?fmz_phase4_/i.test(verifierWithoutComments));
check("verifier handles PUBLIC through ACL grantee zero", verifier.includes("pg_catalog.aclexplode") && verifier.includes("acl.grantee = 0"));
check("verifier checks exact tables columns constraints and indexes", ["exact_operational_tables", "exact_columns", "constraints", "indexes"].every((name) => verifier.includes(`'${name}'`)));
check("verifier checks RLS zero policies and ACL", ["rls_enabled_zero_policies", "member_anon_public_table_acl_none", "service_role_table_acl_minimal"].every((name) => verifier.includes(`'${name}'`)));
check("verifier checks internal function security and source", ["internal_functions_exact_security", "atomic_rate_limit_source_contract", "runtime_transition_source_contract"].every((name) => verifier.includes(`'${name}'`)));
check("verifier checks deferred ledger and empty operational state", verifier.includes("ingestion_ledger_deferred") && verifier.includes("operational_tables_initially_empty"));
check("verifier checks no canonical provider import", verifier.includes("no_provider_canonical_import"));
check("verifier checks Slice 4B live guard", verifier.includes("slice4b_live_guard") && verifier.includes("slice4b_index_count = 7"));
check("verifier checks frozen tables and functions", verifier.includes("frozen_guard_tables") && verifier.includes("frozen_slice3_and_search_functions"));
check("verifier returns individual checks and overall pass", verifier.includes("'overall_pass', bool_and(pass)") && verifier.includes("'checks', jsonb_agg"));

check("Slice 1 migration hash remains frozen", sha256(slice1) === "D70A589FEF997C14FCC9805E746536C86556E22622C8952B33DE9CA222B36188");
check("atomic replacement migration hash remains frozen", sha256(replacement) === "6F3B59207B2974B771A0677720377AAAD7500E31DF16A645B606B99088A8EE40");
check("Slice 4B migration hash remains frozen", sha256(slice4b) === "4C0E63DC09A8CC1DE7F93DBA278CD36F714C52BEDAB32FFC98147A5DA0D5C88F");
check("Slice 4B verifier remains present", sha256(slice4bVerifier).length === 64 && slice4bVerifier.includes("phase4_nutrition_slice4b_alias_search"));

check("catalog architecture records Slice 4C operational schema", /Slice 4C[\s\S]*LIVE AND VERIFIED/i.test(catalogArchitecture) && catalogArchitecture.includes(migrationPath));
check("decisions lock Slice 4C operational state", /Decision 0022[\s\S]*Slice 4C[\s\S]*APPROVED/i.test(decisions));
check("build status records Slice 4B and Slice 4C live", /SLICE 4B LIVE \/ COMPLETE[\s\S]*SLICE 4C LIVE \/ VERIFIED/i.test(buildStatus));
check("master plan records Slice 4C live verification gate", /Slice 4C operational state is LIVE \/ READ-ONLY VERIFIED/i.test(masterPlan));
check("architecture records private provider operation boundary", architecture.includes("nutrition_provider_query_cache") && architecture.includes("fmz_phase4_provider_consume_rate_limits"));
check("test matrix includes Slice 4C local gate", /Slice 4C Operational State Schema Local Checks/i.test(testMatrix));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);

if (failed.length) {
  console.error(`Phase 4 Slice 4C static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}

console.log(`Phase 4 Slice 4C static check passed: ${checks.length}`);
