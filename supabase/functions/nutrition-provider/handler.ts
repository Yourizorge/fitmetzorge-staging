import {
  ACCEPTED_DATA_TYPES,
  ALLOWED_STAGING_ORIGINS,
  BODY_LIMIT_BYTES,
  CANDIDATE_TOKEN_TTL_SECONDS,
  FOOD_DETAIL_TTL_SECONDS,
  MAPPING_VERSION,
  MAX_RETRY_AFTER_SECONDS,
  MAX_SEARCH_RESULTS,
  OFF_DATA_TYPE,
  OFF_FOOD_CACHE_TTL_SECONDS,
  OFF_MAPPING_VERSION,
  OFF_NEGATIVE_CACHE_TTL_SECONDS,
  OFF_PROVIDER_CODE,
  PROVIDER_ATTRIBUTION_URL,
  PROVIDER_CODE,
  PROVIDER_LABEL,
  QUERY_DATA_TYPE_FILTER,
  QUERY_EMPTY_TTL_SECONDS,
  QUERY_POSITIVE_TTL_SECONDS,
  UPSTREAM_RESPONSE_LIMIT_BYTES,
  UPSTREAM_TIMEOUT_MS,
} from "./constants.ts";
import {
  createCandidateId,
  createOffCandidateId,
  hmacHex,
  hmacRequestUuid,
  sha256Hex,
  signCandidateToken,
  signOffCandidateToken,
  stableJson,
  verifyCandidateToken,
  verifyOffCandidateToken,
} from "./crypto.ts";
import { normalizeUsdaFood, normalizeUsdaSearchPayload } from "./normalization.ts";
import { normalizeGtin14, normalizeOffProductPayload, validateOffCandidate } from "./off-normalization.ts";
import type {
  CandidateTokenPayload,
  FoodCacheRow,
  HistoricalProviderIdentity,
  LookupInput,
  MemberSafeCandidate,
  MemberOffSafeCandidate,
  NutritionProviderDependencies,
  OffBarcodeInput,
  OffCandidateTokenPayload,
  OffLogInput,
  OffReplaceInput,
  OffSafeCandidate,
  OffSnapshotCandidate,
  ProviderCode,
  ProviderLogInput,
  ProviderReplaceInput,
  ProviderSnapshotCandidate,
  QueryCacheKey,
  QueryCacheRow,
  RouteName,
  RuntimeTransitionInput,
  SafeCandidate,
  SearchInput,
  StructuredLogEvent,
  UpstreamResponse,
} from "./types.ts";
import { ActiveProviderItemUnavailableError, ProviderError } from "./types.ts";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;
const PROVIDER_FOOD_ID_PATTERN = /^[1-9][0-9]{0,15}$/u;
const GTIN14_PATTERN = /^[0-9]{14}$/u;
const COUNTRY_PATTERN = /^[A-Z]{2}$/u;
// deno-lint-ignore no-control-regex -- control characters are intentionally rejected at the boundary.
const SAFE_QUERY = /^[^\u0000-\u001f\u007f]{3,80}$/u;

function corsHeaders(origin: string | null): Headers {
  const headers = new Headers({
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    vary: "Origin",
  });
  if (origin && ALLOWED_STAGING_ORIGINS.has(origin)) {
    headers.set("access-control-allow-origin", origin);
    headers.set("access-control-allow-methods", "POST, OPTIONS");
    headers.set(
      "access-control-allow-headers",
      "authorization, apikey, content-type, x-client-info, x-retry-count, traceparent, tracestate, baggage",
    );
    headers.set("access-control-expose-headers", "retry-after");
    headers.set("access-control-max-age", "600");
  }
  return headers;
}

function jsonResponse(
  status: number,
  body: unknown,
  origin: string | null,
  extra?: HeadersInit,
): Response {
  const headers = corsHeaders(origin);
  if (extra) new Headers(extra).forEach((value, key) => headers.set(key, value));
  return new Response(JSON.stringify(body), { status, headers });
}

function errorResponse(error: ProviderError, origin: string | null): Response {
  const extra = error.status === 429 && typeof error.details?.retry_after_seconds === "number"
    ? { "retry-after": String(error.details.retry_after_seconds) }
    : undefined;
  return jsonResponse(
    error.status,
    {
      ok: false,
      error: { code: error.code, message: error.message },
    },
    origin,
    extra,
  );
}

function routeFromUrl(url: URL): RouteName {
  const route = url.pathname.split("/").filter(Boolean).at(-1);
  if (
    route === "search" || route === "lookup" || route === "log" || route === "replace" ||
    route === "off-barcode" || route === "off-log" || route === "off-replace"
  ) {
    return route;
  }
  throw new ProviderError("route_not_found", "Route not found.", 404);
}

function exactObject(value: unknown, allowedKeys: readonly string[]): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new ProviderError("invalid_request", "Request body must be an object.", 400);
  }
  const parsed = value as Record<string, unknown>;
  if (Object.keys(parsed).some((key) => !allowedKeys.includes(key))) {
    throw new ProviderError("invalid_request", "Request contains unsupported fields.", 400);
  }
  return parsed;
}

function parseRequestId(value: unknown): string {
  if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
    throw new ProviderError("invalid_request_id", "A valid request_id is required.", 400);
  }
  return value.toLowerCase();
}

function parseSearch(value: unknown): SearchInput {
  const body = exactObject(value, [
    "query",
    "locale",
    "country_code",
    "page_number",
    "page_size",
    "request_id",
  ]);
  if (typeof body.query !== "string") {
    throw new ProviderError("invalid_query", "Query must contain 3 to 80 characters.", 400);
  }
  const query = body.query.normalize("NFKC").replace(/\s+/gu, " ").trim();
  if (!SAFE_QUERY.test(query)) {
    throw new ProviderError("invalid_query", "Query must contain 3 to 80 safe characters.", 400);
  }
  const locale = body.locale ?? "nl";
  if (locale !== "nl" && locale !== "en" && locale !== "de") {
    throw new ProviderError("invalid_locale", "Locale is not supported.", 400);
  }
  const countryCode = typeof body.country_code === "string"
    ? body.country_code.toUpperCase()
    : "NL";
  if (!COUNTRY_PATTERN.test(countryCode)) {
    throw new ProviderError("invalid_country", "Country code is invalid.", 400);
  }
  const pageNumber = body.page_number ?? 1;
  const pageSize = body.page_size ?? MAX_SEARCH_RESULTS;
  if (!Number.isSafeInteger(pageNumber) || Number(pageNumber) < 1 || Number(pageNumber) > 3) {
    throw new ProviderError("invalid_page", "Page number is invalid.", 400);
  }
  if (
    !Number.isSafeInteger(pageSize) || Number(pageSize) < 1 || Number(pageSize) > MAX_SEARCH_RESULTS
  ) {
    throw new ProviderError("invalid_page_size", "Page size is invalid.", 400);
  }
  return {
    query,
    normalizedQuery: query.toLocaleLowerCase(locale),
    locale,
    countryCode,
    pageNumber: Number(pageNumber),
    pageSize: Number(pageSize),
    requestId: parseRequestId(body.request_id),
  };
}

function parseLookup(value: unknown): LookupInput {
  const body = exactObject(value, ["candidate_token", "request_id"]);
  if (typeof body.candidate_token !== "string") {
    throw new ProviderError("candidate_token_invalid", "Candidate token is required.", 400);
  }
  return { candidateToken: body.candidate_token, requestId: parseRequestId(body.request_id) };
}

function parseOffBarcode(value: unknown): OffBarcodeInput {
  const body = exactObject(value, ["barcode", "request_id"]);
  const normalizedGtin14 = normalizeGtin14(body.barcode);
  if (typeof body.barcode !== "string" || !normalizedGtin14) {
    throw new ProviderError(
      "invalid_barcode",
      "A valid EAN-8, UPC-A, EAN-13, or GTIN-14 barcode is required.",
      400,
    );
  }
  return {
    barcode: body.barcode.trim(),
    normalizedGtin14,
    requestId: parseRequestId(body.request_id),
  };
}

function parseUuid(value: unknown, field: string): string {
  if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
    throw new ProviderError("invalid_request", `${field} must be a valid UUID.`, 400);
  }
  return value.toLowerCase();
}

