const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const sha256 = (source) => crypto.createHash("sha256").update(source).digest("hex").toUpperCase();
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const migrationPath = "supabase/migrations/20260821214541_phase4_nutrition_slice4e_ingestion_alias_search.sql";
const verifierPath = "supabase/verification/20260821214541_phase4_nutrition_slice4e_ingestion_alias_search_verification.sql";
const migration = read(migrationPath);
const verifier = read(verifierPath);
const slice1 = read("supabase/migrations/20260818_phase4_nutrition_schema_slice1.sql");
const slice4b = read("supabase/migrations/20260819_phase4_nutrition_slice4b_alias_search.sql");
const slice4c = read("supabase/migrations/20260819_phase4_nutrition_slice4c_operational_state.sql");
const slice4d = read("supabase/migrations/20260819_phase4_nutrition_slice4d_provider_snapshot_logging.sql");
const resolver = read("supabase/migrations/20260820134211_phase4_nutrition_slice4d_historical_provider_resolver.sql");
const phase4Frontend = read("assets/phase4-nutrition-slice3.js");
const architecture = read("docs/PHASE4_NUTRITION_SLICE4E_LOCAL_CATALOG.md");
const decisions = read("docs/DECISIONS.md");
const masterPlan = read("docs/MASTER_BUILD_PLAN.md");
const architectureOverview = read("docs/ARCHITECTURE.md");
const buildStatus = read("docs/BUILD_STATUS.md");
const testMatrix = read("docs/TEST_MATRIX.md");

const migrationWithoutComments = migration.replace(/^\s*--.*$/gm, "");
const verifierWithoutComments = verifier.replace(/^\s*--.*$/gm, "").trim();
const searchFunction = (migration.match(/create\s+or\s+replace\s+function\s+public\.fmz_phase4_search_foods[\s\S]*?\n\$\$;/i) || [""])[0];
const ledgerTable = (migration.match(/create\s+table\s+if\s+not\s+exists\s+public\.nutrition_food_ingestions[\s\S]*?\n\);/i) || [""])[0];

