const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const migration = read("supabase/migrations/20260819_phase4_nutrition_slice4d_provider_snapshot_logging.sql");
const verification = read("supabase/verification/20260819_phase4_nutrition_slice4d_provider_snapshot_logging_verification.sql");
const handler = read("supabase/functions/nutrition-provider/handler.ts");
const index = read("supabase/functions/nutrition-provider/index.ts");
const types = read("supabase/functions/nutrition-provider/types.ts");
const tests = read("supabase/functions/nutrition-provider/nutrition-provider.test.ts");
const readme = read("supabase/functions/nutrition-provider/README.md");
const combined = [migration, verification, handler, index, types, tests, readme].join("\n");
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

check("migration is staging guarded", migration.includes("STAGING ONLY: mokxyyullfhkfalopbzd"));
check("migration is one transaction", /^--[\s\S]*\nbegin;[\s\S]*\ncommit;\s*$/u.test(migration));
check("migration has four balanced function bodies", (migration.match(/^create or replace function /gmu) || []).length === 4 && (migration.match(/\$\$/gu) || []).length === 8);
check("provider log RPC exists", migration.includes("function public.fmz_phase4_log_provider_food_item("));
check("provider replace RPC exists", migration.includes("function public.fmz_phase4_replace_provider_food_log_item("));
check("both provider RPCs are security definer", (migration.match(/security definer/gu) || []).length >= 4);
check("safe search path is fixed", (migration.match(/set search_path = pg_catalog, public, pg_temp/gu) || []).length >= 4);
check("service role is the only RPC grantee", [
  "public", "anon", "authenticated", "service_role",
].every((role) => migration.includes(`) from ${role};`)) && (migration.match(/\) to service_role;/gu) || []).length === 2);
check("PUBLIC cannot execute provider RPCs", (migration.match(/fmz_phase4_(?:log|replace)_provider_food[^;]+\) from public;/gsu) || []).length === 2);
check("anon cannot execute provider RPCs", (migration.match(/fmz_phase4_(?:log|replace)_provider_food[^;]+\) from anon;/gsu) || []).length === 2);
check("authenticated cannot execute provider RPCs", (migration.match(/fmz_phase4_(?:log|replace)_provider_food[^;]+\) from authenticated;/gsu) || []).length === 2);

check("food log compatibility uses transaction-local internal context", migration.includes("fmz.phase4_provider_snapshot_user_id") && migration.includes("pg_catalog.set_config("));
check("normal authenticated ownership remains preferred", migration.includes("coalesce(v_authenticated_user_id, v_internal_user_id)"));
check("provider rows require null food identity", migration.includes("if new.food_id is null then") && migration.includes("new.food_portion_id is not null"));
check("canonical/custom trigger path remains present", migration.includes("f.catalog_scope = 'canonical'") && migration.includes("f.catalog_scope = 'custom'"));
check("historical snapshots remain immutable", migration.includes("historical food log item snapshots are immutable"));
check("existing archive function remains unmodified", !migration.includes("create or replace function public.fmz_phase4_archive_food_log_item"));

check("USDA provider is fixed", (migration.match(/'usda_fdc'/gu) || []).length >= 6);
check("mapping version is fixed", migration.includes("phase4_usda_v1"));
check("accepted data types are fixed", ["Foundation", "Survey (FNDDS)", "SR Legacy"].every((value) => migration.includes(value)));
check("grams are the only consumption unit", migration.includes("provider food logging supports grams only") && !migration.includes("p_consumed_unit in ('g', 'ml'"));
check("reference basis is exactly 100 g", migration.includes("'reference_basis', 'per_100_g'") && migration.includes("100, 'g'"));
check("150 g uses quantity over 100 factor", migration.includes("v_factor := p_consumed_quantity / 100"));
check("zero and negative grams are rejected", migration.includes("p_consumed_quantity <= 0"));
check("excess grams are rejected", migration.includes("p_consumed_quantity > 100000"));
check("missing required macro values are rejected", [
  "energy_kcal_per_100g", "protein_grams_per_100g", "carbohydrate_grams_per_100g", "fat_grams_per_100g",
].every((field) => migration.includes(`jsonb_typeof(p_candidate -> '${field}') is distinct from 'number'`)));
check("nutrition bounds mirror provider normalizer", migration.includes("v_kcal > 1500") && ["v_protein > 100", "v_carbohydrates > 100", "v_fat > 100", "v_fiber > 100"].every((part) => migration.includes(part)));
check("candidate identity is validated", migration.includes("v_candidate_id := (p_candidate ->> 'candidate_id')::uuid") && migration.includes("provider_food_id !~"));
check("provider provenance is cross-checked", ["candidate_id", "provider_food_id", "mapping_version", "provider_data_type", "retrieved_at", "source_version", "reference_basis", "derivation", "attribution"].every((field) => migration.includes(`'${field}'`)));
check("snapshot identity is stored", ["source_type", "candidate_id", "mapping_version", "provider_data_type", "retrieved_at", "source_updated_at", "reference_basis"].every((field) => migration.includes(`'${field}'`)));
check("food id and portion id are null on insert", (migration.match(/(?:v_log\.id|v_original\.food_log_id), null, null/gu) || []).length === 2);
check("calculation basis is direct reference", (migration.match(/'direct_reference'/gu) || []).length >= 3);

