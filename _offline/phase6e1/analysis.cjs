"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const { exact, id, integer, freeze, locales } = require("./common.cjs");
const { isState, view } = require("./flow.cjs");
const contract = freeze(require("./content-contract.json"));
const authorityFields = ["synthetic_only", "subject_id", "authenticated", "adult", "ai_entitlement",
  "private_chat_consent", "ai_analysis_consent", "own_history_access"];
function access(a, subjectId) {
  const valid = exact(a, authorityFields) && a.synthetic_only === true && id(a.subject_id) && a.subject_id === subjectId &&
    authorityFields.filter(k => k !== "subject_id").every(k => typeof a[k] === "boolean");
  const base = valid && a.authenticated && a.adult && a.ai_entitlement;
  return freeze({ chat: Boolean(base && a.private_chat_consent),
    history: Boolean(valid && a.authenticated && a.own_history_access),
    new_analysis: Boolean(base && a.ai_analysis_consent), entitlements_modified: false });
}
function numeric(value, locale) {
  const n = Math.round((value + Number.EPSILON) * 100) / 100;
  return String(n).replace(".", locale === "en" ? "." : ",");
}
const copy = {
  nl: { partial: "Onvolledige registratie.", missing: "Geen bruikbare registratie voor", unavailable: "Geen bruikbare gegevens voor deze analyse.",
    comparison: "ten opzichte van het vorige vergelijkbare venster", none: "Geen vergelijkbaar vorig venster.",
    scope: "Dit zijn beschrijvende registraties, geen trainingsadvies of medische vrijgave.",
    policy: "Persoonlijke aanbevelingen en de voorwaarden voor hervatting zijn nog niet uitgewerkt. Er bestaat geen beoordelingsdienst.",
    recovered: "Je meldt dat de klachten voorbij zijn. Dit is jouw verklaring, geen medische vrijgave." },
  en: { partial: "Incomplete recording.", missing: "No usable recording for", unavailable: "No usable data for this analysis.",
    comparison: "compared with the previous comparable window", none: "No comparable previous window.",
    scope: "These are descriptive records, not training advice or medical clearance.",
    policy: "Personalized recommendations and resumption criteria are not yet defined. There is no review service.",
    recovered: "You report that the symptoms have ended. This is your statement, not medical clearance." },
  de: { partial: "Unvollstaendige Erfassung.", missing: "Keine verwendbare Erfassung fuer", unavailable: "Keine verwendbaren Daten fuer diese Analyse.",
    comparison: "gegenueber dem vorherigen vergleichbaren Zeitraum", none: "Kein vergleichbarer vorheriger Zeitraum.",
    scope: "Dies sind beschreibende Aufzeichnungen, keine Trainingsempfehlung oder medizinische Freigabe.",
    policy: "Persoenliche Empfehlungen und Voraussetzungen fuer die Wiederaufnahme sind noch nicht festgelegt. Es gibt keinen Beurteilungsdienst.",
    recovered: "Du meldest, dass die Beschwerden vorbei sind. Das ist deine Aussage, keine medizinische Freigabe." }
};
function sourceValid(s, subject) {
  return exact(s, ["id", "subject_id", "kind", "start_ms", "end_ms", "coverage", "method"]) && id(s.id) &&
    s.subject_id === subject && s.kind === "synthetic_aggregate" && integer(s.start_ms) &&
    integer(s.end_ms) && s.end_ms > s.start_ms && ["complete", "partial"].includes(s.coverage) &&
    ["day_totals_v1", "workout_totals_v1", "week_totals_v1"].includes(s.method);
}
function valueValid(v, metric, window) {
  return typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= 1000000000 &&
    (!metric.integer || Number.isInteger(v)) &&
    (metric.unit !== "min" || v <= window / 60000) && (metric.unit !== "h" || v <= window / 3600000);
}
function analyze(request, state, authority) {
  if (!isState(state)) throw Error("issued_synthetic_state_required");
  const permission = access(authority, state.subject_id);
  const base = { version: contract.version, access: permission, observations: [], unavailable_metrics: [],
    recommendations: [], actions: [], medical_clearance: false, automatic_actions_allowed: false,
    provider_calls: 0, trainer_sharing: false, runtime_execution: false };
  const invalid = () => freeze({ ...base, status: "invalid_input", messages: [] });
  if (!exact(request, ["synthetic_only", "subject_id", "kind", "locale", "time_basis", "window", "facts"]) ||
      request.synthetic_only !== true || request.subject_id !== state.subject_id || !Object.hasOwn(contract.kinds, request.kind) ||
      !locales.includes(request.locale) || request.time_basis !== "synthetic_utc" ||
      !exact(request.window, ["start_ms", "end_ms"]) || !integer(request.window.start_ms) ||
      !integer(request.window.end_ms) || request.window.end_ms <= request.window.start_ms ||
      !Array.isArray(request.facts) || request.facts.length > 8) return invalid();
  const k = contract.kinds[request.kind], duration = request.window.end_ms - request.window.start_ms;
  if ((k.window_ms !== null && duration !== k.window_ms) || (k.window_ms === null && duration > 86400000)) return invalid();
  if (request.facts.some(f => !exact(f, ["code", "value", "unit", "source", "previous"]) || !k.metrics.includes(f.code) ||
      (f.source !== null && !sourceValid(f.source, state.subject_id)) ||
      (f.previous !== null && (!exact(f.previous, ["value", "unit", "source"]) ||
      (f.previous.source !== null && !sourceValid(f.previous.source, state.subject_id))))) ||
      new Set(request.facts.map(f => f.code)).size !== request.facts.length) return invalid();
  if (!permission.new_analysis) return freeze({ ...base, status: "access_unavailable", messages: [] });
  const locale = request.locale, c = copy[locale], observations = [], unavailable = [];
  for (const code of k.metrics) {
    const f = request.facts.find(f => f.code === code), metric = contract.metrics[code];
    let reason = !f || f.value === null ? "missing_value" : f.source === null ? "missing_source" :
      f.unit !== metric.unit ? "wrong_unit" :
      !valueValid(f.value, metric, duration) ? "invalid_value" :
      f.source.method !== k.method ? "wrong_method" :
      f.source.start_ms !== request.window.start_ms || f.source.end_ms !== request.window.end_ms ? "wrong_window" : null;
    if (reason) { unavailable.push({ code, reason, text: c.missing + " " + metric.label[locale].toLowerCase() + "." }); continue; }
    const p = f.previous, ps = p?.source;
    let comparisonReason = !p || p.value === null || !ps ? "missing_comparator" :
      p.unit !== f.unit ? "different_unit" :
      ps.method !== f.source.method ? "different_method" :
      ps.end_ms - ps.start_ms !== duration || ps.end_ms > f.source.start_ms ? "different_or_overlapping_window" :
      ps.coverage !== "complete" || f.source.coverage !== "complete" ? "partial_coverage" :
      !valueValid(p.value, metric, duration) ? "invalid_comparator" : null;
    const delta = comparisonReason ? null : Math.round((f.value - p.value) * 100) / 100;
    const suffix = metric.unit === "count" ? "" : " " + metric.unit;
    const valueText = metric.label[locale] + ": " + numeric(f.value, locale) + suffix + ".";
    const comparisonText = delta === null ? c.none : (delta > 0 ? "+" : "") + numeric(delta, locale) + suffix + " " + c.comparison + ".";
    observations.push({ code, value: f.value, unit: f.unit, source: { ...f.source },
      comparison: delta === null ? null : { delta, unit: f.unit, source: { ...ps } }, comparison_unavailable: comparisonReason,
      text: valueText + (f.source.coverage === "partial" ? " " + c.partial : "") + " " + comparisonText });
  }
  const flow = view(state);
  return freeze({ ...base, status: observations.length ? "bounded_descriptive_proposal" : "insufficient_data",
    kind: request.kind, window: { ...request.window }, time_basis: request.time_basis, observations,
    unavailable_metrics: unavailable, warnings: flow.warnings, content_boundaries: contract.forbidden_recommendations,
    open_criteria: flow.open_criteria, nonclinical_pending: flow.unresolved_nonclinical.length,
    self_reported_reports: flow.self_reported_reports, complete_health_resumption_flow: false,
    messages: [...(observations.length ? [] : [c.unavailable]), c.scope,
      ...(flow.self_reported_reports ? [c.recovered] : []), c.policy] });
}
module.exports = { access, analyze, contract, copy: freeze(copy) };
