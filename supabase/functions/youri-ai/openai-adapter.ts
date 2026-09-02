import {
  assertProviderOutput,
  assertSyntheticPayloadAllowlist,
  PHASE6B_PROVIDER_OUTPUT_SCHEMA,
  type Phase6bModelRoute,
  type SyntheticProviderPayload,
} from "./provider-contracts.ts";
import type { CoachResponse } from "./contracts.ts";

export const OPENAI_API_HOST = "api.openai.com";
export const OPENAI_RESPONSES_PATH = "/v1/responses";
export const OPENAI_MODEL_READ_PATH = "/v1/models/gpt-5.6-luna";

const FIXED_OPENAI_ENDPOINT = `https://${OPENAI_API_HOST}${OPENAI_RESPONSES_PATH}`;
const FIXED_OPENAI_MODEL_READ_ENDPOINT = `https://${OPENAI_API_HOST}${OPENAI_MODEL_READ_PATH}`;

export interface SafeUpstreamError {
  status: number;
  type: string | null;
  code: string | null;
  classification: string;
}

export interface OpenAiCredentialChecks {
  rawExists: boolean;
  trimmedNonEmpty: boolean;
  leadingOrTrailingWhitespacePresent: boolean;
  quoteCharactersPresent: boolean;
  newlineCharactersPresent: boolean;
  bearerPrefixPresent: boolean;
  projectKeyFormatCompatible: boolean;
  normalizationAppliedExactlyOnce: boolean;
}

export interface OpenAiCredentialInspection {
  apiKey: string | null;
  checks: OpenAiCredentialChecks;
}

export interface OpenAiHeaderChecks {
  exactBearerHeader: boolean;
  exactlyOneBearerPrefix: boolean;
  authorizationHeaderCountOne: boolean;
  organizationHeaderPresent: boolean;
  projectHeaderPresent: boolean;
  proxyHeadersForwarded: boolean;
}

export interface OpenAiModelReadProbeResult {
  upstream: SafeUpstreamError;
  keyAuthenticated: boolean;
  returnedModelMatches: boolean;
  endpointHost: typeof OPENAI_API_HOST;
  endpointPath: typeof OPENAI_MODEL_READ_PATH;
  headerChecks: OpenAiHeaderChecks;
  generationPerformed: false;
  externalCostEurMicros: 0;
}

export function inspectOpenAiCredential(raw: string | null | undefined): OpenAiCredentialInspection {
  const rawValue = typeof raw === "string" ? raw : "";
  const normalized = rawValue.trim();
  const quoteCharactersPresent = normalized.includes("\"") || normalized.includes("'");
  const newlineCharactersPresent = /[\r\n]/.test(rawValue);
  const bearerPrefixPresent = /^bearer\s/i.test(normalized);
  return {
    apiKey: normalized || null,
    checks: {
      rawExists: typeof raw === "string",
      trimmedNonEmpty: Boolean(normalized),
      leadingOrTrailingWhitespacePresent: rawValue !== normalized,
      quoteCharactersPresent,
      newlineCharactersPresent,
      bearerPrefixPresent,
      projectKeyFormatCompatible: /^sk-proj-[A-Za-z0-9_-]{20,}$/.test(normalized),
      normalizationAppliedExactlyOnce: true,
    },
  };
}

