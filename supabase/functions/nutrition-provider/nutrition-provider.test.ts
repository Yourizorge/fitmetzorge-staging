import assert from "node:assert/strict";
import test from "node:test";
import {
  ACCEPTED_DATA_TYPES,
  MAPPING_VERSION,
  OFF_MAPPING_VERSION,
  OFF_PROVIDER_CODE,
  PHASE3_EXERCISE_UUID_NAMESPACE,
  PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE,
} from "./constants.ts";
import {
  candidateIdentityName,
  createCandidateId,
  createOffCandidateId,
  sha256Hex,
  signCandidateToken,
  signOffCandidateToken,
  uuidV5,
} from "./crypto.ts";
import { createNutritionProviderHandler } from "./handler.ts";
import { normalizeUsdaFood } from "./normalization.ts";
import { normalizeGtin14, normalizeOffProductPayload } from "./off-normalization.ts";
import { ActiveProviderItemUnavailableError, ProviderError } from "./types.ts";
import type {
  FoodCacheKey,
  FoodCacheRow,
  HistoricalProviderIdentity,
  NutritionProviderDependencies,
  OffLogMutation,
  OffReplaceMutation,
  OffSnapshotCandidate,
  OperationalStore,
  ProviderLogMutation,
  ProviderReplaceMutation,
  QueryCacheKey,
  QueryCacheRow,
  RuntimeTransitionInput,
  StructuredLogEvent,
  UpstreamResponse,
} from "./types.ts";

const NOW = new Date("2026-08-19T10:00:00.000Z");
const USER_ID = "11111111-1111-4111-8111-111111111111";
const OTHER_USER_ID = "99999999-9999-4999-8999-999999999999";
const REQUEST_ID = "22222222-2222-4222-8222-222222222222";
const ORIGINAL_ITEM_ID = "33333333-3333-4333-8333-333333333333";
const REPLACEMENT_ITEM_ID = "44444444-4444-4444-8444-444444444444";
const HMAC_KEY = "test-only-key-with-at-least-thirty-two-characters";
const OFF_BARCODE = "8710398520395";
const OFF_GTIN14 = "08710398520395";

function usdaFood(overrides: Record<string, unknown> = {}) {
  return {
    fdcId: 171077,
    description: "Chicken breast, roasted",
    dataType: "Foundation",
    publicationDate: "2024-01-01",
    foodNutrients: [
      { nutrient: { id: 2048 }, amount: 165 },
      { nutrient: { id: 1062 }, amount: 690.36 },
      { nutrient: { id: 1003 }, amount: 31.02 },
      { nutrient: { id: 1004 }, amount: 3.57 },
      { nutrient: { id: 1005 }, amount: 0 },
      { nutrient: { id: 1079 }, amount: 0 },
    ],
    foodPortions: [
      { amount: 1, gramWeight: 120, modifier: "breast" },
      { amount: 1, modifier: "missing gram weight" },
    ],
    ...overrides,
  };
}

function offFood(overrides: Record<string, unknown> = {}) {
  return {
    code: OFF_BARCODE,
    product: {
      code: OFF_BARCODE,
      product_name_nl: "Kipfilet naturel",
      brands: "Testmerk",
      countries_tags: ["en:netherlands"],
      product_quantity_unit: "g",
      rev: 42,
      last_updated_t: 1_777_000_000,
      nutriments: {
        "energy-kcal_100g": 110,
        proteins_100g: 23,
        carbohydrates_100g: 0.5,
        fat_100g: 2,
        fiber_100g: null,
      },
      ...(overrides.product as Record<string, unknown> ?? {}),
    },
    ...Object.fromEntries(Object.entries(overrides).filter(([key]) => key !== "product")),
  };
}

function upstream(
  status: number,
  body: unknown,
  headers: Record<string, string> = {},
): UpstreamResponse {
  return { status, headers: new Headers(headers), bodyText: JSON.stringify(body) };
}

class MemoryStore implements OperationalStore {
  queryCache: QueryCacheRow | null = null;
  foodCache: FoodCacheRow | null = null;
  rateAllowed = true;
  probeAllowed = true;
  rateCalls = 0;
  probeCalls = 0;
  queryWrites = 0;
  foodWrites = 0;
  transitions: RuntimeTransitionInput[] = [];
  rateRequestIds: string[] = [];
  providerLogCalls: ProviderLogMutation[] = [];
  providerReplaceCalls: ProviderReplaceMutation[] = [];
  providerReplacementRows = new Set<string>();
  providerLogRequests = new Map<string, string>();
  providerReplaceRequests = new Map<string, string>();
  localBarcodeResult: Record<string, unknown> | null = null;
  offLogCalls: OffLogMutation[] = [];
  offReplaceCalls: OffReplaceMutation[] = [];
  offLogRequests = new Map<string, string>();
  offReplaceRequests = new Map<string, string>();
  offHistoricalSnapshot: OffSnapshotCandidate | null = null;
  resolverCalls: Array<{ userId: string; originalItemId: string }> = [];
  resolverFailures = new Map<string, Error>();
  resolverOwners = new Map<string, string>();
  archivedResolverItems = new Set<string>();
  historicalIdentity: HistoricalProviderIdentity = {
    provider: "usda_fdc",
    provider_food_id: "171077",
    candidate_id: "a30e5e7f-9711-5823-b668-a25ff4a729fe",
    mapping_version: MAPPING_VERSION,
    provider_data_type: "Foundation",
  };

