"use strict";
const old=require("../../phase6e4/test/fixtures.cjs"),engine=require("../engine.cjs"),review=require("../review.cjs");
const {clone,ref,hash}=require("../common.cjs"),prereg=require("../preregistered-cases.json");
const DAY=86400000;
const safety=new Set(["current","unclassified","self_reported","serious_recovered","recurring","new_after_recovery","expired","expired_fresh","missing","missing_fresh","unnecessary_fresh","unclear","technical","clarified","technical_retry"]);
function setup(name="normal",locale="nl"){
 const config={locale};
 if(safety.has(name))config.scenario=name;
 if(name==="mixed_complaint")config.text="Ik bekijk mijn trainingsregistratie. Nu heb ik moeite met ademhalen";
 if(name==="known_language_miss")config.text="Ik inspecteer mijn trainingslogboek";
 const f=old.setup(config),s=f.request.sources,now=f.clock,workout=s.plan.options[0];
 const models=prereg.fixture_contract.exercises;
 workout.exercises=models.map(m=>({exercise_id:m.id,catalog_revision:1,sets:Array.from({length:2},(_,i)=>({
  index:i+1,reps:{min:m.current.reps,max:m.current.reps},load:{value:m.current.weight,unit:"kg"},rir:null,rpe:null}))}));
 s.catalog=models.map((m,i)=>({id:m.id,revision:1,labels:[{nl:"Squat",en:"Squat",de:"Kniebeuge"},{nl:"Roeien",en:"Row",de:"Rudern"},{nl:"Schouderdrukken",en:"Shoulder press",de:"Schulterdruecken"}][i]}));
 s.limits.rules=workout.exercises.flatMap(e=>e.sets.map(t=>({id:"syn-limit-"+e.exercise_id.slice(4)+"-"+t.index,workout_id:workout.workout_id,exercise_id:e.exercise_id,set_index:t.index,
  reps:{min:6,max:12},load:{min:0,max:100,unit:"kg"},allowed:true})));
 const history={id:"syn-history",revision:1,subject_id:s.subject_id,read_at_ms:now,
  coverage:{start_ms:now-14*DAY,end_ms:now,complete:true,workout_id:workout.workout_id},sessions:[]};
 for(let i=0;i<2;i++){
  const sessionId="syn-session-"+(i+1),snapshotId="syn-snapshot-"+(i+1),end=now-(i===0?7:2)*DAY,start=end-3600000;
  const snapshot={id:snapshotId,subject_id:s.subject_id,session_id:sessionId,captured_at_ms:start,plan_ref:{id:s.plan.id,revision:2},
   goal_ref:{id:s.goal.id,revision:1},workout_id:workout.workout_id,exercises:workout.exercises.map(e=>({
    ...clone(e),variant_id:"syn-variant-"+e.exercise_id.slice(4),equipment_id:"syn-equipment-"+e.exercise_id.slice(4)}))};
  const sets=snapshot.exercises.flatMap((e,j)=>e.sets.map(t=>({id:"syn-log-"+(i+1)+"-"+j+"-"+t.index,subject_id:s.subject_id,
   session_id:sessionId,snapshot_id:snapshotId,exercise_id:e.exercise_id,set_index:t.index,completed:true,reps:models[j].recent[i],
   load:clone(t.load),rir:1,rpe:8,quality:"confirmed"})));
  history.sessions.push({id:sessionId,revision:1,subject_id:s.subject_id,workout_id:workout.workout_id,status:"completed",started_at_ms:start,completed_at_ms:end,snapshot,sets});
 }
 const policy={id:"syn-test-policy",revision:1,subject_id:s.subject_id,status:"active",captured_at_ms:now-500,valid_from_ms:now-DAY,valid_until_ms:null,
  trainer_id:s.relationship.trainer_id,relationship_ref:ref(s.relationship),authority_ref:ref(s.authority),plan_ref:ref(s.plan),goal_ref:ref(s.goal),limits_ref:ref(s.limits),
  purpose:"synthetic_test_rules_only",permission:"simulate_progression_and_plan_review",required_approvals:["member","trainer"],
  current_week:{start_ms:now-5*DAY,end_ms:now+2*DAY},next_week:{start_ms:now+2*DAY,end_ms:now+9*DAY},
  evaluation_window:{start_ms:now,end_ms:now+DAY},history_window:{start_ms:history.coverage.start_ms,end_ms:history.coverage.end_ms},
  rules:models.map(m=>({id:"syn-test-rule-"+m.id.slice(4),exercise_id:m.id,catalog_revision:1,workout_id:workout.workout_id,
   variant_id:"syn-variant-"+m.id.slice(4),equipment_id:"syn-equipment-"+m.id.slice(4),set_count:2,unit:"kg",minimum_sessions:2,
   comparable_plan_refs:[{id:s.plan.id,revision:2}],comparable_goal_refs:[{id:s.goal.id,revision:1}],
   reps_step:m.rule.reps_step,reps_ceiling:m.rule.reps_ceiling,reset_reps:m.rule.reset_reps,available_weights:clone(m.rule.weights),
   rir:{required:false,min:0,max:10},rpe:{required:false,min:1,max:10},forbidden_effort_pairs:[],maintain_when:"target_or_effort_not_met"}))};
 const request={synthetic_only:true,locale,binding:clone(f.context.binding),base:f.request,expected_progression:{policy_ref:ref(policy),history_ref:ref(history)},policy,history};
 Object.assign(f,{request,policy,history});
 const r=policy.rules[0],a=history.sessions[0],t=a.sets[0],target=workout.exercises[0].sets[0];
 switch(name){
 case "lb": for(const e of workout.exercises)for(const t of e.sets)t.load.unit="lb";for(const x of s.limits.rules)x.load.unit="lb";for(const r of policy.rules)r.unit="lb";for(const x of history.sessions){for(const e of x.snapshot.exercises)for(const t of e.sets)t.load.unit="lb";for(const t of x.sets)t.load.unit="lb";}break;
 case "fractional_step":policy.rules[1].available_weights=[30,32.125,35];break;
 case "rir_zero":t.rir=0;break;
 case "optional_effort_missing":for(const x of history.sessions)for(const t of x.sets){t.rir=null;t.rpe=null;}break;
 case "required_rir_missing":r.rir.required=true;t.rir=null;break;
 case "required_rpe_missing":r.rpe.required=true;t.rpe=null;break;
 case "effort_rule_not_met":r.rir.min=2;break;
 case "effort_conflict":r.forbidden_effort_pairs=[{rir:1,rpe:8}];break;
 case "declared_conflict":t.quality="disputed";break;
 case "too_few_sessions":history.sessions.pop();break;
 case "missing_set":a.sets.pop();break;
 case "incomplete_session":a.status="in_progress";break;
 case "incomplete_coverage":history.coverage.complete=false;break;
 case "history_missing":request.history=null;break;
 case "history_old":a.completed_at_ms=history.coverage.start_ms-1;a.started_at_ms=a.completed_at_ms-100;a.snapshot.captured_at_ms=a.started_at_ms;break;
 case "history_future":a.completed_at_ms=now+1;break;
 case "session_wrong_member":a.subject_id="syn-other";break;
 case "set_wrong_member":t.subject_id="syn-other";break;
 case "set_wrong_session":t.session_id="syn-other";break;
 case "set_wrong_snapshot":t.snapshot_id="syn-other";break;
 case "set_wrong_exercise":t.exercise_id="syn-other";break;
 case "duplicate_session":history.sessions.push(clone(a));break;
 case "duplicate_set":a.sets.push(clone(t));break;
 case "unknown_catalog":s.catalog[0].revision=99;break;
 case "snapshot_after_start":a.snapshot.captured_at_ms=a.started_at_ms+1;break;
 case "historical_plan_unmapped":r.comparable_plan_refs=[];break;
 case "historical_goal_unmapped":r.comparable_goal_refs=[];break;
 case "different_equipment":a.snapshot.exercises[0].equipment_id="syn-different";break;
 case "different_variant":a.snapshot.exercises[0].variant_id="syn-different";break;
 case "historical_weight_changed":a.snapshot.exercises[0].sets[0].load.value=52.5;break;
 case "current_rep_range":target.reps.max=10;break;
 case "rule_missing":policy.rules.shift();break;
 case "rules_missing":request.policy=null;break;
 case "policy_not_test":policy.purpose="real_coaching";break;
 case "policy_wrong_member":policy.subject_id="syn-other";break;
 case "policy_wrong_trainer":policy.trainer_id="syn-other";break;
 case "policy_revoked":policy.status="revoked";break;
 case "policy_expired":policy.valid_until_ms=now;break;
 case "policy_wrong_plan":policy.plan_ref.revision=99;break;
 case "policy_wrong_goal":policy.goal_ref.revision=99;break;
 case "policy_wrong_limits":policy.limits_ref.revision=99;break;
 case "rules_duplicate":policy.rules.push(clone(r));break;
 case "no_trainer":s.relationship=null;break;
 case "trainer_revoked":s.authority.status="revoked";break;
 case "wrong_trainer_relationship":s.relationship.trainer_id="syn-other";break;
 case "stale_request":f.request.base.expected_readset.revision=99;break;
 case "stale_history_read":history.read_at_ms=now-1;break;
 case "stale_policy_ref":request.expected_progression.policy_ref.revision=99;break;
 case "evaluation_before":policy.evaluation_window.start_ms=now+1;break;
 case "evaluation_end":policy.evaluation_window={start_ms:now-1,end_ms:now};policy.history_window.end_ms=now-1;history.coverage.end_ms=now-1;break;
 case "evaluation_start":break;
 case "bad_next_week":policy.next_week.start_ms+=1;break;
 case "no_weight_step":policy.rules[1].available_weights=[30];break;
 case "step_not_listed":policy.rules[1].available_weights=[31,32.5];break;
 case "mixed_unit":s.limits.rules[0].load.unit="lb";break;
 case "history_mixed_unit":t.load.unit="lb";break;
 case "unknown_unit":target.load.unit="plates";break;
 case "reps_limit":s.limits.rules[0].reps.max=8;break;
 case "weight_limit":s.limits.rules.find(r=>r.exercise_id==="syn-row").load.max=32;break;
 case "max_weight_exact":s.limits.rules.filter(r=>r.exercise_id==="syn-row").forEach(r=>r.load.max=32.5);break;
 case "max_reps_exact":s.limits.rules.filter(r=>r.exercise_id==="syn-squat").forEach(r=>r.reps.max=9);break;
 case "unsupported_set_count":r.set_count=3;break;
 case "rir_invalid":t.rir=-1;break;
 case "rpe_zero":t.rpe=0;break;
 case "missing_reps":t.reps=null;break;
 case "nan_load":t.load.value=NaN;break;
 case "negative_load":t.load.value=-1;break;
 case "no_analysis_consent":f.authority.ai_analysis_consent=false;break;
 case "no_chat_consent":f.authority.private_chat_consent=false;break;
 }
 return f;
}
const run=(name="normal",locale="nl")=>{const f=setup(name,locale);return engine.propose(f.request,f.context,f.authority);};
function actor(f,role="member"){return {synthetic_only:true,subject_id:f.request.base.sources.subject_id,role,
 actor_id:role==="member"?f.request.base.sources.subject_id:f.request.policy.trainer_id,relationship_ref:clone(f.request.policy.relationship_ref)};}
function event(state,f,decision,role="member",eid=null){return {id:eid||"syn-event-"+decision+"-"+role+"-"+state.review_revision,
 decision,expected_review_revision:state.review_revision,proposal_id:state.proposal.id,proposal_revision:state.proposal.version,
 expected_plan_ref:clone(state.proposal.base_plan_ref),actor:actor(f,role)};}
function apply(state,f,decision,role="member",eid=null){return review.act(state,event(state,f,decision,role,eid),f.request,f.context,f.authority);}
function changedPlan(f){
 const s=f.request.base.sources;s.plan.revision++;s.readset.revision++;s.readset.current_refs.plan=ref(s.plan);
 f.request.base.expected_readset=ref(s.readset);
 for(const name of ["authority","limits","selection"])s[name].plan_ref=ref(s.plan);
 f.request.policy.plan_ref=ref(s.plan);f.request.policy.revision++;f.request.expected_progression.policy_ref=ref(f.request.policy);
 return f;
}
module.exports={setup,run,engine,review,clone,ref,hash,DAY,actor,event,apply,changedPlan,prereg,old};
