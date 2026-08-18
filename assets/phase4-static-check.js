const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const migration = read("supabase/migrations/20260818_phase4_nutrition_schema_slice1.sql");
const verification = read("supabase/verification/20260818_phase4_nutrition_schema_slice1_verification.sql");
const contract = read("docs/PHASE4_NUTRITION_PRODUCT_CONTRACT_SCHEMA_SLICE1.md");
const phase1 = read("assets/phase1-foundation.js");
const phase2 = read("assets/phase2-home-recovery.js");
const phase3 = read("assets/phase3-training-engine.js");
const memberUx = read("assets/member-ux-consistency.js");

const checks = [];
function check(name, condition) {
  checks.push({ name, condition: Boolean(condition) });
}

const executable = migration.replace(/--.*$/gm, "");
const outsideDollarBodies = executable.replace(/\$\$[\s\S]*?\$\$/g, "$$");
const createdTables = Array.from(
  migration.matchAll(/create table if not exists public\.([a-z_]+)/gi),
  (match) => match[1]
);
const expectedTables = [
  "nutrition_preferences",
  "foods",
  "food_portions",
  "nutrition_targets",
  "food_logs",
  "food_log_items"
];
const expectedColumns = {
  nutrition_preferences: ["user_id", "timezone_name", "created_at", "updated_at"],
  foods: [
    "id", "owner_user_id", "catalog_scope", "canonical_slug", "name", "brand", "barcode",
    "source_provider", "provider_food_id", "source_version", "license_code", "provenance",
    "quality_status", "reference_amount", "reference_unit", "reference_mass_grams",
    "reference_volume_ml", "density_g_per_ml", "energy_kcal", "protein_grams",
    "carbohydrate_grams", "fat_grams", "fiber_grams", "status", "source_updated_at",
    "metadata", "created_at", "updated_at", "archived_at"
  ],
  food_portions: [
    "id", "food_id", "label", "amount", "unit", "equivalent_amount", "equivalent_unit",
    "is_default", "sort_order", "status", "metadata", "created_at", "updated_at", "archived_at"
  ],
  nutrition_targets: [
    "id", "user_id", "target_context", "energy_kcal", "protein_grams", "carbohydrate_grams",
    "fat_grams", "fiber_grams", "source_type", "created_by_user_id", "status", "effective_from",
    "effective_to", "accepted_by_user_id", "accepted_at", "supersedes_target_id", "request_id",
    "notes", "metadata", "created_at", "updated_at", "archived_at"
  ],
  food_logs: [
    "id", "user_id", "log_date", "timezone_name", "timezone_offset_minutes", "target_id",
    "target_energy_kcal_snapshot", "target_protein_grams_snapshot",
    "target_carbohydrate_grams_snapshot", "target_fat_grams_snapshot", "target_fiber_grams_snapshot",
    "status", "source", "metadata", "created_at", "updated_at", "archived_at"
  ],
  food_log_items: [
    "id", "user_id", "food_log_id", "food_id", "food_portion_id", "meal_moment", "sort_order",
    "consumed_quantity", "consumed_unit", "food_name_snapshot", "brand_snapshot",
    "reference_amount_snapshot", "reference_unit_snapshot", "portion_label_snapshot",
    "portion_equivalent_amount_snapshot", "portion_equivalent_unit_snapshot",
    "density_g_per_ml_snapshot", "calculation_basis", "energy_kcal_snapshot",
    "protein_grams_snapshot", "carbohydrate_grams_snapshot", "fat_grams_snapshot",
    "fiber_grams_snapshot", "source_provider_snapshot", "provider_food_id_snapshot",
    "source_version_snapshot", "provenance_snapshot", "notes", "status", "request_id",
    "consumed_at", "metadata", "created_at", "updated_at", "archived_at"
  ]
};
function migrationTableColumns(table) {
  const block = migration.match(new RegExp(`create table if not exists public\\.${table} \\(([\\s\\S]*?)\\n\\);`, "i"));
  if (!block) return [];
  return block[1]
    .split(/\r?\n/)
    .map((line) => line.match(/^  ([a-z][a-z0-9_]*)\s+(?:uuid|text|jsonb|numeric|timestamptz|date|smallint|integer|boolean)\b/i))
    .filter(Boolean)
    .map((match) => match[1]);
}
function verificationColumns(table) {
  const pattern = new RegExp(`\\('${table}', \\d+, '([a-z][a-z0-9_]*)',`, "g");
  return Array.from(verification.matchAll(pattern), (match) => match[1]);
}
const policyBlocks = Array.from(
  migration.matchAll(/create policy[\s\S]*?;/gi),
  (match) => match[0]
).join("\n");
const functionBlocks = Array.from(
  migration.matchAll(/create or replace function public\.(fmz_phase4_[a-z_]+)\([\s\S]*?\$\$;/gi),
  (match) => ({ name: match[1], source: match[0] })
);
const functionByName = new Map(functionBlocks.map((item) => [item.name, item.source]));
const internalFunctions = [
  "fmz_phase4_touch_updated_at",
  "fmz_phase4_sync_archive_state",
  "fmz_phase4_has_full_nutrition_access",
  "fmz_phase4_enforce_custom_food_limit",
  "fmz_phase4_enforce_food_portion_owner",
  "fmz_phase4_enforce_target_owner",
  "fmz_phase4_enforce_food_log_owner",
  "fmz_phase4_enforce_food_log_item_owner",
  "fmz_phase4_day_payload"
];
const publicRpcs = [
  "fmz_phase4_set_nutrition_timezone",
  "fmz_phase4_search_foods",
  "fmz_phase4_upsert_custom_food",
  "fmz_phase4_archive_custom_food",
  "fmz_phase4_upsert_food_portion",
  "fmz_phase4_save_member_target",
  "fmz_phase4_get_current_nutrition_target",
  "fmz_phase4_log_food_item",
  "fmz_phase4_archive_food_log_item",
  "fmz_phase4_get_nutrition_day",
  "fmz_phase4_get_nutrition_history"
];

check("staging project guard is explicit", migration.includes("mokxyyullfhkfalopbzd"));
check("production project ref is absent", !/hgoygcviutmynaihcvpd/i.test(migration + verification));
check("transaction starts exactly once", (executable.match(/^\s*begin\s*;/gim) || []).length === 1);
check("transaction commits exactly once", (executable.match(/^\s*commit\s*;/gim) || []).length === 1 && /commit\s*;\s*$/i.test(executable));
check("exact six approved tables are created", JSON.stringify(createdTables) === JSON.stringify(expectedTables));
check("all six tables have exact approved column order", expectedTables.every((table) => JSON.stringify(migrationTableColumns(table)) === JSON.stringify(expectedColumns[table])));
check("verification column contract matches migration", expectedTables.every((table) => JSON.stringify(verificationColumns(table)) === JSON.stringify(expectedColumns[table])));
check("no top-level seed or backfill insert exists", !/^\s*insert\s+into\b/im.test(outsideDollarBodies));
check("no destructive table or data statement exists", !/\b(truncate|drop\s+(table|column|schema)|delete\s+from)\b/i.test(executable));
check("no legacy table alteration exists", !/alter\s+table\s+public\.(profiles|coach_workspaces|user_settings|user_onboarding|entitlements|recovery_logs|training_plans|training_plan_days|training_plan_exercises|workout_sessions|workout_set_logs|exercises)\b/i.test(executable));
check("no legacy data mutation exists", !/(insert\s+into|update)\s+public\.(profiles|coach_workspaces|user_settings|user_onboarding|entitlements|recovery_logs|training_plans|training_plan_days|training_plan_exercises|workout_sessions|workout_set_logs|exercises)\b/i.test(outsideDollarBodies));
check("all six tables enable RLS", expectedTables.every((table) => migration.includes(`alter table public.${table} enable row level security;`)));
check("no delete policy exists", !/for\s+delete/i.test(policyBlocks));
check("no trainer policy exists", !/trainer_id|linked_trainer|coach_client|trainer.*policy/i.test(policyBlocks));
check("no public sharing policy exists", !/to\s+public|using\s*\(\s*true\s*\)/i.test(policyBlocks));
check("policy defense derives ownership from auth uid", (policyBlocks.match(/auth\.uid\(\)/g) || []).length >= 18);

check("foods is authenticated select only", /revoke all on table public\.foods from authenticated;[\s\S]*?grant select on table public\.foods to authenticated;/i.test(migration));
check("food portions is authenticated select only", /revoke all on table public\.food_portions from authenticated;[\s\S]*?grant select on table public\.food_portions to authenticated;/i.test(migration));
check("preferences has no direct authenticated table grant", /revoke all on table public\.nutrition_preferences from authenticated;/i.test(migration) && !/grant\s+[^;]*on table public\.nutrition_preferences/i.test(migration));
check("targets has no direct authenticated table grant", /revoke all on table public\.nutrition_targets from authenticated;/i.test(migration) && !/grant\s+[^;]*on table public\.nutrition_targets/i.test(migration));
check("logs has no direct authenticated table grant", /revoke all on table public\.food_logs from authenticated;/i.test(migration) && !/grant\s+[^;]*on table public\.food_logs/i.test(migration));
check("log items has no direct authenticated table grant", /revoke all on table public\.food_log_items from authenticated;/i.test(migration) && !/grant\s+[^;]*on table public\.food_log_items/i.test(migration));
check("all tables revoke public anon and authenticated first", expectedTables.every((table) => ["public", "anon", "authenticated"].every((role) => migration.includes(`revoke all on table public.${table} from ${role};`))));
check("no destructive table privileges are granted", !/grant\s+(delete|truncate|references|trigger|maintain)/i.test(migration));

check("all expected functions are present", [...internalFunctions, ...publicRpcs].every((name) => functionByName.has(name)));
check("no unexpected Phase 4 function is present", functionBlocks.length === internalFunctions.length + publicRpcs.length);
check("all Phase 4 functions use safe search path", functionBlocks.every((item) => /set search_path = pg_catalog, public, pg_temp/i.test(item.source)));
check("protected RPCs derive user from auth uid", publicRpcs.filter((name) => name !== "fmz_phase4_search_foods").every((name) => /auth\.uid\(\)/.test(functionByName.get(name) || "")));
check("search RPC is security invoker over RLS", /security invoker/i.test(functionByName.get("fmz_phase4_search_foods") || "") && /from public\.foods/i.test(functionByName.get("fmz_phase4_search_foods") || ""));
check("internal functions have no authenticated execute", internalFunctions.every((name) => new RegExp(`revoke all on function public\\.${name}\\([\\s\\S]*?from authenticated;`, "i").test(migration)));
check("public RPCs revoke public and anon execute", publicRpcs.every((name) => new RegExp(`revoke all on function public\\.${name}\\([\\s\\S]*?from public;[\\s\\S]*?revoke all on function public\\.${name}\\([\\s\\S]*?from anon;`, "i").test(migration)));
check("public RPCs grant authenticated execute", publicRpcs.every((name) => new RegExp(`grant execute on function public\\.${name}\\(`, "i").test(migration)));

const entitlement = functionByName.get("fmz_phase4_has_full_nutrition_access") || "";
check("entitlement full access contains Pro AI and PT", /entitlement_code in \('pro', 'ai', 'personal_coaching'\)/i.test(entitlement));
check("entitlement requires active current window", /e\.status = 'active'/i.test(entitlement) && /e\.starts_at <= now\(\)/i.test(entitlement) && /e\.ends_at is null or e\.ends_at > now\(\)/i.test(entitlement));
check("missing invalid or expired entitlement falls back to Free", /select exists/i.test(entitlement) && !/coalesce\([^)]*true/i.test(entitlement));

const customLimit = functionByName.get("fmz_phase4_enforce_custom_food_limit") || "";
check("custom food limit is ten active own custom rows", /v_active_count >= 10/i.test(customLimit) && /catalog_scope = 'custom'/i.test(customLimit) && /status = 'active'/i.test(customLimit));
check("custom food limit uses per-user transaction lock", /pg_advisory_xact_lock/i.test(customLimit) && /fmz_phase4_custom_food_limit:/i.test(customLimit));
check("custom food owner and scope are immutable", /ownership and catalog scope are immutable/i.test(customLimit));
check("custom food restore route reuses same limit trigger", /before insert or update of owner_user_id, catalog_scope, status on public\.foods/i.test(migration));
check("custom food create retry uses stable object lock and equality replay", (migration.match(/fmz_phase4_custom_food_request:/g) || []).length >= 2 && /custom food UUID already exists; refresh before saving/i.test(migration));
check("custom portion retry serializes by parent food", /fmz_phase4_food_portion_request:/i.test(migration) && /food portion UUID already exists; refresh before saving/i.test(migration));

const history = functionByName.get("fmz_phase4_get_nutrition_history") || "";
const dayRead = functionByName.get("fmz_phase4_get_nutrition_day") || "";
const logWrite = functionByName.get("fmz_phase4_log_food_item") || "";
check("Free history returns seven local calendar days", /generate_series\(0, 6\)/i.test(history) && /'window_days', 7/i.test(history) && /at time zone v_timezone/i.test(history));
check("Free day read blocks older than six previous days", /p_log_date < v_today - 6/i.test(dayRead));
check("Free logging cannot create hidden older history", /p_log_date < v_today - 6/i.test(logWrite));
check("Free idempotent replay cannot expose older history", /if found[\s\S]*v_log\.log_date < v_today - 6[\s\S]*idempotent_replay', true/i.test(logWrite));
check("full history still uses current server entitlement", /fmz_phase4_has_full_nutrition_access/i.test(history));
check("history page size is server bounded", /least\(coalesce\(p_page_size, 14\), 31\)/i.test(history));

const target = functionByName.get("fmz_phase4_save_member_target") || "";
check("target authority is fixed to member daily", /'daily'/i.test(target) && /'member'/i.test(target) && !/p_target_context|p_source_type|p_user_id/i.test(target));
check("target replacement uses per-user daily lock", /fmz_phase4_nutrition_target:/i.test(target) && /pg_advisory_xact_lock/i.test(target));
check("one active target has a partial unique index", /nutrition_targets_one_active_context_uidx[\s\S]*where status = 'active'/i.test(migration));
check("target request identity is unique", /nutrition_targets_user_request_uidx/i.test(migration));

check("supported units are constrained", /reference_unit in \('g', 'ml', 'serving', 'piece'\)/i.test(migration) && /consumed_unit in \('g', 'ml', 'serving', 'piece'\)/i.test(migration));
check("generic liter kilogram conversion is absent", !/1\s*(liter|litre|l)\s*=\s*1\s*(kilogram|kg)/i.test(migration));
check("cross-unit logging requires density or portion", /explicit portion or density conversion required/i.test(logWrite) && /density_g_per_ml/i.test(logWrite));
check("browser cannot supply macro snapshots", !/p_(energy_kcal_snapshot|protein_grams_snapshot|carbohydrate_grams_snapshot|fat_grams_snapshot)/i.test(logWrite));
check("food log snapshots are calculated server-side", /round\(v_food\.energy_kcal \* v_factor, 3\)/i.test(logWrite) && /provenance_snapshot/i.test(logWrite));
check("historical item fields are immutable", /historical food log item snapshots are immutable/i.test(functionByName.get("fmz_phase4_enforce_food_log_item_owner") || ""));
check("Free archive route cannot expose older history", /v_log_date < v_today - 6/i.test(functionByName.get("fmz_phase4_archive_food_log_item") || ""));
check("stable item request identity is unique", /food_log_items_user_request_uidx/i.test(migration));
check("daily log identity is unique", /food_logs_user_date_unique unique \(user_id, log_date\)/i.test(migration));
check("logging has a per-user day lock", /fmz_phase4_food_log:/i.test(logWrite) && /pg_advisory_xact_lock/i.test(logWrite));
check("logging retry serializes by request UUID", /fmz_phase4_food_log_request:/i.test(logWrite));
check("archive retry serializes by item UUID", /fmz_phase4_food_log_item_request:/i.test(functionByName.get("fmz_phase4_archive_food_log_item") || ""));

check("no provider import or remote call exists", !/openfoodfacts|fooddata central|usda|nevo|fetch\(|https?:\/\//i.test(migration));
check("no barcode integration route exists", !/barcode_enabled|scan_barcode|barcode_provider/i.test(migration));
check("no AI implementation exists", !/openai|chat_completion|responses_api|prompt_text/i.test(migration));
check("no trainer access route exists", !/trainer_id|linked_trainer|coach_client/i.test(migration));
check("no service-role or secret reference exists", !/service_role|supabase_service_role|secret_key|sk-/i.test(migration + verification));
check("no production URL exists", !/appfmz\.nl|www\.fitmetzorge\.com/i.test(migration + verification));

const verificationExecutable = verification.replace(/--.*$/gm, "").trim();
check("verification is one CTE SELECT statement", /^with\b[\s\S]*\bselect\b/i.test(verificationExecutable) && /from checks\s*;\s*$/i.test(verificationExecutable));
check("verification has no mutating statement", !/\b(insert\s+into|update\s+public\.|delete\s+from|truncate|alter\s+table|create\s+(table|function|policy|trigger)|drop\s+(table|column|schema)|grant\s+|revoke\s+|call\s+)\b/i.test(verificationExecutable));
check("verification does not execute app RPCs", !/select\s+public\.fmz_phase4_|perform\s+public\.fmz_phase4_/i.test(verificationExecutable));
check("verification uses ACL metadata for public pseudo-role", /aclexplode/i.test(verification) && /acl\.grantee = 0|grantee = 0/i.test(verification) && !/has_function_privilege/i.test(verification));
check("verification casts FK arrays to text arrays", /\)::text\[\] as source_columns/i.test(verification) && /\)::text\[\] as foreign_columns/i.test(verification));
check("verification returns machine-readable overall pass", /'overall_pass', bool_and\(pass\)/i.test(verification) && /jsonb_agg/i.test(verification));
check("verification checks constraint type keys and semantics", /constraint_type_mismatches/i.test(verification) && /key_constraint_mismatches/i.test(verification) && /constraint_semantic_mismatches/i.test(verification));
check("verification checks exact index keys and predicates", /expected_key_expressions/i.test(verification) && /predicate_compact/i.test(verification) && /pg_get_indexdef\(i\.indexrelid, key_position, true\)/i.test(verification));
check("verification reads index direction and null ordering from indoption", /i\.indoption::smallint\[\]/i.test(verification) && /expected_sort_directions/i.test(verification) && /expected_nulls_first/i.test(verification));
check("verification reads index operator classes from catalog metadata", /i\.indclass::oid\[\]/i.test(verification) && /pg_catalog\.pg_opclass/i.test(verification) && /opc\.opcdefault/i.test(verification) && /expected_opclasses/i.test(verification));
check("verification compares index access method and full reconstructed definition", /expected_access_method/i.test(verification) && /pg_catalog\.pg_am/i.test(verification) && /actual_definition/i.test(verification));
check("verification checks policy roles and expressions", /p\.polpermissive/i.test(verification) && /p\.polroles/i.test(verification) && /using_fragments/i.test(verification) && /check_fragments/i.test(verification));
check("verification checks function metadata and source contracts", /a\.language_name is distinct from e\.language_name/i.test(verification) && /a\.provolatile is distinct from e\.volatility/i.test(verification) && /function_source_mismatches/i.test(verification));
check("verification rejects RPC authority parameters", /public_rpc_authority_parameter_mismatches/i.test(verification) && /p_entitlement_code/i.test(verification));
check("verification checks exact trigger event wiring", /t\.tgtype::integer as trigger_type/i.test(verification) && /update_columns/i.test(verification) && /a\.trigger_type is distinct from e\.trigger_type/i.test(verification));
check("verification checks frozen guard columns", /missing_legacy_guard_columns/i.test(verification) && /'coach_workspaces', 'state'/i.test(verification) && /'exercises', 'canonical_slug'/i.test(verification));

check("locked contract still names exact six tables", expectedTables.every((table) => contract.includes(`\`${table}\``)));
check("Phase 1 frozen runtime marker remains", phase1.includes("FMZ_PHASE1_FOUNDATION_LOADED"));
check("Phase 2 frozen runtime marker remains", phase2.includes("FMZ_PHASE2_HOME_RECOVERY_LOADED"));
check("Phase 3 frozen runtime marker remains", phase3.includes("FMZ_PHASE3_TRAINING_ENGINE_LOADED"));
check("Member UX frozen runtime marker remains", memberUx.includes("FMZ_MEMBER_UX_CONSISTENCY_LOADED"));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) {
  console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
}

if (failed.length) {
  console.error(`Phase 4 static check failed: ${failed.length}`);
  process.exit(1);
}

console.log(`Phase 4 static check passed: ${checks.length}`);
