"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const { exact, id, integer, freeze } = require("./common.cjs");
const DAY = 86400000;
const classes = {
  episode_counter: { days: 30, anchor: "created_at_ms", purpose: "rolling descriptive count, no medical recurrence threshold" },
  closed_details: { days: 90, anchor: "closed_at_ms", purpose: "necessary explanation of closed or disputed issue" },
  minimal_audit: { days: 180, anchor: "created_at_ms", purpose: "minimal content-free decision trace" },
  unresolved_signal: { days: null, anchor: null, purpose: "policy not decided; persistence not enabled" }
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
  return freeze({ version: "phase6e1.retention.v1", status: "PROVISIONAL_D5_SIMULATION", evaluated_at_ms: nowMs,
    items: records.map(r => {
      const c = classes[r.class], unresolved = r.class === "unresolved_signal" ||
        (r.class === "closed_details" && r.closed_at_ms === null);
      const expires = unresolved ? null : r[c.anchor] + limits[r.class] * DAY;
      const disposition = !r.necessary ? "omit_unnecessary" : unresolved ? "policy_open_no_persistence" :
        nowMs >= expires ? "expire_in_projection" : "within_provisional_cap";
      return { id: r.id, class: r.class, purpose: c.purpose, disposition, expires_at_ms: expires,
        projected_details_present: r.details_present && ["within_provisional_cap", "policy_open_no_persistence"].includes(disposition),
        missing_data_state: !r.details_present || ["omit_unnecessary", "expire_in_projection"].includes(disposition) ?
          "missing_context_not_clearance" : "details_available_in_memory",
        unresolved_max_days: unresolved ? null : undefined };
    }),
    unresolved_max_days: null, unresolved_responsibility: null,
    storage_enabled: false, storage_writes: 0, cleanup_performed: false,
    medical_clearance: false, automatic_actions_allowed: false, permanent_health_access_block: false,
    bounded_descriptive_content: "still_available_under_authority",
    recommendations: "globally_unimplemented_policy_not_a_persistent_member_block",
    missing_details_next_step: "clarify_available_context_without_fabricating_history_or_clearance",
    policy_open: ["unresolved_maximum_and_responsibility", "missing_detail_consequences"] });
}
module.exports = { DAY, classes: freeze(classes), plan };
