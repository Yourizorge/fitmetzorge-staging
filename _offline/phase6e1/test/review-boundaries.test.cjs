"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const { assess } = require("../context.cjs"), flow = require("../flow.cjs");
const { subject, message, begin, event } = require("./helpers.cjs");
for (const text of ["Ik heb geen borstpijn. Mijn arm tintelt", "Ik bedoelde mijn training. Mijn arm tintelt"]) {
  test("review: uncovered body-context clause is explicit uncertainty, not suppressed by earlier clause: " + text, () => {
    const a = assess({ synthetic_only: true, text, locale: "nl", availability: "available" });
    assert.equal(a.feedback.key, "unclear");
    assert.equal(a.level, null);
    assert.ok(a.uncertainty.includes("unmapped_body_context"));
  });
}
for (const text of ["Ik bedoelde niet mijn borsttraining", 'Citaat: "Ik bedoelde mijn borsttraining"',
  "Als ik bedoelde mijn borsttraining", "Ik bedoelde mijn borsttraining niet"]) {
  test("review: clarification marker must be affirmative and own, not quoted/hypothetical: " + text, () => {
    const started = begin(message(flow.create(subject), "flurbel").state);
    const r = flow.apply(started.state, event(started.state, "clarify", { binding: started.binding, text, locale: "nl" }));
    assert.equal(r.status, "clarification_still_open");
    assert.equal(flow.view(r.state).unresolved_nonclinical.length, 1);
  });
}
for (const [locale, text] of [["nl", "Misschien heb ik geen klachten meer"],
  ["en", "I think my symptoms are gone"], ["de", "Ich glaube, meine Beschwerden sind vorbei"]]) {
  test("review: tentative recovery is not an affirmative self-report: " + locale, () => {
    const s = message(flow.create(subject), "Ik heb borstpijn").state;
    const r = flow.apply(s, event(s, "self_report", { expected_revision: s.revision,
      targets: [{ message_id: s.issues[0].message_id, source_revision: s.issues[0].source_revision }],
      method: "chat", confirmed: false, text, locale }));
    assert.equal(r.state.self_reports.length, 0);
    assert.equal(flow.view(r.state).current_reports, 1);
    assert.equal(r.medical_clearance, false);
  });
}
test("review: result event cannot reuse another message identity", () => {
  let s = message(flow.create(subject), "flurbel").state;
  const started = begin(s);
  const r = flow.apply(started.state, event(started.state, "clarify", {
    binding: started.binding, text: "Ik bedoelde: ik heb borstpijn", locale: "nl", event_id: s.messages[0].id }));
  assert.equal(r.status, "event_message_identity_conflict");
  assert.equal(r.state, started.state);
});
