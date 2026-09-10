"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,id,integer,clone,freeze,same,hash,reference,ref}=require("./common.cjs");
const {propose,proposalDetails,copy,fill}=require("./engine.cjs");
const {access}=require("../phase6e1/analysis.cjs");
const issued=new WeakMap(),superseded=new WeakSet(),workspaces=new WeakMap();
function workspace(option){
 const data=proposalDetails(option);if(!data)throw Error("issued_proposal_required");
 const token=freeze({subject_id:option.subject_id,initial_plan_ref:clone(option.base_plan_ref)});
 workspaces.set(token,{subject_id:option.subject_id,plan_ref:clone(option.base_plan_ref),plan_hash:option.base_plan_hash,reviews:new Map()});
 return token;
}
function create(option,token=null){
 const data=proposalDetails(option);if(!data)throw Error("issued_proposal_required");
 if(token===null)token=workspace(option);
 const w=workspaces.get(token);if(!w)throw Error("issued_workspace_required");
 if(w.subject_id!==option.subject_id)throw Error("workspace_plan_mismatch");
 if(w.reviews.has(option.id))return w.reviews.get(option.id);
 if(!same(w.plan_ref,option.base_plan_ref)||w.plan_hash!==option.base_plan_hash)throw Error("workspace_plan_mismatch");
 const state=freeze({version:1,review_revision:0,status:"pending",proposal:option,approvals:[],
  active_plan_ref:clone(option.base_plan_ref),simulated_plan:null,applications:0,
  automatic_actions_allowed:false,physical_advice_authorized:false,medical_clearance:false,storage_enabled:false});
 issued.set(state,{data,events:new Map(),locale:data.locale,workspace:w});w.reviews.set(option.id,state);return state;
}
function actorValid(actor,proposal){
 return exact(actor,["synthetic_only","subject_id","actor_id","role","relationship_ref"])&&actor.synthetic_only===true&&
 actor.subject_id===proposal.subject_id&&["member","trainer"].includes(actor.role)&&id(actor.actor_id)&&
 reference(actor.relationship_ref)&&same(actor.relationship_ref,proposal.relationship_ref)&&
 actor.actor_id===(actor.role==="member"?proposal.subject_id:proposal.trainer_id);
}
function act(state,event,request,context,authority){
 const data=issued.get(state),c=copy[data?.locale||"en"];
 const response=(next,reason,extra={})=>freeze({state:next,reason,...extra,
  messages:[c.scope,fill(c.states[next.status]||c.states.invalid,{pending:["member","trainer"].filter(x=>!next.approvals.includes(x)).map(x=>c.role_names[x]).join(", ")}),c.separate]});
 const invalid=reason=>freeze({state,reason,status:"invalid_action",messages:[c.scope,c.states.invalid,c.separate],automatic_actions_allowed:false,medical_clearance:false});
 if(!data||superseded.has(state))return invalid("stale_review_object");
 if(!exact(event,["id","decision","expected_review_revision","proposal_id","proposal_revision","expected_plan_ref","actor"])||
  !id(event.id)||!["view","accept","reject","apply"].includes(event.decision)||!integer(event.expected_review_revision)||
  event.proposal_id!==state.proposal.id||event.proposal_revision!==state.proposal.version||
  !reference(event.expected_plan_ref)||!same(event.expected_plan_ref,state.proposal.base_plan_ref)||!actorValid(event.actor,state.proposal))return invalid("wrong_actor_or_binding");
 if(!access(authority,state.proposal.subject_id).new_analysis)return invalid("access_unavailable");
 const eventHash=hash(event),seen=data.events.get(event.id);
 if(seen)return seen===eventHash?response(state,"idempotent_retry"):invalid("idempotency_conflict");
 if(event.expected_review_revision!==state.review_revision)return invalid("stale_review_revision");
 if(event.decision==="view")return response(state,"view_only");
 if(state.status==="applied")return event.decision==="apply"&&event.actor.role==="trainer"?response(state,"already_applied"):invalid("terminal_state");
 if(["rejected","needs_recheck"].includes(state.status))return invalid("terminal_state");
 const next=(values,reason)=>{
  const n=freeze({...state,...values,review_revision:state.review_revision+1}),events=new Map(data.events);events.set(event.id,eventHash);
  issued.set(n,{...data,events});data.workspace.reviews.set(state.proposal.id,n);superseded.add(state);return response(n,reason);
 };
 if(event.decision==="reject")return next({status:"rejected"},"rejected");
 if(event.decision==="apply"&&event.actor.role!=="trainer")return invalid("trainer_apply_required");
 if(!same(data.workspace.plan_ref,state.proposal.base_plan_ref)||data.workspace.plan_hash!==state.proposal.base_plan_hash)
  return next({status:"needs_recheck",approvals:[]},"active_plan_changed");
 // Re-evaluate sources, context and permissions at every approval/application.
 // Never transfer signatures to a changed source, message or target-week version.
 const fresh=propose(request,context,authority);
 if(!fresh.plan_option||fresh.plan_option.id!==state.proposal.id||fresh.plan_option.basis_hash!==data.data.basis_hash)
  return next({status:"needs_recheck",approvals:[]},"fresh_validation_failed");
 if(event.decision==="accept"){
  if(state.approvals.includes(event.actor.role))return response(state,"already_approved");
  const approvals=[...state.approvals,event.actor.role].sort();
  return next({approvals,status:approvals.length===2?"approved":"pending"},"approval_recorded");
 }
 if(state.status!=="approved"||!["member","trainer"].every(r=>state.approvals.includes(r)))return invalid("approvals_missing");
 const plan=clone(data.data.base_plan);
 for(const change of state.proposal.changes){
  const option=plan.options.find(o=>o.workout_id===change.workout_id),exercise=option?.exercises.find(e=>e.exercise_id===change.exercise_id);
  const index=exercise?.sets.findIndex(s=>s.index===change.set_index);
  if(index===undefined||index<0||!same(exercise.sets[index],change.before))return invalid("plan_content_conflict");
  exercise.sets[index]=clone(change.after);
 }
 // This object is deliberately NOT a live-authoritative plan/authority readset.
 const newRef={id:plan.id,revision:plan.revision+1};
 data.workspace.plan_ref=newRef;data.workspace.plan_hash=null;
 return next({status:"applied",active_plan_ref:newRef,applications:1,
  simulated_plan:{synthetic_only:true,source_kind:"offline_simulated_not_authoritative",base_ref:ref(plan),ref:newRef,
   options:plan.options,applied_proposal_id:state.proposal.id,live_reauthorization_required:true}},"applied_once");
}
module.exports={workspace,create,act};
