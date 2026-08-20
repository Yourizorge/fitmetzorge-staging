const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) =>
  fs.readFileSync(path.join(root, relativePath), "utf8").replace(/\r\n/gu, "\n");
const migrationPath = "supabase/migrations/20260820134211_phase4_nutrition_slice4d_historical_provider_resolver.sql";
const verificationPath = "supabase/verification/20260820134211_phase4_nutrition_slice4d_historical_provider_resolver_verification.sql";
const migration = read(migrationPath);
const verification = read(verificationPath);
const handler = read("supabase/functions/nutrition-provider/handler.ts");
const index = read("supabase/functions/nutrition-provider/index.ts");
const types = read("supabase/functions/nutrition-provider/types.ts");
const tests = read("supabase/functions/nutrition-provider/nutrition-provider.test.ts");
const combined = [migration, verification, handler, index, types, tests].join("\n");
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

check("migration is staging guarded", migration.includes("STAGING ONLY: mokxyyullfhkfalopbzd"));
check("migration is one transaction", /^--[\s\S]*\nbegin;[\s\S]*\ncommit;\s*$/u.test(migration));
check("migration creates exactly one function", (migration.match(/^create or replace function /gmu) || []).length === 1);
check("resolver exact signature exists", migration.includes("function public.fmz_phase4_resolve_provider_food_log_item(\n  p_user_id uuid,\n  p_original_item_id uuid"));
check("resolver returns only jsonb", migration.includes(")\nreturns jsonb\nlanguage plpgsql"));
check("resolver is stable security definer", migration.includes("stable\nsecurity definer"));
check("resolver fixes safe search path", migration.includes("set search_path = pg_catalog, public, pg_temp"));
check("resolver PUBLIC execute revoked", migration.includes("fmz_phase4_resolve_provider_food_log_item(uuid, uuid)\n  from public;"));
check("resolver anon execute revoked", migration.includes("fmz_phase4_resolve_provider_food_log_item(uuid, uuid)\n  from anon;"));
check("resolver authenticated execute revoked", migration.includes("fmz_phase4_resolve_provider_food_log_item(uuid, uuid)\n  from authenticated;"));
check("resolver service role execute reset and granted", migration.includes("fmz_phase4_resolve_provider_food_log_item(uuid, uuid)\n  from service_role;") && migration.includes("fmz_phase4_resolve_provider_food_log_item(uuid, uuid)\n  to service_role;"));

check("resolver filters exact item and user", migration.includes("i.id = p_original_item_id") && migration.includes("i.user_id = p_user_id") && migration.includes("l.user_id = p_user_id"));
check("resolver requires active item and day", migration.includes("i.status = 'active'") && migration.includes("l.status = 'active'"));
check("resolver rejects canonical and custom rows", migration.includes("v_item.food_id is not null") && migration.includes("v_item.food_portion_id is not null"));
check("resolver requires USDA snapshot", migration.includes("source_provider_snapshot is distinct from 'usda_fdc'"));
check("resolver requires provider food id", migration.includes("provider_food_id_snapshot") && migration.includes("^[1-9][0-9]{0,15}$"));
check("resolver requires UUIDv5 candidate identity", migration.includes("v_candidate_id := (v_metadata ->> 'candidate_id')::uuid") && migration.includes("substring(v_candidate_id::text, 15, 1) <> '5'"));
check("resolver requires fixed mapping version", (migration.match(/phase4_usda_v1/gu) || []).length >= 3);
check("resolver requires reviewed provider data types", ["Foundation", "Survey (FNDDS)", "SR Legacy"].every((value) => migration.includes(value)));
check("resolver requires direct 100 g basis", migration.includes("reference_amount_snapshot is distinct from 100::numeric") && migration.includes("reference_unit_snapshot is distinct from 'g'") && migration.includes("reference_basis' is distinct from 'per_100_g'"));
check("resolver requires transient provider metadata", migration.includes("transient_provider_snapshot") && migration.includes("provider_log") && migration.includes("provider_replace"));
check("resolver cross-checks provenance identity", ["provider_food_id", "candidate_id", "mapping_version", "provider_data_type", "reference_basis"].every((field) => migration.includes(`v_provenance ->> '${field}'`)));
check("resolver requires derivation and attribution", migration.includes("v_provenance -> 'derivation'") && migration.includes("v_provenance -> 'attribution'") && migration.includes("USDA FoodData Central") && migration.includes("CC0 1.0") && migration.includes("https://fdc.nal.usda.gov/"));
check("resolver requires trusted calculation version", migration.includes("calculation_version' is distinct from 'phase4_provider_snapshot_v1'"));
check("resolver cross-checks source version and timestamps", migration.includes("v_metadata_retrieved_at is distinct from v_retrieved_at") && migration.includes("v_metadata_source_updated_at is distinct from v_source_updated_at") && migration.includes("source_version_snapshot") && migration.includes("v_provenance ->> 'source_version'"));
check("resolver validates historical nutrient snapshots", ["energy_kcal_snapshot", "protein_grams_snapshot", "carbohydrate_grams_snapshot", "fat_grams_snapshot", "fiber_grams_snapshot"].every((field) => migration.includes(field)));
check("resolver returns minimum identity only", migration.includes("'provider_food_id', v_provider_food_id") && migration.includes("'candidate_id', v_candidate_id") && migration.includes("'provider_data_type', v_provider_data_type") && !migration.includes("candidate_token"));
check("migration creates no tables columns indexes policies or triggers", !/(create\s+table|alter\s+table|create\s+(?:unique\s+)?index|create\s+policy|create\s+trigger)/iu.test(migration));
check("resolver performs no data writes", !/\b(insert|update|delete|truncate)\b/iu.test(migration.match(/as \$\$[\s\S]*?\$\$/u)?.[0] || ""));
check("resolver performs no canonical promotion", !/(public\.foods|public\.food_portions|public\.food_aliases)/u.test(migration));
check("migration changes no existing provider RPC", !migration.includes("function public.fmz_phase4_log_provider_food_item(") && !migration.includes("function public.fmz_phase4_replace_provider_food_log_item("));

