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

function normalizeSafetyText(value: string): string {
  return ` ${value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[\u2018\u2019']/g, "")
    .replace(/\u00df/g, "ss")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ")} `;
}

const seriousPatterns = [
  /\bchest (?:pain|pressure|tightness)\b|\bpain (?:in|on) (?:my |the )?chest\b|\b(?:pressure|tightness) (?:in|on) (?:my |the )?chest\b/,
  /\bcannot breathe\b|\bcant breathe\b|\bstruggling to breathe\b|\bshortness of breath\b|\bshort of breath\b|\bfainted\b|\bpassed out\b|\bsuicid(?:e|al)\b/,
  /\bborstpijn\b|\bpijn (?:op|in) (?:mijn |de )?borst\b|\bmijn borst doet pijn\b|\b(?:druk|beklemming|enge druk) (?:op|in) (?:mijn |de )?borst\b/,
  /\bkan niet ademen\b|\bkrijg geen adem\b|\bgeen lucht\b|\bkortademig\b|\bbenauwd\b|\bflauwgevallen\b|\braak flauw\b|\bbewusteloos\b|\bzelfmoord\b/,
  /\bbrustschmerz(?:en)?\b|\bbrustdruck\b|\bschmerzen (?:in|auf) (?:meiner |der )?brust\b|\b(?:druck|enge) (?:in|auf) (?:meiner |der )?brust\b/,
  /\bkann nicht atmen\b|\bbekomme keine luft\b|\batemnot\b|\bkurzatmig\b|\bohnmacht\b|\bohnmachtig\b|\bbewusstlos\b|\bsuizid\b/,
];
const dizzinessPatterns = [
  /\bduizelig(?:heid)?\b|\bdraaierig\b|\blicht in (?:mijn |het )?hoofd\b|\bbijna (?:aan het )?flauw(?:vallen)?\b|\bflauwgevallen\b|\braak flauw\b/,
  /\bdizz(?:y|iness)\b|\blight ?headed\b|\b(?:nearly|almost|about to) faint(?:ed|ing)?\b|\bfaint(?:ed|ing)\b|\bpassed out\b/,
  /\bschwindel(?:ig)?\b|\bbenommen\b|\bfast ohnmachtig\b|\bohnmachtig\b|\bbewusstlos\b/,
];
const exertionPatterns = [
  /\bsport(?:en)?\b|\btrain(?:en|ing)?\b|\binspanning\b|\boefening\b/,
  /\bexercis(?:e|ing)\b|\btrain(?:ing)?\b|\bworkout\b|\bexertion\b/,
  /\bsport\b|\btraining\b|\btrainieren\b|\bbelastung\b/,
];
const chestDiscomfortPatterns = [
  /\bonprettig gevoel (?:op|in) (?:mijn |de )?borst\b|\bborstklachten\b/,
  /\bchest discomfort\b/,
  /\bbeschwerden (?:in|an) (?:meiner |der )?brust\b|\bunwohlsein (?:in|an) (?:meiner |der )?brust\b/,
];
const educationalPatterns = [
  /\bwat (?:betekent|zijn|is)\b|\bleg uit\b|\bwat moet (?:iemand|je) doen bij\b/,
  /\bwhat (?:does|do|is|are)\b|\bexplain\b|\bwhat should (?:someone|you) do (?:about|with)\b/,
  /\bwas (?:bedeutet|ist|sind)\b|\berklar(?:e|en)\b|\bwas soll (?:man|jemand) bei\b/,
];
const currentPersonalPatterns = [
  /\bik (?:heb|voel|ben|word|werd|krijg)\b|\bmijn borst\b|\bbij mij\b|\bnu\b|\bmomenteel\b|\bvandaag\b|\bhoudt aan\b/,
  /\bi (?:have|feel|am|became|get)\b|\bmy chest\b|\bfor me\b|\bnow\b|\bcurrently\b|\btoday\b|\bpersists?\b/,
  /\bich (?:habe|fuhle|bin|werde|bekomme)\b|\bmeine brust\b|\bbei mir\b|\bjetzt\b|\bheute\b|\bhalt an\b/,
];
const negationBeforeMatch = /\b(?:geen|zonder|niet|no|without|not|kein|keine|keinen|keinem|keiner|ohne|nicht)\b(?:\s+[a-z0-9]+){0,2}\s*$/;

