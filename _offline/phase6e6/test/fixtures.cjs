"use strict";
const old=require("../../phase6e5/test/fixtures.cjs"),engine=require("../engine.cjs"),review=require("../review.cjs");
const {clone,ref,hash}=require("../../phase6e5/common.cjs");
const own=new Set(["type_rule","rulebook_missing","missing_rule","type_missing","ambiguous_rules","type_wrong_revision","rule_revoked","book_wrong_member","book_wrong_trainer","book_stale","book_expired","book_future","book_wrong_policy","rule_wrong_exercise","sets_conflict","min_reps_missing","min_reps_conflict","max_reps_conflict","step_missing","step_zero","step_off_grid","unit_unknown","weight_step_exact","reps_step_overflow","effort_hold","all_maintain","partial_facts"]);
function setup(name="normal",locale="nl"){
 const f=old.setup(own.has(name)?"normal":name,locale),base=f.request,p=base.policy,now=f.clock;
 const book={id:"syn-trainer-rulebook",revision:1,subject_id:p.subject_id,trainer_id:p.trainer_id,policy_ref:ref(p),status:"active",
  captured_at_ms:now-200,valid_from_ms:now-1000,valid_until_ms:null,
  bindings:p.rules.map(r=>({exercise_ref:{id:r.exercise_id,revision:r.catalog_revision},workout_id:r.workout_id,variant_id:r.variant_id,equipment_id:r.equipment_id,type_ref:null})),
  rules:p.rules.map(r=>{
   const q=clone(r);for(const k of ["id","exercise_id","catalog_revision","workout_id","variant_id","equipment_id","reps_ceiling"])delete q[k];
   Object.assign(q,{reps_min:8,reps_max:r.reps_ceiling,weight_step:2.5});
   return {id:r.id,revision:1,status:"active",selector:{kind:"exercise",ref:{id:r.exercise_id,revision:r.catalog_revision}},parameters:q};
  })};
 p.rules=[];f.request={synthetic_only:true,base,expected_rulebook:ref(book),rulebook:book};f.book=book;
 const r=book.rules[0],q=r.parameters;
 switch(name){
 case "type_rule":r.selector={kind:"type",ref:{id:"syn-lower-compound",revision:2}};book.bindings[0].type_ref=clone(r.selector.ref);break;
 case "rulebook_missing":f.request.rulebook=null;break;
 case "missing_rule":book.rules.shift();break;
 case "type_missing":r.selector={kind:"type",ref:{id:"syn-lower-compound",revision:2}};break;
 case "ambiguous_rules":book.bindings[0].type_ref={id:"syn-lower-compound",revision:2};book.rules.push({...clone(r),id:"syn-type-rule",selector:{kind:"type",ref:clone(book.bindings[0].type_ref)}});break;
 case "type_wrong_revision":r.selector={kind:"type",ref:{id:"syn-lower-compound",revision:2}};book.bindings[0].type_ref={id:"syn-lower-compound",revision:1};break;
 case "rule_revoked":r.status="revoked";break;
 case "book_wrong_member":book.subject_id="syn-other";break;
 case "book_wrong_trainer":book.trainer_id="syn-other";break;
 case "book_stale":f.request.expected_rulebook.revision=99;break;
 case "book_expired":book.valid_until_ms=now;break;
 case "book_future":book.captured_at_ms=now+1;break;
 case "book_wrong_policy":book.policy_ref.revision=99;break;
 case "rule_wrong_exercise":r.selector.ref.id="syn-other";break;
 case "sets_conflict":q.set_count=3;break;
 case "min_reps_missing":delete q.reps_min;break;
 case "min_reps_conflict":q.reps_min=9;break;
 case "max_reps_conflict":q.reps_max=7;break;
 case "step_missing":delete q.weight_step;break;
 case "step_zero":q.weight_step=0;break;
 case "step_off_grid":book.rules[1].parameters.available_weights=[30,32,35];break;
 case "unit_unknown":q.unit="plates";break;
 case "weight_step_exact":book.rules[1].parameters.weight_step=0.125;book.rules[1].parameters.available_weights=[30,30.125,30.25];break;
 case "reps_step_overflow":q.reps_step=3;break;
 case "effort_hold":q.rir.min=2;break;
 case "all_maintain":for(const s of base.history.sessions)for(const t of s.sets)t.reps=6;break;
 case "partial_facts":f.request.rulebook=null;base.history.sessions[0].sets[0].reps=null;break;
 }
 return f;
}
const run=f=>engine.propose(f.request,f.context,f.authority);
const actor=(f,role)=>({synthetic_only:true,subject_id:f.request.base.base.sources.subject_id,actor_id:role==="member"?f.request.base.base.sources.subject_id:f.book.trainer_id,role,relationship_ref:clone(f.request.base.policy.relationship_ref)});
const event=(f,s,role,decision,id="syn-event-"+role+"-"+decision+"-"+s.review_revision)=>({id,decision,expected_review_revision:s.review_revision,
 proposal_id:s.proposal.id,proposal_revision:s.proposal.version,expected_plan_ref:clone(s.proposal.base_plan_ref),actor:actor(f,role)});
const act=(f,s,role,decision,id)=>review.act(s,event(f,s,role,decision,id),f.request,f.context,f.authority);
function start(f=setup()){const result=run(f),token=review.workspace(result.plan_option),state=review.create(result.plan_option,token);return {f,result,token,state};}
function approved(f=setup()){const x=start(f);x.state=act(f,x.state,"member","accept").state;x.state=act(f,x.state,"trainer","accept").state;return x;}
module.exports={old,engine,review,setup,run,actor,event,act,start,approved,clone,ref,hash};
