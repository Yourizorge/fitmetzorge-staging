"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),A=require("../adapter.cjs"),M=require("../../../training-review-demo/model.js");
test("approval commands cannot move between kg and lb proposals with equal local revisions",()=>{
 const kg=M.create(A.seed("normal")),lb=M.create(A.seed("lb"));
 const event=kg.event("member_accept","member","cmd-cross-proposal");
 assert.equal(lb.command(event).ok,false);
 assert.equal(lb.view().proposal.member,"pending");
});
for(const change of ["missing_change","duplicate_change","other_exercise","bad_weight","unit_swap","rir_swap","source_version","target_owner","blocked_partial"])
 test("reject tampered public mock seed "+change,()=>{
 const seed=A.seed();switch(change){
 case "missing_change":seed.changes.pop();break;
 case "duplicate_change":seed.changes.push(seed.changes[0]);break;
 case "other_exercise":seed.changes[0].exercise_id="unknown";break;
 case "bad_weight":seed.changes[0].after.load.value=-1;break;
 case "unit_swap":seed.changes[0].after.load.unit="lb";break;
 case "rir_swap":seed.changes[0].after.rir=0;break;
 case "source_version":seed.refs.plan.revision=99;break;
 case "target_owner":seed.target.subject_id="other";break;
 case "blocked_partial":seed.gate="unavailable";break;
 }assert.throws(()=>M.create(seed));
 });
test("O5 exact 30 days, earlier omission, retry and closed-null status preserve original expiry",()=>{
 const {plan}=require("../../phase6e1/retention.cjs"),DAY=86400000,at=10*DAY;
 const record={id:"syn-record",class:"unresolved_signal",created_at_ms:at,closed_at_ms:null,necessary:true,details_present:true};
 assert.equal(plan([record],at+30*DAY-1).items[0].disposition,"within_provisional_cap");
 const expired=plan([record],at+30*DAY);assert.equal(expired.items[0].disposition,"expire_in_projection");assert.equal(expired.medical_clearance,false);
 assert.equal(plan([{...record,necessary:false}],at+DAY).items[0].disposition,"omit_unnecessary");
 assert.equal(plan([record],at+31*DAY).items[0].expires_at_ms,at+30*DAY);
 assert.equal(plan([{...record,class:"closed_details"}],at+30*DAY).items[0].disposition,"expire_in_projection");
 assert.equal(A.seed("expired").gate,"unavailable");assert.equal(A.seed("missing").gate,"unavailable");
});
test("goal text is based on actual synthetic goal code, not invented goal history",()=>{
 assert.equal(A.seed().goal.code,"strength");assert.match(A.seed().goal.labels.nl,/kracht/);assert.equal(A.seed().goal.ref.revision,2);
});
test("missing restore and unknown command are refused",()=>{
 const m=M.create(A.seed());let i=0;
 const go=a=>m.command(m.event(a,a.startsWith("member")?"member":"trainer","cmd-"+(++i)));
 go("member_accept");go("trainer_approve");go("apply");
 const before=m.view();
 assert.equal(m.command(m.event("restore","member","cmd-missing",999)).reason,"missing_version");
 assert.equal(go("unknown").ok,false);assert.deepEqual(m.view(),before);
});
