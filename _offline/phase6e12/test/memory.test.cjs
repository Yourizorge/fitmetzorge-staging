"use strict";
const test=require("node:test"),a=require("node:assert/strict");
require("../../../workout-reflection-demo/data.js");
const M=require("../../../workout-reflection-demo/memory.js"),C=require("../core.cjs");
for(const [name,langs]of Object.entries(globalThis.FMZ6E12Data.profiles))for(const [locale,p]of Object.entries(langs))
test("public parity "+name+" "+locale,()=>{
 const f=C.fixture(name,locale),w=C.create(f),d=w.draft();a(w.register(d).ok);const expected=w.reflect();
 a.deepEqual(p.draft,d);a.deepEqual(p.pack,expected.pack);
 const demo=M.create(p);a(demo.register(p.draft.sets).ok);a(demo.reflect().ok);
 const state=demo.view().workflow;
 a.equal(state.proposal.status,w.view().workflow.proposal.status);
 a.deepEqual(state.proposal.target,w.view().workflow.proposal.target);
});
const p=globalThis.FMZ6E12Data.profiles.normal.nl;
test("unknown input never receives precomputed proposal",()=>{const m=M.create(p),sets=structuredClone(p.draft.sets);sets[0].reps=7;a(m.register(sets).ok);a.equal(m.reflect().reason,"not_example");a.equal(m.view().workflow.proposal.status,"blocked");a.deepEqual(m.view().workflow.active,m.view().workflow.proposal.target);});
for(const change of [s=>s[0].subject_id="other",s=>s[0].session_id="other",s=>s[0].snapshot_id="other",s=>s[0].id="other",s=>s[0].load.unit="lb",s=>s[0].rpe=0,s=>s[0].rir=-1,s=>s[1]=structuredClone(s[0]),s=>s[0].extra="x"])
test("public registration boundary "+String(change),()=>{const m=M.create(p),s=structuredClone(p.draft.sets);change(s);a.equal(m.register(s).ok,false);a.equal(m.view().records.length,0);});
test("public immutable source and independent effort",()=>{const m=M.create(p),s=structuredClone(p.draft.sets);s[0].rir=0;s[0].rpe=null;a(m.register(s).ok);const old=m.view().records[0];s[0].rir=1;a(m.register(s).ok);a.deepEqual(m.view().records[0],old);a.equal(old.sets[0].rir,0);a.equal(old.sets[0].rpe,null);});
for(const gate of ["version_conflict","consent_revoked","relation_revoked","expired"])test("public gate survives new reflection "+gate,()=>{const m=M.create(p);m.inject(gate);a(m.register(p.draft.sets).ok);a(m.reflect().ok);a.equal(m.view().workflow.proposal.status,"blocked");});
test("public atomic rollback and three steps",()=>{
 const m=M.create(p);m.register(p.draft.sets);m.reflect();
 const cmd=(a,r,id)=>m.command(m.event(a,r,id));
 a.equal(cmd("trainer_approve","trainer","cmd-early").ok,false);
 a(cmd("member_accept","member","cmd-m").ok);a(cmd("trainer_approve","trainer","cmd-t").ok);
 const before=JSON.stringify(m.view()),event=m.event("apply","trainer","cmd-a");
 a.equal(m.command(event,{fault_before_commit:true}).ok,false);a.equal(JSON.stringify(m.view()),before);
 a(m.command(event).ok);a(m.command(event).ok);a.equal(m.view().workflow.history.length,1);
});
