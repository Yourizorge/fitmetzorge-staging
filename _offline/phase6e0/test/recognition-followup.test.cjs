"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const fixtures = require("../recognition-followup-cases.json");
const { assess, authority } = require("./helpers.cjs");
const { validateAssessment, boundedAnalysis, copy, help } = require("../engine.cjs");
const { createState, transition } = require("../state.cjs");

for (const c of fixtures.cases) test("recognition follow-up: " + c.id, () => {
  const actual = assess(c.text, c.locale);
  assert.equal(actual.evaluation_state, c.expected_state, c.text);
  assert.equal(actual.help_level, c.expected_level, c.text);
  if (c.expected_context) assert.ok(actual.context_states.includes(c.expected_context), c.text + " context");
  if (c.expected_state === "uncertain") assert.ok(actual.uncertainty_codes.includes("unrecognized_health_context"));
  assert.equal(actual.medical_clearance, false);
  assert.equal(actual.automatic_actions_allowed, false);
  assert.equal(validateAssessment(actual), true);
  assert.deepEqual(assess(c.text, c.locale), actual);
});

for (const c of fixtures.cases.filter(c => c.kind === "original")) {
  test("original gap access and recovery boundaries: " + c.id, () => {
    const assessment = assess(c.text, c.locale);
    assert.equal(assessment.evaluation_state, "uncertain");
    const facts = boundedAnalysis({ synthetic_only: true, kind: "daily",
      facts: [{ code: "completed_workouts", value: 1 }] }, assessment, authority);
    assert.deepEqual(facts.access, { chat: true, history: true, new_analysis: true, entitlements_modified: false });
    assert.equal(facts.facts.length, 1);
    assert.deepEqual(facts.advice, []);
    assert.deepEqual(facts.actions, []);
    assert.equal(help(assessment, "nl", authority).text, copy.nl.uncertain);
    const before = createState("syn-followup");
    const signal = transition(before, { type: "signal", subject_id: before.subject_id,
      request_id: "syn-signal", expected_revision: 0, at_ms: 1, assessment });
    assert.equal(signal.state.revision, 1);
    const recovered = transition(signal.state, { type: "self_report", subject_id: before.subject_id,
      request_id: "syn-recovery", expected_revision: 1, at_ms: 2, method: "chat",
      confirmed: true, assessment: assess("Het gaat weer goed") });
    assert.equal(recovered.status, "self_report_recorded_not_clearance");
    assert.equal(recovered.recovery_status, "unresolved_review_required");
    assert.equal(recovered.medical_clearance, false);
    assert.equal(recovered.automatic_actions_allowed, false);
  });
}
