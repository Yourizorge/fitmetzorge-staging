/* Public synthetic mock controller. No account, storage, provider or private-module access. */
(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.FMZDemoModel = api;
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";
  const clone = value => JSON.parse(JSON.stringify(value));
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const freeze = value => {
    if (value && typeof value === "object") { Object.values(value).forEach(freeze); Object.freeze(value); }
    return value;
  };
  const gates = ["version_conflict", "expired", "no_trainer", "consent_revoked", "relation_revoked", "incomplete", "unavailable"];
  const decisions = ["member_accept", "member_reject", "trainer_approve", "trainer_reject", "trainer_block", "apply", "restore"];
  function validateSeed(seed) {
    if (!Array.isArray(seed.changes) || !seed.target || !seed.refs.plan || !seed.refs.rulebook ||
        seed.refs.plan.id !== seed.plan.id || seed.refs.plan.revision !== seed.plan.revision ||
        !Number.isSafeInteger(seed.clock) || typeof seed.basis !== "string") throw Error("invalid_source_binding");
    const projected = clone(seed.plan), seen = new Set();
    for (const change of seed.changes) {
      const key = change.workout_id + ":" + change.exercise_id + ":" + change.set_index;
      const workouts = projected.options.filter(w => w.workout_id === change.workout_id);
      const exercises = workouts.length === 1 ? workouts[0].exercises.filter(e => e.exercise_id === change.exercise_id) : [];
      const sets = exercises.length === 1 ? exercises[0].sets.filter(t => t.index === change.set_index) : [];
      if (seen.has(key) || sets.length !== 1 || !same(sets[0], change.before)) throw Error("invalid_set_binding");
      seen.add(key);
      const a = change.after;
      if (!a || a.index !== change.set_index || !Number.isSafeInteger(a.reps?.min) || a.reps.min < 1 ||
          a.reps.min !== a.reps.max || !Number.isFinite(a.load?.value) || a.load.value < 0 ||
          !["kg", "lb"].includes(a.load.unit) || a.load.unit !== change.before.load.unit ||
          a.rir !== change.before.rir || a.rpe !== change.before.rpe) throw Error("invalid_set_target");
      exercises[0].sets[exercises[0].sets.indexOf(sets[0])] = clone(a);
    }
    if (!same(projected, seed.target) || (seed.gate && seed.changes.length)) throw Error("partial_or_unbound_target");
  }
  function create(seed) {
    if (!seed || seed.synthetic_only !== true || !seed.plan || !Number.isSafeInteger(seed.plan.revision) ||
        seed.plan.subject_id !== "syn-member" || !Array.isArray(seed.rows) || !seed.refs) throw Error("invalid_synthetic_seed");
    validateSeed(seed);
    const initial = clone(seed);
    let state = {
      synthetic_only: true, clock: seed.clock, revision: 0, sequence: 1,
      active: clone(seed.plan), history: [], audit: [], notifications: [],
      refs: clone(seed.refs), gate: seed.gate || null,
      member: "syn-member", trainer: seed.trainer, consent: true,
      automatic_actions_allowed: false, physical_advice_authorized: false, medical_clearance: false,
      proposal: {
        id: "syn-review-1", kind: "progression", status: seed.gate ? "blocked" : seed.changes.length ? "member_pending" : "maintained",
        member: "pending", trainer: "pending", application: "not_applied",
        base: clone(seed.plan), target: clone(seed.target), refs: clone(seed.refs),
        reason: seed.gate || "created", rows: clone(seed.rows), basis: seed.basis
      }
    };
    const ledger = new Map();
    function note(s, action, actor, reason, before, commandId) {
      s.clock += 1000;
      s.audit.push({
        id: "event-" + (s.audit.length + 1), command_id: commandId,
        at: new Date(s.clock).toISOString(), actor, action, reason,
        proposal_id: s.proposal.id, proposal_kind: s.proposal.kind,
        proposal_basis: s.proposal.basis, source_versions: clone(s.proposal.refs),
        current_source_versions: clone(s.refs), status: s.proposal.status,
        member: s.proposal.member, trainer: s.proposal.trainer, application: s.proposal.application,
        before_version: before, after_version: s.active.revision
      });
    }
    function notify(s, recipient, key, reason = null) {
      if (recipient === "trainer" && (!s.trainer || s.gate === "relation_revoked")) return;
      const id = s.proposal.id + ":" + key + ":" + recipient;
      if (!s.notifications.some(n => n.id === id))
        s.notifications.push({id, recipient, key, reason, at: new Date(s.clock).toISOString()});
    }
    note(state, "create", "system", state.proposal.reason, state.active.revision, "initial");
    if (state.proposal.status === "member_pending") notify(state, "member", "new_member");
    else if (state.gate) notify(state, "member", "blocked", state.gate);
    const view = () => freeze(clone(state));
    function command(input, options = {}) {
      const fail = reason => ({ok: false, reason, state: view()});
      const allowed = ["id", "action", "actor", "subject", "proposal_id", "proposal_basis", "expected_revision", "target_version", "reason"];
      if (!input || !same(Object.keys(input).sort(), allowed.sort()) ||
          typeof input.id !== "string" || !/^cmd-[a-zA-Z0-9_-]{1,90}$/.test(input.id) ||
          !decisions.includes(input.action) || input.subject !== state.member || input.proposal_basis !== state.proposal.basis ||
          !["syn-member", "syn-trainer"].includes(input.actor) ||
          (input.actor === "syn-trainer" && input.actor !== state.trainer) ||
          !Number.isSafeInteger(input.expected_revision) ||
          ![null, "member_declined", "trainer_declined", "trainer_blocked"].includes(input.reason) ||
          (input.target_version !== null && !Number.isSafeInteger(input.target_version))) return fail("invalid_command");
      if (Object.keys(options).some(k => k !== "fault_before_commit") ||
          (options.fault_before_commit !== undefined && typeof options.fault_before_commit !== "boolean")) return fail("invalid_options");
      const fingerprint = JSON.stringify(input);
      if (ledger.has(input.id)) return ledger.get(input.id) === fingerprint ?
        {ok: true, reason: "idempotent_retry", state: view()} : fail("idempotency_conflict");
      if (input.proposal_id !== state.proposal.id || input.expected_revision !== state.revision) return fail("stale_command");
      const a = input.action, p = state.proposal, isMember = input.actor === state.member;
      if ((a.startsWith("member_") && !isMember) || ((a.startsWith("trainer_") || a === "apply") && isMember)) return fail("wrong_role");
      if (a !== "restore" && input.target_version !== null) return fail("invalid_target");
      if (a !== "member_reject" && a !== "trainer_reject" && a !== "trainer_block" && input.reason !== null) return fail("invalid_reason");
      if (state.gate || !state.consent || !state.trainer || !same(p.refs, state.refs) ||
          p.base.revision !== state.active.revision || !same(p.base, state.active)) {
        // Applied proposals may open a fresh restore; their old base is intentionally historical.
        if (!(a === "restore" && p.status === "applied" && !state.gate && state.consent && state.trainer))
          return fail(state.gate || "version_conflict");
      }
      const next = clone(state), np = next.proposal, before = state.active.revision;
      let reason = a;
      if (a === "restore") {
        if (p.status !== "applied") return fail("restore_after_application_only");
        const target = state.history.find(h => h.revision === input.target_version);
        if (!target || target.id !== state.active.id || target.subject_id !== state.member) return fail("missing_version");
        const restored = clone(target); restored.revision = state.active.revision;
        // Only plan content is restored. The new version retains the current capture envelope.
        restored.captured_at_ms = state.active.captured_at_ms;
        if (same(restored, state.active)) return fail("no_changes");
        next.sequence++;
        next.proposal = {id: "syn-review-" + next.sequence, kind: "restore", status: "member_pending",
          member: "pending", trainer: "pending", application: "not_applied", base: clone(state.active),
          target: restored, refs: clone(state.refs), reason: "restore_created", rows: clone(initial.rows),
          restore_version: target.revision, basis: JSON.stringify({original_basis: initial.basis, target_version: target.revision, current: state.refs})};
        reason = "restore_created";
      } else {
        if (["applied", "blocked", "rejected", "maintained"].includes(p.status)) return fail("terminal_state");
        if (a === "member_accept") {
          if (p.status !== "member_pending") return fail("wrong_order");
          np.member = "accepted"; np.status = "trainer_pending";
        } else if (a === "member_reject") {
          if (p.status !== "member_pending") return fail("wrong_order");
          np.member = "rejected"; np.status = "rejected"; reason = "member_declined";
        } else if (a === "trainer_approve" || a === "trainer_reject" || a === "trainer_block") {
          if (p.status !== "trainer_pending" || p.member !== "accepted") return fail("member_first");
          np.trainer = a === "trainer_approve" ? "approved" : a === "trainer_reject" ? "rejected" : "blocked";
          np.status = a === "trainer_approve" ? "approved" : a === "trainer_reject" ? "rejected" : "blocked";
          if (a !== "trainer_approve") reason = a === "trainer_reject" ? "trainer_declined" : "trainer_blocked";
        } else if (a === "apply") {
          if (p.status !== "approved" || p.member !== "accepted" || p.trainer !== "approved") return fail("approvals_missing");
          if (!Number.isSafeInteger(state.active.revision + 1)) return fail("version_overflow");
          next.history.push(clone(state.active));
          next.active = clone(p.target); next.active.revision = state.active.revision + 1;
          next.refs.plan = {id: next.active.id, revision: next.active.revision};
          np.application = "applied"; np.status = "applied"; reason = p.kind === "restore" ? "restored" : "applied";
        }
      }
      next.proposal.reason = reason; next.revision++;
      note(next, a, isMember ? "member" : "trainer", reason, before, input.id);
      if (a === "member_accept") notify(next, "trainer", "new_trainer");
      if (a === "trainer_approve") { notify(next, "member", "approved"); notify(next, "trainer", "approved"); }
      if (a === "apply") { notify(next, "member", "applied"); notify(next, "trainer", "applied"); }
      if (a === "restore") notify(next, "member", "restore");
      if (["rejected", "blocked"].includes(next.proposal.status)) {
        notify(next, "member", next.proposal.status, reason); notify(next, "trainer", next.proposal.status, reason);
      }
      if (options.fault_before_commit) return fail("simulated_commit_failure");
      // One publication boundary for plan, history, approvals, audit and outbox.
      state = next; ledger.set(input.id, fingerprint);
      return {ok: true, reason, state: view()};
    }
    function inject(code) {
      if (!gates.includes(code)) throw Error("unknown_fixture_event");
      if (state.gate === code) return view();
      const next = clone(state); next.gate = code; next.revision++;
      if (code === "consent_revoked") next.consent = false;
      if (code === "no_trainer" || code === "relation_revoked") next.trainer = null;
      if (code === "version_conflict") next.refs.rulebook.revision++;
      if (next.proposal.status !== "applied") {
        next.proposal.status = "blocked"; next.proposal.member = "invalidated"; next.proposal.trainer = "invalidated";
      }
      next.proposal.reason = code;
      note(next, "source_event", "system", code, next.active.revision, "fixture-" + next.revision);
      notify(next, "member", "blocked", code); notify(next, "trainer", "blocked", code);
      state = next; return view();
    }
    function event(action, actor, id, target = null) {
      return {id, action, actor: actor === "member" ? state.member : "syn-trainer", subject: state.member,
        proposal_id: state.proposal.id, proposal_basis: state.proposal.basis, expected_revision: state.revision, target_version: target, reason: null};
    }
    return Object.freeze({view, command, inject, event});
  }
  return Object.freeze({create, clone, same});
});