function parseMealMoment(value: unknown): ProviderLogInput["mealMoment"] {
  if (value !== "breakfast" && value !== "lunch" && value !== "dinner" && value !== "snacks") {
    throw new ProviderError("invalid_meal_moment", "Meal moment is not supported.", 400);
  }
  return value;
}

function parseConsumedQuantity(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0 || value > 100_000) {
    throw new ProviderError("invalid_consumed_quantity", "Consumed grams are invalid.", 400);
  }
  return value;
}

function parseNotes(value: unknown): string | null {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value !== "string" || value.length > 1_000) {
    throw new ProviderError("invalid_notes", "Notes exceed the supported length.", 400);
  }
  const normalized = value.trim();
  return normalized || null;
}

function parseIsoTimestamp(value: unknown, field: string, nullable: boolean): string | null {
  if (nullable && (value === undefined || value === null)) return null;
  if (typeof value !== "string" || !Number.isFinite(Date.parse(value))) {
    throw new ProviderError("invalid_request", `${field} must be a valid timestamp.`, 400);
  }
  return new Date(value).toISOString();
}

const RFC3339_PRECISE_TIMESTAMP_PATTERN =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?(?:Z|[+-](\d{2}):(\d{2}))$/u;

function parseExactIsoTimestamp(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new ProviderError("invalid_request", `${field} must be a valid timestamp.`, 400);
  }
  const timestamp = value.trim();
  const match = RFC3339_PRECISE_TIMESTAMP_PATTERN.exec(timestamp);
  if (!match) {
    throw new ProviderError("invalid_request", `${field} must be a valid timestamp.`, 400);
  }
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, offsetHourText, offsetMinuteText] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  const offsetHour = offsetHourText === undefined ? 0 : Number(offsetHourText);
  const offsetMinute = offsetMinuteText === undefined ? 0 : Number(offsetMinuteText);
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (
    month < 1 || month > 12 || day < 1 || day > daysInMonth[month - 1] ||
    hour > 23 || minute > 59 || second > 59 || offsetHour > 23 || offsetMinute > 59
  ) {
    throw new ProviderError("invalid_request", `${field} must be a valid timestamp.`, 400);
  }
  return timestamp;
}

function parseLogDate(value: unknown): string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/u.test(value)) {
    throw new ProviderError("invalid_log_date", "Log date must be a local calendar date.", 400);
  }
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (!Number.isFinite(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    throw new ProviderError("invalid_log_date", "Log date must be a valid calendar date.", 400);
  }
  return value;
}

function parseTimezone(value: unknown): string {
  if (
    typeof value !== "string" || value.length < 1 || value.length > 64 ||
    !/^[A-Za-z0-9_+\-/]+$/u.test(value)
  ) {
    throw new ProviderError("invalid_timezone", "Timezone is invalid.", 400);
  }
  try {
    new Intl.DateTimeFormat("en", { timeZone: value }).format(new Date(0));
  } catch {
    throw new ProviderError("invalid_timezone", "Timezone is invalid.", 400);
  }
  return value;
}

function parseLog(value: unknown): ProviderLogInput {
  const body = exactObject(value, [
    "candidate_token",
    "item_id",
    "request_id",
    "log_date",
    "timezone_name",
    "timezone_offset_minutes",
    "meal_moment",
    "consumed_quantity",
    "consumed_unit",
    "notes",
    "consumed_at",
  ]);
  if (typeof body.candidate_token !== "string") {
    throw new ProviderError("candidate_token_invalid", "Candidate token is required.", 400);
  }
  if (body.consumed_unit !== "g") {
    throw new ProviderError("invalid_consumed_unit", "Provider logging supports grams only.", 400);
  }
  if (
    !Number.isSafeInteger(body.timezone_offset_minutes) ||
    Number(body.timezone_offset_minutes) < -840 ||
    Number(body.timezone_offset_minutes) > 840
  ) {
    throw new ProviderError("invalid_timezone_offset", "Timezone offset is invalid.", 400);
  }
  return {
    candidateToken: body.candidate_token,
    itemId: parseUuid(body.item_id, "item_id"),
    requestId: parseRequestId(body.request_id),
    logDate: parseLogDate(body.log_date),
    timezoneName: parseTimezone(body.timezone_name),
    timezoneOffsetMinutes: Number(body.timezone_offset_minutes),
    mealMoment: parseMealMoment(body.meal_moment),
    consumedQuantity: parseConsumedQuantity(body.consumed_quantity),
    consumedUnit: "g",
    notes: parseNotes(body.notes),
    consumedAt: parseIsoTimestamp(body.consumed_at, "consumed_at", true),
  };
}

function parseReplace(value: unknown): ProviderReplaceInput {
  const body = exactObject(value, [
    "candidate_token",
    "original_item_id",
    "replacement_item_id",
    "request_id",
    "expected_original_updated_at",
    "meal_moment",
    "consumed_quantity",
    "consumed_unit",
    "notes",
  ]);
  if ("candidate_token" in body && typeof body.candidate_token !== "string") {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 400);
  }
  if (body.consumed_unit !== "g") {
    throw new ProviderError("invalid_consumed_unit", "Provider logging supports grams only.", 400);
  }
  const expectedOriginalUpdatedAt = parseExactIsoTimestamp(
    body.expected_original_updated_at,
    "expected_original_updated_at",
  );
  return {
    candidateToken: typeof body.candidate_token === "string" ? body.candidate_token : null,
    originalItemId: parseUuid(body.original_item_id, "original_item_id"),
    replacementItemId: parseUuid(body.replacement_item_id, "replacement_item_id"),
    requestId: parseRequestId(body.request_id),
    expectedOriginalUpdatedAt,
    mealMoment: parseMealMoment(body.meal_moment),
    consumedQuantity: parseConsumedQuantity(body.consumed_quantity),
    consumedUnit: "g",
    notes: parseNotes(body.notes),
  };
}

function parseOffConsumedUnit(value: unknown): "g" | "ml" {
  if (value !== "g" && value !== "ml") {
    throw new ProviderError("invalid_consumed_unit", "OFF logging supports grams or millilitres.", 400);
  }
  return value;
}

function parseOffLog(value: unknown): OffLogInput {
  const body = exactObject(value, [
    "candidate_token",
    "item_id",
    "request_id",
    "log_date",
    "timezone_name",
    "timezone_offset_minutes",
    "meal_moment",
    "consumed_quantity",
    "consumed_unit",
    "notes",
    "consumed_at",
  ]);
  if (typeof body.candidate_token !== "string") {
    throw new ProviderError("off_candidate_token_invalid", "OFF candidate token is required.", 400);
  }
  if (
    !Number.isSafeInteger(body.timezone_offset_minutes) ||
    Number(body.timezone_offset_minutes) < -840 ||
    Number(body.timezone_offset_minutes) > 840
  ) {
    throw new ProviderError("invalid_timezone_offset", "Timezone offset is invalid.", 400);
  }
  return {
    candidateToken: body.candidate_token,
    itemId: parseUuid(body.item_id, "item_id"),
    requestId: parseRequestId(body.request_id),
    logDate: parseLogDate(body.log_date),
    timezoneName: parseTimezone(body.timezone_name),
    timezoneOffsetMinutes: Number(body.timezone_offset_minutes),
    mealMoment: parseMealMoment(body.meal_moment),
    consumedQuantity: parseConsumedQuantity(body.consumed_quantity),
    consumedUnit: parseOffConsumedUnit(body.consumed_unit),
    notes: parseNotes(body.notes),
    consumedAt: parseIsoTimestamp(body.consumed_at, "consumed_at", true),
  };
}