function assertNormalizedApiKey(apiKey: string): void {
  if (!apiKey) throw new Error("provider_credentials_unavailable");
  if (/^bearer\s/i.test(apiKey) || /[\r\n\"']/.test(apiKey) || /^\s|\s$/.test(apiKey)) {
    throw new Error("provider_credentials_malformed");
  }
}

export function buildOpenAiHeaders(apiKey: string, includeJsonContentType: boolean): Headers {
  assertNormalizedApiKey(apiKey);
  const headers = new Headers({ Authorization: `Bearer ${apiKey}` });
  if (includeJsonContentType) headers.set("Content-Type", "application/json");
  return headers;
}

export function inspectOpenAiHeaderContract(apiKey: string): OpenAiHeaderChecks {
  const headers = buildOpenAiHeaders(apiKey, false);
  const authorization = headers.get("Authorization") || "";
  return {
    exactBearerHeader: authorization === `Bearer ${apiKey}`,
    exactlyOneBearerPrefix: (authorization.match(/Bearer /g) || []).length === 1,
    authorizationHeaderCountOne: [...headers.keys()].filter((name) => name.toLowerCase() === "authorization").length === 1,
    organizationHeaderPresent: headers.has("OpenAI-Organization"),
    projectHeaderPresent: headers.has("OpenAI-Project"),
    proxyHeadersForwarded: [...headers.keys()].some((name) => /^(forwarded|x-forwarded-|via$)/i.test(name)),
  };
}

function safeProviderField(value: unknown): string | null {
  if (typeof value !== "string" || !/^[A-Za-z0-9_.:-]{1,80}$/.test(value)) return null;
  return value;
}

function classifyUpstreamError(status: number, type: string | null, code: string | null): string {
  if (status === 200) return "model_read_authenticated";
  if (status === 401 && code === "invalid_api_key") return "invalid_or_revoked_api_key";
  if (status === 401) return "authentication_rejected";
  if (status === 403) return "permission_denied";
  if (status === 404) return "model_or_endpoint_not_found";
  if (status === 429 && (code === "insufficient_quota" || type === "insufficient_quota")) return "quota_exhausted";
  if (status === 429) return "rate_limited";
  if (status >= 500) return "provider_unavailable";
  return "request_rejected";
}

async function readSafeUpstreamError(response: Response): Promise<SafeUpstreamError> {
  let type: string | null = null;
  let code: string | null = null;
  if (!response.ok) {
    try {
      const payload = await response.json() as Record<string, unknown>;
      const error = payload.error && typeof payload.error === "object"
        ? payload.error as Record<string, unknown>
        : {};
      type = safeProviderField(error.type);
      code = safeProviderField(error.code);
    } catch {
      // An unreadable provider body is intentionally discarded.
    }
  }
  return {
    status: response.status,
    type,
    code,
    classification: classifyUpstreamError(response.status, type, code),
  };
}

function mappedProviderFailure(upstream: SafeUpstreamError): string {
  if (upstream.status === 401) return "provider_authentication_failed";
  if (upstream.status === 403) return "provider_permission_denied";
  if (upstream.status === 404) return "provider_resource_not_found";
  if (upstream.status === 429 && upstream.classification === "quota_exhausted") return "provider_quota_exceeded";
  if (upstream.status === 429) return "provider_rate_limited";
  if (upstream.status >= 500) return "provider_unavailable";
  return "provider_request_rejected";
}

export class SafeProviderError extends Error {
  readonly attemptCount: number;
  readonly costUnknown: boolean;
  readonly upstream: SafeUpstreamError | null;

  constructor(
    code: string,
    attemptCount: number,
    costUnknown: boolean,
    upstream: SafeUpstreamError | null = null,
  ) {
    super(code);
    this.attemptCount = attemptCount;
    this.costUnknown = costUnknown;
    this.upstream = upstream;
  }
}

export interface ProviderUsage {
  inputTokens: number;
  cachedInputTokens: number;
  outputTokens: number;
}

export interface ProviderResult {
  output: CoachResponse;
  usage: ProviderUsage;
  attemptCount: number;
  requestHash: string;
  responseHash: string;
}

interface AdapterOptions {
  apiKey: string;
  endpoint?: string;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

function bytesToHex(value: ArrayBuffer): string {
  return Array.from(new Uint8Array(value)).map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function sha256(value: string): Promise<string> {
  return bytesToHex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
}

function outputText(payload: Record<string, unknown>, attemptCount: number): string {
  if (typeof payload.output_text === "string") return payload.output_text;
  if (!Array.isArray(payload.output)) throw new SafeProviderError("provider_output_missing", attemptCount, false);
  for (const item of payload.output) {
    if (!item || typeof item !== "object") continue;
    const content = (item as Record<string, unknown>).content;
    if (!Array.isArray(content)) continue;
    for (const part of content) {
      if (part && typeof part === "object" && (part as Record<string, unknown>).type === "output_text"
        && typeof (part as Record<string, unknown>).text === "string") {
        return (part as Record<string, unknown>).text as string;
      }
    }
  }
  throw new SafeProviderError("provider_output_missing", attemptCount, false);
}

export function buildOpenAiResponsesRequest(
  modelId: string,
  modelRoute: Phase6bModelRoute,
  payload: SyntheticProviderPayload,
  maxOutputTokens = 512,
) {
  assertSyntheticPayloadAllowlist(payload);
  if (!(["gpt-5.6-luna", "gpt-5.6-terra"] as string[]).includes(modelId)) throw new Error("provider_model_forbidden");
  if ((modelRoute === "luna" && modelId !== "gpt-5.6-luna") || (modelRoute === "terra" && modelId !== "gpt-5.6-terra")) {
    throw new Error("provider_route_conflict");
  }
  if (!Number.isInteger(maxOutputTokens) || maxOutputTokens < 64 || maxOutputTokens > 512) throw new Error("provider_output_limit_invalid");
  return {
    model: modelId,
    store: false,
    background: false,
    tools: [],
    tool_choice: "none",
    max_output_tokens: maxOutputTokens,
    reasoning: { effort: modelRoute === "terra" ? "medium" : "low" },
    safety_identifier: "fmz-synthetic-phase6b-alpha",
    input: [
      {
        role: "developer",
        content: [{
          type: "input_text",
          text: "Return only the required JSON. Use only the supplied synthetic aggregates. Do not diagnose, prescribe, use tools, infer identity, or invent unavailable facts.",
        }],
      },
      { role: "user", content: [{ type: "input_text", text: JSON.stringify(payload) }] },
    ],
    text: {
      format: {
        type: "json_schema",
        name: "fmz_phase6b_coach_response",
        strict: true,
        schema: PHASE6B_PROVIDER_OUTPUT_SCHEMA,
      },
    },
  } as const;
}

export class OpenAiResponsesAdapter {
  readonly adapterCode = "openai_responses";
  private readonly options: AdapterOptions;
  private readonly endpoint: string;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;

  constructor(options: AdapterOptions) {
    assertNormalizedApiKey(options.apiKey);
    this.options = options;
    this.endpoint = options.endpoint || FIXED_OPENAI_ENDPOINT;
    if (this.endpoint !== FIXED_OPENAI_ENDPOINT) throw new Error("provider_endpoint_forbidden");
    this.fetchImpl = options.fetchImpl || fetch;
    this.timeoutMs = options.timeoutMs ?? 20_000;
    if (!Number.isInteger(this.timeoutMs) || this.timeoutMs < 1_000 || this.timeoutMs > 20_000) throw new Error("provider_timeout_invalid");
  }

  async run(
    modelId: string,
    modelRoute: Phase6bModelRoute,
    payload: SyntheticProviderPayload,
    maxAttempts: number,
    maxOutputTokens: number,
  ): Promise<ProviderResult> {
    if (!Number.isInteger(maxAttempts) || maxAttempts < 1 || maxAttempts > 2) throw new Error("provider_retry_limit_invalid");
    const requestBody = buildOpenAiResponsesRequest(modelId, modelRoute, payload, maxOutputTokens);
    const serialized = JSON.stringify(requestBody);
    const requestHash = await sha256(serialized);

    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
      try {
        const response = await this.fetchImpl(this.endpoint, {
          method: "POST",
          headers: buildOpenAiHeaders(this.options.apiKey, true),
          body: serialized,
          signal: controller.signal,
        });
        if (!response.ok) {
          const upstream = await readSafeUpstreamError(response);
          const retryable = response.status === 429 || response.status >= 500;
          if (retryable && attempt < maxAttempts) continue;
          throw new SafeProviderError(mappedProviderFailure(upstream), attempt, true, upstream);
        }
        const raw = await response.json() as Record<string, unknown>;
        const text = outputText(raw, attempt);
        let parsed: unknown;
        try {
          parsed = JSON.parse(text);
        } catch {
          throw new SafeProviderError("provider_structured_output_invalid", attempt, false);
        }
        try {
          assertProviderOutput(parsed);
        } catch {
          throw new SafeProviderError("provider_structured_output_invalid", attempt, false);
        }
        const usage = raw.usage && typeof raw.usage === "object" ? raw.usage as Record<string, unknown> : {};
        const inputDetails = usage.input_tokens_details && typeof usage.input_tokens_details === "object"
          ? usage.input_tokens_details as Record<string, unknown>
          : {};
        const normalizedUsage = {
          inputTokens: Number(usage.input_tokens || 0),
          cachedInputTokens: Number(inputDetails.cached_tokens || 0),
          outputTokens: Number(usage.output_tokens || 0),
        };
        if (!Object.values(normalizedUsage).every(Number.isSafeInteger)
          || normalizedUsage.inputTokens < 0
          || normalizedUsage.cachedInputTokens < 0
          || normalizedUsage.cachedInputTokens > normalizedUsage.inputTokens
          || normalizedUsage.outputTokens < 0) {
          throw new SafeProviderError("provider_usage_invalid", attempt, true);
        }
        return {
          output: parsed as CoachResponse,
          usage: normalizedUsage,
          attemptCount: attempt,
          requestHash,
          responseHash: await sha256(JSON.stringify(parsed)),
        };
      } catch (error) {
        if (error instanceof SafeProviderError) throw error;
        if (error instanceof DOMException && error.name === "AbortError") {
          throw new SafeProviderError("provider_timeout", attempt, true);
        }
        throw new SafeProviderError("provider_network_error", attempt, true);
      } finally {
        clearTimeout(timeout);
      }
    }
    throw new SafeProviderError("provider_unavailable", maxAttempts, true);
  }
}

export async function probeOpenAiModelRead(
  apiKey: string,
  fetchImpl: typeof fetch = fetch,
  timeoutMs = 10_000,
): Promise<OpenAiModelReadProbeResult> {
  assertNormalizedApiKey(apiKey);
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1_000 || timeoutMs > 10_000) {
    throw new Error("provider_probe_timeout_invalid");
  }
  const headerChecks = inspectOpenAiHeaderContract(apiKey);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(FIXED_OPENAI_MODEL_READ_ENDPOINT, {
      method: "GET",
      headers: buildOpenAiHeaders(apiKey, false),
      signal: controller.signal,
    });
    const upstream = await readSafeUpstreamError(response);
    let returnedModelMatches = false;
    if (response.ok) {
      try {
        const payload = await response.json() as Record<string, unknown>;
        returnedModelMatches = payload.object === "model" && payload.id === "gpt-5.6-luna";
      } catch {
        // Authentication is proven by HTTP 200 even if the minimal model payload is malformed.
      }
    }
    return {
      upstream,
      keyAuthenticated: response.status !== 401,
      returnedModelMatches,
      endpointHost: OPENAI_API_HOST,
      endpointPath: OPENAI_MODEL_READ_PATH,
      headerChecks,
      generationPerformed: false,
      externalCostEurMicros: 0,
    };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new SafeProviderError("provider_probe_timeout", 0, false);
    }
    throw new SafeProviderError("provider_probe_network_error", 0, false);
  } finally {
    clearTimeout(timeout);
  }
}