check("log request lock uses established namespace", migration.includes("fmz_phase4_food_log_request:"));
check("day lock uses established namespace", migration.includes("fmz_phase4_food_log:"));
check("item lock uses established namespace", migration.includes("fmz_phase4_food_log_item_request:"));
check("log replay compares exact payload", migration.includes("provider_request' is distinct from v_request_payload"));
check("changed log request reuse is rejected", migration.includes("provider request UUID was already used with a different payload"));
check("replace replay compares exact payload", migration.includes("provider_replacement_request") && migration.includes("is distinct from v_request_payload"));
check("changed replace request reuse is rejected", migration.includes("provider replacement request UUID was already used with a different payload"));
check("stable request unique index remains assumed not recreated", !migration.includes("drop index") && !migration.includes("drop constraint"));

check("provider replace requires optimistic timestamp", migration.includes("p_expected_original_updated_at") && migration.includes("updated_at is distinct from p_expected_original_updated_at"));
check("provider replace locks original", /p_original_item_id[\s\S]*for update;/u.test(migration));
check("provider replace archives original", migration.includes("set status = 'archived'"));
check("provider replace returns active replacement and archived original", migration.includes("'replacement_item'") && migration.includes("'archived_original'"));
check("provider replace is transaction atomic", migration.includes("atomic replacement rolled back"));
check("amount meal candidate and notes participate in request identity", ["consumed_quantity", "meal_moment", "candidate", "notes"].every((field) => migration.includes(`'${field}'`)));

check("Free seven-day boundary remains server-side", (migration.match(/v_log\.log_date < v_today - 6|p_log_date < v_today - 6/gu) || []).length === 2);
check("full entitlement helper remains authoritative", (migration.match(/fmz_phase4_has_full_nutrition_access/gu) || []).length >= 2);
check("timezone is IANA validated", migration.includes("pg_catalog.pg_timezone_names"));
check("local day uses at time zone", migration.includes("at time zone v_timezone"));
check("same-day replacement reuses original food log", migration.includes("v_original.food_log_id"));
check("authoritative day is returned", (migration.match(/fmz_phase4_day_payload/gu) || []).length >= 5);

check("Edge exposes reviewed log and replace routes", ["log", "replace"].every((route) => handler.includes(`route === "${route}"`)));
check("Edge requires bearer auth before route work", handler.includes("verifyBearer(bearerToken(request))"));
check("Edge exact-object boundary rejects extra fields", handler.includes("exactObject(value") && handler.includes("Request contains unsupported fields"));
check("Edge log body accepts no nutrition fields", !/function parseLog[\s\S]*allowedKeys[\s\S]*(kcal|protein|carbohydrate|fat|fiber)/u.test(handler));
check("Edge log body accepts no user role or entitlement", !/function parseLog[\s\S]*allowedKeys[\s\S]*(user_id|role|entitlement)/u.test(handler));
check("Edge revalidates candidate for log", /async function handleLog[\s\S]*handleLookup/u.test(handler));
check("Edge revalidates candidate for replace", /async function handleReplace[\s\S]*handleLookup/u.test(handler));
check("Edge constructs trusted provider snapshot", handler.includes("function providerSnapshot(candidate: SafeCandidate)"));
check("Edge service adapter derives user from verified auth", index.includes("p_user_id: userId") && !handler.includes("body.user_id"));
check("Edge uses service-role-only RPCs", index.includes('admin.rpc("fmz_phase4_log_provider_food_item"') && index.includes('admin.rpc("fmz_phase4_replace_provider_food_log_item"'));
check("Edge does not expose service role outside adapter", !handler.includes("SERVICE_ROLE") && !types.includes("SERVICE_ROLE"));

