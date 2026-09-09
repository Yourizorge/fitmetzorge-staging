"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const { exact, id, integer, freeze, canonical, normalized, locales } = require("./common.cjs");
const { assess } = require("./context.cjs");
const issued = new WeakSet();
const bindKeys = ["subject_id", "message_id", "source_revision", "issue_revision", "attempt"];
const headers = ["type", "subject_id", "event_id", "at_ms"];
const bodyKeys = {
  message: ["expected_revision", "message_id", "text", "locale", "availability"],
  begin: ["expected_revision", "message_id", "source_revision", "mode"],
  retry: ["binding", "availability"],
  clarify: ["binding", "text", "locale"],
  self_report: ["expected_revision", "targets", "method", "confirmed", "text", "locale"]
};
function affirmativeClarification(text) {
  const value = normalized(text).value.trim();
  const outsideQuotes = value.replace(/"[^"]*"/g, "");
  return /^(?:ik bedoelde|i meant|ich meinte)\b/.test(value) &&
    !/\b(?:niet|not|nicht)\b/.test(outsideQuotes);
}
function seal(s) { issued.add(s); return freeze(s); }
function create(subjectId) {
  if (!id(subjectId)) throw Error("synthetic_subject_required");
  return seal({ version: "phase6e1.flow.v1", subject_id: subjectId, revision: 0, at_ms: 0,
    messages: [], issues: [], events: [], self_reports: [] });
}
const isState = x => issued.has(x);
const clone = s => JSON.parse(JSON.stringify(s));
const response = (status, state, extra = {}) => freeze({ status, state, ...extra,
  medical_clearance: false, automatic_actions_allowed: false, trainer_sharing: false,
  persistence_enabled: false, provider_calls: 0 });
