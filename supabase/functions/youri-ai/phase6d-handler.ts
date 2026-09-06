const ALLOWED_ORIGINS = new Set(["https://yourizorge.github.io", "https://test.appfmz.nl"]);
const BODY_LIMIT_BYTES = 4 * 1024;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type AnalysisKind = "daily" | "post_workout" | "weekly";
type Locale = "nl" | "en" | "de";
type JsonObject = Record<string, unknown>;

export interface Phase6dDependencies {
  verifyBearer(token: string): Promise<{ id: string } | null>;
  memberRpc(token: string, name: string, input?: JsonObject): Promise<JsonObject>;
  serviceRpc(name: string, input?: JsonObject): Promise<JsonObject>;
  createMockAnalysis?: (context: JsonObject, locale: Locale) => JsonObject;
}

interface AnalysisRequest {
  request_id: string;
  analysis_kind: AnalysisKind;
  locale: Locale;
  event_id?: string;
}

function isObject(value: unknown): value is JsonObject {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function exactKeys(value: JsonObject, keys: string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

export function parsePhase6dAnalysisRequest(value: unknown): AnalysisRequest {
  if (!isObject(value)) throw new Error("analysis_request_invalid");
  const keys = value.event_id === undefined
    ? ["request_id", "analysis_kind", "locale"]
    : ["request_id", "analysis_kind", "locale", "event_id"];
  if (!exactKeys(value, keys)) throw new Error("analysis_request_invalid");
  if (typeof value.request_id !== "string" || !UUID_PATTERN.test(value.request_id)) {
    throw new Error("analysis_identity_invalid");
  }
  if (!["daily", "post_workout", "weekly"].includes(String(value.analysis_kind))) {
    throw new Error("analysis_kind_invalid");
  }
  if (!["nl", "en", "de"].includes(String(value.locale))) throw new Error("analysis_locale_invalid");
  if (value.event_id !== undefined && (typeof value.event_id !== "string" || !UUID_PATTERN.test(value.event_id))) {
    throw new Error("analysis_event_invalid");
  }
  return value as AnalysisRequest;
}

function featureCode(kind: AnalysisKind): "daily_analysis" | "post_workout" | "weekly_checkin" {
  return kind === "daily" ? "daily_analysis" : kind === "post_workout" ? "post_workout" : "weekly_checkin";
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
  const raw = error instanceof Error ? error.message : "analysis_unexpected_error";
  const match = raw.match(/\b(ai_[a-z0-9_]+|mock_[a-z0-9_]+|chat_[a-z0-9_]+|analysis_[a-z0-9_]+|budget_[a-z0-9_]+|terra_grace_forbidden|safety_hard_stop)\b/i);
  return match?.[1]?.toLowerCase() || "analysis_unexpected_error";
}

function statusFor(code: string): number {
  if ([
    "ai_entitlement_required",
    "ai_analysis_consent_required",
    "ai_age_required",
    "safety_hard_stop",
    "mock_disabled",
    "external_provider_forbidden",
    "analysis_kind_disabled",
    "analysis_result_forbidden",
  ].includes(code)) return 403;
  if (code.includes("stale_conflict") || code.includes("request_conflict")) return 409;
  if (code.includes("limit_reached") || code.includes("rate_limit") || code.includes("budget_") || code === "terra_grace_forbidden") return 429;
  if (code.endsWith("_invalid")) return 400;
  return 422;
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function text(locale: Locale, key: string): string {
  const copy = {
    nl: {
      daily: "Je daganalyse is klaar op basis van de betrouwbare gegevens die nu beschikbaar zijn.",
      post_workout: "Je post-training analyse is klaar op basis van je afgeronde training en recente context.",
      weekly: "Je weekanalyse is klaar op basis van de beschikbare gegevens van de afgelopen lokale dagen.",
      partial: "De analyse is beperkt omdat niet alle databronnen recent beschikbaar zijn.",
      data: "Deze analyse blijft read-only: er zijn geen plannen, doelen of voedingsinstellingen aangepast.",
      training: "Training is meegenomen als samenvatting van afgeronde sessies en sets.",
      nutrition: "Voeding is meegenomen als dagtotalen zonder productdetails of notities.",
      recovery: "Herstel is meegenomen als slaap-, stap- en welzijnsgemiddelden.",
      progress: "Voortgang is meegenomen als meetmomenten en gewichtsverloop.",
    },
    en: {
      daily: "Your daily analysis is ready based on the reliable data currently available.",
      post_workout: "Your post-workout analysis is ready based on the completed workout and recent context.",
      weekly: "Your weekly analysis is ready based on the available data from the recent local days.",
      partial: "The analysis is limited because not all data sources are recently available.",
      data: "This analysis stays read-only: no plans, goals, or nutrition settings were changed.",
      training: "Training was included as a summary of completed sessions and sets.",
      nutrition: "Nutrition was included as daily totals without product details or notes.",
      recovery: "Recovery was included as sleep, step, and wellbeing averages.",
      progress: "Progress was included as measurements and weight trend data.",
    },
    de: {
      daily: "Deine Tagesanalyse ist auf Basis der aktuell verlaesslichen Daten bereit.",
      post_workout: "Deine Post-Training-Analyse ist auf Basis des abgeschlossenen Trainings und des aktuellen Kontexts bereit.",
      weekly: "Deine Wochenanalyse ist auf Basis der verfuegbaren Daten der letzten lokalen Tage bereit.",
      partial: "Die Analyse ist begrenzt, weil nicht alle Datenquellen aktuell verfuegbar sind.",
      data: "Diese Analyse bleibt read-only: Plaene, Ziele oder Ernaehrungseinstellungen wurden nicht geaendert.",
      training: "Training wurde als Zusammenfassung abgeschlossener Einheiten und Saetze einbezogen.",
      nutrition: "Ernaehrung wurde als Tagessummen ohne Produktdetails oder Notizen einbezogen.",
      recovery: "Erholung wurde als Schlaf-, Schritt- und Wohlbefindensdurchschnitt einbezogen.",
      progress: "Fortschritt wurde als Messpunkte und Gewichtsverlauf einbezogen.",
    },
  } as const;
  return copy[locale][key as keyof typeof copy["nl"]] || copy.nl[key as keyof typeof copy["nl"]] || key;
}

function objectAt(value: JsonObject, key: string): JsonObject {
  const item = value[key];
  return isObject(item) ? item : {};
}

function numberAt(value: JsonObject, key: string): number {
  const item = value[key];
  return typeof item === "number" && Number.isFinite(item) ? item : 0;
}

function arrayAt(value: JsonObject, key: string): unknown[] {
  const item = value[key];
  return Array.isArray(item) ? item : [];
}

export function createPhase6dMockAnalysis(context: JsonObject, locale: Locale): JsonObject {
  const kind = String(context.analysis_kind || "daily") as AnalysisKind;
  const quality = objectAt(context, "quality");
  const sources = objectAt(context, "sources");
  const period = objectAt(context, "period");
  const level = String(quality.level || "partial");
  const status = level === "partial" ? "partial" : "ready";
  const observations: JsonObject[] = [];

  const training = objectAt(sources, "training");
  const nutrition = objectAt(sources, "nutrition");
  const recovery = objectAt(sources, "recovery");
  const progress = objectAt(sources, "progress");
  if (numberAt(training, "completed_workouts") || numberAt(training, "set_count")) {
    observations.push({ source: "training", text: text(locale, "training"), evidence: ["aggregate_training"] });
  }
  if (numberAt(nutrition, "days_logged") || numberAt(nutrition, "items_logged")) {
    observations.push({ source: "nutrition", text: text(locale, "nutrition"), evidence: ["aggregate_nutrition"] });
  }
  if (numberAt(recovery, "days_logged")) {
    observations.push({ source: "recovery", text: text(locale, "recovery"), evidence: ["aggregate_recovery"] });
  }
  if (numberAt(progress, "weight_logs") || numberAt(progress, "body_measurement_logs")) {
    observations.push({ source: "progress", text: text(locale, "progress"), evidence: ["aggregate_progress"] });
  }

  const missing = arrayAt(quality, "missing_sources").map(String).slice(0, 8);
  return {
    schema_version: "phase6d.analysis.v1",
    analysis_kind: kind,
    feature_code: featureCode(kind),
    status,
    summary: `${text(locale, kind)} ${level === "partial" ? text(locale, "partial") : text(locale, "data")}`,
    observations,
    uncertainties: missing,
    suggestions: [
      { kind: "read_only_reflection", text: text(locale, "data") },
    ],
    actions: [],
    safety: {
      status: "clear",
      category: "none",
      message_key: "safety.clear",
      automatic_execution_blocked: false,
    },
    data_quality: quality,
    period,
    privacy: {
      chat_history_used_as_context: false,
      raw_prompts_logged: false,
      raw_notes_included: false,
      trainer_visible: false,
      domain_writes_allowed: false,
    },
  };
}

export function validatePhase6dAnalysisOutput(value: unknown): boolean {
  if (!isObject(value)) return false;
  if (value.schema_version !== "phase6d.analysis.v1") return false;
  if (!["daily", "post_workout", "weekly"].includes(String(value.analysis_kind))) return false;
  if (value.feature_code !== featureCode(value.analysis_kind as AnalysisKind)) return false;
  if (!["ready", "partial", "hard_stop", "review_required"].includes(String(value.status))) return false;
  if (typeof value.summary !== "string" || value.summary.trim().length < 1 || value.summary.length > 1600) return false;
  if (!Array.isArray(value.observations) || value.observations.length > 12) return false;
  if (!Array.isArray(value.uncertainties) || value.uncertainties.length > 12) return false;
  if (!Array.isArray(value.suggestions) || value.suggestions.length > 12) return false;
  if (!Array.isArray(value.actions) || value.actions.length !== 0) return false;
  if (!isObject(value.safety) || !["clear", "hard_stop", "review_required"].includes(String(value.safety.status))) return false;
  if (!isObject(value.data_quality) || !isObject(value.period)) return false;
  const raw = JSON.stringify(value);
  return raw.length <= 32768 && !/"(raw_prompt|prompt|message_content|email|jwt|token|secret|service_role|action_code)"\s*:/.test(raw);
}

export function createPhase6dHandler(dependencies: Phase6dDependencies) {
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
    let resultId = "";
    try {
      const raw = await request.text();
      if (new TextEncoder().encode(raw).byteLength > BODY_LIMIT_BYTES) return json(origin, 413, { error: "body_too_large" });
      const input = parsePhase6dAnalysisRequest(JSON.parse(raw));
      const prepared = await dependencies.memberRpc(token, "fmz_phase6d_prepare_analysis", {
        p_request_id: input.request_id,
        p_analysis_kind: input.analysis_kind,
        p_locale: input.locale,
        p_event_id: input.event_id || null,
      });
      if (prepared.status !== "prepared") {
        return json(origin, 200, {
          mode: "deterministic_mock",
          replay: Boolean(prepared.replay),
          result: prepared.result || null,
          external_ai_calls: 0,
          external_ai_cost_eur: 0,
        });
      }
      resultId = String(prepared.result_id || "");
      if (!UUID_PATTERN.test(resultId)) throw new Error("analysis_result_invalid");
      const context = isObject(prepared.context) ? prepared.context : null;
      if (!context) throw new Error("analysis_context_invalid");
      const payloadHash = await sha256(JSON.stringify({ package: "6d", result_id: resultId, context }));
      const missing = arrayAt(context, "unavailable_sources").map(String).slice(0, 24);
      const begun = await dependencies.serviceRpc("fmz_phase6d_service_begin_analysis", {
        p_user_id: member.id,
        p_result_id: resultId,
        p_request_id: input.request_id,
        p_analysis_kind: input.analysis_kind,
        p_payload_hash: payloadHash,
        p_context_sources: context,
        p_unavailable_sources: missing,
      });
      runId = String(begun.run_id || "");
      if (!UUID_PATTERN.test(runId)) throw new Error("analysis_run_invalid");
      if (begun.status === "completed") {
        return json(origin, 200, { mode: "deterministic_mock", replay: true, result_id: resultId, external_ai_calls: 0, external_ai_cost_eur: 0 });
      }
      if (begun.status !== "reserved") throw new Error("analysis_attempt_not_retryable");
      const output = (dependencies.createMockAnalysis || createPhase6dMockAnalysis)(context, input.locale);
      if (!validatePhase6dAnalysisOutput(output)) throw new Error("analysis_mock_output_invalid");
      await dependencies.serviceRpc("fmz_phase6d_service_complete_analysis", {
        p_run_id: runId,
        p_result_id: resultId,
        p_structured_output: output,
        p_actual_cost_micros: 0,
        p_input_tokens: 0,
        p_output_tokens: 0,
      });
      return json(origin, 200, {
        mode: "deterministic_mock",
        replay: false,
        result_id: resultId,
        model_tier: prepared.model_tier,
        external_ai_calls: 0,
        external_ai_cost_eur: 0,
        output,
      });
    } catch (error) {
      const code = safeError(error);
      if (runId && resultId) {
        try {
          await dependencies.serviceRpc("fmz_phase6d_service_fail_analysis", {
            p_run_id: runId,
            p_result_id: resultId,
            p_safe_error_code: code,
          });
        } catch {
          // The sanitized Edge error remains authoritative.
        }
      }
      return json(origin, statusFor(code), { error: code });
    }
  };
}
