import assert from "node:assert/strict";
import test from "node:test";
import {
  assertSyntheticPayloadAllowlist,
  buildSyntheticProviderPayload,
  fixtureRoute,
  PHASE6B_MODEL_ROUTES,
  validateSyntheticProviderRequest,
} from "./provider-contracts.ts";
import {
  buildOpenAiResponsesRequest,
  inspectOpenAiCredential,
  inspectOpenAiHeaderContract,
  OpenAiResponsesAdapter,
  probeOpenAiModelRead,
  SafeProviderError,
} from "./openai-adapter.ts";
import { createPhase6bHandler } from "./phase6b-handler.ts";

const validOutput = {
  schema_version: "phase6a.response.v1",
  feature_code: "daily_analysis",
  summary: "Synthetic contract response.",
  observations: ["Synthetic observation."],
  uncertainties: ["No real member context was used."],
  recommendations: ["Continue the synthetic fixture."],
  actions: [],
  safety: {
    status: "clear",
    category: "none",
    message_key: "safety.clear",
    automatic_execution_blocked: false,
  },
};

function providerResponse(output = validOutput, status = 200, model = "gpt-5.6-luna") {
  return new Response(JSON.stringify({
    id: "resp_synthetic",
    model,
    output_text: JSON.stringify(output),
    usage: {
      input_tokens: 120,
      input_tokens_details: { cached_tokens: 20 },
      output_tokens: 80,
      output_tokens_details: { reasoning_tokens: 30 },
    },
  }), { status, headers: { "Content-Type": "application/json" } });
}

test("fixture routes are exact and deterministic", () => {
  assert.equal(fixtureRoute("luna_connectivity_v1"), "luna");
  assert.equal(fixtureRoute("terra_structured_v1"), "terra");
  assert.equal(PHASE6B_MODEL_ROUTES.luna, "gpt-5.6-luna");
  assert.equal(PHASE6B_MODEL_ROUTES.terra, "gpt-5.6-terra");
});

test("synthetic request accepts only request id and locked fixture", () => {
  const value = validateSyntheticProviderRequest({
    request_id: "10000000-0000-4000-8000-000000000001",
    fixture_code: "luna_connectivity_v1",
  });
  assert.equal(value.fixture_code, "luna_connectivity_v1");
  assert.throws(() => validateSyntheticProviderRequest({ ...value, prompt: "forbidden" }), /provider_test_request_invalid/);
});

test("payload contains only synthetic minimized allowlisted fields", () => {
  const payload = buildSyntheticProviderPayload("terra_structured_v1");
  assert.doesNotThrow(() => assertSyntheticPayloadAllowlist(payload));
  assert.equal(payload.synthetic_subject_token, "synthetic_phase6b_alpha");
  assert.equal(JSON.stringify(payload).includes("user_id"), false);
  assert.equal(JSON.stringify(payload).includes("email"), false);
});

test("unexpected or sensitive payload fields fail closed", () => {
  const payload = buildSyntheticProviderPayload("luna_connectivity_v1") as unknown as Record<string, unknown>;
  payload.email = "synthetic@example.invalid";
  assert.throws(() => assertSyntheticPayloadAllowlist(payload), /provider_payload_fields_invalid/);
});

test("Responses request enforces store false and denies all tools", () => {
  const body = buildOpenAiResponsesRequest(
    "gpt-5.6-luna",
    "luna",
    buildSyntheticProviderPayload("luna_connectivity_v1"),
  );
  assert.equal(body.store, false);
  assert.equal(body.background, false);
  assert.deepEqual(body.tools, []);
  assert.equal(body.tool_choice, "none");
  assert.equal(body.text.format.type, "json_schema");
  assert.equal(body.text.format.strict, true);
  assert.equal("metadata" in body, false);
  assert.equal("previous_response_id" in body, false);
});

test("credential inspection trims once and exposes booleans only", () => {
  const inspected = inspectOpenAiCredential("  sk-proj-test_only_project_key_1234567890  \r\n");
  assert.equal(inspected.apiKey, "sk-proj-test_only_project_key_1234567890");
  assert.deepEqual(inspected.checks, {
    rawExists: true,
    trimmedNonEmpty: true,
    leadingOrTrailingWhitespacePresent: true,
    quoteCharactersPresent: false,
    newlineCharactersPresent: true,
    bearerPrefixPresent: false,
    projectKeyFormatCompatible: true,
    normalizationAppliedExactlyOnce: true,
  });
  assert.equal(JSON.stringify(inspected.checks).includes("sk-proj"), false);
});