  async getQueryCache(_key: QueryCacheKey) {
    return this.queryCache;
  }
  async putQueryCache(row: QueryCacheRow) {
    this.queryCache = row;
    this.queryWrites += 1;
  }
  async getFoodCache(_key: FoodCacheKey) {
    return this.foodCache;
  }
  async putFoodCache(row: FoodCacheRow) {
    this.foodCache = row;
    this.foodWrites += 1;
  }
  async consumeRateLimit(_providerCode: "usda_fdc" | "open_food_facts", _subject: string, requestId: string) {
    this.rateCalls += 1;
    const replayed = this.rateRequestIds.includes(requestId);
    this.rateRequestIds.push(requestId);
    return this.rateAllowed
      ? { allowed: true, replayed }
      : { allowed: false, replayed: false, retry_after_seconds: 37 };
  }
  async beginProbe(_providerCode: "usda_fdc" | "open_food_facts") {
    this.probeCalls += 1;
    return { probe_allowed: this.probeAllowed };
  }
  async transitionRuntime(
    _providerCode: "usda_fdc" | "open_food_facts",
    input: RuntimeTransitionInput,
  ) {
    this.transitions.push(input);
  }
  async resolveProviderFoodLogItem(userId: string, originalItemId: string) {
    this.resolverCalls.push({ userId, originalItemId });
    const failure = this.resolverFailures.get(originalItemId);
    if (failure) throw failure;
    const owner = this.resolverOwners.get(originalItemId);
    if ((owner && owner !== userId) || this.archivedResolverItems.has(originalItemId)) {
      throw new ActiveProviderItemUnavailableError();
    }
    return this.historicalIdentity;
  }
  async logProviderFoodItem(input: ProviderLogMutation) {
    const payload = JSON.stringify(input);
    const existing = this.providerLogRequests.get(input.input.requestId);
    if (existing && existing !== payload) {
      throw new ProviderError(
        "provider_log_request_conflict",
        "Request identity was already used with different input.",
        409,
      );
    }
    this.providerLogRequests.set(input.input.requestId, payload);
    this.providerLogCalls.push(input);
    return {
      item: {
        id: input.input.itemId,
        food_id: null,
        consumed_quantity: input.input.consumedQuantity,
        consumed_unit: "g",
        energy_kcal_snapshot:
          Math.round(input.candidate.energy_kcal_per_100g * input.input.consumedQuantity * 10) /
          1_000,
      },
      day: { log_date: input.input.logDate },
      idempotent_replay: this.providerLogCalls.length > 1,
    };
  }
  async replaceProviderFoodLogItem(input: ProviderReplaceMutation) {
    const payload = JSON.stringify(input);
    const existing = this.providerReplaceRequests.get(input.input.requestId);
    if (existing) {
      if (existing !== payload) {
        throw new ProviderError(
          "provider_replace_request_conflict",
          "Request identity was already used with different input.",
          409,
        );
      }
      this.providerReplaceCalls.push(input);
      return {
        replacement_item: {
          id: input.input.replacementItemId,
          food_id: null,
          status: "active",
        },
        archived_original: { id: input.input.originalItemId, status: "archived" },
        day: { log_date: "2026-08-19" },
        idempotent_replay: true,
      };
    }
    if (this.archivedResolverItems.has(input.input.originalItemId)) {
      throw new ProviderError(
        "provider_replace_stale",
        "Food log item changed; refresh and try again.",
        409,
      );
    }
    this.providerReplaceRequests.set(input.input.requestId, payload);
    this.providerReplaceCalls.push(input);
    this.providerReplacementRows.add(input.input.replacementItemId);
    this.archivedResolverItems.add(input.input.originalItemId);
    this.resolverOwners.set(input.input.replacementItemId, input.userId);
    return {
      replacement_item: {
        id: input.input.replacementItemId,
        food_id: null,
        status: "active",
      },
      archived_original: { id: input.input.originalItemId, status: "archived" },
      day: { log_date: "2026-08-19" },
      idempotent_replay: false,
    };
  }
  async resolveLocalBarcode(_userId: string, _normalizedGtin14: string) {
    return this.localBarcodeResult;
  }
  async resolveTransientOffFoodLogItem(userId: string, originalItemId: string) {
    this.resolverCalls.push({ userId, originalItemId });
    const failure = this.resolverFailures.get(originalItemId);
    if (failure) throw failure;
    const owner = this.resolverOwners.get(originalItemId);
    if (
      !this.offHistoricalSnapshot || (owner && owner !== userId) ||
      this.archivedResolverItems.has(originalItemId)
    ) throw new ActiveProviderItemUnavailableError();
    return this.offHistoricalSnapshot;
  }
  async logTransientOffFoodItem(input: OffLogMutation) {
    const payload = JSON.stringify(input);
    const existing = this.offLogRequests.get(input.input.requestId);
    if (existing && existing !== payload) {
      throw new ProviderError("provider_log_request_conflict", "Request conflict.", 409);
    }
    this.offLogRequests.set(input.input.requestId, payload);
    this.offLogCalls.push(input);
    return {
      item: {
        id: input.input.itemId,
        food_id: null,
        source_provider_snapshot: OFF_PROVIDER_CODE,
        consumed_quantity: input.input.consumedQuantity,
        consumed_unit: input.input.consumedUnit,
      },
      day: { log_date: input.input.logDate },
      idempotent_replay: this.offLogCalls.length > 1,
    };
  }
  async replaceTransientOffFoodItem(input: OffReplaceMutation) {
    const payload = JSON.stringify(input);
    const existing = this.offReplaceRequests.get(input.input.requestId);
    if (existing && existing !== payload) {
      throw new ProviderError("provider_replace_request_conflict", "Request conflict.", 409);
    }
    this.offReplaceRequests.set(input.input.requestId, payload);
    this.offReplaceCalls.push(input);
    this.archivedResolverItems.add(input.input.originalItemId);
    this.resolverOwners.set(input.input.replacementItemId, input.userId);
    return {
      replacement_item: {
        id: input.input.replacementItemId,
        food_id: null,
        source_provider_snapshot: OFF_PROVIDER_CODE,
        status: "active",
      },
      archived_original: { id: input.input.originalItemId, status: "archived" },
      day: { log_date: "2026-08-19" },
      idempotent_replay: Boolean(existing),
    };
  }
}

function dependencies(store = new MemoryStore(), searchResponse?: UpstreamResponse): {
  deps: NutritionProviderDependencies;
  logs: StructuredLogEvent[];
  calls: { search: number; lookup: number; offLookup: number };
} {
  const logs: StructuredLogEvent[] = [];
  const calls = { search: 0, lookup: 0, offLookup: 0 };
  return {
    deps: {
      auth: {
        verifyBearer: async (token) =>
          token === "valid-token-value-that-is-long" ? { id: USER_ID } : null,
      },
      store,
      usda: {
        search: async () => {
          calls.search += 1;
          return searchResponse ?? upstream(200, { foods: [usdaFood()] });
        },
        lookup: async () => {
          calls.lookup += 1;
          return upstream(200, usdaFood());
        },
      },
      off: {
        async lookupBarcode() {
          calls.offLookup += 1;
          return upstream(200, offFood());
        },
      },
      logger: { write: (event) => logs.push(event) },
      hmacKey: HMAC_KEY,
      clock: { now: () => new Date(NOW) },
      timeoutMs: 1_000,
    },
    logs,
    calls,
  };
}