check("replace candidate token is optional only for resolver mode", types.includes("candidateToken: string | null") && handler.includes('"candidate_token" in body'));
check("token mode bypasses resolver orchestration", handler.includes("if (input.candidateToken === null)") && handler.includes("const candidateToken = input.candidateToken ?? await historicalCandidateToken("));
check("tokenless mode resolves by authenticated user and original item", /resolveProviderFoodLogItem\(\s*userId,\s*input\.originalItemId/u.test(handler));
check("replay fallback resolves only supplied replacement item", handler.includes("resolveProviderFoodLogItem(\n          userId,\n          input.replacementItemId"));
check("fallback uses a dedicated internal unavailable error", types.includes("class ActiveProviderItemUnavailableError") && handler.includes("error instanceof ActiveProviderItemUnavailableError"));
check("only exact active-item database denial enables fallback", index.includes('error?.code === "42501"') && index.includes('error.message === "active provider food log item is unavailable for this user"'));
check("fallback resolver denial remains generic forbidden", handler.includes('"provider_replace_forbidden"') && handler.includes('"Provider food logging is not allowed for this request."'));
check("service adapter calls only narrow resolver RPC", index.includes('admin.rpc("fmz_phase4_resolve_provider_food_log_item"') && index.includes("p_user_id: userId") && index.includes("p_original_item_id: originalItemId"));
check("resolver response is revalidated deterministically", handler.includes("identity.candidate_id !== await createCandidateId(identity.provider_food_id)"));
check("historical identity is signed internally only", handler.includes("return await signCandidateToken(") && !index.includes("candidate_token:"));
check("historical mode reuses cache-first lookup", /async function handleReplace[\s\S]*handleLookup/u.test(handler) && /async function handleLookup[\s\S]*getFoodCache/u.test(handler));
check("USDA fallback remains controlled", /async function handleLookup[\s\S]*enforceOperationalGate[\s\S]*dependencies\.usda\.lookup/u.test(handler));
check("provider failure precedes replacement mutation", handler.indexOf("const lookup = await handleLookup(", handler.indexOf("async function handleReplace")) < handler.indexOf("replaceProviderFoodLogItem", handler.indexOf("async function handleReplace")));
check("new food still uses signed token route", tests.includes("changing provider food continues to require a newly signed candidate token"));
check("browser cannot submit provider identity", tests.includes('provider_food_id: "171078"') && handler.includes("Request contains unsupported fields"));
check("browser cannot submit trusted nutrition", !/function parseReplace[\s\S]*energy_kcal/iu.test(handler.match(/function parseReplace[\s\S]*?\n\}\n/u)?.[0] || ""));
check("exact updated_at parser remains precision safe", handler.includes("parseExactIsoTimestamp(") && handler.includes("return timestamp;") && tests.includes("2026-08-20T10:12:34.123456Z"));
check("existing stale response mapping remains", index.includes('code === "40001"') && index.includes("provider_${operation}_stale") && index.includes("409"));
check("no canonical promotion route introduced", !handler.includes("food_aliases") && !handler.includes("food_portions"));