function parseOffReplace(value: unknown): OffReplaceInput {
  const body = exactObject(value, [
    "candidate_token",
    "original_item_id",
    "replacement_item_id",
    "request_id",
    "expected_original_updated_at",
    "meal_moment",
    "consumed_quantity",
    "consumed_unit",
    "notes",
  ]);
  if ("candidate_token" in body && typeof body.candidate_token !== "string") {
    throw new ProviderError("off_candidate_token_invalid", "OFF candidate token is invalid.", 400);
  }
  return {
    candidateToken: typeof body.candidate_token === "string" ? body.candidate_token : null,
    originalItemId: parseUuid(body.original_item_id, "original_item_id"),
    replacementItemId: parseUuid(body.replacement_item_id, "replacement_item_id"),
    requestId: parseRequestId(body.request_id),
    expectedOriginalUpdatedAt: parseExactIsoTimestamp(
      body.expected_original_updated_at,
      "expected_original_updated_at",
    ),
    mealMoment: parseMealMoment(body.meal_moment),
    consumedQuantity: parseConsumedQuantity(body.consumed_quantity),
    consumedUnit: parseOffConsumedUnit(body.consumed_unit),
    notes: parseNotes(body.notes),
  };
}

async function readBody(request: Request): Promise<unknown> {
  const length = request.headers.get("content-length");
  if (length && Number(length) > BODY_LIMIT_BYTES) {
    throw new ProviderError("request_too_large", "Request body is too large.", 400);
  }
  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > BODY_LIMIT_BYTES) {
    throw new ProviderError("request_too_large", "Request body is too large.", 400);
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new ProviderError("invalid_json", "Request body is not valid JSON.", 400);
  }
}

function bearerToken(request: Request): string {
  const header = request.headers.get("authorization");
  const match = header?.match(/^Bearer ([A-Za-z0-9._~-]{20,4096})$/u);
  if (!match) throw new ProviderError("unauthorized", "Authentication is required.", 401);
  return match[1];
}

function isFresh(expiresAt: string, now: Date): boolean {
  const expiry = Date.parse(expiresAt);
  return Number.isFinite(expiry) && expiry > now.getTime();
}

function exactRecord(
  value: unknown,
  expectedKeys: readonly string[],
): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const parsed = value as Record<string, unknown>;
  return Object.keys(parsed).sort().join("|") === [...expectedKeys].sort().join("|")
    ? parsed
    : null;
}

function safeCachedText(value: unknown, maxLength: number, nullable = false): boolean {
  if (nullable && value === null) return true;
  return typeof value === "string" &&
    value.length > 0 &&
    value.length <= maxLength &&
    !Array.from(value).some((character) => {
      const code = character.charCodeAt(0);
      return code <= 0x1f || code === 0x7f;
    });
}

function safeCachedNumber(value: unknown, minimum: number, maximum: number): boolean {
  return typeof value === "number" && Number.isFinite(value) && value >= minimum &&
    value <= maximum;
}

async function isSafeCandidatePayload(value: unknown): Promise<boolean> {
  const candidate = exactRecord(value, [
    "attribution",
    "brand",
    "candidate_id",
    "carbohydrates",
    "data_type",
    "derivation",
    "fat",
    "fiber",
    "kcal",
    "mapping_version",
    "name",
    "portions",
    "protein",
    "provenance",
    "provider",
    "provider_food_id",
    "provider_label",
    "quality",
    "reference_amount",
    "reference_unit",
  ]);
  if (!candidate) return false;
  if (
    typeof candidate.provider_food_id !== "string" ||
    !/^[1-9][0-9]{0,15}$/u.test(candidate.provider_food_id) ||
    candidate.provider !== PROVIDER_CODE ||
    candidate.provider_label !== PROVIDER_LABEL ||
    candidate.mapping_version !== MAPPING_VERSION ||
    candidate.quality !== "candidate" ||
    candidate.reference_amount !== 100 ||
    candidate.reference_unit !== "g" ||
    typeof candidate.candidate_id !== "string" ||
    candidate.candidate_id !== await createCandidateId(candidate.provider_food_id) ||
    typeof candidate.data_type !== "string" ||
    !ACCEPTED_DATA_TYPES.includes(candidate.data_type as typeof ACCEPTED_DATA_TYPES[number]) ||
    !safeCachedText(candidate.name, 180) ||
    !safeCachedText(candidate.brand, 120, true) ||
    !safeCachedNumber(candidate.kcal, 0, 1_500) ||
    !safeCachedNumber(candidate.protein, 0, 100) ||
    !safeCachedNumber(candidate.carbohydrates, 0, 100) ||
    !safeCachedNumber(candidate.fat, 0, 100) ||
    !(candidate.fiber === null || safeCachedNumber(candidate.fiber, 0, 100))
  ) return false;

  const derivation = exactRecord(candidate.derivation, ["energy", "reference_basis"]);
  if (
    !derivation ||
    !["2048_kcal", "2047_kcal", "1008_kcal", "1062_kj_converted"].includes(
      String(derivation.energy),
    ) ||
    derivation.reference_basis !== "per_100_g"
  ) return false;

  const attribution = exactRecord(candidate.attribution, ["label", "license", "url"]);
  if (
    !attribution ||
    attribution.label !== PROVIDER_LABEL ||
    attribution.license !== "CC0 1.0" ||
    attribution.url !== PROVIDER_ATTRIBUTION_URL
  ) return false;

  const provenance = exactRecord(candidate.provenance, [
    "data_type",
    "mapping_version",
    "provider",
    "provider_food_id",
    "retrieved_at",
    "source_version",
  ]);
  if (
    !provenance ||
    provenance.provider !== PROVIDER_CODE ||
    provenance.provider_food_id !== candidate.provider_food_id ||
    provenance.data_type !== candidate.data_type ||
    provenance.mapping_version !== MAPPING_VERSION ||
    typeof provenance.retrieved_at !== "string" ||
    !Number.isFinite(Date.parse(provenance.retrieved_at)) ||
    !safeCachedText(provenance.source_version, 120, true)
  ) return false;

  if (!Array.isArray(candidate.portions) || candidate.portions.length > 20) return false;
  return candidate.portions.every((value) => {
    const portion = exactRecord(value, [
      "amount",
      "equivalent_amount",
      "equivalent_unit",
      "label",
      "unit",
    ]);
    return Boolean(
      portion &&
        safeCachedText(portion.label, 80) &&
        safeCachedNumber(portion.amount, Number.MIN_VALUE, 10_000) &&
        portion.unit === "serving" &&
        safeCachedNumber(portion.equivalent_amount, Number.MIN_VALUE, 100_000) &&
        portion.equivalent_unit === "g",
    );
  });
}

async function validQueryCache(
  row: QueryCacheRow | null,
  now: Date,
): Promise<SafeCandidate[] | null> {
  if (!row || !isFresh(row.expires_at, now) || row.mapping_version !== MAPPING_VERSION) return null;
  if (row.cache_status !== "positive" && row.cache_status !== "empty") return null;
  if (
    !Array.isArray(row.result_payload) ||
    row.result_payload.length !== row.result_count ||
    row.result_payload.length > MAX_SEARCH_RESULTS ||
    (row.cache_status === "empty") !== (row.result_payload.length === 0)
  ) return null;
  if (await sha256Hex(row.result_payload) !== row.payload_checksum) return null;
  for (const candidate of row.result_payload) {
    if (!await isSafeCandidatePayload(candidate)) return null;
  }
  return row.result_payload;
}

async function validFoodCache(row: FoodCacheRow | null, now: Date): Promise<SafeCandidate | null> {
  if (!row || !isFresh(row.expires_at, now) || row.mapping_version !== MAPPING_VERSION) return null;
  if (row.quality_state !== "candidate" && row.quality_state !== "validated") return null;
  if (await sha256Hex(row.normalized_payload) !== row.payload_checksum) return null;
  if (!await isSafeCandidatePayload(row.normalized_payload)) return null;
  const payload = row.normalized_payload as Partial<SafeCandidate>;
  if (
    payload.candidate_id !== row.candidate_id ||
    payload.provider_food_id !== row.provider_food_id ||
    payload.mapping_version !== MAPPING_VERSION ||
    payload.provider !== PROVIDER_CODE
  ) return null;
  return payload as SafeCandidate;
}

