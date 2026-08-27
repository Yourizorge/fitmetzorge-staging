const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");
const bytes = (file) => fs.readFileSync(path.join(root, file));
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const migration = read("supabase/migrations/20260827_phase4_nutrition_slice4fd_transient_off_barcode.sql");
const verifier = read("supabase/verification/20260827_phase4_nutrition_slice4fd_transient_off_barcode_verification.sql");
const handler = read("supabase/functions/nutrition-provider/handler.ts");
const edgeIndex = read("supabase/functions/nutrition-provider/index.ts");
const cryptoSource = read("supabase/functions/nutrition-provider/crypto.ts");
const normalization = read("supabase/functions/nutrition-provider/off-normalization.ts");
const edgeTypes = read("supabase/functions/nutrition-provider/types.ts");
const edgeConstants = read("supabase/functions/nutrition-provider/constants.ts");
const runtime = read("assets/phase4-nutrition-slice3.js");
const app = read("app.js");
const index = read("index.html");
const license = read("assets/vendor/zxing-browser-0.2.1.LICENSE.txt");
const vendorHash = crypto.createHash("sha256").update(bytes("assets/vendor/zxing-browser-0.2.1.min.js")).digest("hex").toUpperCase();
const sql = migration.replace(/^--.*$/gmu, "");
const verifierSql = verifier.replace(/^--.*$/gmu, "").trim();
const verifierExecutable = verifierSql.replace(/'(?:''|[^'])*'/gsu, "''");
const localResolver = migration.slice(
  migration.indexOf("create or replace function public.fmz_phase4_resolve_member_barcode"),
  migration.indexOf("create or replace function public.fmz_phase4_upsert_custom_food_with_barcode")
);
const decodedBarcodeHandler = runtime.slice(
  runtime.indexOf("async function handleDecodedBarcode"),
  runtime.indexOf("async function startNativeBarcodeScanner")
);

