"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const { execFileSync } = require("node:child_process");
const { assess, authority } = require("./helpers.cjs");
const { copy, boundedAnalysis } = require("../engine.cjs");
const { createState, transition, recoveryStatus } = require("../state.cjs");
const { proposal, warningPreview, recoveryPreview } = require("../warning-recovery-proposal.cjs");
const cases = require("../recognition-followup-cases.json").cases;
const warning = (assessment, annotation, locale = "nl", permissions = authority) =>
  warningPreview({ synthetic_only: true, assessment, annotation, locale, authority: permissions });
const origin = (revision, kind = "health_report", recurrence = false) => ({ revision, origin: kind, recurrence });
const resolve = revision => ({ subject_id: "syn-flow", revision, reviewed_revision: revision,
  assessment: assess("Ik bedoelde het gewicht van de halter"),
  disposition: "nonclinical_issue_resolved", basis: "synthetic_review_outcome" });
function event(state, type, assessment, patch = {}) {
  return { type, subject_id: state.subject_id, request_id: "syn-flow-" + (state.clock_ms + 1),
    expected_revision: state.revision, at_ms: state.clock_ms + 1, assessment, ...patch };
}
function signal(state, assessment) { return transition(state, event(state, "signal", assessment)).state; }
function report(state) {
  return transition(state, event(state, "self_report", assess("Mijn klachten zijn voorbij"),
    { method: "chat", confirmed: true })).state;
}
function preview(state, provenance, patch = {}) {
  return recoveryPreview({ synthetic_only: true, state, assessment: assess("Vandaag lees ik mijn resultaten"),
    locale: "nl", annotation: "ordinary", authority, origins: provenance, resolutions: [], ...patch });
}
function boundaries(view) {
  assert.deepEqual(view.visible, { chat: true, existing_results: true, new_bounded_facts: true, personalized_request_entry: true });
  for (const key of ["personalized_analyses_executed", "automatic_actions_allowed", "medical_clearance",
    "actual_review_requested", "trainer_sharing"]) assert.equal(view[key], false, key);
  assert.equal(view.provider_calls, 0);
  assert.equal(view.storage_writes, 0);
}
test("separate multilingual proposal, no replacement of accepted copy or medical ranks", () => {
  assert.equal(proposal.status, "UNAPPROVED_OFFLINE_CONCEPT");
  assert.equal(proposal.runtime_activation, false);
  assert.equal(proposal.medical_level_changes, false);
  assert(Object.isFrozen(proposal.warnings.current_unclassified));
  for (const group of [proposal.warnings, proposal.recovery_messages]) {
    for (const item of Object.values(group)) for (const locale of ["nl", "en", "de"]) assert(item[locale].length > 20);
  }
  for (const locale of ["nl", "en", "de"]) assert.equal(proposal.recovery_messages.report_recorded[locale], copy[locale].recovery);
});
for (const c of cases.filter(c => c.kind === "original")) for (const locale of ["nl", "en", "de"]) {
  test("current complaint proposal without new level: " + c.id + "/" + locale, () => {
    const a = assess(c.text, c.locale), before = structuredClone(a);
    const output = warning(a, "reported_current_complaint", locale);
    assert.equal(output.key, "current_unclassified");
    assert.equal(output.help_level, null);
    assert.equal(a.evaluation_state, "uncertain");
    assert.equal(output.text, proposal.warnings.current_unclassified[locale]);
    assert.notEqual(output.text, copy[locale].uncertain);
    assert.deepEqual(a, before);
  });
}
for (const locale of ["nl", "en", "de"]) {
  for (const text of ["", "florb", "\u{1F642}"]) test("word/emoji/missing context is not a complaint: " + locale + "/" + text, () => {
    const view = warning(assess(text, locale), "unresolved_meaning", locale);
    assert.equal(view.key, "unclear");
    assert.equal(view.text, proposal.warnings.unclear[locale]);
    assert.doesNotMatch(view.text, /Stop|Beende|noodhulp|emergency|Notfall/);
  });
  test("technical failure does not infer symptoms: " + locale, () => {
    const view = warning(assess("hello", locale, { availability: "unavailable" }), "ordinary", locale);
    assert.equal(view.key, "technical");
    assert.equal(view.help_level, null);
    assert.equal(view.text, proposal.warnings.technical[locale]);
  });
  for (const kind of ["negation", "historical", "educational", "quoted"]) {
    const c = cases.find(c => c.kind === kind && c.locale === locale);
    test("separate noncurrent context: " + c.id, () => {
      const a = assess(c.text, locale), view = warning(a, "noncurrent_only", locale);
      assert.equal(a.help_level, "R0");
      assert.equal(view.key, "noncurrent");
      assert.equal(view.text, proposal.warnings.noncurrent[locale]);
    });
  }
}
test("generic health vocabulary is not automatically a reported complaint", () => {
  const a = assess("medicatie");
  assert.equal(a.evaluation_state, "uncertain");
  assert.equal(warning(a, "unresolved_meaning").key, "unclear");
});
test("an existing recognized level is never reduced by proposed annotation or emoji", () => {
  const a = assess("Ik heb pijn op de borst \u{1F642}");
  for (const annotation of ["ordinary", "noncurrent_only", "unresolved_meaning"]) {
    const view = warning(a, annotation);
    assert.equal(view.help_level, a.help_level);
    assert.equal(view.source, "existing_copy");
    assert.equal(view.text, copy.nl[a.warning_key]);
  }
});
for (const c of cases.filter(c => c.kind === "original")) {
  test("exact before/after self-report for original complaint: " + c.id, () => {
    const a = assess(c.text, c.locale);
    const start = signal(createState("syn-flow"), a), original = structuredClone(start);
    const before = preview(start, [origin(1)], { assessment: a, annotation: "reported_current_complaint" });
    const afterState = report(start), after = preview(afterState, [origin(1)]);
    boundaries(before); boundaries(after);
    assert.equal(before.path, "current_complaint");
    assert.equal(after.path, "health_resumption_policy_not_defined");
    assert.equal(after.self_report_current, true);
    assert(after.open_decisions.includes("unclassified_health_recovery"));
    assert(after.messages.some(m => m.key === "health_policy_missing"));
    assert.deepEqual(after.retained_history, original.events);
    assert.deepEqual(start, original);
    assert.equal(recoveryStatus(afterState), "unresolved_review_required");
    assert.throws(() => preview(afterState, [origin(1)], { resolutions: [resolve(1)] }), /nonclinical_resolution_only/);
    const facts = boundedAnalysis({ synthetic_only: true, kind: "weekly",
      facts: [{ code: "completed_workouts", value: 2 }] }, a, authority);
    assert.equal(facts.facts.length, 1);
    assert.deepEqual(facts.advice, []); assert.deepEqual(facts.actions, []);
  });
}
for (const [kind, a] of [["communication", assess("\u{1F642}")],
  ["technical", assess("hello", "nl", { availability: "unavailable" })]]) {
  test("old nonclinical uncertainty has a separate resolution path: " + kind, () => {
    const start = signal(createState("syn-flow"), a), recovered = report(start);
    const unchanged = structuredClone(recovered);
    const before = preview(start, [origin(1, kind)]);
    const afterReport = preview(recovered, [origin(1, kind)]);
    const resolved = preview(recovered, [origin(1, kind)], { resolutions: [resolve(1)] });
    boundaries(before); boundaries(afterReport); boundaries(resolved);
    assert.equal(before.path, "clarify_nonclinical_episode");
    assert.equal(afterReport.path, "clarify_nonclinical_episode");
    assert.equal(resolved.path, "separate_personalized_content_gate");
    assert.deepEqual(resolved.closed_nonclinical_revisions, [1]);
    assert.deepEqual(resolved.pending_revisions, []);
    assert.deepEqual(recovered, unchanged);
    assert.deepEqual(resolved.retained_history, start.events);
    assert.equal(recoveryStatus(recovered), "unresolved_review_required");
    assert.equal(resolved.actual_review_requested, false);
  });
}
test("partial technical resolution does not close a separate health episode", () => {
  let state = signal(createState("syn-flow"), assess("Mijn borst voelt loodzwaar"));
  state = signal(state, assess("hello", "nl", { availability: "unavailable" }));
  state = report(state);
  const view = preview(state, [origin(1), origin(2, "technical")], { resolutions: [resolve(2)] });
  assert.equal(view.path, "health_resumption_policy_not_defined");
  assert.deepEqual(view.pending_revisions, [1]);
  assert.equal(view.retained_history.length, 2);
  boundaries(view);
});
test("outage preserves previous health history without adding a new health warning", () => {
  const state = signal(createState("syn-flow"), assess("Mijn borst voelt loodzwaar"));
  const view = preview(state, [origin(1)], { assessment: assess("hello", "nl", { availability: "unavailable" }) });
  assert.equal(view.warning.key, "technical");
  assert.equal(view.path, "technical_reassessment");
  assert.equal(view.prior_health_warning_preserved, true);
  assert.deepEqual(view.retained_history, state.events);
  boundaries(view);
});
test("lower existing level reaches a separate content gate, not execution, after self-report", () => {
  const start = signal(createState("syn-flow"), assess("Ik ben duizelig"));
  assert.equal(preview(start, [origin(1)]).path, "self_report_not_recorded");
  const after = preview(report(start), [origin(1)]);
  assert.equal(after.path, "separate_personalized_content_gate");
  boundaries(after);
});
for (const text of ["Ik heb pijn op de borst", "Ik kan niet ademen"]) {
  test("serious recovery explicitly names missing criteria: " + text, () => {
    const state = report(signal(createState("syn-flow"), assess(text)));
    const view = preview(state, [origin(1)]);
    assert.equal(view.path, "health_resumption_policy_not_defined");
    assert(view.open_decisions.includes("serious_recovery"));
    assert(view.open_decisions.includes("review_owner_deadline_appeal"));
    boundaries(view);
  });
}
test("new symptoms after self-report invalidate the earlier report and resolution cannot release them", () => {
  let state = report(signal(createState("syn-flow"), assess("Ik ben duizelig")));
  const a = assess("Mijn borst voelt loodzwaar");
  state = signal(state, a);
  assert.equal(state.self_reported_revision, null);
  const provenance = [origin(1), origin(2, "health_report", true)];
  const current = preview(state, provenance, { assessment: a, annotation: "reported_current_complaint" });
  assert.equal(current.path, "current_complaint");
  assert(current.open_decisions.includes("recurrence_recovery"));
  const after = preview(report(state), provenance);
  assert.equal(after.path, "health_resumption_policy_not_defined");
  assert(after.open_decisions.includes("recurrence_recovery"));
  boundaries(current); boundaries(after);
});
test("all historical nonclinical issues must be accounted for, not only the latest", () => {
  let state = signal(createState("syn-flow"), assess("\u{1F642}"));
  state = signal(state, assess("", "nl"));
  const view = preview(report(state), [origin(1, "communication"), origin(2, "communication")],
    { resolutions: [resolve(2)] });
  assert.equal(view.path, "clarify_nonclinical_episode");
  assert.deepEqual(view.pending_revisions, [1]);
});
test("missing historical details are explicit open criteria, not clearance or silent deletion", () => {
  const state = { ...createState("syn-flow"), unknown_after_deletion: true };
  const view = preview(state, []);
  assert.equal(view.path, "missing_details_policy_not_defined");
  assert(view.open_decisions.includes("missing_details_and_retention"));
  boundaries(view);
});
test("permission axes remain independent and help stays inside accessible chat", () => {
  const state = report(signal(createState("syn-flow"), assess("Mijn borst voelt loodzwaar")));
  for (const key of ["authenticated", "adult", "ai_entitlement", "private_chat_consent", "ai_analysis_consent", "own_history_access"]) {
    const permissions = { ...authority, [key]: false };
    const view = preview(state, [origin(1)], { authority: permissions });
    if (["authenticated", "adult", "ai_entitlement", "private_chat_consent"].includes(key)) {
      assert.equal(view.visible.chat, false); assert.equal(view.warning.text, null); assert.deepEqual(view.messages, []);
    }
    if (key === "private_chat_consent") assert.equal(view.visible.new_bounded_facts, true);
    if (key === "ai_analysis_consent") { assert.equal(view.visible.chat, true); assert.equal(view.visible.new_bounded_facts, false); }
    assert.equal(view.automatic_actions_allowed, false);
  }
});
test("invalid or synthetic release-shaped inputs are rejected", () => {
  const state = report(signal(createState("syn-flow"), assess("\u{1F642}")));
  for (const patch of [{ synthetic_only: false }, { surprise: true }, { resolutions: [resolve(99)] },
    { resolutions: [resolve(1), resolve(1)] }, { resolutions: [{ ...resolve(1), basis: "user_says_recovered" }] },
    { resolutions: [{ ...resolve(1), assessment: assess("") }] },
    { resolutions: [{ ...resolve(1), subject_id: "syn-another" }] },
    { resolutions: [{ ...resolve(1), reviewed_revision: 99 }] }, { origins: [] }]) {
    assert.throws(() => preview(state, [origin(1, "communication")], patch));
  }
  const health = signal(createState("syn-flow"), assess("Ik heb pijn op de borst"));
  assert.throws(() => preview(health, [origin(1, "communication")]), /provenance_required/);
});
test("a later complaint is assessed separately without reopening or erasing a closed nonclinical issue", () => {
  let state = report(signal(createState("syn-flow"), assess("\u{1F642}")));
  const settlement = resolve(1);
  assert.equal(preview(state, [origin(1, "communication")], { resolutions: [settlement] }).path,
    "separate_personalized_content_gate");
  const a = assess("Mijn borst voelt loodzwaar");
  state = signal(state, a);
  const view = preview(state, [origin(1, "communication"), origin(2)],
    { resolutions: [settlement], assessment: a, annotation: "reported_current_complaint" });
  assert.equal(view.path, "current_complaint");
  assert.equal(view.self_report_current, false);
  assert.deepEqual(view.closed_nonclinical_revisions, [1]);
  assert.deepEqual(view.pending_revisions, [2]);
  assert.equal(view.retained_history.length, 2);
  boundaries(view);
});
test("proposal is Node-only, immutable local imports, no IO or runtime references", () => {
  const dir = path.resolve(__dirname, "..");
  const source = fs.readFileSync(path.join(dir, "warning-recovery-proposal.cjs"), "utf8");
  assert.throws(() => vm.runInNewContext(source, { window: {}, require() { throw Error("unexpected_import"); } }), /offline_node_only/);
  assert.doesNotMatch(source, /\b(?:fetch|XMLHttpRequest|WebSocket|setInterval|setTimeout|Date)\b|process\.env|Math\.random|\bimport\s*\(/);
  for (const m of source.matchAll(/require\("([^"]+)"\)/g)) assert.match(m[1], /^\.\/(?:engine\.cjs|state\.cjs|warning-recovery-proposal\.json)$/);
  for (const file of ["engine.cjs", "state.cjs", "retention.cjs", "corpus.cjs"]) assert.doesNotMatch(fs.readFileSync(path.join(dir, file), "utf8"), /warning-recovery/);
});
test("classifier, medical levels, original fixtures, state contract, copy and D1-D12 stay byte-identical", () => {
  const root = path.resolve(__dirname, "../../..");
  const files = ["engine.cjs", "rules.json", "context-hints.json", "contract.json", "copy.json", "state.cjs",
    "retention.cjs", "recognition-followup-cases.json", "known-limitations.json"].map(f => "_offline/phase6e0/" + f);
  files.push("docs/PHASE6E0_OWNER_DECISIONS.md", "docs/PACKAGE6D_CORRECTED_FREEZE_AND_6E_OWNER_DECISIONS.md");
  assert.equal(execFileSync("git", ["diff", "--name-only", "c1e3b634e95c3d8911f31c414b198e2dfff415be", "--", ...files],
    { cwd: root, encoding: "utf8", windowsHide: true }).trim(), "");
});
