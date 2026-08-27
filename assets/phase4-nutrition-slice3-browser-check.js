const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const slice2 = fs.readFileSync(path.join(root, "assets/phase4-nutrition-slice2.js"), "utf8");
const slice3 = fs.readFileSync(path.join(root, "assets/phase4-nutrition-slice3.js"), "utf8");
const checks = [];

function check(name, condition) {
  checks.push({ name, condition: Boolean(condition) });
}

function harnessSource() {
  return `
    let state = { accountSettings: { language: "nl" }, ui: { loggedIn: true, role: "client" } };
    let onlineReady = true;
    let onlineProfile = { id: "11111111-1111-4111-8111-111111111111", role: "client" };
    const SUPABASE_URL = "https://mokxyyullfhkfalopbzd.supabase.co";
    const SUPABASE_ANON_KEY = "test-publishable-key";
    let testUuidCounter = 100;
    if (!window.crypto.randomUUID) {
      Object.defineProperty(window.crypto, "randomUUID", { value: () => "00000000-0000-4000-8000-" + String(testUuidCounter += 1).padStart(12, "0") });
    }
    let renderNutrition = function legacyNutrition() { window.__legacyNutritionCalls += 1; };
    window.__legacyNutritionCalls = 0;
    window.__calls = [];
    function testToday() {
      const now = new Date();
      return [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0")].join("-");
    }
    function shiftTestDate(value, amount) {
      const parts = value.split("-").map(Number);
      const date = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + amount, 12));
      return [date.getUTCFullYear(), String(date.getUTCMonth() + 1).padStart(2, "0"), String(date.getUTCDate()).padStart(2, "0")].join("-");
    }
    function daysBehind(value) {
      const a = new Date(testToday() + "T12:00:00Z");
      const b = new Date(value + "T12:00:00Z");
      return Math.round((a - b) / 86400000);
    }
    function escapeHTML(value) {
      return String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
    }
    function isLoggedIn() { return Boolean(state.ui.loggedIn); }
    function isOnlineMode() { return true; }
    function todayISO() { return testToday(); }

    const food1 = {
      id: "10000000-0000-4000-8000-000000000001", catalog_scope: "canonical", name: "Oats, raw", brand: "Reviewed",
      reference_amount: 100, reference_unit: "g", reference_mass_grams: 100, reference_volume_ml: null, density_g_per_ml: null,
      energy_kcal: 370, protein_grams: 13, carbohydrate_grams: 62, fat_grams: 7, fiber_grams: 10,
      status: "active", source_provider: "reviewed_catalog", source_version: "v1", provenance: { source: "test" }, metadata: { dutch_display_label: "Havermout" }, updated_at: "2026-08-19T08:00:00Z"
    };
    const food2 = {
      id: "10000000-0000-4000-8000-000000000002", catalog_scope: "canonical", name: "Skyr", brand: null,
      reference_amount: 100, reference_unit: "g", reference_mass_grams: 100, reference_volume_ml: null, density_g_per_ml: null,
      energy_kcal: 62, protein_grams: 11, carbohydrate_grams: 4, fat_grams: 0.2, fiber_grams: 0,
      status: "active", source_provider: "reviewed_catalog", source_version: "v1", provenance: { source: "test" }, updated_at: "2026-08-19T08:00:00Z"
    };
    const customSearchFood = {
      ...food2,
      id: "40000000-0000-4000-8000-000000000001",
      catalog_scope: "custom",
      name: "Eigen protein pudding",
      source_provider: "custom_user",
      metadata: {}
    };
    const offProducts = Array.from({ length: 5 }, (_, index) => ({
      result_type: "off_branded_food",
      source_provider: "open_food_facts",
      source_id: "30000000-0000-4000-8000-" + String(index + 1).padStart(12, "0"),
      barcode: "871000000000" + index,
      display_name: index === 0 ? "Red Bull Energy Drink" : "Red Bull Zero " + (index + 1),
      brand: "Red Bull",
      nutrition_basis: index === 4 ? "per_100_g" : "per_100_ml",
      reference_amount: 100,
      reference_unit: index === 4 ? "g" : "ml",
      energy_kcal_reference: index === 0 ? 45 : 3,
      protein_grams_reference: 0,
      carbohydrate_grams_reference: index === 0 ? 11 : 0,
      fat_grams_reference: 0,
      fiber_grams_reference: null,
      quality_status: "complete",
      loggable: true,
      rank_tier: 1,
      rank_score: index,
      cursor_name: "red bull " + String(index + 1),
      cursor_source: "off_branded_food",
      cursor_id: "30000000-0000-4000-8000-" + String(index + 1).padStart(12, "0")
    }));
    const spaProduct = {
      ...offProducts[0],
      source_id: "30000000-0000-4000-8000-000000000099",
      barcode: "5410013104766",
      display_name: "spa reine blauw",
      brand: "SPA",
      energy_kcal_reference: 0,
      carbohydrate_grams_reference: 0,
      cursor_name: "spa reine blauw",
      cursor_id: "30000000-0000-4000-8000-000000000099"
    };
    function unifiedFood(food, index = 0) {
      const resultType = food.catalog_scope === "custom" ? "custom_food" : "generic_food";
      return {
        result_type: resultType,
        source_provider: food.source_provider,
        source_id: food.id,
        barcode: null,
        display_name: food.metadata?.dutch_display_label || food.name,
        brand: food.brand,
        nutrition_basis: food.reference_unit === "ml" ? "per_100_ml" : "per_100_g",
        reference_amount: food.reference_amount,
        reference_unit: food.reference_unit,
        energy_kcal_reference: food.energy_kcal,
        protein_grams_reference: food.protein_grams,
        carbohydrate_grams_reference: food.carbohydrate_grams,
        fat_grams_reference: food.fat_grams,
        fiber_grams_reference: food.fiber_grams,
        quality_status: resultType === "generic_food" ? "reviewed" : "member",
        loggable: true,
        rank_tier: resultType === "custom_food" ? 0 : 2,
        rank_score: index,
        cursor_name: (food.metadata?.dutch_display_label || food.name).toLowerCase(),
        cursor_source: resultType,
        cursor_id: food.id
      };
    }
    const providerCandidate1 = {
      candidate_id: "81000000-0000-5000-8000-000000000001", candidate_token: "signed-candidate-token-1",
      provider: "usda_fdc", provider_label: "USDA FoodData Central", provider_food_id: "171077",
      name: "Chicken breast, roasted", brand: null, data_type: "Foundation", mapping_version: "phase4_usda_v1",
      reference_amount: 100, reference_unit: "g", kcal: 165, protein: 31, carbohydrates: 0, fat: 3.6, fiber: 0,
      portions: [], derivation: { energy: "2048_kcal", reference_basis: "per_100_g" }, quality: "candidate",
      attribution: { label: "USDA FoodData Central", license: "CC0 1.0", url: "https://fdc.nal.usda.gov/" },
      provenance: { provider: "usda_fdc", provider_food_id: "171077", data_type: "Foundation", mapping_version: "phase4_usda_v1", retrieved_at: "2026-08-20T10:00:00.000Z", source_version: null }
    };
    const providerCandidate2 = {
      ...providerCandidate1,
      candidate_id: "81000000-0000-5000-8000-000000000002", candidate_token: "signed-candidate-token-2",
      provider_food_id: "171496", name: "Turkey breast, roasted", kcal: 147, protein: 30.1, fat: 2.1,
      provenance: { ...providerCandidate1.provenance, provider_food_id: "171496" }
    };
    const transientOffCandidate = {
      candidate_id: "82000000-0000-5000-8000-000000000001",
      candidate_token: "signed-off-candidate-token-1",
      provider: "open_food_facts",
      provider_label: "Open Food Facts",
      provider_food_id: "04006381333931",
      barcode: "04006381333931",
      barcode_original: "4006381333931",
      name: "Barcode test drink",
      brand: "Test brand",
      data_type: "off_branded",
      mapping_version: "phase4_off_barcode_v1",
      reference_amount: 100,
      reference_unit: "ml",
      nutrition_basis: "per_100_ml",
      kcal: 42,
      protein: 0,
      carbohydrates: 10.5,
      fat: 0,
      fiber: null,
      quality: "candidate",
      attribution: { label: "Open Food Facts contributors", license: "ODbL-1.0", url: "https://world.openfoodfacts.org/" },
      provenance: { provider: "open_food_facts", provider_food_id: "04006381333931", reference_basis: "per_100_ml", source_revision: "off_rev:1", source_checksum: "a".repeat(64), retrieved_at: "2026-08-27T10:00:00.000Z" }
    };
    window.__mock = {
      target: null,
      foods: [food1, food2],
      customFoods: [],
      activeItems: [],
      archivedItems: [],
      requests: new Map(),
      replacementRequests: new Map(),
      offRequests: new Map(),
      offReplacementRequests: new Map(),
      failLogNetworkOnce: false,
      failReplaceNetworkOnce: false,
      failReplaceConflictOnce: false,
      failReplaceStaleOnce: false,
      providerRequests: new Map(),
      providerReplacementRequests: new Map(),
      providerCalls: [],
      providerSearchFailure: "",
      providerSearchDelays: {},
      localSearchDelays: {},
      providerLookupFailure: "",
      providerLogCommitThenNetworkOnce: false,
      providerCommitThenNetworkOnce: false,
      providerReplaceStaleOnce: false,
      offLogCommitThenNetworkOnce: false,
      offReplaceCommitThenNetworkOnce: false,
      offReplaceStaleOnce: false,
      transientOffRequests: new Map(),
      transientOffReplacementRequests: new Map(),
      offBarcodeDelay: 0,
      timezone: "UTC"
    };
    function totals(items) {
      const fields = ["energy_kcal", "protein_grams", "carbohydrate_grams", "fat_grams", "fiber_grams"];
      const result = {};
      for (const field of fields) result[field] = items.reduce((sum, item) => sum + Number(item[field + "_snapshot"] || 0), 0);
      return result;
    }
    function dayPayload(date) {
      const items = window.__mock.activeItems.filter((item) => item.log_date === date && item.status === "active").map((item) => ({ ...item }));
      return {
        log_date: date,
        log: items.length ? { id: "20000000-0000-4000-8000-000000000001", log_date: date, status: "active", timezone_name: window.__mock.timezone } : null,
        target: window.__mock.target ? { ...window.__mock.target } : null,
        items,
        totals: totals(items)
      };
    }
    function itemFromArgs(args, food, id, requestId, original = null) {
      const factor = Number(args.p_consumed_quantity) / Number(food.reference_amount);
      return {
        id,
        user_id: onlineProfile.id,
        food_log_id: "20000000-0000-4000-8000-000000000001",
        food_id: food.id,
        food_portion_id: args.p_food_portion_id || null,
        meal_moment: args.p_meal_moment,
        sort_order: original?.sort_order || window.__mock.activeItems.filter((item) => item.meal_moment === args.p_meal_moment).length,
        consumed_quantity: args.p_consumed_quantity,
        consumed_unit: args.p_consumed_unit,
        food_name_snapshot: food.name,
        brand_snapshot: food.brand,
        reference_amount_snapshot: food.reference_amount,
        reference_unit_snapshot: food.reference_unit,
        calculation_basis: args.p_food_portion_id ? "portion_conversion" : "direct_reference",
        energy_kcal_snapshot: Number((food.energy_kcal * factor).toFixed(3)),
        protein_grams_snapshot: Number((food.protein_grams * factor).toFixed(3)),
        carbohydrate_grams_snapshot: Number((food.carbohydrate_grams * factor).toFixed(3)),
        fat_grams_snapshot: Number((food.fat_grams * factor).toFixed(3)),
        fiber_grams_snapshot: Number((food.fiber_grams * factor).toFixed(3)),
        source_provider_snapshot: food.source_provider,
        provider_food_id_snapshot: null,
        source_version_snapshot: food.source_version,
        provenance_snapshot: food.provenance,
        notes: args.p_notes || null,
        status: "active",
        request_id: requestId,
        consumed_at: original?.consumed_at || args.p_consumed_at,
        updated_at: "2026-08-19T10:" + String(window.__calls.length).padStart(2, "0") + ":00Z",
        archived_at: null,
        log_date: original?.log_date || args.p_log_date
      };
    }
    function requestFingerprint(args) {
      return JSON.stringify(args, Object.keys(args).sort());
    }
    function providerItemFromBody(body, candidate, original = null) {
      const factor = Number(body.consumed_quantity) / 100;
      const operation = original ? "provider_replace" : "provider_log";
      return {
        id: original ? body.replacement_item_id : body.item_id,
        user_id: onlineProfile.id,
        food_log_id: original?.food_log_id || "20000000-0000-4000-8000-000000000001",
        food_id: null,
        food_portion_id: null,
        meal_moment: body.meal_moment,
        sort_order: original?.sort_order || window.__mock.activeItems.filter((item) => item.meal_moment === body.meal_moment).length,
        consumed_quantity: body.consumed_quantity,
        consumed_unit: "g",
        food_name_snapshot: candidate.name,
        brand_snapshot: candidate.brand,
        reference_amount_snapshot: 100,
        reference_unit_snapshot: "g",
        calculation_basis: "direct_reference",
        energy_kcal_snapshot: Number((candidate.kcal * factor).toFixed(3)),
        protein_grams_snapshot: Number((candidate.protein * factor).toFixed(3)),
        carbohydrate_grams_snapshot: Number((candidate.carbohydrates * factor).toFixed(3)),
        fat_grams_snapshot: Number((candidate.fat * factor).toFixed(3)),
        fiber_grams_snapshot: candidate.fiber === null ? null : Number((candidate.fiber * factor).toFixed(3)),
        source_provider_snapshot: "usda_fdc",
        provider_food_id_snapshot: candidate.provider_food_id,
        source_version_snapshot: null,
        provenance_snapshot: { provider: "usda_fdc", candidate_id: candidate.candidate_id },
        notes: body.notes || null,
        status: "active",
        request_id: body.request_id,
        consumed_at: original?.consumed_at || body.consumed_at,
        updated_at: original ? "2026-08-20T12:34:56.234567+00:00" : "2026-08-20T12:34:56.123456+00:00",
        archived_at: null,
        log_date: original?.log_date || body.log_date,
        metadata: { operation, ...(original ? { replaces_item_id: original.id } : {}) }
      };
    }
    function offItemFromArgs(args, product, original = null) {
      const factor = Number(args.p_consumed_quantity) / 100;
      const operation = original ? "off_replace" : "off_log";
      return {
        id: original ? args.p_replacement_item_id : args.p_item_id,
        user_id: onlineProfile.id,
        food_log_id: original?.food_log_id || "20000000-0000-4000-8000-000000000001",
        food_id: null,
        food_portion_id: null,
        meal_moment: args.p_meal_moment,
        sort_order: original?.sort_order || window.__mock.activeItems.filter((item) => item.meal_moment === args.p_meal_moment).length,
        consumed_quantity: args.p_consumed_quantity,
        consumed_unit: product.reference_unit,
        food_name_snapshot: product.display_name,
        brand_snapshot: product.brand,
        reference_amount_snapshot: 100,
        reference_unit_snapshot: product.reference_unit,
        calculation_basis: "direct_reference",
        energy_kcal_snapshot: Number((product.energy_kcal_reference * factor).toFixed(3)),
        protein_grams_snapshot: Number((product.protein_grams_reference * factor).toFixed(3)),
        carbohydrate_grams_snapshot: Number((product.carbohydrate_grams_reference * factor).toFixed(3)),
        fat_grams_snapshot: Number((product.fat_grams_reference * factor).toFixed(3)),
        fiber_grams_snapshot: product.fiber_grams_reference === null ? null : Number((product.fiber_grams_reference * factor).toFixed(3)),
        source_provider_snapshot: "open_food_facts",
        provider_food_id_snapshot: product.barcode.padStart(14, "0"),
        source_version_snapshot: "e544a38353692b2df59df78f47393990a578eb8e",
        provenance_snapshot: { provider: "open_food_facts", candidate_id: product.source_id, reference_basis: product.nutrition_basis, license_code: "ODbL-1.0" },
        notes: args.p_notes || null,
        status: "active",
        request_id: original ? args.p_replacement_request_id : args.p_request_id,
        consumed_at: original?.consumed_at || args.p_consumed_at,
        updated_at: original ? "2026-08-26T12:34:56.234567+00:00" : "2026-08-26T12:34:56.123456+00:00",
        archived_at: null,
        log_date: original?.log_date || args.p_log_date,
        metadata: {
          operation,
          off_product_id: product.source_id,
          candidate_id: product.source_id,
          reference_basis: product.nutrition_basis,
          display_name_nl: product.display_name,
          ...(original ? { replaces_item_id: original.id } : {})
        }
      };
    }
    function transientOffItemFromBody(body, candidate, original = null) {
      const factor = Number(body.consumed_quantity) / 100;
      return {
        id: original ? body.replacement_item_id : body.item_id,
        user_id: onlineProfile.id,
        food_log_id: original?.food_log_id || "20000000-0000-4000-8000-000000000001",
        food_id: null,
        food_portion_id: null,
        meal_moment: body.meal_moment,
        sort_order: original?.sort_order || window.__mock.activeItems.filter((item) => item.meal_moment === body.meal_moment).length,
        consumed_quantity: body.consumed_quantity,
        consumed_unit: candidate.reference_unit,
        food_name_snapshot: candidate.name,
        brand_snapshot: candidate.brand,
        reference_amount_snapshot: 100,
        reference_unit_snapshot: candidate.reference_unit,
        calculation_basis: "direct_reference",
        energy_kcal_snapshot: Number((candidate.kcal * factor).toFixed(3)),
        protein_grams_snapshot: Number((candidate.protein * factor).toFixed(3)),
        carbohydrate_grams_snapshot: Number((candidate.carbohydrates * factor).toFixed(3)),
        fat_grams_snapshot: Number((candidate.fat * factor).toFixed(3)),
        fiber_grams_snapshot: candidate.fiber === null ? null : Number((candidate.fiber * factor).toFixed(3)),
        source_provider_snapshot: "open_food_facts",
        provider_food_id_snapshot: candidate.provider_food_id,
        source_version_snapshot: candidate.provenance.source_revision,
        provenance_snapshot: { ...candidate.provenance },
        notes: body.notes || null,
        status: "active",
        request_id: body.request_id,
        consumed_at: original?.consumed_at || body.consumed_at,
        updated_at: original ? "2026-08-27T12:34:56.234567+00:00" : "2026-08-27T12:34:56.123456+00:00",
        archived_at: null,
        log_date: original?.log_date || body.log_date,
        metadata: {
          operation: original ? "transient_off_replace" : "transient_off_log",
          candidate_id: candidate.candidate_id,
          reference_basis: candidate.nutrition_basis,
          ...(original ? { replaces_item_id: original.id } : {})
        }
      };
    }
    function jsonResponse(status, value) {
      return new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
    }
    const supabaseClient = {
      auth: {
        async getSession() {
          return { data: { session: { access_token: "test-member-jwt" } }, error: null };
        }
      },
      rpc: async (name, args = {}) => {
        window.__calls.push({ type: "rpc", name, args: JSON.parse(JSON.stringify(args)) });
        await Promise.resolve();
        if (name === "fmz_phase4_set_nutrition_timezone") {
          window.__mock.timezone = args.p_timezone_name;
          return { data: { timezone_name: args.p_timezone_name }, error: null };
        }
        if (name === "fmz_phase4_get_current_nutrition_target") return { data: window.__mock.target, error: null };
        if (name === "fmz_phase4_save_member_target") {
          window.__mock.target = { id: args.p_target_id, request_id: args.p_request_id, energy_kcal: args.p_energy_kcal, protein_grams: args.p_protein_grams, carbohydrate_grams: args.p_carbohydrate_grams, fat_grams: args.p_fat_grams, status: "active" };
          return { data: { ...window.__mock.target }, error: null };
        }
        if (name === "fmz_phase4_get_nutrition_day") {
          if (daysBehind(args.p_log_date) > 6) return { data: null, error: { code: "42501", message: "Free Nutrition history is limited to seven local calendar days" } };
          return { data: dayPayload(args.p_log_date), error: null };
        }
        if (name === "fmz_phase4_search_nutrition_catalog") {
          const query = String(args.p_query || "").toLowerCase();
          const delay = Number(window.__mock.localSearchDelays[query] || 0);
          if (delay > 0) await new Promise((resolve) => setTimeout(resolve, delay));
          let rows = query.includes("empty") ? [] : window.__mock.foods.map(unifiedFood);
          if (query.includes("red bull")) rows = offProducts;
          if (query.includes("spa reine")) rows = [spaProduct];
          if (query.includes("mixed")) rows = [unifiedFood(customSearchFood), offProducts[0], unifiedFood(window.__mock.foods[0], 1)];
          return { data: rows.slice(0, args.p_page_size).map((food) => ({ ...food })), error: null };
        }
        if (name === "fmz_phase4_upsert_custom_food" || name === "fmz_phase4_upsert_custom_food_with_barcode") {
          const food = {
            id: args.p_food_id, catalog_scope: "custom", name: args.p_name, brand: args.p_brand,
            barcode: args.p_barcode || null,
            reference_amount: args.p_reference_amount, reference_unit: args.p_reference_unit,
            reference_mass_grams: args.p_reference_mass_grams, reference_volume_ml: args.p_reference_volume_ml,
            density_g_per_ml: null, energy_kcal: args.p_energy_kcal, protein_grams: args.p_protein_grams,
            carbohydrate_grams: args.p_carbohydrate_grams, fat_grams: args.p_fat_grams, fiber_grams: args.p_fiber_grams,
            status: "active", source_provider: "custom_user", source_version: null, provenance: { source: "member_entry" }, updated_at: "2026-08-19T09:00:00Z"
          };
          window.__mock.foods.push(food);
          window.__mock.customFoods.push(food);
          return { data: { ...food }, error: null };
        }
        if (name === "fmz_phase4_log_food_item") {
          const fingerprint = requestFingerprint(args);
          const existing = window.__mock.requests.get(args.p_request_id);
          if (existing) {
            if (existing.fingerprint !== fingerprint) return { data: null, error: { code: "23505", message: "request UUID changed payload" } };
            return { data: { item: { ...existing.item }, day: dayPayload(existing.item.log_date), idempotent_replay: true }, error: null };
          }
          if (window.__mock.failLogNetworkOnce) {
            window.__mock.failLogNetworkOnce = false;
            return { data: null, error: { message: "network unavailable" } };
          }
          const food = window.__mock.foods.find((entry) => entry.id === args.p_food_id);
          const item = itemFromArgs(args, food, args.p_item_id, args.p_request_id);
          window.__mock.activeItems.push(item);
          window.__mock.requests.set(args.p_request_id, { fingerprint, item });
          return { data: { item: { ...item }, day: dayPayload(args.p_log_date), idempotent_replay: false }, error: null };
        }
        if (name === "fmz_phase4_log_off_food_item") {
          const fingerprint = requestFingerprint(args);
          const existing = window.__mock.offRequests.get(args.p_request_id);
          if (existing) {
            if (existing.fingerprint !== fingerprint) return { data: null, error: { code: "23505", message: "OFF request UUID was already used with a different payload" } };
            return { data: { item: { ...existing.item }, day: dayPayload(existing.item.log_date), idempotent_replay: true }, error: null };
          }
          const product = offProducts.find((entry) => entry.source_id === args.p_off_product_id);
          if (!product || product.reference_unit !== args.p_consumed_unit) return { data: null, error: { code: "22023", message: "OFF quantity unit must match the catalog nutrition basis" } };
          const item = offItemFromArgs(args, product);
          window.__mock.activeItems.push(item);
          window.__mock.offRequests.set(args.p_request_id, { fingerprint, item });
          if (window.__mock.offLogCommitThenNetworkOnce) {
            window.__mock.offLogCommitThenNetworkOnce = false;
            return { data: null, error: { message: "network unavailable after commit" } };
          }
          return { data: { item: { ...item }, day: dayPayload(args.p_log_date), idempotent_replay: false }, error: null };
        }
        if (name === "fmz_phase4_replace_food_log_item") {
          const fingerprint = requestFingerprint(args);
          const existing = window.__mock.replacementRequests.get(args.p_replacement_request_id);
          if (existing) {
            if (existing.fingerprint !== fingerprint) return { data: null, error: { code: "23505", message: "replacement request UUID was already used with a different payload" } };
            return { data: { replacement_item: { ...existing.item }, archived_original: { id: existing.original.id, status: "archived" }, day: dayPayload(existing.item.log_date), idempotent_replay: true }, error: null };
          }
          if (window.__mock.failReplaceNetworkOnce) {
            window.__mock.failReplaceNetworkOnce = false;
            return { data: null, error: { message: "network unavailable" } };
          }
          if (window.__mock.failReplaceConflictOnce) {
            window.__mock.failReplaceConflictOnce = false;
            return { data: null, error: { code: "23505", message: "replacement request UUID was already used with a different payload" } };
          }
          if (window.__mock.failReplaceStaleOnce) {
            window.__mock.failReplaceStaleOnce = false;
            return { data: null, error: { code: "40001", message: "food log item changed; refresh before replacing" } };
          }
          const index = window.__mock.activeItems.findIndex((item) => item.id === args.p_original_item_id && item.status === "active");
          if (index < 0) return { data: null, error: { code: "40001", message: "food log item is no longer active; refresh before replacing" } };
          const original = window.__mock.activeItems[index];
          if (original.updated_at !== args.p_expected_original_updated_at) return { data: null, error: { code: "40001", message: "food log item changed; refresh before replacing" } };
          const food = window.__mock.foods.find((entry) => entry.id === args.p_food_id);
          const replacementItem = itemFromArgs(args, food, args.p_replacement_item_id, args.p_replacement_request_id, original);
          original.status = "archived";
          original.archived_at = "2026-08-19T11:00:00Z";
          window.__mock.archivedItems.push({ ...original });
          window.__mock.activeItems.splice(index, 1, replacementItem);
          window.__mock.replacementRequests.set(args.p_replacement_request_id, { fingerprint, item: replacementItem, original });
          return { data: { replacement_item: { ...replacementItem }, archived_original: { id: original.id, status: "archived" }, day: dayPayload(replacementItem.log_date), idempotent_replay: false }, error: null };
        }
        if (name === "fmz_phase4_replace_off_food_log_item") {
          const fingerprint = requestFingerprint(args);
          const existing = window.__mock.offReplacementRequests.get(args.p_replacement_request_id);
          if (existing) {
            if (existing.fingerprint !== fingerprint) return { data: null, error: { code: "23505", message: "OFF replacement request UUID was already used with a different payload" } };
            return { data: { replacement_item: { ...existing.item }, archived_original: { id: existing.original.id, status: "archived" }, day: dayPayload(existing.item.log_date), idempotent_replay: true }, error: null };
          }
          if (window.__mock.offReplaceStaleOnce) {
            window.__mock.offReplaceStaleOnce = false;
            return { data: null, error: { code: "40001", message: "food log item changed; refresh before replacing" } };
          }
          const index = window.__mock.activeItems.findIndex((item) => item.id === args.p_original_item_id && item.status === "active");
          if (index < 0) return { data: null, error: { code: "40001", message: "food log item changed; refresh before replacing" } };
          const original = window.__mock.activeItems[index];
          if (original.updated_at !== args.p_expected_original_updated_at) return { data: null, error: { code: "40001", message: "food log item changed; refresh before replacing" } };
          const product = offProducts.find((entry) => entry.source_id === args.p_off_product_id);
          if (!product || product.reference_unit !== args.p_consumed_unit) return { data: null, error: { code: "22023", message: "OFF quantity unit must match the catalog nutrition basis" } };
          const replacementItem = offItemFromArgs(args, product, original);
          original.status = "archived";
          original.archived_at = "2026-08-26T13:00:00Z";
          window.__mock.archivedItems.push({ ...original });
          window.__mock.activeItems.splice(index, 1, replacementItem);
          window.__mock.offReplacementRequests.set(args.p_replacement_request_id, { fingerprint, item: replacementItem, original });
          if (window.__mock.offReplaceCommitThenNetworkOnce) {
            window.__mock.offReplaceCommitThenNetworkOnce = false;
            return { data: null, error: { message: "network unavailable after commit" } };
          }
          return { data: { replacement_item: { ...replacementItem }, archived_original: { id: original.id, status: "archived" }, day: dayPayload(replacementItem.log_date), idempotent_replay: false }, error: null };
        }
        if (name === "fmz_phase4_archive_food_log_item") {
          const index = window.__mock.activeItems.findIndex((item) => item.id === args.p_item_id);
          if (index < 0) return { data: { item: null, day: dayPayload(testToday()), idempotent_replay: true }, error: null };
          const item = window.__mock.activeItems[index];
          if (item.updated_at !== args.p_expected_updated_at) return { data: null, error: { code: "40001", message: "food log item changed; refresh before archiving" } };
          item.status = "archived";
          window.__mock.archivedItems.push({ ...item });
          window.__mock.activeItems.splice(index, 1);
          return { data: { item: { ...item }, day: dayPayload(item.log_date), idempotent_replay: false }, error: null };
        }
        return { data: null, error: { message: "unexpected rpc " + name } };
      },
      from: (table) => {
        const filters = {};
        const query = {
          select() { return query; },
          eq(column, value) { filters[column] = value; return query; },
          in(column, values) { filters[column] = Array.isArray(values) ? [...values] : []; return query; },
          order() { return query; },
          async range(start, end) {
            window.__calls.push({ type: "select", table, start, end, filters: { ...filters } });
            if (table === "foods") return { data: window.__mock.customFoods.slice(start, end + 1).map((food) => ({ ...food })), error: null };
            return { data: [], error: null };
          },
          async maybeSingle() {
            window.__calls.push({ type: "select-one", table, filters: { ...filters } });
            if (table === "foods") return { data: { ...window.__mock.foods.find((food) => food.id === filters.id && food.status === "active") }, error: null };
            return { data: null, error: null };
          },
          async single() { return query.maybeSingle(); },
          then(resolve, reject) {
            const data = table === "food_portions"
              ? [{ id: "30000000-0000-4000-8000-000000000001", food_id: filters.food_id, label: "Kom", amount: 1, unit: "serving", equivalent_amount: 30, equivalent_unit: "g", status: "active" }]
              : table === "foods" && Array.isArray(filters.id)
                ? window.__mock.foods.filter((food) => filters.id.includes(food.id)).map(({ id, name, metadata }) => ({ id, name, metadata }))
                : [];
            return Promise.resolve({ data, error: null }).then(resolve, reject);
          }
        };
        return query;
      }
    };
    function providerCandidateForToken(token) {
      if (token === providerCandidate1.candidate_token) return providerCandidate1;
      if (token === providerCandidate2.candidate_token) return providerCandidate2;
      return null;
    }
    window.fetch = async (url, init = {}) => {
      const route = new URL(String(url)).pathname.split("/").filter(Boolean).at(-1);
      const body = JSON.parse(String(init.body || "{}"));
      window.__mock.providerCalls.push({ route, body: JSON.parse(JSON.stringify(body)) });
      if (init.method !== "POST" || init.headers?.Authorization !== "Bearer test-member-jwt" || init.headers?.apikey !== SUPABASE_ANON_KEY) {
        return jsonResponse(401, { ok: false, error: { code: "unauthorized", message: "Authentication is required." } });
      }
      if (route === "off-barcode") {
        if (window.__mock.offBarcodeDelay) await new Promise((resolve) => setTimeout(resolve, window.__mock.offBarcodeDelay));
        if (body.barcode === "00036000291452") {
          const food = window.__mock.foods[0];
          return jsonResponse(200, { ok: true, data: { cache: "not_checked", source: "local", result: { ...unifiedFood(food), id: food.id, name: food.name, metadata: food.metadata, energy_kcal: food.energy_kcal, protein_grams: food.protein_grams, carbohydrate_grams: food.carbohydrate_grams, fat_grams: food.fat_grams, fiber_grams: food.fiber_grams } } });
        }
        if (body.barcode === "05410013128298") return jsonResponse(422, { ok: false, error: { code: "off_product_market_unsupported", message: "Product is not eligible.", details: { suggested_query: "SPA Reine" } } });
        if (body.barcode === "00000096385074") return jsonResponse(404, { ok: false, error: { code: "off_product_not_found", message: "No product found." } });
        return jsonResponse(200, { ok: true, data: { cache: "miss", source: "open_food_facts", result: { ...transientOffCandidate }, provider: "open_food_facts" } });
      }
      if (route === "off-log") {
        if (body.candidate_token !== transientOffCandidate.candidate_token) return jsonResponse(409, { ok: false, error: { code: "off_candidate_token_invalid", message: "Candidate token invalid." } });
        const fingerprint = requestFingerprint(body);
        const existing = window.__mock.transientOffRequests.get(body.request_id);
        if (existing) return jsonResponse(200, { ok: true, data: { cache: "hit", result: { item: { ...existing.item }, day: dayPayload(existing.item.log_date), idempotent_replay: true } } });
        const item = transientOffItemFromBody(body, transientOffCandidate);
        window.__mock.activeItems.push(item);
        window.__mock.transientOffRequests.set(body.request_id, { fingerprint, item });
        return jsonResponse(200, { ok: true, data: { cache: "hit", result: { item: { ...item }, day: dayPayload(item.log_date), idempotent_replay: false } } });
      }
      if (route === "off-replace") {
        const index = window.__mock.activeItems.findIndex((item) => item.id === body.original_item_id && item.status === "active");
        if (index < 0) return jsonResponse(403, { ok: false, error: { code: "off_replace_forbidden", message: "Replacement is unavailable." } });
        const original = window.__mock.activeItems[index];
        if (original.updated_at !== body.expected_original_updated_at) return jsonResponse(409, { ok: false, error: { code: "off_replace_stale", message: "Item changed." } });
        const item = transientOffItemFromBody(body, transientOffCandidate, original);
        original.status = "archived";
        window.__mock.archivedItems.push({ ...original });
        window.__mock.activeItems.splice(index, 1, item);
        return jsonResponse(200, { ok: true, data: { cache: body.candidate_token ? "hit" : "not_checked", result: { replacement_item: { ...item }, archived_original: { id: original.id, status: "archived" }, day: dayPayload(item.log_date), idempotent_replay: false } } });
      }
      if (route === "search") {
        if (window.__mock.providerSearchFailure === "rate") return jsonResponse(429, { ok: false, error: { code: "provider_rate_limited", message: "Provider is temporarily rate limited." } });
        if (window.__mock.providerSearchFailure === "unavailable") return jsonResponse(503, { ok: false, error: { code: "provider_unavailable", message: "Provider is temporarily unavailable." } });
        const delay = Number(window.__mock.providerSearchDelays[body.query] || 0);
        if (delay > 0) await new Promise((resolve) => setTimeout(resolve, delay));
        const results = body.query.toLowerCase().includes("empty") ? [] : body.query.toLowerCase().includes("turkey") ? [providerCandidate2] : [providerCandidate1];
        return jsonResponse(200, { ok: true, data: { cache: "miss", results, provider: "usda_fdc" } });
      }
      if (route === "lookup") {
        if (window.__mock.providerLookupFailure === "candidate") return jsonResponse(409, { ok: false, error: { code: "candidate_token_expired", message: "Candidate token expired." } });
        const candidate = providerCandidateForToken(body.candidate_token);
        if (!candidate) return jsonResponse(409, { ok: false, error: { code: "candidate_token_invalid", message: "Candidate token invalid." } });
        return jsonResponse(200, { ok: true, data: { cache: "hit", result: { ...candidate }, provider: "usda_fdc" } });
      }
      if (route === "log") {
        const fingerprint = requestFingerprint(body);
        const existing = window.__mock.providerRequests.get(body.request_id);
        if (existing) {
          if (existing.fingerprint !== fingerprint) return jsonResponse(409, { ok: false, error: { code: "provider_log_request_conflict", message: "Request identity changed." } });
          return jsonResponse(200, { ok: true, data: { cache: "hit", result: { item: { ...existing.item }, day: dayPayload(existing.item.log_date), idempotent_replay: true }, provider: "usda_fdc" } });
        }
        const candidate = providerCandidateForToken(body.candidate_token);
        if (!candidate) return jsonResponse(409, { ok: false, error: { code: "candidate_token_invalid", message: "Candidate token invalid." } });
        const item = providerItemFromBody(body, candidate);
        window.__mock.activeItems.push(item);
        window.__mock.providerRequests.set(body.request_id, { fingerprint, item });
        if (window.__mock.providerLogCommitThenNetworkOnce) {
          window.__mock.providerLogCommitThenNetworkOnce = false;
          throw new TypeError("network unavailable after commit");
        }
        return jsonResponse(200, { ok: true, data: { cache: "hit", result: { item: { ...item }, day: dayPayload(body.log_date), idempotent_replay: false }, provider: "usda_fdc" } });
      }
      if (route === "replace") {
        const fingerprint = requestFingerprint(body);
        const existing = window.__mock.providerReplacementRequests.get(body.request_id);
        if (existing) {
          if (existing.fingerprint !== fingerprint) return jsonResponse(409, { ok: false, error: { code: "provider_replace_request_conflict", message: "Request identity changed." } });
          return jsonResponse(200, { ok: true, data: { cache: "hit", result: { replacement_item: { ...existing.item }, archived_original: { id: existing.original.id, status: "archived" }, day: dayPayload(existing.item.log_date), idempotent_replay: true }, provider: "usda_fdc" } });
        }
        if (window.__mock.providerReplaceStaleOnce) {
          window.__mock.providerReplaceStaleOnce = false;
          return jsonResponse(409, { ok: false, error: { code: "provider_replace_stale", message: "Food log item changed; refresh and try again." } });
        }
        const index = window.__mock.activeItems.findIndex((item) => item.id === body.original_item_id && item.status === "active");
        if (index < 0) return jsonResponse(403, { ok: false, error: { code: "provider_replace_forbidden", message: "Provider food logging is not allowed." } });
        const original = window.__mock.activeItems[index];
        if (original.updated_at !== body.expected_original_updated_at) return jsonResponse(409, { ok: false, error: { code: "provider_replace_stale", message: "Food log item changed; refresh and try again." } });
        const candidate = body.candidate_token
          ? providerCandidateForToken(body.candidate_token)
          : original.provider_food_id_snapshot === providerCandidate2.provider_food_id ? providerCandidate2 : providerCandidate1;
        if (!candidate) return jsonResponse(409, { ok: false, error: { code: "candidate_token_invalid", message: "Candidate token invalid." } });
        const replacementItem = providerItemFromBody(body, candidate, original);
        original.status = "archived";
        original.archived_at = "2026-08-20T12:35:00.000000+00:00";
        window.__mock.archivedItems.push({ ...original });
        window.__mock.activeItems.splice(index, 1, replacementItem);
        window.__mock.providerReplacementRequests.set(body.request_id, { fingerprint, item: replacementItem, original });
        if (window.__mock.providerCommitThenNetworkOnce) {
          window.__mock.providerCommitThenNetworkOnce = false;
          throw new TypeError("network unavailable after commit");
        }
        return jsonResponse(200, { ok: true, data: { cache: "hit", result: { replacement_item: { ...replacementItem }, archived_original: { id: original.id, status: "archived" }, day: dayPayload(replacementItem.log_date), idempotent_replay: false }, provider: "usda_fdc" } });
      }
      return jsonResponse(404, { ok: false, error: { code: "route_not_found", message: "Route not found." } });
    };
    ${slice2}
    ${slice3}
    window.__renderNutrition = () => renderNutrition();
    window.__setLanguage = (value) => { state.accountSettings.language = value; renderNutrition(); };
    window.__setRole = (value) => { state.ui.role = value; renderNutrition(); };
  `;
}

