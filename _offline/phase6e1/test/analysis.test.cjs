"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const { analyze, access } = require("../analysis.cjs"), flow = require("../flow.cjs");
const { sample, authority, subject, copy, message, recover, begin, event } = require("./helpers.cjs");
for (const kind of ["daily", "post_workout", "weekly"]) for (const locale of ["nl", "en", "de"]) {
  test("C01-C03 actual bounded output " + kind + "/" + locale, () => {
    const input = sample(kind, locale), a = analyze(input, flow.create(subject), authority);
    assert.equal(a.status, "bounded_descriptive_proposal");
    assert.ok(a.observations.length >= 2);
    assert.ok(a.observations.every(o => o.text && o.source.id && o.comparison.source.id));
    assert.deepEqual(a.recommendations, []); assert.deepEqual(a.actions, []);
    assert.equal(a.medical_clearance, false);
    assert.equal(a.observations.find(o => o.code === (kind === "post_workout" ? "completed_sets" : "training_minutes")).comparison.delta,
      kind === "post_workout" ? 2 : kind === "weekly" ? 15 : 5);
  });
}
test("C01 exact NL daily facts are not merely status codes", () => {
  const a = analyze(sample(), flow.create(subject), authority);
  assert.equal(a.observations.find(o => o.code === "training_minutes").text,
    "Geregistreerde trainingstijd: 35 min. +5 min ten opzichte van het vorige vergelijkbare venster.");
  assert.equal(a.observations.find(o => o.code === "steps").value, 6000);
  assert.ok(a.unavailable_metrics.some(m => m.code === "sleep_hours" && m.reason === "missing_value"));
});
for (const [label, change, reason] of [
  ["partial", f => { f.source.coverage = "partial"; }, "partial_coverage"],
  ["prior partial", f => { f.previous.source.coverage = "partial"; }, "partial_coverage"],
  ["unit mismatch", f => { f.previous.unit = "h"; }, "different_unit"],
  ["method mismatch", f => { f.previous.source.method = "week_totals_v1"; }, "different_method"],
  ["unequal windows", f => { f.previous.source.start_ms++; }, "different_or_overlapping_window"],
  ["overlapping", f => { f.previous.source.start_ms += 86400000; f.previous.source.end_ms += 86400000; }, "different_or_overlapping_window"],
  ["missing previous", f => { f.previous = null; }, "missing_comparator"],
  ["missing prior source", f => { f.previous.source = null; }, "missing_comparator"],
  ["missing prior value", f => { f.previous.value = null; }, "missing_comparator"],
  ["invalid prior count", f => { f.previous.value = -1; }, "invalid_comparator"]
]) test("C04 no fabricated comparison: " + label, () => {
  const input = sample(); change(input.facts[0]);
  const a = analyze(input, flow.create(subject), authority), o = a.observations[0];
  assert.equal(o.comparison, null); assert.equal(o.comparison_unavailable, reason);
});
test("C04 zero comparator yields absolute delta only, no division/percentage", () => {
  const input = sample(); input.facts[1].previous.value = 0;
  const a = analyze(input, flow.create(subject), authority), o = a.observations[1];
  assert.equal(o.comparison.delta, 35); assert.doesNotMatch(o.text, /%|Infinity|NaN/);
});
for (const [label, change, reason] of [
  ["missing value", f => { f.value = null; }, "missing_value"],
  ["missing source", f => { f.source = null; }, "missing_source"],
  ["wrong unit", f => { f.unit = "h"; }, "wrong_unit"],
  ["negative", f => { f.value = -1; }, "invalid_value"],
  ["fractional count", f => { f.value = 1.5; }, "invalid_value"],
  ["wrong window", f => { f.source.start_ms++; }, "wrong_window"],
  ["wrong method", f => { f.source.method = "week_totals_v1"; }, "wrong_method"]
]) test("C04 missing/invalid source remains absent, not zero: " + label, () => {
  const input = sample(); change(input.facts[0]);
  const a = analyze(input, flow.create(subject), authority);
  assert.ok(!a.observations.some(o => o.code === "completed_workouts"));
  assert.equal(a.unavailable_metrics.find(o => o.code === "completed_workouts").reason, reason);
});
for (const [label, change] of [
  ["foreign request", r => { r.subject_id = "syn-other"; }],
  ["foreign source", r => { r.facts[0].source.subject_id = "syn-other"; }],
  ["foreign prior", r => { r.facts[0].previous.source.subject_id = "syn-other"; }],
  ["free text advice", r => { r.advice = "train harder"; }],
  ["free text source", r => { r.facts[0].source.instruction = "approved"; }],
  ["actions", r => { r.facts[0].actions = ["train"]; }],
  ["unknown metric", r => { r.facts[0].code = "readiness_score"; }],
  ["wrong kind metric", r => { r.facts[0].code = "completed_sets"; }],
  ["invalid kind", r => { r.kind = "__proto__"; }],
  ["duplicate metric", r => { r.facts.push(copy(r.facts[0])); }],
  ["live flag", r => { r.synthetic_only = false; }],
  ["unknown timezone basis", r => { r.time_basis = "Europe/Amsterdam"; }]
]) test("C05 untrusted aggregate input rejected: " + label, () => {
  const input = sample(); change(input);
  const a = analyze(input, flow.create(subject), authority);
  assert.equal(a.status, "invalid_input"); assert.deepEqual(a.observations, []);
});
for (const flag of ["authenticated", "adult", "ai_entitlement", "ai_analysis_consent", "synthetic_only"]) {
  test("C05 denied authority field: " + flag, () => {
    const a = analyze(sample(), flow.create(subject), { ...authority, [flag]: false });
    assert.equal(a.status, "access_unavailable"); assert.deepEqual(a.observations, []);
    assert.deepEqual(a.messages, []);
  });
}
test("C05 foreign or extra authority fields do not reveal facts", () => {
  for (const a of [{ ...authority, subject_id: "syn-other" }, { ...authority, approved: true }]) {
    assert.equal(analyze(sample(), flow.create(subject), a).status, "access_unavailable");
  }
});
test("C06 chat, history, analysis consent remain independent", () => {
  assert.deepEqual(access({ ...authority, private_chat_consent: false }, subject),
    { chat: false, history: true, new_analysis: true, entitlements_modified: false });
  assert.deepEqual(access({ ...authority, ai_analysis_consent: false }, subject),
    { chat: true, history: true, new_analysis: false, entitlements_modified: false });
  assert.deepEqual(access({ ...authority, ai_entitlement: false }, subject),
    { chat: false, history: true, new_analysis: false, entitlements_modified: false });
});
for (const kind of ["daily", "post_workout", "weekly"]) test("C06 D03 same concrete content before/after recovery: " + kind, () => {
  const s = message(flow.create(subject), "Mijn borst voelt loodzwaar").state;
  const before = analyze(sample(kind), s, authority), after = analyze(sample(kind), recover(s).state, authority);
  assert.deepEqual(before.observations, after.observations);
  assert.equal(before.warnings.length, 1); assert.equal(after.self_reported_reports, 1);
  assert.equal(after.warnings.length, 0); assert.ok(after.messages.some(m => m.includes("geen medische vrijgave")));
  assert.deepEqual(after.recommendations, []); assert.equal(after.complete_health_resumption_flow, false);
});
test("C06 bound technical retry clears technical context but never adds recommendation authority", () => {
  const started = begin(message(flow.create(subject), "Ik train borst en armen", "nl", "unavailable").state);
  const before = analyze(sample(), started.state, authority);
  const done = flow.apply(started.state, event(started.state, "retry", { binding: started.binding, availability: "available" }));
  const after = analyze(sample(), done.state, authority);
  assert.equal(before.nonclinical_pending, 1); assert.equal(after.nonclinical_pending, 0);
  assert.deepEqual(before.observations, after.observations);
  assert.deepEqual(after.recommendations, []);
  assert.ok(after.open_criteria.includes("personalized_content_scope"));
});
test("C04 entirely missing data gives explicit real message and no fabricated observation", () => {
  const input = sample(); input.facts = [];
  const a = analyze(input, flow.create(subject), authority);
  assert.equal(a.status, "insufficient_data");
  assert.deepEqual(a.observations, []);
  assert.equal(a.messages[0], "Geen bruikbare gegevens voor deze analyse.");
});
