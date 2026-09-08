"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const { assess } = require("../context.cjs");
const fixtures = require("../training-followup-cases.json");
for (const c of fixtures.cases) test("narrow follow-up: " + c.id, () => {
  const a = assess({ synthetic_only: true, text: c.text, locale: c.locale, availability: c.availability });
  assert.equal(a.feedback.key, c.warning, c.text);
  assert.equal(a.level, c.level, c.text);
  assert.equal(a.medical_clearance, false);
  assert.equal(a.automatic_actions_allowed, false);
  if (c.warning === "current_unclassified") {
    assert.equal(a.category, "health_report");
    assert.ok(a.trace.some(t => t.context === "current" && t.provisional_level === null));
    assert.equal(a.feedback.text, require("../../phase6e0/warning-recovery-proposal.json").warnings.current_unclassified[c.locale]);
  }
  for (const t of a.trace) assert.equal(c.text.slice(t.start, t.end), t.fragment);
});
