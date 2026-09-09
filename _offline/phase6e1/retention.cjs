"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const { exact, id, integer, freeze } = require("./common.cjs");
const { isState } = require("./flow.cjs");
const DAY = 86400000;
const issuedProjections = new WeakSet();
const classes = {
  episode_counter: { days: 30, anchor: "created_at_ms", purpose: "rolling descriptive count, no medical recurrence threshold" },
  closed_details: { days: 90, anchor: "closed_at_ms", purpose: "necessary explanation of closed or disputed issue" },
  minimal_audit: { days: 180, anchor: "created_at_ms", purpose: "minimal content-free decision trace" },
  unresolved_signal: { days: 30, anchor: "created_at_ms", purpose: "follow recent reports and avoid unnecessarily asking for the same context" }
};
function plan(records, nowMs, limits = { episode_counter: 30, closed_details: 90, minimal_audit: 180 }) {
  const invalid = () => freeze({ status: "invalid_input", items: [], storage_writes: 0, cleanup_performed: false, medical_clearance: false });
  if (!Array.isArray(records) || records.length > 256 || !integer(nowMs) ||
      !exact(limits, ["episode_counter", "closed_details", "minimal_audit"]) ||
      Object.entries(limits).some(([k, v]) => !integer(v) || v > classes[k].days)) return invalid();
  if (records.some(r => !exact(r, ["id", "class", "created_at_ms", "closed_at_ms", "necessary", "details_present"]) ||
      !id(r.id) || !Object.hasOwn(classes, r.class) || !integer(r.created_at_ms) || r.created_at_ms > nowMs ||
      (r.closed_at_ms !== null && (!integer(r.closed_at_ms) || r.closed_at_ms < r.created_at_ms || r.closed_at_ms > nowMs)) ||
      typeof r.necessary !== "boolean" || typeof r.details_present !== "boolean") ||
      new Set(records.map(r => r.id)).size !== records.length) return invalid();
  if (records.some(r => !Number.isSafeInteger((r.class === "unresolved_signal" ||
      (r.class === "closed_details" && r.closed_at_ms === null) ? r.created_at_ms + 30 * DAY :
      r[classes[r.class].anchor] + limits[r.class] * DAY)))) return invalid();
  return freeze({ version: "phase6e1.retention.v2", status: "OWNER_ACCEPTED_OFFLINE_D5_SIMULATION", evaluated_at_ms: nowMs,
    items: records.map(r => {
      const c = classes[r.class], unresolved = r.class === "unresolved_signal" ||
        (r.class === "closed_details" && r.closed_at_ms === null);
      const expires = unresolved ? r.created_at_ms + 30 * DAY : r[c.anchor] + limits[r.class] * DAY;
      const disposition = !r.necessary ? "omit_unnecessary" :
        nowMs >= expires ? "expire_in_projection" : "within_provisional_cap";
      return { id: r.id, class: r.class, purpose: c.purpose, disposition, expires_at_ms: expires,
        projected_details_present: !unresolved && r.details_present && disposition === "within_provisional_cap",
        missing_data_state: !r.details_present || ["omit_unnecessary", "expire_in_projection"].includes(disposition) ?
          "missing_context_not_clearance" : "details_available_in_memory",
        unresolved_max_days: unresolved ? 30 : undefined };
    }),
    unresolved_max_days: 30, unresolved_responsibility: "FitMetZorge",
    storage_enabled: false, storage_writes: 0, cleanup_performed: false,
    medical_clearance: false, automatic_actions_allowed: false, permanent_health_access_block: false,
    bounded_descriptive_content: "still_available_under_authority",
    recommendations: "globally_unimplemented_policy_not_a_persistent_member_block",
    missing_details_next_step: "clarify_available_context_without_fabricating_history_or_clearance",
    policy_open: ["legal_privacy_medical_validation", "live_deletion_and_missing_context_integration"] });
}

// Only this minimal projection represents O5 records. Raw flow history and D5
// what-if diagnostics are not storage payloads. A revision watermark avoids
// resurrecting removed records without retaining per-message tombstones.
function projectSafety(state, nowMs, options = {}, previous = null) {
  if (!isState(state)) throw Error("issued_synthetic_state_required");
  if (previous !== null && !issuedProjections.has(previous)) throw Error("issued_safety_projection_required");
  const allowed = ["unnecessary_message_ids", "missing_message_ids"];
  if (!options || !exact(options, Object.keys(options)) ||
      Object.keys(options).some(k => !allowed.includes(k)) || !integer(nowMs) || nowMs < state.at_ms ||
      (previous && (previous.subject_id !== state.subject_id || previous.evaluated_at_ms > nowMs ||
        previous.source_revision > state.revision))) throw Error("invalid_projection");
  const groups = new Map();
  for (const issue of state.issues) {
    const origin = issue.retention_origin;
    if (!origin || !Number.isSafeInteger(origin.first_registered_at_ms + 30 * DAY)) throw Error("invalid_projection");
    const key = origin.message_id + ":" + origin.source_revision;
    if (!groups.has(key)) groups.set(key, { origin, issues: [] });
    groups.get(key).issues.push(issue);
  }
  const sources = new Set([...groups.values()].map(g => g.origin.message_id));
  for (const k of allowed) {
    const ids = Object.hasOwn(options, k) ? options[k] : [];
    if (!Array.isArray(ids) || ids.some(x => !id(x) || !sources.has(x)) ||
        new Set(ids).size !== ids.length) throw Error("invalid_projection");
  }
  const unnecessary = new Set(options.unnecessary_message_ids || []), missing = new Set(options.missing_message_ids || []);
  const prior = new Set((previous?.records || []).map(r => r.message_ref.message_id + ":" + r.message_ref.source_revision));
  const records = [];
  for (const [key, { origin, issues }] of groups) {
    const first = origin.first_registered_at_ms;
    if (unnecessary.has(origin.message_id) || nowMs >= first + 30 * DAY ||
        (previous && !prior.has(key) && origin.source_revision <= previous.source_revision)) continue;
    const active = issues.filter(i => i.status !== "settled" && !i.self_reported);
    const status = missing.has(origin.message_id) ? "context_missing" :
      active.some(i => i.status === "open") ? "open" : active.length ? "awaiting" :
      issues.some(i => i.self_reported) ? "self_reported" : "settled";
    records.push({ first_registered_at_ms: first, status,
      message_ref: { message_id: origin.message_id, source_revision: origin.source_revision } });
  }
  const projection = { version: "phase6e1.retention.v2", subject_id: state.subject_id,
    source_revision: state.revision, evaluated_at_ms: nowMs, records,
    storage_enabled: false, storage_writes: 0, cleanup_performed: false,
    medical_clearance: false, automatic_actions_allowed: false, permanent_health_access_block: false,
    responsibility: "FitMetZorge", maximum_days: 30,
    missing_context_next_step: "ask_current_context_if_needed_without_reconstruction_or_clearance" };
  issuedProjections.add(projection);
  return freeze(projection);
}
module.exports = { DAY, classes: freeze(classes), plan, projectSafety };
