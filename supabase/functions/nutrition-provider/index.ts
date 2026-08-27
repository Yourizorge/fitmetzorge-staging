import { createClient } from "npm:@supabase/supabase-js@2.95.0";
import {
  MAX_SEARCH_RESULTS,
  OFF_API_BASE_URL,
  OFF_MAPPING_VERSION,
  OFF_PROVIDER_CODE,
  OFF_USER_AGENT,
  PROVIDER_CODE,
  QUERY_DATA_TYPE_FILTER,
  USDA_API_BASE_URL,
} from "./constants.ts";
import { createNutritionProviderHandler } from "./handler.ts";
import { ActiveProviderItemUnavailableError, ProviderError } from "./types.ts";
import type {
  AuthGateway,
  FoodCacheKey,
  FoodCacheRow,
  HistoricalProviderIdentity,
  OffClient,
  OffSnapshotCandidate,
  OperationalStore,
  ProviderCode,
  ProviderLogger,
  QueryCacheKey,
  QueryCacheRow,
  RuntimeTransitionInput,
  UsdaClient,
  UsdaLookupRequest,
  UsdaSearchRequest,
} from "./types.ts";

function requiredEnvironment(name: string): string {
  const value = Deno.env.get(name)?.trim();
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

function firstKey(...names: string[]): string {
  for (const name of names) {
    const raw = Deno.env.get(name)?.trim();
    if (!raw) continue;
    if (!raw.startsWith("[") && !raw.startsWith("{")) return raw;
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        const first = parsed.find((value) => typeof value === "string" && value.trim());
        if (first) return first.trim();
      }
      if (parsed && typeof parsed === "object") {
        const values = Object.values(parsed as Record<string, unknown>);
        const first = values.find((value) => typeof value === "string" && value.trim());
        if (typeof first === "string") return first.trim();
      }
    } catch {
      // Structured key sets that cannot be interpreted are not usable client keys.
    }
  }
  throw new Error(`Missing usable Supabase key: ${names.join(", ")}`);
}

const supabaseUrl = requiredEnvironment("SUPABASE_URL");
const publishableKey = firstKey(
  "SUPABASE_PUBLISHABLE_KEY",
  "SUPABASE_ANON_KEY",
  "SUPABASE_PUBLISHABLE_KEYS",
);
const serviceRoleKey = firstKey(
  "SUPABASE_SECRET_KEY",
  "SUPABASE_SERVICE_ROLE_KEY",
  "SUPABASE_SECRET_KEYS",
);
const usdaApiKey = requiredEnvironment("USDA_FDC_API_KEY");
const providerHmacKey = requiredEnvironment("FMZ_PROVIDER_HMAC_KEY");

const admin = createClient(supabaseUrl, serviceRoleKey, {
  auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
  global: { headers: { "x-fmz-component": "nutrition-provider" } },
});

const auth: AuthGateway = {
  async verifyBearer(token) {
    const verifier = createClient(supabaseUrl, publishableKey, {
      auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
      global: { headers: { Authorization: `Bearer ${token}` } },
    });
    const { data, error } = await verifier.auth.getUser(token);
    if (error || !data.user) return null;
    return { id: data.user.id };
  },
};

function failDatabase(operation: string, error: { message?: string } | null): never {
  throw new Error(`${operation} failed: ${error?.message ?? "database error"}`);
}

function failProviderMutation(
  operation: "log" | "replace",
  error: { code?: string; message?: string } | null,
): never {
  const code = error?.code ?? "";
  if (code === "22023" || code === "23514") {
    throw new ProviderError(
      `provider_${operation}_invalid`,
      "Provider food input was rejected.",
      400,
    );
  }
  if (code === "23505") {
    throw new ProviderError(
      `provider_${operation}_request_conflict`,
      "Request identity was already used with different input.",
      409,
    );
  }
  if (code === "40001") {
    throw new ProviderError(
      `provider_${operation}_stale`,
      "Food log item changed; refresh and try again.",
      409,
    );
  }
  if (code === "42501") {
    throw new ProviderError(
      `provider_${operation}_forbidden`,
      "Provider food logging is not allowed for this request.",
      403,
    );
  }
  throw new ProviderError(
    `provider_${operation}_unavailable`,
    "Provider food logging could not be completed.",
    500,
  );
}

