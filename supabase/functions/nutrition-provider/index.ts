import { createClient } from "npm:@supabase/supabase-js@2.95.0";
import {
  MAX_SEARCH_RESULTS,
  PROVIDER_CODE,
  QUERY_DATA_TYPE_FILTER,
  USDA_API_BASE_URL,
} from "./constants.ts";
import { createNutritionProviderHandler } from "./handler.ts";
import type {
  AuthGateway,
  FoodCacheKey,
  FoodCacheRow,
  OperationalStore,
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
  async consumeRateLimit(userSubjectHmac, requestId) {
    const { data, error } = await admin.rpc("fmz_phase4_provider_consume_rate_limits", {
      p_provider_code: PROVIDER_CODE,
      p_user_subject_hmac: userSubjectHmac,
      p_request_id: requestId,
    });
    if (error) failDatabase("rate limit", error);
    return data;
  },
  async beginProbe() {
    const { data, error } = await admin.rpc("fmz_phase4_provider_transition_runtime_state", {
      p_provider_code: PROVIDER_CODE,
      p_event: "begin_probe",
      p_metadata: { caller: "nutrition-provider", mapping_version: "phase4_usda_v1" },
    });
    if (error) failDatabase("circuit probe", error);
    return data;
  },
  async transitionRuntime(input: RuntimeTransitionInput) {
    const { error } = await admin.rpc("fmz_phase4_provider_transition_runtime_state", {
      p_provider_code: PROVIDER_CODE,
      p_event: input.event,
      p_retry_after_seconds: input.retryAfterSeconds ?? null,
      p_error_class: input.errorClass ?? null,
      p_upstream_limit: input.upstreamLimit ?? null,
      p_upstream_remaining: input.upstreamRemaining ?? null,
      p_upstream_reset_at: input.upstreamResetAt ?? null,
      p_metadata: input.metadata ??
        { caller: "nutrition-provider", mapping_version: "phase4_usda_v1" },
    });
    if (error) failDatabase("circuit transition", error);
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

const logger: ProviderLogger = {
  write(event) {
    console.info(JSON.stringify({ component: "nutrition-provider", ...event }));
  },
};

const handler = createNutritionProviderHandler({
  auth,
  store,
  usda,
  logger,
  hmacKey: providerHmacKey,
});

Deno.serve(handler);

export { handler, QUERY_DATA_TYPE_FILTER };