check("valid provider log test exists", tests.includes("provider log revalidates the signed candidate"));
check("150 g calculation test exists", tests.includes("energy_kcal_snapshot, 247.5"));
check("invalid gram tests exist", tests.includes("consumed_quantity: 0") && tests.includes("consumed_quantity: -1"));
check("non-gram test exists", tests.includes('consumed_unit: "ml"'));
check("missing macro test exists", tests.includes("missingMacro"));
check("invalid candidate test exists", tests.includes("tamperedResponse"));
check("idempotent retry test exists", tests.includes("retries are idempotent"));
check("changed payload reuse test exists", tests.includes("consumed_quantity: 151"));
check("atomic replace test exists", tests.includes("separate atomic backend mutation contract"));

check("migration has no table creation", !/create\s+table/iu.test(migration));
check("migration has no table removal", !/drop\s+table/iu.test(migration));
check("migration has no row removal", !/\bdelete\s+from\b/iu.test(migration));
check("migration has no canonical food writes", !/(insert\s+into|update)\s+public\.(foods|food_portions|food_aliases)\b/iu.test(migration));
check("no seed or provider import exists", !/(copy\s+public\.|insert\s+into\s+public\.foods)/iu.test(migration));
check("no trainer access path exists", !/(trainer_id|coach_workspaces|trainer policy)/iu.test(migration));
check("no production project ref exists", ![migration, handler, index, types, tests, readme].join("\n").includes("hgoygcviutmynaihcvpd"));
check("no embedded JWT-like secret exists", !/eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}/u.test(combined));

check("verifier is one read-only CTE statement", /with[\s\S]*select jsonb_build_object\([\s\S]*from checks;\s*$/u.test(verification));
check("verifier has one terminal SQL statement", (verification.match(/;/gu) || []).length === 1);
check("verifier returns overall_pass", verification.includes("'overall_pass', bool_and(pass)"));
check("verifier checks exact ACL", verification.includes("provider_functions_acl_service_role_only"));
check("verifier checks exact safe search path", verification.includes("search_path=pg_catalog, public, pg_temp"));
check("verifier normalizes pg_proc source whitespace", (verification.match(/regexp_replace\(/gu) || []).length >= 3 && verification.includes("'[[:space:]]+'") && verification.includes("source_compact"));
check("verifier compact checks preserve member authority", verification.includes("v_user_iduuid:=auth.uid()") && verification.includes("f.owner_user_id=v_user_id") && verification.includes("p.food_id=new.food_id"));
check("verifier compact checks preserve gram contract", verification.includes("p_consumed_unitisdistinctfrom''g''") && verification.includes("v_factor:=p_consumed_quantity/100") && verification.includes("reference_amount''isdistinctfrom''100''"));
check("verifier compact checks preserve idempotency", verification.includes("wherei.user_id=v_user_idandi.request_id=p_request_id") && verification.includes("providerrequestUUIDwasalreadyusedwithadifferentpayload"));
check("verifier compact checks preserve provider bounds", verification.includes("v_kcal<0orv_kcal>1500") && verification.includes("v_provider_data_typenotin") && verification.includes("v_provenance->>''reference_basis''isdistinctfrom''per_100_g''"));
check("verifier compact checks preserve atomic replacement", verification.includes("wherei.id=p_original_item_idandi.user_id=v_user_idforupdate") && verification.includes("updatepublic.food_log_itemssetstatus=''archived''") && verification.includes("atomicreplacementrolledback"));
check("verifier checks nullable food identity", verification.includes("food_log_items_nullable_provider_compatibility"));
check("verifier checks trigger mapping", verification.includes("food_logs_20_enforce_owner") && verification.includes("food_log_items_20_enforce_owner"));
check("verifier checks canonical member writes", verification.includes("canonical_member_write_paths_preserved"));
check("verifier checks provider numeric bounds", verification.includes("provider_numeric_and_snapshot_bounds"));
check("verifier checks archive compatibility", verification.includes("existing_archive_provider_compatible"));
check("verifier locks exact two-argument archive signature", verification.includes("fmz_phase4_archive_food_log_item(uuid,timestamp with time zone)") && verification.includes("argument_types = 'uuid, timestamp with time zone'") && !verification.includes("fmz_phase4_archive_food_log_item(uuid,uuid,timestamp with time zone)"));
check("verifier checks provider day totals", verification.includes("provider_day_payload_compatibility"));
check("verifier checks no canonical promotion", verification.includes("no_canonical_provider_promotion"));
check("verifier checks frozen guards", verification.includes("frozen_guard_tables_present_with_rls") && verification.includes("frozen_function_guards"));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
if (failed.length) {
  console.error(`Phase 4 provider logging static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4 provider logging static check passed: ${checks.length}`);
