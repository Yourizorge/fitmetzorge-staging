"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const { exact, canonical, freeze, locales } = require("../phase6e1/common.cjs");
const flow = require("../phase6e1/flow.cjs");
const analysis = require("../phase6e1/analysis.cjs");
const retention = require("../phase6e1/retention.cjs");
const contract = freeze(require("./contract.json")), copy = freeze(require("./copy.json"));
const issued = new WeakMap(), superseded = new WeakSet();

function prepare(state, nowMs, options = {}, previous = null) {
  if (!flow.isState(state)) throw Error("issued_synthetic_state_required");
  const prior = previous === null ? null : issued.get(previous);
  if (previous !== null && (!prior || superseded.has(previous))) throw Error("current_issued_context_required");
  if (prior && (state.subject_id !== prior.state.subject_id ||
      state.events.length < prior.state.events.length ||
      prior.state.events.some((e, i) => canonical(e) !== canonical(state.events[i])))) throw Error("context_lineage_mismatch");
  let projection = retention.projectSafety(state, nowMs, options, prior?.projection || null);
  // Omitted options must not recreate a previously unavailable source. Carry
  // only still-retained O5 references, never a separate indefinite tombstone.
  const priorMissing = (prior?.projection.records || []).filter(r => r.status === "context_missing")
    .map(r => r.message_ref.message_id);
  if (priorMissing.length) projection = retention.projectSafety(state, nowMs, { ...options,
    missing_message_ids: [...new Set([...priorMissing, ...(options.missing_message_ids || [])])] }, prior.projection);
  const latest = state.messages.at(-1);
  const context = freeze({ version: contract.version,
    binding: { subject_id: state.subject_id, revision: state.revision,
      message_id: latest?.id || null, source_revision: latest?.source_revision ?? null },
    evaluated_at_ms: nowMs, safety_records: projection.records,
    storage_enabled: false, medical_clearance: false });
  issued.set(context, { state, projection, missing: new Set(projection.records
    .filter(r => r.status === "context_missing").map(r => r.message_ref.message_id)) });
  if (previous) superseded.add(previous);
  return context;
}
const key = origin => origin.message_id + ":" + origin.source_revision;
function contextView(context, canRead, locale) {
  const data = issued.get(context), state = data.state;
  const empty = { mode: "context_missing", warnings: [], nonclinical_options: [],
    self_reported: false, expert_criteria: [], feedback: [] };
  if (!canRead) return empty;
  const records = new Map(data.projection.records.map(r => [key(r.message_ref), r]));
  const available = [], gaps = [];
  for (const issue of state.issues) {
    const record = records.get(key(issue.retention_origin));
    if (!record || record.status === "context_missing") gaps.push(issue.retention_origin.source_revision);
    else available.push(issue);
  }
  const health = available.filter(i => i.kind === "health_report");
  const current = health.filter(i => !i.self_reported);
  const pending = available.filter(i => i.kind !== "health_report" && i.status !== "settled");
  const bind = i => ({ subject_id: state.subject_id, message_id: i.message_id,
    source_revision: i.source_revision, issue_revision: i.issue_revision, attempt: i.attempt });
  const warnings = current.map(i => ({ binding: bind(i), ...i.feedback }));
  const nonclinical = pending.map(i => ({ binding: bind(i),
    choices: [i.kind === "technical" ? "retry" : "reformulate", "continue_chat"] }));
  const latest = state.messages.at(-1);
  const unresolvedRevisions = [...gaps, ...pending.map(i => i.retention_origin.source_revision)];
  // A fresh ordinary message can support nonphysical reflection, but cannot
  // dismiss an available current health report or recreate expired safety data.
  const fresh = latest && !data.missing.has(latest.id) &&
    ["ordinary", "noncurrent"].includes(latest.assessment.category) &&
    unresolvedRevisions.every(revision => latest.source_revision > revision);
  const mode = current.length ? "current_health" : !latest || data.missing.has(latest.id) ? "context_missing" :
    gaps.length && !fresh ? "context_missing" : pending.length && !fresh ? "clarification" :
      health.some(i => i.self_reported) ? "self_reported" :
        gaps.length || pending.length ? "fresh_limited_context" : "ordinary_or_settled";
  const criteria = [];
  if (health.some(i => i.level === null)) criteria.push("unclassified_recovery");
  if (health.some(i => ["R3", "R4"].includes(i.level))) criteria.push("serious_recovery");
  if (health.some(i => i.repeated_signal)) criteria.push("recurrence_meaning_and_recovery");
  const feedback = [...warnings.map(w => w.text)];
  if (mode === "clarification") feedback.push(...pending.map(i => i.feedback.text));
  if (health.some(i => i.self_reported)) feedback.push(analysis.copy[locale].recovered);
  if (mode === "context_missing" || mode === "fresh_limited_context") feedback.push(copy[locale].context_missing);
  if (!state.issues.length && latest?.assessment.category === "noncurrent") feedback.push(latest.assessment.feedback.text);
  return { mode, warnings, nonclinical_options: nonclinical,
    self_reported: health.some(i => i.self_reported), expert_criteria: criteria, feedback };
}
function fill(template, values) {
  return template.replace(/\{([a-z_]+)\}/g, (_, name) => {
    if (!Object.hasOwn(values, name)) throw Error("missing_template_value");
    return values[name];
  });
}
const numeric = (n, locale, signed = false) => (signed && n > 0 ? "+" : "") +
  String(Math.round((n + Number.EPSILON) * 100) / 100).replace(".", locale === "en" ? "." : ",");