function providerMutationResult(
  operation: "log" | "replace",
  value: unknown,
): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new ProviderError(
      `provider_${operation}_response_invalid`,
      "Provider food logging returned an invalid response.",
      500,
    );
  }
  const result = value as Record<string, unknown>;
  const required = operation === "log"
    ? ["item", "day", "idempotent_replay"]
    : ["replacement_item", "archived_original", "day", "idempotent_replay"];
  if (
    required.some((key) => !(key in result)) ||
    typeof result.idempotent_replay !== "boolean" ||
    !result.day || typeof result.day !== "object" || Array.isArray(result.day)
  ) {
    throw new ProviderError(
      `provider_${operation}_response_invalid`,
      "Provider food logging returned an invalid response.",
      500,
    );
  }
  return result;
}

const store: OperationalStore = {
  async getQueryCache(key: QueryCacheKey) {
    const { data, error } = await admin
      .from("nutrition_provider_query_cache")
      .select(
        "provider_code,query_hmac,locale,country_code,page_number,page_size,data_type_filter,filter_key,filter_identity,mapping_version,result_payload,payload_checksum,result_count,cache_status,source_version,fetched_at,expires_at",
      )
      .eq("provider_code", key.providerCode)
      .eq("query_hmac", key.queryHmac)
      .eq("locale", key.locale)
      .eq("country_code", key.countryCode)
      .eq("page_number", key.pageNumber)
      .eq("page_size", key.pageSize)
      .eq("filter_key", key.filterKey)
      .eq("mapping_version", key.mappingVersion)
      .maybeSingle();
    if (error) failDatabase("query cache read", error);
    return data as QueryCacheRow | null;
  },
  async putQueryCache(row: QueryCacheRow) {
    const { error } = await admin.from("nutrition_provider_query_cache").upsert(row, {
      onConflict:
        "provider_code,query_hmac,locale,country_code,page_number,page_size,filter_key,mapping_version",
    });
    if (error) failDatabase("query cache write", error);
  },
  async getFoodCache(key: FoodCacheKey) {
    const { data, error } = await admin
      .from("nutrition_provider_food_cache")
      .select(
        "provider_code,provider_food_id,provider_data_type,mapping_version,candidate_id,normalized_payload,payload_checksum,quality_state,rejection_code,source_version,source_updated_at,provenance,metadata,fetched_at,expires_at",
      )
      .eq("provider_code", key.providerCode)
      .eq("provider_food_id", key.providerFoodId)
      .eq("mapping_version", key.mappingVersion)
      .maybeSingle();
    if (error) failDatabase("food cache read", error);
    return data as FoodCacheRow | null;
  },
  async putFoodCache(row: FoodCacheRow) {
    const { error } = await admin.from("nutrition_provider_food_cache").upsert(row, {
      onConflict: "provider_code,provider_food_id,mapping_version",
    });
    if (error) failDatabase("food cache write", error);
  },
  async consumeRateLimit(providerCode, userSubjectHmac, requestId) {
    const { data, error } = await admin.rpc("fmz_phase4_provider_consume_rate_limits", {
      p_provider_code: providerCode,
      p_user_subject_hmac: userSubjectHmac,
      p_request_id: requestId,
    });
    if (error) failDatabase("rate limit", error);
    return data;
  },
  async beginProbe(providerCode) {
    const { data, error } = await admin.rpc("fmz_phase4_provider_transition_runtime_state", {
      p_provider_code: providerCode,
      p_event: "begin_probe",
      p_metadata: {
        caller: "nutrition-provider",
        mapping_version: providerCode === OFF_PROVIDER_CODE ? OFF_MAPPING_VERSION : "phase4_usda_v1",
      },
    });
    if (error) failDatabase("circuit probe", error);
    return data;
  },
  async transitionRuntime(providerCode: ProviderCode, input: RuntimeTransitionInput) {
    const { error } = await admin.rpc("fmz_phase4_provider_transition_runtime_state", {
      p_provider_code: providerCode,
      p_event: input.event,
      p_retry_after_seconds: input.retryAfterSeconds ?? null,
      p_error_class: input.errorClass ?? null,
      p_upstream_limit: input.upstreamLimit ?? null,
      p_upstream_remaining: input.upstreamRemaining ?? null,
      p_upstream_reset_at: input.upstreamResetAt ?? null,
      p_metadata: input.metadata ?? {
        caller: "nutrition-provider",
        mapping_version: providerCode === OFF_PROVIDER_CODE ? OFF_MAPPING_VERSION : "phase4_usda_v1",
      },
    });
    if (error) failDatabase("circuit transition", error);
  },
  async resolveProviderFoodLogItem(userId, originalItemId) {
    const { data, error } = await admin.rpc("fmz_phase4_resolve_provider_food_log_item", {
      p_user_id: userId,
      p_original_item_id: originalItemId,
    });
    if (
      error?.code === "42501" &&
      error.message === "active provider food log item is unavailable for this user"
    ) {
      throw new ActiveProviderItemUnavailableError();
    }
    if (error) failProviderMutation("replace", error);
    return data as HistoricalProviderIdentity;
  },
  async logProviderFoodItem({ userId, input, candidate }) {
    const { data, error } = await admin.rpc("fmz_phase4_log_provider_food_item", {
      p_user_id: userId,
      p_item_id: input.itemId,
      p_request_id: input.requestId,
      p_log_date: input.logDate,
      p_timezone_name: input.timezoneName,
      p_timezone_offset_minutes: input.timezoneOffsetMinutes,
      p_meal_moment: input.mealMoment,
      p_consumed_quantity: input.consumedQuantity,
      p_consumed_unit: input.consumedUnit,
      p_notes: input.notes,
      p_consumed_at: input.consumedAt,
      p_candidate: candidate,
    });
    if (error) failProviderMutation("log", error);
    return providerMutationResult("log", data);
  },
  async replaceProviderFoodLogItem({ userId, input, candidate }) {
    const { data, error } = await admin.rpc("fmz_phase4_replace_provider_food_log_item", {
      p_user_id: userId,
      p_original_item_id: input.originalItemId,
      p_replacement_item_id: input.replacementItemId,
      p_replacement_request_id: input.requestId,
      p_expected_original_updated_at: input.expectedOriginalUpdatedAt,
      p_meal_moment: input.mealMoment,
      p_consumed_quantity: input.consumedQuantity,
      p_consumed_unit: input.consumedUnit,
      p_notes: input.notes,
      p_candidate: candidate,
    });
    if (error) failProviderMutation("replace", error);
    return providerMutationResult("replace", data);
  },
  async resolveLocalBarcode(userId, normalizedGtin14) {
    const { data, error } = await admin.rpc("fmz_phase4_resolve_member_barcode", {
      p_user_id: userId,
      p_normalized_gtin14: normalizedGtin14,
    });
    if (error) failDatabase("local barcode resolution", error);
    if (data === null) return null;
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      throw new ProviderError("local_barcode_response_invalid", "Local barcode result is invalid.", 500);
    }
    return data as Record<string, unknown>;
  },
  async resolveTransientOffFoodLogItem(userId, originalItemId) {
    const { data, error } = await admin.rpc("fmz_phase4_resolve_transient_off_food_log_item", {
      p_user_id: userId,
      p_original_item_id: originalItemId,
    });
    if (error?.code === "42501") throw new ActiveProviderItemUnavailableError();
    if (error) failProviderMutation("replace", error);
    return data as OffSnapshotCandidate;
  },
  async logTransientOffFoodItem({ userId, input, candidate }) {
    const { data, error } = await admin.rpc("fmz_phase4_log_transient_off_food_item", {
      p_user_id: userId,
      p_item_id: input.itemId,
      p_request_id: input.requestId,
      p_log_date: input.logDate,
      p_timezone_name: input.timezoneName,
      p_timezone_offset_minutes: input.timezoneOffsetMinutes,
      p_meal_moment: input.mealMoment,
      p_consumed_quantity: input.consumedQuantity,
      p_consumed_unit: input.consumedUnit,
      p_notes: input.notes,
      p_consumed_at: input.consumedAt,
      p_candidate: candidate,
    });
    if (error) failProviderMutation("log", error);
    return providerMutationResult("log", data);
  },
  async replaceTransientOffFoodItem({ userId, input, candidate }) {
    const { data, error } = await admin.rpc("fmz_phase4_replace_transient_off_food_item", {
      p_user_id: userId,
      p_original_item_id: input.originalItemId,
      p_replacement_item_id: input.replacementItemId,
      p_replacement_request_id: input.requestId,
      p_expected_original_updated_at: input.expectedOriginalUpdatedAt,
      p_meal_moment: input.mealMoment,
      p_consumed_quantity: input.consumedQuantity,
      p_consumed_unit: input.consumedUnit,
      p_notes: input.notes,
      p_candidate: candidate,
    });
    if (error) failProviderMutation("replace", error);
    return providerMutationResult("replace", data);
  },
};

