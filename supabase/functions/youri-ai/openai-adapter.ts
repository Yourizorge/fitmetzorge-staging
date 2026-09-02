import {
  assertProviderOutput,
  assertSyntheticPayloadAllowlist,
  PHASE6B_PROVIDER_OUTPUT_SCHEMA,
  type Phase6bModelRoute,
  type SyntheticProviderPayload,
} from "./provider-contracts.ts";
import type { CoachResponse } from "./contracts.ts";

const FIXED_OPENAI_ENDPOINT = "https://api.openai.com/v1/responses";

export class SafeProviderError extends Error {
  readonly attemptCount: number;
  readonly costUnknown: boolean;

  constructor(
    code: string,
    attemptCount: number,
    costUnknown: boolean,
  ) {
    super(code);
    this.attemptCount = attemptCount;
    this.costUnknown = costUnknown;
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
    if (!options.apiKey.trim()) throw new Error("provider_credentials_unavailable");
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
          headers: {
            Authorization: `Bearer ${this.options.apiKey}`,
            "Content-Type": "application/json",
          },
          body: serialized,
          signal: controller.signal,
        });
        if (!response.ok) {
          const retryable = response.status === 429 || response.status >= 500;
          if (retryable && attempt < maxAttempts) continue;
          const code = response.status === 401 || response.status === 403
            ? "provider_authentication_failed"
            : response.status === 429
            ? "provider_rate_limited"
            : response.status >= 500
            ? "provider_unavailable"
            : "provider_request_rejected";
          throw new SafeProviderError(code, attempt, true);
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
