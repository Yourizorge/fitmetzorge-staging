"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const { assess, isAssessment } = require("../context.cjs");
const fixtures = require("../preregistered-cases.json");
const frozen = require("../../phase6e0/recognition-followup-cases.json");
const keys = ["no_signal", "caution", "stop_clarify", "professional_review", "urgent_help"];
const inherited = frozen.cases.map(c => ({ id: "retained/" + c.id, locale: c.locale, text: c.text,
  availability: "available", expected: { level: c.expected_level, contexts: c.expected_context ? [c.expected_context] : [],
    warning: c.expected_level && c.expected_level !== "R0" ? keys[Number(c.expected_level.slice(1))] :
      c.expected_context === "current" ? "current_unclassified" : c.expected_context ? "noncurrent" : "no_signal",
    recovery: false, conflicts: [] } }));
for (const c of [...inherited, ...fixtures.cases]) test("text-to-feedback: " + c.id, () => {
  // Expectations are deliberately not forwarded to the classifier.
  const input = { synthetic_only: true, text: c.text, locale: c.locale, availability: c.availability };
  const a = assess(input);
  assert.equal(a.feedback.key, c.expected.warning, c.text);
  assert.equal(a.level, c.expected.level, c.text);
  assert.equal(a.recovery, c.expected.recovery, c.text);
  for (const context of c.expected.contexts) assert.ok(a.trace.some(t => t.context === context), context + ": " + c.text);
  for (const conflict of c.expected.conflicts) assert.ok(a.conflicts.includes(conflict), conflict);
  for (const t of a.trace) {
    assert.equal(c.text.slice(t.start, t.end), t.fragment);
    assert.ok(t.start >= 0 && t.end > t.start && t.end <= c.text.length);
    assert.ok(t.rule_id && t.context_basis.length);
  }
  assert.equal(a.medical_clearance, false);
  assert.equal(a.automatic_actions_allowed, false);
  assert.equal(isAssessment(a), true);
  assert.equal(isAssessment(JSON.parse(JSON.stringify(a))), false);
  assert.deepEqual(assess(input), a);
});
test("contract: annotations, approval and expected labels are not accepted input", () => {
  for (const field of ["annotation", "context", "expected", "approved", "help_level", "subject"]) {
    const a = assess({ synthetic_only: true, text: "Ik heb borstpijn", locale: "nl", availability: "available", [field]: "R0" });
    assert.equal(a.feedback.key, "technical");
    assert.deepEqual(a.uncertainty, ["invalid_input"]);
    assert.equal(a.medical_clearance, false);
  }
});
test("contract: invalid/oversized/live input cannot create a result with clearance", () => {
  for (const input of [null, {}, { synthetic_only: false, text: "I have chest pain", locale: "en", availability: "available" },
    { synthetic_only: true, text: "a".repeat(4097), locale: "nl", availability: "available" }]) {
    assert.equal(assess(input).feedback.key, "technical");
  }
});
test("contract: existing warning copy and all four original unclassified gaps are retained", () => {
  const copy = require("../../phase6e0/warning-recovery-proposal.json").warnings;
  for (const c of frozen.cases.filter(c => c.kind === "original")) {
    const a = assess({ synthetic_only: true, text: c.text, locale: c.locale, availability: "available" });
    assert.equal(a.feedback.text, copy.current_unclassified[c.locale]);
    assert.equal(a.level, null);
  }
});