test("OpenAI header contract is exactly one bearer and forwards no proxy headers", () => {
  assert.deepEqual(inspectOpenAiHeaderContract("sk-proj-test_only_project_key_1234567890"), {
    exactBearerHeader: true,
    exactlyOneBearerPrefix: true,
    authorizationHeaderCountOne: true,
    organizationHeaderPresent: false,
    projectHeaderPresent: false,
    proxyHeadersForwarded: false,
  });
});

test("model-read probe is GET-only, non-generative and proves authentication", async () => {
  let inspectedRequest: Request | null = null;
  const result = await probeOpenAiModelRead(
    "sk-proj-test_only_project_key_1234567890",
    async (input, init) => {
      inspectedRequest = new Request(input, init);
      return new Response(JSON.stringify({ id: "gpt-5.6-luna", object: "model" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    },
  );
  assert.equal(inspectedRequest?.method, "GET");
  assert.equal(inspectedRequest?.url, "https://api.openai.com/v1/models/gpt-5.6-luna");
  assert.equal(await inspectedRequest?.text(), "");
  assert.equal(result.keyAuthenticated, true);
  assert.equal(result.returnedModelMatches, true);
  assert.equal(result.generationPerformed, false);
  assert.equal(result.externalCostEurMicros, 0);
});

test("model-read probe preserves only safe upstream authentication fields", async () => {
  const key = "sk-proj-test_only_project_key_1234567890";
  const result = await probeOpenAiModelRead(key, async () => new Response(JSON.stringify({
    error: {
      message: `Incorrect API key provided: ${key}`,
      type: "invalid_request_error",
      code: "invalid_api_key",
    },
  }), { status: 401, headers: { "Content-Type": "application/json" } }));
  assert.deepEqual(result.upstream, {
    status: 401,
    type: "invalid_request_error",
    code: "invalid_api_key",
    classification: "invalid_or_revoked_api_key",
  });
  assert.equal(result.keyAuthenticated, false);
  assert.equal(JSON.stringify(result).includes(key), false);
  assert.equal(JSON.stringify(result).includes("Incorrect API key"), false);
});

test("model allowlist and route pairing fail closed", () => {
  const payload = buildSyntheticProviderPayload("luna_connectivity_v1");
  assert.throws(() => buildOpenAiResponsesRequest("gpt-5.6", "luna", payload), /provider_model_forbidden/);
  assert.throws(() => buildOpenAiResponsesRequest("gpt-5.6-terra", "luna", payload), /provider_route_conflict/);
});

test("adapter validates strict output and token accounting", async () => {
  const adapter = new OpenAiResponsesAdapter({ apiKey: "test-only", fetchImpl: async () => providerResponse() });
  const result = await adapter.run(
    "gpt-5.6-luna", "luna", buildSyntheticProviderPayload("luna_connectivity_v1"), 2, 512,
  );
  assert.deepEqual(result.usage, { inputTokens: 120, cachedInputTokens: 20, outputTokens: 80, reasoningTokens: 30 });
  assert.equal(result.attemptCount, 1);
  assert.equal(result.returnedModelId, "gpt-5.6-luna");
  assert.equal(result.providerResponseId, "resp_synthetic");
  assert.match(result.requestHash, /^[0-9a-f]{64}$/);
  assert.match(result.responseHash, /^[0-9a-f]{64}$/);
});

test("adapter rejects a returned model that differs from the locked route", async () => {
  const adapter = new OpenAiResponsesAdapter({
    apiKey: "test-only",
    fetchImpl: async () => providerResponse(validOutput, 200, "gpt-5.6-terra"),
  });
  await assert.rejects(
    adapter.run("gpt-5.6-luna", "luna", buildSyntheticProviderPayload("luna_connectivity_v1"), 1, 512),
    (error: unknown) => error instanceof SafeProviderError && error.message === "provider_returned_model_mismatch",
  );
});

test("adapter rejects malformed structured output", async () => {
  const adapter = new OpenAiResponsesAdapter({ apiKey: "test-only", fetchImpl: async () => providerResponse({ bad: true } as never) });
  await assert.rejects(
    adapter.run("gpt-5.6-luna", "luna", buildSyntheticProviderPayload("luna_connectivity_v1"), 1, 512),
    (error: unknown) => error instanceof SafeProviderError && error.message === "provider_structured_output_invalid",
  );
});

test("adapter rejects unknown keys on an otherwise valid structured output", async () => {
  const adapter = new OpenAiResponsesAdapter({
    apiKey: "test-only",
    fetchImpl: async () => providerResponse({ ...validOutput, unexpected: "forbidden" } as never),
  });
  await assert.rejects(
    adapter.run("gpt-5.6-luna", "luna", buildSyntheticProviderPayload("luna_connectivity_v1"), 1, 512),
    (error: unknown) => error instanceof SafeProviderError && error.message === "provider_structured_output_invalid",
  );
});

test("adapter retries one rate limit and remains bounded", async () => {
  let calls = 0;
  const adapter = new OpenAiResponsesAdapter({
    apiKey: "test-only",
    fetchImpl: async () => {
      calls += 1;
      return calls === 1 ? new Response("", { status: 429 }) : providerResponse(validOutput, 200, "gpt-5.6-terra");
    },
  });
  const result = await adapter.run(
    "gpt-5.6-terra", "terra", buildSyntheticProviderPayload("terra_structured_v1"), 2, 512,
  );
  assert.equal(calls, 2);
  assert.equal(result.attemptCount, 2);
});

test("post-retry output failure reports the real provider attempt count", async () => {
  let calls = 0;
  const adapter = new OpenAiResponsesAdapter({
    apiKey: "test-only",
    fetchImpl: async () => {
      calls += 1;
      return calls === 1
        ? new Response("", { status: 429 })
        : new Response(JSON.stringify({ model: "gpt-5.6-luna", usage: {} }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
    },
  });
  await assert.rejects(
    adapter.run("gpt-5.6-luna", "luna", buildSyntheticProviderPayload("luna_connectivity_v1"), 2, 512),
    (error: unknown) => error instanceof SafeProviderError
      && error.message === "provider_output_missing"
      && error.attemptCount === 2,
  );
});

test("adapter returns sanitized auth failure without response body", async () => {
  const adapter = new OpenAiResponsesAdapter({ apiKey: "test-only", fetchImpl: async () => new Response("sensitive", { status: 401 }) });
  await assert.rejects(
    adapter.run("gpt-5.6-luna", "luna", buildSyntheticProviderPayload("luna_connectivity_v1"), 1, 512),
    (error: unknown) => error instanceof SafeProviderError && error.message === "provider_authentication_failed" && error.costUnknown,
  );
});

test("adapter does not misclassify provider permission errors as authentication", async () => {
  const adapter = new OpenAiResponsesAdapter({
    apiKey: "test-only",
    fetchImpl: async () => new Response(JSON.stringify({
      error: { type: "insufficient_permissions", code: "model_not_allowed", message: "sensitive" },
    }), { status: 403, headers: { "Content-Type": "application/json" } }),
  });
  await assert.rejects(
    adapter.run("gpt-5.6-luna", "luna", buildSyntheticProviderPayload("luna_connectivity_v1"), 1, 512),
    (error: unknown) => error instanceof SafeProviderError
      && error.message === "provider_permission_denied"
      && error.upstream?.status === 403
      && error.upstream.type === "insufficient_permissions"
      && error.upstream.code === "model_not_allowed",
  );
});

function handlerDependencies(overrides: Record<string, unknown> = {}) {
  const calls: Array<{ name: string; input: Record<string, unknown> }> = [];
  return {
    calls,
    dependencies: {
      authorizeServer: async () => true,
      providerTestEnvironmentEnabled: true,
      authDiagnosticEnvironmentEnabled: false,
      openAiApiKey: "test-only",
      openAiCredentialChecks: inspectOpenAiCredential("test-only").checks,
      runAuthProbe: async () => {
        throw new Error("diagnostic_not_expected");
      },
      readStatus: async () => ({ execution_mode: "synthetic_only" }),
      begin: async (input: Record<string, unknown>) => {
        calls.push({ name: "begin", input });
        return {
          replay: false,
          run_id: "20000000-0000-4000-8000-000000000001",
          status: "reserved" as const,
          model_id: "gpt-5.6-luna",
          max_attempts: 2,
          max_output_tokens: 512,
        };
      },
      complete: async (input: Record<string, unknown>) => {
        calls.push({ name: "complete", input });
        return { actual_eur_micros: 500 };
      },
      fail: async (input: Record<string, unknown>) => {
        calls.push({ name: "fail", input });
        return { status: "failed" };
      },
      fetchImpl: async () => providerResponse(),
      ...overrides,
    },
  };
}

function syntheticRequest() {
  return new Request("https://example.test/youri-ai/phase6b/synthetic-test", {
    method: "POST",
    headers: { Authorization: "Bearer server-only", "Content-Type": "application/json" },
    body: JSON.stringify({ request_id: "10000000-0000-4000-8000-000000000001", fixture_code: "luna_connectivity_v1" }),
  });
}

test("ordinary caller cannot access synthetic provider route", async () => {
  const { dependencies } = handlerDependencies({ authorizeServer: async () => false });
  const response = await createPhase6bHandler(dependencies)(syntheticRequest());
  assert.equal(response.status, 401);
});

test("browser origin is rejected from server-only provider route", async () => {
  const { dependencies } = handlerDependencies();
  const request = syntheticRequest();
  request.headers.set("Origin", "https://yourizorge.github.io");
  const response = await createPhase6bHandler(dependencies)(request);
  assert.equal(response.status, 403);
});

test("auth diagnostic is server-only, separately gated and performs no accounting", async () => {
  const disabled = handlerDependencies();
  const request = new Request("https://example.test/youri-ai/phase6b/auth-diagnostic", {
    method: "GET",
    headers: { Authorization: "Bearer server-only" },
  });
  assert.equal((await createPhase6bHandler(disabled.dependencies)(request)).status, 503);
  assert.equal(disabled.calls.length, 0);

  const enabled = handlerDependencies({
    authDiagnosticEnvironmentEnabled: true,
    runAuthProbe: async () => ({
      upstream: { status: 401, type: "invalid_request_error", code: "invalid_api_key", classification: "invalid_or_revoked_api_key" },
      keyAuthenticated: false,
      returnedModelMatches: false,
      endpointHost: "api.openai.com",
      endpointPath: "/v1/models/gpt-5.6-luna",
      headerChecks: inspectOpenAiHeaderContract("test-only"),
      generationPerformed: false,
      externalCostEurMicros: 0,
    }),
  });
  const response = await createPhase6bHandler(enabled.dependencies)(request);
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.probe.upstream.code, "invalid_api_key");
  assert.equal(body.probe.generationPerformed, false);
  assert.equal(enabled.calls.length, 0);
});

test("missing environment test flag and key fail before reservation", async () => {
  const disabled = handlerDependencies({ providerTestEnvironmentEnabled: false });
  assert.equal((await createPhase6bHandler(disabled.dependencies)(syntheticRequest())).status, 503);
  assert.equal(disabled.calls.length, 0);
  const missing = handlerDependencies({ openAiApiKey: null });
  assert.equal((await createPhase6bHandler(missing.dependencies)(syntheticRequest())).status, 503);
  assert.equal(missing.calls.length, 0);
});

test("successful synthetic handler performs accounting around one provider call", async () => {
  const state = handlerDependencies();
  const response = await createPhase6bHandler(state.dependencies)(syntheticRequest());
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.store, false);
  assert.equal(body.tools_used, 0);
  assert.equal(body.returned_model_id, "gpt-5.6-luna");
  assert.equal(body.provider_response_id, "resp_synthetic");
  assert.equal(body.attempt_count, 1);
  assert.deepEqual(state.calls.map((call) => call.name), ["begin", "complete"]);
});

test("provider failure is conservatively accounted and sanitized", async () => {
  const state = handlerDependencies({ fetchImpl: async () => new Response("do not expose", { status: 500 }) });
  const response = await createPhase6bHandler(state.dependencies)(syntheticRequest());
  assert.equal(response.status, 503);
  const body = await response.json();
  assert.equal(body.error, "provider_unavailable");
  assert.deepEqual(state.calls.map((call) => call.name), ["begin", "fail"]);
  assert.equal(state.calls[1].input.p_cost_unknown, true);
});

test("real member processing has no route", async () => {
  const { dependencies } = handlerDependencies();
  const request = new Request("https://example.test/youri-ai/phase6b/member", {
    method: "POST",
    headers: { Authorization: "Bearer server-only" },
  });
  const response = await createPhase6bHandler(dependencies)(request);
  assert.equal(response.status, 404);
});
