"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,id,integer,reference,clone,freeze,same,hash,ref}=require("../phase6e5/common.cjs");
const {access}=require("../phase6e1/analysis.cjs"),engine=require("./engine.cjs");
 const {view}=require("../phase6e4/context.cjs");
const issued=new WeakMap(),spaces=new WeakMap();
function workspace(option){
 const data=engine.details(option);if(!data)throw Error("issued_proposal_required");
 const token=freeze({subject_id:option.subject_id,initial_plan_ref:clone(option.base_plan_ref)});
 spaces.set(token,{active_plan:clone(data.base_plan),previous_plans:[],audit:[],events:new Map(),reviews:new Map()});return token;
}
function create(option,token=null){
 const data=engine.details(option);if(!data)throw Error("issued_proposal_required");
 if(token===null)token=workspace(option);
 const w=spaces.get(token);if(!w)throw Error("issued_workspace_required");
 if(token.subject_id!==option.subject_id)throw Error("workspace_subject");
 if(w.reviews.has(option.id))return w.reviews.get(option.id);
 if(!same(ref(w.active_plan),option.base_plan_ref)||hash(w.active_plan)!==option.base_plan_hash)throw Error("workspace_plan");
 const state=freeze({review_revision:0,status:"pending",proposal:option,member_acceptance:"pending",trainer_approval:"pending",application:"not_applied",
  active_plan:clone(w.active_plan),previous_plans:clone(w.previous_plans),audit:clone(w.audit),applications:0,
  automatic_actions_allowed:false,physical_advice_authorized:false,medical_clearance:false,storage_enabled:false,
  source_kind:"offline_simulated_not_authoritative"});
 issued.set(state,{token,locale:data.locale});w.reviews.set(option.id,state);return state;
}
function actorValid(a,p){
 return exact(a,["synthetic_only","subject_id","actor_id","role","relationship_ref"])&&a.synthetic_only===true&&a.subject_id===p.subject_id&&
 ["member","trainer"].includes(a.role)&&a.actor_id===(a.role==="member"?p.subject_id:p.trainer_id)&&same(a.relationship_ref,p.relationship_ref);
}
function act(state,event,request,ctx,authority,options={}){
 const meta=issued.get(state),c=engine.copy[meta?.locale||"en"],w=meta&&spaces.get(meta.token);
 const response=(s,reason,invalid=false)=>freeze({state:s,reason,status:invalid?"invalid_action":s.status,
  messages:[c.scope,c.states[invalid?"invalid":s.status],c.separate],automatic_actions_allowed:false,physical_advice_authorized:false});
 const invalid=reason=>response(state,reason,true);
 if(!meta||w.reviews.get(state.proposal.id)!==state)return invalid("stale_review");
 if(!exact(options,[])&&!exact(options,["fault_before_commit"]))return invalid("invalid_test_options");
 if(options.fault_before_commit!==undefined&&typeof options.fault_before_commit!=="boolean")return invalid("invalid_test_options");
 if(!exact(event,["id","decision","expected_review_revision","proposal_id","proposal_revision","expected_plan_ref","actor"])||
  !id(event.id)||!["view","accept","reject","apply"].includes(event.decision)||!integer(event.expected_review_revision)||
  event.proposal_id!==state.proposal.id||event.proposal_revision!==state.proposal.version||!reference(event.expected_plan_ref)||
  !same(event.expected_plan_ref,state.proposal.base_plan_ref)||!actorValid(event.actor,state.proposal))return invalid("wrong_actor_or_binding");
 if(!access(authority,state.proposal.subject_id).new_analysis)return invalid("access_unavailable");
 let current;try{current=view(ctx,request?.base?.binding,authority,meta.locale);}catch{return invalid("invalid_context");}
 if(!current.valid)return invalid("invalid_context");
 const eventHash=hash(event),seen=w.events.get(event.id);
 if(seen)return seen.hash===eventHash?response(state,"idempotent_retry"):invalid("idempotency_conflict");
 if(event.expected_review_revision!==state.review_revision)return invalid("stale_review_revision");
 if(event.decision==="view")return response(state,"view_only");
 if(state.status==="applied")return event.decision==="apply"&&event.actor.role==="trainer"?response(state,"already_applied"):invalid("terminal_state");
 if(["rejected","needs_recheck"].includes(state.status))return invalid("terminal_state");
 const commit=(values,reason,plan=w.active_plan,previous=w.previous_plans)=>{
  const status=values.status||state.status;
  const entry={index:w.audit.length+1,previous_hash:w.audit.at(-1)?.hash||null,event:clone(event),at_ms:ctx.evaluated_at_ms,
   proposal_ref:{id:state.proposal.id,revision:state.proposal.version},source_refs:clone(state.proposal.source_refs),
   source_basis_hash:state.proposal.basis_hash,rulebook_hash:state.proposal.rulebook_hash,
   before_plan_ref:ref(w.active_plan),after_plan_ref:ref(plan),before_plan_hash:hash(w.active_plan),after_plan_hash:hash(plan),
   resulting_status:status,reason};
  const audit=[...w.audit,freeze({...entry,hash:hash(entry)})],events=new Map(w.events);events.set(event.id,{hash:eventHash});
  const next=freeze({...state,...values,review_revision:state.review_revision+1,active_plan:clone(plan),previous_plans:clone(previous),audit:clone(audit)});
  const reviews=new Map(w.reviews);reviews.set(state.proposal.id,next);
  const aggregate={active_plan:clone(plan),previous_plans:clone(previous),audit,events,reviews};
  if(options.fault_before_commit)return invalid("simulated_commit_failure");
  // Publish plan, review, prior snapshot, audit and idempotency ledger together.
  spaces.set(meta.token,aggregate);issued.set(next,meta);return response(next,reason);
 };
 if(event.decision==="reject")return commit({status:"rejected",[event.actor.role==="member"?"member_acceptance":"trainer_approval"]:"rejected"},"rejected");
 if(event.decision==="apply"&&event.actor.role!=="trainer")return invalid("trainer_apply_required");
 if(!same(ref(w.active_plan),state.proposal.base_plan_ref)||hash(w.active_plan)!==state.proposal.base_plan_hash)
  return commit({status:"needs_recheck",member_acceptance:"invalidated",trainer_approval:"invalidated"},"active_plan_changed");
 const fresh=engine.propose(request,ctx,authority);
 if(!fresh.plan_option||fresh.plan_option.id!==state.proposal.id||fresh.plan_option.basis_hash!==state.proposal.basis_hash)
  return commit({status:"needs_recheck",member_acceptance:"invalidated",trainer_approval:"invalidated"},"fresh_validation_failed");
 if(event.decision==="accept"){
  const field=event.actor.role==="member"?"member_acceptance":"trainer_approval";
  if(state[field]==="accepted")return response(state,"already_approved");
  const values={[field]:"accepted"};
  values.status=(values.member_acceptance||state.member_acceptance)==="accepted"&&(values.trainer_approval||state.trainer_approval)==="accepted"?"approved":"pending";
  return commit(values,"approval_recorded");
 }
 if(state.member_acceptance!=="accepted"||state.trainer_approval!=="accepted")return invalid("approvals_missing");
 const plan=clone(w.active_plan),keys=new Set();
 for(const change of state.proposal.changes){
  const options=plan.options.filter(o=>o.workout_id===change.workout_id),exercise=options.length===1&&options[0].exercises.find(e=>e.exercise_id===change.exercise_id),
   index=exercise?.sets.findIndex(t=>t.index===change.set_index),key=change.workout_id+":"+change.exercise_id+":"+change.set_index;
  if(keys.has(key)||index===undefined||index<0||!same(exercise.sets[index],change.before))return invalid("plan_content_conflict");
  keys.add(key);exercise.sets[index]=clone(change.after);
 }
 if(!Number.isSafeInteger(plan.revision+1))return invalid("plan_revision_overflow");
 plan.revision+=1;
 return commit({status:"applied",application:"applied",applications:1},"applied_once",plan,[...w.previous_plans,clone(w.active_plan)]);
}
function inspect(token){
 const w=spaces.get(token);if(!w)throw Error("issued_workspace_required");
 return freeze({active_plan:clone(w.active_plan),previous_plans:clone(w.previous_plans),audit:clone(w.audit),event_count:w.events.size,
  reviews:[...w.reviews.values()].map(s=>({id:s.proposal.id,revision:s.review_revision,status:s.status}))});
}
module.exports={workspace,create,act,inspect};