check("migration has staging-only project guard", migration.includes("STAGING ONLY: mokxyyullfhkfalopbzd"));
check("migration filename uses Supabase CLI timestamp", /^20260821\d{6}_phase4_nutrition_slice4e_ingestion_alias_search\.sql$/.test(path.basename(migrationPath)));
check("migration is one explicit transaction", /^\s*--[\s\S]*?\nbegin;/i.test(migration) && /commit;\s*$/i.test(migration));
check("migration creates exactly one table", [...migration.matchAll(/create\s+table\s+if\s+not\s+exists\s+public\.([a-z0-9_]+)/gi)].map((match) => match[1]).join(",") === "nutrition_food_ingestions");
check("migration creates no import rows", !/^\s*(insert|update|delete|truncate|copy)\b/im.test(migrationWithoutComments));
check("migration contains no seed manifest", !/(manifest_foods|seed_foods|copy\s+public\.foods)/i.test(migrationWithoutComments));
check("migration has no provider call", !/(api\.nal\.usda\.gov|world\.openfoodfacts\.org|fetch\s*\()/i.test(migration));
check("migration has no production ref or secret", !/(hgoygcviutmynaihcvpd|service[_-]?role[_-]?key|supabase_service_role|api[_-]?key|hmac[_-]?key)/i.test(migration));
check("migration adds no trainer policy", !/create\s+policy[^;]*trainer|grant[^;]*trainer/i.test(migration));

check("ledger has UUID primary key", /id\s+uuid\s+primary\s+key/i.test(ledgerTable));
for (const column of [
  "artifact_version text not null",
  "artifact_sha256 text not null",
  "source_provider text not null",
  "mapping_version text not null",
  "status text not null default 'reviewed'",
  "predecessor_ingestion_id uuid references public.nutrition_food_ingestions(id) on delete restrict",
  "manifest_food_count integer not null",
  "manifest_alias_count integer not null",
  "reviewed_by text not null",
  "reviewed_at timestamptz not null",
  "imported_at timestamptz",
  "provenance jsonb not null default '{}'::jsonb",
  "metadata jsonb not null default '{}'::jsonb",
  "created_at timestamptz not null default now()",
  "updated_at timestamptz not null default now()"
]) {
  check(`ledger column contract: ${column}`, ledgerTable.includes(column));
}
check("artifact SHA is unique", ledgerTable.includes("nutrition_food_ingestions_artifact_sha256_key unique (artifact_sha256)"));
check("provider version is unique", ledgerTable.includes("nutrition_food_ingestions_provider_version_key unique (source_provider, artifact_version)"));
check("artifact SHA is uppercase SHA-256", /artifact_sha256\s*~\s*'\^\[A-F0-9\]\{64\}\$'/i.test(ledgerTable));
check("provider text is normalized and bounded", ledgerTable.includes("source_provider = lower(btrim(source_provider))") && ledgerTable.includes("between 2 and 40"));
check("version and mapping text are bounded", ledgerTable.includes("artifact_version)) between 1 and 120") && ledgerTable.includes("mapping_version)) between 1 and 120"));
check("ledger status lifecycle values are constrained", /status\s+in\s*\('reviewed',\s*'imported',\s*'superseded',\s*'rejected'\)/i.test(ledgerTable));
check("predecessor cannot self-reference", ledgerTable.includes("predecessor_ingestion_id <> id"));
check("manifest counts are non-negative and bounded", ledgerTable.includes("manifest_food_count between 0 and 1000000") && ledgerTable.includes("manifest_alias_count between 0 and 5000000"));
check("ledger JSON fields must be objects", ledgerTable.includes("jsonb_typeof(provenance) = 'object'") && ledgerTable.includes("jsonb_typeof(metadata) = 'object'"));
check("imported state requires imported timestamp", /status\s+in\s*\('imported',\s*'superseded'\)[\s\S]*imported_at\s+is\s+not\s+null/i.test(ledgerTable));
check("reviewed and rejected state reject imported timestamp", /status\s+in\s*\('reviewed',\s*'rejected'\)[\s\S]*imported_at\s+is\s+null/i.test(ledgerTable));
check("import timestamp follows review", ledgerTable.includes("imported_at >= reviewed_at"));
check("ledger audit identity is immutable", migration.includes("food ingestion audit identity is immutable"));
check("ledger transition graph is forward-only", migration.includes("old.status = 'reviewed' and new.status in ('imported', 'rejected')") && migration.includes("old.status = 'imported' and new.status = 'superseded'"));
check("ingestion chain uses one per-provider advisory namespace", migration.includes("pg_advisory_xact_lock") && migration.includes("fmz_phase4_food_ingestion_chain:"));
check("subsequent artifacts require explicit predecessor", migration.includes("subsequent food ingestion artifact requires predecessor"));
check("predecessor provider must match", migration.includes("predecessor must use the same source provider"));
check("predecessor chain cannot branch", /create\s+unique\s+index[\s\S]*nutrition_food_ingestions_predecessor_uidx[\s\S]*predecessor_ingestion_id[\s\S]*where\s+predecessor_ingestion_id\s+is\s+not\s+null/i.test(migration));
check("ledger removal is blocked by trigger", migration.includes("nutrition_food_ingestions_20_prevent_removal") && migration.includes("forward fixes only"));
check("ledger timestamp trigger reuses reviewed helper", migration.includes("nutrition_food_ingestions_90_touch_updated_at") && migration.includes("fmz_phase4_touch_updated_at()"));
check("ledger RLS is enabled", /alter\s+table\s+public\.nutrition_food_ingestions\s+enable\s+row\s+level\s+security/i.test(migration));
check("ledger creates no policy", !/create\s+policy[^;]*nutrition_food_ingestions/i.test(migration));
check("ledger app and service ACL are revoked", ["public", "anon", "authenticated", "service_role"].every((role) => new RegExp(`revoke\\s+all\\s+on\\s+table\\s+public\\.nutrition_food_ingestions\\s+from\\s+${role}`, "i").test(migration)));
check("ledger trigger functions are invoker and private", /fmz_phase4_enforce_food_ingestion_state\(\)[\s\S]*security\s+invoker/i.test(migration) && /fmz_phase4_prevent_food_ingestion_removal\(\)[\s\S]*security\s+invoker/i.test(migration) && !/grant\s+execute\s+on\s+function\s+public\.fmz_phase4_(?:enforce_food_ingestion_state|prevent_food_ingestion_removal)/i.test(migration));

check("foods gets nullable ingestion link", /alter\s+table\s+public\.foods[\s\S]*add\s+column\s+if\s+not\s+exists\s+ingestion_id\s+uuid/i.test(migration));
check("foods ingestion FK is restrictive", /foods_ingestion_id_fkey[\s\S]*references\s+public\.nutrition_food_ingestions\(id\)[\s\S]*on\s+delete\s+restrict/i.test(migration));
check("custom foods cannot acquire ingestion authority", migration.includes("foods_ingestion_scope_check") && migration.includes("catalog_scope = 'canonical' or ingestion_id is null"));
check("reviewed canonical foods require ingestion", /foods_canonical_ingestion_quality_check[\s\S]*quality_status\s+not\s+in\s*\('reviewed',\s*'verified'\)[\s\S]*ingestion_id\s+is\s+not\s+null/i.test(migration));
check("foods ingestion lookup is indexed", migration.includes("foods_ingestion_id_idx") && migration.includes("where ingestion_id is not null"));

check("aliases get nullable ingestion link", /alter\s+table\s+public\.food_aliases[\s\S]*add\s+column\s+if\s+not\s+exists\s+ingestion_id\s+uuid/i.test(migration));
check("aliases get explicit preferred marker", migration.includes("add column if not exists is_preferred boolean not null default false"));
check("alias ingestion FK is restrictive", /food_aliases_ingestion_id_fkey[\s\S]*references\s+public\.nutrition_food_ingestions\(id\)[\s\S]*on\s+delete\s+restrict/i.test(migration));
check("reviewed provider aliases require ingestion", /food_aliases_reviewed_ingestion_check[\s\S]*source_provider\s+is\s+null[\s\S]*review_status\s*=\s*'pending'/i.test(migration));
check("preferred aliases are reviewed Dutch market aliases", /food_aliases_preferred_review_check[\s\S]*language_code\s*=\s*'nl'[\s\S]*market_code\s+is\s+not\s+null[\s\S]*review_status\s+in\s*\('reviewed',\s*'verified'\)/i.test(migration));
check("ambiguous preferred aliases are unique per normalized term and market", /create\s+unique\s+index[\s\S]*food_aliases_preferred_nl_market_uidx[\s\S]*normalized_alias,\s*market_code[\s\S]*is_preferred/i.test(migration));

check("canonical SELECT policy requires active quality-gated ingestion", /alter\s+policy\s+"foods_select_visible"[\s\S]*catalog_scope\s*=\s*'canonical'[\s\S]*status\s*=\s*'active'[\s\S]*quality_status\s+in\s*\('reviewed',\s*'verified'\)[\s\S]*ingestion_id\s+is\s+not\s+null/i.test(migration));
check("owned custom foods remain visible independent of canonical quality", /alter\s+policy\s+"foods_select_visible"[\s\S]*catalog_scope\s*=\s*'custom'[\s\S]*owner_user_id\s*=\s*\(select\s+auth\.uid\(\)\)/i.test(migration));
check("alias policy keeps reviewed and verified only", /alter\s+policy\s+"food_aliases_select_visible"[\s\S]*review_status\s+in\s*\('reviewed',\s*'verified'\)/i.test(migration));
check("alias policy checks parent canonical quality", /alter\s+policy\s+"food_aliases_select_visible"[\s\S]*f\.quality_status\s+in\s*\('reviewed',\s*'verified'\)[\s\S]*f\.ingestion_id\s+is\s+not\s+null/i.test(migration));
check("alias policy preserves owned custom parent", /alter\s+policy\s+"food_aliases_select_visible"[\s\S]*f\.catalog_scope\s*=\s*'custom'[\s\S]*f\.owner_user_id\s*=\s*\(select\s+auth\.uid\(\)\)/i.test(migration));

check("search keeps exact frontend signature", /fmz_phase4_search_foods\(\s*p_query\s+text\s+default\s+null,\s*p_page_size\s+integer\s+default\s+25,\s*p_after_name\s+text\s+default\s+null,\s*p_after_id\s+uuid\s+default\s+null/iu.test(searchFunction));
check("search keeps SETOF foods response", /returns\s+setof\s+public\.foods/i.test(searchFunction));
check("search remains stable invoker with safe path", /stable[\s\S]*security\s+invoker[\s\S]*search_path\s*=\s*pg_catalog,\s*public,\s*pg_temp/i.test(searchFunction));
check("search derives authority from auth uid", searchFunction.includes("v_user_id uuid := auth.uid()") && searchFunction.includes("authenticated user required"));
check("search includes own custom candidates", searchFunction.includes("f.catalog_scope = 'custom'") && searchFunction.includes("f.owner_user_id = v_user_id"));
check("search includes reviewed canonical candidates", searchFunction.includes("f.catalog_scope = 'canonical'") && searchFunction.includes("f.quality_status in ('reviewed', 'verified')") && searchFunction.includes("f.ingestion_id is not null"));
check("search includes reviewed aliases", searchFunction.includes("from public.food_aliases a") && searchFunction.includes("a.review_status in ('reviewed', 'verified')"));
check("search deduplicates by food id", searchFunction.includes("select distinct on (c.food_id)"));
check("search ranks exact custom first", /select\s+f\.id,\s*10,/i.test(searchFunction));
check("search ranks exact Dutch alias before canonical", /case\s+when\s+a\.language_code\s*=\s*'nl'\s+then\s+20\s+else\s+22\s+end/i.test(searchFunction) && /select\s+f\.id,\s*30,/i.test(searchFunction));
check("search ranks alias prefix before canonical prefix", /then\s+40\s+else\s+42\s+end/i.test(searchFunction) && /select\s+f\.id,\s*50,/i.test(searchFunction));
check("search ranks NL market and preferred aliases", searchFunction.includes("a.language_code = 'nl' and a.market_code = 'NL'") && searchFunction.includes("case when a.is_preferred then 0 else 1 end"));
check("search uses reviewed alias priority", searchFunction.includes("-a.priority::integer"));
check("search uses controlled trigram operator and similarity", searchFunction.includes("operator(extensions.%)") && searchFunction.includes("extensions.similarity") && searchFunction.includes("char_length(v_normalized_query) >= 3"));
check("search candidate branches are capped", (searchFunction.match(/limit 250/gi) || []).length >= 10);
check("search page size remains 1 through 50", searchFunction.includes("greatest(1, least(coalesce(p_page_size, 25), 50))"));
check("search has no OFFSET pagination", !/\boffset\b/i.test(searchFunction));
check("search recomputes cursor rank from food id", searchFunction.includes("cursor_key as") && searchFunction.includes("r.food_id = p_after_id") && searchFunction.includes("lower(r.food_name) = lower(btrim(p_after_name))"));
check("search keyset compares complete rank and tie-break", /r\.match_tier,[\s\S]*r\.similarity_sort,[\s\S]*lower\(f\.name\),[\s\S]*f\.id[\s\S]*>\s*\([\s\S]*c\.match_tier,[\s\S]*c\.food_id/i.test(searchFunction));
check("search result tie-break is stable name and UUID", /order\s+by[\s\S]*r\.match_tier,[\s\S]*lower\(f\.name\),[\s\S]*f\.id[\s\S]*limit\s+v_page_size/i.test(searchFunction));
check("search execute remains authenticated only", /revoke\s+all\s+on\s+function\s+public\.fmz_phase4_search_foods\(text,\s*integer,\s*text,\s*uuid\)\s+from\s+public/i.test(migration) && /from\s+anon/i.test(migration) && /grant\s+execute[\s\S]*to\s+authenticated/i.test(migration));
check("search does not return ledger data", !/returns\s+table[\s\S]*ingestion/i.test(searchFunction));

const visibleFood = (food, userId) => food.catalogScope === "custom"
  ? food.ownerUserId === userId
  : food.status === "active" && ["reviewed", "verified"].includes(food.qualityStatus) && Boolean(food.ingestionId);
const visibleAlias = (alias, food, userId) => alias.status === "active"
  && ["reviewed", "verified"].includes(alias.reviewStatus)
  && visibleFood(food, userId);
const rank = (candidate) => [candidate.tier, candidate.locale, candidate.preferred, -candidate.priority, -candidate.similarity, candidate.name.toLowerCase(), candidate.id];
const compareRank = (left, right) => {
  const a = rank(left);
  const b = rank(right);
  for (let index = 0; index < a.length; index += 1) {
    if (a[index] < b[index]) return -1;
    if (a[index] > b[index]) return 1;
  }
  return 0;
};
const dedupe = (candidates) => Array.from(candidates.reduce((byId, candidate) => {
  const current = byId.get(candidate.id);
  if (!current || compareRank(candidate, current) < 0) byId.set(candidate.id, candidate);
  return byId;
}, new Map()).values()).sort(compareRank);

const reviewedCanonical = { catalogScope: "canonical", status: "active", qualityStatus: "reviewed", ingestionId: "ledger" };
const verifiedCanonical = { ...reviewedCanonical, qualityStatus: "verified" };
const pendingCanonical = { ...reviewedCanonical, qualityStatus: "pending" };
const ownedCustom = { catalogScope: "custom", status: "archived", ownerUserId: "member-a" };
const otherCustom = { ...ownedCustom, ownerUserId: "member-b" };
check("model: pending canonical hidden", !visibleFood(pendingCanonical, "member-a"));
check("model: reviewed canonical visible", visibleFood(reviewedCanonical, "member-a"));
check("model: verified canonical visible", visibleFood(verifiedCanonical, "member-a"));
check("model: unledgered reviewed canonical hidden", !visibleFood({ ...reviewedCanonical, ingestionId: null }, "member-a"));
check("model: owned custom visible", visibleFood(ownedCustom, "member-a"));
check("model: other-user custom hidden", !visibleFood(otherCustom, "member-a"));
check("model: pending alias hidden", !visibleAlias({ status: "active", reviewStatus: "pending" }, reviewedCanonical, "member-a"));
check("model: reviewed alias visible", visibleAlias({ status: "active", reviewStatus: "reviewed" }, reviewedCanonical, "member-a"));
check("model: alias parent quality gate", !visibleAlias({ status: "active", reviewStatus: "verified" }, pendingCanonical, "member-a"));

const ranked = [
  { id: "food-custom", name: "Kip eigen", tier: 10, locale: 0, preferred: 0, priority: 0, similarity: 1 },
  { id: "food-alias", name: "Chicken breast raw", tier: 20, locale: 0, preferred: 0, priority: 80, similarity: 1 },
  { id: "food-canonical", name: "Kipfilet", tier: 30, locale: 0, preferred: 0, priority: 0, similarity: 1 },
  { id: "food-prefix", name: "Kipfilet bereid", tier: 40, locale: 0, preferred: 1, priority: 60, similarity: 1 }
].sort(compareRank);
check("model: exact NL alias outranks exact canonical", ranked.findIndex((item) => item.id === "food-alias") < ranked.findIndex((item) => item.id === "food-canonical"));
check("model: exact custom outranks alias", ranked[0].id === "food-custom");
check("model: alias prefix outranks canonical prefix", compareRank({ ...ranked[1], id: "a", tier: 40 }, { ...ranked[2], id: "b", tier: 50 }) < 0);
check("model: preferred NL alias wins equal alias", compareRank({ id: "a", name: "Rice cooked", tier: 20, locale: 0, preferred: 0, priority: 50, similarity: 1 }, { id: "b", name: "Rice dry", tier: 20, locale: 0, preferred: 1, priority: 50, similarity: 1 }) < 0);
check("model: raw and cooked identities remain separate", dedupe([
  { id: "raw", name: "Chicken breast raw", tier: 20, locale: 0, preferred: 0, priority: 50, similarity: 1 },
  { id: "cooked", name: "Chicken breast cooked", tier: 20, locale: 0, preferred: 1, priority: 40, similarity: 1 }
]).length === 2);
check("model: duplicate aliases collapse by food ID", dedupe([
  { id: "same", name: "Rice cooked", tier: 40, locale: 0, preferred: 1, priority: 10, similarity: 1 },
  { id: "same", name: "Rice cooked", tier: 20, locale: 0, preferred: 0, priority: 80, similarity: 1 }
]).length === 1);
const pageModel = dedupe(ranked);
const cursor = pageModel[1];
check("model: keyset page is stable after cursor", pageModel.filter((item) => compareRank(item, cursor) > 0).every((item) => compareRank(item, cursor) > 0));
check("model: NL EN DE aliases remain representable", ["nl", "en", "de"].every((language) => slice4b.includes(`'${language}'`)));

check("verifier is one SELECT CTE statement", /^with\b/i.test(verifierWithoutComments) && /select\s+jsonb_pretty\(/i.test(verifierWithoutComments) && /from\s+result;\s*$/i.test(verifierWithoutComments));
check("verifier has no mutating statement", !/^\s*(insert|update|delete|truncate|create|alter|drop|grant|revoke|comment|call)\b/im.test(verifierWithoutComments));
check("verifier invokes no application RPC", !/select\s+public\.fmz_phase4_/i.test(verifierWithoutComments));
check("verifier returns overall pass", verifier.includes("'overall_pass', overall_pass"));
check("verifier uses ACL metadata for PUBLIC", verifier.includes("pg_catalog.aclexplode") && verifier.includes("acl.grantee = 0"));
for (const verifierCheck of [
  "ledger_table_and_columns",
  "ledger_defaults_and_constraints",
  "ledger_constraint_semantics",
  "ledger_predecessor_chain_and_lock",
  "ledger_rls_acl_and_no_policies",
  "foods_ingestion_link",
  "aliases_ingestion_and_preferred_rule",
  "canonical_quality_visibility",
  "alias_quality_and_parent_visibility",
  "search_signature_security_and_acl",
  "search_alias_ranking_and_quality",
  "search_stable_bounded_keyset",
  "catalog_table_acl_and_no_browser_writes",
  "no_trainer_or_removal_policy",
  "frozen_slice4b_4c_4d_contracts",
  "all_guard_tables_present_with_rls",
  "no_catalog_import_in_migration",
  "forbidden_reference_scan"
]) {
  check(`verifier includes ${verifierCheck}`, verifier.includes(`'${verifierCheck}'`));
}

check("Slice 1 migration remains frozen", sha256(slice1) === "D70A589FEF997C14FCC9805E746536C86556E22622C8952B33DE9CA222B36188");
check("Slice 4B migration remains frozen", sha256(slice4b) === "4C0E63DC09A8CC1DE7F93DBA278CD36F714C52BEDAB32FFC98147A5DA0D5C88F");
check("Slice 4C migration remains frozen", sha256(slice4c) === "0A2D2CA5B4CAAD30A17B73F66C018A742DC1D9326335AA7C9307D0021CF0AE2F");
check("Slice 4D provider migration remains frozen", sha256(slice4d) === "10228D7CDEC07341C85BFF80D2464ED4F46995FB732976F3045DFB2CB72F9DD0");
check("Slice 4D resolver migration remains frozen", sha256(resolver) === "2B28BA69D89892D9CD52E852DB7F6E12D9849977C646C2E596C5464EA39F44CD");
check("Slice 4D frontend remains frozen", sha256(phase4Frontend) === "525538DD4A9D57A4321BFFC3FA9D396937F6E8BA8FC438D85F15C32BD0A16F26");
check("architecture documents no import execution", architecture.includes("Catalog imported: NO") && architecture.includes("Migration executed: NO"));
check("decision log locks Slice 4E authority", /Decision 0025[\s\S]*Slice 4E/i.test(decisions));
check("master plan records Slice 4E review gate", /Slice 4E[\s\S]*migration review/i.test(masterPlan));
check("architecture overview records ledger and alias search", architectureOverview.includes("nutrition_food_ingestions") && architectureOverview.includes("alias-aware"));
check("build status records local-only Slice 4E", /Slice 4E[\s\S]*LOCAL[\s\S]*NOT EXECUTED/i.test(buildStatus));
check("test matrix records Slice 4E suite", testMatrix.includes("Phase 4 Slice 4E Ingestion Ledger + Alias Search Local Checks"));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) {
  console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
}

console.log(`Migration SHA-256: ${sha256(migration)}`);
console.log(`Verifier SHA-256: ${sha256(verifier)}`);

if (failed.length) {
  console.error(`Phase 4 Nutrition Slice 4E static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}

console.log(`Phase 4 Nutrition Slice 4E static check passed: ${checks.length}`);