function hasNonNegatedMatch(text: string, pattern: RegExp): boolean {
  const matcher = new RegExp(pattern.source, pattern.flags.includes("g") ? pattern.flags : `${pattern.flags}g`);
  for (const match of text.matchAll(matcher)) {
    const prefix = text.slice(Math.max(0, (match.index || 0) - 48), match.index).trimEnd();
    if (!negationBeforeMatch.test(prefix)) return true;
  }
  return false;
}

function hasConcept(text: string, patterns: RegExp[]): boolean {
  return patterns.some((pattern) => hasNonNegatedMatch(text, pattern));
}

export function classifyPhase6cSafety(content: string): "clear" | "hard_stop" {
  const text = normalizeSafetyText(content);
  const educationalOnly = educationalPatterns.some((pattern) => pattern.test(text)) &&
    !currentPersonalPatterns.some((pattern) => pattern.test(text));
  if (educationalOnly) return "clear";

  const serious = hasConcept(text, seriousPatterns);
  const dizziness = hasConcept(text, dizzinessPatterns);
  const exertion = exertionPatterns.some((pattern) => pattern.test(text));
  const chestDiscomfort = hasConcept(text, chestDiscomfortPatterns);
  return serious || dizziness || (chestDiscomfort && (dizziness || exertion)) ? "hard_stop" : "clear";
}

const medicalAdvicePatterns = [
  /diagnos|medicat|dosage|treatment|prescri/i,
  /diagnos|medicijn|dosering|behandeling|voorschrift/i,
  /diagnos|medikament|dosierung|behandlung|rezept/i,
];

export function createPhase6cMockReply(content: string, locale: Locale): CoachResponse {
  const hardStop = classifyPhase6cSafety(content) === "hard_stop";
  const safeRefusal = !hardStop && medicalAdvicePatterns.some((pattern) => pattern.test(content));
  const copy = {
    nl: {
      normal: "Ik hoor je. Kies een kleine, haalbare volgende stap en kijk daarna eerlijk wat het effect is.",
      refusal: "Ik kan geen diagnose, medicatie- of behandeladvies geven. Bespreek dit met een bevoegde zorgprofessional.",
      hard: "Stop direct met sporten. Ik kan geen diagnose stellen. Laat deze klachten snel professioneel medisch beoordelen. Zijn de klachten ernstig, houden ze aan of is er direct gevaar, bel dan 112.",
    },
    en: {
      normal: "I hear you. Choose one small, realistic next step and then review its effect honestly.",
      refusal: "I cannot provide diagnosis, medication, or treatment advice. Discuss this with a qualified health professional.",
      hard: "Stop exercising now. I cannot diagnose this. Seek prompt professional medical assessment. If symptoms are severe, ongoing, or there is immediate danger, call your local emergency number.",
    },
    de: {
      normal: "Ich hoere dich. Waehle einen kleinen, realistischen naechsten Schritt und pruefe danach ehrlich die Wirkung.",
      refusal: "Ich kann keine Diagnose, Medikamenten- oder Behandlungsempfehlung geben. Besprich das mit medizinischem Fachpersonal.",
      hard: "Beende das Training sofort. Ich kann keine Diagnose stellen. Lass diese Beschwerden zeitnah medizinisch abklaeren. Bei starken oder anhaltenden Beschwerden oder unmittelbarer Gefahr rufe den Notruf.",
    },
  }[locale];
  return {
    schema_version: "phase6a.response.v1",
    feature_code: "private_chat",
    summary: hardStop ? copy.hard : safeRefusal ? copy.refusal : copy.normal,
    observations: [],
    uncertainties: [],
    recommendations: hardStop ? ["seek_prompt_professional_medical_assessment"] : safeRefusal ? ["consult_qualified_professional"] : ["choose_one_realistic_next_step"],
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
