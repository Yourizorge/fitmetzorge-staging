"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { DAY, retentionPlan, episodeCount } = require("../retention.cjs");
const row = (kind, patch = {}) => ({ id: "syn-record-a", class: kind, created_at_ms: 0,
  closed_at_ms: kind === "closed_details" ? 10 * DAY : null, necessary: true, ...patch });
for (const [kind, days, anchor] of [["episode_counter", 30, 0], ["closed_details", 90, 10], ["minimal_audit", 180, 0]]) {
  for (const offset of [-1, 0, 1]) test(kind + " exact cutoff " + offset + " ms", () => {
    const source = [row(kind)], before = structuredClone(source);
    const result = retentionPlan(source, (anchor + days) * DAY + offset);
    assert.deepEqual(result[offset < 0 ? "retain_ids" : "delete_ids"], ["syn-record-a"]);
    assert.deepEqual(source, before);
    assert.equal(result.storage_or_cleanup_performed, false);
    assert.equal(result.medical_clearance, false);
    assert.equal(result.automatic_actions_allowed, false);
  });
  test(kind + " unnecessary records have no default retention entitlement", () => {
    assert.deepEqual(retentionPlan([row(kind, { necessary: false })], 10 * DAY).delete_ids, ["syn-record-a"]);
  });
}
for (const kind of ["unresolved_signal", "closed_details"]) {
  for (const necessary of [true, false]) test(kind + " no invented unresolved lifetime: " + necessary, () => {
    const result = retentionPlan([row(kind, { closed_at_ms: null, necessary })], 10000 * DAY);
    assert.deepEqual(result.review_ids, ["syn-record-a"]);
    assert.deepEqual(result.delete_ids, []);
    assert.deepEqual(result.retain_ids, []);
    assert.equal(result.unresolved_owner, null);
    assert.equal(result.unresolved_max_days, null);
  });
}
test("closed details are measured from closure, not event creation", () => {
  assert.deepEqual(retentionPlan([row("closed_details")], 90 * DAY).retain_ids, ["syn-record-a"]);
});
test("owner can propose shorter maxima including zero without enlarging them", () => {
  const limits = { episode_days: 0, closed_days: 1, audit_days: 2 };
  assert.deepEqual(retentionPlan([row("episode_counter")], 0, limits).delete_ids, ["syn-record-a"]);
  assert.deepEqual(retentionPlan([row("closed_details")], 11 * DAY, limits).delete_ids, ["syn-record-a"]);
});
for (const limits of [{ episode_days: 31, closed_days: 90, audit_days: 180 },
  { episode_days: 30, closed_days: 91, audit_days: 180 },
  { episode_days: 30, closed_days: 90, audit_days: 181 },
  { episode_days: -1, closed_days: 90, audit_days: 180 }, { extra: 1 }, null]) {
  test("retention limits reject extension or malformed input: " + JSON.stringify(limits), () => {
    assert.equal(retentionPlan([], 0, limits).status, "invalid_input");
  });
}
for (const patch of [{ id: "real-data" }, { created_at_ms: -1 }, { created_at_ms: 10001 * DAY },
  { created_at_ms: NaN }, { closed_at_ms: -1 }, { class: "chat" }, { class: "analysis" },
  { necessary: "yes" }, { text: "should never be stored" }]) {
  test("retention rejects malformed or out-of-scope record: " + JSON.stringify(patch), () => {
    assert.equal(retentionPlan([row("episode_counter", patch)], 10000 * DAY).status, "invalid_input");
  });
}
test("malformed records, duplicate identities, invalid clocks and capacities rejected", () => {
  for (const records of [null, [null], [row("minimal_audit"), row("minimal_audit")],
    Array.from({ length: 257 }, (_, i) => row("minimal_audit", { id: "syn-" + i }))]) {
    assert.equal(retentionPlan(records, 0).status, "invalid_input");
  }
  for (const clock of [-1, NaN, Infinity, 0.1]) assert.equal(retentionPlan([], clock).status, "invalid_input");
});
test("episode count is a deduplicated 30-day count, never a clinical threshold", () => {
  const events = [{ id: "syn-a", at_ms: 0 }, { id: "syn-b", at_ms: 1 }, { id: "syn-b", at_ms: 1 }];
  const result = episodeCount(events, 30 * DAY);
  assert.equal(result.count, 1);
  assert.equal(result.medical_prediction, false);
  assert.equal(result.automatic_actions_allowed, false);
  assert.equal(episodeCount(events, 30 * DAY + 1).count, 0);
});
test("conflicting episode timestamps are not silently deduplicated", () => {
  assert.equal(episodeCount([{ id: "syn-a", at_ms: 0 }, { id: "syn-a", at_ms: 1 }], 1).status, "identity_conflict");
});
test("episode invalid times, content, identities and absent data are not invented", () => {
  assert.equal(episodeCount([], 0).count, 0);
  for (const rows of [null, [{ id: "real", at_ms: 0 }], [{ id: "syn-a", at_ms: 1 }],
    [{ id: "syn-a", at_ms: -1 }], [{ id: "syn-a", at_ms: 0, content: "not allowed" }]]) {
    assert.equal(episodeCount(rows, 0).status, "invalid_input");
  }
});
