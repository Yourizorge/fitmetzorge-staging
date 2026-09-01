export const PHASE6A_RESPONSE_SCHEMA_VERSION = "phase6a.response.v1" as const;
export const PHASE6A_CONTEXT_SCHEMA_VERSION = "phase6a.context-manifest.v1" as const;

export const AI_FEATURE_CODES = [
  "private_chat",
  "daily_analysis",
  "weekly_checkin",
  "post_workout",
] as const;

export const AI_ACTION_CODES = [
  "training_volume_adjustment",
  "add_rest_day",
  "reschedule_training",
  "replace_exercise",
  "calorie_target_adjustment",
] as const;

export const MOCK_FIXTURES = [
  "success",
  "failure",
  "timeout",
  "malformed",
  "safety_hard_stop",
  "action_out_of_bounds",
] as const;

export type AiFeatureCode = (typeof AI_FEATURE_CODES)[number];
export type AiActionCode = (typeof AI_ACTION_CODES)[number];
export type MockFixture = (typeof MOCK_FIXTURES)[number];

export interface ContractRequest {
  request_id: string;
  feature_code: AiFeatureCode;
  locale: "nl" | "en" | "de";
  fixture: MockFixture;
}

export interface TrustStatus {
  structurally_eligible: boolean;
  operationally_allowed: boolean;
  deny_reason: string;
  entitlement_code: "ai" | "personal_coaching" | null;
  consent_state: "granted" | "withdrawn" | "missing";
  safety_status: "clear" | "hard_stop" | "review_required" | "resolved";
  feature_enabled: boolean;
  adapter_enabled: boolean;
  fair_use_status: "normal" | "warning" | "grace" | "blocked";
  automatic_billing: false;
  provider_cost_visible_to_member: false;
}

export interface ActionProposal {
  action_code: AiActionCode;
  payload: Record<string, unknown>;
}

export interface CoachResponse {
  schema_version: typeof PHASE6A_RESPONSE_SCHEMA_VERSION;
  feature_code: AiFeatureCode;
  summary: string;
  observations: string[];
  uncertainties: string[];
  recommendations: string[];
  actions: ActionProposal[];
  safety: {
    status: "clear" | "hard_stop" | "review_required";
    category: "none" | "serious_health" | "unclear_health" | "injury" | "eating_disorder" | "other";
    message_key: string;
    automatic_execution_blocked: boolean;
  };
}

export interface ProviderNeutralAdapter {
  readonly adapterCode: string;
  readonly externalCalls: 0;
  run(request: ContractRequest): Promise<unknown>;
}

