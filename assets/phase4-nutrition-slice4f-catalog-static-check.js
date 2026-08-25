const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const catalog = path.join(root, "supabase", "catalog", "20260825_phase4_off_catalog");
const read = (file) => fs.readFileSync(file, "utf8");
const sha256 = (file) => crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex").toUpperCase();
const readHeader = (file) => {
  const descriptor = fs.openSync(file, "r");
  const buffer = Buffer.alloc(16384);
  const length = fs.readSync(descriptor, buffer, 0, buffer.length, 0);
  fs.closeSync(descriptor);
  return buffer.subarray(0, length).toString("utf8").split(/\r?\n/u, 1)[0];
};
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const manifestPath = path.join(catalog, "20260825_phase4_off_artifact_manifest.json");
const releasePath = path.join(catalog, "20260825_phase4_off_release.json");
const sourceLockPath = path.join(catalog, "20260825_phase4_off_source_lock.json");
const productsPath = path.join(catalog, "20260825_phase4_off_products.csv");
const namesPath = path.join(catalog, "20260825_phase4_off_product_names.csv");
const fixturesPath = path.join(catalog, "20260825_phase4_off_search_fixtures.json");
const importerPath = path.join(root, "supabase", "imports", "20260825_phase4_off_catalog_import.psql");
const verifierPath = path.join(root, "supabase", "verification", "20260825_phase4_nutrition_slice4f_off_catalog_import_verification.sql");
const generatorPath = path.join(root, "supabase", "catalog", "generate_phase4_off_catalog.py");
const extractorPath = path.join(root, "supabase", "catalog", "extract_phase4_off_netherlands.py");
const finalizerPath = path.join(root, "supabase", "catalog", "finalize_phase4_off_catalog_artifacts.py");
const artifactVerifierPath = path.join(root, "supabase", "catalog", "verify_phase4_off_catalog_artifacts.py");

for (const file of [manifestPath, releasePath, sourceLockPath, productsPath, namesPath, fixturesPath, importerPath, verifierPath, extractorPath, generatorPath, finalizerPath, artifactVerifierPath]) {
  check(`artifact exists: ${path.basename(file)}`, fs.existsSync(file));
}

