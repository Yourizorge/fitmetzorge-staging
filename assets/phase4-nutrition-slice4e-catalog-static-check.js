const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const bytes = (relativePath) => fs.readFileSync(path.join(root, relativePath));
const sha256 = (value) => crypto.createHash("sha256").update(value).digest("hex").toUpperCase();
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const manifestPath = "supabase/catalog/20260822_phase4_dutch_catalog_manifest.json";
const generatorPath = "supabase/catalog/generate_phase4_dutch_catalog.py";
const seedPath = "supabase/seeds/20260822_phase4_dutch_catalog_seed.sql";
const verifierPath = "supabase/verification/20260822_phase4_dutch_catalog_import_verification.sql";
const manifestSource = read(manifestPath);
const manifest = JSON.parse(manifestSource);
const generator = read(generatorPath);
const seed = read(seedPath);
const verifier = read(verifierPath);
const phase4Frontend = read("assets/phase4-nutrition-slice3.js");

const EXPECTED_MANIFEST_SHA = "5E9D8ED2C70125794F869827FC835A62BED56749CB23792E4225310E8F6864D5";
const EXPECTED_SEED_SHA = "567B6E6A63E93329B5B696B4631331716DE53E05AC08CD32DDD37ACE7A38886B";
const EXPECTED_VERIFIER_SHA = "E27C09762C2C853AC1C2DE1AB75498297155DD9B698C5B006A74124CCEEAED51";
const PROVIDER_NAMESPACE = "23440733-7e58-4c21-ad15-591eae6ab8ac";
const ALLOWED_TYPES = new Set(["Foundation", "Survey (FNDDS)", "SR Legacy"]);
const REQUIRED_TERMS = [
  "kipfilet", "rijst", "havermout", "banaan", "broccoli", "olijfolie",
  "ei", "appel", "aardappel", "melk", "volkoren brood", "halfvolle melk"
];

const stableStringify = (value) => {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
};

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
const normalizeAlias = (value) => value.toLocaleLowerCase("nl-NL")
  .replace(/[^\p{L}\p{N}_]+/gu, " ")
  .replace(/\s+/gu, " ")
  .trim();

check("manifest SHA is locked", sha256(bytes(manifestPath)) === EXPECTED_MANIFEST_SHA);
check("seed SHA is locked", sha256(bytes(seedPath)) === EXPECTED_SEED_SHA);
check("verifier SHA is locked", sha256(bytes(verifierPath)) === EXPECTED_VERIFIER_SHA);
check("manifest is newline-terminated human-readable JSON", manifestSource.endsWith("\n") && manifestSource.includes("\n  \"foods\""));
check("manifest identity is locked", manifest.artifact_version === "phase4_nl_generic_usda_v1_20260822" && manifest.mapping_version === "phase4_usda_v1");
check("ingestion UUID is locked", manifest.ingestion_id === "92fbeedd-63a8-5d22-9000-24e2a16189f1");
check("provider UUID namespace is locked", manifest.provider_candidate_uuid_namespace === PROVIDER_NAMESPACE);
check("provider identity format is exact", manifest.provider_identity_format === "usda_fdc:<fdcId>");
check("manifest has exactly 64 foods", manifest.manifest_food_count === 64 && manifest.foods.length === 64);
const aliases = manifest.foods.flatMap((food) => food.aliases.map((alias) => ({ food, alias })));
check("manifest alias count is exact", manifest.manifest_alias_count === 197 && aliases.length === 197);
check("manifest expects zero portions", manifest.expected_portion_count === 0);
check("category counts sum to 64", Object.values(manifest.category_counts).reduce((sum, value) => sum + value, 0) === 64);
for (const [category, count] of Object.entries({ protein: 11, dairy: 7, carbohydrates: 17, fruit: 8, vegetables: 10, fats_basics: 7, legumes: 4 })) {
  check(`category count ${category}`, manifest.category_counts[category] === count);
}

