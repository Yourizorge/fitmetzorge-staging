"use strict";
const flow = require("../../phase6e1/flow.cjs"), legacy = require("../../phase6e1/test/helpers.cjs");
const engine = require("../engine.cjs"), prereg = require("../preregistered-cases.json");
const DAY = 86400000, CLOCK = 40 * DAY;
const types = { daily: "daily_record_check", post_workout: "workout_reflection", weekly: "weekly_review" };
const clone = value => JSON.parse(JSON.stringify(value));
function sample(kind, locale) {
  const r = legacy.sample(kind, locale), offset = 10 * DAY;
  r.window.start_ms += offset; r.window.end_ms += offset;
  for (const f of r.facts) {
    f.source.start_ms += offset; f.source.end_ms += offset; f.source.id = "syn-current";
    f.previous.source.start_ms += offset; f.previous.source.end_ms += offset; f.previous.source.id = "syn-previous";
  }
  return r;
}
function vary(r, name) {
  const required = { daily: "training_minutes", post_workout: "completed_sets", weekly: "training_minutes" }[r.kind];
  const row = r.facts.find(f => f.code === required);
  if (name === "sleep_present") r.facts.push({ code: "sleep_hours", value: 8, unit: "h", source: clone(row.source), previous: null });
  if (name === "zero") for (const f of r.facts) { f.value = 0; f.previous.value = 0; }
  if (name === "missing_required") r.facts = r.facts.filter(f => f.code !== required);
  if (name === "partial") row.source.coverage = "partial";
  if (name === "split_sources") r.facts[0].source.id = "syn-split-source";
  if (name === "no_comparator") for (const f of r.facts) f.previous = null;
  if (name === "different_unit") row.previous.unit = "h";
  if (name === "different_method") row.previous.source.method = "workout_totals_v1";
  if (name === "overlap" || name === "nonadjacent") for (const f of r.facts) {
    const shift = name === "overlap" ? DAY : -DAY;
    f.previous.source.start_ms += shift; f.previous.source.end_ms += shift;
  }
  if (name === "lower") row.previous.value = 120;
  if (name === "equal") for (const f of r.facts) f.previous.value = f.value;
  if (name === "empty") r.facts = [];
  if (name === "future") {
    r.window.start_ms += DAY; r.window.end_ms += DAY;
    for (const f of r.facts) for (const s of [f.source, f.previous.source]) { s.start_ms += DAY; s.end_ms += DAY; }
  }
  return r;
}
function setup(c = {}) {
  const kind = c.kind || "daily", locale = c.locale || "nl", scenario = c.scenario || "ordinary";
  let state = flow.create(legacy.subject), clock = CLOCK - 1, previous = null, options = {};
  function apply(type, body) {
    const event = { ...legacy.event(state, type, body), at_ms: ++clock };
    const result = flow.apply(state, event);
    if (result.state === state) throw Error("fixture event rejected: " + result.status);
    state = result.state; return result;
  }
  function send(text, availability = "available") {
    return apply("message", { expected_revision: state.revision, message_id: "syn-message-" + (state.revision + 1), text, locale, availability });
  }
  const ordinary = prereg.normal_messages[locale];
  const firstText = scenario === "unclear" || scenario === "clarified" || scenario === "clarification_other_health" || scenario === "continue_chat" ? "flurbel" :
    ["current", "serious_recovered", "recurring", "new_after_recovery", "technical_retry_health"].includes(scenario) ? "Ik heb borstpijn" :
    ["unclassified", "self_reported", "expired", "expired_fresh", "missing", "missing_fresh", "unnecessary", "unnecessary_fresh"].includes(scenario) ? "Mijn borst voelt loodzwaar" :
    scenario === "historical" ? "Vorige maand had ik borstpijn" :
    scenario === "negated" ? "Ik heb geen pijn op de borst" :
    scenario === "quoted" ? '"Ik heb borstpijn" is een citaat.' : ordinary;
  if (scenario !== "no_message") send(firstText, ["technical", "technical_retry", "technical_retry_health"].includes(scenario) ? "unavailable" : "available");
  else clock = CLOCK;
  if (scenario === "clarification_other_health") send("Ik heb borstpijn");
  if (["self_reported", "serious_recovered", "recurring", "new_after_recovery"].includes(scenario)) {
    apply("self_report", { expected_revision: state.revision,
      targets: state.issues.filter(i => i.kind === "health_report").map(i => ({ message_id: i.message_id, source_revision: i.source_revision })),
      method: "chat", confirmed: false, text: "Mijn klachten zijn voorbij", locale: "nl" });
    if (scenario === "recurring") send("Ik heb borstpijn");
    if (scenario === "new_after_recovery") send("Nu heb ik moeite met ademhalen");
  }
  if (["technical_retry", "technical_retry_health", "clarified", "clarification_other_health"].includes(scenario)) {
    const issue = state.issues.find(i => i.kind !== "health_report"), mode = issue.kind === "technical" ? "retry" : "clarify";
    const attempt = apply("begin", { expected_revision: state.revision, message_id: issue.message_id, source_revision: issue.source_revision, mode });
    apply(mode, mode === "retry" ? { binding: attempt.binding, availability: "available" } :
      { binding: attempt.binding, text: "Ik bedoelde mijn borsttraining met gewichten", locale: "nl" });
  }
  if (scenario === "continue_chat") send(ordinary);
  if (/^(expired|missing|unnecessary)/.test(scenario)) {
    previous = engine.prepare(state, clock);
    if (scenario.startsWith("expired")) clock = CLOCK + 30 * DAY;
    if (scenario.startsWith("missing")) options = { missing_message_ids: [state.messages[0].id] };
    if (scenario.startsWith("unnecessary")) options = { unnecessary_message_ids: [state.messages[0].id] };
    previous = engine.prepare(state, clock, options, previous);
    if (scenario.endsWith("_fresh")) send(ordinary);
  }
  const context = engine.prepare(state, clock, options, previous);
  const request = { synthetic_only: true, type: c.type || types[kind], binding: clone(context.binding),
    analysis: vary(sample(kind, locale), c.variant || "normal") };
  return { state, context, request, authority: clone(legacy.authority), clock, options };
}
module.exports = { setup, sample, vary, clone, types, DAY, CLOCK, legacy, flow, engine };
