import assert from "node:assert/strict";
import test from "node:test";
import {
  ACCEPTED_DATA_TYPES,
  MAPPING_VERSION,
  PHASE3_EXERCISE_UUID_NAMESPACE,
  PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE,
} from "./constants.ts";
import {
  candidateIdentityName,
  createCandidateId,
  sha256Hex,
  signCandidateToken,
  uuidV5,
} from "./crypto.ts";
import { createNutritionProviderHandler } from "./handler.ts";
import { normalizeUsdaFood } from "./normalization.ts";
import type {
  FoodCacheKey,
  FoodCacheRow,
  NutritionProviderDependencies,
  OperationalStore,
  QueryCacheKey,
  QueryCacheRow,
  RuntimeTransitionInput,
  StructuredLogEvent,
  UpstreamResponse,
} from "./types.ts";

const NOW = new Date("2026-08-19T10:00:00.000Z");
const USER_ID = "11111111-1111-4111-8111-111111111111";
const REQUEST_ID = "22222222-2222-4222-8222-222222222222";
const HMAC_KEY = "test-only-key-with-at-least-thirty-two-characters";

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
  async consumeRateLimit(_subject: string, requestId: string) {
    this.rateCalls += 1;
    const replayed = this.rateRequestIds.includes(requestId);
    this.rateRequestIds.push(requestId);
    return this.rateAllowed
      ? { allowed: true, replayed }
      : { allowed: false, replayed: false, retry_after_seconds: 37 };
  }
  async beginProbe() {
    this.probeCalls += 1;
    return { probe_allowed: this.probeAllowed };
  }
  async transitionRuntime(input: RuntimeTransitionInput) {
    this.transitions.push(input);
  }
}

function dependencies(store = new MemoryStore(), searchResponse?: UpstreamResponse): {
  deps: NutritionProviderDependencies;
  logs: StructuredLogEvent[];
  calls: { search: number; lookup: number };
} {
  const logs: StructuredLogEvent[] = [];
  const calls = { search: 0, lookup: 0 };
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
  route: "search" | "lookup",
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