if (checks.every((item) => item.condition)) {
  const manifest = JSON.parse(read(manifestPath));
  const release = JSON.parse(read(releasePath));
  const sourceLock = JSON.parse(read(sourceLockPath));
  const importer = read(importerPath);
  const verifier = read(verifierPath);
  const extractor = read(extractorPath);
  const generator = read(generatorPath);
  const finalizer = read(finalizerPath);
  const artifactVerifier = read(artifactVerifierPath);
  const expectedSourceHash = "38D7A48D32F574812490024AA77FB064E84B041CB2687E46DF87AFCE441100C2";
  const expectedRevision = "e544a38353692b2df59df78f47393990a578eb8e";

  check("source revision is pinned", sourceLock.immutable_revision === expectedRevision && manifest.source.revision === expectedRevision);
  check("source hash is pinned", sourceLock.source_file_sha256 === expectedSourceHash && manifest.source.file_sha256 === expectedSourceHash);
  check("source size is pinned", sourceLock.source_file_size === 7797955269 && manifest.source.file_size === 7797955269);
  check("extractor hashes full source before transformation", extractor.includes("sha256_file(args.source) != SOURCE_FILE_SHA256") && extractor.includes("SOURCE_FILE_SIZE = 7_797_955_269"));
  check("extractor locks immutable revision", extractor.includes(expectedRevision));
  check("extractor uses Netherlands association", extractor.includes("list_contains(countries_tags, 'en:netherlands')"));
  check("extractor locks exact Netherlands output", extractor.includes("NETHERLANDS_SOURCE_COUNT = 106_650") && extractor.includes("EXPECTED_EXTRACT_SHA256"));
  check("Netherlands count is exact", manifest.source.netherlands_count === 106650);
  check("eligible product count is exact", manifest.counts.products === 24458);
  check("mass basis count is exact", manifest.counts.per_100_g === 20355);
  check("volume basis count is exact", manifest.counts.per_100_ml === 4103);
  check("Dutch product-name count is exact", manifest.counts.dutch_product_names === 18970);
  check("release identity is deterministic", release.id === "4b487f4f-ac8e-5579-a2a2-d4164c4b368a");
  check("release uses ODbL 1.0", release.license_code === "ODbL-1.0" && release.license_url === "https://opendatacommons.org/licenses/odbl/1-0/");
  check("images are deliberately excluded", release.metadata.image_policy === "references_not_imported");
  for (const [filename, metadata] of Object.entries(manifest.files)) {
    const file = path.join(catalog, filename);
    check(`manifest byte size: ${filename}`, fs.statSync(file).size === metadata.bytes);
    check(`manifest hash: ${filename}`, sha256(file) === metadata.sha256);
  }
  for (const [relativePath, metadata] of Object.entries(manifest.execution_files)) {
    const file = path.join(root, relativePath);
    check(`execution byte size: ${relativePath}`, fs.statSync(file).size === metadata.bytes);
    check(`execution hash: ${relativePath}`, sha256(file) === metadata.sha256);
  }

  check("generator locks 24,458 products", generator.includes("ELIGIBLE_PRODUCT_COUNT = 24_458"));
  check("generator locks exact basis split", generator.includes("EXPECTED_MASS_COUNT = 20_355") && generator.includes("EXPECTED_VOLUME_COUNT = 4_103"));
  check("generator locks accepted source audit counts", generator.includes("NETHERLANDS_VALID_BARCODE_COUNT = 85_192") && generator.includes("NETHERLANDS_REQUIRED_MACROS_PRESENT_COUNT = 56_512") && generator.includes("NETHERLANDS_VALID_REQUIRED_MACROS_COUNT = 56_440"));
  check("generator verifies exact source extract", generator.includes("sha256_file(args.source) != SOURCE_EXTRACT_SHA256"));
  check("generator derives kcal from explicit kJ", generator.includes('"energy_kj_100g_div_4_184"') && generator.includes('/ Decimal("4.184")'));
  check("generator rejects unusable one-character names", generator.includes("len(normalize_catalog_text(primary_name)) < 2"));
  check("generator uses provider namespace", generator.includes("23440733-7e58-4c21-ad15-591eae6ab8ac"));
  check("generator uses OFF provider prefix", generator.includes('f"open_food_facts:{gtin14}"'));
  check("generator does not fabricate search variants", !generator.includes('"search_variant",'));
  check("generator has no AI translation", !/(openai|anthropic|gemini|translate api)/iu.test(generator));
  check("finalizer is file based", finalizer.includes("\\\\copy fmz_off_products_stage") && finalizer.includes("\\\\copy fmz_off_names_stage"));
  check("import stops on first error", importer.includes("\\set ON_ERROR_STOP on"));
  const productHeader = readHeader(productsPath).split(",");
  const nameHeader = readHeader(namesPath).split(",");
  const copyColumns = [...importer.matchAll(/\\copy\s+fmz_off_(products|names)_stage\s*\(([^)]+)\)/giu)]
    .map((match) => [match[1], match[2].split(",").map((value) => value.trim())]);
  check("product CSV header matches copy contract", JSON.stringify(copyColumns.find(([type]) => type === "products")?.[1]) === JSON.stringify(productHeader));
  check("name CSV header matches copy contract", JSON.stringify(copyColumns.find(([type]) => type === "names")?.[1]) === JSON.stringify(nameHeader));
  check("import is one transaction", /^begin;$/imu.test(importer) && /commit;\s*$/iu.test(importer));
  check("import uses an advisory transaction lock", importer.includes("pg_advisory_xact_lock"));
  check("import is fail-on-drift", importer.includes("product drift") && importer.includes("name drift"));
  check("release finalizes after products and names", importer.indexOf("insert into public.nutrition_off_product_names") < importer.indexOf("set status = 'imported'"));
  check("import has no destructive removal", !/\b(delete|truncate)\b/iu.test(importer));
  for (const table of ["foods", "food_aliases", "food_portions", "food_logs", "food_log_items"]) {
    check(`no frozen write: ${table}`, !new RegExp(`\\b(?:insert\\s+into|update)\\s+public\\.${table}\\b`, "iu").test(importer));
  }
  check("verifier is SELECT/CTE only", verifier.replace(/^\s*--.*$/gmu, "").trimStart().toLowerCase().startsWith("with"));
  check("verifier returns null-safe overall_pass", verifier.includes("'overall_pass', bool_and(coalesce(pass, false))"));
  check("verifier checks products and names", verifier.includes("'product_count'") && verifier.includes("'name_count'"));
  check("verifier checks frozen domains", verifier.includes("'frozen_usda_foods'") && verifier.includes("'frozen_member_items'"));
  check("artifact verifier recalculates UUIDs", artifactVerifier.includes("uuid.uuid5(PROVIDER_NAMESPACE, identity)"));
  check("artifact verifier validates macros", artifactVerifier.includes("macro_bounds"));
  check("artifact verifier checks replay and drift", artifactVerifier.includes("importer_replay_path") && artifactVerifier.includes("importer_fail_on_drift"));

  const combined = `${generator}\n${finalizer}\n${artifactVerifier}\n${importer}\n${verifier}`;
  check("no production project ref", !combined.includes("hgoygcviutmynaihcvpd"));
  check("no service-role secret", !/(service[_-]?role[_-]?key\s*[:=]|eyJ[a-zA-Z0-9_-]{40,})/u.test(combined));
  check("no provider network call during import", !/(world\.openfoodfacts\.org|fetch\(|http_request)/iu.test(importer));
}

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
if (failed.length) {
  console.error(`Phase 4 Slice 4F catalog artifact static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4 Slice 4F catalog artifact static check passed: ${checks.length}`);
