"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { createState, validateState, transition, recoveryStatus } = require("../state.cjs");
const { boundedAnalysis } = require("../engine.cjs");
const { assess, authority } = require("./helpers.cjs");
const event = (state, type, patch = {}) => ({ type, subject_id: state.subject_id,
  request_id: "syn-request-" + state.clock_ms, expected_revision: state.revision,
  at_ms: state.clock_ms + 1, ...patch });
const signal = (state, text = "Ik ben duizelig") =>
  transition(state, event(state, "signal", { assessment: assess(text) }));
const report = (state, patch = {}) => transition(state, event(state, "self_report", {
  assessment: assess("Het gaat weer goed"), method: "chat", confirmed: true, ...patch }));
function signalled(text) { return signal(createState("syn-person-a"), text).state; }

test("strict synthetic identity and initial state", () => {
  assert.throws(() => createState("real-member"), /synthetic_subject_required/);
  assert.equal(validateState(createState("syn-person-a")), true);
  assert.equal(recoveryStatus(createState("syn-person-a")), "no_prior_signal");
});
test("state is immutable and contains no source message or provider output", () => {
  const original = createState("syn-person-a"), before = structuredClone(original);
  const result = signal(original);
  assert.deepEqual(original, before);
  assert.equal(result.status, "signal_recorded");
  assert.equal(result.state.revision, 1);
  assert.equal(JSON.stringify(result.state).includes("Ik ben"), false);
  assert.equal(result.automatic_actions_allowed, false);
});
test("explicit low-level recovery is only a read-only review candidate", () => {
  const result = report(signalled());
  assert.equal(result.status, "self_report_recorded_not_clearance");
  assert.equal(result.recovery_status, "normal_read_only_review_candidate");
  assert.equal(result.medical_clearance, false);
  assert.equal(result.automatic_actions_allowed, false);
});
test("confirmation method requires deliberate affirmation, not a phrase match", () => {
  assert.equal(report(signalled(), { method: "confirmation", assessment: assess("Vandaag rust ik") }).status,
    "self_report_recorded_not_clearance");
});
for (const patch of [
  { confirmed: false }, { assessment: assess("Hallo") },
  { assessment: assess("Het is niet zo dat het gaat weer goed") },
  { assessment: assess("Het gaat weer goed?") },
  { assessment: assess("Je hebt mij verkeerd begrepen") },
  { assessment: assess('Citaat: "Het gaat weer goed"') },
  { assessment: assess("Stel dat het gaat weer goed") },
  { assessment: assess("Gisteren het gaat weer goed") },
  { assessment: assess("Mijn partner: het gaat weer goed") },
  { assessment: assess("Het gaat weer goed", "nl", { context: { subject: "other", timing: "current" } }) }
]) test("non-affirmative recovery never releases: " + JSON.stringify(patch), () => {
  const result = report(signalled(), patch);
  assert.notEqual(result.recovery_status, "normal_read_only_review_candidate");
  assert.equal(result.automatic_actions_allowed, false);
});
for (const text of ["Ik heb pijn op de borst", "Ik kan niet ademen"]) {
  test("serious self-report remains an open review condition: " + text, () => {
    const result = report(signalled(text));
    assert.equal(result.status, "self_report_recorded_not_clearance");
    assert.equal(result.recovery_status, "serious_recovery_review_required");
    const view = boundedAnalysis({ synthetic_only: true, kind: "weekly",
      facts: [{ code: "completed_workouts", value: 2 }] }, assess(text), authority);
    assert.equal(view.access.new_analysis, true);
    assert.equal(view.facts.length, 1);
    assert.deepEqual(view.advice, []);
  });
}
test("uncertainty cannot be erased by a later simple self-report", () => {
  const result = report(signalled("Geen duizeligheid, maar nu ben ik duizelig"));
  assert.equal(result.recovery_status, "unresolved_review_required");
});
for (const text of ["Het gaat weer goed, maar nu heb ik pijn op de borst",
  "Mijn keel zwelt op. Het gaat weer goed", "Ik heb onbekende klachten"]) {
  test("recovery containing new or uncertain symptoms records a new revision: " + text, () => {
    const start = signalled();
    const result = report(start, { assessment: assess(text) });
    assert.equal(result.status, "recovery_rejected_new_or_uncertain_signal");
    assert.equal(result.state.revision, start.revision + 1);
    assert.equal(result.state.self_reported_revision, null);
  });
}
test("recurrence after self-report invalidates the old report", () => {
  const recovered = report(signalled()).state;
  const result = signal(recovered);
  assert.equal(result.state.revision, recovered.revision + 1);
  assert.equal(result.state.self_reported_revision, null);
  assert.equal(result.recovery_status, "self_report_not_recorded");
});
for (const type of ["new_conversation", "delete_conversation", "retention_tick"]) {
  test(type + " never releases a prior signal even after long synthetic time", () => {
    const start = signalled("Ik heb pijn op de borst");
    const result = transition(start, event(start, type, { at_ms: 1000 * 86400000 }));
    assert.equal(result.status, "no_release");
    assert.equal(result.state.revision, start.revision);
    assert.equal(result.recovery_status, "serious_recovery_review_required");
    assert.deepEqual(result.state.events, start.events);
  });
}
test("synthetic deletion removes event/journal metadata but not uncertainty", () => {
  const start = signalled();
  const deleted = transition(start, event(start, "delete_details")).state;
  assert.deepEqual(deleted.events, []);
  assert.equal(deleted.requests.length, 1);
  assert.equal(JSON.stringify(deleted).includes("dizziness"), false);
  assert.equal(deleted.unknown_after_deletion, true);
  assert.equal(report(deleted).recovery_status, "unresolved_review_required");
  assert.equal(signal(deleted).recovery_status, "unresolved_review_required");
});
test("replay is idempotent; reused request identity with another payload conflicts", () => {
  const start = createState("syn-person-a");
  const request = event(start, "signal", { assessment: assess("Ik ben duizelig") });
  const first = transition(start, request);
  assert.equal(transition(first.state, request).status, "replay_no_change");
  assert.equal(transition(first.state, { ...request, at_ms: 4 }).status, "request_conflict");
});
test("concurrent and cross-subject requests cannot write the wrong revision", () => {
  const start = signalled();
  assert.equal(transition(start, event(start, "new_conversation",
    { subject_id: "syn-person-b" })).status, "subject_mismatch");
  assert.equal(transition(start, event(start, "new_conversation",
    { expected_revision: 0 })).status, "stale_revision");
  assert.equal(transition(start, event(start, "new_conversation",
    { at_ms: 0 })).status, "out_of_order_event");
});
for (const patch of [{ surprise: true }, { at_ms: NaN }, { at_ms: -1 },
  { expected_revision: 0.5 }, { type: "release_actions" }, { request_id: "member-real" }]) {
  test("malformed transition rejected: " + JSON.stringify(patch), () => {
    const start = signalled();
    const result = transition(start, event(start, "new_conversation", patch));
    assert.equal(result.status, "invalid_event");
    assert.strictEqual(result.state, start);
  });
}
for (const patch of [{ extra: true }, { automatic_actions_allowed: true }, { revision: -1 },
  { events: [null] }, { requests: [{ id: "syn-a", signature: "" }, { id: "syn-a", signature: "" }] }]) {
  test("malformed state rejected: " + JSON.stringify(patch), () => {
    const state = { ...createState("syn-person-a"), ...patch };
    assert.equal(validateState(state), false);
    assert.equal(transition(state, {}).status, "invalid_state");
  });
}
test("capacity is bounded and does not prevent synthetic deletion", () => {
  let state = createState("syn-person-a");
  for (let i = 0; i < 128; i++) state = signal(state).state;
  assert.equal(signal(state).status, "offline_capacity_review_required");
  const result = transition(state, event(state, "delete_details"));
  assert.equal(result.status, "synthetic_details_removed_status_unresolved");
  assert.equal(result.state.events.length, 0);
});
