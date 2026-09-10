"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,id,integer,clone,same,ref,number,list,unique,reference,nullable,rir,rpe,load,reps}=require("./common.cjs");
const DAY=86400000;
const period=x=>exact(x,["start_ms","end_ms"])&&integer(x.start_ms)&&integer(x.end_ms)&&x.start_ms<x.end_ms;
const meta=["id","revision","subject_id","status","captured_at_ms","valid_from_ms","valid_until_ms"];
const version=x=>id(x.id)&&integer(x.revision)&&id(x.subject_id)&&["active","revoked","inactive"].includes(x.status)&&
 integer(x.captured_at_ms)&&integer(x.valid_from_ms)&&nullable(x.valid_until_ms,integer)&&(x.valid_until_ms===null||x.valid_until_ms>x.valid_from_ms);
const effortRule=x=>exact(x,["required","min","max"])&&typeof x.required==="boolean"&&number(x.min)&&number(x.max)&&x.min<=x.max;
const rule=x=>exact(x,["id","exercise_id","catalog_revision","workout_id","variant_id","equipment_id","set_count","unit",
 "minimum_sessions","comparable_plan_refs","comparable_goal_refs","reps_step","reps_ceiling","reset_reps","available_weights","rir","rpe","forbidden_effort_pairs","maintain_when"])&&
 id(x.id)&&id(x.exercise_id)&&integer(x.catalog_revision)&&id(x.workout_id)&&id(x.variant_id)&&id(x.equipment_id)&&
 integer(x.set_count)&&x.set_count>0&&x.set_count<=100&&["kg","lb"].includes(x.unit)&&
 integer(x.minimum_sessions)&&x.minimum_sessions>0&&x.minimum_sessions<=100&&
 list(x.comparable_plan_refs,50,reference)&&list(x.comparable_goal_refs,50,reference)&&
 integer(x.reps_step)&&x.reps_step>0&&integer(x.reps_ceiling)&&x.reps_ceiling>0&&
 integer(x.reset_reps)&&x.reset_reps>0&&x.reset_reps<=x.reps_ceiling&&
 list(x.available_weights,1000,number)&&x.available_weights.every((v,i,a)=>i===0||v>a[i-1])&&
 effortRule(x.rir)&&rir(x.rir.min)&&rir(x.rir.max)&&effortRule(x.rpe)&&rpe(x.rpe.min)&&rpe(x.rpe.max)&&
 list(x.forbidden_effort_pairs,100,p=>exact(p,["rir","rpe"])&&rir(p.rir)&&rpe(p.rpe))&&
 x.maintain_when==="target_or_effort_not_met";
const snapshotSet=x=>exact(x,["index","reps","load","rir","rpe"])&&integer(x.index)&&x.index>0&&reps(x.reps)&&load(x.load)&&nullable(x.rir,rir)&&nullable(x.rpe,rpe);
const snapshotExercise=x=>exact(x,["exercise_id","catalog_revision","variant_id","equipment_id","sets"])&&id(x.exercise_id)&&integer(x.catalog_revision)&&id(x.variant_id)&&id(x.equipment_id)&&
 list(x.sets,100,snapshotSet)&&x.sets.length>0&&x.sets.every((s,i)=>s.index===i+1);
const snapshot=x=>exact(x,["id","subject_id","session_id","captured_at_ms","plan_ref","goal_ref","workout_id","exercises"])&&
 id(x.id)&&id(x.subject_id)&&id(x.session_id)&&integer(x.captured_at_ms)&&reference(x.plan_ref)&&reference(x.goal_ref)&&id(x.workout_id)&&
 list(x.exercises,100,snapshotExercise)&&unique(x.exercises.map(e=>e.exercise_id));
const log=x=>exact(x,["id","subject_id","session_id","snapshot_id","exercise_id","set_index","completed","reps","load","rir","rpe","quality"])&&
 id(x.id)&&id(x.subject_id)&&id(x.session_id)&&id(x.snapshot_id)&&id(x.exercise_id)&&integer(x.set_index)&&x.set_index>0&&typeof x.completed==="boolean"&&
 nullable(x.reps,v=>integer(v)&&v<=1000000000)&&load(x.load)&&nullable(x.rir,rir)&&nullable(x.rpe,rpe)&&["confirmed","disputed"].includes(x.quality);
const session=x=>exact(x,["id","revision","subject_id","workout_id","status","started_at_ms","completed_at_ms","snapshot","sets"])&&
 id(x.id)&&integer(x.revision)&&id(x.subject_id)&&id(x.workout_id)&&["completed","in_progress"].includes(x.status)&&integer(x.started_at_ms)&&integer(x.completed_at_ms)&&snapshot(x.snapshot)&&list(x.sets,10000,log);
