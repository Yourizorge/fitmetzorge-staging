import type { AcceptedDataType } from "./constants.ts";

export type Locale = "nl" | "en" | "de";
export type ProviderCode = "usda_fdc" | "open_food_facts";
export type RouteName =
  | "search"
  | "lookup"
  | "log"
  | "replace"
  | "off-barcode"
  | "off-log"
  | "off-replace";
export type CacheStatus = "positive" | "empty" | "quarantined";
export type QualityState = "candidate" | "validated" | "quarantined" | "rejected";

export interface AuthenticatedUser {
  id: string;
}

export interface AuthGateway {
  verifyBearer(token: string): Promise<AuthenticatedUser | null>;
}

export interface SearchInput {
  query: string;
  normalizedQuery: string;
  locale: Locale;
  countryCode: string;
  pageNumber: number;
  pageSize: number;
  requestId: string;
}

export interface LookupInput {
  candidateToken: string;
  requestId: string;
}

export interface OffBarcodeInput {
  barcode: string;
  normalizedGtin14: string;
  requestId: string;
}

export interface ProviderLogInput {
  candidateToken: string;
  itemId: string;
  requestId: string;
  logDate: string;
  timezoneName: string;
  timezoneOffsetMinutes: number;
  mealMoment: "breakfast" | "lunch" | "dinner" | "snacks";
  consumedQuantity: number;
  consumedUnit: "g";
  notes: string | null;
  consumedAt: string | null;
}

export interface ProviderReplaceInput {
  candidateToken: string | null;
  originalItemId: string;
  replacementItemId: string;
  requestId: string;
  expectedOriginalUpdatedAt: string;
  mealMoment: "breakfast" | "lunch" | "dinner" | "snacks";
  consumedQuantity: number;
  consumedUnit: "g";
  notes: string | null;
}

export interface OffLogInput {
  candidateToken: string;
  itemId: string;
  requestId: string;
  logDate: string;
  timezoneName: string;
  timezoneOffsetMinutes: number;
  mealMoment: "breakfast" | "lunch" | "dinner" | "snacks";
  consumedQuantity: number;
  consumedUnit: "g" | "ml";
  notes: string | null;
  consumedAt: string | null;
}

export interface OffReplaceInput {
  candidateToken: string | null;
  originalItemId: string;
  replacementItemId: string;
  requestId: string;
  expectedOriginalUpdatedAt: string;
  mealMoment: "breakfast" | "lunch" | "dinner" | "snacks";
  consumedQuantity: number;
  consumedUnit: "g" | "ml";
  notes: string | null;
}

export interface HistoricalProviderIdentity {
  provider: "usda_fdc";
  provider_food_id: string;
  candidate_id: string;
  mapping_version: string;
  provider_data_type: AcceptedDataType;
}

export interface CandidateTokenPayload {
  version: 1;
  provider: "usda_fdc";
  provider_food_id: string;
  data_type: AcceptedDataType;
  mapping_version: string;
  candidate_id: string;
  expires_at: number;
}

export interface OffCandidateTokenPayload {
  version: 2;
  provider: "open_food_facts";
  provider_food_id: string;
  data_type: "off_branded";
  mapping_version: string;
  candidate_id: string;
  reference_basis: "per_100_g" | "per_100_ml";
  payload_checksum: string;
  expires_at: number;
}

export interface SafePortion {
  label: string;
  amount: number;
  unit: "serving";
  equivalent_amount: number;
  equivalent_unit: "g";
}

export interface NutrientDerivation {
  energy: "2048_kcal" | "2047_kcal" | "1008_kcal" | "1062_kj_converted";
  reference_basis: "per_100_g";
}

export interface SafeCandidate {
  candidate_id: string;
  provider: "usda_fdc";
  provider_label: string;
  provider_food_id: string;
  name: string;
  brand: string | null;
  data_type: AcceptedDataType;
  mapping_version: string;
  reference_amount: 100;
  reference_unit: "g";
  kcal: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number | null;
  portions: SafePortion[];
  derivation: NutrientDerivation;
  quality: "candidate";
  attribution: {
    label: string;
    license: "CC0 1.0";
    url: string;
  };
  provenance: {
    provider: "usda_fdc";
    provider_food_id: string;
    data_type: AcceptedDataType;
    mapping_version: string;
    retrieved_at: string;
    source_version: string | null;
  };
}

