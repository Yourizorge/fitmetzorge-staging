const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const migrationPath = "supabase/migrations/20260826143000_phase4_nutrition_slice4fc_off_authoritative_logging.sql";
const verificationPath = "supabase/verification/20260826143000_phase4_nutrition_slice4fc_off_authoritative_logging_verification.sql";
const migration = read(migrationPath);
const verification = read(verificationPath);
const index = read("index.html");
const app = read("app.js");
const runtime = read("assets/phase4-nutrition-slice3.js");
const browser = read("assets/phase4-nutrition-slice3-browser-check.js");

function sqlFunction(source, name, nextName) {
  const start = source.indexOf(`create or replace function public.${name}(`);
  const end = nextName ? source.indexOf(`create or replace function public.${nextName}(`, start + 1) : source.indexOf("revoke all on function", start + 1);
  return start >= 0 && end > start ? source.slice(start, end) : "";
}

function jsFunction(source, name) {
  const marker = `function ${name}(`;
  const start = source.indexOf(marker);
  if (start < 0) return "";
  let depth = 0;
  let opened = false;
  for (let index = start; index < source.length; index += 1) {
    if (source[index] === "{") { depth += 1; opened = true; }
    if (source[index] === "}") {
      depth -= 1;
      if (opened && depth === 0) return source.slice(start, index + 1);
    }
  }
  return "";
}

const resolver = sqlFunction(migration, "fmz_phase4_resolve_off_food_snapshot", "fmz_phase4_enforce_food_log_item_owner");
const guard = sqlFunction(migration, "fmz_phase4_enforce_food_log_item_owner", "fmz_phase4_log_off_food_item");
const logRpc = sqlFunction(migration, "fmz_phase4_log_off_food_item", "fmz_phase4_replace_off_food_log_item");
const replaceRpc = sqlFunction(migration, "fmz_phase4_replace_off_food_log_item");
const saveOff = jsFunction(runtime, "saveOffEntry");
const entryDialog = jsFunction(runtime, "entryDialog");
const itemDialog = jsFunction(runtime, "itemDialog");
const editLoader = jsFunction(runtime, "loadFoodForEdit");

check("migration target is staging only", migration.includes("STAGING ONLY: mokxyyullfhkfalopbzd"));
check("migration is one transaction", /^--[\s\S]*\nbegin;[\s\S]*\ncommit;\s*$/i.test(migration));
check("migration adds no table", !/\bcreate\s+table\b/i.test(migration));
check("migration alters no table", !/\balter\s+table\b/i.test(migration));
check("migration removes no object or data", !/\b(?:drop|truncate|delete\s+from)\b/i.test(migration));
check("migration adds no policy", !/\bcreate\s+policy\b/i.test(migration));
check("migration grants no table privilege", !/grant\s+(?:select|insert|update|delete|all)\s+on\s+(?:table\s+)?/i.test(migration));
check("migration has no production reference", !/(?:hgoygcviutmynaihcvpd|wzsupwcfkkiguuobfevx)/i.test(migration));

