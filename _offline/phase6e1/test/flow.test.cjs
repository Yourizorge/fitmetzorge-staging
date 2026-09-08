"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const flow = require("../flow.cjs");
const { subject, copy, event, message, begin, recover } = require("./helpers.cjs");
function noMutation(r, state) { assert.equal(r.state, state); assert.equal(r.medical_clearance, false); }
test("B02 technical retry uses original text and retires only technical issue", () => {
  const first = message(flow.create(subject), "Ik heb borstpijn", "nl", "unavailable");
  const started = begin(first.state);
  const r = flow.apply(started.state, event(started.state, "retry", { binding: started.binding, availability: "available" }));
  assert.equal(r.status, "technical_issue_settled_new_health_report");
  assert.equal(flow.view(r.state).unresolved_nonclinical.length, 0);
  assert.equal(flow.view(r.state).current_reports, 1);
  assert.equal(r.assessment.feedback.key, "professional_review");
  assert.equal(r.state.messages[1].text, first.state.messages[0].text);
  assert.equal(r.state.issues[0].status, "settled");
});
for (const field of ["subject_id", "message_id", "source_revision", "issue_revision", "attempt"]) {
  test("B01 rejects wrong binding: " + field, () => {
    const s = begin(message(flow.create(subject), "train", "en", "unavailable").state);
    const b = { ...s.binding, [field]: typeof s.binding[field] === "number" ? s.binding[field] + 1 : "syn-foreign" };
    const r = flow.apply(s.state, event(s.state, "retry", { binding: b, availability: "available" }));
    noMutation(r, s.state); assert.notEqual(r.status, "technical_issue_settled");
  });
}
test("B03 identical retry idempotent; payload conflict rejected; another completion is stale", () => {
  const started = begin(message(flow.create(subject), "train", "en", "unavailable").state);
  const e = event(started.state, "retry", { binding: started.binding, availability: "available" });
  const done = flow.apply(started.state, e);
  assert.equal(done.status, "technical_issue_settled");
  const duplicate = flow.apply(done.state, e);
  assert.equal(duplicate.status, "duplicate"); noMutation(duplicate, done.state);
  const conflict = flow.apply(done.state, { ...e, availability: "unavailable" });
  assert.equal(conflict.status, "event_id_conflict"); noMutation(conflict, done.state);
  const stale = flow.apply(done.state, { ...e, event_id: "syn-other-completion", at_ms: done.state.at_ms + 1 });
  assert.equal(stale.status, "stale_or_wrong_attempt"); noMutation(stale, done.state);
});
test("B04 superseded attempt cannot complete; newest succeeds", () => {
  const one = begin(message(flow.create(subject), "train", "en", "unavailable").state);
  const two = begin(one.state);
  const stale = flow.apply(two.state, event(two.state, "retry", { binding: one.binding, availability: "available" }));
  noMutation(stale, two.state);
  const done = flow.apply(two.state, event(two.state, "retry", { binding: two.binding, availability: "available" }));
  assert.equal(done.status, "technical_issue_settled");
  assert.equal(flow.view(done.state).unresolved_nonclinical.length, 0);
});
test("B04 new complaint during older valid retry survives resolution", () => {
  const started = begin(message(flow.create(subject), "train", "en", "unavailable").state);
  const health = message(started.state, "Mijn borst voelt loodzwaar");
  const done = flow.apply(health.state, event(health.state, "retry", { binding: started.binding, availability: "available" }));
  assert.equal(done.status, "technical_issue_settled");
  assert.equal(flow.view(done.state).current_reports, 1);
  assert.equal(flow.view(done.state).warnings[0].key, "current_unclassified");
});
test("B02 failed retry remains open but can later settle without permanent error", () => {
  let s = begin(message(flow.create(subject), "train", "en", "unavailable").state);
  const failed = flow.apply(s.state, event(s.state, "retry", { binding: s.binding, availability: "unavailable" }));
  assert.equal(failed.status, "technical_issue_still_open");
  s = begin(failed.state);
  const done = flow.apply(s.state, event(s.state, "retry", { binding: s.binding, availability: "available" }));
  assert.equal(flow.view(done.state).unresolved_nonclinical.length, 0);
});
for (const [locale, text] of [["nl", "Ik bedoelde mijn borsttraining met gewichten"], ["en", "I meant the quotation: \"I have chest pain\""],
  ["de", "Ich meinte mein Brusttraining"]]) {
  test("B06 explicit clarification settles only communication: " + locale, () => {
    const started = begin(message(flow.create(subject), "flurbel", locale).state);
    const done = flow.apply(started.state, event(started.state, "clarify", { binding: started.binding, text, locale }));
    assert.equal(done.status, "communication_issue_settled");
    assert.equal(flow.view(done.state).unresolved_nonclinical.length, 0);
    assert.equal(done.state.messages[0].text, "flurbel");
    assert.equal(done.state.events.length, 3);
  });
}
for (const text of ["R0", "approved", "Ik train mijn borst", "Mijn klachten zijn voorbij", "Ik bedoelde flurbel"]) {
  test("B05 insufficient clarification cannot settle: " + text, () => {
    const started = begin(message(flow.create(subject), "flurbel").state);
    const r = flow.apply(started.state, event(started.state, "clarify", { binding: started.binding, text, locale: "nl" }));
    assert.equal(r.status, "clarification_still_open");
    assert.equal(flow.view(r.state).unresolved_nonclinical.length, 1);
  });
}
test("B07 new health in clarification retained along with other health and communication", () => {
  const initial = message(flow.create(subject), "flurbel").state;
  const health = message(initial, "Mijn borst voelt loodzwaar").state;
  const started = begin(health, health.issues[0]);
  const r = flow.apply(started.state, event(started.state, "clarify", { binding: started.binding,
    text: "Ich meinte: Jetzt habe ich Brustschmerzen", locale: "de" }));
  assert.equal(r.status, "new_health_report_during_clarification");
  assert.equal(flow.view(r.state).health_reports, 2);
  assert.equal(flow.view(r.state).unresolved_nonclinical.length, 1);
  assert.equal(r.state.issues[1].level, null);
});
test("B06 health reports cannot be turned into clarification targets", () => {
  const health = message(flow.create(subject), "Ik heb borstpijn").state;
  const r = flow.apply(health, event(health, "begin", { expected_revision: health.revision,
    message_id: health.issues[0].message_id, source_revision: health.issues[0].source_revision, mode: "clarify" }));
  noMutation(r, health); assert.equal(r.status, "nonclinical_issue_required");
});
for (const [locale, text] of [["nl", "Mijn klachten zijn voorbij"], ["en", "My symptoms are gone"], ["de", "Meine Beschwerden sind vorbei"]]) {
  test("B08 D02 affirmative chat reports recovery without clearance: " + locale, () => {
    const health = message(flow.create(subject), "Mijn borst voelt loodzwaar").state;
    const r = recover(health, "chat", text, locale);
    assert.equal(r.status, "self_report_recorded_not_clearance");
    const v = flow.view(r.state);
    assert.equal(v.current_reports, 0); assert.equal(v.health_reports, 1);
    assert.equal(v.self_reported_reports, 1); assert.equal(v.medical_clearance, false);
    assert.ok(v.open_criteria.includes("unclassified_recovery"));
    assert.equal(v.complete_health_resumption_flow, false);
    assert.deepEqual(r.state.messages, health.messages);
  });
}
test("B08 explicit confirmation bound to target not another open complaint", () => {
  let s = message(flow.create(subject), "Ik heb borstpijn").state;
  s = message(s, "Ich kriege kaum noch Luft", "de").state;
  const r = recover(s, "confirmation", "", "nl", [{ message_id: s.issues[0].message_id, source_revision: s.issues[0].source_revision }]);
  assert.equal(flow.view(r.state).current_reports, 1);
  assert.equal(flow.view(r.state).warnings[0].key, "current_unclassified");
});
test("B08 stale confirmation fails after a new complaint", () => {
  const s = message(flow.create(subject), "Ik heb borstpijn").state;
  const e = event(s, "self_report", { expected_revision: s.revision, targets: [{ message_id: s.issues[0].message_id,
    source_revision: s.issues[0].source_revision }], method: "confirmation", confirmed: true, text: "", locale: "nl" }, "recovery");
  const newState = message(s, "Ik ben duizelig").state;
  const r = flow.apply(newState, { ...e, at_ms: newState.at_ms + 1 });
  assert.equal(r.status, "stale_revision"); noMutation(r, newState);
});
for (const text of ["Mijn klachten zijn niet voorbij", "Mijn klachten zijn voorbij maar ik heb borstpijn"]) {
  test("B08 recovery conflict records new complaint, no self report: " + text, () => {
    const s = message(flow.create(subject), "Ik heb borstpijn").state;
    const r = recover(s, "chat", text);
    assert.equal(r.status, "recovery_conflict_new_health_report");
    assert.equal(r.state.self_reports.length, 0);
    assert.equal(flow.view(r.state).current_reports, 2);
  });
}
for (const text of ['Citaat: "Mijn klachten zijn voorbij"', "Zijn mijn klachten voorbij?", "Stel dat mijn klachten zijn voorbij"]) {
  test("B08 non-affirmative recovery is not recorded: " + text, () => {
    const s = message(flow.create(subject), "Ik heb borstpijn").state;
    const r = recover(s, "chat", text); noMutation(r, s);
    assert.equal(r.status, "affirmative_self_report_required");
  });
}
test("D01 D02 repeated same signal after report creates a new current revision, not clinical recurrence score", () => {
  const one = message(flow.create(subject), "Ik heb borstpijn").state;
  const self = recover(one).state;
  const again = message(self, "Ik heb borstpijn").state;
  const v = flow.view(again);
  assert.equal(v.current_reports, 1); assert.equal(v.self_reported_reports, 1);
  assert.equal(v.history[1].repeated_signal, true);
  assert.ok(v.open_criteria.includes("recurrence_meaning_and_recovery"));
  assert.ok(v.open_criteria.includes("serious_recovery"));
});
test("D01 R3, R4 and null retain distinct open criteria without invented clearance", () => {
  for (const [text, level, criterion] of [["Ik heb borstpijn", "R3", "serious_recovery"],
    ["I cannot breathe", "R4", "serious_recovery"], ["Mijn borst voelt loodzwaar", null, "unclassified_recovery"]]) {
    const s = message(flow.create(subject), text, "en").state, r = recover(s);
    assert.equal(s.issues[0].level, level);
    assert.ok(flow.view(r.state).open_criteria.includes(criterion));
    assert.deepEqual(flow.view(r.state).recommendations, []);
  }
});
test("B09 ordinary R0/new chat/time/approved/deletion do not release health", () => {
  const s = message(flow.create(subject), "Ik heb borstpijn").state;
  const ordinary = message(s, "Ik train borst en armen").state;
  assert.equal(flow.view(ordinary).current_reports, 1);
  for (const type of ["new_conversation", "delete", "tick", "approve", "__proto__"]) {
    const r = flow.apply(s, event(s, type, {})); noMutation(r, s);
  }
  const e = event(s, "message", { expected_revision: s.revision, message_id: "syn-new-message",
    text: "train", locale: "en", availability: "available", approved: true });
  noMutation(flow.apply(s, e), s);
});
test("B01 immutable branded state rejects forged serialization and cross-subject events", () => {
  const s = flow.create(subject);
  assert.throws(() => flow.apply(copy(s), {}), /issued_synthetic_state_required/);
  const e = event(s, "message", { expected_revision: 0, message_id: "syn-message", text: "train", locale: "en", availability: "available" });
  noMutation(flow.apply(s, { ...e, subject_id: "syn-other" }), s);
  assert.throws(() => { s.revision = 2; }, TypeError);
});