async function validOffFoodCache(
  row: FoodCacheRow | null,
  now: Date,
): Promise<{ candidate: OffSafeCandidate; checksum: string } | null> {
  if (
    !row || !isFresh(row.expires_at, now) || row.provider_code !== OFF_PROVIDER_CODE ||
    row.provider_data_type !== OFF_DATA_TYPE || row.mapping_version !== OFF_MAPPING_VERSION ||
    (row.quality_state !== "candidate" && row.quality_state !== "validated") ||
    !/^[0-9a-f]{64}$/u.test(row.payload_checksum)
  ) return null;
  if (await sha256Hex(row.normalized_payload) !== row.payload_checksum) return null;
  const candidate = await validateOffCandidate(row.normalized_payload);
  if (
    !candidate || candidate.candidate_id !== row.candidate_id ||
    candidate.provider_food_id !== row.provider_food_id
  ) return null;
  return { candidate, checksum: candidate.provenance.source_checksum };
}

async function validRejectedOffFoodCache(
  row: FoodCacheRow | null,
  expectedGtin14: string,
  now: Date,
): Promise<string | null> {
  if (
    !row || !isFresh(row.expires_at, now) || row.provider_code !== OFF_PROVIDER_CODE ||
    row.provider_food_id !== expectedGtin14 || row.provider_data_type !== OFF_DATA_TYPE ||
    row.mapping_version !== OFF_MAPPING_VERSION ||
    (row.quality_state !== "quarantined" && row.quality_state !== "rejected") ||
    !row.rejection_code || !/^[a-z0-9-]{1,80}$/u.test(row.rejection_code)
  ) return null;
  if (await sha256Hex(row.normalized_payload) !== row.payload_checksum) return null;
  const payload = exactRecord(row.normalized_payload, [
    "data_type",
    "mapping_version",
    "provider",
    "provider_food_id",
    "rejection_code",
  ]);
  return payload && payload.provider === OFF_PROVIDER_CODE &&
      payload.provider_food_id === expectedGtin14 && payload.data_type === OFF_DATA_TYPE &&
      payload.mapping_version === OFF_MAPPING_VERSION && payload.rejection_code === row.rejection_code
    ? row.rejection_code
    : null;
}

async function memberOffCandidate(
  candidate: OffSafeCandidate,
  checksum: string,
  hmacKey: string,
  now: Date,
): Promise<MemberOffSafeCandidate> {
  return {
    ...candidate,
    candidate_token: await signOffCandidateToken(hmacKey, candidate, checksum, now),
  };
}

async function validRejectedFoodCache(
  row: FoodCacheRow | null,
  token: CandidateTokenPayload,
  now: Date,
): Promise<boolean> {
  if (
    !row ||
    !isFresh(row.expires_at, now) ||
    row.mapping_version !== MAPPING_VERSION ||
    (row.quality_state !== "quarantined" && row.quality_state !== "rejected") ||
    row.provider_code !== token.provider ||
    row.provider_food_id !== token.provider_food_id ||
    row.provider_data_type !== token.data_type ||
    row.candidate_id !== token.candidate_id
  ) return false;
  if (await sha256Hex(row.normalized_payload) !== row.payload_checksum) return false;
  const payload = exactRecord(row.normalized_payload, [
    "data_type",
    "mapping_version",
    "provider",
    "provider_food_id",
    "rejection_code",
  ]);
  return Boolean(
    payload &&
      payload.provider === token.provider &&
      payload.provider_food_id === token.provider_food_id &&
      payload.data_type === token.data_type &&
      payload.mapping_version === token.mapping_version &&
      typeof payload.rejection_code === "string" &&
      /^[a-z0-9-]{1,80}$/u.test(payload.rejection_code) &&
      payload.rejection_code === row.rejection_code,
  );
}

function memberCandidates(
  candidates: SafeCandidate[],
  hmacKey: string,
  now: Date,
): Promise<MemberSafeCandidate[]> {
  return Promise.all(candidates.map(async (candidate) => ({
    ...candidate,
    candidate_token: await signCandidateToken(
      hmacKey,
      candidate.provider_food_id,
      candidate.data_type,
      now,
    ),
  })));
}

function retryAfter(response: UpstreamResponse): number {
  const raw = response.headers.get("retry-after");
  const seconds = raw ? Number(raw) : Number.NaN;
  return Number.isSafeInteger(seconds) && seconds > 0
    ? Math.min(seconds, MAX_RETRY_AFTER_SECONDS)
    : 60;
}

function boundedJson(response: UpstreamResponse): unknown {
  if (new TextEncoder().encode(response.bodyText).byteLength > UPSTREAM_RESPONSE_LIMIT_BYTES) {
    throw new ProviderError(
      "provider_response_too_large",
      "Provider response exceeded the safe limit.",
      502,
    );
  }
  try {
    return JSON.parse(response.bodyText);
  } catch {
    throw new ProviderError("provider_response_malformed", "Provider response is malformed.", 502);
  }
}

async function withTimeout<T>(
  timeoutMs: number,
  action: (signal: AbortSignal) => Promise<T>,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await action(controller.signal);
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ProviderError("provider_timeout", "Provider request timed out.", 503);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function upstreamRateMetadata(
  response: UpstreamResponse,
): Pick<RuntimeTransitionInput, "upstreamLimit" | "upstreamRemaining"> {
  const limit = Number(response.headers.get("x-ratelimit-limit"));
  const remaining = Number(response.headers.get("x-ratelimit-remaining"));
  const metadata: Pick<RuntimeTransitionInput, "upstreamLimit" | "upstreamRemaining"> = {};
  if (
    Number.isSafeInteger(limit) && limit >= 0 && Number.isSafeInteger(remaining) &&
    remaining >= 0 && remaining <= limit
  ) {
    metadata.upstreamLimit = limit;
    metadata.upstreamRemaining = remaining;
  }
  return metadata;
}

async function enforceOperationalGate(
  dependencies: NutritionProviderDependencies,
  providerCode: ProviderCode,
  userId: string,
  clientRequestId: string,
  operationIdentity: string,
): Promise<void> {
  const subject = await hmacHex(dependencies.hmacKey, "provider-rate-subject-v1", userId);
  const rateRequestId = await hmacRequestUuid(
    dependencies.hmacKey,
    clientRequestId,
    `${subject}:${operationIdentity}`,
  );
  const rate = await dependencies.store.consumeRateLimit(providerCode, subject, rateRequestId);
  if (!rate.allowed) {
    const retry = Math.max(1, Math.min(rate.retry_after_seconds ?? 60, MAX_RETRY_AFTER_SECONDS));
    throw new ProviderError("rate_limited", "Provider request limit reached.", 429, {
      retry_after_seconds: retry,
    });
  }
  if (rate.replayed) {
    throw new ProviderError(
      "request_replay_pending",
      "This provider request is already being processed or requires a new request_id.",
      409,
    );
  }
  const probe = await dependencies.store.beginProbe(providerCode);
  if (!probe.probe_allowed) {
    throw new ProviderError(
      "provider_temporarily_unavailable",
      "Provider is temporarily unavailable.",
      503,
    );
  }
}

async function queryCacheKey(input: SearchInput, hmacKey: string): Promise<QueryCacheKey> {
  const filterIdentity = {
    country_code: input.countryCode,
    data_types: QUERY_DATA_TYPE_FILTER,
    locale: input.locale,
    page_number: input.pageNumber,
    page_size: input.pageSize,
  };
  return {
    providerCode: PROVIDER_CODE,
    queryHmac: await hmacHex(hmacKey, "provider-query-v1", input.normalizedQuery),
    locale: input.locale,
    countryCode: input.countryCode,
    pageNumber: input.pageNumber,
    pageSize: input.pageSize,
    filterKey: await hmacHex(hmacKey, "provider-filter-v1", stableJson(filterIdentity)),
    mappingVersion: MAPPING_VERSION,
  };
}

async function handleSearch(
  input: SearchInput,
  userId: string,
  dependencies: NutritionProviderDependencies,
  now: Date,
): Promise<{ cache: "hit" | "miss"; results: MemberSafeCandidate[] }> {
  const key = await queryCacheKey(input, dependencies.hmacKey);
  const cached = await validQueryCache(await dependencies.store.getQueryCache(key), now);
  if (cached !== null) {
    return { cache: "hit", results: await memberCandidates(cached, dependencies.hmacKey, now) };
  }

  await enforceOperationalGate(
    dependencies,
    PROVIDER_CODE,
    userId,
    input.requestId,
    stableJson({
      country_code: input.countryCode,
      locale: input.locale,
      normalized_query: input.normalizedQuery,
      page_number: input.pageNumber,
      page_size: input.pageSize,
      route: "search",
    }),
  );
  let response: UpstreamResponse;
  try {
    response = await withTimeout(
      dependencies.timeoutMs ?? UPSTREAM_TIMEOUT_MS,
      (signal) =>
        dependencies.usda.search({
          query: input.query,
          pageNumber: input.pageNumber,
          pageSize: input.pageSize,
          dataTypes: ACCEPTED_DATA_TYPES,
          signal,
        }),
    );
  } catch (error) {
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "failure",
      errorClass: error instanceof ProviderError && error.code === "provider_timeout"
        ? "upstream-timeout"
        : "upstream-network-error",
    });
    if (error instanceof ProviderError) throw error;
    throw new ProviderError("provider_unavailable", "Provider is temporarily unavailable.", 503);
  }
  if (response.status === 429) {
    const retry = retryAfter(response);
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "rate_limited",
      retryAfterSeconds: Math.min(retry, 3_600),
      errorClass: "upstream-rate-limited",
      ...upstreamRateMetadata(response),
    });
    throw new ProviderError("provider_rate_limited", "Provider is temporarily rate limited.", 503);
  }
  if (response.status < 200 || response.status >= 300) {
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "failure",
      errorClass: "upstream-http-error",
    });
    throw new ProviderError("provider_unavailable", "Provider is temporarily unavailable.", 503);
  }

  let normalized;
  try {
    normalized = await normalizeUsdaSearchPayload(boundedJson(response), now);
  } catch (error) {
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "failure",
      errorClass: "upstream-payload-invalid",
    });
    throw error;
  }
  await dependencies.store.transitionRuntime(PROVIDER_CODE, {
    event: "success",
    ...upstreamRateMetadata(response),
  });

  const fetchedAt = now.toISOString();
  const ttl = normalized.candidates.length > 0
    ? QUERY_POSITIVE_TTL_SECONDS
    : QUERY_EMPTY_TTL_SECONDS;
  const filterIdentity = {
    country_code: input.countryCode,
    data_types: QUERY_DATA_TYPE_FILTER,
    locale: input.locale,
    page_number: input.pageNumber,
    page_size: input.pageSize,
  };
  await dependencies.store.putQueryCache({
    provider_code: PROVIDER_CODE,
    query_hmac: key.queryHmac,
    locale: input.locale,
    country_code: input.countryCode,
    page_number: input.pageNumber,
    page_size: input.pageSize,
    data_type_filter: QUERY_DATA_TYPE_FILTER,
    filter_key: key.filterKey,
    filter_identity: filterIdentity,
    mapping_version: MAPPING_VERSION,
    result_payload: normalized.candidates,
    payload_checksum: await sha256Hex(normalized.candidates),
    result_count: normalized.candidates.length,
    cache_status: normalized.candidates.length > 0 ? "positive" : "empty",
    source_version: null,
    fetched_at: fetchedAt,
    expires_at: new Date(now.getTime() + ttl * 1_000).toISOString(),
  });
  return {
    cache: "miss",
    results: await memberCandidates(normalized.candidates, dependencies.hmacKey, now),
  };
}

