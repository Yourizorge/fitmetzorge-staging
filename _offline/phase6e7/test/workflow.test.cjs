"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const A=require("../adapter.cjs"),M=require("../../../training-review-demo/model.js"),copy=require("../../../training-review-demo/copy.js");
const create=(name="normal")=>M.create(A.seed(name));
const go=(m,a,role=a.startsWith("member")?"member":"trainer",target=null,id=null,options)=>m.command(m.event(a,role,id||"cmd-"+a+"-"+m.view().revision,target),options);
function stage(name){
 const m=create();
 if(["trainer_pending","approved","applied","restore_pending"].includes(name))go(m,"member_accept");
 if(["approved","applied","restore_pending"].includes(name))go(m,"trainer_approve");
 if(["applied","restore_pending"].includes(name))go(m,"apply");
 if(name==="restore_pending")go(m,"restore","member",3);
 if(name==="rejected")go(m,"member_reject");
 if(name==="blocked"){go(m,"member_accept");go(m,"trainer_block");}
 return name==="maintained"?create("all_maintain"):m;
}
const expected={
 member_pending:{member:["member_accept","member_reject"],trainer:[]},
 trainer_pending:{member:[],trainer:["trainer_approve","trainer_reject","trainer_block"]},
 approved:{member:[],trainer:["apply"]},applied:{member:["restore"],trainer:["restore"]},
 restore_pending:{member:["member_accept","member_reject"],trainer:[]},
 rejected:{member:[],trainer:[]},blocked:{member:[],trainer:[]},maintained:{member:[],trainer:[]}
};
for(const state of Object.keys(expected))for(const role of ["member","trainer"])for(const action of ["member_accept","member_reject","trainer_approve","trainer_reject","trainer_block","apply","restore"])
 test(state+" / "+role+" / "+action,()=>{
 const m=stage(state),before=m.view(),r=go(m,action,role,action==="restore"?3:null);
 assert.equal(r.ok,expected[state][role].includes(action),r.reason);
 if(!r.ok)assert.deepEqual(m.view(),before);else if(action!=="apply")assert.deepEqual(m.view().active,before.active);
});
test("mixed reps weight maintain and full restore v3 v4 v5 v6",()=>{
 const seed=A.seed(),m=create(),before=m.view().active;
 assert.deepEqual(seed.rows.map(x=>x.kind),["increase_reps","increase_weight","maintain"]);
 assert.equal(go(m,"member_accept").state.active.revision,3);assert.equal(go(m,"trainer_approve").state.active.revision,3);
 assert.equal(go(m,"apply").state.active.revision,4);assert.deepEqual(m.view().history,[before]);
 assert.equal(m.view().active.options[0].exercises[0].sets[0].reps.min,9);
 assert.equal(m.view().active.options[0].exercises[1].sets[0].load.value,32.5);
 assert.deepEqual(m.view().active.options[0].exercises[2],before.options[0].exercises[2]);
 const r=go(m,"restore","member",3);assert(r.ok);assert.equal(r.state.proposal.member,"pending");assert.equal(r.state.proposal.trainer,"pending");
 assert.equal(go(m,"apply").ok,false);go(m,"member_accept");go(m,"trainer_approve");assert(go(m,"apply").ok);
 assert.equal(m.view().active.revision,5);assert.deepEqual({...m.view().active,revision:3},before);assert.deepEqual(m.view().history[0],before);
 assert(go(m,"restore","trainer",4).ok);go(m,"member_accept");go(m,"trainer_approve");assert(go(m,"apply").ok);
 assert.equal(m.view().active.revision,6);assert.equal(m.view().audit.filter(a=>a.action==="apply").length,3);
});
for(const code of ["version_conflict","expired","no_trainer","consent_revoked","relation_revoked","incomplete","unavailable"])
 for(const at of ["trainer_pending","approved","restore_pending"])test(code+" at "+at+" prevents partial writes",()=>{
 const m=stage(at),before=m.view();m.inject(code);assert.equal(m.view().proposal.status,"blocked");assert.equal(m.view().proposal.member,"invalidated");
 assert.equal(go(m,"apply").ok,false);assert.equal(go(m,"member_accept").ok,false);assert.deepEqual(m.view().active,before.active);assert.deepEqual(m.view().history,before.history);
});
for(const at of ["member_pending","trainer_pending","approved","applied","restore_pending"])test("atomic fault "+at,()=>{
 const m=stage(at),before=m.view(),a={member_pending:"member_accept",trainer_pending:"trainer_approve",approved:"apply",applied:"restore",restore_pending:"member_accept"}[at];
 const r=go(m,a,a==="member_accept"||a==="restore"?"member":"trainer",a==="restore"?3:null,null,{fault_before_commit:true});
 assert.equal(r.reason,"simulated_commit_failure");assert.deepEqual(m.view(),before);
});
test("identical retries and different command duplicate application",()=>{
 const m=stage("approved"),e=m.event("apply","trainer","cmd-stable");assert(m.command(e).ok);const after=m.view();
 for(let i=0;i<10;i++){assert.equal(m.command(e).reason,"idempotent_retry");assert.deepEqual(m.view(),after);}
 assert.equal(m.command({...e,action:"trainer_reject"}).reason,"idempotency_conflict");
 assert.equal(go(m,"apply").ok,false);assert.deepEqual(m.view(),after);
});
for(const field of ["subject","actor","proposal_id","expected_revision","extra","target_version","reason"])test("invalid binding "+field,()=>{
 const m=create(),e=m.event("member_accept","member","cmd-check"),before=m.view();
 e[field]=["expected_revision","target_version"].includes(field)?999:"wrong";
 assert.equal(m.command(e).ok,false);assert.deepEqual(m.view(),before);
});
for(const name of A.names.filter(x=>!["normal","lb","rir_zero","optional_effort_missing","all_maintain"].includes(x)))
 test("blocked fixture "+name,()=>{
 const s=A.seed(name),m=M.create(s),before=m.view().active;assert(s.gate);assert.equal(s.changes.length,0);assert.equal(m.view().proposal.status,"blocked");
 for(const action of ["member_accept","trainer_approve","apply","restore"])assert.equal(go(m,action,action==="member_accept"?"member":"trainer",action==="restore"?3:null).ok,false);
 assert.deepEqual(m.view().active,before);assert.equal(m.view().history.length,0);
});
test("W1 W2 exact step without fabricated alternative",()=>{
 const a=A.seed("ambiguous_rules"),b=A.seed("step_off_grid");assert.equal(a.gate,"ambiguous_rules");assert.equal(b.gate,"weight_step_conflict");
 const r=b.w2.find(x=>x.exercise==="syn-row");assert.equal(r.step,2.5);assert.deepEqual(r.available,[30,32,35]);assert.deepEqual(b.target,b.plan);assert.equal(b.changes.length,0);
});
test("units null and zero independent RIR RPE",()=>{
 assert.equal(A.seed("lb").target.options[0].exercises[1].sets[0].load.unit,"lb");
 assert(A.seed("rir_zero").rows[0].observations.some(o=>o.rir===0&&o.rpe===8));
 assert(A.seed("optional_effort_missing").rows.every(r=>r.observations.every(o=>o.rir===null&&o.rpe===null)));
});
test("fresh frozen source and consent check before private command",()=>{
 const f=A.fixtures.setup(),m=A.workspace(f);assert(go(m,"member_accept").ok);f.authority.ai_analysis_consent=false;assert.equal(go(m,"trainer_approve").ok,false);
 const g=A.fixtures.setup(),n=A.workspace(g);go(n,"member_accept");g.book.revision++;assert.equal(go(n,"trainer_approve").ok,false);
});
test("wrong synthetic owner and fixture rejected",()=>{
 assert.throws(()=>A.seed("real-member"));const f=A.fixtures.setup();f.request.base.base.sources.subject_id="other";assert.throws(()=>A.fromFixture(f));
 assert.throws(()=>M.create({...A.seed(),synthetic_only:false}));
});
test("withdrawal after application does not silently undo or allow restore",()=>{
 for(const code of ["consent_revoked","relation_revoked","unavailable"]){const m=stage("applied"),before=m.view().active;m.inject(code);assert.equal(go(m,"restore","member",3).ok,false);assert.deepEqual(m.view().active,before);}
});
test("immutable view and source-bound timestamped audit",()=>{
 const m=create();assert.throws(()=>{m.view().active.revision=999;});go(m,"member_accept");go(m,"trainer_approve");go(m,"apply");
 let last="";for(const a of m.view().audit){assert(a.at>last);last=a.at;assert(a.source_versions.plan);assert(a.proposal_basis);assert(a.reason);}
});
test("minimal notification keys, recipients and exact copy",()=>{
 const m=create();assert.deepEqual(m.view().notifications.map(n=>n.recipient),["member"]);
 go(m,"member_accept");assert.equal(m.view().notifications.at(-1).key,"new_trainer");
 go(m,"trainer_approve");assert.equal(m.view().notifications.filter(n=>n.key==="approved").length,2);
 go(m,"apply");assert.equal(m.view().notifications.filter(n=>n.key==="applied").length,2);
 assert.equal(copy.nl.new_member,"Youri heeft een voorstel voor je volgende training.");
 assert.equal(copy.nl.new_trainer,"Er wacht een trainingsvoorstel op jouw beoordeling.");
 assert.equal(copy.nl.approved_notice,"Het voorstel is goedgekeurd en wacht op toepassing.");
 assert.equal(copy.nl.applied_notice,"Je trainingsschema heeft een nieuwe versie.");
 for(const n of m.view().notifications)assert.deepEqual(Object.keys(n).sort(),["at","id","key","reason","recipient"]);
 assert.doesNotMatch(JSON.stringify(create("current").view().notifications),/borst|chest|Luft|message_id|chat|diagnos/i);
});
for(const locale of ["nl","en","de"])test("complete concept locale "+locale,()=>{
 assert.deepEqual(Object.keys(copy[locale]),Object.keys(copy.nl));assert(Object.values(copy[locale]).every(s=>typeof s==="string"&&s.length&&!s.includes("undefined")));
});
test("30 frozen examples exactly match original evidence",()=>{
 const generated=require("../../phase6e6/test/examples.cjs").generate(),saved=JSON.parse(fs.readFileSync("docs/PHASE6E6_EXAMPLES.json"));
 assert.equal(generated.length,30);assert.deepEqual(generated,Array.isArray(saved)?saved:saved.examples);
});
test("public generated data is allowlisted and reproducible",()=>{
 const text=fs.readFileSync("training-review-demo/data.js","utf8"),ctx={window:{}};vm.runInNewContext(text,ctx);
 assert.deepEqual(JSON.parse(JSON.stringify(ctx.window.FMZDemoData)),A.publicData());
 assert.doesNotMatch(text,/private_chat_consent|safety_records|message_id|require\(|_offline/);
});