const foodIds = new Set();
const providerIds = new Set();
const slugs = new Set();
for (const food of manifest.foods) {
  check(`food ${food.fdc_id}: accepted data type`, ALLOWED_TYPES.has(food.usda_data_type));
  check(`food ${food.fdc_id}: deterministic UUIDv5`, food.canonical_uuid === uuidV5(PROVIDER_NAMESPACE, `usda_fdc:${food.fdc_id}`));
  check(`food ${food.fdc_id}: stable canonical slug`, food.canonical_slug === `usda-fdc-${food.fdc_id}`);
  check(`food ${food.fdc_id}: generic source identity`, !/(brand owner|trademark|upc|gtin)/iu.test(food.usda_source_description));
  check(`food ${food.fdc_id}: authentic canonical name`, food.canonical_name === food.usda_source_description);
  check(`food ${food.fdc_id}: reviewed decision`, food.reviewer_decision === "include" && food.reviewer_notes.length >= 20);
  check(`food ${food.fdc_id}: per-100-g required nutrients`, ["kcal", "protein", "carbohydrates", "fat"].every((key) => Number.isFinite(food.nutrition_per_100_g[key])));
  check(`food ${food.fdc_id}: nutrient bounds`, food.nutrition_per_100_g.kcal >= 0 && food.nutrition_per_100_g.kcal <= 1500 && ["protein", "carbohydrates", "fat"].every((key) => food.nutrition_per_100_g[key] >= 0 && food.nutrition_per_100_g[key] <= 100));
  check(`food ${food.fdc_id}: missing fiber is not fabricated`, food.nutrition_per_100_g.fiber === null || (food.nutrition_per_100_g.fiber >= 0 && food.nutrition_per_100_g.fiber <= 100));
  check(`food ${food.fdc_id}: source traceability`, Boolean(food.source_version && food.source_updated_at && food.retrieved_at && food.mapping_version && food.license && food.attribution?.url));
  check(`food ${food.fdc_id}: source mapping contract`, food.mapping_version === "phase4_usda_v1" && food.license === "CC0-1.0" && food.nutrient_derivation.reference_basis === "per_100_g");
  const checksumSource = { ...food };
  delete checksumSource.checksum;
  check(`food ${food.fdc_id}: record checksum`, food.checksum === sha256(Buffer.from(stableStringify(checksumSource), "utf8")));
  check(`food ${food.fdc_id}: unique identities`, !foodIds.has(food.canonical_uuid) && !providerIds.has(food.fdc_id) && !slugs.has(food.canonical_slug));
  foodIds.add(food.canonical_uuid);
  providerIds.add(food.fdc_id);
  slugs.add(food.canonical_slug);
}
check("records checksum is reproducible", manifest.records_sha256 === sha256(Buffer.from(stableStringify(manifest.foods), "utf8")));

const aliasIds = new Set();
for (const { food, alias } of aliases) {
  const expectedAliasId = uuidV5(food.canonical_uuid, `food_alias:${alias.language_code}:${alias.market_code || ""}:${alias.normalized_alias}`);
  check(`alias ${alias.alias_id}: deterministic UUIDv5`, alias.alias_id === expectedAliasId);
  check(`alias ${alias.alias_id}: normalized text`, alias.normalized_alias === normalizeAlias(alias.alias));
  check(`alias ${alias.alias_id}: reviewed and attributed`, alias.review_status === "reviewed" && alias.source_provider === "usda_fdc" && alias.license_code === "CC0-1.0");
  check(`alias ${alias.alias_id}: NL market rule`, alias.language_code !== "nl" || alias.market_code === "NL");
  check(`alias ${alias.alias_id}: unique identity`, !aliasIds.has(alias.alias_id));
  aliasIds.add(alias.alias_id);
}

