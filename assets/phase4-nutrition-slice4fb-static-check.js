const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

const index = read("index.html");
const app = read("app.js");
const runtime = read("assets/phase4-nutrition-slice3.js");
const browser = read("assets/phase4-nutrition-slice3-browser-check.js");

function functionBody(source, name) {
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

const searchFoods = runtime.slice(runtime.indexOf("async function searchFoods("), runtime.indexOf("function scheduleLocalSearch("));
const resultGuard = functionBody(runtime, "isSafeUnifiedSearchResult");
const resultMapper = functionBody(runtime, "mapUnifiedSearchResult");
const resultKey = functionBody(runtime, "searchResultKey");
const supplement = functionBody(runtime, "shouldSupplementProvider");
const localResults = functionBody(runtime, "localSearchResultsMarkup");
const searchRow = functionBody(runtime, "searchRow");
const selectFood = functionBody(runtime, "selectSearchFood");
const offDialog = functionBody(runtime, "offProductDialog");
const renderResults = functionBody(runtime, "renderSearchResults");
const renderPortal = runtime.slice(runtime.indexOf("function renderPortal("), runtime.indexOf("function openSearch("));

check("4F-B runtime version is explicit", runtime.includes('PHASE4_SLICE3_VERSION = "20260826-phase4f-b-unified-catalog1"'));
check("4F-B app cache is explicit", index.includes("app.js?v=20260826-phase4f-b1") && app.includes("phase4-nutrition-slice3.js?v=20260826-phase4f-b1"));
check("unified catalog RPC is used", searchFoods.includes('rpc("fmz_phase4_search_nutrition_catalog"'));
check("legacy local-only search RPC is removed", !runtime.includes('rpc("fmz_phase4_search_foods"'));
check("unified search is bounded", runtime.includes("PHASE4_SLICE3_SEARCH_PAGE_SIZE = 25") && searchFoods.includes("p_page_size: PHASE4_SLICE3_SEARCH_PAGE_SIZE"));
check("unified search sends active locale", searchFoods.includes("p_locale: language()"));
check("typed cursor rank is sent", searchFoods.includes("p_after_rank") && searchFoods.includes("p_after_score"));
check("typed cursor identity is sent", searchFoods.includes("p_after_name") && searchFoods.includes("p_after_source") && searchFoods.includes("p_after_id"));
check("typed cursor is read from server rows", searchFoods.includes("last?.cursor_name") && searchFoods.includes("last?.cursor_source") && searchFoods.includes("last?.cursor_id"));
check("typed identities prevent cross-source dedupe", resultKey.includes("food?.result_type") && searchFoods.includes("searchResultKey(food)"));
check("allowed result types are explicit", ["custom_food", "generic_food", "off_branded_food"].every((type) => resultGuard.includes(`'${type}'`)));
check("unexpected result types fail closed", resultGuard.includes("return false") && resultMapper.includes("if (!isSafeUnifiedSearchResult(row)) return null"));
check("all local results must be server-loggable", resultGuard.includes("row?.loggable !== true"));
check("generic quality is constrained", resultGuard.includes("'reviewed'") && resultGuard.includes("'verified'"));
check("OFF provider identity is constrained", resultGuard.includes("open_food_facts"));
check("OFF quality is constrained", resultGuard.includes("'complete'") && resultGuard.includes("'reviewed'"));
check("OFF basis is constrained", resultGuard.includes("per_100_g") && resultGuard.includes("per_100_ml") && resultGuard.includes("referenceAmount !== 100"));
check("OFF g and ml units stay source truthful", resultGuard.includes("referenceUnit !== 'g'") && resultGuard.includes("referenceUnit !== 'ml'"));
check("negative or invalid nutrients fail closed", resultGuard.includes("Number.isFinite(value)") && resultGuard.includes("value < 0"));
check("Dutch generic display label comes from RPC display name", resultMapper.includes("dutch_display_label: String(row.display_name).trim()"));
check("OFF result group is separate", localResults.includes('result_type === "off_branded_food"') && runtime.includes('productResults: "Producten"'));
check("custom result group remains separate", localResults.includes('result_type === "custom_food"'));
check("generic result group remains separate", localResults.includes('result_type === "generic_food"'));
check("OFF card includes brand", searchRow.includes("food.brand"));
check("OFF card includes 100 g and 100 ml basis", searchRow.includes("per_100_g") && searchRow.includes("per_100_ml"));
check("OFF card includes kcal and macros", ["energy_kcal", "protein_grams", "carbohydrate_grams", "fat_grams"].every((field) => searchRow.includes(field)));
check("OFF attribution is visible", searchRow.includes('text("offSource")') && runtime.includes('offAttribution: "Productgegevens: Open Food Facts-bijdragers (ODbL)"'));
check("OFF selection opens an inspect-only route", selectFood.includes('food.result_type === "off_branded_food"') && selectFood.includes('openPortal("off"'));
check("OFF selection never opens normal entry form", selectFood.indexOf('openPortal("off"') < selectFood.indexOf("openEntry(food"));
check("OFF dialog has no logging form", !offDialog.includes("phase4Slice3EntryForm") && !offDialog.includes("saveEntry"));
check("OFF dialog announces deferred authoritative logging", offDialog.includes('text("offLoggingPending")') && runtime.includes("4F-C"));
check("OFF dialog keeps attribution", offDialog.includes('text("offAttribution")'));
check("OFF back action preserves search context", runtime.includes("data-phase4-s3-back-off") && runtime.includes('openPortal("search"'));
check("custom and generic selection still opens entry", selectFood.includes("openEntry(food"));
check("USDA is supplemental only below local threshold", supplement.includes("items.length < PHASE4_LOCAL_RESULTS_BEFORE_PROVIDER") && runtime.includes("PHASE4_LOCAL_RESULTS_BEFORE_PROVIDER = 5"));
check("USDA waits for local search result", searchFoods.includes("if (reset && shouldSupplementProvider(requestQuery, search.items)) scheduleProviderSearch"));
check("local query debounce is 240 ms", runtime.includes("PHASE4_LOCAL_SEARCH_DEBOUNCE_MS = 240"));
check("input updates only result containers", renderResults.includes("phase4Slice3LocalSearchResults") && renderResults.includes("phase4Slice3ProviderSearchResults"));
check("search input uses a stable portal node", renderPortal.includes("preserveSearchFocus") && renderPortal.includes("renderSearchResults()") && renderPortal.includes("return"));
check("search stale responses are rejected", searchFoods.includes("search.requestToken !== requestToken") && searchFoods.includes("normalizedSearchQuery(search.query) !== requestQuery"));
check("provider fallback remains bounded", runtime.includes("PHASE4_PROVIDER_SEARCH_PAGE_SIZE = 5") && runtime.includes("PHASE4_PROVIDER_MAX_PAGES = 3"));
check("OFF flow adds no direct table write", !/\.from\(["'](?:nutrition_off_products|nutrition_off_product_names)["']\)\s*\.(?:insert|update|upsert|delete)/i.test(runtime));
check("OFF flow adds no Edge mutation route", !/providerRequest\(["'](?:log|replace)["'][\s\S]{0,250}off_branded_food/.test(runtime));
check("browser mock uses official typed RPC", browser.includes('name === "fmz_phase4_search_nutrition_catalog"'));
check("browser mock covers OFF branded type", browser.includes('result_type: "off_branded_food"'));
check("browser proves local OFF suppresses USDA", browser.includes("sufficient OFF results suppress external provider search"));
check("browser proves OFF inspect-only boundary", browser.includes("OFF selection is inspect-only until 4F-C"));
check("browser proves Dutch generic label", browser.includes("NL logged item uses reviewed Dutch display label"));
check("mobile viewports remain covered", browser.includes("390, height: 844") && browser.includes("320, height: 700"));
check("tablet and desktop remain covered", browser.includes("820, height: 1180") && browser.includes("1440, height: 900"));
check("no MutationObserver is introduced", !runtime.includes("MutationObserver"));
check("no polling is introduced", !/setInterval\s*\(/.test(runtime));
check("no service-role credential is present", !/service[_-]?role/i.test(runtime));
check("no production project ref is present", !/wzsupwcfkkiguuobfevx/.test(runtime));
check("no AI integration is introduced", !/(?:openai|anthropic|gemini|youri[_-]?ai)/i.test(runtime));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
if (failed.length) {
  console.error(`Phase 4F-B static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4F-B static check passed: ${checks.length}`);
