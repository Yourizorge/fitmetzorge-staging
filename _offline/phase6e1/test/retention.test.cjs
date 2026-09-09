"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const { plan, DAY } = require("../retention.cjs");
const record = (cls, extra = {}) => ({ id: "syn-record", class: cls, created_at_ms: 0, closed_at_ms: null,
  necessary: true, details_present: true, ...extra });
for (const [cls, days, closed] of [["episode_counter", 30, null], ["closed_details", 90, 10 * DAY], ["minimal_audit", 180, null]]) {
  for (const delta of [-1, 0, 1]) test("E01 exact " + cls + " boundary " + delta, () => {
    const at = (closed || 0) + days * DAY + delta;
    const r = plan([record(cls, { closed_at_ms: closed })], at);
    assert.equal(r.items[0].disposition, delta < 0 ? "within_provisional_cap" : "expire_in_projection");
    assert.equal(r.items[0].expires_at_ms, (closed || 0) + days * DAY);
    assert.equal(r.medical_clearance, false); assert.equal(r.cleanup_performed, false);
  });
}
for (const days of [0, 31, 181, 36500]) test("E02 owner O5 replaces historically open cap at day " + days, () => {
  const r = plan([record("unresolved_signal")], days * DAY);
  assert.equal(r.items[0].disposition, days < 30 ? "within_provisional_cap" : "expire_in_projection");
  assert.equal(r.items[0].expires_at_ms, 30 * DAY);
  assert.equal(r.items[0].projected_details_present, false);
  assert.equal(r.unresolved_max_days, 30); assert.equal(r.storage_enabled, false);
  assert.equal(r.permanent_health_access_block, false);
});
test("E03 expired/missing details preserve no false clearance and no lifetime content block", () => {
  const records = [record("closed_details", { closed_at_ms: 0 }), record("minimal_audit", { id: "syn-audit", details_present: false })];
  const original = JSON.stringify(records);
  const r = plan(records, 181 * DAY);
  assert.ok(r.items.every(i => i.missing_data_state === "missing_context_not_clearance"));
  assert.equal(JSON.stringify(records), original);
  assert.equal(r.bounded_descriptive_content, "still_available_under_authority");
  assert.equal(r.storage_writes, 0); assert.equal(r.medical_clearance, false);
});
test("E04 necessity precedes unresolved storage; no storage activated", () => {
  const r = plan([record("unresolved_signal", { necessary: false })], 1);
  assert.equal(r.items[0].disposition, "omit_unnecessary");
  assert.equal(r.storage_enabled, false);
});
test("E04 optional shorter cap allowed; increases invalid", () => {
  assert.equal(plan([record("episode_counter")], DAY, { episode_counter: 1, closed_details: 80, minimal_audit: 100 }).items[0].disposition, "expire_in_projection");
  assert.equal(plan([], 0, { episode_counter: 31, closed_details: 90, minimal_audit: 180 }).status, "invalid_input");
});
test("E01 unclosed detail is unresolved, not a 90-day or indefinite-retain default", () => {
  const r = plan([record("closed_details")], 1000 * DAY);
  assert.equal(r.items[0].disposition, "expire_in_projection");
  assert.equal(r.items[0].expires_at_ms, 30 * DAY);
});
test("E04 malformed, duplicate, future or live records rejected", () => {
  for (const records of [[record("unknown")], [record("episode_counter"), record("episode_counter")],
    [record("episode_counter", { created_at_ms: 2 })], [record("episode_counter", { id: "member-1" })],
    [record("minimal_audit", { text: "do not store raw text here" })]]) {
    assert.equal(plan(records, 1).status, "invalid_input");
  }
});