function validate(request,now,base){
 const p=request.policy,h=request.history,s=request.base.sources,subject=s.subject_id;
 const bad=(reason,status="invalid_input")=>({valid:false,reason,status});
 if(p===null)return bad("missing_policy","unavailable");
 if(!exact(p,[...meta,"trainer_id","relationship_ref","authority_ref","plan_ref","goal_ref","limits_ref","purpose","permission",
  "required_approvals","current_week","next_week","evaluation_window","history_window","rules"])||!version(p)||!id(p.trainer_id)||
  !["relationship_ref","authority_ref","plan_ref","goal_ref","limits_ref"].every(k=>reference(p[k]))||
  p.purpose!=="synthetic_test_rules_only"||p.permission!=="simulate_progression_and_plan_review"||
  !same(p.required_approvals,["member","trainer"])||![p.current_week,p.next_week,p.evaluation_window,p.history_window].every(period)||
  !list(p.rules,100,rule)||!unique(p.rules.map(r=>r.id))||!unique(p.rules.map(r=>r.exercise_id)))return bad("policy_shape");
 if(p.subject_id!==subject||p.trainer_id!==s.relationship.trainer_id)return bad("policy_identity");
 if(p.captured_at_ms>now)return bad("policy_time");
 if(p.status!=="active"||p.valid_from_ms>now||p.valid_until_ms!==null&&p.valid_until_ms<=now)return bad("policy_not_current","unavailable");
 if([["relationship_ref","relationship"],["authority_ref","authority"],["plan_ref","plan"],["goal_ref","goal"],["limits_ref","limits"]].some(([a,b])=>!same(p[a],ref(s[b]))))return bad("policy_binding","unavailable");
 if(p.current_week.end_ms-p.current_week.start_ms!==7*DAY||p.next_week.end_ms-p.next_week.start_ms!==7*DAY||
  p.next_week.start_ms!==p.current_week.end_ms||p.evaluation_window.start_ms<p.current_week.start_ms||p.evaluation_window.end_ms>p.next_week.start_ms||
  p.history_window.end_ms>p.evaluation_window.start_ms)return bad("policy_window");
 if(now<p.evaluation_window.start_ms||now>=p.evaluation_window.end_ms)return bad("evaluation_window","unavailable");
 if(h===null)return bad("missing_history","unavailable");
 if(!exact(h,["id","revision","subject_id","read_at_ms","coverage","sessions"])||!reference(ref(h))||!id(h.subject_id)||!integer(h.read_at_ms)||
  !exact(h.coverage,["start_ms","end_ms","complete","workout_id"])||!integer(h.coverage.start_ms)||!integer(h.coverage.end_ms)||
  typeof h.coverage.complete!=="boolean"||!id(h.coverage.workout_id)||!list(h.sessions,100,session)||!unique(h.sessions.map(x=>x.id)))return bad("history_shape");
 if(h.subject_id!==subject)return bad("history_identity");
 if(!exact(request.expected_progression,["policy_ref","history_ref"])||!reference(request.expected_progression.policy_ref)||!reference(request.expected_progression.history_ref))return bad("progression_readset_shape");
 if(h.read_at_ms!==now||!same(request.expected_progression.policy_ref,ref(p))||!same(request.expected_progression.history_ref,ref(h)))return bad("stale_progression_readset","unavailable");
 if(!h.coverage.complete)return bad("incomplete_history","unavailable");
 if(h.coverage.start_ms!==p.history_window.start_ms||h.coverage.end_ms!==p.history_window.end_ms)return bad("history_window","unavailable");
 if(h.coverage.workout_id!==base.candidate.workout_id)return bad("history_binding");
 const keys=new Set(),logIds=new Set(),snapshotIds=new Set();
 for(const x of h.sessions){
  if(x.subject_id!==subject||x.snapshot.subject_id!==subject||x.sets.some(t=>t.subject_id!==subject))return bad("history_identity");
  if(x.started_at_ms>x.completed_at_ms||x.completed_at_ms>now||x.snapshot.captured_at_ms>x.started_at_ms)return bad("history_time");
  if(x.completed_at_ms<p.history_window.start_ms||x.completed_at_ms>p.history_window.end_ms)return bad("history_window","unavailable");
  if(x.workout_id!==h.coverage.workout_id||x.snapshot.workout_id!==x.workout_id||x.snapshot.session_id!==x.id||snapshotIds.has(x.snapshot.id))return bad("history_binding");
  snapshotIds.add(x.snapshot.id);
  if(!unique(x.sets.map(t=>t.exercise_id+":"+t.set_index))||!unique(x.snapshot.exercises.map(t=>t.exercise_id)))return bad("history_binding");
  for(const t of x.sets){
   const e=x.snapshot.exercises.find(e=>e.exercise_id===t.exercise_id);
   if(t.session_id!==x.id||t.snapshot_id!==x.snapshot.id||!e||!e.sets.some(s=>s.index===t.set_index)||logIds.has(t.id))return bad("history_binding");
   logIds.add(t.id);
  }
  if(x.status!=="completed"||x.sets.some(t=>!t.completed||t.reps===null||t.load.value===null)||
    x.snapshot.exercises.reduce((n,e)=>n+e.sets.length,0)!==x.sets.length)return bad("incomplete_history","unavailable");
  if(keys.has(x.completed_at_ms))return bad("ambiguous_session_order","unavailable");keys.add(x.completed_at_ms);
 }
 const exerciseIds=new Set(base.candidate.rows.map(r=>r.exercise_id));
 if(p.rules.some(r=>!exerciseIds.has(r.exercise_id)||r.workout_id!==base.candidate.workout_id))return bad("policy_binding","unavailable");
 return {valid:true,policy:p,history:h};
}
function calculate(rule,targets,history){
 const fail=(reason,detail=null)=>({status:"unavailable",reason,detail});
 if(!rule)return fail("missing_rule");
 if(targets.length!==rule.set_count)return fail("set_count_mismatch");
 const current=targets[0].target,unit=current.load.unit;
 if(targets.some(r=>r.target.reps.min!==r.target.reps.max||!same(r.target.reps,current.reps)||!same(r.target.load,current.load)))return fail("point_target_required");
 if(rule.unit!==unit||targets.some(r=>r.catalog_ref.revision!==rule.catalog_revision))return fail("history_not_comparable");
 if(history.sessions.length<rule.minimum_sessions)return fail("insufficient_sessions");
 const sessions=[...history.sessions].sort((a,b)=>b.completed_at_ms-a.completed_at_ms).slice(0,rule.minimum_sessions);
 if(history.sessions.some(x=>x.sets.some(t=>t.exercise_id===rule.exercise_id&&
  (t.quality!=="confirmed"||rule.forbidden_effort_pairs.some(p=>p.rir===t.rir&&p.rpe===t.rpe)))))return fail("conflicting_effort","disputed_record");
 const observations=[];
 for(const x of sessions){
  const e=x.snapshot.exercises.find(e=>e.exercise_id===rule.exercise_id);
  if(!rule.comparable_plan_refs.some(r=>same(r,x.snapshot.plan_ref)))return fail("history_not_comparable","historical_plan_ref");
  if(!rule.comparable_goal_refs.some(r=>same(r,x.snapshot.goal_ref)))return fail("history_not_comparable","historical_goal_ref");
  if(!e||e.catalog_revision!==rule.catalog_revision)return fail("history_not_comparable","exercise_identity");
  if(e.equipment_id!==rule.equipment_id)return fail("history_not_comparable","equipment");
  if(e.variant_id!==rule.variant_id)return fail("history_not_comparable","variant");
  if(e.sets.length!==rule.set_count)return fail("history_not_comparable","set_count");
  for(const t of e.sets){
   const actual=x.sets.find(a=>a.exercise_id===rule.exercise_id&&a.set_index===t.index);
   if(!actual||t.reps.min!==t.reps.max||t.reps.min!==current.reps.min||!same(t.load,current.load)||actual.load.unit!==unit||actual.load.value!==current.load.value)return fail("history_not_comparable");
   if(actual.quality!=="confirmed"||rule.forbidden_effort_pairs.some(p=>p.rir===actual.rir&&p.rpe===actual.rpe))return fail("conflicting_effort");
   if(rule.rir.required&&actual.rir===null)return fail("missing_effort","rir");
   if(rule.rpe.required&&actual.rpe===null)return fail("missing_effort","rpe");
   observations.push({session_ref:ref(x),snapshot_id:x.snapshot.id,plan_ref:clone(x.snapshot.plan_ref),goal_ref:clone(x.snapshot.goal_ref),
    completed_at_ms:x.completed_at_ms,set_id:actual.id,set_index:actual.set_index,reps:actual.reps,load:clone(actual.load),rir:actual.rir,rpe:actual.rpe});
  }
 }
 const met=observations.every(x=>x.reps>=current.reps.min&&
  (x.rir===null||x.rir>=rule.rir.min&&x.rir<=rule.rir.max)&&(x.rpe===null||x.rpe>=rule.rpe.min&&x.rpe<=rule.rpe.max));
 let kind="maintain",reason="target_or_effort_not_met",nextReps=current.reps.min,nextLoad=current.load.value;
 if(met){
  if(current.reps.min<rule.reps_ceiling){
   nextReps+=rule.reps_step;if(nextReps>rule.reps_ceiling)return fail("rep_step_unavailable");
   kind="increase_reps";reason="all_required_targets_met_below_ceiling";
  }else if(current.reps.min===rule.reps_ceiling){
   const at=rule.available_weights.indexOf(current.load.value);
   if(at<0||at+1>=rule.available_weights.length)return fail("weight_step_unavailable");
   nextLoad=rule.available_weights[at+1];nextReps=rule.reset_reps;kind="increase_weight";reason="all_required_targets_met_at_ceiling";
  }else return fail("rule_target_conflict");
 }
 if(targets.some(r=>nextReps<r.boundary.reps.min||nextReps>r.boundary.reps.max||nextLoad<r.boundary.load.min||nextLoad>r.boundary.load.max||unit!==r.boundary.load.unit))return fail("proposal_outside_limits");
 return {status:"available",kind,reason,current_plan:{sets:targets.length,reps:current.reps.min,load:clone(current.load)},
  next_week:{sets:targets.length,reps:nextReps,load:{value:nextLoad,unit}},observations,rule:clone(rule),
  boundaries:targets.map(r=>clone(r.boundary)),effort_is_self_report:true};
}
module.exports={validate,calculate};
