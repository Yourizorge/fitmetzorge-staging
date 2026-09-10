"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),F=require("./fixtures.cjs"),{canonical}=require("../common.cjs");
function start(){const f=F.setup(),p=F.engine.propose(f.request,f.context,f.authority).plan_option;return {f,p,state:F.review.create(p)};}
function approved(s,f){s=F.apply(s,f,"accept","member").state;return F.apply(s,f,"accept","trainer").state;}
for(const c of F.prereg.approval_cases)test("preregistered approval: "+c.id,()=>{
 let {f,p,state}=start();const original=canonical(f.request),oldPlan=canonical(f.request.base.sources.plan),oldHistory=canonical(f.history);
 let result;
 switch(c.id){
 case "view_does_not_change_plan":result=F.apply(state,f,"view");assert.equal(result.state,state);break;
 case "member_accept_waits_for_trainer":result=F.apply(state,f,"accept");assert.equal(result.state.status,"pending");assert.deepEqual(result.state.approvals,["member"]);break;
 case "trainer_accept_waits_for_member":result=F.apply(state,f,"accept","trainer");assert.equal(result.state.status,"pending");assert.deepEqual(result.state.approvals,["trainer"]);break;
 case "both_approve_no_auto_apply":state=approved(state,f);assert.equal(state.status,"approved");assert.equal(state.simulated_plan,null);break;
 case "explicit_trainer_apply_once":state=approved(state,f);result=F.apply(state,f,"apply","trainer");assert.equal(result.state.status,"applied");assert.equal(result.state.applications,1);assert.equal(result.state.active_plan_ref.revision,4);break;
 case "member_cannot_apply":state=approved(state,f);result=F.apply(state,f,"apply","member");assert.equal(result.status,"invalid_action");assert.equal(result.state.applications,0);break;
 case "reject_keeps_original":result=F.apply(state,f,"reject");assert.equal(result.state.status,"rejected");break;
 case "trainer_reject_keeps_original":result=F.apply(state,f,"reject","trainer");assert.equal(result.state.status,"rejected");break;
 case "rejected_cannot_accept":state=F.apply(state,f,"reject").state;result=F.apply(state,f,"accept");assert.equal(result.status,"invalid_action");break;
 case "wrong_member_actor":case "wrong_trainer_actor":case "wrong_relationship_revision":case "wrong_proposal_id":case "wrong_proposal_revision":case "wrong_plan_revision":{
  const e=F.event(state,f,"accept",c.id==="wrong_trainer_actor"?"trainer":"member");
  if(c.id.includes("_actor"))e.actor.actor_id="syn-other";
  if(c.id==="wrong_relationship_revision")e.actor.relationship_ref.revision++;
  if(c.id==="wrong_proposal_id")e.proposal_id="syn-other";
  if(c.id==="wrong_proposal_revision")e.proposal_revision++;
  if(c.id==="wrong_plan_revision")e.expected_plan_ref.revision++;
  result=F.review.act(state,e,f.request,f.context,f.authority);assert.equal(result.status,"invalid_action");break;
 }
 case "changed_plan_needs_recheck":F.changedPlan(f);result=F.apply(state,f,"accept");assert.equal(result.state.status,"needs_recheck");break;
 case "changed_goal_needs_recheck":f.request.base.sources.goal.revision++;result=F.apply(state,f,"accept");assert.equal(result.state.status,"needs_recheck");break;
 case "changed_policy_needs_recheck":f.policy.revision++;f.request.expected_progression.policy_ref=F.ref(f.policy);result=F.apply(state,f,"accept");assert.equal(result.state.status,"needs_recheck");break;
 case "changed_history_needs_recheck":f.history.revision++;f.request.expected_progression.history_ref=F.ref(f.history);result=F.apply(state,f,"accept");assert.equal(result.state.status,"needs_recheck");break;
 case "new_safety_before_accept":{const fresh=F.setup("current");result=F.review.act(state,F.event(state,f,"accept"),fresh.request,fresh.context,fresh.authority);assert.equal(result.state.status,"needs_recheck");break;}
 case "self_report_before_apply":case "expired_context_before_apply":{
  state=approved(state,f);const fresh=F.setup(c.id==="self_report_before_apply"?"self_reported":"expired");
  result=F.review.act(state,F.event(state,f,"apply","trainer"),fresh.request,fresh.context,fresh.authority);assert.equal(result.state.status,"needs_recheck");assert.equal(result.state.applications,0);break;
 }
 case "revoked_authority_before_apply":state=approved(state,f);f.request.base.sources.authority.status="revoked";result=F.apply(state,f,"apply","trainer");assert.equal(result.state.status,"needs_recheck");assert.equal(result.state.applications,0);break;
 case "consent_withdrawn_before_apply":state=approved(state,f);f.authority.ai_analysis_consent=false;result=F.apply(state,f,"apply","trainer");assert.equal(result.status,"invalid_action");assert.equal(result.state.applications,0);break;
 case "duplicate_accept_same_event":case "same_event_different_payload":{
  const e=F.event(state,f,"accept");state=F.review.act(state,e,f.request,f.context,f.authority).state;
  if(c.id==="same_event_different_payload")e.decision="reject";
  result=F.review.act(state,e,f.request,f.context,f.authority);assert.equal(result.reason,c.id==="same_event_different_payload"?"idempotency_conflict":"idempotent_retry");assert.equal(result.state,state);break;
 }
 case "duplicate_accept_new_event":state=F.apply(state,f,"accept").state;result=F.apply(state,f,"accept","member","syn-another");assert.equal(result.reason,"already_approved");assert.equal(result.state,state);break;
 case "duplicate_apply_same_event":case "duplicate_apply_new_event":{
  state=approved(state,f);const e=F.event(state,f,"apply","trainer");state=F.review.act(state,e,f.request,f.context,f.authority).state;
  result=c.id==="duplicate_apply_same_event"?F.review.act(state,e,f.request,f.context,f.authority):F.apply(state,f,"apply","trainer","syn-another");
  assert.equal(result.reason,c.id==="duplicate_apply_same_event"?"idempotent_retry":"already_applied");assert.equal(result.state.applications,1);break;
 }
 case "stale_review_object":{const old=state;state=F.apply(state,f,"accept").state;result=F.apply(old,f,"accept","trainer");assert.equal(result.reason,"stale_review_object");break;}
 case "cloned_proposal_denied":assert.throws(()=>F.review.create(F.clone(p)),/issued_proposal/);break;
 case "reassessment_requires_new_approvals":{
  state=F.apply(state,f,"accept").state;F.changedPlan(f);state=F.apply(state,f,"accept","trainer").state;assert.equal(state.status,"needs_recheck");
  const next=F.engine.propose(f.request,f.context,f.authority).plan_option;assert.notEqual(next.id,p.id);
  const rechecked=F.review.create(next);assert.deepEqual(rechecked.approvals,[]);assert.equal(rechecked.status,"pending");break;
 }
 case "no_history_mutation":state=approved(state,f);state=F.apply(state,f,"apply","trainer").state;
  assert.equal(canonical(f.history),oldHistory);assert.equal(canonical(f.request.base.sources.plan),oldPlan);assert.equal(canonical(f.request),original);break;
 case "no_chat_sharing_or_safety_copy":assert.doesNotMatch(canonical(state),/message_text|safety_records|symptom|borstpijn/);break;
 default:assert.fail("unimplemented preregistered approval "+c.id);
 }
 if(result&&result.state.status!=="applied")assert.equal(result.state.applications,0);
 assert.equal((result?.state||state).medical_clearance,false);assert.equal((result?.state||state).physical_advice_authorized,false);
 assert.equal((result?.state||state).automatic_actions_allowed,false);
});
