import {
  assertSyntheticPayloadAllowlist,
  buildSyntheticProviderPayload,
  fixtureRoute,
  PHASE6B_MODEL_ROUTES,
  validateSyntheticProviderRequest,
} from "./provider-contracts.ts";
import {
  type OpenAiCredentialChecks,
  type OpenAiModelReadProbeResult,
  OpenAiResponsesAdapter,
  SafeProviderError,
  sha256,
} from "./openai-adapter.ts";

const BODY_LIMIT_BYTES = 2048;

export interface BeginResult {
  replay: boolean;
  run_id: string;
  status: "reserved" | "completed" | "failed";
  model_id: string;
  max_attempts: number;
  max_output_tokens?: number;
}

export interface Phase6bDependencies {
  authorizeServer(request: Request): Promise<boolean>;
  providerTestEnvironmentEnabled: boolean;
  authDiagnosticEnvironmentEnabled: boolean;
  openAiApiKey: string | null;
  openAiCredentialChecks: OpenAiCredentialChecks;
  runAuthProbe(): Promise<OpenAiModelReadProbeResult>;
  readStatus(): Promise<Record<string, unknown>>;
  begin(input: Record<string, unknown>): Promise<BeginResult>;
  complete(input: Record<string, unknown>): Promise<Record<string, unknown>>;
  fail(input: Record<string, unknown>): Promise<Record<string, unknown>>;
  fetchImpl?: typeof fetch;
}

function json(status: number, body: Record<string, unknown>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

function safeCode(error: unknown): string {
  const code = error instanceof Error ? error.message : "provider_unexpected_error";
  return /^[a-z0-9_]{1,80}$/.test(code) ? code : "provider_unexpected_error";
}

export function createPhase6bHandler(dependencies: Phase6bDependencies) {
  return async (request: Request): Promise<Response> => {
    if (request.headers.get("Origin")) return json(403, { error: "server_only_route" });
    if (!(await dependencies.authorizeServer(request))) return json(401, { error: "server_authorization_required" });
    const path = new URL(request.url).pathname;

    if (path.endsWith("/phase6b/status")) {
      if (request.method !== "GET") return json(405, { error: "method_not_allowed" });
      return json(200, {
        ...(await dependencies.readStatus()),
        provider_credential_available: Boolean(dependencies.openAiApiKey),
        synthetic_test_environment_enabled: dependencies.providerTestEnvironmentEnabled,
        real_member_processing_enabled: false,
      });
    }

    if (path.endsWith("/phase6b/auth-diagnostic")) {
      if (request.method !== "GET") return json(405, { error: "method_not_allowed" });
      if (!dependencies.authDiagnosticEnvironmentEnabled) {
        return json(503, { error: "auth_diagnostic_environment_disabled" });
      }
      if (!dependencies.openAiApiKey) return json(503, { error: "provider_credentials_unavailable" });
      try {
        const probe = await dependencies.runAuthProbe();
        return json(200, {
          mode: "provider_authentication_diagnostic",
          secret_checks: dependencies.openAiCredentialChecks,
          probe,
          synthetic_test_environment_enabled: dependencies.providerTestEnvironmentEnabled,
          real_member_processing_enabled: false,
        });
      } catch (error) {
        return json(503, { error: safeCode(error) });
      }
    }

    if (!path.endsWith("/phase6b/synthetic-test")) return json(404, { error: "route_not_found" });
    if (request.method !== "POST") return json(405, { error: "method_not_allowed" });
    if (!dependencies.providerTestEnvironmentEnabled) return json(503, { error: "synthetic_test_environment_disabled" });
    if (!dependencies.openAiApiKey) return json(503, { error: "provider_credentials_unavailable" });
    const length = Number(request.headers.get("Content-Length") || "0");
    if (Number.isFinite(length) && length > BODY_LIMIT_BYTES) return json(413, { error: "body_too_large" });

    let runId: string | null = null;
    try {
      const raw = await request.text();
      if (new TextEncoder().encode(raw).byteLength > BODY_LIMIT_BYTES) return json(413, { error: "body_too_large" });
      const contract = validateSyntheticProviderRequest(JSON.parse(raw));
      const route = fixtureRoute(contract.fixture_code);
      const payload = buildSyntheticProviderPayload(contract.fixture_code);
      assertSyntheticPayloadAllowlist(payload);
      const payloadHash = await sha256(JSON.stringify(payload));
      const begin = await dependencies.begin({
        p_request_id: contract.request_id,
        p_fixture_code: contract.fixture_code,
        p_request_purpose: payload.request_purpose,
        p_model_route: route,
        p_payload_hash: payloadHash,
      });
      runId = begin.run_id;
      if (begin.replay) {
        if (begin.status === "reserved") return json(409, { error: "provider_test_in_progress" });
        return json(200, { replay: true, status: begin.status, external_call_performed: false });
      }
      if (begin.model_id !== PHASE6B_MODEL_ROUTES[route]) throw new Error("provider_model_contract_conflict");
      const adapter = new OpenAiResponsesAdapter({
        apiKey: dependencies.openAiApiKey,
        fetchImpl: dependencies.fetchImpl,
        timeoutMs: 20_000,
      });
      const result = await adapter.run(begin.model_id, route, payload, begin.max_attempts, begin.max_output_tokens || 512);
      const completion = await dependencies.complete({
        p_run_id: begin.run_id,
        p_attempt_count: result.attemptCount,
        p_input_tokens: result.usage.inputTokens,
        p_cached_input_tokens: result.usage.cachedInputTokens,
        p_output_tokens: result.usage.outputTokens,
        p_response_hash: result.responseHash,
        p_provider_request_hash: result.requestHash,
      });
      return json(200, {
        mode: "synthetic_provider_test",
        fixture_code: contract.fixture_code,
        model_id: begin.model_id,
        store: false,
        tools_used: 0,
        usage: result.usage,
        estimated_cost_eur_micros: completion.actual_eur_micros,
        output: result.output,
      });
    } catch (error) {
      const providerError = error instanceof SafeProviderError ? error : null;
      if (runId) {
        try {
          await dependencies.fail({
            p_run_id: runId,
            p_attempt_count: providerError?.attemptCount || 0,
            p_safe_error_code: safeCode(error),
            p_cost_unknown: providerError?.costUnknown ?? false,
          });
        } catch {
          return json(500, { error: "provider_accounting_failure" });
        }
      }
      const code = safeCode(error);
      const status = code.includes("authorization") ? 401
        : code.includes("budget") || code.includes("call_cap") ? 429
        : code.includes("timeout") ? 504
        : code.includes("unavailable") || code.includes("network") ? 503
        : code.includes("invalid") || code.includes("conflict") ? 422
        : 500;
      return json(status, { error: code });
    }
  };
}
