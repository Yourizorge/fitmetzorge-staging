const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const runtime = read("assets/phase4-nutrition-slice3.js");
const app = read("app.js");
const index = read("index.html");
const edge = read("supabase/functions/nutrition-provider/handler.ts");
const edgeIndex = read("supabase/functions/nutrition-provider/index.ts");
const edgeCrypto = read("supabase/functions/nutrition-provider/crypto.ts");
const edgeTypes = read("supabase/functions/nutrition-provider/types.ts");
const edgeConstants = read("supabase/functions/nutrition-provider/constants.ts");
const offNormalization = read("supabase/functions/nutrition-provider/off-normalization.ts");
const verifier = read("supabase/verification/20260831_phase4_nutrition_4fe_final_verification.sql");
const sql = verifier.replace(/^--.*$/gmu, "").trim();
const executable = sql.replace(/'(?:''|[^'])*'/gsu, "''");
const nativeScannerSource = runtime.slice(
  runtime.indexOf("async function startNativeBarcodeScanner"),
  runtime.indexOf("async function startZxingBarcodeScanner")
);
const zxingScannerSource = runtime.slice(
  runtime.indexOf("async function startZxingBarcodeScanner"),
  runtime.indexOf("async function startBarcodeScanner")
);
const scannerSource = nativeScannerSource + zxingScannerSource;

check("4F-E verifier is one SELECT/CTE", /^(with\b|select\b)/iu.test(sql) && (executable.match(/;/gu) || []).length === 1);
check("4F-E verifier is read-only", !/\b(insert|update|delete|alter|create|drop|truncate|grant|revoke|call|execute)\b/iu.test(executable));
check("4F-E verifier targets staging only", verifier.includes("mokxyyullfhkfalopbzd") && !verifier.includes("hgoygcviutmynaihcvpd"));
check("4F-E verifier covers RLS and ACL", verifier.includes("rls_enabled_on_all_nutrition_tables") && verifier.includes("browser_table_acl_minimal"));
check("4F-E verifier covers cross-owner integrity", verifier.includes("log_parent_and_snapshot_integrity") && verifier.includes("cross_owner_rows"));
check("4F-E verifier covers entitlements", verifier.includes("free_history_and_full_entitlements_frozen"));
check("4F-E verifier covers Dutch identity pairs", ["kipfilet rauw", "rijst droog", "pasta droog", "aardappel rauw"].every((value) => verifier.includes(value)));
check("4F-E verifier covers frozen catalog counts", verifier.includes("24458") && verifier.includes("74184") && verifier.includes("20355") && verifier.includes("4103") && verifier.includes("canonical_foods = 64") && verifier.includes("active_aliases = 197"));
check("4F-E verifier covers OFF identity and ODbL", verifier.includes("off_identity_and_required_macros") && verifier.includes("off_odbl_provenance_complete"));
check("4F-E verifier covers authoritative totals", verifier.includes("authoritative_totals_use_snapshots"));
check("4F-E verifier covers idempotency and units", verifier.includes("off_logging_is_idempotent_atomic_and_unit_safe"));