function request(
  route: "search" | "lookup" | "log" | "replace" | "off-barcode" | "off-log" | "off-replace",
  body: unknown,
  options: { token?: string; origin?: string } = {},
) {
  return new Request(`https://project.functions.supabase.co/nutrition-provider/${route}`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${options.token ?? "valid-token-value-that-is-long"}`,
      "content-type": "application/json",
      origin: options.origin ?? "https://yourizorge.github.io",
    },
    body: JSON.stringify(body),
  });
}

async function providerToken() {
  return await signCandidateToken(HMAC_KEY, "171077", "Foundation", NOW);
}

async function validFoodCache(): Promise<FoodCacheRow> {
  const candidate = await normalizeUsdaFood(usdaFood(), NOW);
  return {
    provider_code: "usda_fdc",
    provider_food_id: "171077",
    provider_data_type: "Foundation",
    mapping_version: MAPPING_VERSION,
    candidate_id: candidate.candidate_id,
    normalized_payload: candidate,
    payload_checksum: await sha256Hex(candidate),
    quality_state: "candidate",
    rejection_code: null,
    source_version: null,
    source_updated_at: null,
    provenance: candidate.provenance,
    metadata: {},
    fetched_at: NOW.toISOString(),
    expires_at: new Date(NOW.getTime() + 60_000).toISOString(),
  };
}

async function validOffFoodCache(overrides: Record<string, unknown> = {}): Promise<FoodCacheRow> {
  const candidate = await normalizeOffProductPayload(offFood(overrides), OFF_GTIN14, NOW);
  return {
    provider_code: OFF_PROVIDER_CODE,
    provider_food_id: OFF_GTIN14,
    provider_data_type: "off_branded",
    mapping_version: OFF_MAPPING_VERSION,
    candidate_id: candidate.candidate_id,
    normalized_payload: candidate,
    payload_checksum: await sha256Hex(candidate),
    quality_state: "validated",
    rejection_code: null,
    source_version: candidate.provenance.source_revision,
    source_updated_at: candidate.provenance.source_updated_at,
    provenance: candidate.provenance,
    metadata: { cache_kind: "transient_off_exact_barcode" },
    fetched_at: NOW.toISOString(),
    expires_at: new Date(NOW.getTime() + 60_000).toISOString(),
  };
}

async function offCandidateToken(overrides: Record<string, unknown> = {}) {
  const candidate = await normalizeOffProductPayload(offFood(overrides), OFF_GTIN14, NOW);
  return await signOffCandidateToken(
    HMAC_KEY,
    candidate,
    candidate.provenance.source_checksum,
    NOW,
  );
}

function offLogBody(candidateToken: string, overrides: Record<string, unknown> = {}) {
  return {
    candidate_token: candidateToken,
    item_id: ORIGINAL_ITEM_ID,
    request_id: REQUEST_ID,
    log_date: "2026-08-19",
    timezone_name: "Europe/Amsterdam",
    timezone_offset_minutes: 120,
    meal_moment: "lunch",
    consumed_quantity: 125,
    consumed_unit: "g",
    notes: "Scanned product",
    consumed_at: "2026-08-19T10:00:00.000Z",
    ...overrides,
  };
}

function offReplaceBody(overrides: Record<string, unknown> = {}) {
  return {
    original_item_id: ORIGINAL_ITEM_ID,
    replacement_item_id: REPLACEMENT_ITEM_ID,
    request_id: REQUEST_ID,
    expected_original_updated_at: "2026-08-20T10:12:34.123456Z",
    meal_moment: "dinner",
    consumed_quantity: 175,
    consumed_unit: "g",
    notes: "Updated scanned product",
    ...overrides,
  };
}

function providerLogBody(candidateToken: string, overrides: Record<string, unknown> = {}) {
  return {
    candidate_token: candidateToken,
    item_id: "33333333-3333-4333-8333-333333333333",
    request_id: REQUEST_ID,
    log_date: "2026-08-19",
    timezone_name: "Europe/Amsterdam",
    timezone_offset_minutes: 120,
    meal_moment: "lunch",
    consumed_quantity: 150,
    consumed_unit: "g",
    notes: "After training",
    consumed_at: "2026-08-19T10:00:00.000Z",
    ...overrides,
  };
}

function historicalReplaceBody(overrides: Record<string, unknown> = {}) {
  return {
    original_item_id: ORIGINAL_ITEM_ID,
    replacement_item_id: REPLACEMENT_ITEM_ID,
    request_id: REQUEST_ID,
    expected_original_updated_at: "2026-08-20T10:12:34.123456Z",
    meal_moment: "dinner",
    consumed_quantity: 150,
    consumed_unit: "g",
    notes: "Updated historical provider item",
    ...overrides,
  };
}

function searchBody(overrides: Record<string, unknown> = {}) {
  return {
    query: "chicken breast",
    locale: "nl",
    country_code: "NL",
    page_number: 1,
    page_size: 10,
    request_id: REQUEST_ID,
    ...overrides,
  };
}

test("dedicated namespace is fixed, separate and deterministic", async () => {
  assert.equal(PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE, "23440733-7e58-4c21-ad15-591eae6ab8ac");
  assert.notEqual(PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE, PHASE3_EXERCISE_UUID_NAMESPACE);
  assert.equal(candidateIdentityName("171077"), "usda_fdc:171077");
  const first = await createCandidateId("171077");
  const second = await createCandidateId("171077");
  assert.equal(first, second);
  assert.equal(first, "a30e5e7f-9711-5823-b668-a25ff4a729fe");
  assert.notEqual(first, await createCandidateId("171078"));
  assert.notEqual(
    first,
    await uuidV5(PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE, "open_food_facts:171077"),
  );
  assert.notEqual(first, await uuidV5(PHASE3_EXERCISE_UUID_NAMESPACE, "usda_fdc:171077"));
});

test("normalization uses reviewed 100 g nutrient contract and explicit gram portions", async () => {
  const candidate = await normalizeUsdaFood(usdaFood(), NOW);
  assert.equal(candidate.kcal, 165);
  assert.equal(candidate.protein, 31.02);
  assert.equal(candidate.carbohydrates, 0);
  assert.equal(candidate.fat, 3.57);
  assert.equal(candidate.reference_amount, 100);
  assert.equal(candidate.reference_unit, "g");
  assert.equal(candidate.derivation.energy, "2048_kcal");
  assert.deepEqual(candidate.portions, [{
    label: "breast",
    amount: 1,
    unit: "serving",
    equivalent_amount: 120,
    equivalent_unit: "g",
  }]);
});

test("normalization rejects branded, missing macros and conflicting energy", async () => {
  await assert.rejects(() => normalizeUsdaFood(usdaFood({ dataType: "Branded" }), NOW));
  await assert.rejects(() => normalizeUsdaFood(usdaFood({ dataType: "Experimental" }), NOW));
  await assert.rejects(() => normalizeUsdaFood(usdaFood({ foodNutrients: [] }), NOW));
  await assert.rejects(() =>
    normalizeUsdaFood(
      usdaFood({
        foodNutrients: [
          { nutrient: { id: 2048 }, amount: 100 },
          { nutrient: { id: 1062 }, amount: 2_000 },
          { nutrient: { id: 1003 }, amount: 10 },
          { nutrient: { id: 1004 }, amount: 10 },
          { nutrient: { id: 1005 }, amount: 10 },
        ],
      }),
      NOW,
    )
  );
});

test("all reviewed USDA energy paths and nutrient bounds normalize explicitly", async () => {
  const macros = [
    { nutrient: { id: 1003 }, amount: 12 },
    { nutrient: { id: 1004 }, amount: 4 },
    { nutrient: { id: 1005 }, amount: 20 },
    { nutrient: { id: 1079 }, amount: 3 },
  ];
  const general = await normalizeUsdaFood(
    usdaFood({
      foodNutrients: [{ nutrient: { id: 2047 }, amount: 150 }, ...macros],
    }),
    NOW,
  );
  assert.equal(general.derivation.energy, "2047_kcal");

  const legacy = await normalizeUsdaFood(
    usdaFood({
      dataType: "Survey (FNDDS)",
      foodNutrients: [{ nutrient: { id: 1008 }, amount: 145 }, ...macros],
    }),
    NOW,
  );
  assert.equal(legacy.derivation.energy, "1008_kcal");

  const converted = await normalizeUsdaFood(
    usdaFood({
      dataType: "SR Legacy",
      foodNutrients: [{ nutrient: { id: 1062 }, amount: 418.4 }, ...macros],
    }),
    NOW,
  );
  assert.equal(converted.derivation.energy, "1062_kj_converted");
  assert.equal(converted.kcal, 100);
  assert.equal(converted.fiber, 3);

  await assert.rejects(() =>
    normalizeUsdaFood(
      usdaFood({
        foodNutrients: [
          { nutrient: { id: 2048 }, amount: 100 },
          { nutrient: { id: 1003 }, amount: -1 },
          { nutrient: { id: 1004 }, amount: 1 },
          { nutrient: { id: 1005 }, amount: 1 },
        ],
      }),
      NOW,
    )
  );

  const searchShape = await normalizeUsdaFood(
    usdaFood({
      foodNutrients: [
        { nutrientId: 1008, unitName: "KCAL", value: 120 },
        { nutrientId: 1003, unitName: "G", value: 10 },
        { nutrientId: 1004, unitName: "G", value: 2 },
        { nutrientId: 1005, unitName: "G", value: 15 },
        { nutrientId: 1079, unitName: "G", value: 1 },
      ],
    }),
    NOW,
  );
  assert.equal(searchShape.kcal, 120);
  assert.equal(searchShape.protein, 10);

  await assert.rejects(() =>
    normalizeUsdaFood(
      usdaFood({
        foodNutrients: [
          { nutrientId: 1008, unitName: "KCAL", value: 120 },
          { nutrientId: 1003, unitName: "MG", value: 10 },
          { nutrientId: 1004, unitName: "G", value: 2 },
          { nutrientId: 1005, unitName: "G", value: 15 },
        ],
      }),
      NOW,
    )
  );
});

test("unauthenticated and unapproved origins are rejected", async () => {
  const missing = dependencies();
  const missingRequest = new Request(
    "https://project.functions.supabase.co/nutrition-provider/search",
    {
      method: "POST",
      headers: { "content-type": "application/json", origin: "https://yourizorge.github.io" },
      body: JSON.stringify(searchBody()),
    },
  );
  assert.equal((await createNutritionProviderHandler(missing.deps)(missingRequest)).status, 401);
  const first = dependencies();
  const unauthorized = await createNutritionProviderHandler(first.deps)(
    request("search", searchBody(), { token: "invalid-token-value-that-is-long" }),
  );
  assert.equal(unauthorized.status, 401);
  const second = dependencies();
  const disallowed = await createNutritionProviderHandler(second.deps)(
    request("search", searchBody(), { origin: "https://appfmz.nl" }),
  );
  assert.equal(disallowed.status, 403);
  assert.equal(disallowed.headers.get("access-control-allow-origin"), null);
});

test("approved CORS preflight is bounded and supports current Supabase client headers", async () => {
  const current = dependencies();
  const response = await createNutritionProviderHandler(current.deps)(
    new Request(
      "https://project.functions.supabase.co/nutrition-provider/search",
      {
        method: "OPTIONS",
        headers: {
          origin: "https://yourizorge.github.io",
          "access-control-request-method": "POST",
          "access-control-request-headers":
            "authorization,apikey,content-type,x-client-info,x-retry-count",
        },
      },
    ),
  );
  assert.equal(response.status, 204);
  assert.equal(response.headers.get("access-control-allow-origin"), "https://yourizorge.github.io");
  assert.equal(response.headers.get("vary"), "Origin");
  const allowed = response.headers.get("access-control-allow-headers") ?? "";
  for (
    const header of ["authorization", "apikey", "content-type", "x-client-info", "x-retry-count"]
  ) {
    assert.equal(allowed.includes(header), true);
  }
  assert.equal(current.calls.search, 0);
  assert.equal(current.calls.lookup, 0);
});

test("search validates exact bounded input", async () => {
  const { deps } = dependencies();
  const handler = createNutritionProviderHandler(deps);
  assert.equal((await handler(request("search", searchBody({ query: "x" })))).status, 400);
  assert.equal(
    (await handler(request("search", searchBody({ query: "x".repeat(81) })))).status,
    400,
  );
  assert.equal((await handler(request("search", searchBody({ locale: "fr" })))).status, 400);
  assert.equal((await handler(request("search", searchBody({ page_number: 4 })))).status, 400);
  assert.equal((await handler(request("search", searchBody({ role: "trainer" })))).status, 400);
  assert.equal(
    (await handler(request("search", searchBody({ url: "https://evil.example" })))).status,
    400,
  );
  assert.equal((await handler(request("search", searchBody({ request_id: "bad" })))).status, 400);
});

test("search miss consumes server rate gate, probes circuit, normalizes and caches", async () => {
  const store = new MemoryStore();
  const { deps, calls, logs } = dependencies(store);
  const response = await createNutritionProviderHandler(deps)(request("search", searchBody()));
  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.data.cache, "miss");
  assert.equal(payload.data.results.length, 1);
  assert.equal(typeof payload.data.results[0].candidate_token, "string");
  assert.equal(store.rateCalls, 1);
  assert.equal(store.probeCalls, 1);
  assert.equal(calls.search, 1);
  assert.equal(store.queryWrites, 1);
  assert.equal(store.transitions.at(-1)?.event, "success");
  assert.equal(JSON.stringify(payload).includes(HMAC_KEY), false);
  assert.equal(JSON.stringify(logs).includes("chicken"), false);
  assert.equal(JSON.stringify(logs).includes(USER_ID), false);
});

test("fresh valid query cache bypasses provider, rate and circuit", async () => {
  const store = new MemoryStore();
  const candidate = await normalizeUsdaFood(usdaFood(), NOW);
  store.queryCache = {
    provider_code: "usda_fdc",
    query_hmac: "a".repeat(64),
    locale: "nl",
    country_code: "NL",
    page_number: 1,
    page_size: 10,
    data_type_filter: [...ACCEPTED_DATA_TYPES],
    filter_key: "b".repeat(64),
    filter_identity: {},
    mapping_version: MAPPING_VERSION,
    result_payload: [candidate],
    payload_checksum: await sha256Hex([candidate]),
    result_count: 1,
    cache_status: "positive",
    source_version: null,
    fetched_at: NOW.toISOString(),
    expires_at: new Date(NOW.getTime() + 60_000).toISOString(),
  };
  const { deps, calls } = dependencies(store);
  const response = await createNutritionProviderHandler(deps)(request("search", searchBody()));
  assert.equal(response.status, 200);
  assert.equal((await response.json()).data.cache, "hit");
  assert.equal(store.rateCalls, 0);
  assert.equal(store.probeCalls, 0);
  assert.equal(calls.search, 0);
});

test("empty cache is honored and expired cache is refreshed", async () => {
  const emptyStore = new MemoryStore();
  emptyStore.queryCache = {
    provider_code: "usda_fdc",
    query_hmac: "a".repeat(64),
    locale: "nl",
    country_code: "NL",
    page_number: 1,
    page_size: 10,
    data_type_filter: [...ACCEPTED_DATA_TYPES],
    filter_key: "b".repeat(64),
    filter_identity: {},
    mapping_version: MAPPING_VERSION,
    result_payload: [],
    payload_checksum: await sha256Hex([]),
    result_count: 0,
    cache_status: "empty",
    source_version: null,
    fetched_at: NOW.toISOString(),
    expires_at: new Date(NOW.getTime() + 60_000).toISOString(),
  };
  const empty = dependencies(emptyStore);
  const emptyResponse = await createNutritionProviderHandler(empty.deps)(
    request("search", searchBody()),
  );
  assert.equal(emptyResponse.status, 200);
  assert.deepEqual((await emptyResponse.json()).data.results, []);
  assert.equal(empty.calls.search, 0);

  const expiredStore = new MemoryStore();
  expiredStore.queryCache = {
    ...emptyStore.queryCache,
    expires_at: new Date(NOW.getTime() - 1).toISOString(),
  };
  const expired = dependencies(expiredStore);
  assert.equal(
    (await createNutritionProviderHandler(expired.deps)(request("search", searchBody()))).status,
    200,
  );
  assert.equal(expired.calls.search, 1);
});

test("corrupt cache checksum is ignored and safely refreshed", async () => {
  const store = new MemoryStore();
  const candidate = await normalizeUsdaFood(usdaFood(), NOW);
  store.queryCache = {
    provider_code: "usda_fdc",
    query_hmac: "a".repeat(64),
    locale: "nl",
    country_code: "NL",
    page_number: 1,
    page_size: 10,
    data_type_filter: [...ACCEPTED_DATA_TYPES],
    filter_key: "b".repeat(64),
    filter_identity: {},
    mapping_version: MAPPING_VERSION,
    result_payload: [candidate],
    payload_checksum: "0".repeat(64),
    result_count: 1,
    cache_status: "positive",
    source_version: null,
    fetched_at: NOW.toISOString(),
    expires_at: new Date(NOW.getTime() + 60_000).toISOString(),
  };
  const { deps, calls } = dependencies(store);
  const response = await createNutritionProviderHandler(deps)(request("search", searchBody()));
  assert.equal(response.status, 200);
  assert.equal(calls.search, 1);
  assert.equal(store.queryWrites, 1);
});

test("checksum-valid query cache with an unsafe payload shape is rejected", async () => {
  const store = new MemoryStore();
  const candidate = await normalizeUsdaFood(usdaFood(), NOW);
  const unsafeCandidate = { ...candidate, internal_secret: "must-not-leak" };
  store.queryCache = {
    provider_code: "usda_fdc",
    query_hmac: "a".repeat(64),
    locale: "nl",
    country_code: "NL",
    page_number: 1,
    page_size: 10,
    data_type_filter: [...ACCEPTED_DATA_TYPES],
    filter_key: "b".repeat(64),
    filter_identity: {},
    mapping_version: MAPPING_VERSION,
    result_payload: [unsafeCandidate] as unknown as QueryCacheRow["result_payload"],
    payload_checksum: await sha256Hex([unsafeCandidate]),
    result_count: 1,
    cache_status: "positive",
    source_version: null,
    fetched_at: NOW.toISOString(),
    expires_at: new Date(NOW.getTime() + 60_000).toISOString(),
  };
  const current = dependencies(store);
  const response = await createNutritionProviderHandler(current.deps)(
    request("search", searchBody()),
  );
  assert.equal(response.status, 200);
  assert.equal(current.calls.search, 1);
  assert.equal(JSON.stringify(await response.json()).includes("must-not-leak"), false);
});

test("rate idempotency is bound to both client request id and operation identity", async () => {
  const firstStore = new MemoryStore();
  const first = dependencies(firstStore);
  await createNutritionProviderHandler(first.deps)(request("search", searchBody()));

  const retryStore = new MemoryStore();
  const retry = dependencies(retryStore);
  await createNutritionProviderHandler(retry.deps)(request("search", searchBody()));

  const differentStore = new MemoryStore();
  const different = dependencies(differentStore);
  await createNutritionProviderHandler(different.deps)(
    request("search", searchBody({ query: "turkey breast" })),
  );

  assert.equal(firstStore.rateRequestIds[0], retryStore.rateRequestIds[0]);
  assert.notEqual(firstStore.rateRequestIds[0], REQUEST_ID);
  assert.notEqual(firstStore.rateRequestIds[0], differentStore.rateRequestIds[0]);
});

test("concurrent identical retries present one stable operation id to atomic rate RPC", async () => {
  const store = new MemoryStore();
  const current = dependencies(store);
  const handler = createNutritionProviderHandler(current.deps);
  const responses = await Promise.all([
    handler(request("search", searchBody())),
    handler(request("search", searchBody())),
  ]);
  assert.equal(store.rateRequestIds.length, 2);
  assert.equal(store.rateRequestIds[0], store.rateRequestIds[1]);
  assert.deepEqual(responses.map((response) => response.status).sort(), [200, 409]);
  assert.equal(current.calls.search, 1);
});

test("lookup requires untampered non-expired signed candidate token", async () => {
  const validToken = await signCandidateToken(HMAC_KEY, "171077", "Foundation", NOW);
  const { deps, calls } = dependencies();
  const handler = createNutritionProviderHandler(deps);
  const response = await handler(
    request("lookup", { candidate_token: validToken, request_id: REQUEST_ID }),
  );
  assert.equal(response.status, 200);
  assert.equal(calls.lookup, 1);
  const tampered = `${validToken.slice(0, -1)}${validToken.endsWith("a") ? "b" : "a"}`;
  assert.equal(
    (await handler(request("lookup", { candidate_token: tampered, request_id: REQUEST_ID })))
      .status,
    409,
  );

  const expiredClock = new Date(NOW.getTime() + 16 * 60_000);
  const expiredDeps = dependencies().deps;
  expiredDeps.clock = { now: () => expiredClock };
  assert.equal(
    (await createNutritionProviderHandler(expiredDeps)(request("lookup", {
      candidate_token: validToken,
      request_id: REQUEST_ID,
    }))).status,
    409,
  );
});

test("fresh food detail cache bypasses provider and checksum mismatch refreshes", async () => {
  const candidate = await normalizeUsdaFood(usdaFood(), NOW);
  const token = await signCandidateToken(HMAC_KEY, "171077", "Foundation", NOW);
  const baseCache: FoodCacheRow = {
    provider_code: "usda_fdc",
    provider_food_id: "171077",
    provider_data_type: "Foundation",
    mapping_version: MAPPING_VERSION,
    candidate_id: candidate.candidate_id,
    normalized_payload: candidate,
    payload_checksum: await sha256Hex(candidate),
    quality_state: "candidate",
    rejection_code: null,
    source_version: null,
    source_updated_at: null,
    provenance: candidate.provenance,
    metadata: {},
    fetched_at: NOW.toISOString(),
    expires_at: new Date(NOW.getTime() + 60_000).toISOString(),
  };

  const hitStore = new MemoryStore();
  hitStore.foodCache = baseCache;
  const hit = dependencies(hitStore);
  const hitResponse = await createNutritionProviderHandler(hit.deps)(request("lookup", {
    candidate_token: token,
    request_id: REQUEST_ID,
  }));
  assert.equal(hitResponse.status, 200);
  assert.equal((await hitResponse.json()).data.cache, "hit");
  assert.equal(hit.calls.lookup, 0);
  assert.equal(hitStore.rateCalls, 0);

  const badStore = new MemoryStore();
  badStore.foodCache = { ...baseCache, payload_checksum: "0".repeat(64) };
  const bad = dependencies(badStore);
  assert.equal(
    (await createNutritionProviderHandler(bad.deps)(request("lookup", {
      candidate_token: token,
      request_id: REQUEST_ID,
    }))).status,
    200,
  );
  assert.equal(bad.calls.lookup, 1);
  assert.equal(badStore.foodWrites, 1);
});

test("checksum-valid food cache with an unsafe payload shape is rejected", async () => {
  const candidate = await normalizeUsdaFood(usdaFood(), NOW);
  const token = await signCandidateToken(HMAC_KEY, "171077", "Foundation", NOW);
  const unsafeCandidate = { ...candidate, internal_secret: "must-not-leak" };
  const store = new MemoryStore();
  store.foodCache = {
    provider_code: "usda_fdc",
    provider_food_id: "171077",
    provider_data_type: "Foundation",
    mapping_version: MAPPING_VERSION,
    candidate_id: candidate.candidate_id,
    normalized_payload: unsafeCandidate,
    payload_checksum: await sha256Hex(unsafeCandidate),
    quality_state: "candidate",
    rejection_code: null,
    source_version: null,
    source_updated_at: null,
    provenance: candidate.provenance,
    metadata: {},
    fetched_at: NOW.toISOString(),
    expires_at: new Date(NOW.getTime() + 60_000).toISOString(),
  };
  const current = dependencies(store);
  const response = await createNutritionProviderHandler(current.deps)(request("lookup", {
    candidate_token: token,
    request_id: REQUEST_ID,
  }));
  assert.equal(response.status, 200);
  assert.equal(current.calls.lookup, 1);
  assert.equal(JSON.stringify(await response.json()).includes("must-not-leak"), false);
});

test("invalid detail is quarantined and a fresh quarantine blocks repeated upstream use", async () => {
  const token = await signCandidateToken(HMAC_KEY, "171077", "Foundation", NOW);
  const store = new MemoryStore();
  const current = dependencies(store);
  current.deps.usda.lookup = async () => {
    current.calls.lookup += 1;
    return upstream(200, usdaFood({ foodNutrients: [] }));
  };
  const handler = createNutritionProviderHandler(current.deps);
  const body = { candidate_token: token, request_id: REQUEST_ID };
  assert.equal((await handler(request("lookup", body))).status, 502);
  assert.equal(store.foodCache?.quality_state, "quarantined");
  assert.equal(store.foodCache?.rejection_code, "candidate-missing-nutrients");
  assert.equal((await handler(request("lookup", body))).status, 502);
  assert.equal(current.calls.lookup, 1);

  if (!store.foodCache) throw new Error("Expected quarantine cache row.");
  store.foodCache.payload_checksum = "0".repeat(64);
  current.deps.usda.lookup = async () => {
    current.calls.lookup += 1;
    return upstream(200, usdaFood());
  };
  assert.equal(
    (await handler(request("lookup", {
      ...body,
      request_id: "33333333-3333-4333-8333-333333333333",
    }))).status,
    200,
  );
  assert.equal(current.calls.lookup, 2);
});

test("rate and circuit denials prevent upstream calls", async () => {
  const rateStore = new MemoryStore();
  rateStore.rateAllowed = false;
  const rate = dependencies(rateStore);
  const rateResponse = await createNutritionProviderHandler(rate.deps)(
    request("search", searchBody()),
  );
  assert.equal(rateResponse.status, 429);
  assert.equal(rateResponse.headers.get("retry-after"), "37");
  assert.equal(rate.calls.search, 0);

  const circuitStore = new MemoryStore();
  circuitStore.probeAllowed = false;
  const circuit = dependencies(circuitStore);
  const circuitResponse = await createNutritionProviderHandler(circuit.deps)(
    request("search", searchBody()),
  );
  assert.equal(circuitResponse.status, 503);
  assert.equal(circuit.calls.search, 0);
});

test("half-open allowed probe reaches provider and success resets runtime", async () => {
  const store = new MemoryStore();
  store.beginProbe = async () => {
    store.probeCalls += 1;
    return { probe_allowed: true, state: { circuit_state: "half_open" as const } };
  };
  const current = dependencies(store);
  const response = await createNutritionProviderHandler(current.deps)(
    request("search", searchBody()),
  );
  assert.equal(response.status, 200);
  assert.equal(current.calls.search, 1);
  assert.equal(store.transitions.at(-1)?.event, "success");
});

test("provider rate limits and malformed responses transition shared runtime safely", async () => {
  const limitedStore = new MemoryStore();
  const limited = dependencies(limitedStore, upstream(429, {}, { "retry-after": "90" }));
  assert.equal(
    (await createNutritionProviderHandler(limited.deps)(request("search", searchBody()))).status,
    503,
  );
  assert.equal(limitedStore.transitions[0].event, "rate_limited");

  const malformedStore = new MemoryStore();
  const malformed = dependencies(malformedStore, {
    status: 200,
    headers: new Headers(),
    bodyText: "not-json",
  });
  assert.equal(
    (await createNutritionProviderHandler(malformed.deps)(request("search", searchBody()))).status,
    502,
  );
  assert.equal(malformedStore.queryWrites, 0);
  assert.equal(malformedStore.transitions[0].event, "failure");

  const unavailableStore = new MemoryStore();
  const unavailable = dependencies(unavailableStore, upstream(503, {}));
  assert.equal(
    (await createNutritionProviderHandler(unavailable.deps)(request("search", searchBody())))
      .status,
    503,
  );
  assert.equal(unavailableStore.transitions[0].event, "failure");
});

test("provider timeout aborts request and records circuit failure without retry", async () => {
  const store = new MemoryStore();
  let calls = 0;
  const current = dependencies(store);
  current.deps.timeoutMs = 5;
  current.deps.usda.search = ({ signal }) => {
    calls += 1;
    return new Promise((_resolve, reject) => {
      signal.addEventListener("abort", () => reject(new Error("aborted")), { once: true });
    });
  };
  const response = await createNutritionProviderHandler(current.deps)(
    request("search", searchBody()),
  );
  assert.equal(response.status, 503);
  assert.equal(calls, 1);
  assert.equal(store.transitions[0].errorClass, "upstream-timeout");
});

test("provider log revalidates the signed candidate and forwards trusted 100 g snapshots", async () => {
  const store = new MemoryStore();
  const current = dependencies(store);
  const response = await createNutritionProviderHandler(current.deps)(
    request("log", providerLogBody(await providerToken())),
  );
  assert.equal(response.status, 200);
  assert.equal(current.calls.lookup, 1);
  assert.equal(store.providerLogCalls.length, 1);
  const mutation = store.providerLogCalls[0];
  assert.equal(mutation.userId, USER_ID);
  assert.equal(mutation.input.consumedQuantity, 150);
  assert.equal(mutation.input.consumedUnit, "g");
  assert.equal(mutation.candidate.provider, "usda_fdc");
  assert.equal(mutation.candidate.provider_food_id, "171077");
  assert.equal(mutation.candidate.reference_amount, 100);
  assert.equal(mutation.candidate.reference_unit, "g");
  assert.equal(mutation.candidate.energy_kcal_per_100g, 165);
  assert.equal(mutation.candidate.protein_grams_per_100g, 31.02);
  assert.equal(mutation.candidate.source_updated_at, "2024-01-01T00:00:00.000Z");
  assert.equal((mutation.candidate.provenance as Record<string, unknown>).reference_basis, "per_100_g");
  const payload = await response.json();
  assert.equal(payload.data.result.item.food_id, null);
  assert.equal(payload.data.result.item.energy_kcal_snapshot, 247.5);
});

test("provider log request schema rejects browser nutrition authority and non-gram input", async () => {
  const token = await providerToken();
  for (const unsafe of [
    { kcal: 1 },
    { protein: 1 },
    { carbohydrate: 1 },
    { fat: 1 },
    { fiber: 1 },
    { food_id: "44444444-4444-4444-8444-444444444444" },
    { user_id: USER_ID },
    { role: "trainer" },
    { entitlement: "pro" },
    { provider_url: "https://example.invalid" },
  ]) {
    const store = new MemoryStore();
    const current = dependencies(store);
    const response = await createNutritionProviderHandler(current.deps)(
      request("log", providerLogBody(token, unsafe)),
    );
    assert.equal(response.status, 400);
    assert.equal(store.providerLogCalls.length, 0);
    assert.equal(current.calls.lookup, 0);
  }

  for (const invalid of [
    { consumed_unit: "ml" },
    { consumed_quantity: 0 },
    { consumed_quantity: -1 },
  ]) {
    const store = new MemoryStore();
    const response = await createNutritionProviderHandler(dependencies(store).deps)(
      request("log", providerLogBody(token, invalid)),
    );
    assert.equal(response.status, 400);
    assert.equal(store.providerLogCalls.length, 0);
  }
});

test("provider log rejects invalid candidates before any member log mutation", async () => {
  const validToken = await providerToken();
  const tampered = `${validToken.slice(0, -1)}${validToken.endsWith("a") ? "b" : "a"}`;
  const tamperedStore = new MemoryStore();
  const tamperedResponse = await createNutritionProviderHandler(dependencies(tamperedStore).deps)(
    request("log", providerLogBody(tampered)),
  );
  assert.equal(tamperedResponse.status, 409);
  assert.equal(tamperedStore.providerLogCalls.length, 0);

  const missingMacroStore = new MemoryStore();
  const missingMacro = dependencies(missingMacroStore);
  missingMacro.deps.usda.lookup = async () => upstream(200, usdaFood({
    foodNutrients: [
      { nutrient: { id: 2048 }, amount: 165 },
      { nutrient: { id: 1003 }, amount: 31 },
      { nutrient: { id: 1004 }, amount: 4 },
    ],
  }));
  const missingResponse = await createNutritionProviderHandler(missingMacro.deps)(
    request("log", providerLogBody(validToken)),
  );
  assert.equal(missingResponse.status, 502);
  assert.equal(missingMacroStore.providerLogCalls.length, 0);
});

test("provider log retries are idempotent and changed payload reuse is rejected", async () => {
  const store = new MemoryStore();
  const current = dependencies(store);
  const handler = createNutritionProviderHandler(current.deps);
  const token = await providerToken();
  const body = providerLogBody(token);
  assert.equal((await handler(request("log", body))).status, 200);
  const replay = await handler(request("log", body));
  assert.equal(replay.status, 200);
  assert.equal((await replay.json()).data.result.idempotent_replay, true);
  assert.equal(store.providerLogCalls.length, 2);
  assert.equal(current.calls.lookup, 1);

  const changed = await handler(request("log", providerLogBody(token, { consumed_quantity: 151 })));
  assert.equal(changed.status, 409);
  assert.equal(store.providerLogCalls.length, 2);
});

test("provider replacement uses a separate atomic backend mutation contract", async () => {
  const store = new MemoryStore();
  const current = dependencies(store);
  const token = await providerToken();
  const body = {
    candidate_token: token,
    original_item_id: "33333333-3333-4333-8333-333333333333",
    replacement_item_id: "44444444-4444-4444-8444-444444444444",
    request_id: REQUEST_ID,
    expected_original_updated_at: "2026-08-19T09:55:00.000Z",
    meal_moment: "dinner",
    consumed_quantity: 200,
    consumed_unit: "g",
    notes: "Edited",
  };
  const handler = createNutritionProviderHandler(current.deps);
  const response = await handler(request("replace", body));
  assert.equal(response.status, 200);
  assert.equal(store.providerReplaceCalls.length, 1);
  assert.equal(store.providerReplaceCalls[0].input.originalItemId, body.original_item_id);
  assert.equal(store.providerReplaceCalls[0].input.replacementItemId, body.replacement_item_id);
  assert.equal(store.providerReplaceCalls[0].input.mealMoment, "dinner");
  const payload = await response.json();
  assert.equal(payload.data.result.replacement_item.status, "active");
  assert.equal(payload.data.result.archived_original.status, "archived");

  assert.equal((await handler(request("replace", body))).status, 200);
  assert.equal(
    (await handler(request("replace", { ...body, notes: "Changed reuse" }))).status,
    409,
  );
});

test("provider replacement preserves authoritative timestamp precision exactly", async () => {
  const token = await providerToken();
  const cases = [
    ["2026-08-20T10:12:34.123Z", "2026-08-20T10:12:34.123Z"],
    ["2026-08-20T10:12:34.123456+00:00", "2026-08-20T10:12:34.123456+00:00"],
    ["2026-08-20T12:12:34.654321+02:00", "2026-08-20T12:12:34.654321+02:00"],
    ["  2026-08-20T10:12:34.123456Z  ", "2026-08-20T10:12:34.123456Z"],
  ];
  for (const [inputTimestamp, expectedTimestamp] of cases) {
    const store = new MemoryStore();
    const handler = createNutritionProviderHandler(dependencies(store).deps);
    const response = await handler(request("replace", {
      candidate_token: token,
      original_item_id: "33333333-3333-4333-8333-333333333333",
      replacement_item_id: "44444444-4444-4444-8444-444444444444",
      request_id: REQUEST_ID,
      expected_original_updated_at: inputTimestamp,
      meal_moment: "dinner",
      consumed_quantity: 200,
      consumed_unit: "g",
      notes: "Edited",
    }));
    assert.equal(response.status, 200);
    assert.equal(store.providerReplaceCalls.length, 1);
    assert.equal(
      store.providerReplaceCalls[0].input.expectedOriginalUpdatedAt,
      expectedTimestamp,
    );
  }
});

test("provider replacement rejects malformed authoritative timestamps", async () => {
  const token = await providerToken();
  for (const timestamp of [
    "2026-08-20 10:12:34Z",
    "2026-08-20T10:12:34",
    "2026-02-30T10:12:34.123456Z",
    "2026-08-20T25:12:34Z",
    "not-a-timestamp",
  ]) {
    const store = new MemoryStore();
    const handler = createNutritionProviderHandler(dependencies(store).deps);
    const response = await handler(request("replace", {
      candidate_token: token,
      original_item_id: "33333333-3333-4333-8333-333333333333",
      replacement_item_id: "44444444-4444-4444-8444-444444444444",
      request_id: REQUEST_ID,
      expected_original_updated_at: timestamp,
      meal_moment: "dinner",
      consumed_quantity: 200,
      consumed_unit: "g",
      notes: null,
    }));
    assert.equal(response.status, 400);
    assert.equal((await response.json()).error.code, "invalid_request");
    assert.equal(store.providerReplaceCalls.length, 0);
  }
});

test("historical provider replacement resolves the owned item and uses a valid cache first", async () => {
  const store = new MemoryStore();
  store.foodCache = await validFoodCache();
  const current = dependencies(store);
  const response = await createNutritionProviderHandler(current.deps)(request(
    "replace",
    historicalReplaceBody(),
  ));
  assert.equal(response.status, 200);
  assert.deepEqual(store.resolverCalls, [{
    userId: USER_ID,
    originalItemId: "33333333-3333-4333-8333-333333333333",
  }]);
  assert.equal(current.calls.lookup, 0);
  assert.equal(store.rateCalls, 0);
  assert.equal(store.providerReplaceCalls.length, 1);
  assert.equal(store.providerReplaceCalls[0].input.candidateToken, null);
  assert.equal(store.providerReplaceCalls[0].input.consumedQuantity, 150);
  assert.equal(store.providerReplaceCalls[0].input.mealMoment, "dinner");
  assert.equal(store.providerReplaceCalls[0].input.notes, "Updated historical provider item");
  assert.equal(
    store.providerReplaceCalls[0].input.expectedOriginalUpdatedAt,
    "2026-08-20T10:12:34.123456Z",
  );
});

test("historical provider replacement refreshes a missing cache through controlled lookup", async () => {
  const store = new MemoryStore();
  const current = dependencies(store);
  const response = await createNutritionProviderHandler(current.deps)(request(
    "replace",
    historicalReplaceBody(),
  ));
  assert.equal(response.status, 200);
  assert.equal(store.resolverCalls.length, 1);
  assert.equal(current.calls.lookup, 1);
  assert.equal(store.rateCalls, 1);
  assert.equal(store.foodWrites, 1);
  assert.equal(store.providerReplaceCalls.length, 1);
});

test("historical provider replacement never mutates when provider revalidation is unavailable", async () => {
  const store = new MemoryStore();
  const current = dependencies(store);
  current.deps.usda.lookup = async () => upstream(503, { error: "temporarily unavailable" });
  const response = await createNutritionProviderHandler(current.deps)(request(
    "replace",
    historicalReplaceBody(),
  ));
  assert.equal(response.status, 503);
  assert.equal(store.resolverCalls.length, 1);
  assert.equal(store.providerReplaceCalls.length, 0);
});

test("historical provider resolver identity must match deterministic provider identity", async () => {
  const store = new MemoryStore();
  store.historicalIdentity = {
    ...store.historicalIdentity,
    candidate_id: "55555555-5555-5555-8555-555555555555",
  };
  const response = await createNutritionProviderHandler(dependencies(store).deps)(request(
    "replace",
    historicalReplaceBody(),
  ));
  assert.equal(response.status, 409);
  assert.equal(store.providerReplaceCalls.length, 0);
});

test("changing provider food continues to require a newly signed candidate token", async () => {
  const store = new MemoryStore();
  const current = dependencies(store);
  const response = await createNutritionProviderHandler(current.deps)(request(
    "replace",
    { ...historicalReplaceBody(), candidate_token: await providerToken() },
  ));
  assert.equal(response.status, 200);
  assert.equal(store.resolverCalls.length, 0);
  assert.equal(current.calls.lookup, 1);

  const arbitraryIdentity = await createNutritionProviderHandler(dependencies().deps)(request(
    "replace",
    { ...historicalReplaceBody(), provider_food_id: "171078" },
  ));
  assert.equal(arbitraryIdentity.status, 400);
});

test("historical provider replacement replay remains idempotent", async () => {
  const store = new MemoryStore();
  store.foodCache = await validFoodCache();
  const handler = createNutritionProviderHandler(dependencies(store).deps);
  const first = await handler(request("replace", historicalReplaceBody()));
  const replay = await handler(request("replace", historicalReplaceBody()));
  assert.equal(first.status, 200);
  assert.equal(store.archivedResolverItems.has(ORIGINAL_ITEM_ID), true);
  assert.equal(store.providerReplacementRows.size, 1);
  assert.equal(replay.status, 200);
  assert.equal((await replay.json()).data.result.idempotent_replay, true);
  assert.deepEqual(store.resolverCalls, [
    { userId: USER_ID, originalItemId: ORIGINAL_ITEM_ID },
    { userId: USER_ID, originalItemId: ORIGINAL_ITEM_ID },
    { userId: USER_ID, originalItemId: REPLACEMENT_ITEM_ID },
  ]);
  assert.equal(store.providerReplaceCalls.length, 2);
  assert.equal(store.providerReplacementRows.size, 1);
});

test("historical replay delegates changed grams meal and notes to database rejection", async () => {
  const changedCases = [
    { consumed_quantity: 151 },
    { meal_moment: "lunch" },
    { notes: "Changed replay notes" },
  ];
  for (const changed of changedCases) {
    const store = new MemoryStore();
    store.foodCache = await validFoodCache();
    const handler = createNutritionProviderHandler(dependencies(store).deps);
    assert.equal((await handler(request("replace", historicalReplaceBody()))).status, 200);
    const response = await handler(request("replace", historicalReplaceBody(changed)));
    assert.equal(response.status, 409);
    assert.equal((await response.json()).error.code, "provider_replace_request_conflict");
    assert.equal(store.providerReplacementRows.size, 1);
  }
});

test("historical replay cannot change provider candidate under the same request", async () => {
  const store = new MemoryStore();
  store.foodCache = await validFoodCache();
  const current = dependencies(store);
  const handler = createNutritionProviderHandler(current.deps);
  assert.equal((await handler(request("replace", historicalReplaceBody()))).status, 200);

  store.foodCache = null;
  current.deps.usda.lookup = async () => upstream(200, usdaFood({ fdcId: 171078 }));
  const changedCandidateToken = await signCandidateToken(
    HMAC_KEY,
    "171078",
    "Foundation",
    NOW,
  );
  const response = await handler(request("replace", historicalReplaceBody({
    candidate_token: changedCandidateToken,
  })));
  assert.equal(response.status, 409);
  assert.equal((await response.json()).error.code, "provider_replace_request_conflict");
  assert.equal(store.providerReplacementRows.size, 1);
});

test("historical replay rejects wrong replacement and request identities without a third row", async () => {
  const store = new MemoryStore();
  store.foodCache = await validFoodCache();
  const handler = createNutritionProviderHandler(dependencies(store).deps);
  assert.equal((await handler(request("replace", historicalReplaceBody()))).status, 200);

  const wrongReplacement = await handler(request("replace", historicalReplaceBody({
    replacement_item_id: "55555555-5555-4555-8555-555555555555",
  })));
  assert.equal(wrongReplacement.status, 409);
  assert.equal((await wrongReplacement.json()).error.code, "provider_replace_request_conflict");

  const wrongRequest = await handler(request("replace", historicalReplaceBody({
    request_id: "66666666-6666-4666-8666-666666666666",
  })));
  assert.equal(wrongRequest.status, 409);
  assert.equal((await wrongRequest.json()).error.code, "provider_replace_stale");
  assert.equal(store.providerReplacementRows.size, 1);
});

test("historical replay fallback rejects archived and cross-user replacement items", async () => {
  for (const mode of ["archived", "other_user"] as const) {
    const store = new MemoryStore();
    store.foodCache = await validFoodCache();
    const handler = createNutritionProviderHandler(dependencies(store).deps);
    assert.equal((await handler(request("replace", historicalReplaceBody()))).status, 200);
    if (mode === "archived") store.archivedResolverItems.add(REPLACEMENT_ITEM_ID);
    if (mode === "other_user") store.resolverOwners.set(REPLACEMENT_ITEM_ID, OTHER_USER_ID);

    const response = await handler(request("replace", historicalReplaceBody()));
    assert.equal(response.status, 403);
    assert.equal((await response.json()).error.code, "provider_replace_forbidden");
    assert.equal(store.providerReplaceCalls.length, 1);
    assert.equal(store.providerReplacementRows.size, 1);
  }
});

test("historical replacement never falls back for unexpected resolver failures", async () => {
  const store = new MemoryStore();
  store.resolverFailures.set(
    ORIGINAL_ITEM_ID,
    new ProviderError(
      "provider_replace_unavailable",
      "Provider food logging could not be completed.",
      500,
    ),
  );
  const response = await createNutritionProviderHandler(dependencies(store).deps)(request(
    "replace",
    historicalReplaceBody(),
  ));
  assert.equal(response.status, 500);
  assert.deepEqual(store.resolverCalls, [{ userId: USER_ID, originalItemId: ORIGINAL_ITEM_ID }]);
  assert.equal(store.providerReplaceCalls.length, 0);
});

test("oversized bodies are rejected before provider use", async () => {
  const { deps, calls } = dependencies();
  const response = await createNutritionProviderHandler(deps)(request(
    "search",
    searchBody({
      query: "a".repeat(3),
      padding: "x".repeat(3_000),
    }),
  ));
  assert.equal(response.status, 400);
  assert.equal(calls.search, 0);
});

test("OFF GTIN normalization and explicit g/ml contracts reject unsafe products", async () => {
  assert.equal(normalizeGtin14(OFF_BARCODE), OFF_GTIN14);
  assert.equal(normalizeGtin14("8710398520396"), null);
  const grams = await normalizeOffProductPayload(offFood(), OFF_GTIN14, NOW);
  assert.equal(grams.reference_unit, "g");
  assert.equal(grams.nutrition_basis, "per_100_g");
  assert.equal(grams.provider, OFF_PROVIDER_CODE);
  assert.equal(grams.candidate_id, await createOffCandidateId(OFF_GTIN14));

  const millilitres = await normalizeOffProductPayload(
    offFood({ product: { product_quantity_unit: "ml" } }),
    OFF_GTIN14,
    NOW,
  );
  assert.equal(millilitres.reference_unit, "ml");
  assert.equal(millilitres.nutrition_basis, "per_100_ml");
  await assert.rejects(() =>
    normalizeOffProductPayload(
      offFood({ product: { countries_tags: ["en:belgium"] } }),
      OFF_GTIN14,
      NOW,
    )
  );
  await assert.rejects(() =>
    normalizeOffProductPayload(
      offFood({ product: { nutriments: { "energy-kcal_100g": 110 } } }),
      OFF_GTIN14,
      NOW,
    )
  );
});

test("OFF barcode lookup is local-first and never calls remote for a trusted local hit", async () => {
  const store = new MemoryStore();
  store.localBarcodeResult = {
    result_type: "off_branded_food",
    source_provider: OFF_PROVIDER_CODE,
    source_id: "55555555-5555-4555-8555-555555555555",
    normalized_gtin14: OFF_GTIN14,
  };
  const { deps, calls } = dependencies(store);
  const response = await createNutritionProviderHandler(deps)(request("off-barcode", {
    barcode: OFF_BARCODE,
    request_id: REQUEST_ID,
  }));
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.data.source, "local");
  assert.equal(calls.offLookup, 0);
  assert.equal(store.rateCalls, 0);
});

test("OFF remote exact lookup validates, signs, caches and suppresses repeated provider calls", async () => {
  const store = new MemoryStore();
  const { deps, calls } = dependencies(store);
  const handler = createNutritionProviderHandler(deps);
  const first = await handler(request("off-barcode", {
    barcode: OFF_BARCODE,
    request_id: REQUEST_ID,
  }));
  const firstBody = await first.json();
  assert.equal(first.status, 200);
  assert.equal(firstBody.data.source, OFF_PROVIDER_CODE);
  assert.equal(firstBody.data.cache, "miss");
  assert.equal(firstBody.data.result.provider_food_id, OFF_GTIN14);
  assert.equal(typeof firstBody.data.result.candidate_token, "string");
  assert.equal(calls.offLookup, 1);
  assert.equal(store.foodWrites, 1);

  const second = await handler(request("off-barcode", {
    barcode: OFF_BARCODE,
    request_id: "55555555-5555-4555-8555-555555555555",
  }));
  const secondBody = await second.json();
  assert.equal(second.status, 200);
  assert.equal(secondBody.data.cache, "hit");
  assert.equal(calls.offLookup, 1);
});

test("OFF token is tamper-evident and cannot cross USDA/OFF source boundaries", async () => {
  const store = new MemoryStore();
  store.foodCache = await validOffFoodCache();
  const { deps } = dependencies(store);
  const handler = createNutritionProviderHandler(deps);
  const token = await offCandidateToken();
  const tampered = `${token.slice(0, -1)}${token.endsWith("a") ? "b" : "a"}`;
  assert.equal((await handler(request("off-log", offLogBody(tampered)))).status, 409);
  assert.equal((await handler(request("off-log", offLogBody(await providerToken())))).status, 409);
  assert.equal((await handler(request("lookup", {
    candidate_token: token,
    request_id: REQUEST_ID,
  }))).status, 409);
  assert.equal(store.offLogCalls.length, 0);
});

test("transient OFF logging uses trusted cache snapshot and idempotent gram requests", async () => {
  const store = new MemoryStore();
  store.foodCache = await validOffFoodCache();
  const { deps } = dependencies(store);
  const handler = createNutritionProviderHandler(deps);
  const body = offLogBody(await offCandidateToken());
  const first = await handler(request("off-log", body));
  const second = await handler(request("off-log", body));
  assert.equal(first.status, 200);
  assert.equal(second.status, 200);
  assert.equal((await second.json()).data.result.idempotent_replay, true);
  assert.equal(store.offLogCalls[0].candidate.reference_unit, "g");
  assert.equal(store.offLogCalls[0].candidate.source_checksum.length, 64);
  assert.equal(store.offLogCalls[0].candidate.provenance.license_code, "ODbL-1.0");
});

test("transient OFF logging never assumes ml equals g", async () => {
  const store = new MemoryStore();
  store.foodCache = await validOffFoodCache({ product: { product_quantity_unit: "ml" } });
  const { deps } = dependencies(store);
  const handler = createNutritionProviderHandler(deps);
  const token = await offCandidateToken({ product: { product_quantity_unit: "ml" } });
  assert.equal((await handler(request("off-log", offLogBody(token)))).status, 400);
  assert.equal((await handler(request("off-log", offLogBody(token, {
    consumed_unit: "ml",
  })))).status, 200);
  assert.equal(store.offLogCalls.at(-1)?.candidate.reference_unit, "ml");
});

test("historical transient OFF edit uses immutable server snapshot without an expired token", async () => {
  const store = new MemoryStore();
  const candidate = await normalizeOffProductPayload(offFood(), OFF_GTIN14, NOW);
  store.offHistoricalSnapshot = {
    provider: OFF_PROVIDER_CODE,
    provider_food_id: candidate.provider_food_id,
    candidate_id: candidate.candidate_id,
    mapping_version: OFF_MAPPING_VERSION,
    provider_data_type: "off_branded",
    food_name: candidate.name,
    brand: candidate.brand,
    barcode_original: candidate.barcode_original,
    normalized_gtin14: candidate.barcode,
    reference_amount: 100,
    reference_unit: candidate.reference_unit,
    energy_kcal_per_100: candidate.kcal,
    protein_grams_per_100: candidate.protein,
    carbohydrate_grams_per_100: candidate.carbohydrates,
    fat_grams_per_100: candidate.fat,
    fiber_grams_per_100: candidate.fiber,
    source_version: candidate.provenance.source_revision,
    source_checksum: candidate.provenance.source_checksum,
    retrieved_at: candidate.provenance.retrieved_at,
    source_updated_at: candidate.provenance.source_updated_at,
    provenance: candidate.provenance,
  };
  store.resolverOwners.set(ORIGINAL_ITEM_ID, USER_ID);
  const { deps } = dependencies(store);
  const response = await createNutritionProviderHandler(deps)(
    request("off-replace", offReplaceBody()),
  );
  assert.equal(response.status, 200);
  assert.equal(store.offReplaceCalls.length, 1);
  assert.equal(store.offReplaceCalls[0].candidate.source_checksum, candidate.provenance.source_checksum);
  assert.equal(store.foodWrites, 0);
});

test("OFF provider rate denial never calls upstream or creates a transient log", async () => {
  const store = new MemoryStore();
  store.rateAllowed = false;
  const { deps, calls } = dependencies(store);
  const response = await createNutritionProviderHandler(deps)(request("off-barcode", {
    barcode: OFF_BARCODE,
    request_id: REQUEST_ID,
  }));
  assert.equal(response.status, 429);
  assert.equal(calls.offLookup, 0);
  assert.equal(store.offLogCalls.length, 0);
});