async function handleLookup(
  input: LookupInput,
  userId: string,
  dependencies: NutritionProviderDependencies,
  now: Date,
): Promise<{ cache: "hit" | "miss"; result: MemberSafeCandidate }> {
  const token = await verifyCandidateToken(
    dependencies.hmacKey,
    input.candidateToken,
    now,
    ACCEPTED_DATA_TYPES,
  );
  const cacheKey = {
    providerCode: PROVIDER_CODE as "usda_fdc",
    providerFoodId: token.provider_food_id,
    mappingVersion: MAPPING_VERSION,
  };
  const foodCacheRow = await dependencies.store.getFoodCache(cacheKey);
  if (await validRejectedFoodCache(foodCacheRow, token, now)) {
    throw new ProviderError(
      "candidate_unavailable",
      "Candidate did not pass provider quality checks.",
      502,
    );
  }
  const cached = await validFoodCache(foodCacheRow, now);
  if (cached) {
    if (cached.data_type !== token.data_type || cached.candidate_id !== token.candidate_id) {
      throw new ProviderError(
        "candidate_token_mismatch",
        "Candidate token identity does not match.",
        409,
      );
    }
    return {
      cache: "hit",
      result: (await memberCandidates([cached], dependencies.hmacKey, now))[0],
    };
  }

  await enforceOperationalGate(
    dependencies,
    PROVIDER_CODE,
    userId,
    input.requestId,
    stableJson({
      data_type: token.data_type,
      mapping_version: token.mapping_version,
      provider: token.provider,
      provider_food_id: token.provider_food_id,
      route: "lookup",
    }),
  );
  let response: UpstreamResponse;
  try {
    response = await withTimeout(
      dependencies.timeoutMs ?? UPSTREAM_TIMEOUT_MS,
      (signal) => dependencies.usda.lookup({ providerFoodId: token.provider_food_id, signal }),
    );
  } catch (error) {
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "failure",
      errorClass: error instanceof ProviderError && error.code === "provider_timeout"
        ? "upstream-timeout"
        : "upstream-network-error",
    });
    if (error instanceof ProviderError) throw error;
    throw new ProviderError("provider_unavailable", "Provider is temporarily unavailable.", 503);
  }
  if (response.status === 404) {
    await dependencies.store.transitionRuntime(PROVIDER_CODE, { event: "success" });
    throw new ProviderError("candidate_not_found", "Candidate was not found.", 404);
  }
  if (response.status === 429) {
    const retry = retryAfter(response);
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "rate_limited",
      retryAfterSeconds: Math.min(retry, 3_600),
      errorClass: "upstream-rate-limited",
      ...upstreamRateMetadata(response),
    });
    throw new ProviderError("provider_rate_limited", "Provider is temporarily rate limited.", 503);
  }
  if (response.status < 200 || response.status >= 300) {
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "failure",
      errorClass: "upstream-http-error",
    });
    throw new ProviderError("provider_unavailable", "Provider is temporarily unavailable.", 503);
  }

  let candidate: SafeCandidate;
  try {
    candidate = await normalizeUsdaFood(boundedJson(response), now);
  } catch (error) {
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "failure",
      errorClass: "upstream-payload-invalid",
    });
    if (error instanceof ProviderError) {
      const rejectedPayload = {
        provider: PROVIDER_CODE,
        provider_food_id: token.provider_food_id,
        data_type: token.data_type,
        mapping_version: MAPPING_VERSION,
        rejection_code: error.code.replaceAll("_", "-").slice(0, 80),
      };
      await dependencies.store.putFoodCache({
        provider_code: PROVIDER_CODE,
        provider_food_id: token.provider_food_id,
        provider_data_type: token.data_type,
        mapping_version: MAPPING_VERSION,
        candidate_id: token.candidate_id,
        normalized_payload: rejectedPayload,
        payload_checksum: await sha256Hex(rejectedPayload),
        quality_state: "quarantined",
        rejection_code: error.code.replaceAll("_", "-").slice(0, 80),
        source_version: null,
        source_updated_at: null,
        provenance: { provider: PROVIDER_CODE, mapping_version: MAPPING_VERSION },
        metadata: {},
        fetched_at: now.toISOString(),
        expires_at: new Date(now.getTime() + QUERY_EMPTY_TTL_SECONDS * 1_000).toISOString(),
      });
    }
    throw error;
  }
  if (
    candidate.provider_food_id !== token.provider_food_id || candidate.data_type !== token.data_type
  ) {
    await dependencies.store.transitionRuntime(PROVIDER_CODE, {
      event: "failure",
      errorClass: "candidate-identity-mismatch",
    });
    throw new ProviderError(
      "candidate_token_mismatch",
      "Candidate identity does not match provider response.",
      409,
    );
  }
  await dependencies.store.transitionRuntime(PROVIDER_CODE, {
    event: "success",
    ...upstreamRateMetadata(response),
  });

  const fetchedAt = now.toISOString();
  await dependencies.store.putFoodCache({
    provider_code: PROVIDER_CODE,
    provider_food_id: candidate.provider_food_id,
    provider_data_type: candidate.data_type,
    mapping_version: MAPPING_VERSION,
    candidate_id: candidate.candidate_id,
    normalized_payload: candidate,
    payload_checksum: await sha256Hex(candidate),
    quality_state: "candidate",
    rejection_code: null,
    source_version: candidate.provenance.source_version,
    source_updated_at: null,
    provenance: candidate.provenance,
    metadata: { attribution_license: candidate.attribution.license },
    fetched_at: fetchedAt,
    expires_at: new Date(now.getTime() + FOOD_DETAIL_TTL_SECONDS * 1_000).toISOString(),
  });
  return {
    cache: "miss",
    result: (await memberCandidates([candidate], dependencies.hmacKey, now))[0],
  };
}