check("migration is one transaction", /^\s*begin;/iu.test(sql) && /commit;\s*$/iu.test(sql));
check("migration has exact staging guard", migration.includes("STAGING ONLY: mokxyyullfhkfalopbzd"));
check("migration does not persist runtime OFF products", !/(insert\s+into|update|delete\s+from)\s+public\.nutrition_off_/iu.test(sql));
check("migration does not seed canonical foods", !/insert\s+into\s+public\.foods/iu.test(sql));
check("migration has no destructive member delete", !/delete\s+from\s+public\.(foods|food_logs|food_log_items)/iu.test(sql));
check("migration adds no trainer policy", !/(create\s+policy|grant)[^;]*trainer/iu.test(sql));
check("migration adds no DELETE policy", !/create\s+policy[^;]*for\s+delete/iu.test(sql));
check("provider constraints isolate USDA and OFF", ["nutrition_provider_food_cache_provider_check", "nutrition_provider_rate_buckets_provider_check", "nutrition_provider_runtime_state_provider_check"].every((name) => migration.includes(name)) && migration.includes("provider_code in ('usda_fdc', 'open_food_facts')"));
check("OFF food cache data type is source-bound", migration.includes("provider_code = 'open_food_facts' and provider_data_type = 'off_branded'"));
check("custom barcode uniqueness is archive-aware", migration.includes("foods_active_custom_gtin_owner_uidx") && migration.includes("catalog_scope = 'custom'") && migration.includes("status = 'active'") && migration.includes("fmz_phase4_normalize_gtin14(barcode) is not null"));
check("custom barcode duplicate precheck is explicit", migration.includes("duplicate active custom-food GTINs require owner review before Phase 4F-D") && migration.includes("having count(*) > 1"));
check("local barcode resolver checks permanent OFF first", localResolver.indexOf("from public.nutrition_off_products") < localResolver.indexOf("from public.foods f"));
check("local barcode resolver is service-only", migration.includes("grant execute on function public.fmz_phase4_resolve_member_barcode(uuid,text) to service_role") && !/grant execute on function public\.fmz_phase4_resolve_member_barcode\([^;]+to authenticated/isu.test(migration));
check("custom barcode save owns auth identity", migration.includes("v_user_id uuid := auth.uid()") && migration.includes("custom food does not belong to authenticated user"));
check("custom barcode wrapper is authenticated-only", migration.includes("fmz_phase4_upsert_custom_food_with_barcode") && migration.includes(") to authenticated;"));
check("transient candidate is exact 21-field object", migration.includes("count(*) from pg_catalog.jsonb_object_keys(p_candidate)) <> 21"));
check("transient candidate is OFF source-bound", migration.includes("p_candidate ->> 'provider' is distinct from 'open_food_facts'") && migration.includes("'open_food_facts:' || v_gtin14"));
check("transient candidate has dedicated mapping", migration.includes("phase4_off_barcode_v1") && migration.includes("off_branded"));
check("ODbL identity is enforced", migration.includes("ODbL-1.0") && migration.includes("https://opendatacommons.org/licenses/odbl/1-0/"));
check("NL relevance is enforced", migration.includes("countries_tags") && migration.includes("en:netherlands"));
check("required macros are bounded", migration.includes("v_key = 'energy_kcal_per_100' and v_value > 900") && migration.includes("v_key <> 'energy_kcal_per_100' and v_value > 100"));
check("fiber remains nullable", migration.includes("fiber_grams_per_100") && migration.includes("= 'null'::jsonb"));
check("grams and millilitres remain distinct", migration.includes("p_consumed_unit is distinct from v_reference_unit") && !/(ml\s*=\s*g|g\s*=\s*ml)/iu.test(migration));
check("log and replacement share request lock", migration.includes("fmz_phase4_food_log_request:"));
check("replacement shares archive object lock", migration.includes("fmz_phase4_food_log_item_request:"));
check("idempotent replay compares full immutable request", migration.includes("transient_off_request' is distinct from v_request_payload") && migration.includes("transient_off_replacement_request' is distinct from v_request_payload"));
check("atomic replacement archives original in transaction", migration.includes("update public.food_log_items set status = 'archived'") && migration.includes("atomic replacement rolled back"));
check("changing product can use a fresh trusted candidate", !migration.includes("transient OFF replacement accepts transient OFF snapshots only"));
check("live verifier covers fresh-candidate replacement", verifier.includes("fresh_candidate_can_replace_any_active_own_item"));
check("historical resolver is active-own-item only", migration.includes("active transient OFF food log item is unavailable for this user") && migration.includes("i.status = 'active' and l.status = 'active'"));
check("historical resolver revalidates immutable totals", migration.includes("historical transient OFF snapshot failed immutable identity validation") && migration.includes("energy_kcal_snapshot is distinct from round"));
check("service-only transient mutations", ["fmz_phase4_log_transient_off_food_item", "fmz_phase4_replace_transient_off_food_item", "fmz_phase4_resolve_transient_off_food_log_item"].every((name) => migration.includes(`grant execute on function public.${name}`)) && !/grant execute on function public\.fmz_phase4_(?:log|replace|resolve)_transient_off[^;]+to authenticated/isu.test(migration));
check("internal candidate and mutation functions are non-executable", migration.includes("fmz_phase4_validate_transient_off_candidate(jsonb) from service_role") && migration.includes("fmz_phase4_transient_off_food_item_mutation") && !/grant execute on function public\.fmz_phase4_(?:validate_transient|transient_off_food_item_mutation)/iu.test(migration));

check("Edge exposes exact OFF routes", ["off-barcode", "off-log", "off-replace"].every((route) => handler.includes(`route === \"${route}\"`) || edgeTypes.includes(`\"${route}\"`)));
check("Edge is local-first", handler.indexOf("resolveLocalBarcode") < handler.indexOf("dependencies.off.lookupBarcode"));
check("OFF exact endpoint is product-by-barcode only", edgeConstants.includes("/api/v2/product") && edgeIndex.includes(".json") && !edgeConstants.includes("search.pl"));
check("OFF request sends FitMetZorge User-Agent", edgeConstants.includes("FitMetZorge") && edgeIndex.includes('"user-agent": OFF_USER_AGENT'));
check("OFF request sends no member identity", !/lookupBarcode\([^)]*user/iu.test(edgeIndex));
check("GTIN Mod-10 is server-validated", normalization.includes("normalizeGtin14") && normalization.includes("mod10Valid"));
check("OFF product identity must match exact GTIN", normalization.includes("off_product_identity_mismatch") && normalization.includes("expectedGtin14"));
check("OFF nutrition basis is explicit", normalization.includes("per_100_g") && normalization.includes("per_100_ml"));
check("OFF quantity fallback remains explicit", edgeIndex.includes('"nutrition_data_per"') && normalization.includes('nutritionDataPer === "100g"') && normalization.includes('nutritionDataPer === "100ml"'));
check("OFF quantity sources cannot conflict", normalization.includes('off_product_unit_conflict') && normalization.includes('quantityUnit !== nutritionUnit'));
check("missing macros are not zero-filled", normalization.includes("off_product_incomplete") && normalization.includes("boundedNutrient(nutriments.proteins_100g, 100, true)") && !/\?\?\s*0/iu.test(normalization));
check("remote OFF candidate is signed", handler.includes("signOffCandidateToken") && cryptoSource.includes("signOffCandidateToken"));
check("OFF and USDA token sources cannot cross", cryptoSource.includes("candidate-token-v1") && cryptoSource.includes("candidate-token-v2-off") && cryptoSource.includes("parsed.provider !== OFF_PROVIDER_CODE"));
check("dedicated provider namespace remains locked", edgeConstants.includes("23440733-7e58-4c21-ad15-591eae6ab8ac") && cryptoSource.includes("createOffCandidateId") && cryptoSource.includes("PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE") && !/createOffCandidateId[\s\S]{0,300}PHASE3_EXERCISE_UUID_NAMESPACE/u.test(cryptoSource));
check("short-lived OFF token is enforced", edgeConstants.includes("CANDIDATE_TOKEN_TTL_SECONDS = 15 * 60") && cryptoSource.includes("parsed.expires_at <= nowSeconds"));
check("OFF cache is transient and expiring", handler.includes("transient_off_exact_barcode") && handler.includes("OFF_FOOD_CACHE_TTL_SECONDS"));
check("rate and circuit gates are provider-specific", handler.includes("OFF_PROVIDER_CODE") && handler.includes("enforceOperationalGate") && handler.includes("transitionRuntime"));
check("Edge log uses only trusted candidate snapshot", handler.includes("resolveOffTokenCandidate") && handler.includes("offSnapshot(resolved.candidate)"));
check("historical edit resolves server snapshot", handler.includes("resolveHistoricalOffSnapshot") && handler.includes("resolveTransientOffFoodLogItem"));
check("Edge admin RPCs are server-side only", edgeIndex.includes("fmz_phase4_log_transient_off_food_item") && edgeIndex.includes("fmz_phase4_replace_transient_off_food_item"));

check("scanner is contextual in add-food", runtime.includes("data-phase4-s3-scan-barcode") && runtime.includes("openScanner"));
check("scanner uses native BarcodeDetector first", runtime.includes("window.BarcodeDetector") && runtime.includes("startNativeBarcodeScanner"));
check("scanner has reviewed ZXing fallback", runtime.includes("ZXingBrowser?.BrowserMultiFormatReader") && index.includes("zxing-browser-0.2.1.min.js"));
check("ZXing bundle hash is locked", vendorHash === "066BC34EDFCDD4A33F0964AEEC967752A0DEA1CCAF36E58E319AC9FCB5070F6A");
check("ZXing licence is MIT", /MIT License/iu.test(license));
check("camera starts only from explicit action", runtime.includes("data-phase4-s3-start-camera") && runtime.includes("return startBarcodeScanner()"));
check("camera frames stay local", !/(canvas\.toDataURL|toBlob|image_data|video_frame)/iu.test(runtime));
check("only barcode string reaches OFF route", runtime.includes('providerRequest("off-barcode", { barcode: original, request_id:'));
check("scanner stops all media tracks", runtime.includes("getTracks().forEach((track) => track.stop())"));
check("scanner never auto-logs", decodedBarcodeHandler.includes("await lookupBarcode(value)") && !/(off-log|saveEntry|saveTransientOffEntry)/iu.test(decodedBarcodeHandler));
check("duplicate scanner events are suppressed", runtime.includes("barcodeScannerLocked") && runtime.includes('slice3State.scanner.status === "lookup"'));
check("manual barcode uses the same lookup path", runtime.includes("phase4Slice3BarcodeForm") && runtime.includes('lookupBarcode(new FormData(event.target).get("barcode"))'));
check("local barcode hit reuses frozen flows", runtime.includes('data?.source === "local"') && runtime.includes("openEntry(food") && runtime.includes('openPortal("off"'));
check("transient OFF log uses Edge route", runtime.includes('providerRequest(original ? "off-replace" : "off-log"'));
check("transient UI sends no nutrient fields", !/(candidate_token[\s\S]{0,500}(energy_kcal|protein_grams|carbohydrate_grams|fat_grams))/iu.test(runtime));
check("historical transient edit needs no expired token", runtime.includes("openTransientOffEntry(null, \"\"") && runtime.includes("...(candidateToken ? { candidate_token: candidateToken } : {})"));
check("unknown barcode offers private custom fallback", runtime.includes("createCustomWithBarcode") && runtime.includes("fmz_phase4_upsert_custom_food_with_barcode"));
check("custom barcode is normalized before save", runtime.includes("barcode: normalizeGtin14"));
check("scanner layout is mobile-first", runtime.includes("phase4-s3-scan-sheet") && runtime.includes("94dvh") && runtime.includes("@media (max-width:359px)"));
check("scanner copy exists in NL EN DE", (runtime.match(/scanBarcodeTitle:/gu) || []).length === 3);
check("new cache version is wired", index.includes("20260827-phase4fd-barcode1") && app.includes("20260827-phase4fd-barcode1") && runtime.includes("20260827-phase4fd-barcode1"));
check("no service-role frontend exposure", !/(service[_-]?role|SUPABASE_SERVICE)/iu.test(runtime + app + index));
check("no production project reference", !/(fitmetzorge-production|prod[_-]?supabase|production\.supabase)/iu.test(runtime + app + index + migration));
check("no polling or MutationObserver", !/(MutationObserver|setInterval\s*\()/u.test(runtime));

check("verifier is one read-only SELECT/CTE", /^(with\b|select\b)/iu.test(verifierSql) && /;\s*$/u.test(verifierSql) && (verifierExecutable.match(/;/gu) || []).length === 1);
check("verifier has no DDL or DML", !/\b(insert|update|delete|alter|create|drop|truncate|grant|revoke|call)\b/iu.test(verifierExecutable));
check("verifier checks persistent catalog non-mutation", verifier.includes("no_persistent_catalog_mutation"));
check("verifier checks operational isolation", verifier.includes("operational_table_acl_isolated"));
check("verifier checks frozen RLS", verifier.includes("rls_preserved"));

const failed = checks.filter((entry) => !entry.condition);
for (const entry of checks) console.log(`${entry.condition ? "PASS" : "FAIL"} - ${entry.name}`);
if (failed.length) {
  console.error(`Phase 4F-D static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4F-D static check passed: ${checks.length}`);