function issueFor(s, messageId, sourceRevision) {
  return s.issues.find(i => i.message_id === messageId && i.source_revision === sourceRevision);
}
function binding(s, i) {
  return { subject_id: s.subject_id, message_id: i.message_id, source_revision: i.source_revision,
    issue_revision: i.issue_revision, attempt: i.attempt };
}
function addMessage(s, messageId, text, locale, availability, atMs, retentionOrigin = null) {
  const assessment = assess({ synthetic_only: true, text, locale, availability });
  s.messages.push({ id: messageId, source_revision: s.revision, at_ms: atMs, text, locale, assessment });
  if (["health_report", "communication", "technical"].includes(assessment.category)) {
    const codes = [...new Set(assessment.trace.filter(t => t.context === "current").map(t => t.signal))];
    s.issues.push({ message_id: messageId, source_revision: s.revision, issue_revision: 0, attempt: 0,
      retention_origin: retentionOrigin || { message_id: messageId, source_revision: s.revision, first_registered_at_ms: atMs },
      kind: assessment.category, status: "open", mode: null, created_at_ms: atMs, closed_at_ms: null,
      level: assessment.level, codes, feedback: assessment.feedback, self_reported: false,
      repeated_signal: assessment.category === "health_report" && s.issues.some(i =>
        i.kind === "health_report" && i.codes.some(c => codes.includes(c))) });
  }
  return assessment;
}
function apply(state, event) {
  if (!isState(state)) throw Error("issued_synthetic_state_required");
  const reject = status => response(status, state);
  if (!event || !Object.hasOwn(bodyKeys, event.type) || !exact(event, [...headers, ...bodyKeys[event.type]]) ||
      event.subject_id !== state.subject_id || !id(event.event_id) || !integer(event.at_ms)) return reject("invalid_event");
  const digest = canonical(event), previous = state.events.find(e => e.id === event.event_id);
  if (previous) return reject(previous.digest === digest ? "duplicate" : "event_id_conflict");
  if (state.messages.some(m => m.id === event.event_id)) return reject("event_message_identity_conflict");
  if (event.at_ms < state.at_ms) return reject("stale_clock");
  if (Object.hasOwn(event, "expected_revision") && event.expected_revision !== state.revision) return reject("stale_revision");
  if (state.events.length >= 256) return reject("synthetic_capacity_reached");
  const s = clone(state); s.revision++; s.at_ms = event.at_ms;
  let status, extra = {};
  if (event.type === "message") {
    if (!id(event.message_id) || s.messages.some(m => m.id === event.message_id) || !locales.includes(event.locale) ||
        typeof event.text !== "string" || event.text.length > 4096 || !["available", "unavailable"].includes(event.availability)) return reject("invalid_message");
    extra.assessment = addMessage(s, event.message_id, event.text, event.locale, event.availability, event.at_ms);
    status = "message_assessed";
  } else if (event.type === "begin") {
    const i = issueFor(s, event.message_id, event.source_revision);
    if (!i || i.status === "settled" || i.kind === "health_report" ||
        !["retry", "clarify"].includes(event.mode) ||
        (i.kind === "technical" ? event.mode !== "retry" : event.mode !== "clarify")) return reject("nonclinical_issue_required");
    i.issue_revision++; i.attempt++; i.mode = event.mode; i.status = "awaiting";
    extra.binding = binding(s, i); status = "attempt_started";
  } else if (event.type === "retry" || event.type === "clarify") {
    const b = event.binding;
    if (!exact(b, bindKeys) || b.subject_id !== s.subject_id) return reject("invalid_binding");
    const i = issueFor(s, b.message_id, b.source_revision);
    if (!i || i.status !== "awaiting" || i.mode !== event.type ||
        canonical(binding(s, i)) !== canonical(b)) return reject("stale_or_wrong_attempt");
    const original = s.messages.find(m => m.id === i.message_id);
    let a;
    if (event.type === "retry") {
      if (!["available", "unavailable"].includes(event.availability)) return reject("invalid_retry");
      a = assess({ synthetic_only: true, text: original.text, locale: original.locale, availability: event.availability });
    } else {
      if (typeof event.text !== "string" || event.text.length > 4096 || !locales.includes(event.locale)) return reject("invalid_clarification");
      a = assess({ synthetic_only: true, text: event.text, locale: event.locale, availability: "available" });
    }
    extra.assessment = a; i.issue_revision++; i.status = "open"; i.mode = null;
    if (a.category === "technical") status = "technical_issue_still_open";
    else if (event.type === "clarify" && a.category === "health_report") {
      addMessage(s, event.event_id, event.text, event.locale, "available", event.at_ms);
      status = "new_health_report_during_clarification";
    } else if (event.type === "clarify" && (!affirmativeClarification(event.text) ||
        !["ordinary", "noncurrent"].includes(a.category) || a.recovery)) status = "clarification_still_open";
    else {
      i.status = "settled"; i.closed_at_ms = event.at_ms;
      status = event.type === "retry" ? "technical_issue_settled" : "communication_issue_settled";
      if (event.type === "retry" && ["health_report", "communication"].includes(a.category)) {
        addMessage(s, event.event_id, original.text, original.locale, "available", event.at_ms, i.retention_origin);
        status = "technical_issue_settled_new_" + a.category;
      }
    }
  } else {
    const targets = event.targets;
    if (!Array.isArray(targets) || !targets.length || targets.length > 256 ||
        targets.some(t => !exact(t, ["message_id", "source_revision"])) ||
        new Set(targets.map(t => canonical(t))).size !== targets.length ||
        targets.some(t => issueFor(s, t.message_id, t.source_revision)?.kind !== "health_report") ||
        !["confirmation", "chat"].includes(event.method) || !locales.includes(event.locale) ||
        typeof event.text !== "string" || event.text.length > 4096 || typeof event.confirmed !== "boolean") return reject("invalid_self_report");
    let a = null;
    if (event.method === "confirmation") {
      if (!event.confirmed || event.text !== "") return reject("explicit_confirmation_required");
    } else {
      if (event.confirmed !== false) return reject("chat_cannot_supply_confirmation");
      a = assess({ synthetic_only: true, text: event.text, locale: event.locale, availability: "available" });
      if (a.category === "health_report") {
        extra.assessment = addMessage(s, event.event_id, event.text, event.locale, "available", event.at_ms);
        status = "recovery_conflict_new_health_report";
      } else if (!a.recovery) return reject("affirmative_self_report_required");
    }
    if (!status) {
      for (const target of targets) {
        const i = issueFor(s, target.message_id, target.source_revision);
        i.self_reported = true; i.issue_revision++; i.self_report_revision = s.revision;
      }
      s.self_reports.push({ revision: s.revision, at_ms: event.at_ms, targets: clone(targets),
        method: event.method, text: event.text, medical_clearance: false });
      status = "self_report_recorded_not_clearance";
    }
  }
  // Revision-bound evidence is retained in memory only; no service, queue or approval is created.
  s.events.push({ id: event.event_id, revision: s.revision, digest, type: event.type });
  return response(status, seal(s), extra);
}
function view(state) {
  if (!isState(state)) throw Error("issued_synthetic_state_required");
  const health = state.issues.filter(i => i.kind === "health_report");
  const current = health.filter(i => !i.self_reported);
  const nonclinical = state.issues.filter(i => i.kind !== "health_report" && i.status !== "settled");
  const open = ["personalized_content_scope"];
  if (health.some(i => i.level === null)) open.push("unclassified_recovery");
  if (health.some(i => ["R3", "R4"].includes(i.level))) open.push("serious_recovery");
  if (health.some(i => i.repeated_signal)) open.push("recurrence_meaning_and_recovery");
  return freeze({ subject_id: state.subject_id, revision: state.revision,
    health_reports: health.length, current_reports: current.length,
    self_reported_reports: health.filter(i => i.self_reported).length,
    unresolved_nonclinical: nonclinical.map(i => binding(state, i)),
    nonclinical_options: nonclinical.map(i => ({ binding: binding(state, i),
      choices: [i.kind === "technical" ? "retry" : "reformulate", "continue_chat"] })),
    clarification_required: false,
    settled_nonclinical: state.issues.filter(i => i.status === "settled").map(i => binding(state, i)),
    warnings: current.map(i => ({ message_id: i.message_id, ...i.feedback })),
    history: health.map(i => ({ message_id: i.message_id, source_revision: i.source_revision,
      self_reported: i.self_reported, repeated_signal: i.repeated_signal, level: i.level, original_warning: i.feedback })),
    content_mode: "bounded_descriptive_proposal", recommendations: [], actions: [],
    open_criteria: open, complete_health_resumption_flow: false, medical_clearance: false,
    permanent_health_access_block: false, human_approval_service: false,
    proposed_next_step: nonclinical.length ? "optional_clarification_or_retry_or_continue_chat" :
      current.length ? "help_and_explicit_self_report_when_applicable" : "bounded_content_with_open_recommendation_policy" });
}
module.exports = { create, apply, view, isState };