function offFoodCacheKey(normalizedGtin14: string) {
  return {
    providerCode: OFF_PROVIDER_CODE as "open_food_facts",
    providerFoodId: normalizedGtin14,
    mappingVersion: OFF_MAPPING_VERSION,
  };
}

async function putRejectedOffCache(
  dependencies: NutritionProviderDependencies,
  normalizedGtin14: string,
  rejectionCode: string,
  now: Date,
): Promise<void> {
  const normalizedCode = rejectionCode.replaceAll("_", "-").slice(0, 80);
  const payload = {
    provider: OFF_PROVIDER_CODE,
    provider_food_id: normalizedGtin14,
    data_type: OFF_DATA_TYPE,
    mapping_version: OFF_MAPPING_VERSION,
    rejection_code: normalizedCode,
  };
  await dependencies.store.putFoodCache({
    provider_code: OFF_PROVIDER_CODE,
    provider_food_id: normalizedGtin14,
    provider_data_type: OFF_DATA_TYPE,
    mapping_version: OFF_MAPPING_VERSION,
    candidate_id: await createOffCandidateId(normalizedGtin14),
    normalized_payload: payload,
    payload_checksum: await sha256Hex(payload),
    quality_state: "quarantined",
    rejection_code: normalizedCode,
    source_version: null,
    source_updated_at: null,
    provenance: { provider: OFF_PROVIDER_CODE, mapping_version: OFF_MAPPING_VERSION },
    metadata: { cache_kind: "transient_off_negative" },
    fetched_at: now.toISOString(),
    expires_at: new Date(now.getTime() + OFF_NEGATIVE_CACHE_TTL_SECONDS * 1_000).toISOString(),
  });
}

async function resolveOffTokenCandidate(
  candidateToken: string,
  dependencies: NutritionProviderDependencies,
  now: Date,
): Promise<{ candidate: OffSafeCandidate; cache: "hit" }> {
  const token = await verifyOffCandidateToken(dependencies.hmacKey, candidateToken, now);
  const cached = await validOffFoodCache(
    await dependencies.store.getFoodCache(offFoodCacheKey(token.provider_food_id)),
    now,
  );
  if (!cached) {
    throw new ProviderError(
      "off_candidate_unavailable",
      "OFF candidate is no longer available; scan the barcode again.",
      409,
    );
  }
  if (
    cached.candidate.candidate_id !== token.candidate_id ||
    cached.candidate.nutrition_basis !== token.reference_basis ||
    cached.checksum !== token.payload_checksum
  ) {
    throw new ProviderError(
      "off_candidate_token_mismatch",
      "OFF candidate token does not match the trusted snapshot.",
      409,
    );
  }
  return { candidate: cached.candidate, cache: "hit" };
}

async function handleOffBarcode(
  input: OffBarcodeInput,
  userId: string,
  dependencies: NutritionProviderDependencies,
  now: Date,
): Promise<{
  cache: "hit" | "miss" | "not_checked";
  source: "local" | "open_food_facts";
  result: Record<string, unknown> | MemberOffSafeCandidate;
}> {
  const local = await dependencies.store.resolveLocalBarcode(userId, input.normalizedGtin14);
  if (local) return { cache: "not_checked", source: "local", result: local };

  const cacheKey = offFoodCacheKey(input.normalizedGtin14);
  const cacheRow = await dependencies.store.getFoodCache(cacheKey);
  const cached = await validOffFoodCache(cacheRow, now);
  if (cached) {
    return {
      cache: "hit",
      source: OFF_PROVIDER_CODE,
      result: await memberOffCandidate(
        cached.candidate,
        cached.checksum,
        dependencies.hmacKey,
        now,
      ),
    };
  }
  if (await validRejectedOffFoodCache(cacheRow, input.normalizedGtin14, now)) {
    throw new ProviderError(
      "off_product_unavailable",
      "No usable Open Food Facts product was found for this barcode.",
      404,
    );
  }

  await enforceOperationalGate(
    dependencies,
    OFF_PROVIDER_CODE,
    userId,
    input.requestId,
    stableJson({
      provider: OFF_PROVIDER_CODE,
      normalized_gtin14: input.normalizedGtin14,
      route: "off-barcode",
    }),
  );
  let response: UpstreamResponse;
  try {
    response = await withTimeout(
      dependencies.timeoutMs ?? UPSTREAM_TIMEOUT_MS,
      (signal) => dependencies.off.lookupBarcode({ normalizedGtin14: input.normalizedGtin14, signal }),
    );
  } catch (error) {
    await dependencies.store.transitionRuntime(OFF_PROVIDER_CODE, {
      event: "failure",
      errorClass: error instanceof ProviderError && error.code === "provider_timeout"
        ? "upstream-timeout"
        : "upstream-network-error",
    });
    if (error instanceof ProviderError) throw error;
    throw new ProviderError("off_provider_unavailable", "Open Food Facts is unavailable.", 503);
  }
  if (response.status === 404) {
    await dependencies.store.transitionRuntime(OFF_PROVIDER_CODE, { event: "success" });
    await putRejectedOffCache(dependencies, input.normalizedGtin14, "off_product_not_found", now);
    throw new ProviderError(
      "off_product_not_found",
      "No Open Food Facts product was found for this barcode.",
      404,
    );
  }
  if (response.status === 429) {
    const retry = retryAfter(response);
    await dependencies.store.transitionRuntime(OFF_PROVIDER_CODE, {
      event: "rate_limited",
      retryAfterSeconds: Math.min(retry, 3_600),
      errorClass: "upstream-rate-limited",
      ...upstreamRateMetadata(response),
    });
    throw new ProviderError("off_provider_rate_limited", "Open Food Facts is busy.", 503);
  }
  if (response.status < 200 || response.status >= 300) {
    await dependencies.store.transitionRuntime(OFF_PROVIDER_CODE, {
      event: "failure",
      errorClass: "upstream-http-error",
    });
    throw new ProviderError("off_provider_unavailable", "Open Food Facts is unavailable.", 503);
  }

  let candidate: OffSafeCandidate;
  try {
    candidate = await normalizeOffProductPayload(
      boundedJson(response),
      input.normalizedGtin14,
      now,
    );
  } catch (error) {
    await dependencies.store.transitionRuntime(OFF_PROVIDER_CODE, {
      event: "failure",
      errorClass: error instanceof ProviderError ? error.code.replaceAll("_", "-") : "upstream-payload-invalid",
    });
    if (error instanceof ProviderError && error.status >= 400 && error.status < 500) {
      await putRejectedOffCache(dependencies, input.normalizedGtin14, error.code, now);
    }
    throw error;
  }
  await dependencies.store.transitionRuntime(OFF_PROVIDER_CODE, {
    event: "success",
    ...upstreamRateMetadata(response),
  });
  const payloadChecksum = await sha256Hex(candidate);
  await dependencies.store.putFoodCache({
    provider_code: OFF_PROVIDER_CODE,
    provider_food_id: candidate.provider_food_id,
    provider_data_type: OFF_DATA_TYPE,
    mapping_version: OFF_MAPPING_VERSION,
    candidate_id: candidate.candidate_id,
    normalized_payload: candidate,
    payload_checksum: payloadChecksum,
    quality_state: "validated",
    rejection_code: null,
    source_version: candidate.provenance.source_revision,
    source_updated_at: candidate.provenance.source_updated_at,
    provenance: candidate.provenance,
    metadata: {
      cache_kind: "transient_off_exact_barcode",
      source_checksum: candidate.provenance.source_checksum,
      reference_basis: candidate.nutrition_basis,
    },
    fetched_at: now.toISOString(),
    expires_at: new Date(now.getTime() + OFF_FOOD_CACHE_TTL_SECONDS * 1_000).toISOString(),
  });
  return {
    cache: "miss",
    source: OFF_PROVIDER_CODE,
    result: await memberOffCandidate(
      candidate,
      candidate.provenance.source_checksum,
      dependencies.hmacKey,
      now,
    ),
  };
}

