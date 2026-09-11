"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),f=require("./fixtures.cjs"),cases=require("../preregistered-cases.json");
const {review,setup,run,start,approved,act,event,clone,hash}=f;
const untouched=x=>{assert.equal(x.state.applications,0);assert.equal(x.state.application,"not_applied");assert.equal(x.state.active_plan.revision,3);};
function changed(x,name){
 const y=setup(name);const r=review.act(x.state,event(y,x.state,"trainer","apply"),y.request,y.context,y.authority);
 assert.equal(r.state.status,"needs_recheck");assert.equal(r.state.applications,0);assert.equal(r.state.active_plan.revision,3);
}
const checks={
 three_distinct_statuses(){
  const x=start();untouched(x);x.state=act(x.f,x.state,"member","accept").state;assert.equal(x.state.member_acceptance,"accepted");assert.equal(x.state.trainer_approval,"pending");untouched(x);
  x.state=act(x.f,x.state,"trainer","accept").state;assert.equal(x.state.status,"approved");untouched(x);
  x.state=act(x.f,x.state,"trainer","apply").state;assert.equal(x.state.application,"applied");assert.equal(x.state.active_plan.revision,4);assert.equal(x.state.applications,1);
 },
 trainer_first(){const x=start();x.state=act(x.f,x.state,"trainer","accept").state;assert.equal(x.state.member_acceptance,"pending");untouched(x);x.state=act(x.f,x.state,"member","accept").state;assert.equal(x.state.status,"approved");untouched(x);},
 member_cannot_apply(){const x=approved(),r=act(x.f,x.state,"member","apply");assert.equal(r.reason,"trainer_apply_required");assert.strictEqual(r.state,x.state);},
 approval_required(){const x=start(),r=act(x.f,x.state,"trainer","apply");assert.equal(r.reason,"approvals_missing");assert.strictEqual(r.state,x.state);},
 trainer_required(){const x=approved();changed(x,"no_trainer");},
 reject_member(){const x=start();const r=act(x.f,x.state,"member","reject");assert.equal(r.state.status,"rejected");assert.equal(r.state.member_acceptance,"rejected");assert.equal(act(x.f,r.state,"trainer","accept").reason,"terminal_state");},
 reject_trainer(){const x=approved(),r=act(x.f,x.state,"trainer","reject");assert.equal(r.state.status,"rejected");assert.equal(r.state.trainer_approval,"rejected");untouched({state:r.state});},
 duplicate_event(){const x=start(),e=event(x.f,x.state,"member","accept"),r=review.act(x.state,e,x.f.request,x.f.context,x.f.authority);const retry=review.act(r.state,e,x.f.request,x.f.context,x.f.authority);assert.equal(retry.reason,"idempotent_retry");assert.strictEqual(retry.state,r.state);},
 duplicate_apply(){const x=approved(),e=event(x.f,x.state,"trainer","apply"),r=review.act(x.state,e,x.f.request,x.f.context,x.f.authority);assert.equal(review.act(r.state,e,x.f.request,x.f.context,x.f.authority).reason,"idempotent_retry");assert.equal(act(x.f,r.state,"trainer","apply").reason,"already_applied");assert.equal(r.state.applications,1);},
 event_payload_conflict(){const x=start(),e=event(x.f,x.state,"member","accept"),r=review.act(x.state,e,x.f.request,x.f.context,x.f.authority);e.decision="reject";assert.equal(review.act(r.state,e,x.f.request,x.f.context,x.f.authority).reason,"idempotency_conflict");},
 wrong_actor(){const x=start(),e=event(x.f,x.state,"member","accept");e.actor.actor_id="syn-other";assert.equal(review.act(x.state,e,x.f.request,x.f.context,x.f.authority).status,"invalid_action");},
 wrong_relation(){const x=start(),e=event(x.f,x.state,"trainer","accept");e.actor.relationship_ref.revision=99;assert.equal(review.act(x.state,e,x.f.request,x.f.context,x.f.authority).status,"invalid_action");},
 wrong_proposal(){const x=start(),e=event(x.f,x.state,"trainer","accept");e.proposal_id="syn-other";assert.equal(review.act(x.state,e,x.f.request,x.f.context,x.f.authority).status,"invalid_action");},
 wrong_review_revision(){const x=start(),e=event(x.f,x.state,"member","accept");e.expected_review_revision=99;assert.equal(review.act(x.state,e,x.f.request,x.f.context,x.f.authority).reason,"stale_review_revision");},
 wrong_plan_revision(){const x=start(),e=event(x.f,x.state,"member","accept");e.expected_plan_ref.revision=99;assert.equal(review.act(x.state,e,x.f.request,x.f.context,x.f.authority).status,"invalid_action");},
 clone_proposal(){assert.throws(()=>review.create(clone(run(setup()).plan_option)),/issued_proposal_required/);},
 clone_review(){const x=start();assert.equal(review.act(clone(x.state),event(x.f,x.state,"member","accept"),x.f.request,x.f.context,x.f.authority).reason,"stale_review");},
 stale_review(){const x=start();act(x.f,x.state,"member","accept");assert.equal(act(x.f,x.state,"trainer","accept").reason,"stale_review");},
 source_change(){const x=approved();x.f.request.base.history.revision+=1;x.f.request.base.expected_progression.history_ref.revision+=1;assert.equal(act(x.f,x.state,"trainer","apply").state.status,"needs_recheck");},
 rulebook_revision_change(){const x=approved();x.f.book.revision+=1;x.f.request.expected_rulebook.revision+=1;const r=act(x.f,x.state,"trainer","apply");assert.equal(r.state.status,"needs_recheck");assert.equal(r.state.member_acceptance,"invalidated");},
 safety_after_approvals(){changed(approved(),"current");},
 self_report_after_approvals(){changed(approved(),"self_reported");},
 O5_after_approvals(){changed(approved(),"expired_fresh");},
 consent_revoked(){const x=approved();x.f.authority.ai_analysis_consent=false;const r=act(x.f,x.state,"trainer","apply");assert.equal(r.reason,"access_unavailable");assert.strictEqual(r.state,x.state);},
 no_partial_apply(){const x=approved();x.f.request.base.history.sessions[0].sets.pop();const r=act(x.f,x.state,"trainer","apply");assert.equal(r.state.status,"needs_recheck");assert.deepEqual(r.state.active_plan,x.state.active_plan);assert.equal(r.state.previous_plans.length,0);},
 parallel_proposals(){
  const x=approved(),y=setup();y.book.revision+=1;y.request.expected_rulebook.revision+=1;let s=review.create(run(y).plan_option,x.token);
  s=act(y,s,"member","accept").state;s=act(y,s,"trainer","accept").state;
  x.state=act(x.f,x.state,"trainer","apply").state;const r=act(y,s,"trainer","apply");assert.equal(r.reason,"active_plan_changed");assert.equal(review.inspect(x.token).active_plan.revision,4);assert.equal(review.inspect(x.token).previous_plans.length,1);
 },
 previous_plan_retained(){const x=approved(),before=clone(x.state.active_plan),r=act(x.f,x.state,"trainer","apply");assert.deepEqual(r.state.previous_plans,[before]);assert.deepEqual(x.f.request.base.base.sources.plan,before);},
 source_versions_retained(){const x=approved(),r=act(x.f,x.state,"trainer","apply");for(const a of r.state.audit){assert.deepEqual(a.source_refs,r.state.proposal.source_refs);assert.equal(a.source_basis_hash,r.state.proposal.basis_hash);assert.equal(a.rulebook_hash,r.state.proposal.rulebook_hash);}},
 hash_chained_audit(){const x=approved(),r=act(x.f,x.state,"trainer","apply");assert.equal(r.state.audit.length,3);let previous=null;for(const a of r.state.audit){const b=clone(a);delete b.hash;assert.equal(a.hash,hash(b));assert.equal(a.previous_hash,previous);previous=a.hash;}assert.notEqual(r.state.audit[2].before_plan_hash,r.state.audit[2].after_plan_hash);},
 failure_before_commit(){const x=approved(),before=review.inspect(x.token),e=event(x.f,x.state,"trainer","apply"),r=review.act(x.state,e,x.f.request,x.f.context,x.f.authority,{fault_before_commit:true});assert.equal(r.reason,"simulated_commit_failure");assert.strictEqual(r.state,x.state);assert.deepEqual(review.inspect(x.token),before);},
 retry_after_failure(){const x=approved(),e=event(x.f,x.state,"trainer","apply");review.act(x.state,e,x.f.request,x.f.context,x.f.authority,{fault_before_commit:true});const r=review.act(x.state,e,x.f.request,x.f.context,x.f.authority);assert.equal(r.reason,"applied_once");assert.equal(r.state.audit.length,3);assert.equal(review.inspect(x.token).event_count,3);},
 input_unchanged(){const x=approved(),before=clone(x.f.request);act(x.f,x.state,"trainer","apply");assert.deepEqual(x.f.request,before);},
 idempotency_across_proposals(){const x=start(),y=setup();y.book.revision+=1;y.request.expected_rulebook.revision+=1;const s=review.create(run(y).plan_option,x.token);x.state=act(x.f,x.state,"member","accept","syn-shared-event").state;const r=act(y,s,"member","accept","syn-shared-event");assert.equal(r.reason,"idempotency_conflict");}
};
for(const id of cases.review)test("preregistered review: "+id,()=>{assert.equal(typeof checks[id],"function",id);checks[id]();});