const preferred = aliases.filter(({ alias }) => alias.is_preferred);
const preferredKeys = preferred.map(({ alias }) => `${alias.normalized_alias}|${alias.market_code}`);
check("preferred alias identities are unique", new Set(preferredKeys).size === preferredKeys.length);
check("preferred aliases are reviewed Dutch market decisions", preferred.every(({ alias }) => alias.language_code === "nl" && alias.market_code === "NL" && alias.review_status === "reviewed"));
check("preferred decisions are documented", manifest.preferred_ambiguous_aliases.length === preferred.length && preferred.length === 9);

check("raw and cooked pairs are complete", manifest.raw_cooked_pairs.length === 10 && manifest.raw_cooked_pairs.every((pair) => pair.members.length === 2 && new Set(pair.members.map((item) => item.food_uuid)).size === 2 && pair.members.some((item) => ["raw", "dry"].includes(item.preparation_state)) && pair.members.some((item) => item.preparation_state === "cooked")));
check("known Dutch gaps are documented", ["magere kwark", "halfvolle kwark", "skyr", "specific Dutch bread types"].every((term) => manifest.coverage_gaps.some((gap) => gap.term === term && gap.reason.length >= 30)));
for (const term of REQUIRED_TERMS) {
  check(`Dutch local search coverage: ${term}`, aliases.some(({ alias }) => alias.language_code === "nl" && alias.market_code === "NL" && alias.normalized_alias === term));
}
check("manifest required terms match static contract", REQUIRED_TERMS.every((term) => manifest.required_search_terms.includes(term)));

for (const source of manifest.source_archives) {
  check(`source ${source.data_type}: accepted`, ALLOWED_TYPES.has(source.data_type));
  check(`source ${source.data_type}: official USDA URL`, source.download_url.startsWith("https://fdc.nal.usda.gov/fdc-datasets/"));
  check(`source ${source.data_type}: archive hash`, /^[A-F0-9]{64}$/u.test(source.archive_sha256));
  check(`source ${source.data_type}: extracted JSON hash`, /^[A-F0-9]{64}$/u.test(source.json_sha256));
}