function offSnapshot(candidate: OffSafeCandidate): OffSnapshotCandidate {
  return {
    provider: OFF_PROVIDER_CODE,
    provider_food_id: candidate.provider_food_id,
    candidate_id: candidate.candidate_id,
    mapping_version: OFF_MAPPING_VERSION,
    provider_data_type: OFF_DATA_TYPE,
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
}

async function validHistoricalOffSnapshot(value: unknown): Promise<OffSnapshotCandidate> {
  const snapshot = exactRecord(value, [
    "barcode_original",
    "brand",
    "candidate_id",
    "carbohydrate_grams_per_100",
    "energy_kcal_per_100",
    "fat_grams_per_100",
    "fiber_grams_per_100",
    "food_name",
    "mapping_version",
    "normalized_gtin14",
    "protein_grams_per_100",
    "provenance",
    "provider",
    "provider_data_type",
    "provider_food_id",
    "reference_amount",
    "reference_unit",
    "retrieved_at",
    "source_checksum",
    "source_updated_at",
    "source_version",
  ]);
  if (!snapshot) {
    throw new ProviderError("off_replace_resolver_invalid", "Historical OFF snapshot is invalid.", 500);
  }
  const gtin = normalizeGtin14(snapshot.provider_food_id);
  const referenceUnit = snapshot.reference_unit;
  const expectedBasis = referenceUnit === "ml" ? "per_100_ml" : "per_100_g";
  const provenance = snapshot.provenance as Record<string, unknown> | null;
  if (
    !gtin || gtin !== snapshot.provider_food_id || snapshot.normalized_gtin14 !== gtin ||
    normalizeGtin14(snapshot.barcode_original) !== gtin || snapshot.provider !== OFF_PROVIDER_CODE ||
    snapshot.provider_data_type !== OFF_DATA_TYPE || snapshot.mapping_version !== OFF_MAPPING_VERSION ||
    snapshot.candidate_id !== await createOffCandidateId(gtin) || snapshot.reference_amount !== 100 ||
    (referenceUnit !== "g" && referenceUnit !== "ml") || !safeCachedText(snapshot.food_name, 240) ||
    !safeCachedText(snapshot.brand, 160) || !/^[0-9a-f]{64}$/u.test(String(snapshot.source_checksum)) ||
    !safeCachedText(snapshot.source_version, 120) ||
    typeof snapshot.retrieved_at !== "string" || !Number.isFinite(Date.parse(snapshot.retrieved_at)) ||
    !safeCachedNumber(snapshot.energy_kcal_per_100, 0, 900) ||
    !safeCachedNumber(snapshot.protein_grams_per_100, 0, 100) ||
    !safeCachedNumber(snapshot.carbohydrate_grams_per_100, 0, 100) ||
    !safeCachedNumber(snapshot.fat_grams_per_100, 0, 100) ||
    !(snapshot.fiber_grams_per_100 === null || safeCachedNumber(snapshot.fiber_grams_per_100, 0, 100)) ||
    !provenance || provenance.provider !== OFF_PROVIDER_CODE ||
    provenance.provider_food_id !== gtin || provenance.candidate_id !== snapshot.candidate_id ||
    provenance.mapping_version !== OFF_MAPPING_VERSION || provenance.reference_basis !== expectedBasis ||
    provenance.source_checksum !== snapshot.source_checksum || provenance.source_revision !== snapshot.source_version
  ) {
    throw new ProviderError("off_replace_resolver_invalid", "Historical OFF snapshot is invalid.", 500);
  }
  return snapshot as unknown as OffSnapshotCandidate;
}

function requireOffUnit(referenceUnit: "g" | "ml", consumedUnit: "g" | "ml"): void {
  if (referenceUnit !== consumedUnit) {
    throw new ProviderError(
      "off_unit_mismatch",
      referenceUnit === "ml" ? "This product must be logged in millilitres." : "This product must be logged in grams.",
      400,
    );
  }
}

async function handleOffLog(
  input: OffLogInput,
  userId: string,
  dependencies: NutritionProviderDependencies,
  now: Date,
): Promise<{ cache: "hit"; result: Record<string, unknown> }> {
  const resolved = await resolveOffTokenCandidate(input.candidateToken, dependencies, now);
  requireOffUnit(resolved.candidate.reference_unit, input.consumedUnit);
  const result = await dependencies.store.logTransientOffFoodItem({
    userId,
    input,
    candidate: offSnapshot(resolved.candidate),
  });
  return { cache: "hit", result };
}

async function resolveHistoricalOffSnapshot(
  input: OffReplaceInput,
  userId: string,
  dependencies: NutritionProviderDependencies,
): Promise<OffSnapshotCandidate> {
  try {
    return await validHistoricalOffSnapshot(
      await dependencies.store.resolveTransientOffFoodLogItem(userId, input.originalItemId),
    );
  } catch (error) {
    if (!(error instanceof ActiveProviderItemUnavailableError)) throw error;
    try {
      return await validHistoricalOffSnapshot(
        await dependencies.store.resolveTransientOffFoodLogItem(userId, input.replacementItemId),
      );
    } catch (fallbackError) {
      if (!(fallbackError instanceof ActiveProviderItemUnavailableError)) throw fallbackError;
      throw new ProviderError(
        "off_replace_forbidden",
        "OFF food logging is not allowed for this request.",
        403,
      );
    }
  }
}

async function handleOffReplace(
  input: OffReplaceInput,
  userId: string,
  dependencies: NutritionProviderDependencies,
  now: Date,
): Promise<{ cache: "hit" | "not_checked"; result: Record<string, unknown> }> {
  let candidate: OffSnapshotCandidate;
  let cache: "hit" | "not_checked" = "not_checked";
  if (input.candidateToken) {
    const resolved = await resolveOffTokenCandidate(input.candidateToken, dependencies, now);
    candidate = offSnapshot(resolved.candidate);
    cache = "hit";
  } else {
    candidate = await resolveHistoricalOffSnapshot(input, userId, dependencies);
  }
  requireOffUnit(candidate.reference_unit, input.consumedUnit);
  const result = await dependencies.store.replaceTransientOffFoodItem({ userId, input, candidate });
  return { cache, result };
}

function providerSnapshot(candidate: SafeCandidate): ProviderSnapshotCandidate {
  const sourceUpdatedAt = candidate.provenance.source_version &&
      Number.isFinite(Date.parse(candidate.provenance.source_version))
    ? new Date(candidate.provenance.source_version).toISOString()
    : null;
  return {
    provider: PROVIDER_CODE,
    provider_food_id: candidate.provider_food_id,
    candidate_id: candidate.candidate_id,
    mapping_version: MAPPING_VERSION,
    provider_data_type: candidate.data_type,
    food_name: candidate.name,
    brand: candidate.brand,
    reference_amount: 100,
    reference_unit: "g",
    energy_kcal_per_100g: candidate.kcal,
    protein_grams_per_100g: candidate.protein,
    carbohydrate_grams_per_100g: candidate.carbohydrates,
    fat_grams_per_100g: candidate.fat,
    fiber_grams_per_100g: candidate.fiber,
    source_version: candidate.provenance.source_version,
    retrieved_at: candidate.provenance.retrieved_at,
    source_updated_at: sourceUpdatedAt,
    provenance: {
      provider: PROVIDER_CODE,
      provider_food_id: candidate.provider_food_id,
      candidate_id: candidate.candidate_id,
      mapping_version: MAPPING_VERSION,
      provider_data_type: candidate.data_type,
      retrieved_at: candidate.provenance.retrieved_at,
      source_version: candidate.provenance.source_version,
      source_updated_at: sourceUpdatedAt,
      reference_basis: "per_100_g",
      derivation: candidate.derivation,
      attribution: candidate.attribution,
    },
  };
}

async function historicalCandidateToken(
  value: unknown,
  hmacKey: string,
  now: Date,
): Promise<string> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new ProviderError(
      "provider_replace_resolver_invalid",
      "Historical provider identity could not be validated.",
      500,
    );
  }
  const identity = value as HistoricalProviderIdentity;
  const expectedKeys = [
    "candidate_id",
    "mapping_version",
    "provider",
    "provider_data_type",
    "provider_food_id",
  ];
  if (
    Object.keys(identity).sort().join("|") !== expectedKeys.join("|") ||
    identity.provider !== PROVIDER_CODE ||
    identity.mapping_version !== MAPPING_VERSION ||
    !PROVIDER_FOOD_ID_PATTERN.test(identity.provider_food_id) ||
    !UUID_PATTERN.test(identity.candidate_id) ||
    identity.candidate_id.charAt(14).toLowerCase() !== "5" ||
    !ACCEPTED_DATA_TYPES.includes(identity.provider_data_type)
  ) {
    throw new ProviderError(
      "provider_replace_resolver_invalid",
      "Historical provider identity could not be validated.",
      500,
    );
  }
  if (identity.candidate_id !== await createCandidateId(identity.provider_food_id)) {
    throw new ProviderError(
      "provider_replace_resolver_mismatch",
      "Historical provider identity does not match.",
      409,
    );
  }
  return await signCandidateToken(
    hmacKey,
    identity.provider_food_id,
    identity.provider_data_type,
    now,
  );
}