export interface MemberSafeCandidate extends SafeCandidate {
  candidate_token: string;
}

export interface OffSafeCandidate {
  candidate_id: string;
  provider: "open_food_facts";
  provider_label: string;
  provider_food_id: string;
  barcode: string;
  barcode_original: string;
  name: string;
  brand: string;
  data_type: "off_branded";
  mapping_version: string;
  reference_amount: 100;
  reference_unit: "g" | "ml";
  nutrition_basis: "per_100_g" | "per_100_ml";
  kcal: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number | null;
  quality: "candidate";
  attribution: {
    label: string;
    license: "ODbL-1.0";
    url: string;
  };
  provenance: {
    provider: "open_food_facts";
    provider_food_id: string;
    candidate_id: string;
    mapping_version: string;
    reference_basis: "per_100_g" | "per_100_ml";
    source_revision: string;
    source_checksum: string;
    retrieved_at: string;
    source_updated_at: string | null;
    original_barcode: string;
    countries_tags: string[];
    license_code: "ODbL-1.0";
    license_url: string;
    attribution: { label: string; url: string };
    derivation: Record<string, unknown>;
  };
}

export interface MemberOffSafeCandidate extends OffSafeCandidate {
  candidate_token: string;
}

export interface OffSnapshotCandidate {
  provider: "open_food_facts";
  provider_food_id: string;
  candidate_id: string;
  mapping_version: string;
  provider_data_type: "off_branded";
  food_name: string;
  brand: string;
  barcode_original: string;
  normalized_gtin14: string;
  reference_amount: 100;
  reference_unit: "g" | "ml";
  energy_kcal_per_100: number;
  protein_grams_per_100: number;
  carbohydrate_grams_per_100: number;
  fat_grams_per_100: number;
  fiber_grams_per_100: number | null;
  source_version: string;
  source_checksum: string;
  retrieved_at: string;
  source_updated_at: string | null;
  provenance: Record<string, unknown>;
}

export interface ProviderSnapshotCandidate {
  provider: "usda_fdc";
  provider_food_id: string;
  candidate_id: string;
  mapping_version: string;
  provider_data_type: AcceptedDataType;
  food_name: string;
  brand: string | null;
  reference_amount: 100;
  reference_unit: "g";
  energy_kcal_per_100g: number;
  protein_grams_per_100g: number;
  carbohydrate_grams_per_100g: number;
  fat_grams_per_100g: number;
  fiber_grams_per_100g: number | null;
  source_version: string | null;
  retrieved_at: string;
  source_updated_at: string | null;
  provenance: Record<string, unknown>;
}

export interface ProviderLogMutation {
  userId: string;
  input: ProviderLogInput;
  candidate: ProviderSnapshotCandidate;
}

export interface ProviderReplaceMutation {
  userId: string;
  input: ProviderReplaceInput;
  candidate: ProviderSnapshotCandidate;
}

export interface OffLogMutation {
  userId: string;
  input: OffLogInput;
  candidate: OffSnapshotCandidate;
}

export interface OffReplaceMutation {
  userId: string;
  input: OffReplaceInput;
  candidate: OffSnapshotCandidate;
}

export interface QueryCacheKey {
  providerCode: "usda_fdc";
  queryHmac: string;
  locale: Locale;
  countryCode: string;
  pageNumber: number;
  pageSize: number;
  filterKey: string;
  mappingVersion: string;
}

export interface QueryCacheRow {
  provider_code: "usda_fdc";
  query_hmac: string;
  locale: Locale;
  country_code: string;
  page_number: number;
  page_size: number;
  data_type_filter: string[];
  filter_key: string;
  filter_identity: Record<string, unknown>;
  mapping_version: string;
  result_payload: SafeCandidate[];
  payload_checksum: string;
  result_count: number;
  cache_status: CacheStatus;
  source_version: string | null;
  fetched_at: string;
  expires_at: string;
}

export interface FoodCacheKey {
  providerCode: ProviderCode;
  providerFoodId: string;
  mappingVersion: string;
}

export interface FoodCacheRow {
  provider_code: ProviderCode;
  provider_food_id: string;
  provider_data_type: AcceptedDataType | "off_branded";
  mapping_version: string;
  candidate_id: string;
  normalized_payload: SafeCandidate | OffSafeCandidate | Record<string, unknown>;
  payload_checksum: string;
  quality_state: QualityState;
  rejection_code: string | null;
  source_version: string | null;
  source_updated_at: string | null;
  provenance: Record<string, unknown>;
  metadata: Record<string, unknown>;
  fetched_at: string;
  expires_at: string;
}