function recommend(request, context, authority) {
  if (!issued.has(context)) throw Error("issued_context_required");
  const { state } = issued.get(context), permission = analysis.access(authority, state.subject_id);
  const locale = locales.includes(request?.analysis?.locale) ? request.analysis.locale : "en", c = copy[locale];
  const base = { version: contract.version, status: "invalid_input", access: permission,
    observations: [], unavailable_metrics: [], recommendations: [], warnings: [], nonclinical_options: [],
    messages: [], actions: [], automatic_actions_allowed: false, trainer_sharing: false,
    medical_clearance: false, training_suitability_assessed: false, runtime_execution: false,
    storage_enabled: false, provider_calls: 0, human_approval_service: false,
    clarification_required: false, permanent_health_access_block: false, owner_accepted: false };
  const reject = reason => freeze({ ...base, reason, messages: [c.invalid] });
  if (superseded.has(context)) return reject("stale_context");
  if (!exact(request, ["synthetic_only", "type", "binding", "analysis"]) ||
      request.synthetic_only !== true || !Object.hasOwn(contract.types, request.type) ||
      !exact(request.binding, ["subject_id", "revision", "message_id", "source_revision"]) ||
      canonical(request.binding) !== canonical(context.binding)) return reject("invalid_binding_or_request");
  const policy = contract.types[request.type];
  if (!policy.blocked && request.analysis?.kind !== policy.kind) return reject("wrong_analysis_kind");
  const facts = analysis.analyze(request.analysis, state, authority);
  if (facts.status === "invalid_input") return reject("invalid_aggregate_contract");
  if (!permission.new_analysis) return freeze({ ...base, status: "access_unavailable", messages: [c.access] });
  if (request.analysis.window.end_ms > context.evaluated_at_ms) return reject("future_window");
  const safety = contextView(context, permission.chat, locale);
  const result = { ...base, observations: facts.observations, unavailable_metrics: facts.unavailable_metrics,
    warnings: safety.warnings, nonclinical_options: safety.nonclinical_options,
    context_mode: safety.mode, expert_criteria: safety.expert_criteria,
    self_reported: safety.self_reported, binding: context.binding,
    all_expert_reviews_open: true, complete_health_resumption_flow: false };
  const finish = (status, reason, text, extra = {}) => freeze({ ...result, status, reason,
    messages: [...safety.feedback, text, c.scope], ...extra });
  if (policy.blocked) return finish("content_boundary", "unreviewed_content_or_sources", c.boundary,
    { missing_conditions: policy.missing });
  const rows = policy.required.map(code => facts.observations.find(o => o.code === code));
  if (rows.some(r => !r)) return finish("facts_only", "required_data_missing", c.data);
  if (rows.some(r => r.source.coverage !== "complete")) return finish("facts_only", "required_data_partial", c.data);
  if (rows.some(r => canonical(r.source) !== canonical(rows[0].source))) return finish("facts_only", "incoherent_source_bundle", c.data);
  if (policy.comparison) {
    if (rows.some(r => !r.comparison)) return finish("facts_only", "comparison_unavailable", c.data);
    if (rows.some(r => r.comparison.source.end_ms !== r.source.start_ms)) return finish("facts_only", "comparison_not_adjacent", c.data);
    if (rows.some(r => canonical(r.comparison.source) !== canonical(rows[0].comparison.source)))
      return finish("facts_only", "incoherent_comparison_bundle", c.data);
  }
  const row = code => rows.find(r => r.code === code);
  if (request.type === "workout_reflection" && row("completed_sets").value === 0)
    return finish("facts_only", "no_completed_set_basis", c.data);
  if (request.type !== "daily_record_check") {
    if (safety.mode === "current_health") return finish("facts_only", "current_health_report", c.current);
    if (["context_missing", "clarification"].includes(safety.mode))
      return finish("clarification", safety.mode, c[safety.mode]);
  }
  let text;
  if (request.type === "daily_record_check") {
    const sleep = facts.observations.find(o => o.code === "sleep_hours");
    const missing = facts.unavailable_metrics.find(o => o.code === "sleep_hours")?.reason === "missing_value";
    const sleepText = sleep?.source.coverage === "complete" ? fill(c.sleep_present, { sleep: numeric(sleep.value, locale) }) :
      missing ? c.sleep_missing : c.sleep_unusable;
    text = fill(c.daily, { minutes: numeric(row("training_minutes").value, locale), steps: numeric(row("steps").value, locale), sleep: sleepText });
  } else if (request.type === "workout_reflection") text = fill(c.post_workout, {
    sets: numeric(row("completed_sets").value, locale), reps: numeric(row("completed_reps").value, locale),
    minutes: numeric(row("duration_minutes").value, locale) });
  else text = fill(c.weekly, { workouts: numeric(row("completed_workouts").value, locale),
    minutes: numeric(row("training_minutes").value, locale),
    delta_minutes: numeric(row("training_minutes").comparison.delta, locale, true),
    delta_workouts: numeric(row("completed_workouts").comparison.delta, locale, true) });
  const sleepBasis = request.type === "daily_record_check" ? facts.observations.filter(r =>
    r.code === "sleep_hours" && r.source.coverage === "complete") : [];
  const basis = [...rows, ...sleepBasis].map(r => ({ metric: r.code, value: r.value, unit: r.unit, source: r.source,
    ...(policy.comparison ? { comparison: r.comparison } : {}) }));
  return finish("recommendation", "bounded_nonphysical_proposal", text, { recommendations: [{
    type: request.type, content_class: policy.content_class, text, basis, bound_to: context.binding,
    goal_source: null, trainer_limits_source: null, physical_prescription: false }] });
}
module.exports = { prepare, recommend, contract };
