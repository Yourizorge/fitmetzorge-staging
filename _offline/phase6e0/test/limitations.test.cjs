"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const gaps = require("../known-limitations.json");
const { assess } = require("./helpers.cjs");
for (const gap of gaps.cases) test("KNOWN GAP observation, NOT clinical acceptance: " + gap.id, () => {
  const observed = assess(gap.text, gap.locale);
  assert.equal(observed.help_level, gap.observed_level,
    "Recognition changed: reassess and update the documented gap, do not silently count it as clinical success.");
  assert.equal(observed.medical_clearance, false);
  assert.equal(observed.automatic_actions_allowed, false);
});
for (const [locale, text] of [["nl", "Ik heb sinds gisteren pijn op de borst"],
  ["en", "I have chest pain since yesterday"], ["de", "Ich habe seit gestern Brustschmerzen"]]) {
  test("ongoing symptom since yesterday is not historical-only: " + locale, () => {
    assert.equal(assess(text, locale).help_level, "R3");
  });
}
