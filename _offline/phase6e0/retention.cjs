"use strict";
const { contract, exact } = require("./engine.cjs");
const DAY = 86400000;
const classes = ["episode_counter", "closed_details", "minimal_audit", "unresolved_signal"];
function retentionPlan(records, nowMs, limits = { episode_days: 30, closed_days: 90, audit_days: 180 }) {
  const invalid = () => ({ status: "invalid_input", delete_ids: [], retain_ids: [], review_ids: [],
    medical_clearance: false, automatic_actions_allowed: false });
  if (!Array.isArray(records) || records.length > 256 || !Number.isSafeInteger(nowMs) || nowMs < 0 ||
    !exact(limits, ["episode_days", "closed_days", "audit_days"]) ||
    !Object.entries(limits).every(([key, value]) => Number.isInteger(value) && value >= 0 &&
      value <= ({ episode_days: 30, closed_days: 90, audit_days: 180 })[key])) return invalid();
  const validTime = value => Number.isSafeInteger(value) && value >= 0 && value <= nowMs;
  const valid = records.every(record => exact(record, ["id", "class", "created_at_ms", "closed_at_ms", "necessary"]) &&
    typeof record.id === "string" && /^syn-[a-z0-9-]{1,64}$/.test(record.id) &&
    classes.includes(record.class) && validTime(record.created_at_ms) &&
    (record.closed_at_ms === null || (validTime(record.closed_at_ms) && record.closed_at_ms >= record.created_at_ms)) &&
    typeof record.necessary === "boolean");
  if (!valid || new Set(records.map(record => record.id)).size !== records.length) return invalid();
  const result = { status: contract.retention.policy_status, synthetic_only: true, evaluated_at_ms: nowMs,
    delete_ids: [], retain_ids: [], review_ids: [], unresolved_owner: null, unresolved_max_days: null,
    medical_clearance: false, automatic_actions_allowed: false, storage_or_cleanup_performed: false };
  for (const record of records) {
    if (record.class === "unresolved_signal" || (record.class === "closed_details" && record.closed_at_ms === null)) {
      result.review_ids.push(record.id);
      continue;
    }
    if (!record.necessary) { result.delete_ids.push(record.id); continue; }
    const start = record.class === "closed_details" ? record.closed_at_ms : record.created_at_ms;
    const days = ({ episode_counter: limits.episode_days, closed_details: limits.closed_days, minimal_audit: limits.audit_days })[record.class];
    result[nowMs - start >= days * DAY ? "delete_ids" : "retain_ids"].push(record.id);
  }
  return result;
}
function episodeCount(events, nowMs) {
  if (!Array.isArray(events) || events.length > 256 || !Number.isSafeInteger(nowMs) || nowMs < 0 ||
    events.some(event => !exact(event, ["id", "at_ms"]) || typeof event.id !== "string" ||
      !/^syn-[a-z0-9-]{1,64}$/.test(event.id) || !Number.isSafeInteger(event.at_ms) || event.at_ms < 0 || event.at_ms > nowMs)) {
    return { status: "invalid_input", count: null };
  }
  const identities = new Map();
  for (const event of events) {
    if (identities.has(event.id) && identities.get(event.id) !== event.at_ms) return { status: "identity_conflict", count: null };
    identities.set(event.id, event.at_ms);
  }
  return { status: "DRAFT_SYNTHETIC_WINDOW", count: [...identities.values()].filter(at => nowMs - at < 30 * DAY).length,
    window_days: 30, medical_prediction: false, automatic_actions_allowed: false };
}
module.exports = { DAY, retentionPlan, episodeCount };