async function handleLog(
  input: ProviderLogInput,
  userId: string,
  dependencies: NutritionProviderDependencies,
  now: Date,
): Promise<{ cache: "hit" | "miss"; result: Record<string, unknown> }> {
  const lookup = await handleLookup(
    { candidateToken: input.candidateToken, requestId: input.requestId },
    userId,
    dependencies,
    now,
  );
  const result = await dependencies.store.logProviderFoodItem({
    userId,
    input,
    candidate: providerSnapshot(lookup.result),
  });
  return { cache: lookup.cache, result };
}

async function handleReplace(
  input: ProviderReplaceInput,
  userId: string,
  dependencies: NutritionProviderDependencies,
  now: Date,
): Promise<{ cache: "hit" | "miss"; result: Record<string, unknown> }> {
  let historicalIdentity: HistoricalProviderIdentity | null = null;
  if (input.candidateToken === null) {
    try {
      historicalIdentity = await dependencies.store.resolveProviderFoodLogItem(
        userId,
        input.originalItemId,
      );
    } catch (error) {
      if (!(error instanceof ActiveProviderItemUnavailableError)) throw error;
      try {
        historicalIdentity = await dependencies.store.resolveProviderFoodLogItem(
          userId,
          input.replacementItemId,
        );
      } catch (fallbackError) {
        if (!(fallbackError instanceof ActiveProviderItemUnavailableError)) throw fallbackError;
        throw new ProviderError(
          "provider_replace_forbidden",
          "Provider food logging is not allowed for this request.",
          403,
        );
      }
    }
  }
  const candidateToken = input.candidateToken ?? await historicalCandidateToken(
    historicalIdentity,
    dependencies.hmacKey,
    now,
  );
  const lookup = await handleLookup(
    { candidateToken, requestId: input.requestId },
    userId,
    dependencies,
    now,
  );
  const result = await dependencies.store.replaceProviderFoodLogItem({
    userId,
    input,
    candidate: providerSnapshot(lookup.result),
  });
  return { cache: lookup.cache, result };
}

function latencyBucket(startedAt: number): StructuredLogEvent["latency_bucket"] {
  const elapsed = performance.now() - startedAt;
  if (elapsed < 100) return "lt_100ms";
  if (elapsed < 500) return "lt_500ms";
  if (elapsed < 2_000) return "lt_2s";
  return "gte_2s";
}

export function createNutritionProviderHandler(dependencies: NutritionProviderDependencies) {
  if (!dependencies.hmacKey || dependencies.hmacKey.length < 32) {
    throw new Error("FMZ_PROVIDER_HMAC_KEY must contain at least 32 characters.");
  }
  return async (request: Request): Promise<Response> => {
    const startedAt = performance.now();
    const origin = request.headers.get("origin");
    let route: RouteName | "unknown" = "unknown";
    let requestId = "00000000-0000-4000-8000-000000000000";
    let cache: StructuredLogEvent["cache"] = "not_checked";
    let rejectionCategory: string | undefined;
    try {
      if (origin && !ALLOWED_STAGING_ORIGINS.has(origin)) {
        throw new ProviderError("origin_not_allowed", "Origin is not allowed.", 403);
      }
      if (request.method === "OPTIONS") {
        return new Response(null, { status: 204, headers: corsHeaders(origin) });
      }
      if (request.method !== "POST") {
        throw new ProviderError("method_not_allowed", "Only POST is supported.", 405);
      }
      route = routeFromUrl(new URL(request.url));
      const user = await dependencies.auth.verifyBearer(bearerToken(request));
      if (!user?.id || !UUID_PATTERN.test(user.id)) {
        throw new ProviderError("unauthorized", "Authentication is required.", 401);
      }
      const body = await readBody(request);
      const now = (dependencies.clock ?? { now: () => new Date() }).now();
      if (route === "search") {
        const input = parseSearch(body);
        requestId = input.requestId;
        const result = await handleSearch(input, user.id, dependencies, now);
        cache = result.cache;
        return jsonResponse(
          200,
          { ok: true, data: { ...result, provider: PROVIDER_CODE } },
          origin,
        );
      }
      if (route === "lookup") {
        const input = parseLookup(body);
        requestId = input.requestId;
        const result = await handleLookup(input, user.id, dependencies, now);
        cache = result.cache;
        return jsonResponse(
          200,
          { ok: true, data: { ...result, provider: PROVIDER_CODE } },
          origin,
        );
      }
      if (route === "log") {
        const input = parseLog(body);
        requestId = input.requestId;
        const result = await handleLog(input, user.id, dependencies, now);
        cache = result.cache;
        return jsonResponse(
          200,
          { ok: true, data: { ...result, provider: PROVIDER_CODE } },
          origin,
        );
      }
      if (route === "replace") {
        const input = parseReplace(body);
        requestId = input.requestId;
        const result = await handleReplace(input, user.id, dependencies, now);
        cache = result.cache;
        return jsonResponse(200, { ok: true, data: { ...result, provider: PROVIDER_CODE } }, origin);
      }
      if (route === "off-barcode") {
        const input = parseOffBarcode(body);
        requestId = input.requestId;
        const result = await handleOffBarcode(input, user.id, dependencies, now);
        cache = result.cache;
        return jsonResponse(
          200,
          { ok: true, data: { ...result, provider: OFF_PROVIDER_CODE } },
          origin,
        );
      }
      if (route === "off-log") {
        const input = parseOffLog(body);
        requestId = input.requestId;
        const result = await handleOffLog(input, user.id, dependencies, now);
        cache = result.cache;
        return jsonResponse(
          200,
          { ok: true, data: { ...result, provider: OFF_PROVIDER_CODE } },
          origin,
        );
      }
      const input = parseOffReplace(body);
      requestId = input.requestId;
      const result = await handleOffReplace(input, user.id, dependencies, now);
      cache = result.cache;
      return jsonResponse(
        200,
        { ok: true, data: { ...result, provider: OFF_PROVIDER_CODE } },
        origin,
      );
    } catch (error) {
      const safeError = error instanceof ProviderError
        ? error
        : new ProviderError("internal_error", "Request could not be completed.", 500);
      rejectionCategory = safeError.code;
      return errorResponse(safeError, origin);
    } finally {
      dependencies.logger.write({
        request_id: requestId,
        route,
        provider: route.startsWith("off-") ? OFF_PROVIDER_CODE : PROVIDER_CODE,
        cache,
        status_class: rejectionCategory ?? "success",
        latency_bucket: latencyBucket(startedAt),
        ...(rejectionCategory ? { rejection_category: rejectionCategory } : {}),
      });
    }
  };
}

export const PROVIDER_CACHE_IDENTITY_VERSION_SECONDS = CANDIDATE_TOKEN_TTL_SECONDS;
