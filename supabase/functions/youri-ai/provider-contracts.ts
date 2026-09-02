import { validateCoachResponse, type CoachResponse } from "./contracts.ts";

export const PHASE6B_SYNTHETIC_PAYLOAD_VERSION = "phase6b.synthetic-payload.v1" as const;
export const PHASE6B_MODEL_ROUTES = {
  luna: "gpt-5.6-luna",
  terra: "gpt-5.6-terra",
} as const;

export type Phase6bModelRoute = keyof typeof PHASE6B_MODEL_ROUTES;
export type Phase6bFixtureCode = "luna_connectivity_v1" | "terra_structured_v1";

export interface SyntheticProviderRequest {
  request_id: string;
  fixture_code: Phase6bFixtureCode;
}

export interface SyntheticProviderPayload {
  schema_version: typeof PHASE6B_SYNTHETIC_PAYLOAD_VERSION;
  feature_code: "daily_analysis";
  locale: "en";
  synthetic_subject_token: "synthetic_phase6b_alpha";
  snapshot: {
    goal_code: "general_fitness";
    training: { completed_sessions_7d: number };
    nutrition: { average_energy_kcal_7d: number };
    recovery: { average_sleep_hours_7d: number };
  };
  request_purpose: "connectivity_and_contract" | "complex_route_contract";
}

export const PHASE6B_PROVIDER_OUTPUT_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: [
    "schema_version", "feature_code", "summary", "observations", "uncertainties",
    "recommendations", "actions", "safety",
  ],
  properties: {
    schema_version: { type: "string", const: "phase6a.response.v1" },
    feature_code: { type: "string", const: "daily_analysis" },
    summary: { type: "string", minLength: 1, maxLength: 2000 },
    observations: { type: "array", maxItems: 12, items: { type: "string", minLength: 1, maxLength: 1000 } },
    uncertainties: { type: "array", maxItems: 12, items: { type: "string", minLength: 1, maxLength: 1000 } },
    recommendations: { type: "array", maxItems: 12, items: { type: "string", minLength: 1, maxLength: 1000 } },
    actions: { type: "array", maxItems: 0, items: { type: "object", additionalProperties: false, properties: {}, required: [] } },
    safety: {
      type: "object",
      additionalProperties: false,
      required: ["status", "category", "message_key", "automatic_execution_blocked"],
      properties: {
        status: { type: "string", enum: ["clear", "hard_stop", "review_required"] },
        category: { type: "string", enum: ["none", "serious_health", "unclear_health", "injury", "eating_disorder", "other"] },
        message_key: { type: "string", maxLength: 120 },
        automatic_execution_blocked: { type: "boolean" },
      },
    },
  },
} as const;

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const EXACT_PAYLOAD_KEYS = [
  "feature_code", "locale", "request_purpose", "schema_version", "snapshot", "synthetic_subject_token",
];
const EXACT_SNAPSHOT_KEYS = ["goal_code", "nutrition", "recovery", "training"];

function plain(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

export function validateSyntheticProviderRequest(value: unknown): SyntheticProviderRequest {
  if (!plain(value) || !exactKeys(value, ["fixture_code", "request_id"])) throw new Error("provider_test_request_invalid");
  if (typeof value.request_id !== "string" || !UUID_PATTERN.test(value.request_id)) throw new Error("provider_test_request_id_invalid");
  if (!(["luna_connectivity_v1", "terra_structured_v1"] as unknown[]).includes(value.fixture_code)) {
    throw new Error("provider_test_fixture_invalid");
  }
  return value as unknown as SyntheticProviderRequest;
}

export function fixtureRoute(fixture: Phase6bFixtureCode): Phase6bModelRoute {
  return fixture === "terra_structured_v1" ? "terra" : "luna";
}

export function buildSyntheticProviderPayload(fixture: Phase6bFixtureCode): SyntheticProviderPayload {
  const complex = fixture === "terra_structured_v1";
  return {
    schema_version: PHASE6B_SYNTHETIC_PAYLOAD_VERSION,
    feature_code: "daily_analysis",
    locale: "en",
    synthetic_subject_token: "synthetic_phase6b_alpha",
    snapshot: {
      goal_code: "general_fitness",
      training: { completed_sessions_7d: complex ? 4 : 3 },
      nutrition: { average_energy_kcal_7d: complex ? 2310 : 2260 },
      recovery: { average_sleep_hours_7d: complex ? 6.9 : 7.2 },
    },
    request_purpose: complex ? "complex_route_contract" : "connectivity_and_contract",
  };
}

export function assertSyntheticPayloadAllowlist(value: unknown): asserts value is SyntheticProviderPayload {
  if (!plain(value) || !exactKeys(value, EXACT_PAYLOAD_KEYS)) throw new Error("provider_payload_fields_invalid");
  if (value.schema_version !== PHASE6B_SYNTHETIC_PAYLOAD_VERSION
    || value.feature_code !== "daily_analysis"
    || value.locale !== "en"
    || value.synthetic_subject_token !== "synthetic_phase6b_alpha") {
    throw new Error("provider_payload_contract_invalid");
  }
  if (!plain(value.snapshot) || !exactKeys(value.snapshot, EXACT_SNAPSHOT_KEYS)) throw new Error("provider_payload_snapshot_invalid");
  const snapshot = value.snapshot;
  if (snapshot.goal_code !== "general_fitness"
    || !plain(snapshot.training) || !exactKeys(snapshot.training, ["completed_sessions_7d"])
    || !plain(snapshot.nutrition) || !exactKeys(snapshot.nutrition, ["average_energy_kcal_7d"])
    || !plain(snapshot.recovery) || !exactKeys(snapshot.recovery, ["average_sleep_hours_7d"])) {
    throw new Error("provider_payload_snapshot_invalid");
  }
  const serialized = JSON.stringify(value);
  if (/(email|full_name|name|address|phone|user_id|trainer_notes|private_chat|injury|medication)/i.test(serialized)) {
    throw new Error("provider_payload_sensitive_field_forbidden");
  }
}

export function assertProviderOutput(value: unknown): asserts value is CoachResponse {
  if (!validateCoachResponse(value) || (value as CoachResponse).feature_code !== "daily_analysis") {
    throw new Error("provider_structured_output_invalid");
  }
}