check("cache-hit historical edit test exists", tests.includes("uses a valid cache first"));
check("cache-miss lookup test exists", tests.includes("controlled lookup"));
check("provider unavailable no-mutation test exists", tests.includes("never mutates when provider revalidation is unavailable"));
check("resolver mismatch test exists", tests.includes("must match deterministic provider identity"));
check("historical replay test exists", tests.includes("historical provider replacement replay remains idempotent"));
check("historical replay test models archived original", tests.includes("archivedResolverItems.has(ORIGINAL_ITEM_ID)") && tests.includes("ActiveProviderItemUnavailableError"));
check("historical replay proves replacement resolver fallback", tests.includes("originalItemId: REPLACEMENT_ITEM_ID"));
check("historical replay proves no duplicate replacement row", tests.includes("providerReplacementRows.size, 1"));
check("changed grams meal and notes remain database rejected", tests.includes("delegates changed grams meal and notes to database rejection"));
check("changed provider candidate remains database rejected", tests.includes("cannot change provider candidate under the same request"));
check("wrong replacement and request identities are rejected", tests.includes("rejects wrong replacement and request identities without a third row"));
check("archived and cross-user fallback are rejected", tests.includes("rejects archived and cross-user replacement items"));
check("unexpected resolver failures never trigger fallback", tests.includes("never falls back for unexpected resolver failures"));
check("amount meal notes test coverage exists", tests.includes("Updated historical provider item") && tests.includes("consumedQuantity, 150") && tests.includes('mealMoment, "dinner"'));

check("verifier is one read-only CTE statement", /with[\s\S]*select jsonb_build_object\([\s\S]*from checks;\s*$/u.test(verification));
check("verifier has one terminal statement", (verification.match(/;/gu) || []).length === 1);
check("verifier returns overall_pass", verification.includes("'overall_pass', bool_and(pass)"));
check("verifier checks exact ACL", verification.includes("resolver_service_role_only_execute"));
check("verifier checks active ownership", verification.includes("resolver_active_item_only") && verification.includes("resolver_exact_user_ownership"));
check("verifier checks snapshot identity", verification.includes("resolver_usda_provider_identity") && verification.includes("resolver_snapshot_provenance_validation"));
check("verifier checks read-only resolver", verification.includes("resolver_read_only_no_canonical_promotion"));
check("verifier checks frozen provider RPCs", verification.includes("provider_log_rpc_frozen") && verification.includes("provider_replace_rpc_frozen"));
check("verifier checks Slice 4B/4C guards", verification.includes("slice4b_4c_operational_guards_frozen"));
check("verifier expects the frozen runtime-state table", verification.includes("('nutrition_provider_runtime_state')"));
check("verifier rejects the obsolete circuit-state table name", !verification.includes("nutrition_provider_circuit_state"));
check("verifier preserves all sixteen frozen guard tables", [
  "profiles",
  "coach_workspaces",
  "user_settings",
  "user_onboarding",
  "entitlements",
  "recovery_logs",
  "foods",
  "food_portions",
  "food_aliases",
  "nutrition_targets",
  "food_logs",
  "food_log_items",
  "nutrition_provider_query_cache",
  "nutrition_provider_food_cache",
  "nutrition_provider_rate_buckets",
  "nutrition_provider_runtime_state"
].every((tableName) => new RegExp(`\\('${tableName}'(?:\\s*::text)?\\)`, "u").test(verification)));

check("no production project reference exists", ![migration, handler, index, types, tests].join("\n").includes("hgoygcviutmynaihcvpd"));
check("no embedded JWT-like token exists", !/eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}/u.test(combined));
check("no frontend runtime is referenced", !combined.includes("phase4-nutrition-slice3.js"));
check("no trainer access is introduced", !/(trainer_id|trainer policy|coach_workspaces\.state)/iu.test([migration, handler, index, types].join("\n")));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
if (failed.length) {
  console.error(`Phase 4 historical provider resolver static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4 historical provider resolver static check passed: ${checks.length}`);