async function waitDay(page) {
  await page.waitForFunction(() => window.FMZ_PHASE4_NUTRITION_SLICE3?.state().dayStatus === "ready");
}

async function openFirstItem(page) {
  await page.locator("[data-phase4-s3-item]").first().click();
  await page.waitForSelector("#phase4Slice3Portal");
}

async function startEdit(page) {
  await openFirstItem(page);
  await page.getByRole("button", { name: "Bewerken" }).click();
  await page.waitForSelector("#phase4Slice3EntryForm");
}

async function searchGeometry(page) {
  return page.evaluate(() => {
    const input = document.querySelector('#phase4Slice3SearchForm input[name="query"]');
    const sheet = document.querySelector(".phase4-s3-search-sheet");
    const results = document.querySelector(".phase4-s3-search-results");
    const inputRect = input?.getBoundingClientRect();
    const sheetRect = sheet?.getBoundingClientRect();
    const resultsStyle = results ? getComputedStyle(results) : null;
    return {
      inputTop: inputRect?.top ?? -1,
      sheetTop: sheetRect?.top ?? -1,
      sheetBottom: sheetRect?.bottom ?? -1,
      pageScrollY: window.scrollY,
      focused: document.activeElement === input,
      resultsOverflowY: resultsStyle?.overflowY || "",
      overflowAnchor: resultsStyle?.overflowAnchor || "",
      resultsClientHeight: results?.clientHeight || 0,
      resultsScrollHeight: results?.scrollHeight || 0
    };
  });
}