check("server resolver exists", Boolean(resolver));
check("server resolver is stable definer", /stable[\s\S]*security definer/i.test(resolver));
check("server resolver has safe search path", resolver.includes("set search_path = pg_catalog, public, pg_temp"));
check("resolver reads OFF products server-side", resolver.includes("from public.nutrition_off_products p"));
check("resolver joins release ledger", resolver.includes("join public.nutrition_off_catalog_releases r"));
check("resolver requires active product", resolver.includes("p.lifecycle_status = 'active'"));
check("resolver requires complete or reviewed quality", resolver.includes("p.quality_status in ('complete', 'reviewed')"));
check("resolver requires current imported lineage", resolver.includes("r.status = 'imported'") && resolver.includes("r.imported_at is not null"));
check("resolver requires all authoritative macros", ["energy_kcal_100", "protein_grams_100", "carbohydrate_grams_100", "fat_grams_100"].every((field) => resolver.includes(`p.${field} is not null`)));
check("resolver keeps source version within immutable snapshot bounds", resolver.includes("char_length(p.off_revision) between 1 and 120"));
check("resolver keeps per-100 g/ml bases separate", resolver.includes("per_100_g") && resolver.includes("per_100_ml") && resolver.includes("then 'ml' else 'g'"));
check("resolver carries provider identity", resolver.includes("p.normalized_gtin14") && resolver.includes("p.provider_identity_name"));
check("resolver carries release identity", resolver.includes("'release_id', p.release_id") && resolver.includes("'mapping_version', r.mapping_version"));
check("resolver carries ODbL license", resolver.includes("'license_code', p.license_code") && resolver.includes("'license_url', p.license_url"));
check("resolver carries attribution", resolver.includes("'attribution_text', p.attribution_text") && resolver.includes("'attribution', jsonb_build_object"));
check("resolver carries immutable provenance", resolver.includes("'source_checksum', p.source_checksum") && resolver.includes("'source_revision', p.off_revision") && resolver.includes("'catalog_provenance', p.provenance"));
check("resolver has no browser user input nutrients", !/p_(?:energy|protein|carbohydrate|fat|fiber)/i.test(resolver));

check("snapshot guard preserves USDA branch", guard.includes("new.source_provider_snapshot = 'usda_fdc'") && guard.includes("phase4_usda_v1"));
check("snapshot guard adds isolated OFF branch", guard.includes("new.source_provider_snapshot = 'open_food_facts'") && guard.includes("fmz.phase4_off_snapshot_user_id"));
check("OFF guard requires authenticated ownership", guard.includes("v_authenticated_user_id is distinct from new.user_id") && guard.includes("v_off_internal_user_id is distinct from new.user_id"));
check("OFF guard only accepts OFF operations", guard.includes("('off_log', 'off_replace')"));
check("OFF guard requires exact source unit", guard.includes("new.consumed_unit is distinct from new.reference_unit_snapshot"));
check("OFF guard rejects portions and density", guard.includes("new.food_portion_id is not null") && guard.includes("new.density_g_per_ml_snapshot is not null"));
check("OFF guard validates ODbL metadata", guard.includes("ODbL-1.0") && guard.includes("https://opendatacommons.org/licenses/odbl/1-0/"));
check("snapshot update remains immutable", guard.includes("historical food log item snapshots are immutable"));

check("OFF log RPC is authenticated definer", logRpc.includes("v_user_id uuid := auth.uid()") && logRpc.includes("security definer"));
check("OFF log RPC has no user-id parameter", !/\bp_user_id\b/.test(logRpc.slice(0, logRpc.indexOf("returns jsonb"))));
check("OFF log RPC accepts product id not nutrients", logRpc.includes("p_off_product_id uuid") && !/p_(?:energy|protein|carbohydrate|fat|fiber)/i.test(logRpc.slice(0, logRpc.indexOf("returns jsonb"))));
check("OFF log RPC resolves catalog authority", logRpc.includes("fmz_phase4_resolve_off_food_snapshot(p_off_product_id)"));
check("OFF log RPC enforces matching g/ml unit", logRpc.includes("p_consumed_unit is distinct from v_reference_unit"));
check("OFF log RPC does not perform density conversion", !/p_density_g_per_ml|density_g_per_ml_snapshot\s*\*|\/\s*[^;\n]*density_g_per_ml/i.test(logRpc) && logRpc.includes("density_g_per_ml_snapshot") && logRpc.includes("null,"));
check("OFF log RPC uses reference factor", logRpc.includes("v_factor := p_consumed_quantity / 100"));
check("OFF log RPC uses shared request lock", logRpc.includes("fmz_phase4_food_log_request:"));
check("OFF log RPC uses shared day lock", logRpc.includes("fmz_phase4_food_log:"));
check("OFF log RPC stores equality replay request", logRpc.includes("'off_request', v_request_payload") && logRpc.includes("'idempotent_replay', true"));
check("OFF log RPC enforces local day", logRpc.includes("pg_timezone_names") && logRpc.includes("p_consumed_at at time zone v_timezone"));
check("OFF log RPC preserves seven-day Free boundary", logRpc.includes("p_log_date < v_today - 6") && logRpc.includes("fmz_phase4_has_full_nutrition_access"));
check("OFF log RPC returns authoritative day", logRpc.includes("fmz_phase4_day_payload(v_user_id, p_log_date)"));
check("OFF log RPC creates immutable snapshot row", logRpc.includes("insert into public.food_log_items") && logRpc.includes("'open_food_facts'"));

