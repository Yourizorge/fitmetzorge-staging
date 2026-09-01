import assert from "node:assert/strict";
import test from "node:test";
import {
  evaluateBudgetContract,
  validateActionProposal,
  validateCoachResponse,
  validateContextManifest,
  validateContractRequest,
  type TrustStatus,
} from "./contracts.ts";
import { createYouriAiHandler } from "./handler.ts";
import { DeterministicMockAdapter } from "./mock-adapter.ts";

const request = {
  request_id: "10000000-0000-4000-8000-000000000001",
  feature_code: "private_chat" as const,
  locale: "nl" as const,
  fixture: "success" as const,
};

const allowedTrust: TrustStatus = {
  structurally_eligible: true,
  operationally_allowed: true,
  deny_reason: "allowed",
  entitlement_code: "ai",
  consent_state: "granted",
  safety_status: "clear",
  feature_enabled: true,
  adapter_enabled: true,
  fair_use_status: "normal",
  automatic_billing: false,
  provider_cost_visible_to_member: false,
};

function invoke(body: unknown, trust = allowedTrust, mockTestEnabled = true, token = "test-token") {
  const handler = createYouriAiHandler({
    mockTestEnabled,
    async verifyBearer(value) { return value === "test-token" ? { id: "member" } : null; },
    async readTrustStatus() { return trust; },
  });
  return handler(new Request("https://example.test/youri-ai", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Origin: "https://yourizorge.github.io",
    },
    body: JSON.stringify(body),
  }));
}

test("strict request contract accepts only the locked shape", () => {
  assert.deepEqual(validateContractRequest(request), request);
  assert.throws(() => validateContractRequest({ ...request, model: "owner_supplied" }), /request_contract_invalid/);
  assert.throws(() => validateContractRequest({ ...request, request_id: "not-a-uuid" }), /request_id_invalid/);
});

test("mock adapter is deterministic and makes zero external calls", async () => {
  const adapter = new DeterministicMockAdapter();
  const first = await adapter.run(request);
  const second = await adapter.run(request);
  assert.deepEqual(first, second);
  assert.equal(adapter.externalCalls, 0);
  assert.equal(validateCoachResponse(first), true);
});

test("malformed and out-of-bounds mock outputs are rejected", async () => {
  const adapter = new DeterministicMockAdapter();
  assert.equal(validateCoachResponse(await adapter.run({ ...request, fixture: "malformed" })), false);
  assert.equal(validateCoachResponse(await adapter.run({ ...request, fixture: "action_out_of_bounds" })), false);
});

test("safety hard stop blocks automatic execution", async () => {
  const output = await new DeterministicMockAdapter().run({ ...request, fixture: "safety_hard_stop" });
  assert.equal(validateCoachResponse(output), true);
  const safety = (output as { safety: { status: string; automatic_execution_blocked: boolean } }).safety;
  assert.equal(safety.status, "hard_stop");
  assert.equal(safety.automatic_execution_blocked, true);
});

test("action allowlist applies volume, calories and compatible alternatives", () => {
  assert.equal(validateActionProposal({ action_code: "training_volume_adjustment", payload: { delta_percent: 20, explanation: "bounded", reversible: true } }), true);
  assert.equal(validateActionProposal({ action_code: "training_volume_adjustment", payload: { delta_percent: 21, explanation: "too large", reversible: true } }), false);
  assert.equal(validateActionProposal({ action_code: "training_volume_adjustment", payload: { delta_percent: -40, reason_code: "deload", explanation: "fatigue", reversible: true } }), true);
  assert.equal(validateActionProposal({ action_code: "calorie_target_adjustment", payload: { delta_percent: 10, delta_kcal: 300, has_sufficient_new_authoritative_data: true, explanation: "bounded", reversible: true } }), true);
  assert.equal(validateActionProposal({ action_code: "calorie_target_adjustment", payload: { delta_percent: 10, delta_kcal: 301, has_sufficient_new_authoritative_data: true, explanation: "too large", reversible: true } }), false);
  assert.equal(validateActionProposal({ action_code: "replace_exercise", payload: { compatible_alternative: false, explanation: "wrong", reversible: true } }), false);
  assert.equal(validateActionProposal({ action_code: "medication_change", payload: { explanation: "forbidden", reversible: true } }), false);
});

test("budget uses warning, included, grace and hard ceilings without billing", () => {
  assert.deepEqual(evaluateBudgetContract(0, 0, 2_399_999, "luna").fair_use_status, "normal");
  assert.deepEqual(evaluateBudgetContract(2_400_000, 0, 0, "luna").fair_use_status, "warning");
  assert.equal(evaluateBudgetContract(3_000_000, 0, 1, "terra").allowed, false);
  assert.equal(evaluateBudgetContract(3_000_000, 0, 1, "luna").allowed, true);
  assert.equal(evaluateBudgetContract(4_000_000, 0, 1, "luna").allowed, false);
  assert.equal(evaluateBudgetContract(4_000_000, 0, 0, "luna").automatic_billing, false);
});

test("context manifest validator rejects authority and shape drift", () => {
  const manifest = {
    manifest_version: "phase6a.context-manifest.v1",
    context_hash: "a".repeat(64),
    sources: { training: { authority: "training_plans", copied: false } },
    unavailable_sources: ["health_sync"],
    source_cutoff_at: "2026-09-01T12:00:00.000Z",
  };
  assert.equal(validateContextManifest(manifest), true);
  assert.equal(validateContextManifest({ ...manifest, provider_model: "browser-choice" }), false);
});

test("no consent, withdrawn consent, Free, Pro and expired entitlement are denied", async () => {
  for (const denyReason of [
    "ai_consent_required",
    "ai_consent_required",
    "ai_entitlement_required",
    "ai_entitlement_required",
    "ai_entitlement_required",
  ]) {
    const response = await invoke(request, { ...allowedTrust, structurally_eligible: false, operationally_allowed: false, deny_reason: denyReason });
    assert.equal(response.status, 422);
  }
});

test("feature-off and explicit mock-off gates prevent mock output", async () => {
  const disabled = await invoke(request, { ...allowedTrust, operationally_allowed: false, feature_enabled: false, deny_reason: "ai_feature_disabled" });
  assert.equal(disabled.status, 403);
  const mockDisabled = await invoke(request, allowedTrust, false);
  assert.equal(mockDisabled.status, 403);
  assert.deepEqual(await mockDisabled.json(), { error: "mock_disabled" });
});

test("explicit local mock flag returns validated fixture with zero calls and cost", async () => {
  const response = await invoke(request);
  assert.equal(response.status, 200);
  const payload = await response.json() as Record<string, unknown>;
  assert.equal(payload.external_ai_calls, 0);
  assert.equal(payload.external_ai_cost_eur, 0);
  assert.equal(validateCoachResponse(payload.output), true);
});

test("unauthorized and unsupported-origin requests are denied", async () => {
  const unauthorized = await invoke(request, allowedTrust, true, "wrong-token");
  assert.equal(unauthorized.status, 401);
  const handler = createYouriAiHandler({
    mockTestEnabled: true,
    async verifyBearer() { return { id: "member" }; },
    async readTrustStatus() { return allowedTrust; },
  });
  const forbidden = await handler(new Request("https://example.test/youri-ai", {
    method: "POST",
    headers: { Authorization: "Bearer ok", Origin: "https://evil.example" },
    body: JSON.stringify(request),
  }));
  assert.equal(forbidden.status, 403);
  assert.equal(forbidden.headers.get("Access-Control-Allow-Origin"), null);
});