function searchGeometryStable(before, after) {
  return ["inputTop", "sheetTop", "sheetBottom", "pageScrollY"].every((key) => Math.abs(before[key] - after[key]) <= 1);
}

async function run() {
  const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
  const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(edgePath) ? edgePath : undefined });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.on("pageerror", (error) => checks.push({ name: `browser page error: ${error.message}`, condition: false }));
  await page.setContent(`<!doctype html><html><head><style>
    :root { --bg:#111820; --surface:#18232c; --surface-2:#202d36; --line:#35434d; --text:#f4f7f8; --muted:#a8b4bb; --shadow:0 12px 32px rgba(0,0,0,.25); }
    * { box-sizing:border-box; } body { margin:0; padding:16px; background:var(--bg); color:var(--text); font:16px Arial,sans-serif; }
    button,input,select,textarea { font:inherit; border:1px solid var(--line); border-radius:6px; padding:8px 10px; background:var(--surface-2); color:var(--text); }
    .primary-btn,.secondary-btn { min-height:44px; } .field { display:grid; gap:6px; } .muted,.eyebrow { color:var(--muted); } .sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); }
    .view { display:block; } .legacy { min-height:40px; }
  </style></head><body><section id="nutrition" class="view"><div class="legacy">Legacy nutrition</div></section></body></html>`);
  await page.addScriptTag({ content: harnessSource() });
  await page.evaluate(() => window.__renderNutrition());
  await waitDay(page);

  check("Slice 3 member Nutrition renders", await page.getByRole("heading", { name: "Voeding", exact: true }).count() === 1);
  check("four meal sections render", await page.locator(".phase4-s3-meal").count() === 4);
  check("no-target state is truthful", await page.getByText("Nog geen dagdoel. Je invoer wordt wel veilig bijgehouden.").count() === 1);
  check("empty day state renders", await page.getByText("Nog geen voeding gelogd op deze dag.").count() === 1);
  check("legacy member Nutrition stays hidden", await page.locator("#nutrition.phase4-nutrition-active").count() === 1 && await page.locator(".legacy").isHidden());
  check("timezone is synchronized before day read", await page.evaluate(() => {
    const calls = window.__calls.filter((call) => call.type === "rpc");
    return calls.findIndex((call) => call.name === "fmz_phase4_set_nutrition_timezone") < calls.findIndex((call) => call.name === "fmz_phase4_get_nutrition_day");
  }));
  check("EAN-8 UPC-A EAN-13 and GTIN-14 normalize as strings", await page.evaluate(() => {
    const normalize = window.FMZ_PHASE4_NUTRITION_SLICE3.normalizeBarcode;
    return normalize("96385074") === "00000096385074"
      && normalize("036000291452") === "00036000291452"
      && normalize("4006381333931") === "04006381333931"
      && normalize("04006381333931") === "04006381333931";
  }));

  await page.getByRole("button", { name: "Dagdoel instellen" }).click();
  await page.waitForTimeout(50);
  if (await page.locator("#phase4TargetForm").count() === 0) {
    throw new Error(`Target dialog did not open: ${JSON.stringify(await page.evaluate(() => ({ slice2: window.FMZ_PHASE4_NUTRITION_SLICE2?.state(), slice3: window.FMZ_PHASE4_NUTRITION_SLICE3?.state(), portals: Array.from(document.querySelectorAll('[id*=phase4]')).map((element) => element.id) })))}`);
  }
  await page.locator('#phase4TargetForm input[name="energy"]').fill("2200");
  await page.locator('#phase4TargetForm input[name="protein"]').fill("180");
  await page.locator('#phase4TargetForm input[name="carbohydrate"]').fill("240");
  await page.locator('#phase4TargetForm input[name="fat"]').fill("70");
  await page.getByRole("button", { name: "Doelen opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4NutritionPortal"));
  check("Slice 2 target authority updates Slice 3", await page.locator(".phase4-s3-progress").first().getByText("2.200 kcal", { exact: true }).count() === 1 && await page.getByRole("button", { name: "Dagdoel aanpassen" }).count() === 1);

  await page.locator('[data-phase4-s3-add="breakfast"]').click();
  await page.getByRole("button", { name: "Barcode scannen" }).click();
  check("barcode scanner is contextual inside add-food", await page.getByRole("heading", { name: "Barcode zoeken" }).count() === 1);
  await page.getByRole("button", { name: "Camera starten" }).click();
  check("camera unavailable keeps manual fallback visible", await page.locator('#phase4Slice3BarcodeForm input[name="barcode"]').count() === 1 && await page.getByText(/handmatige barcode-invoer/).count() === 1);
  await page.locator('#phase4Slice3BarcodeForm input[name="barcode"]').fill("123");
  await page.locator("#phase4Slice3BarcodeForm").evaluate((form) => form.requestSubmit());
  check("invalid barcode is rejected before Edge request", await page.getByText(/geldige EAN-8/).count() === 1 && await page.evaluate(() => window.__mock.providerCalls.filter((call) => call.route === "off-barcode").length === 0));
  await page.locator('#phase4Slice3BarcodeForm input[name="barcode"]').fill(" 0360 0029 1452 ");
  await page.locator("#phase4Slice3BarcodeForm").evaluate((form) => form.requestSubmit());
  await page.waitForSelector("#phase4Slice3EntryForm");
  check("manual barcode strips harmless spacing and sends canonical GTIN-14 once", await page.getByText("Havermout", { exact: true }).count() >= 1 && await page.evaluate(() => window.__mock.providerCalls.filter((call) => call.route === "off-barcode" && call.body.barcode === "00036000291452").length === 1));
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  await page.locator('[data-phase4-s3-add="breakfast"]').click();
  await page.getByRole("button", { name: "Barcode scannen" }).click();
  await page.evaluate(() => { window.__mock.offBarcodeDelay = 40; });
  await page.locator('#phase4Slice3BarcodeForm input[name="barcode"]').fill("4006381333931");
  await page.locator("#phase4Slice3BarcodeForm").evaluate((form) => { form.requestSubmit(); form.requestSubmit(); });
  await page.getByRole("heading", { name: "Product bekijken" }).waitFor();
  check("duplicate barcode submits create one canonical lookup", await page.evaluate(() => window.__mock.providerCalls.filter((call) => call.route === "off-barcode" && call.body.barcode === "04006381333931").length === 1));
  check("transient OFF result renders trusted product preview", await page.getByText("Barcode test drink", { exact: true }).count() === 1 && await page.getByText(/Open Food Facts-bijdragers/).count() >= 1);
  await page.getByRole("button", { name: "Product toevoegen" }).click();
  await page.waitForSelector('#phase4Slice3EntryForm[data-off-entry="true"]');
  check("per-100-ml transient result preserves millilitre-only flow", await page.locator('#phase4Slice3EntryForm input[name="selection"]').getAttribute("value") === "direct:ml");
  check("transient provider logging is initialized without browser nutrients", await page.evaluate(() => {
    const form = document.querySelector("#phase4Slice3EntryForm");
    return form?.dataset.offEntry === "true" && !form.querySelector('[name="energy"], [name="protein"], [name="carbohydrate"], [name="fat"]');
  }));
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  await page.locator('[data-phase4-s3-add="breakfast"]').click();
  await page.getByRole("button", { name: "Barcode scannen" }).click();
  await page.locator('#phase4Slice3BarcodeForm input[name="barcode"]').fill("5410013128298");
  await page.locator("#phase4Slice3BarcodeForm").evaluate((form) => form.requestSubmit());
  await page.getByText("spa reine blauw", { exact: true }).waitFor();
  check("unusable exact SPA package opens trusted local alternatives", await page.locator('#phase4Slice3SearchForm input[name="query"]').inputValue() === "SPA Reine" && await page.getByText(/exacte verpakking heeft geen complete voedingswaarden/).count() === 1);
  check("SPA alternative remains selectable through frozen OFF catalog flow", await page.locator('[data-phase4-s3-select-food="off_branded_food:30000000-0000-4000-8000-000000000099"]').count() === 1);
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  await page.locator('[data-phase4-s3-add="breakfast"]').click();
  await page.getByRole("button", { name: "Barcode scannen" }).click();
  await page.locator('#phase4Slice3BarcodeForm input[name="barcode"]').fill("96385074");
  await page.locator("#phase4Slice3BarcodeForm").evaluate((form) => form.requestSubmit());
  await page.getByRole("button", { name: "Eigen product met barcode maken" }).waitFor();
  check("unknown OFF product offers private custom fallback", await page.getByText(/Geen bruikbaar product gevonden/).count() === 1);
  await page.getByRole("button", { name: "Eigen product met barcode maken" }).click();
  check("custom fallback prefills normalized barcode", await page.locator('#phase4Slice3CustomForm input[name="barcode"]').inputValue() === "00000096385074");
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  for (const viewport of [{ width: 390, height: 844 }, { width: 320, height: 700 }]) {
    await page.setViewportSize(viewport);
    await page.locator('[data-phase4-s3-add="breakfast"]').click();
    await page.getByRole("button", { name: "Barcode scannen" }).click();
    const scannerLayout = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth, sheetBottom: document.querySelector(".phase4-s3-scan-sheet")?.getBoundingClientRect().bottom || 0, height: innerHeight }));
    check(`scanner ${viewport.width}x${viewport.height} has no horizontal overflow`, scannerLayout.scroll <= scannerLayout.viewport);
    check(`scanner ${viewport.width}x${viewport.height} remains vertically reachable`, scannerLayout.sheetBottom <= scannerLayout.height + 1);
    await page.locator("#phase4Slice3Portal .phase4-s3-close").click();
  }
  await page.setViewportSize({ width: 390, height: 844 });

  await page.locator('[data-phase4-s3-add="breakfast"]').click();
  await page.waitForFunction(() => document.querySelectorAll(".phase4-s3-search-row").length === 2);
  check("add-food search reuses bounded typed RPC", await page.evaluate(() => window.__calls.some((call) => call.name === "fmz_phase4_search_nutrition_catalog" && call.args.p_page_size === 25 && call.args.p_locale === "nl")));
  await page.locator('[data-phase4-s3-select-food="generic_food:10000000-0000-4000-8000-000000000001"]').click();
  await page.waitForSelector("#phase4Slice3EntryForm");
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("50");
  await page.getByRole("button", { name: "Toevoegen", exact: true }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal") && document.querySelectorAll("[data-phase4-s3-item]").length === 1);
  check("new item uses server logging RPC", await page.evaluate(() => window.__calls.some((call) => call.name === "fmz_phase4_log_food_item")));
  check("new item sends local date timezone and offset", await page.evaluate(() => {
    const call = window.__calls.find((entry) => entry.name === "fmz_phase4_log_food_item");
    return Boolean(call.args.p_log_date && call.args.p_timezone_name && Number.isInteger(call.args.p_timezone_offset_minutes));
  }));
  check("authoritative consumed kcal renders", await page.getByText("185 kcal", { exact: true }).count() >= 1);
  check("authoritative protein total renders", await page.getByText("6,5 g", { exact: true }).count() >= 1);
  await page.waitForFunction(() => document.body.textContent.includes("Havermout"));
  check("NL logged item uses reviewed Dutch display label", await page.getByText("Havermout", { exact: true }).count() === 1);
  check("immutable log snapshot keeps canonical name", await page.evaluate(() => window.__mock.activeItems[0].food_name_snapshot === "Oats, raw"));
  check("EN display helper keeps canonical name", await page.evaluate(() => window.FMZ_PHASE4_NUTRITION_SLICE2.displayFoodName(window.__mock.foods[0], "-", "en") === "Oats, raw"));

  await startEdit(page);
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("75");
  await page.locator('#phase4Slice3EntryForm textarea[name="notes"]').fill("Na training");
  const archiveCallsBeforeEdit = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_archive_food_log_item").length);
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const replacementCall = await page.evaluate(() => window.__calls.find((call) => call.name === "fmz_phase4_replace_food_log_item"));
  check("same-meal amount and notes edit uses atomic RPC", replacementCall.args.p_meal_moment === "breakfast" && replacementCall.args.p_consumed_quantity === 75 && replacementCall.args.p_notes === "Na training");
  check("atomic edit sends expected timestamp", Boolean(replacementCall.args.p_expected_original_updated_at));
  check("atomic edit performs no browser archive call", await page.evaluate((before) => window.__calls.filter((call) => call.name === "fmz_phase4_archive_food_log_item").length === before, archiveCallsBeforeEdit));
  check("original is archived in one atomic mock transaction", await page.evaluate(() => window.__mock.archivedItems.length === 1 && window.__mock.activeItems.length === 1));
  check("totals refresh after amount edit", await page.getByText("278 kcal", { exact: true }).count() >= 1);

  await startEdit(page);
  await page.getByRole("button", { name: "Ander voedingsmiddel" }).click();
  await page.waitForFunction(() => document.querySelectorAll(".phase4-s3-search-row").length === 2);
  await page.locator('[data-phase4-s3-select-food="generic_food:10000000-0000-4000-8000-000000000002"]').click();
  await page.locator('#phase4Slice3EntryForm select[name="meal"]').selectOption("dinner");
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("200");
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const changedMealCall = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_food_log_item").at(-1));
  check("changed-meal edit is atomic", changedMealCall.args.p_meal_moment === "dinner");
  check("food edit sends selected canonical food", changedMealCall.args.p_food_id === "10000000-0000-4000-8000-000000000002");
  check("replacement stays the only active intake", await page.evaluate(() => window.__mock.activeItems.length === 1 && window.__mock.activeItems[0].meal_moment === "dinner"));

  await startEdit(page);
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("210");
  await page.evaluate(() => { window.__mock.failReplaceNetworkOnce = true; });
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => document.querySelector("#phase4Slice3Portal .phase4-s3-feedback.error"));
  const failedNetworkCall = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_food_log_item").at(-1));
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const retriedNetworkCall = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_food_log_item").at(-1));
  check("unchanged network retry preserves replacement UUID", failedNetworkCall.args.p_replacement_item_id === retriedNetworkCall.args.p_replacement_item_id);
  check("unchanged network retry preserves request UUID", failedNetworkCall.args.p_replacement_request_id === retriedNetworkCall.args.p_replacement_request_id);

  await startEdit(page);
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("220");
  await page.evaluate(() => { window.__mock.failReplaceNetworkOnce = true; });
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => document.querySelector("#phase4Slice3Portal .phase4-s3-feedback.error"));
  const changedDraftFirst = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_food_log_item").at(-1));
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("230");
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const changedDraftSecond = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_food_log_item").at(-1));
  check("changed draft rotates replacement UUID", changedDraftFirst.args.p_replacement_item_id !== changedDraftSecond.args.p_replacement_item_id);
  check("changed draft rotates request UUID", changedDraftFirst.args.p_replacement_request_id !== changedDraftSecond.args.p_replacement_request_id);

  await startEdit(page);
  await page.evaluate(() => { window.__mock.failReplaceConflictOnce = true; });
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => document.body.textContent.includes("veilige aanvraagidentiteit"));
  const conflictFirst = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_food_log_item").at(-1));
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const conflictSecond = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_food_log_item").at(-1));
  check("23505 conflict is visible and retryable", conflictFirst.args.p_replacement_request_id !== conflictSecond.args.p_replacement_request_id);

  await startEdit(page);
  await page.evaluate(() => { window.__mock.failReplaceStaleOnce = true; });
  const dayReadCountBeforeStale = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_get_nutrition_day").length);
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction((before) => window.__calls.filter((call) => call.name === "fmz_phase4_get_nutrition_day").length > before, dayReadCountBeforeStale);
  check("40001 stale edit refreshes authoritative day", await page.getByText(/intussen gewijzigd/).count() >= 1);
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  await openFirstItem(page);
  await page.getByRole("button", { name: "Verwijderen" }).click();
  await page.getByRole("button", { name: "Verwijderen", exact: true }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  check("archive remove uses reviewed RPC", await page.evaluate(() => window.__calls.some((call) => call.name === "fmz_phase4_archive_food_log_item")));
  check("archive refresh removes item from active totals", await page.locator("[data-phase4-s3-item]").count() === 0 && await page.getByText("0 kcal", { exact: true }).count() >= 1);

  await page.setViewportSize({ width: 390, height: 500 });
  await page.locator('[data-phase4-s3-add="breakfast"]').click();
  const providerSearchForm = page.locator("#phase4Slice3SearchForm");
  const unifiedSearchInput = providerSearchForm.locator('input[name="query"]');
  await unifiedSearchInput.evaluate((input) => { window.__stableUnifiedSearchInput = input; });
  const keyboardViewportGeometry = await searchGeometry(page);
  check("keyboard-style viewport uses a fixed-height mobile search sheet", keyboardViewportGeometry.sheetTop >= 0 && Math.abs(keyboardViewportGeometry.sheetBottom - 500) <= 1);
  check("search results are independently scrollable with anchoring disabled", keyboardViewportGeometry.resultsOverflowY === "auto" && keyboardViewportGeometry.overflowAnchor === "none");
  const providerCallsBeforeTyping = await page.evaluate(() => window.__mock.providerCalls.length);
  await unifiedSearchInput.fill("ch");
  await page.waitForFunction(() => document.querySelectorAll(".phase4-s3-search-row").length === 2);
  check("local results appear immediately for short query", await page.getByText("Havermout", { exact: true }).count() === 1);
  await page.waitForTimeout(500);
  check("query shorter than three characters skips provider", await page.evaluate((before) => window.__mock.providerCalls.length === before, providerCallsBeforeTyping));
  const localCallsBeforeContinuousTyping = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_search_nutrition_catalog").length);
  await page.evaluate(() => {
    window.__mock.localSearchDelays["chicken breast"] = 300;
    window.__mock.providerSearchDelays["chicken breast"] = 650;
  });
  await unifiedSearchInput.fill("");
  await unifiedSearchInput.pressSequentially("chicken breast", { delay: 20 });
  check("continuous typing keeps input node focus and value", await page.evaluate(() => {
    const input = document.querySelector('#phase4Slice3SearchForm input[name="query"]');
    return input === window.__stableUnifiedSearchInput && document.activeElement === input && input.value === "chicken breast";
  }));
  await page.waitForFunction((before) => window.__calls.filter((call) => call.name === "fmz_phase4_search_nutrition_catalog").length > before, localCallsBeforeContinuousTyping);
  const localLoadingGeometry = await searchGeometry(page);
  check("local loading does not move the mobile sheet or search field", searchGeometryStable(keyboardViewportGeometry, localLoadingGeometry));
  check("continuous typing creates one debounced local search", await page.evaluate((before) => window.__calls.filter((call) => call.name === "fmz_phase4_search_nutrition_catalog").length - before === 1, localCallsBeforeContinuousTyping));
  check("local results remain available before provider settles", await page.getByText("Havermout", { exact: true }).count() === 1);
  await page.waitForTimeout(200);
  check("provider search is debounced", await page.evaluate((before) => window.__mock.providerCalls.length === before, providerCallsBeforeTyping));
  await page.waitForFunction(() => window.FMZ_PHASE4_NUTRITION_SLICE3?.state().providerSearchStatus === "loading");
  const providerLoadingGeometry = await searchGeometry(page);
  check("provider loading does not move the mobile sheet or search field", searchGeometryStable(keyboardViewportGeometry, providerLoadingGeometry));
  await page.waitForSelector('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000001"]');
  const providerResultGeometry = await searchGeometry(page);
  check("provider result insertion does not move the mobile sheet or search field", searchGeometryStable(keyboardViewportGeometry, providerResultGeometry));
  check("result insertion keeps focus and page scroll stable", providerResultGeometry.focused && providerResultGeometry.pageScrollY === keyboardViewportGeometry.pageScrollY && providerResultGeometry.resultsScrollHeight > providerResultGeometry.resultsClientHeight);
  await page.evaluate(() => {
    delete window.__mock.localSearchDelays["chicken breast"];
    delete window.__mock.providerSearchDelays["chicken breast"];
  });
  check("input node remains stable after local and provider renders", await page.evaluate(() => document.querySelector('#phase4Slice3SearchForm input[name="query"]') === window.__stableUnifiedSearchInput));
  check("automatic provider search uses bounded contract", await page.evaluate(() => {
    const call = window.__mock.providerCalls.find((entry) => entry.route === "search");
    return call.body.query === "chicken breast" && call.body.page_number === 1 && call.body.page_size === 5 && call.body.locale === "nl";
  }));
  check("manual provider search button is absent", await page.getByRole("button", { name: "Meer voedingsmiddelen zoeken" }).count() === 0);
  check("local and provider groups render together", await page.getByText("Voedingsmiddelen", { exact: true }).count() === 1 && await page.getByText("Meer resultaten", { exact: true }).count() === 1);
  check("provider result is truthful and attributed", await page.getByText("Chicken breast, roasted", { exact: true }).count() === 1 && await page.getByText("Bron: USDA FoodData Central (CC0)", { exact: true }).count() === 1);
  check("candidate token is never visible", !(await page.locator("body").innerText()).includes("signed-candidate-token"));

  await unifiedSearchInput.fill("empty");
  await page.getByText("Geen passende voedingsmiddelen gevonden.", { exact: true }).waitFor();
  const emptyGeometry = await searchGeometry(page);
  await unifiedSearchInput.fill("chicken breast");
  await page.waitForSelector('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000001"]');
  const refillGeometry = await searchGeometry(page);
  check("empty-to-results transition keeps the mobile search field stable", searchGeometryStable(emptyGeometry, refillGeometry) && refillGeometry.focused);

  await page.evaluate(() => { window.__mock.providerSearchDelays["stale chicken"] = 900; });
  await providerSearchForm.locator('input[name="query"]').fill("stale chicken");
  await page.waitForFunction(() => window.__mock.providerCalls.some((entry) => entry.route === "search" && entry.body.query === "stale chicken"));
  await providerSearchForm.locator('input[name="query"]').fill("turkey breast");
  await page.waitForSelector('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000002"]');
  await page.waitForTimeout(600);
  check("stale provider response is ignored", await page.getByText("Turkey breast, roasted", { exact: true }).count() === 1 && await page.getByText("Chicken breast, roasted", { exact: true }).count() === 0);
  await page.evaluate(() => { delete window.__mock.providerSearchDelays["stale chicken"]; });
  await unifiedSearchInput.fill("mixed");
  await page.waitForFunction(() => document.querySelectorAll(".phase4-s3-search-row").length >= 3);
  check("custom OFF and generic results retain separate source groups", await page.getByText("Mijn voedingsmiddelen", { exact: true }).count() === 1 && await page.getByText("Producten", { exact: true }).count() === 1 && await page.getByText("Voedingsmiddelen", { exact: true }).count() === 1);
  check("typed mixed results do not collapse distinct source identities", await page.getByText("Eigen protein pudding", { exact: true }).count() === 1 && await page.getByText("Red Bull Energy Drink", { exact: true }).count() === 1 && await page.getByText("Havermout", { exact: true }).count() === 1);
  for (const typingCase of [
    { query: "red bull", width: 390, height: 844 },
    { query: "kipfilet", width: 320, height: 700 }
  ]) {
    await page.setViewportSize({ width: typingCase.width, height: typingCase.height });
    const typingGeometryBefore = await searchGeometry(page);
    const localBefore = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_search_nutrition_catalog").length);
    const providerBefore = await page.evaluate(() => window.__mock.providerCalls.filter((entry) => entry.route === "search").length);
    await unifiedSearchInput.fill("");
    await unifiedSearchInput.pressSequentially(typingCase.query, { delay: 20 });
    await page.waitForFunction((before) => window.__calls.filter((call) => call.name === "fmz_phase4_search_nutrition_catalog").length > before, localBefore);
    if (typingCase.query === "red bull") {
      await page.waitForFunction(() => document.querySelectorAll('[data-phase4-s3-select-food^="off_branded_food:"]').length === 5);
      await page.waitForTimeout(650);
    } else {
      await page.waitForFunction((query) => window.__mock.providerCalls.some((entry) => entry.route === "search" && entry.body.query === query), typingCase.query);
      await page.waitForFunction(() => window.FMZ_PHASE4_NUTRITION_SLICE3?.state().providerSearchStatus === "ready");
    }
    const typingGeometryAfter = await searchGeometry(page);
    check(`${typingCase.width}px continuous ${typingCase.query} typing stays stable`, await page.evaluate((query) => {
      const input = document.querySelector('#phase4Slice3SearchForm input[name="query"]');
      return input === window.__stableUnifiedSearchInput && document.activeElement === input && input.value === query;
    }, typingCase.query));
    check(`${typingCase.query} avoids local request storm`, await page.evaluate((before) => window.__calls.filter((call) => call.name === "fmz_phase4_search_nutrition_catalog").length - before === 1, localBefore));
    if (typingCase.query === "red bull") {
      check("sufficient OFF results suppress external provider search", await page.evaluate(({ before, query }) => window.__mock.providerCalls.filter((entry) => entry.route === "search").length === before && !window.__mock.providerCalls.some((entry) => entry.route === "search" && entry.body.query === query), { before: providerBefore, query: typingCase.query }));
    } else {
      check(`${typingCase.query} triggers one supplemental provider request`, await page.evaluate(({ before, query }) => window.__mock.providerCalls.filter((entry) => entry.route === "search" && entry.body.query === query).length === 1 && window.__mock.providerCalls.filter((entry) => entry.route === "search").length > before, { before: providerBefore, query: typingCase.query }));
    }
    check(`${typingCase.width}px sheet and input stay vertically stable`, searchGeometryStable(typingGeometryBefore, typingGeometryAfter) && typingGeometryAfter.focused);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await providerSearchForm.locator('input[name="query"]').fill("red bull");
  await page.waitForFunction(() => document.querySelectorAll('[data-phase4-s3-select-food^="off_branded_food:"]').length === 5);
  check("OFF branded products render in their own group", await page.getByText("Producten", { exact: true }).count() === 1 && await page.getByText("Red Bull Energy Drink", { exact: true }).count() === 1);
  check("OFF result exposes brand basis and attribution", await page.getByText("Red Bull", { exact: true }).count() >= 1 && await page.getByText("Voedingswaarden per 100 ml", { exact: true }).count() >= 1 && await page.getByText("Open Food Facts", { exact: true }).count() >= 1);
  const providerCallsBeforeOffInspect = await page.evaluate(() => window.__mock.providerCalls.length);
  await page.locator('[data-phase4-s3-select-food="off_branded_food:30000000-0000-4000-8000-000000000001"]').click();
  await page.getByRole("heading", { name: "Product bekijken" }).waitFor();
  check("OFF detail is explicit before logging", await page.locator("#phase4Slice3EntryForm").count() === 0 && await page.getByRole("button", { name: "Product toevoegen" }).count() === 1);
  check("OFF detail performs no provider or logging mutation", await page.evaluate((before) => window.__mock.providerCalls.length === before, providerCallsBeforeOffInspect));
  await page.getByRole("button", { name: "Product toevoegen" }).click();
  await page.waitForSelector('#phase4Slice3EntryForm[data-off-entry="true"]');
  check("OFF 100 ml product is quantity-safe", await page.locator('#phase4Slice3EntryForm input[name="selection"][value="direct:ml"]').count() === 1 && await page.getByText(/nooit onderling gelijkgesteld/).count() === 1);
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("250");
  await page.evaluate(() => { window.__mock.offLogCommitThenNetworkOnce = true; });
  await page.getByRole("button", { name: "Toevoegen", exact: true }).click();
  await page.waitForFunction(() => document.querySelector("#phase4Slice3Portal .phase4-s3-feedback.error"));
  const offLogFirst = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_log_off_food_item").at(-1).args);
  await page.getByRole("button", { name: "Toevoegen", exact: true }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const offLogReplay = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_log_off_food_item").at(-1).args);
  check("OFF log retry preserves stable identities", offLogFirst.p_item_id === offLogReplay.p_item_id && offLogFirst.p_request_id === offLogReplay.p_request_id);
  check("OFF log sends only product identity and no browser nutrients", offLogReplay.p_off_product_id === "30000000-0000-4000-8000-000000000001" && !Object.keys(offLogReplay).some((key) => /kcal|protein|carbohydrate|fat|fiber|energy/.test(key)));
  check("OFF authoritative ml snapshot updates day total", await page.getByText("113 kcal", { exact: true }).count() >= 1 && await page.getByText("Red Bull Energy Drink", { exact: true }).count() === 1);

  await openFirstItem(page);
  check("OFF historical detail preserves source and attribution", await page.getByText("Open Food Facts", { exact: true }).count() >= 1 && await page.getByText(/historische bron/).count() === 1);
  await page.getByRole("button", { name: "Bewerken" }).click();
  await page.waitForSelector('#phase4Slice3EntryForm[data-off-entry="true"]');
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("200");
  await page.evaluate(() => { window.__mock.offReplaceCommitThenNetworkOnce = true; });
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => document.querySelector("#phase4Slice3Portal .phase4-s3-feedback.error"));
  const offReplaceFirst = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_off_food_log_item").at(-1).args);
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const offReplaceReplay = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_off_food_log_item").at(-1).args);
  check("same OFF product edit is atomic and idempotent", offReplaceFirst.p_replacement_item_id === offReplaceReplay.p_replacement_item_id && offReplaceFirst.p_replacement_request_id === offReplaceReplay.p_replacement_request_id && await page.getByText("90 kcal", { exact: true }).count() >= 1);

  await startEdit(page);
  await page.getByRole("button", { name: "Ander voedingsmiddel" }).click();
  await page.waitForSelector("#phase4Slice3SearchForm");
  await page.locator('#phase4Slice3SearchForm input[name="query"]').fill("red bull");
  await page.waitForFunction(() => document.querySelectorAll('[data-phase4-s3-select-food^="off_branded_food:"]').length === 5);
  await page.locator('[data-phase4-s3-select-food="off_branded_food:30000000-0000-4000-8000-000000000002"]').click();
  await page.getByRole("button", { name: "Product toevoegen" }).click();
  await page.waitForSelector('#phase4Slice3EntryForm[data-off-entry="true"]');
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const changedOffCall = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_replace_off_food_log_item").at(-1).args);
  check("changing OFF product uses atomic replacement", changedOffCall.p_off_product_id === "30000000-0000-4000-8000-000000000002" && await page.getByText("Red Bull Zero 2", { exact: true }).count() === 1);

  await openFirstItem(page);
  await page.getByRole("button", { name: "Verwijderen" }).click();
  await page.getByRole("button", { name: "Verwijderen", exact: true }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  check("OFF archive removes active intake but preserves history", await page.evaluate(() => window.__mock.activeItems.filter((item) => item.source_provider_snapshot === "open_food_facts").length === 0 && window.__mock.archivedItems.filter((item) => item.source_provider_snapshot === "open_food_facts").length >= 3));

  await page.getByRole("button", { name: "Voeding toevoegen" }).first().click();
  await page.waitForSelector("#phase4Slice3SearchForm");
  await providerSearchForm.locator('input[name="query"]').fill("chicken breast");
  await page.waitForSelector('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000001"]');
  await page.locator('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000001"]').click();
  await page.waitForSelector('#phase4Slice3EntryForm[data-provider-entry="true"]');
  check("provider selection requires lookup", await page.evaluate(() => window.__mock.providerCalls.some((entry) => entry.route === "lookup")));
  check("provider entry is grams only", await page.locator('#phase4Slice3EntryForm input[name="selection"][value="direct:g"]').count() === 1 && await page.getByText("Dit voedingsmiddel wordt in gram gelogd.", { exact: true }).count() === 1);
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("100");
  await page.evaluate(() => { window.__mock.providerLogCommitThenNetworkOnce = true; });
  await page.getByRole("button", { name: "Toevoegen", exact: true }).click();
  await page.waitForFunction(() => document.querySelector("#phase4Slice3Portal .phase4-s3-feedback.error"));
  const providerLogFirst = await page.evaluate(() => window.__mock.providerCalls.filter((entry) => entry.route === "log").at(-1).body);
  await page.getByRole("button", { name: "Toevoegen", exact: true }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const providerLogReplay = await page.evaluate(() => window.__mock.providerCalls.filter((entry) => entry.route === "log").at(-1).body);
  check("provider log retry preserves stable identities", providerLogFirst.item_id === providerLogReplay.item_id && providerLogFirst.request_id === providerLogReplay.request_id);
  check("provider log sends no browser nutrients", !Object.keys(providerLogReplay).some((key) => /kcal|protein|carbohydrate|fat|fiber|provider_food_id/.test(key)));
  check("provider item renders from snapshots", await page.getByText("Chicken breast, roasted", { exact: true }).count() === 1 && await page.getByText("USDA FoodData Central", { exact: true }).count() >= 1);
  check("provider authoritative 100 g total renders", await page.getByText("165 kcal", { exact: true }).count() >= 1);

  const providerCallsBeforeHistoricalOpen = await page.evaluate(() => window.__mock.providerCalls.length);
  await startEdit(page);
  check("historical provider edit needs no live lookup", await page.evaluate((before) => window.__mock.providerCalls.length === before, providerCallsBeforeHistoricalOpen));
  check("historical snapshot disclosure renders", await page.getByText(/geen nieuwe zoekopdracht nodig/).count() === 1);
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("150");
  await page.evaluate(() => { window.__mock.providerCommitThenNetworkOnce = true; });
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => document.querySelector("#phase4Slice3Portal .phase4-s3-feedback.error"));
  const historicalReplaceFirst = await page.evaluate(() => window.__mock.providerCalls.filter((entry) => entry.route === "replace").at(-1).body);
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const historicalReplaceReplay = await page.evaluate(() => window.__mock.providerCalls.filter((entry) => entry.route === "replace").at(-1).body);
  check("historical same-food edit sends no old candidate token", !("candidate_token" in historicalReplaceReplay));
  check("exact microsecond updated_at is preserved", historicalReplaceReplay.expected_original_updated_at === "2026-08-20T12:34:56.123456+00:00");
  check("historical replace retry preserves identities", historicalReplaceFirst.replacement_item_id === historicalReplaceReplay.replacement_item_id && historicalReplaceFirst.request_id === historicalReplaceReplay.request_id);
  check("historical replay creates no duplicate active row", await page.evaluate(() => window.__mock.activeItems.filter((item) => item.source_provider_snapshot === "usda_fdc").length === 1));
  check("authoritative 150 g totals render", await page.getByText("248 kcal", { exact: true }).count() >= 1);

  await startEdit(page);
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("160");
  await page.evaluate(() => { window.__mock.providerReplaceStaleOnce = true; });
  const dayReadsBeforeProviderStale = await page.evaluate(() => window.__calls.filter((call) => call.name === "fmz_phase4_get_nutrition_day").length);
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction((before) => window.__calls.filter((call) => call.name === "fmz_phase4_get_nutrition_day").length > before, dayReadsBeforeProviderStale);
  const providerStaleCall = await page.evaluate(() => window.__mock.providerCalls.filter((entry) => entry.route === "replace").at(-1).body);
  check("provider stale edit refreshes authoritative day", await page.getByText(/dag is vernieuwd/).count() === 1);
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("170");
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const providerChangedDraftCall = await page.evaluate(() => window.__mock.providerCalls.filter((entry) => entry.route === "replace").at(-1).body);
  check("changed provider draft rotates identities", providerStaleCall.replacement_item_id !== providerChangedDraftCall.replacement_item_id && providerStaleCall.request_id !== providerChangedDraftCall.request_id);

  await startEdit(page);
  await page.getByRole("button", { name: "Ander voedingsmiddel" }).click();
  const changeProviderSearch = page.locator("#phase4Slice3SearchForm");
  await changeProviderSearch.locator('input[name="query"]').fill("turkey breast");
  await page.waitForSelector('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000002"]');
  await page.locator('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000002"]').click();
  await page.waitForSelector('#phase4Slice3EntryForm[data-provider-entry="true"]');
  await page.locator('#phase4Slice3EntryForm input[name="quantity"]').fill("180");
  await page.getByRole("button", { name: "Wijziging opslaan" }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  const changedProviderFoodCall = await page.evaluate(() => window.__mock.providerCalls.filter((entry) => entry.route === "replace").at(-1).body);
  check("changing provider food uses a fresh signed token", changedProviderFoodCall.candidate_token === "signed-candidate-token-2");
  check("changed provider food renders authoritative snapshot", await page.getByText("Turkey breast, roasted", { exact: true }).count() === 1);

  await startEdit(page);
  await page.getByRole("button", { name: "Ander voedingsmiddel" }).click();
  const invalidCandidateSearch = page.locator("#phase4Slice3SearchForm");
  await invalidCandidateSearch.locator('input[name="query"]').fill("chicken breast");
  await page.waitForSelector('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000001"]');
  await page.evaluate(() => { window.__mock.providerLookupFailure = "candidate"; });
  await page.locator('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000001"]').click();
  await page.waitForFunction(() => document.body.textContent.includes("zoekresultaat is verlopen"));
  check("invalid candidate is localized", await page.getByText(/zoekresultaat is verlopen/).count() === 1);
  await page.evaluate(() => { window.__mock.providerLookupFailure = ""; });
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  await page.locator('[data-phase4-s3-add="lunch"]').click();
  const providerErrorSearch = page.locator("#phase4Slice3SearchForm");
  await providerErrorSearch.locator('input[name="query"]').fill("empty food");
  await page.waitForFunction(() => document.body.textContent.includes("Geen passende voedingsmiddelen gevonden"));
  check("combined empty state is truthful", await page.getByText("Geen passende voedingsmiddelen gevonden.", { exact: true }).count() === 1 && await page.getByText("Geen aanvullende voedingsmiddelen gevonden.", { exact: true }).count() === 0);
  await page.evaluate(() => { window.__mock.providerSearchFailure = "rate"; });
  await providerErrorSearch.locator('input[name="query"]').fill("rate food");
  await page.waitForFunction(() => document.body.textContent.includes("tijdelijk druk"));
  check("provider rate limit is localized", await page.getByText(/tijdelijk druk/).count() === 1 && await page.getByText("Havermout", { exact: true }).count() === 1);
  await page.evaluate(() => { window.__mock.providerSearchFailure = "unavailable"; });
  await providerErrorSearch.locator('input[name="query"]').fill("unavailable food");
  await page.waitForFunction(() => document.body.textContent.includes("tijdelijk niet beschikbaar"));
  check("provider outage preserves local results", await page.getByText(/Lokale en eigen voedingsmiddelen blijven bruikbaar/).count() === 1 && await page.getByText("Havermout", { exact: true }).count() === 1);
  check("provider retry appears only after failure", await page.locator("[data-phase4-s3-provider-retry]").count() === 1);
  await page.evaluate(() => { window.__mock.providerSearchFailure = ""; });
  await page.locator("[data-phase4-s3-provider-retry]").click();
  await page.waitForSelector('[data-phase4-s3-select-provider="81000000-0000-5000-8000-000000000001"]');
  check("provider retry recovers without duplicate normal action", await page.locator("[data-phase4-s3-provider-retry]").count() === 0 && await page.getByRole("button", { name: "Meer voedingsmiddelen zoeken" }).count() === 0);
  for (const viewport of [{ width: 390, height: 844 }, { width: 320, height: 700 }, { width: 820, height: 1180 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    const providerLayout = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth, sheetBottom: document.querySelector(".phase4-s3-sheet")?.getBoundingClientRect().bottom || 0, height: window.innerHeight }));
    check(`provider dialog ${viewport.width}x${viewport.height} stays reachable`, providerLayout.scroll <= providerLayout.viewport && providerLayout.sheetBottom <= providerLayout.height + 1);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  await openFirstItem(page);
  await page.getByRole("button", { name: "Verwijderen" }).click();
  await page.getByRole("button", { name: "Verwijderen", exact: true }).click();
  await page.waitForFunction(() => !document.getElementById("phase4Slice3Portal"));
  check("provider archive uses reviewed existing RPC", await page.evaluate(() => window.__mock.activeItems.filter((item) => item.source_provider_snapshot === "usda_fdc").length === 0));

  await page.locator('[data-phase4-s3-add="snacks"]').click();
  await page.getByRole("button", { name: "Eigen voedingsmiddel maken" }).first().click();
  const custom = page.locator("#phase4Slice3CustomForm");
  await custom.locator('input[name="name"]').fill("Eigen yoghurt");
  await custom.locator('input[name="energy"]').fill("60");
  await custom.locator('input[name="protein"]').fill("10");
  await custom.locator('input[name="carbohydrate"]').fill("4");
  await custom.locator('input[name="fat"]').fill("0");
  await page.getByRole("button", { name: "Maken en gebruiken" }).click();
  await page.waitForSelector("#phase4Slice3EntryForm");
  check("custom-food-from-log continues to amount entry", await page.getByText("Eigen yoghurt", { exact: true }).count() >= 1);
  check("custom food RPC sends no user authority", await page.evaluate(() => {
    const call = window.__calls.filter((entry) => entry.name === "fmz_phase4_upsert_custom_food").at(-1);
    return !Object.keys(call.args).some((key) => /user|owner|role|trainer|entitlement/.test(key));
  }));
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  await page.locator('[data-phase4-s3-date="previous"]').click();
  await waitDay(page);
  check("previous-day navigation requests exact calendar date", await page.evaluate(() => {
    const calls = window.__calls.filter((call) => call.name === "fmz_phase4_get_nutrition_day");
    return calls.at(-1).args.p_log_date === shiftTestDate(testToday(), -1);
  }));
  for (let index = 0; index < 6; index += 1) {
    await page.locator('[data-phase4-s3-date="previous"]').click();
    await page.waitForTimeout(0);
  }
  await page.waitForFunction(() => window.FMZ_PHASE4_NUTRITION_SLICE3.state().dayStatus === "error");
  check("Free seven-day boundary displays server error", await page.getByText(/zes vorige lokale kalenderdagen/).count() === 1);
  await page.getByRole("button", { name: "Terug naar vandaag" }).click();
  await waitDay(page);

  await page.evaluate(() => window.__setLanguage("en"));
  check("English daily Nutrition copy renders", await page.getByRole("heading", { name: "Nutrition", exact: true }).count() === 1 && await page.getByRole("heading", { name: "Breakfast" }).count() === 1);
  await page.locator('[data-phase4-s3-add="breakfast"]').click();
  await page.waitForFunction(() => document.querySelectorAll(".phase4-s3-search-row").length >= 2);
  check("English unified search group copy renders", await page.getByText("Foods", { exact: true }).count() === 1);
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();
  await page.evaluate(() => window.__setLanguage("de"));
  check("German daily Nutrition copy renders", await page.getByRole("heading", { name: "Ernaehrung", exact: true }).count() === 1 && await page.getByRole("heading", { name: "Fruehstueck" }).count() === 1);
  await page.locator('[data-phase4-s3-add="breakfast"]').click();
  await page.waitForFunction(() => document.querySelectorAll(".phase4-s3-search-row").length >= 2);
  check("German unified search group copy renders", await page.getByText("Lebensmittel", { exact: true }).count() >= 1);
  await page.locator("#phase4Slice3Portal .phase4-s3-close").click();

  for (const viewport of [
    { name: "390x844", width: 390, height: 844 },
    { name: "320x700", width: 320, height: 700 },
    { name: "820x1180", width: 820, height: 1180 },
    { name: "1440x900", width: 1440, height: 900 }
  ]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.evaluate(() => window.__setLanguage("nl"));
    const layout = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
      minimum: Math.min(...Array.from(document.querySelectorAll("#phase4NutritionRoot button")).map((button) => button.getBoundingClientRect().height))
    }));
    check(`${viewport.name} has no horizontal overflow`, layout.scroll <= layout.viewport);
    check(`${viewport.name} touch targets remain usable`, layout.minimum >= 44);
  }

  await page.setViewportSize({ width: 390, height: 844 });
  const opener = page.locator('[data-phase4-s3-add="breakfast"]');
  await opener.focus();
  await opener.click();
  await page.keyboard.press("Escape");
  check("Escape closes Slice 3 portal", await page.locator("#phase4Slice3Portal").count() === 0);
  check("portal close restores focus", await opener.evaluate((element) => document.activeElement === element));

  await page.evaluate(() => window.__setRole("trainer"));
  check("trainer Nutrition delegates to frozen legacy renderer", await page.evaluate(() => window.__legacyNutritionCalls > 0));
  check("trainer does not receive Slice 3 client shell", await page.locator("#nutrition.phase4-nutrition-active").count() === 0);

  await browser.close();
  const failed = checks.filter((item) => !item.condition);
  for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
  if (failed.length) {
    console.error(`Phase 4 Nutrition Slice 3 browser check failed: ${failed.length}/${checks.length}`);
    process.exit(1);
  }
  console.log(`Phase 4 Nutrition Slice 3 browser check passed: ${checks.length}`);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