async function fetchUsda(
  url: URL,
  init: RequestInit,
): Promise<{ status: number; headers: Headers; bodyText: string }> {
  const response = await fetch(url, init);
  return { status: response.status, headers: response.headers, bodyText: await response.text() };
}

const usda: UsdaClient = {
  search(input: UsdaSearchRequest) {
    const url = new URL(`${USDA_API_BASE_URL}/foods/search`);
    url.searchParams.set("api_key", usdaApiKey);
    return fetchUsda(url, {
      method: "POST",
      signal: input.signal,
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({
        query: input.query,
        dataType: [...input.dataTypes],
        pageNumber: input.pageNumber,
        pageSize: Math.min(input.pageSize, MAX_SEARCH_RESULTS),
      }),
    });
  },
  lookup(input: UsdaLookupRequest) {
    const url = new URL(`${USDA_API_BASE_URL}/food/${encodeURIComponent(input.providerFoodId)}`);
    url.searchParams.set("api_key", usdaApiKey);
    return fetchUsda(url, {
      method: "GET",
      signal: input.signal,
      headers: { accept: "application/json" },
    });
  },
};

const off: OffClient = {
  lookupBarcode(input) {
    const url = new URL(
      `${OFF_API_BASE_URL}/${encodeURIComponent(input.normalizedGtin14)}.json`,
    );
    url.searchParams.set(
      "fields",
      [
        "code",
        "product_name_nl",
        "product_name",
        "product_name_en",
        "brands",
        "countries_tags",
        "product_quantity_unit",
        "nutriments",
        "rev",
        "last_updated_t",
        "last_modified_t",
      ].join(","),
    );
    return fetchUsda(url, {
      method: "GET",
      signal: input.signal,
      headers: {
        accept: "application/json",
        "user-agent": OFF_USER_AGENT,
      },
    });
  },
};

const logger: ProviderLogger = {
  write(event) {
    console.info(JSON.stringify({ component: "nutrition-provider", ...event }));
  },
};

const handler = createNutritionProviderHandler({
  auth,
  store,
  usda,
  off,
  logger,
  hmacKey: providerHmacKey,
});

Deno.serve(handler);

export { handler, QUERY_DATA_TYPE_FILTER };
