"use strict";
if (typeof window !== "undefined") throw Error("offline_node_only");
const fixtures = require("../phase6e6/test/fixtures.cjs");
const model = require("../../training-review-demo/model.js");
const {clone, hash} = require("../phase6e5/common.cjs");
const names = ["normal", "lb", "all_maintain", "step_off_grid", "ambiguous_rules", "no_trainer",
  "missing_set", "no_analysis_consent", "book_expired", "stale_request", "current",
  "self_reported", "expired", "missing", "rir_zero", "optional_effort_missing"];
const locales = ["nl", "en", "de"];
function gateFor(name, out) {
  if (name === "no_trainer") return "no_trainer";
  if (name === "no_analysis_consent") return "consent_revoked";
  if (name === "book_expired") return "expired";
  if (name === "stale_request") return "version_conflict";
  if (name === "missing_set") return "incomplete";
  if (name === "step_off_grid") return "weight_step_conflict";
  if (name === "ambiguous_rules") return "ambiguous_rules";
  return out.plan_option || out.rows.length && out.rows.every(r => r.kind === "maintain" && r.status === "available") ? null : "unavailable";
}
function fromFixture(f, name = "normal") {
  const out = fixtures.run(f), sources = f.request.base.base.sources;
  if (sources.synthetic_only !== true || sources.subject_id !== "syn-member" || sources.plan.subject_id !== sources.subject_id)
    throw Error("synthetic_owner_required");
  const base = clone(sources.plan), target = clone(base), option = out.plan_option;
  if (option && (!fixtures.engine.details(option) || option.subject_id !== sources.subject_id ||
      option.base_plan_hash !== hash(base))) throw Error("issued_source_binding_required");
  for (const change of option?.changes || []) {
    const w = target.options.find(w => w.workout_id === change.workout_id);
    const e = w?.exercises.find(e => e.exercise_id === change.exercise_id);
    const index = e?.sets.findIndex(t => t.index === change.set_index);
    if (index === undefined || index < 0 || JSON.stringify(e.sets[index]) !== JSON.stringify(change.before))
      throw Error("complete_set_binding_required");
    e.sets[index] = clone(change.after);
  }
  const refs = option?.source_refs || Object.fromEntries(["goal", "plan", "relationship", "authority", "limits"]
    .filter(k => sources[k]).map(k => [k, {id: sources[k].id, revision: sources[k].revision}]));
  refs.rulebook ||= {id: f.book.id, revision: f.book.revision};
  const w2 = out.reason === "weight_step_conflict" ? f.book.rules.map(r => ({
    rule: r.id, exercise: r.selector.ref.id, step: r.parameters.weight_step,
    unit: r.parameters.unit, available: clone(r.parameters.available_weights)
  })) : [];
  // This is an explicit synthetic public allowlist, not a serialized private engine or chat context.
  return {
    synthetic_only: true, id: name, clock: 1789293600000, source_evaluated_at_ms: f.clock,
    trainer: sources.relationship?.trainer_id || null,
    plan: base, target, refs: clone(refs), basis: option?.basis_hash || hash({refs, status: out.status, reason: out.reason}),
    gate: gateFor(name, out), changes: clone(option?.changes || []), w2,
    rows: out.rows.map(r => ({exercise_id: r.exercise_id, labels: r.labels, kind: r.kind, reason: r.reason,
      current: r.current_plan, next: r.next_week, observations: r.observations, rule: r.rule})),
    facts: clone(out.facts.observations),
    catalog: clone(sources.catalog),
    goal: {ref: refs.goal || null, code: sources.goal?.code || null,
      labels: sources.goal?.code === "strength" ? {nl: "Fictief bestaand doel: kracht",
      en: "Fictional existing goal: strength", de: "Fiktives bestehendes Ziel: Kraft"} :
      {nl: "Doelinhoud ontbreekt", en: "Goal content missing", de: "Zielinhalt fehlt"}},
    reason: out.reason || null
  };
}
function seed(name = "normal", locale = "nl") {
  if (!names.includes(name) || !locales.includes(locale)) throw Error("unknown_fixture");
  return fromFixture(fixtures.setup(name, locale), name);
}
function workspace(f = fixtures.setup(), name = "normal") {
  const first = fromFixture(f, name), controller = model.create(first), baseline = hash(f.request);
  function command(event, options) {
    const fresh = fromFixture(f, name);
    if (fresh.gate || hash(f.request) !== baseline || fresh.basis !== first.basis)
      controller.inject(fresh.gate === "consent_revoked" ? "consent_revoked" : fresh.gate === "expired" ? "expired" : "unavailable");
    return controller.command(event, options);
  }
  return {...controller, command};
}
function publicData() {
  return {synthetic_only: true, version: "6e7-demo-v1",
    source_commit: "6479711ffb4fa97ad4934e8245c9ae334f5b1337",
    seeds: Object.fromEntries(names.map(n => [n, seed(n)]))};
}
module.exports = {names, locales, seed, fromFixture, workspace, publicData, fixtures};