export interface ContextManifest {
  manifest_version: typeof PHASE6A_CONTEXT_SCHEMA_VERSION;
  context_hash: string;
  sources: Record<string, unknown>;
  unavailable_sources: string[];
  source_cutoff_at: string;
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function boundedStrings(value: unknown, maxItems: number, maxLength = 1000): value is string[] {
  return Array.isArray(value) && value.length <= maxItems && value.every((item) =>
    typeof item === "string" && item.length >= 1 && item.length <= maxLength
  );
}

export function validateContractRequest(value: unknown): ContractRequest {
  if (!isPlainObject(value) || !hasExactKeys(value, ["request_id", "feature_code", "locale", "fixture"])) {
    throw new Error("request_contract_invalid");
  }
  if (typeof value.request_id !== "string" || !UUID_PATTERN.test(value.request_id)) {
    throw new Error("request_id_invalid");
  }
  if (!AI_FEATURE_CODES.includes(value.feature_code as AiFeatureCode)) {
    throw new Error("feature_invalid");
  }
  if (!(["nl", "en", "de"] as unknown[]).includes(value.locale)) {
    throw new Error("locale_invalid");
  }
  if (!MOCK_FIXTURES.includes(value.fixture as MockFixture)) {
    throw new Error("fixture_invalid");
  }
  return value as unknown as ContractRequest;
}

export function validateActionProposal(action: unknown): action is ActionProposal {
  if (!isPlainObject(action) || !hasExactKeys(action, ["action_code", "payload"])) return false;
  if (!AI_ACTION_CODES.includes(action.action_code as AiActionCode) || !isPlainObject(action.payload)) return false;
  const payload = action.payload;
  if (typeof payload.explanation !== "string" || !payload.explanation.trim() || payload.reversible !== true) return false;

  if (action.action_code === "training_volume_adjustment") {
    const delta = Number(payload.delta_percent);
    if (!Number.isFinite(delta) || delta > 20 || delta < -100) return false;
    if (delta < -20 && !["fatigue", "deload"].includes(String(payload.reason_code))) return false;
  } else if (action.action_code === "calorie_target_adjustment") {
    const percent = Math.abs(Number(payload.delta_percent));
    const kcal = Math.abs(Number(payload.delta_kcal));
    if (!Number.isFinite(percent) || !Number.isFinite(kcal) || percent > 10 || kcal > 300) return false;
    if (payload.has_sufficient_new_authoritative_data !== true) return false;
  } else if (action.action_code === "replace_exercise") {
    if (payload.compatible_alternative !== true) return false;
  }
  return true;
}

export function validateCoachResponse(value: unknown): value is CoachResponse {
  if (!isPlainObject(value) || !hasExactKeys(value, [
    "schema_version",
    "feature_code",
    "summary",
    "observations",
    "uncertainties",
    "recommendations",
    "actions",
    "safety",
  ])) return false;
  if (value.schema_version !== PHASE6A_RESPONSE_SCHEMA_VERSION) return false;
  if (!AI_FEATURE_CODES.includes(value.feature_code as AiFeatureCode)) return false;
  if (typeof value.summary !== "string" || value.summary.length < 1 || value.summary.length > 2000) return false;
  if (!boundedStrings(value.observations, 12) || !boundedStrings(value.uncertainties, 12) || !boundedStrings(value.recommendations, 12)) return false;
  if (!Array.isArray(value.actions) || value.actions.length > 8 || !value.actions.every(validateActionProposal)) return false;
  if (!isPlainObject(value.safety) || !hasExactKeys(value.safety, ["status", "category", "message_key", "automatic_execution_blocked"])) return false;
  if (!(["clear", "hard_stop", "review_required"] as unknown[]).includes(value.safety.status)) return false;
  if (!(["none", "serious_health", "unclear_health", "injury", "eating_disorder", "other"] as unknown[]).includes(value.safety.category)) return false;
  if (typeof value.safety.message_key !== "string" || value.safety.message_key.length > 120) return false;
  if (typeof value.safety.automatic_execution_blocked !== "boolean") return false;
  if (value.safety.status !== "clear" && value.safety.automatic_execution_blocked !== true) return false;
  return true;
}

export function validateContextManifest(value: unknown): value is ContextManifest {
  if (!isPlainObject(value) || !hasExactKeys(value, [
    "manifest_version",
    "context_hash",
    "sources",
    "unavailable_sources",
    "source_cutoff_at",
  ])) return false;
  return value.manifest_version === PHASE6A_CONTEXT_SCHEMA_VERSION
    && typeof value.context_hash === "string"
    && /^[0-9a-f]{64}$/.test(value.context_hash)
    && isPlainObject(value.sources)
    && boundedStrings(value.unavailable_sources, 24, 80)
    && typeof value.source_cutoff_at === "string"
    && !Number.isNaN(Date.parse(value.source_cutoff_at));
}

export function evaluateBudgetContract(
  consumedMicros: number,
  reservedMicros: number,
  requestedMicros: number,
  modelTier: "luna" | "terra",
) {
  if ([consumedMicros, reservedMicros, requestedMicros].some((value) => !Number.isInteger(value) || value < 0)) {
    throw new Error("budget_input_invalid");
  }
  const total = consumedMicros + reservedMicros + requestedMicros;
  const allowed = total <= 4_000_000 && !(modelTier === "terra" && total > 3_000_000);
  return {
    allowed,
    reason: total > 4_000_000
      ? "budget_hard_stop"
      : modelTier === "terra" && total > 3_000_000
      ? "terra_grace_forbidden"
      : "allowed",
    fair_use_status: total >= 4_000_000
      ? "blocked"
      : total > 3_000_000
      ? "grace"
      : total >= 2_400_000
      ? "warning"
      : "normal",
    automatic_billing: false as const,
  };
}

export function assertTrustGate(status: TrustStatus): void {
  if (!status.structurally_eligible || !status.operationally_allowed) {
    throw new Error(status.deny_reason || "ai_not_allowed");
  }
  if (status.automatic_billing !== false || status.provider_cost_visible_to_member !== false) {
    throw new Error("budget_contract_invalid");
  }
}
