"use strict";
const { contract, exact, rank, validateAssessment } = require("./engine.cjs");
const syntheticId = value => typeof value === "string" && /^syn-[a-z0-9-]{1,64}$/.test(value);
const time = value => Number.isSafeInteger(value) && value >= 0;
const stateKeys = ["contract_version", "subject_id", "revision", "clock_ms", "events",
  "requests", "self_reported_revision", "unknown_after_deletion", "automatic_actions_allowed"];
function createState(subjectId) {
  if (!syntheticId(subjectId)) throw new Error("synthetic_subject_required");
  return { contract_version: contract.version, subject_id: subjectId, revision: 0, clock_ms: 0,
    events: [], requests: [], self_reported_revision: null, unknown_after_deletion: false,
    automatic_actions_allowed: false };
}
function validateState(state) {
  return exact(state, stateKeys) && state.contract_version === contract.version &&
    syntheticId(state.subject_id) && Number.isSafeInteger(state.revision) && state.revision >= 0 &&
    time(state.clock_ms) && Array.isArray(state.events) && state.events.length <= 128 &&
    new Set(state.events.map(event => event?.id)).size === state.events.length &&
    new Set(state.events.map(event => event?.revision)).size === state.events.length &&
    state.events.every(event => exact(event, ["id", "revision", "occurred_at_ms", "help_level", "signal_codes", "evaluation_state"]) &&
      syntheticId(event.id) && Number.isSafeInteger(event.revision) && event.revision > 0 &&
      event.revision <= state.revision && time(event.occurred_at_ms) && event.occurred_at_ms <= state.clock_ms &&
      [null, "R1", "R2", "R3", "R4"].includes(event.help_level) && Array.isArray(event.signal_codes) &&
      event.signal_codes.every(code => require("./rules.json").some(rule => rule.code === code)) &&
      new Set(event.signal_codes).size === event.signal_codes.length &&
      ["known", "uncertain", "unavailable"].includes(event.evaluation_state)) &&
    Array.isArray(state.requests) && state.requests.length <= 256 &&
    new Set(state.requests.map(request => request?.id)).size === state.requests.length &&
    state.requests.every(request => exact(request, ["id", "signature"]) && syntheticId(request.id) &&
      typeof request.signature === "string" && request.signature.length <= 5000) &&
    (state.self_reported_revision === null || (Number.isSafeInteger(state.self_reported_revision) &&
      state.self_reported_revision >= 0 && state.self_reported_revision <= state.revision)) &&
    typeof state.unknown_after_deletion === "boolean" && state.automatic_actions_allowed === false;
}
function recoveryStatus(state) {
  if (!validateState(state)) return "invalid_state";
  if (state.unknown_after_deletion || state.events.some(event => event.help_level === null || event.evaluation_state !== "known")) return "unresolved_review_required";
  if (state.events.some(event => rank(event.help_level) >= 3)) return "serious_recovery_review_required";
  if (state.self_reported_revision === state.revision && state.events.length) return "normal_read_only_review_candidate";
  return state.events.length ? "self_report_not_recorded" : "no_prior_signal";
}
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
  return value;
}
function transition(state, event) {
  const fail = code => ({ status: code, state, medical_clearance: false, automatic_actions_allowed: false });
  if (!validateState(state)) return fail("invalid_state");
  const baseKeys = ["type", "subject_id", "request_id", "expected_revision", "at_ms"];
  const signal = event?.type === "signal", report = event?.type === "self_report";
  const keys = [...baseKeys, ...(signal || report ? ["assessment"] : []), ...(report ? ["method", "confirmed"] : [])];
  if (!exact(event, keys) || !["signal", "self_report", "new_conversation", "delete_conversation", "delete_details", "retention_tick"].includes(event.type) ||
    !syntheticId(event.subject_id) || !syntheticId(event.request_id) || !time(event.at_ms) ||
    !Number.isSafeInteger(event.expected_revision) || event.expected_revision < 0 ||
    ((signal || report) && !validateAssessment(event.assessment)) ||
    (report && (!["confirmation", "chat"].includes(event.method) || typeof event.confirmed !== "boolean"))) return fail("invalid_event");
  if (event.subject_id !== state.subject_id) return fail("subject_mismatch");
  const signature = JSON.stringify(canonical(event));
  const previous = state.requests.find(request => request.id === event.request_id);
  if (previous) return fail(previous.signature === signature ? "replay_no_change" : "request_conflict");
  if (event.expected_revision !== state.revision) return fail("stale_revision");
  if (event.at_ms < state.clock_ms) return fail("out_of_order_event");
  if (event.type !== "delete_details" && (state.requests.length >= 256 || state.events.length >= 128)) return fail("offline_capacity_review_required");
  const next = structuredClone(state);
  const assessment = event.assessment;
  let status = "no_release";
  const recognized = assessment && (rank(assessment.help_level) >= 1 || assessment.evaluation_state !== "known");
  if ((signal || report) && recognized) {
    next.revision++;
    next.self_reported_revision = null;
    next.events.push({ id: event.request_id, revision: next.revision, occurred_at_ms: event.at_ms,
      help_level: assessment.help_level === "R0" ? null : assessment.help_level,
      signal_codes: [...assessment.signal_codes], evaluation_state: assessment.evaluation_state });
    status = report ? "recovery_rejected_new_or_uncertain_signal" : "signal_recorded";
  } else if (report) {
    if (!event.confirmed || (event.method === "chat" && assessment.recovery_intent !== "symptoms_resolved") ||
      assessment.recovery_intent === "disputed") return fail("explicit_self_report_required");
    next.self_reported_revision = next.revision;
    status = "self_report_recorded_not_clearance";
  } else if (event.type === "delete_details") {
    // Deletion is not recovery. No real deletion or lifetime state policy is implemented here.
    next.events = [];
    next.requests = [];
    next.unknown_after_deletion = state.events.length > 0 || state.unknown_after_deletion;
    next.revision++;
    next.self_reported_revision = null;
    status = "synthetic_details_removed_status_unresolved";
  }
  next.clock_ms = event.at_ms;
  next.requests.push({ id: event.request_id, signature });
  if (!validateState(next)) throw new Error("offline_state_defect");
  return { status, state: next, recovery_status: recoveryStatus(next), medical_clearance: false,
    automatic_actions_allowed: false };
}
module.exports = { createState, validateState, transition, recoveryStatus };
