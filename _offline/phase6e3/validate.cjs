"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const { exact, id, integer, canonical } = require("../phase6e1/common.cjs");
const ref = r => exact(r, ["id","revision"]) && id(r.id) && integer(r.revision);
const nullable = (value, valid) => value === null || valid(value);
const number = n => typeof n === "number" && Number.isFinite(n) && n >= 0 && n <= 1000000000;
const reps = n => number(n) && Number.isInteger(n);
const rir = n => integer(n) && n <= 10;
const rpe = n => number(n) && n >= 1 && n <= 10 && Number.isInteger(n * 2);
const load = x => exact(x, ["value","unit"]) && nullable(x.value, number) &&
  nullable(x.unit, u => typeof u === "string" && /^[a-z_]{1,16}$/.test(u));
const range = x => exact(x, ["min","max"]) && reps(x.min) && reps(x.max) && x.min <= x.max;
const unique = xs => new Set(xs).size === xs.length;
const list = (xs, max, valid) => Array.isArray(xs) && xs.length <= max && xs.every(valid);
const tuple = x => x.exercise_id + ":" + x.index;
const target = x => exact(x, ["index","reps","load","rir","rpe"]) && integer(x.index) && x.index > 0 &&
  nullable(x.reps,range) && load(x.load) && nullable(x.rir,rir) && nullable(x.rpe,rpe);
const exercise = x => exact(x, ["exercise_id","catalog_revision","sets"]) && id(x.exercise_id) &&
  integer(x.catalog_revision) && list(x.sets,100,target) && x.sets.length > 0 &&
  x.sets.every((s,i) => s.index === i+1);
const catalogEntry = x => exact(x, ["id","revision","labels"]) && id(x.id) && integer(x.revision) &&
  exact(x.labels,["nl","en","de"]) && Object.values(x.labels).every(v =>
    typeof v === "string" && v.trim() === v && v.length > 0 && v.length <= 120 && !/[\u0000-\u001f<>]/.test(v));

function validateSources(s, subject, nowMs) {
  const bad = reason => ({valid:false, reason});
  if (!exact(s, ["synthetic_only","subject_id","session","snapshot","goal","catalog","recording"]) ||
      s.synthetic_only !== true || s.subject_id !== subject || !id(subject) || !integer(nowMs))
    return bad("source_envelope");
  const session = s.session;
  if (!exact(session, ["id","subject_id","started_at_ms","ended_at_ms","snapshot_ref","recording_ref"]) ||
      !id(session.id) || session.subject_id !== subject || !integer(session.started_at_ms) ||
      !integer(session.ended_at_ms) || session.ended_at_ms <= session.started_at_ms ||
      session.ended_at_ms - session.started_at_ms > 86400000 || session.ended_at_ms > nowMs ||
      !ref(session.snapshot_ref) || !ref(session.recording_ref)) return bad("session");
  const p = s.snapshot, g = s.goal, r = s.recording;
  if (p !== null && (!exact(p, ["id","revision","subject_id","session_id","kind","captured_at_ms","plan_ref","goal_link","exercises"]) ||
      !id(p.id) || !integer(p.revision) || p.subject_id !== subject || p.session_id !== session.id ||
      p.kind !== "historical_session_snapshot" || !integer(p.captured_at_ms) || p.captured_at_ms > session.started_at_ms ||
      !ref(p.plan_ref) || !list(p.exercises,100,exercise) || !unique(p.exercises.map(e=>e.exercise_id)) ||
      !(p.goal_link === null || (exact(p.goal_link,["id","revision","basis","at_ms"]) &&
        id(p.goal_link.id) && integer(p.goal_link.revision) && p.goal_link.basis === "member_selected_for_workout" &&
        integer(p.goal_link.at_ms) && p.goal_link.at_ms <= p.captured_at_ms)))) return bad("historical_snapshot");
  if (g !== null && (!exact(g, ["id","revision","subject_id","code","status_at_capture","captured_at_ms","valid_from_ms","valid_until_ms"]) ||
      !id(g.id) || !integer(g.revision) || g.subject_id !== subject || typeof g.code !== "string" ||
      !/^[a-z_]{1,40}$/.test(g.code) || !["active","inactive"].includes(g.status_at_capture) ||
      !integer(g.captured_at_ms) || g.captured_at_ms > nowMs || !integer(g.valid_from_ms) ||
      !nullable(g.valid_until_ms, integer) ||
      (g.valid_until_ms !== null && g.valid_until_ms < g.valid_from_ms))) return bad("goal");
  if (!list(s.catalog,100,catalogEntry) || !unique(s.catalog.map(c=>c.id+":"+c.revision))) return bad("catalog");
  const setValid = x => exact(x,["id","subject_id","session_id","exercise_id","index","reps","load","rir","rpe","occurred_at_ms"]) &&
    id(x.id) && x.subject_id === subject && x.session_id === session.id && id(x.exercise_id) &&
    integer(x.index) && x.index > 0 && nullable(x.reps,reps) && load(x.load) &&
    nullable(x.rir,rir) && nullable(x.rpe,rpe) && integer(x.occurred_at_ms) &&
    x.occurred_at_ms >= session.started_at_ms && x.occurred_at_ms <= session.ended_at_ms;
  if (r !== null && (!exact(r,["id","revision","subject_id","session_id","snapshot_ref","recorded_at_ms","coverage","sets"]) ||
      !id(r.id) || !integer(r.revision) || r.subject_id !== subject || r.session_id !== session.id ||
      !ref(r.snapshot_ref) || canonical(r.snapshot_ref) !== canonical(session.snapshot_ref) ||
      !integer(r.recorded_at_ms) || r.recorded_at_ms < session.ended_at_ms || r.recorded_at_ms > nowMs ||
      !["complete","partial"].includes(r.coverage) || !list(r.sets,10000,setValid) ||
      !unique(r.sets.map(x=>x.id)) || !unique(r.sets.map(tuple)))) return bad("recording");
  // A source revision may be unavailable; a record aimed at another actual set
  // is a binding error, not an invitation to pair it by list position.
  if (p && r && p.id === session.snapshot_ref.id && p.revision === session.snapshot_ref.revision) {
    const keys = new Set(p.exercises.flatMap(e=>e.sets.map(t=>tuple({exercise_id:e.exercise_id,index:t.index}))));
    if (r.sets.some(x=>!keys.has(tuple(x)))) return bad("set_binding");
  }
  return {valid:true};
}
module.exports = { validateSources, tuple };
