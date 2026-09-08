"use strict";

if (typeof window !== "undefined" || !process.versions.node) throw new Error("offline_node_only");
const { exact, rank, validateAssessment, access, copy } = require("./engine.cjs");
const { validateState } = require("./state.cjs");
const proposal = require("./warning-recovery-proposal.json");
function freeze(value) {
  if (value && typeof value === "object") {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}
freeze(proposal);
const annotations = ["reported_current_complaint", "unresolved_meaning", "noncurrent_only", "ordinary"];
const origins = ["health_report", "communication", "technical", "noncurrent"];
const locales = ["nl", "en", "de"];
function warningPreview(request) {
  if (!exact(request, ["synthetic_only", "assessment", "locale", "annotation", "authority"]) ||
      request.synthetic_only !== true || !validateAssessment(request.assessment) ||
      !locales.includes(request.locale) || !annotations.includes(request.annotation)) {
    throw new Error("invalid_warning_proposal");
  }
  const a = request.assessment;
  let key, source = "proposal";
  if (a.evaluation_state === "unavailable") key = "technical";
  else if (rank(a.help_level) >= 1) { key = a.warning_key; source = "existing_copy"; }
  else if (request.annotation === "reported_current_complaint" &&
      a.context_states.includes("current") && a.uncertainty_codes.includes("unrecognized_health_context")) {
    key = "current_unclassified";
  } else if (a.evaluation_state === "uncertain") key = "unclear";
  else if (request.annotation === "noncurrent_only" && !a.context_states.includes("current") &&
      a.context_states.some(c => ["past", "educational", "negated", "quoted", "hypothetical"].includes(c))) {
    key = "noncurrent";
  } else if (request.annotation === "ordinary") { key = "no_signal"; source = "existing_copy"; }
  else key = "unclear";
  const text = source === "existing_copy" ? copy[request.locale][key] : proposal.warnings[key][request.locale];
  return { status: proposal.status, key, source, help_level: a.help_level,
    text: access(request.authority).chat ? text : null,
    annotation_source: proposal.annotation_source,
    medical_clearance: false, automatic_actions_allowed: false, provider_calls: 0 };
}
function recoveryPreview(request) {
  if (!exact(request, ["synthetic_only", "state", "assessment", "locale", "annotation",
      "authority", "origins", "resolutions"]) || request.synthetic_only !== true ||
      !validateState(request.state) || !Array.isArray(request.origins) ||
      !Array.isArray(request.resolutions)) throw new Error("invalid_recovery_proposal");
  const state = request.state, a = request.assessment;
  const warning = warningPreview({ synthetic_only: true, assessment: a, locale: request.locale,
    annotation: request.annotation, authority: request.authority });
  const provenance = request.origins;
  if (provenance.length !== state.events.length ||
      new Set(provenance.map(p => p?.revision)).size !== provenance.length ||
      !provenance.every(p => exact(p, ["revision", "origin", "recurrence"]) &&
        origins.includes(p.origin) && typeof p.recurrence === "boolean" &&
        (!p.recurrence || p.origin === "health_report") &&
        state.events.some(e => e.revision === p.revision &&
          (rank(e.help_level) < 1 || p.origin === "health_report")))) {
    throw new Error("complete_synthetic_provenance_required");
  }
  // This sidecar is a manual fixture annotation, not a new classifier or a user-controlled release field.
  const settled = new Set();
  for (const resolution of request.resolutions) {
    const p = provenance.find(p => p.revision === resolution?.revision);
    if (!exact(resolution, ["subject_id", "revision", "reviewed_revision", "assessment", "disposition", "basis"]) || !p ||
        resolution.subject_id !== state.subject_id ||
        !Number.isSafeInteger(resolution.reviewed_revision) ||
        resolution.reviewed_revision < p.revision || resolution.reviewed_revision > state.revision ||
        p.origin === "health_report" || settled.has(p.revision) ||
        resolution.disposition !== "nonclinical_issue_resolved" ||
        resolution.basis !== "synthetic_review_outcome" ||
        !validateAssessment(resolution.assessment) ||
        resolution.assessment.evaluation_state !== "known" ||
        resolution.assessment.help_level !== "R0") throw new Error("nonclinical_resolution_only");
    settled.add(p.revision);
  }
  const health = provenance.filter(p => p.origin === "health_report");
  const pending = provenance.filter(p => !settled.has(p.revision));
  const medical = state.events.filter(e => health.some(p => p.revision === e.revision));
  const reported = state.events.length > 0 && state.self_reported_revision === state.revision;
  const openDecisions = ["personalized_content_scope"];
  if (medical.some(e => e.help_level === null || e.evaluation_state !== "known")) openDecisions.push("unclassified_health_recovery");
  if (medical.some(e => rank(e.help_level) >= 3)) openDecisions.push("serious_recovery");
  if (health.some(p => p.recurrence)) openDecisions.push("recurrence_recovery");
  if (state.unknown_after_deletion) openDecisions.push("missing_details_and_retention");
  if (openDecisions.length > 1) openDecisions.push("review_owner_deadline_appeal");
  let path, messages = [], steps;
  if (warning.key === "current_unclassified" || rank(a.help_level) >= 1) {
    path = "current_complaint";
    messages = ["new_signal", "report_available"];
    steps = ["record_or_reassess_current_report", "self_report_only_when_symptoms_have_ended"];
  } else if (warning.key === "technical") {
    path = "technical_reassessment";
    steps = ["retry_assessment", "resolve_technical_episode_separately"];
  } else if (state.unknown_after_deletion) {
    path = "missing_details_policy_not_defined";
    messages = ["details_missing"];
    steps = ["define_minimum_reassessment_data_and_deletion_consequences"];
  } else if (warning.key === "unclear" || pending.some(p => p.origin !== "health_report")) {
    path = "clarify_nonclinical_episode";
    messages = ["clarify_context"];
    steps = ["clarify_original_meaning_and_current_context", "separate_nonclinical_disposition_for_each_revision"];
  } else if (health.length && !reported) {
    path = "self_report_not_recorded";
    messages = ["report_available"];
    steps = ["record_explicit_self_report", "reassess_if_new_symptoms"];
  } else if (health.length && openDecisions.length > 1) {
    path = "health_resumption_policy_not_defined";
    messages = ["report_recorded", "health_policy_missing"];
    steps = ["owner_define_resumption_route_and_responsible_role", "expert_define_scope_and_evidence",
      "separate_explicit_content_decision_bound_to_latest_revision"];
  } else {
    path = "separate_personalized_content_gate";
    if (reported) messages.push("report_recorded");
    messages.push(settled.size ? "nonclinical_closed" : "content_request");
    steps = ["prepare_new_scoped_analysis_request", "apply_separately_approved_content_policy"];
  }
  const permission = access(request.authority);
  return {
    status: proposal.status, path, warning,
    visible: { chat: permission.chat, existing_results: permission.history,
      new_bounded_facts: permission.new_analysis, personalized_request_entry: permission.new_analysis },
    messages: permission.chat ? messages.map(key => ({ key, text: proposal.recovery_messages[key][request.locale] })) : [],
    next_steps: steps, open_decisions: openDecisions,
    self_report_current: reported,
    closed_nonclinical_revisions: [...settled].sort((x, y) => x - y),
    pending_revisions: pending.map(p => p.revision),
    retained_history: state.events.map(e => ({ ...e, signal_codes: [...e.signal_codes] })),
    prior_health_warning_preserved: health.length > 0,
    personalized_analyses_executed: false, automatic_actions_allowed: false,
    medical_clearance: false, actual_review_requested: false, trainer_sharing: false,
    provider_calls: 0, storage_writes: 0
  };
}
module.exports = { proposal, warningPreview, recoveryPreview };