const seedWithoutComments = seed.replace(/^\s*--.*$/gmu, "");
check("seed is one explicit transaction", /^\s*begin;/iu.test(seedWithoutComments) && /commit;\s*$/iu.test(seedWithoutComments));
check("seed embeds exact manifest hash", seed.includes(`Exact manifest SHA-256: ${EXPECTED_MANIFEST_SHA}`) && seed.includes(`v_artifact_sha constant text := '${EXPECTED_MANIFEST_SHA}'`));
check("seed validates exact artifact identity and counts", seed.includes("catalog manifest identity or count mismatch") && seed.includes("existing ingestion identity differs from reviewed manifest"));
check("seed serializes replay", seed.includes("pg_advisory_xact_lock") && seed.includes("fmz_phase4_catalog_seed:"));
check("seed uses insert-or-replay semantics", (seed.match(/on conflict do nothing;/giu) || []).length === 3);
check("seed rejects food drift", seed.includes("existing canonical food differs from reviewed manifest"));
check("seed rejects alias drift", seed.includes("existing food alias differs from reviewed manifest"));
check("seed verifies imported counts", seed.includes("catalog import count mismatch"));
check("seed transitions only ledger state", /update\s+public\.nutrition_food_ingestions\s+set\s+status\s*=\s*'imported'/iu.test(seedWithoutComments));
check("seed has no destructive row operation", !/^\s*(delete|truncate)\b/imu.test(seedWithoutComments));
check("seed creates no portion row", !/insert\s+into\s+public\.food_portions/iu.test(seedWithoutComments));
check("seed never updates custom foods", !/update\s+public\.foods/iu.test(seedWithoutComments) && !/update\s+public\.food_aliases/iu.test(seedWithoutComments));
check("seed has no provider or network call", !/(api\.nal\.usda\.gov|fetch\s*\(|http_request|net\.)/iu.test(seedWithoutComments));
check("seed has no service-role frontend contract", !/(service[_-]?role[_-]?key|supabase_service_role)/iu.test(seed));
check("seed has no production ref", !seed.includes("hgoygcviutmynaihcvpd"));

const verifierWithoutComments = verifier.replace(/^\s*--.*$/gmu, "").trim();
check("verifier is one SELECT/CTE statement", /^with\b/iu.test(verifierWithoutComments) && /select\s+pg_catalog\.jsonb_pretty/iu.test(verifierWithoutComments) && /from\s+result;\s*$/iu.test(verifierWithoutComments));
check("verifier is read-only", !/^\s*(insert|update|delete|truncate|create|alter|drop|grant|revoke|comment|call)\b/imu.test(verifierWithoutComments));
check("verifier calls no app RPC", !/select\s+public\.fmz_phase4_/iu.test(verifierWithoutComments));
check("verifier checks exact artifact and counts", verifier.includes(EXPECTED_MANIFEST_SHA) && verifier.includes("exact_food_count") && verifier.includes("exact_alias_count"));
for (const name of [
  "all_expected_food_ids_and_provider_ids", "deterministic_uuid_manifest_contract",
  "reviewed_active_generic_usda_only", "accepted_usda_datatypes_only",
  "per_100_gram_reference_contract", "nutrient_bounds_and_missing_fiber_preserved",
  "provenance_mapping_license_attribution", "all_expected_aliases_linked",
  "preferred_nl_alias_uniqueness", "required_dutch_search_terms_present",
  "raw_cooked_pairs_remain_distinct", "zero_imported_portions", "custom_foods_untouched_by_ingestion"
]) {
  check(`verifier includes ${name}`, verifier.includes(`'${name}'`));
}

const localRender = phase4Frontend.indexOf("localResults.innerHTML = localSearchResultsMarkup()");
const providerRender = phase4Frontend.indexOf("providerResults.innerHTML = providerSearchMarkup()");
check("member UX renders local aliases before provider supplements", localRender >= 0 && providerRender > localRender);
check("frozen Phase 4 behavior plus approved 4F-B unified search hash", sha256(Buffer.from(phase4Frontend)) === "C82BEAB87AE97D9B178DD8C35580F7CC42698A12E8EC94B8863BB52F69E0FD62");
check("generator pins all three official archive hashes", manifest.source_archives.every((source) => generator.includes(source.archive_sha256)));
check("generator uses exact provider UUID identity", generator.includes('f"usda_fdc:{selection.fdc_id}"') && !generator.includes("PHASE3_EXERCISE_UUID_NAMESPACE"));
check("generator does not estimate missing fiber", generator.includes('result["fiber"] = None'));
check("generator rejects branded fields", generator.includes('food.get("brandOwner") or food.get("brandName")'));

const forbiddenSources = /(open\s*food\s*facts|nevo|experimental|branded food)/iu;
check("manifest contains no forbidden catalog source", !forbiddenSources.test(manifest.foods.map((food) => `${food.usda_data_type} ${food.usda_source_description}`).join("\n")));
check("artifacts contain no secrets", !/(eyJ[a-zA-Z0-9_-]{20,}|service[_-]?role[_-]?key\s*[:=]|usda_api_key\s*[:=]|hmac[_-]?key\s*[:=])/iu.test(`${manifestSource}\n${seed}\n${verifier}`));
check("artifacts contain no production ref", !`${manifestSource}\n${seed}\n${verifier}`.includes("hgoygcviutmynaihcvpd"));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
console.log(`Manifest SHA-256: ${sha256(bytes(manifestPath))}`);
console.log(`Seed SHA-256: ${sha256(bytes(seedPath))}`);
console.log(`Verifier SHA-256: ${sha256(bytes(verifierPath))}`);
if (failed.length) {
  console.error(`Phase 4 Slice 4E catalog static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4 Slice 4E catalog static check passed: ${checks.length}`);