check("OFF replace RPC is authenticated definer", replaceRpc.includes("v_user_id uuid := auth.uid()") && replaceRpc.includes("security definer"));
check("OFF replace RPC accepts any own active original", replaceRpc.includes("where i.id = p_original_item_id and i.user_id = v_user_id") && !replaceRpc.includes("v_original.source_provider_snapshot is distinct from"));
check("OFF replace RPC uses shared request and object locks", replaceRpc.includes("fmz_phase4_food_log_request:") && replaceRpc.includes("fmz_phase4_food_log_item_request:"));
check("OFF replace RPC guards optimistic timestamp", replaceRpc.includes("v_original.updated_at is distinct from p_expected_original_updated_at"));
check("OFF replace RPC resolves selected product server-side", replaceRpc.includes("fmz_phase4_resolve_off_food_snapshot(p_off_product_id)"));
check("OFF replace RPC enforces source basis", replaceRpc.includes("p_consumed_unit is distinct from v_reference_unit") && replaceRpc.includes("v_factor := p_consumed_quantity / 100"));
check("OFF replace RPC inserts then archives atomically", replaceRpc.indexOf("insert into public.food_log_items") < replaceRpc.indexOf("update public.food_log_items") && replaceRpc.includes("atomic replacement rolled back"));
check("OFF replace RPC stores equality replay request", replaceRpc.includes("'off_replacement_request', v_request_payload") && replaceRpc.includes("'idempotent_replay', true"));
check("OFF replace RPC returns authoritative day", replaceRpc.includes("fmz_phase4_day_payload(v_user_id, v_log.log_date)"));

check("resolver is not executable by browser", migration.includes("fmz_phase4_resolve_off_food_snapshot(uuid) from authenticated"));
check("trigger function is not directly executable", migration.includes("fmz_phase4_enforce_food_log_item_owner() from authenticated"));
check("only OFF write RPCs are granted authenticated", migration.includes("fmz_phase4_log_off_food_item(") && migration.includes("fmz_phase4_replace_off_food_log_item(") && (migration.match(/\) to authenticated;/g) || []).length === 2);
check("anon PUBLIC service role are revoked", ["from public;", "from anon;", "from service_role;"].every((clause) => migration.includes(clause)));

