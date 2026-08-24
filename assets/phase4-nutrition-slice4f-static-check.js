const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const migrationPath = "supabase/migrations/20260824113551_phase4_nutrition_slice4f_off_catalog_search.sql";
const verifierPath = "supabase/verification/20260824113551_phase4_nutrition_slice4f_off_catalog_search_verification.sql";
const migration = read(migrationPath);
const verifier = read(verifierPath);
const decisions = read("docs/DECISIONS.md");
const architecture = read("docs/ARCHITECTURE.md");
const masterPlan = read("docs/MASTER_BUILD_PLAN.md");
const slice4fDoc = read("docs/PHASE4_NUTRITION_SLICE4F_OFF_CATALOG.md");
const withoutComments = migration.replace(/^\s*--.*$/gmu, "");
const verifierWithoutComments = verifier.replace(/^\s*--.*$/gmu, "").trim();
const PROVIDER_NAMESPACE = "23440733-7e58-4c21-ad15-591eae6ab8ac";

const uuidBytes = (value) => Buffer.from(value.replaceAll("-", ""), "hex");
const formatUuid = (value) => {
  const hex = Buffer.from(value).toString("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
};
const uuidV5 = (namespace, name) => {
  const digest = crypto.createHash("sha1").update(uuidBytes(namespace)).update(Buffer.from(name, "utf8")).digest();
  digest[6] = (digest[6] & 0x0f) | 0x50;
  digest[8] = (digest[8] & 0x3f) | 0x80;
  return formatUuid(digest.subarray(0, 16));
};
const normalizeGtin14 = (barcode) => {
  if (!/^(?:\d{8}|\d{12}|\d{13}|\d{14})$/u.test(barcode)) return null;
  const normalized = barcode.padStart(14, "0");
  let sum = 0;
  for (let index = 0; index < 13; index += 1) sum += Number(normalized[index]) * (index % 2 === 0 ? 3 : 1);
  return Number(normalized[13]) === (10 - (sum % 10)) % 10 ? normalized : null;
};

check("migration is one transaction", /^\s*begin;/iu.test(withoutComments) && /commit;\s*$/iu.test(withoutComments));
check("migration targets staging only in header", migration.includes("STAGING ONLY: mokxyyullfhkfalopbzd"));
check("migration creates exactly the three OFF tables", (migration.match(/create table if not exists public\.nutrition_off_/giu) || []).length === 3);
check("release ledger is separate", migration.includes("public.nutrition_off_catalog_releases"));
check("OFF products are separate", migration.includes("public.nutrition_off_products"));
check("localized names are separate", migration.includes("public.nutrition_off_product_names"));
check("public foods schema is not altered", !/alter\s+table\s+public\.foods\b/iu.test(withoutComments));
check("public foods are never seeded", !/insert\s+into\s+public\.foods\b/iu.test(withoutComments));
check("no member log schema or write is added", !/(insert\s+into\s+public\.food_log|update\s+public\.food_log|alter\s+table\s+public\.food_log)/iu.test(withoutComments));

const barcodeVectors = [
  ["96385074", "00000096385074", "4ef1d24f-f2b1-5fdf-ac5d-da0fef1754c6"],
  ["036000291452", "00036000291452", "126f13e7-303c-5f20-9266-01e7544b00f9"],
  ["4006381333931", "04006381333931", "746f197f-769c-56ef-9e88-a0d52a9d6041"],
  ["10012345000017", "10012345000017", "4709b8e3-145b-52d2-b83e-b3e1ac1f7343"]
];
for (const [input, normalized, expectedId] of barcodeVectors) {
  check(`${input}: valid GTIN normalization`, normalizeGtin14(input) === normalized);
  check(`${input}: deterministic OFF UUIDv5`, uuidV5(PROVIDER_NAMESPACE, `open_food_facts:${normalized}`) === expectedId);
}
check("invalid check digit rejects", normalizeGtin14("4006381333932") === null);
check("unsupported barcode length rejects", normalizeGtin14("123456789") === null);
check("leading zero representation is preserved", normalizeGtin14("036000291452") === "00036000291452");
check("provider namespace is exact", migration.includes(PROVIDER_NAMESPACE));
check("provider identity prefix is exact", migration.includes("'open_food_facts:' || normalized_gtin14"));
check("UUIDv5 is database enforced", migration.includes("id = public.fmz_phase4_provider_candidate_uuid_v5(provider_identity_name)"));
check("UUIDv5 version and variant bits are set", migration.includes("& 15) | 80") && migration.includes("& 63) | 128"));
check("Phase 3 namespace is absent", !migration.includes("9439f2af-0e84-5e41-9482-d4b6765154ed"));
check("catalog search text has one immutable normalizer", migration.includes("function public.fmz_phase4_normalize_catalog_text") && migration.includes("v_query text := public.fmz_phase4_normalize_catalog_text"));
check("brand normalization is derived from brand", migration.includes("normalized_brand = public.fmz_phase4_normalize_catalog_text(brand)"));
check("search-name normalization is derived from name", migration.includes("normalized_name = public.fmz_phase4_normalize_catalog_text(name)"));

check("normalized GTIN is unique", migration.includes("constraint nutrition_off_products_gtin_key unique (normalized_gtin14)"));
check("provider identity name is unique", migration.includes("constraint nutrition_off_products_identity_name_key unique (provider_identity_name)"));
check("duplicate conflict can be quarantined", migration.includes("quality_status in ('incomplete', 'complete', 'reviewed', 'quarantined')") && migration.includes("metadata ? 'quarantine_reason'"));
check("release import count matches loggable rows", migration.includes("imported count must equal active loggable products"));
check("only one current imported release", migration.includes("nutrition_off_releases_current_uidx") && migration.includes("where status = 'imported'"));
check("release lifecycle is forward-only", migration.includes("invalid OFF release status transition") && migration.includes("use a successor release"));
check("name rows match product revision and licence", migration.includes("must match its product source revision and licence"));
check("one preferred active name per product and language", migration.includes("nutrition_off_product_names_preferred_uidx"));

check("100 g and 100 ml bases are distinct", migration.includes("nutrition_basis in ('per_100_g', 'per_100_ml')"));
check("no ml-equals-g conversion", !/(1\s*ml\s*=\s*1\s*g|density conversion|per_100_ml[^\n]+per_100_g)/iu.test(migration));
for (const column of ["energy_kcal_100", "protein_grams_100", "carbohydrate_grams_100", "fat_grams_100"]) {
  check(`${column}: required for loggable quality`, new RegExp(`${column} is not null`, "iu").test(migration));
}
check("energy bounds are safe", migration.includes("energy_kcal_100 between 0 and 900"));
check("macro bounds are safe", ["protein_grams_100", "carbohydrate_grams_100", "fat_grams_100"].every((name) => migration.includes(`${name} between 0 and 100`)));
check("fiber remains nullable", /fiber_grams_100 numeric\(10,3\),/iu.test(migration));
check("incomplete and quarantined are not search-authoritative", migration.includes("quality_status in ('complete', 'reviewed')") && !migration.includes("quality_status in ('complete', 'reviewed', 'incomplete')"));
check("archived OFF rows are excluded", migration.includes("lifecycle_status = 'active'"));

check("RLS enabled on all OFF tables", (migration.match(/alter table public\.nutrition_off_[a-z_]+ enable row level security;/giu) || []).length === 3);
check("only two catalog SELECT policies are created", (migration.match(/create policy/giu) || []).length === 2 && !/for\s+(insert|update|delete)/iu.test(migration));
check("authenticated tables are SELECT-only", (migration.match(/grant select on table public\.nutrition_off_/giu) || []).length === 2 && !/grant\s+(insert|update|delete|truncate|references|trigger)/iu.test(migration));
check("anon and PUBLIC are revoked", migration.includes("from anon") && migration.includes("from public"));
check("service role has no direct OFF table grant", migration.includes("from service_role") && !/grant\s+.+\s+to\s+service_role/iu.test(migration));
check("no trainer policy or grant", !/(create policy[^;]*trainer|grant[^;]*trainer)/iu.test(migration));
check("no DELETE policy", !/create policy[^;]*for delete/iu.test(migration));

check("frozen search RPC is not replaced", !migration.includes("create or replace function public.fmz_phase4_search_foods("));
check("new typed search RPC exists", migration.includes("create or replace function public.fmz_phase4_search_nutrition_catalog("));
for (const sourceType of ["custom_food", "off_branded_food", "generic_food"]) {
  check(`typed search preserves ${sourceType}`, migration.includes(`'${sourceType}'`));
}
for (const returnField of ["result_type text", "source_provider text", "source_id uuid", "barcode text", "display_name text", "nutrition_basis text", "loggable boolean", "rank_tier integer", "rank_score numeric", "cursor_id uuid"]) {
  check(`typed search returns ${returnField}`, migration.includes(returnField));
}
const rankingOrder = [
  "exact_off_barcode_candidates", "exact_custom_name_candidates", "exact_off_nl_name_candidates",
  "exact_off_other_name_candidates", "exact_off_brand_candidates", "exact_generic_alias_candidates",
  "prefix_off_name_candidates", "prefix_generic_alias_candidates", "trigram_off_name_candidates",
  "trigram_generic_alias_candidates"
].map((name) => migration.indexOf(`${name} as (`));
check("ranking branches are present in deterministic order", rankingOrder.every((position, index) => position >= 0 && (index === 0 || position > rankingOrder[index - 1])));
check("every candidate branch is bounded", (migration.match(/_candidates as \(/gu) || []).length === 17 && (migration.match(/\n\s+limit (?:1|25|100|150|200)\r?\n/gu) || []).length === 15);
check("global candidate cap is bounded", migration.includes("limit 1000"));
check("page size is capped at 25", migration.includes("least(coalesce(p_page_size, 25), 25)"));
check("keyset cursor is complete", migration.includes("complete catalog cursor required") && migration.includes("p_after_rank") && migration.includes("p_after_id"));
check("OFFSET pagination is absent", !/\boffset\b/iu.test(withoutComments));
check("prefix and trigram indexes exist", migration.includes("text_pattern_ops") && migration.includes("gin_trgm_ops"));
check("exact GTIN B-tree path exists", migration.includes("nutrition_off_products_gtin_key"));

check("local exact barcode RPC exists", migration.includes("fmz_phase4_lookup_off_product_by_barcode"));
check("barcode lookup is authenticated and read-only", migration.includes("authenticated user required") && !/insert|update|delete/iu.test(migration.slice(migration.indexOf("create or replace function public.fmz_phase4_lookup_off_product_by_barcode"), migration.indexOf("revoke all on table"))));
check("barcode lookup has no provider call", !/(openfoodfacts\.org|fetch\(|http_request)/iu.test(migration));
check("barcode lookup quality gates rows", migration.slice(migration.indexOf("create or replace function public.fmz_phase4_lookup_off_product_by_barcode")).includes("quality_status in ('complete', 'reviewed')"));

check("ODbL release metadata is mandatory", migration.includes("license_code text not null default 'ODbL-1.0'") && migration.includes("attribution_text text not null default 'Open Food Facts contributors'"));
check("image references are optional", migration.includes("image_reference_url text") && migration.includes("image_reference_url is null"));
check("image licence remains separate", migration.includes("image_license_code = 'CC-BY-SA-4.0'"));
check("no image download or media import", !/(download|storage\.from|image upload)/iu.test(withoutComments));
check("no OFF catalog rows are embedded", !/insert\s+into\s+public\.nutrition_off_/iu.test(withoutComments));
check("expected future eligible count is documented, not seeded", slice4fDoc.includes("24,458") && !migration.includes("24458"));
check("future logs use immutable snapshots by design", /immutable snapshot/iu.test(slice4fDoc) && slice4fDoc.includes("source checksum"));
check("unknown barcode path remains architecture-only", slice4fDoc.includes("local miss") && /private custom[- ]product/iu.test(slice4fDoc));

check("verifier is one SELECT/CTE statement", /^with\b/iu.test(verifierWithoutComments) && /select\s+pg_catalog\.jsonb_pretty/iu.test(verifierWithoutComments));
check("verifier is read-only", !/^\s*(insert|update|delete|truncate|create|alter|drop|grant|revoke|comment|call)\b/imu.test(verifierWithoutComments));
check("verifier executes no app RPC", !/select\s+public\.fmz_phase4_/iu.test(verifierWithoutComments));
check("verifier checks overall pass", verifier.includes("'overall_pass', bool_and(pass)"));
for (const verifierCheck of [
  "off_release_forward_lifecycle", "off_odbl_metadata_contract", "off_gtin_and_identity_contract",
  "off_gtin_uniqueness", "off_basis_and_macro_contract", "off_quality_and_archive_contract",
  "off_search_indexes", "off_rls_enabled", "off_select_policies_exact", "off_table_acl_least_privilege",
  "typed_unified_search_signature", "typed_unified_search_sources_separate",
  "typed_unified_search_quality_and_ranking", "typed_unified_search_keyset_and_bounds",
  "local_barcode_lookup_contract", "frozen_tables_present_with_rls", "frozen_functions_present"
]) check(`verifier includes ${verifierCheck}`, verifier.includes(`'${verifierCheck}'`));

check("decision log locks separate ODbL domain", decisions.includes("separate ODbL catalog domain") && decisions.includes("nutrition_off_products"));
check("architecture documents typed search", architecture.includes("fmz_phase4_search_nutrition_catalog"));
check("master plan keeps Slice 4E frozen", masterPlan.includes("Slice 4E") && masterPlan.includes("frozen"));
check("Slice 4F documentation locks no execution", slice4fDoc.includes("Migration executed: NO") && slice4fDoc.includes("OFF products imported: NO"));

const combined = `${migration}\n${verifier}`;
check("no secret material", !/(eyJ[a-zA-Z0-9_-]{20,}|service[_-]?role[_-]?key\s*[:=]|supabase_service_role\s*[:=])/iu.test(combined));
check("no production project reference", !combined.includes("hgoygcviutmynaihcvpd"));
check("no AI integration", !/(openai|anthropic|gemini|chat completion)/iu.test(combined));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
if (failed.length) {
  console.error(`Phase 4 Slice 4F static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4 Slice 4F static check passed: ${checks.length}`);
