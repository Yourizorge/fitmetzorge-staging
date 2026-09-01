import {
  assertTrustGate,
  validateCoachResponse,
  validateContractRequest,
  type TrustStatus,
} from "./contracts.ts";
import { DeterministicMockAdapter } from "./mock-adapter.ts";

const ALLOWED_ORIGINS = new Set(["https://yourizorge.github.io", "https://test.appfmz.nl"]);
const BODY_LIMIT_BYTES = 8 * 1024;

export interface YouriAiDependencies {
  verifyBearer(token: string): Promise<{ id: string } | null>;
  readTrustStatus(token: string, featureCode: string): Promise<TrustStatus>;
  mockTestEnabled: boolean;
}

function cors(origin: string | null): HeadersInit {
  if (!origin || !ALLOWED_ORIGINS.has(origin)) return {};
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Headers": "authorization, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}

function response(origin: string | null, status: number, body: Record<string, unknown>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors(origin), "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

function safeError(error: unknown): string {
  const code = error instanceof Error ? error.message : "unexpected_error";
  return /^[a-z0-9_]{1,80}$/.test(code) ? code : "unexpected_error";
}

export function createYouriAiHandler(dependencies: YouriAiDependencies) {
  const adapter = new DeterministicMockAdapter();

  return async (request: Request): Promise<Response> => {
    const origin = request.headers.get("Origin");
    if (origin && !ALLOWED_ORIGINS.has(origin)) return response(null, 403, { error: "origin_forbidden" });
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (request.method !== "POST") return response(origin, 405, { error: "method_not_allowed" });

    const length = Number(request.headers.get("Content-Length") || "0");
    if (Number.isFinite(length) && length > BODY_LIMIT_BYTES) return response(origin, 413, { error: "body_too_large" });
    const authorization = request.headers.get("Authorization") || "";
    const token = authorization.startsWith("Bearer ") ? authorization.slice(7).trim() : "";
    if (!token || !(await dependencies.verifyBearer(token))) return response(origin, 401, { error: "unauthorized" });

    try {
      const rawBody = await request.text();
      if (new TextEncoder().encode(rawBody).byteLength > BODY_LIMIT_BYTES) return response(origin, 413, { error: "body_too_large" });
      const contract = validateContractRequest(JSON.parse(rawBody));
      const trust = await dependencies.readTrustStatus(token, contract.feature_code);
      assertTrustGate(trust);
      if (!dependencies.mockTestEnabled) return response(origin, 403, { error: "mock_disabled" });

      const output = await adapter.run(contract);
      if (!validateCoachResponse(output)) return response(origin, 422, { error: "structured_output_invalid" });
      return response(origin, 200, {
        mode: "deterministic_mock",
        external_ai_calls: 0,
        external_ai_cost_eur: 0,
        output,
      });
    } catch (error) {
      const code = safeError(error);
      const status = code === "ai_feature_disabled" || code === "provider_disabled" || code === "mock_disabled"
        ? 403
        : code.endsWith("_invalid") || code === "request_contract_invalid"
        ? 400
        : code === "mock_provider_timeout"
        ? 504
        : 422;
      return response(origin, status, { error: code });
    }
  };
}