check("runtime keeps stable unified-search input", runtime.includes("renderSearchResults") && runtime.includes('#phase4Slice3SearchForm input[name="query"]'));
check("runtime keeps bounded debounce", runtime.includes("localSearchDebounceTimer") && runtime.includes("providerSearchDebounceTimer") && runtime.includes("PHASE4_LOCAL_SEARCH_DEBOUNCE_MS") && runtime.includes("PHASE4_PROVIDER_SEARCH_DEBOUNCE_MS"));
check("runtime keeps stale provider suppression", runtime.includes("search.requestToken !== requestToken") && runtime.includes("provider.requestToken !== requestToken"));
check("runtime keeps grouped local and provider results", runtime.includes("localResults") && runtime.includes("providerResults"));
check("runtime preserves authoritative day refresh", runtime.includes("await loadDay(true)") && runtime.includes("acceptAuthoritativeDay"));
check("runtime exposes four meal moments", ["breakfast", "lunch", "dinner", "snacks"].every((value) => runtime.includes(value)));
check("runtime preserves archive instead of delete", runtime.includes("fmz_phase4_archive_food_log_item") && !/\.from\(["']food_log_items["']\)\s*\.delete/isu.test(runtime));
check("runtime preserves canonical logging RPC", runtime.includes("fmz_phase4_log_food_item"));
check("runtime preserves atomic canonical replacement", runtime.includes("fmz_phase4_replace_food_log_item"));
check("runtime preserves OFF log and replacement", runtime.includes("fmz_phase4_log_off_food_item") && runtime.includes("fmz_phase4_replace_off_food_log_item"));
check("runtime preserves provider log and replacement", runtime.includes('providerRequest(original ? "replace" : "log"'));
check("browser sends no nutrient authority to OFF log", !/off_product_id[\s\S]{0,300}(energy_kcal|protein_grams|carbohydrate_grams|fat_grams)/u.test(runtime));
check("browser sends no nutrient authority to transient OFF", runtime.includes('providerRequest(original ? "off-replace" : "off-log"') && !/providerRequest\(original \? "off-replace" : "off-log"[\s\S]{0,400}(energy_kcal|protein_grams|carbohydrate_grams|fat_grams)/u.test(runtime));
check("scanner supports only approved 1D formats", ["ean_13", "ean_8", "upc_a", "itf"].every((value) => runtime.includes(value)) && !runtime.includes('"qr_code"'));
check("scanner uses 120 ms cadence", runtime.includes("delayBetweenScanAttempts: 120") && runtime.includes("delayBetweenScanSuccess: 120"));
check("scanner requests rear camera and bounded HD", runtime.includes('facingMode: { ideal: "environment" }') && runtime.includes("width: { ideal: 1280, max: 1920 }") && runtime.includes("height: { ideal: 720, max: 1080 }"));
check("scanner autofocus is optional and continuous", runtime.includes('focusMode.includes("continuous")') && runtime.includes('focusMode: "continuous"'));
check("scanner frames remain local", !/(fetch\s*\(|providerRequest\s*\(|XMLHttpRequest|canvas\.toDataURL|canvas\.toBlob|ImageCapture|storage\.from)/u.test(scannerSource));
check("scanner duplicate suppression remains", runtime.includes("scanner.lastDecoded") && runtime.includes("barcodeScannerLocked") && runtime.includes("scanner.submittedBarcode"));
check("manual and camera use canonical GTIN", runtime.includes("handleDecodedBarcode") && runtime.includes("normalizeGtin14"));
check("SPA incomplete package uses trusted local alternatives", runtime.includes("suggested_query") && runtime.includes("barcodeAlternativeResults"));

check("Edge validates bearer user", edgeIndex.includes("verifier.auth.getUser(token)") && edgeIndex.includes("Authorization: `Bearer ${token}`"));
check("Edge routes remain bounded", ["search", "lookup", "log", "replace", "off-barcode", "off-log", "off-replace"].every((value) => edge.includes(`\"${value}\"`)));
check("Edge keeps fixed OFF host", edgeConstants.includes("world.openfoodfacts.org") || edge.includes("world.openfoodfacts.org"));
check("Edge keeps fixed USDA host", edgeConstants.includes("api.nal.usda.gov") || edge.includes("api.nal.usda.gov"));
check("Edge uses abort bounds", edge.includes("AbortController") && edge.includes("abort"));
check("Edge candidate validation is source-bound", offNormalization.includes("createOffCandidateId(normalizedGtin14)") && edgeCrypto.includes("offCandidateIdentityName") && edgeCrypto.includes("`${OFF_PROVIDER_CODE}:${normalizedGtin14}`"));
check("Edge does not expose service role to browser", !/(service[_-]?role|SUPABASE_SERVICE_ROLE)/iu.test(runtime + app + index));
check("frontend has no production ref", !/(hgoygcviutmynaihcvpd|fitmetzorge-production)/iu.test(runtime + app + index));
check("frontend has no MutationObserver or polling", !/(MutationObserver|setInterval\s*\()/u.test(runtime));
check("frontend has no AI or provider secret", !/(OPENAI|ANTHROPIC|GEMINI|USDA_FDC_API_KEY|FMZ_PROVIDER_HMAC_KEY)/u.test(runtime + app + index));
check("provider types preserve explicit g ml basis", edgeTypes.includes("per_100_g") && edgeTypes.includes("per_100_ml"));
check("no ml equals g conversion", !/(ml\s*=\s*g|g\s*=\s*ml|1\s*ml\s*=\s*1\s*g)/iu.test(runtime + edge + offNormalization));
check("owner barcode cache version remains live", runtime.includes("20260827-phase4fd-owner-barcode1") && app.includes("20260827-phase4fd-owner-barcode1") && index.includes("20260827-phase4fd-owner-barcode1"));

const failed = checks.filter((entry) => !entry.condition);
for (const entry of checks) console.log(`${entry.condition ? "PASS" : "FAIL"} - ${entry.name}`);
if (failed.length) {
  console.error(`Phase 4F-E static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4F-E static check passed: ${checks.length}`);
