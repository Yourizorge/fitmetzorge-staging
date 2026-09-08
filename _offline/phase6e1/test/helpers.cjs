"use strict";
const flow = require("../flow.cjs");
const { DAY } = require("../retention.cjs");
const subject = "syn-owner";
const authority = { synthetic_only: true, subject_id: subject, authenticated: true, adult: true,
  ai_entitlement: true, private_chat_consent: true, ai_analysis_consent: true, own_history_access: true };
const copy = x => JSON.parse(JSON.stringify(x));
function event(s, type, body, suffix = String(s.revision + 1)) {
  return { type, subject_id: s.subject_id, event_id: "syn-event-" + suffix, at_ms: s.at_ms + 1, ...body };
}
function message(s, text, locale = "nl", availability = "available") {
  return flow.apply(s, event(s, "message", { expected_revision: s.revision,
    message_id: "syn-message-" + (s.revision + 1), text, locale, availability }));
}
function begin(s, issue = s.issues[0]) {
  return flow.apply(s, event(s, "begin", { expected_revision: s.revision, message_id: issue.message_id,
    source_revision: issue.source_revision, mode: issue.kind === "technical" ? "retry" : "clarify" }));
}
function recover(s, method = "confirmation", text = "", locale = "nl", targets = null) {
  return flow.apply(s, event(s, "self_report", { expected_revision: s.revision,
    targets: targets || s.issues.filter(i => i.kind === "health_report").map(i => ({
      message_id: i.message_id, source_revision: i.source_revision })), method, confirmed: method === "confirmation", text, locale }));
}
function source(kind, start, end, overrides = {}) {
  return { id: "syn-aggregate-" + start + "-" + end, subject_id: subject, kind: "synthetic_aggregate", start_ms: start, end_ms: end,
    coverage: "complete", method: ({ daily: "day_totals_v1", post_workout: "workout_totals_v1", weekly: "week_totals_v1" })[kind],
    ...overrides };
}
function sample(kind = "daily", locale = "nl") {
  const duration = kind === "weekly" ? 7 * DAY : kind === "daily" ? DAY : 3600000;
  const end = 30 * DAY, start = end - duration;
  const rows = kind === "weekly" ? [["completed_workouts", 3, "count", 3], ["training_minutes", 105, "min", 90]] :
    kind === "post_workout" ? [["duration_minutes", 35, "min", 30], ["completed_sets", 12, "count", 10], ["completed_reps", 96, "count", 80]] :
    [["completed_workouts", 1, "count", 1], ["training_minutes", 35, "min", 30], ["steps", 6000, "count", 5000]];
  return { synthetic_only: true, subject_id: subject, kind, locale, time_basis: "synthetic_utc", window: { start_ms: start, end_ms: end },
    facts: rows.map(([code, value, unit, previous]) => ({ code, value, unit, source: source(kind, start, end),
      previous: { value: previous, unit, source: source(kind, start - duration, start) } })) };
}
module.exports = { subject, authority, copy, event, message, begin, recover, source, sample, DAY };
