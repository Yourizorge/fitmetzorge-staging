import { validateCoachResponse, type CoachResponse } from "./contracts.ts";

const ALLOWED_ORIGINS = new Set(["https://yourizorge.github.io", "https://test.appfmz.nl"]);
const BODY_LIMIT_BYTES = 6 * 1024;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type Locale = "nl" | "en" | "de";
type JsonObject = Record<string, unknown>;

export interface Phase6cDependencies {
  verifyBearer(token: string): Promise<{ id: string } | null>;
  memberRpc(token: string, name: string, input?: JsonObject): Promise<JsonObject>;
  serviceRpc(name: string, input?: JsonObject): Promise<JsonObject>;
  createMockReply?: (content: string, locale: Locale) => CoachResponse;
}

interface ChatRequest {
  request_id: string;
  attempt_id: string;
  thread_id: string;
  expected_revision: number;
  locale: Locale;
  content: string;
}

function isObject(value: unknown): value is JsonObject {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function exactKeys(value: JsonObject, keys: string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

export function parsePhase6cChatRequest(value: unknown): ChatRequest {
  const keys = ["request_id", "attempt_id", "thread_id", "expected_revision", "locale", "content"];
  if (!isObject(value) || !exactKeys(value, keys)) throw new Error("chat_request_invalid");
  if (![value.request_id, value.attempt_id, value.thread_id].every((item) => typeof item === "string" && UUID_PATTERN.test(item))) {
    throw new Error("chat_identity_invalid");
  }
  if (!Number.isSafeInteger(value.expected_revision) || Number(value.expected_revision) < 1) throw new Error("chat_revision_invalid");
  if (!["nl", "en", "de"].includes(String(value.locale))) throw new Error("chat_locale_invalid");
  if (typeof value.content !== "string" || value.content.trim().length < 1 || value.content.trim().length > 4000) {
    throw new Error("chat_content_invalid");
  }
  return { ...value, content: value.content.trim() } as ChatRequest;
}

function cors(origin: string | null): HeadersInit {
  if (!origin || !ALLOWED_ORIGINS.has(origin)) return {};
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}

function json(origin: string | null, status: number, body: JsonObject): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors(origin), "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

function safeError(error: unknown): string {
  const raw = error instanceof Error ? error.message : "chat_unexpected_error";
  const match = raw.match(/\b(ai_[a-z0-9_]+|mock_[a-z0-9_]+|chat_[a-z0-9_]+|safety_hard_stop)\b/i);
  return match?.[1]?.toLowerCase() || "chat_unexpected_error";
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

const seriousPatterns = [
  /chest pain|cannot breathe|can't breathe|fainting|suicid/i,
  /borstpijn|geen adem|niet ademen|flauwvallen|zelfmoord/i,
  /brustschmerz|keine luft|nicht atmen|ohnmacht|suizid/i,
];
const medicalAdvicePatterns = [
  /diagnos|medicat|dosage|treatment|prescri/i,
  /diagnos|medicijn|dosering|behandeling|voorschrift/i,
  /diagnos|medikament|dosierung|behandlung|rezept/i,
];

export function createPhase6cMockReply(content: string, locale: Locale): CoachResponse {
  const hardStop = seriousPatterns.some((pattern) => pattern.test(content));
  const safeRefusal = !hardStop && medicalAdvicePatterns.some((pattern) => pattern.test(content));
  const copy = {
    nl: {
      normal: "Ik hoor je. Kies een kleine, haalbare volgende stap en kijk daarna eerlijk wat het effect is.",
      refusal: "Ik kan geen diagnose, medicatie- of behandeladvies geven. Bespreek dit met een bevoegde zorgprofessional.",
      hard: "Stop hiermee en zoek direct passende professionele hulp. Bij acuut gevaar: bel 112.",
    },
    en: {
      normal: "I hear you. Choose one small, realistic next step and then review its effect honestly.",
      refusal: "I cannot provide diagnosis, medication, or treatment advice. Discuss this with a qualified health professional.",
      hard: "Stop and seek appropriate professional help now. In immediate danger, call your local emergency number.",
    },
    de: {
      normal: "Ich hoere dich. Waehle einen kleinen, realistischen naechsten Schritt und pruefe danach ehrlich die Wirkung.",
      refusal: "Ich kann keine Diagnose, Medikamenten- oder Behandlungsempfehlung geben. Besprich das mit medizinischem Fachpersonal.",
      hard: "Stoppe und hole jetzt passende professionelle Hilfe. Bei akuter Gefahr rufe den Notruf.",
    },
  }[locale];
  return {
    schema_version: "phase6a.response.v1",
    feature_code: "private_chat",
    summary: hardStop ? copy.hard : safeRefusal ? copy.refusal : copy.normal,
    observations: [],
    uncertainties: [],
    recommendations: hardStop ? ["seek_appropriate_professional_support"] : safeRefusal ? ["consult_qualified_professional"] : ["choose_one_realistic_next_step"],
    actions: [],
    safety: {
      status: hardStop ? "hard_stop" : "clear",
      category: hardStop ? "serious_health" : "none",
      message_key: hardStop ? "safety.professional_support" : safeRefusal ? "safety.medical_boundary" : "safety.clear",
      automatic_execution_blocked: hardStop,
    },
  };
}

function statusFor(code: string): number {
  if (["ai_entitlement_required", "ai_consent_required", "ai_age_required", "safety_hard_stop", "mock_disabled", "external_provider_forbidden", "ai_thread_forbidden"].includes(code)) return 403;
  if (code.includes("stale_conflict") || code.includes("request_conflict")) return 409;
  if (code.includes("limit_reached") || code.includes("rate_limit")) return 429;
  if (code.endsWith("_invalid")) return 400;
  return 422;
}

export function createPhase6cHandler(dependencies: Phase6cDependencies) {
  return async (request: Request): Promise<Response> => {
    const origin = request.headers.get("Origin");
    if (origin && !ALLOWED_ORIGINS.has(origin)) return json(null, 403, { error: "origin_forbidden" });
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (request.method !== "POST") return json(origin, 405, { error: "method_not_allowed" });
    const length = Number(request.headers.get("Content-Length") || "0");
    if (Number.isFinite(length) && length > BODY_LIMIT_BYTES) return json(origin, 413, { error: "body_too_large" });
    const authorization = request.headers.get("Authorization") || "";
    const token = authorization.startsWith("Bearer ") ? authorization.slice(7).trim() : "";
    const member = token ? await dependencies.verifyBearer(token) : null;
    if (!member) return json(origin, 401, { error: "unauthorized" });

    let runId = "";
    try {
      const raw = await request.text();
      if (new TextEncoder().encode(raw).byteLength > BODY_LIMIT_BYTES) return json(origin, 413, { error: "body_too_large" });
      const input = parsePhase6cChatRequest(JSON.parse(raw));
      const submitted = await dependencies.memberRpc(token, "fmz_phase6c_submit_message", {
        p_thread_id: input.thread_id,
        p_request_id: input.request_id,
        p_expected_revision: input.expected_revision,
        p_locale: input.locale,
        p_content: input.content,
      });
      const messageId = String(submitted.message_id || "");
      if (!UUID_PATTERN.test(messageId)) throw new Error("chat_submit_invalid");
      const payloadHash = await sha256(JSON.stringify({ package: "6c", message_id: messageId, content: input.content }));
      const begun = await dependencies.serviceRpc("fmz_phase6c_service_begin_mock_run", {
        p_user_id: member.id,
        p_source_message_id: messageId,
        p_attempt_id: input.attempt_id,
        p_payload_hash: payloadHash,
      });
      runId = String(begun.run_id || "");
      if (!UUID_PATTERN.test(runId)) throw new Error("chat_run_invalid");
      if (begun.status === "completed") {
        return json(origin, 200, { mode: "deterministic_mock", replay: true, external_ai_calls: 0, external_ai_cost_eur: 0 });
      }
      if (begun.status !== "reserved") throw new Error("chat_attempt_not_retryable");
      const output = (dependencies.createMockReply || createPhase6cMockReply)(input.content, input.locale);
      if (!validateCoachResponse(output) || output.actions.length !== 0) throw new Error("chat_mock_output_invalid");
      await dependencies.serviceRpc("fmz_phase6a_service_complete_run", {
        p_run_id: runId,
        p_structured_output: output,
        p_actual_cost_micros: 0,
        p_input_tokens: 0,
        p_output_tokens: 0,
      });
      return json(origin, 200, { mode: "deterministic_mock", replay: false, external_ai_calls: 0, external_ai_cost_eur: 0, output });
    } catch (error) {
      const code = safeError(error);
      if (runId) {
        try {
          await dependencies.serviceRpc("fmz_phase6a_service_fail_run", { p_run_id: runId, p_safe_error_code: code });
        } catch {
          // The original sanitized failure remains authoritative.
        }
      }
      return json(origin, statusFor(code), { error: code });
    }
  };
}