export interface RateLimitResult {
  allowed: boolean;
  replayed: boolean;
  retry_after_seconds?: number;
  retry_at?: string;
}

export interface ProbeResult {
  probe_allowed: boolean;
  state?: {
    circuit_state?: "closed" | "open" | "half_open";
    next_probe_at?: string | null;
  };
}

export type RuntimeEvent = "success" | "failure" | "rate_limited" | "begin_probe";

export interface RuntimeTransitionInput {
  event: RuntimeEvent;
  retryAfterSeconds?: number;
  errorClass?: string;
  upstreamLimit?: number;
  upstreamRemaining?: number;
  upstreamResetAt?: string;
  metadata?: Record<string, unknown>;
}

export interface OperationalStore {
  getQueryCache(key: QueryCacheKey): Promise<QueryCacheRow | null>;
  putQueryCache(row: QueryCacheRow): Promise<void>;
  getFoodCache(key: FoodCacheKey): Promise<FoodCacheRow | null>;
  putFoodCache(row: FoodCacheRow): Promise<void>;
  consumeRateLimit(
    providerCode: ProviderCode,
    userSubjectHmac: string,
    requestId: string,
  ): Promise<RateLimitResult>;
  beginProbe(providerCode: ProviderCode): Promise<ProbeResult>;
  transitionRuntime(providerCode: ProviderCode, input: RuntimeTransitionInput): Promise<void>;
  resolveLocalBarcode(userId: string, normalizedGtin14: string): Promise<Record<string, unknown> | null>;
  resolveProviderFoodLogItem(
    userId: string,
    originalItemId: string,
  ): Promise<HistoricalProviderIdentity>;
  logProviderFoodItem(input: ProviderLogMutation): Promise<Record<string, unknown>>;
  replaceProviderFoodLogItem(
    input: ProviderReplaceMutation,
  ): Promise<Record<string, unknown>>;
  resolveTransientOffFoodLogItem(
    userId: string,
    originalItemId: string,
  ): Promise<OffSnapshotCandidate>;
  logTransientOffFoodItem(input: OffLogMutation): Promise<Record<string, unknown>>;
  replaceTransientOffFoodItem(input: OffReplaceMutation): Promise<Record<string, unknown>>;
}

export interface UpstreamResponse {
  status: number;
  headers: Headers;
  bodyText: string;
}

export interface UsdaSearchRequest {
  query: string;
  pageNumber: number;
  pageSize: number;
  dataTypes: readonly AcceptedDataType[];
  signal: AbortSignal;
}

export interface UsdaLookupRequest {
  providerFoodId: string;
  signal: AbortSignal;
}

export interface UsdaClient {
  search(input: UsdaSearchRequest): Promise<UpstreamResponse>;
  lookup(input: UsdaLookupRequest): Promise<UpstreamResponse>;
}

export interface OffBarcodeRequest {
  normalizedGtin14: string;
  signal: AbortSignal;
}

export interface OffClient {
  lookupBarcode(input: OffBarcodeRequest): Promise<UpstreamResponse>;
}

export interface StructuredLogEvent {
  request_id: string;
  route: RouteName | "unknown";
  provider: ProviderCode;
  cache: "hit" | "miss" | "not_checked";
  status_class: string;
  latency_bucket: "lt_100ms" | "lt_500ms" | "lt_2s" | "gte_2s";
  rejection_category?: string;
}

export interface ProviderLogger {
  write(event: StructuredLogEvent): void;
}

export interface HandlerClock {
  now(): Date;
}

export interface NutritionProviderDependencies {
  auth: AuthGateway;
  store: OperationalStore;
  usda: UsdaClient;
  off: OffClient;
  logger: ProviderLogger;
  hmacKey: string;
  clock?: HandlerClock;
  timeoutMs?: number;
}

export class ActiveProviderItemUnavailableError extends Error {
  constructor() {
    super("Active provider food log item is unavailable.");
    this.name = "ActiveProviderItemUnavailableError";
  }
}

export class ProviderError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: Record<string, unknown>;

  constructor(
    code: string,
    message: string,
    status: number,
    details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ProviderError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}