check("runtime preserves 4F-C under the 4F-D successor", runtime.includes('PHASE4_SLICE3_VERSION = "20260827-phase4fd-barcode1"'));
check("index serves the reviewed 4F-D cache", index.includes('app.js?v=20260827-phase4fd-barcode1'));
check("app loads the reviewed 4F-D runtime cache", app.includes('assets/phase4-nutrition-slice3.js?v=20260827-phase4fd-barcode1'));
check("runtime recognizes OFF snapshots separately", runtime.includes("function isOffSnapshot(") && runtime.includes('source_provider_snapshot === "open_food_facts"'));
check("OFF detail keeps explicit selection", runtime.includes("data-phase4-s3-use-off") && runtime.includes("function openOffEntry("));
check("OFF entry respects product unit", entryDialog.includes("food?.reference_unit || item?.reference_unit_snapshot") && entryDialog.includes("offUnitOnly"));
check("OFF entry renders ODbL attribution", entryDialog.includes("offAttribution"));
check("runtime uses dedicated OFF log RPC", saveOff.includes('rpc("fmz_phase4_log_off_food_item"'));
check("runtime uses dedicated OFF replace RPC", saveOff.includes('rpc("fmz_phase4_replace_off_food_log_item"'));
check("runtime sends no nutrient fields", !/(?:p_energy|p_protein|p_carbohydrate|p_fat|p_fiber)/.test(saveOff));
check("runtime submits selected OFF identity", saveOff.includes("p_off_product_id: offProductId"));
check("runtime preserves stable retries", saveOff.includes("prepareSubmission(kind, fingerprint)") && saveOff.includes("resetSubmission(kind)"));
check("runtime handles stale edits", saveOff.includes('code === "40001"') && saveOff.includes("loadDay(true)"));
check("historical OFF rendering is source-aware", itemDialog.includes("isOffSnapshot(item)") && itemDialog.includes("offHistorical") && itemDialog.includes("offAttribution"));
const offEditBranch = editLoader.slice(editLoader.indexOf("if (isOffSnapshot(item))"), editLoader.indexOf("if (!item?.food_id"));
check("historical OFF edit avoids browser nutrient reconstruction", offEditBranch.includes("metadata?.off_product_id") && !/(?:energy_kcal|protein_grams|carbohydrate_grams|fat_grams|fiber_grams)/.test(offEditBranch));
check("archive still uses frozen RPC", runtime.includes('rpc("fmz_phase4_archive_food_log_item"'));
check("custom and generic logging remain", runtime.includes('rpc("fmz_phase4_log_food_item"') && runtime.includes('rpc("fmz_phase4_replace_food_log_item"'));
check("USDA provider logging remains", runtime.includes('providerRequest(original ? "replace" : "log"'));

check("browser covers OFF log retry", browser.includes("OFF log retry preserves stable identities"));
check("browser covers no nutrient authority", browser.includes("OFF log sends only product identity and no browser nutrients"));
check("browser covers authoritative totals", browser.includes("OFF authoritative ml snapshot updates day total"));
check("browser covers historical source", browser.includes("OFF historical detail preserves source and attribution"));
check("browser covers same-product edit", browser.includes("same OFF product edit is atomic and idempotent"));
check("browser covers changing-product edit", browser.includes("changing OFF product uses atomic replacement"));
check("browser covers archive/history", browser.includes("OFF archive removes active intake but preserves history"));
check("browser covers phone targets", browser.includes("390, height: 844") && browser.includes("320, height: 700"));

check("verifier is one WITH/SELECT statement", /^--[\s\S]*\nwith\s/i.test(verification) && /\nselect\s+jsonb_pretty\(/i.test(verification) && (verification.match(/;\s*$/g) || []).length === 1);
check("verifier does not invoke application RPCs", !/select\s+(?:public\.)?fmz_phase4_(?:log|replace|archive|resolve)/i.test(verification));
check("verifier has null-safe overall pass", verification.includes("'overall_pass', coalesce(bool_and(coalesce(passed, false)), false)"));
check("verifier checks locked catalog counts", ["24458", "74184", "20355", "4103", "64", "197"].every((value) => verification.includes(value)));
check("verifier checks ACL and RLS", verification.includes("function_acl") && verification.includes("rls_remains_enabled"));
check("verifier uses the live Slice 4E ingestion ledger name", verification.includes("nutrition_food_ingestions") && !verification.includes("food_catalog_ingestions"));
check("verifier checks frozen logging", verification.includes("frozen_logging_functions_present"));

check("no browser service role", !/service[_-]?role/i.test(runtime));
check("no production reference", !/(?:hgoygcviutmynaihcvpd|wzsupwcfkkiguuobfevx)/i.test(runtime + migration + verification));
check("no AI or direct upstream provider call added", !/(?:openai|anthropic|gemini|youri[_-]?ai)/i.test(runtime) && !/(?:api\.openfoodfacts|world\.openfoodfacts|api\.nal\.usda)/i.test(runtime));
check("no MutationObserver", !runtime.includes("MutationObserver"));
check("no polling", !/setInterval\s*\(/.test(runtime));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
if (failed.length) {
  console.error(`Phase 4F-C static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4F-C static check passed: ${checks.length}`);
