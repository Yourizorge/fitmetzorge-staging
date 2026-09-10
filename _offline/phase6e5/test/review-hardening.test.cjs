"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),F=require("./fixtures.cjs");
const approved=(s,f)=>F.apply(F.apply(s,f,"accept").state,f,"accept","trainer").state;
test("same simulation workspace deduplicates opening the exact proposal",()=>{
 const f=F.setup(),p=F.engine.propose(f.request,f.context,f.authority).plan_option,w=F.review.workspace(p);
 const first=F.review.create(p,w),second=F.review.create(p,w);assert.equal(first,second);
 const accepted=F.apply(first,f,"accept").state;assert.equal(F.review.create(p,w),accepted);
});
test("parallel proposals cannot both modify the same active simulated plan",()=>{
 const f=F.setup(),p=F.engine.propose(f.request,f.context,f.authority).plan_option,w=F.review.workspace(p);
 let one=F.review.create(p,w);one=approved(one,f);
 const other=F.setup();other.policy.rules[1].available_weights=[30,33,35];other.policy.revision++;other.request.expected_progression.policy_ref=F.ref(other.policy);
 const p2=F.engine.propose(other.request,other.context,other.authority).plan_option;assert.notEqual(p2.id,p.id);
 let two=F.review.create(p2,w);two=approved(two,other);
 const applied=F.apply(one,f,"apply","trainer");assert.equal(applied.state.applications,1);
 const denied=F.apply(two,other,"apply","trainer");assert.equal(denied.state.status,"needs_recheck");assert.equal(denied.state.applications,0);
 assert.equal(denied.reason,"active_plan_changed");
});
test("duplicate opening after application reuses its original result",()=>{
 const f=F.setup(),p=F.engine.propose(f.request,f.context,f.authority).plan_option,w=F.review.workspace(p);
 let s=approved(F.review.create(p,w),f);s=F.apply(s,f,"apply","trainer").state;
 const again=F.engine.propose(f.request,f.context,f.authority).plan_option;
 assert.equal(F.review.create(again,w),s);assert.equal(s.applications,1);
});
test("unrelated plan or member cannot join an issued simulation workspace",()=>{
 const f=F.setup(),p=F.engine.propose(f.request,f.context,f.authority).plan_option,w=F.review.workspace(p);
 const different=F.setup();F.changedPlan(different);const p2=F.engine.propose(different.request,different.context,different.authority).plan_option;
 assert.throws(()=>F.review.create(p2,w),/workspace_plan_mismatch/);
 assert.throws(()=>F.review.create(p,{}),/issued_workspace/);
});
test("review access uses the exact frozen authority shape, not truthy flags",()=>{
 const f=F.setup(),p=F.engine.propose(f.request,f.context,f.authority).plan_option,s=F.review.create(p);
 f.authority.authenticated="yes";
 assert.equal(F.apply(s,f,"view").status,"invalid_action");
});
test("disputed earlier record inside supplied window is not silently ignored",()=>{
 const f=F.setup(),x=F.clone(f.history.sessions[0]);x.id="syn-session-3";x.snapshot.id="syn-snapshot-3";x.snapshot.session_id=x.id;
 x.started_at_ms-=F.DAY;x.completed_at_ms-=F.DAY;x.snapshot.captured_at_ms=x.started_at_ms;
 for(const s of x.sets){s.id=s.id.replace("syn-log-1-","syn-log-3-");s.session_id=x.id;s.snapshot_id=x.snapshot.id;}
 x.sets[0].quality="disputed";f.history.sessions.push(x);
 const r=F.engine.propose(f.request,f.context,f.authority);assert.equal(r.rows[0].reason,"conflicting_effort");assert.equal(r.plan_option,null);
});
test("missing required RIR states the specific field without inventing a value",()=>{
 const r=F.run("required_rir_missing");assert.equal(r.rows[0].detail,"rir");assert(r.messages.some(s=>s.includes("RIR")&&s.includes("ontbreekt")));
});
test("unmapped historical plan identifies that exact missing comparison",()=>{
 const r=F.run("historical_plan_unmapped");assert.equal(r.rows[0].detail,"historical_plan_ref");
});
