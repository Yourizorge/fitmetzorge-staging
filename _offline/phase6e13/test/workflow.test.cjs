"use strict";
const test=require("node:test"),a=require("node:assert/strict"),{build}=require("../build.cjs"),{create}=require("../../../proactive-signals-demo/model.js");
const data=build();
const setup=(locale="nl",name="changes")=>create(data.locales[locale][name]);
for(const locale of ["nl","en","de"])for(const name of data.scenarios)test(locale+" "+name+" arrival/replay/reset",()=>{
 const m=setup(locale,name),e=m.event("source_arrival","v1"),r=m.command(e);a(r.ok);a.equal(m.view().history.length,1);
 a.equal(m.view().cards.length,data.locales[locale][name].versions[0].result.status==="candidate_only"?1:0);
 a.equal(m.command(e).replayed,true);a.equal(m.view().history.length,1);a.equal(setup(locale,name).view().history.length,0);
});
test("distinct review and dismiss; neither changes plan",()=>{
 for(const action of ["review","dismiss"]){const m=setup();m.command(m.event("source_arrival","v1"));a(m.command(m.event(action)).ok);a.equal(m.view().cards[0].state,action==="review"?"reviewed":"dismissed");a(m.view().audit.every(e=>!e.plan_changed));a.equal(m.command(m.event(action)).reason,"not_pending");}
});
test("source arrival automatically emits once without member question",()=>{
 const m=setup();m.command(m.event("source_arrival","v1"));const before=m.view();a.equal(before.cards[0].state,"pending");
 const e=m.event("source_arrival","v1","syn-command-10");a.equal(m.command(e).reason,"source_already_seen");a.deepEqual(m.view(),before);
 a.equal(m.command({...e,type:"review"}).reason,"request_conflict");
});
test("correction supersedes old card; restore is new revision preserving old sources",()=>{
 const m=setup();m.command(m.event("source_arrival","v1"));m.command(m.event("review"));m.command(m.event("source_arrival","v2"));
 a.equal(m.view().cards[0].state,"superseded");a.equal(m.view().cards[1].state,"pending");
 a(m.command(m.event("source_arrival","v3")).ok);a.deepEqual(m.view().history.map(h=>h.revision),[1,2,3]);a(m.view().history[2].restore_of);a.equal(m.view().cards.filter(c=>c.state==="pending").length,1);
});
for(const type of ["apply","activate","trainer_approve","member_accept","delete","auth","send_notification"])test(type+" not in this scope",()=>{
 const m=setup();m.command(m.event("source_arrival","v1"));const before=m.view();a.equal(m.command(m.event(type)).ok,false);a.deepEqual(m.view(),before);
});
for(const type of ["expire","revoke"])test(type+" blocks pending and future requests without history deletion",()=>{
 const m=setup();m.command(m.event("source_arrival","v1"));a(m.command(m.event(type)).ok);
 a.equal(m.command(m.event("review")).reason,"access_withdrawn");a.equal(m.command(m.event("source_arrival","v2")).reason,"access_withdrawn");a.equal(m.view().cards[0].state,"withdrawn");a.equal(m.view().history.length,1);
});
test("failure before memory commit preserves entire state; explicit retry commits once",()=>{
 const m=setup(),e=m.event("source_arrival","v1"),before=m.view();a.equal(m.command(e,{failBeforeCommit:true}).reason,"simulated_before_commit_failure");a.deepEqual(m.view(),before);
 a(m.command(e).ok);a.equal(m.command(e).replayed,true);a.equal(m.view().history.length,1);
});
test("stale review and payload/source mismatch",()=>{
 const m=setup();m.command(m.event("source_arrival","v1"));const e=m.event("review");
 m.command(m.event("source_arrival","v2","syn-command-9"));a.equal(m.command(e).reason,"stale_request");
 const altered=m.event("review");altered.source_hash="0".repeat(64);a.equal(m.command(altered).reason,"source_mismatch");
});
test("duplicate command with different payload blocked",()=>{
 const m=setup(),e=m.event("source_arrival","v1");m.command(e);a.equal(m.command({...e,type:"apply"}).reason,"request_conflict");
});
test("wrong owner, arbitrary payload, old bundle and unknown source blocked",()=>{
 const m=setup(),e=m.event("source_arrival","v1");
 a.equal(m.command({...e,actor:"syn-trainer"}).reason,"invalid_actor_or_envelope");
 a.equal(m.command({...e,user_metadata:{role:"owner"}}).reason,"invalid_actor_or_envelope");
 a.equal(m.command({...e,source_hash:"0".repeat(64)}).reason,"payload_or_source_hash");
 a.equal(m.command({...e,source:"v9"}).reason,"payload_or_source_hash");
 a(m.command(e).ok);a.equal(m.command(m.event("source_arrival","v3")).reason,"source_lineage");
});
test("all public outputs exactly match executable deterministic build",()=>{
 const vm=require("node:vm"),fs=require("node:fs"),path=require("node:path"),ctx={};vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,"../../../proactive-signals-demo/data.js"),"utf8"),ctx);
 a.deepEqual(JSON.parse(JSON.stringify(ctx.FMZ13Data)),data);
});
