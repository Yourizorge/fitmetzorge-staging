"use strict";
const test=require("node:test"),a=require("node:assert/strict");
const {fixture,create,scenarios,clone,hash}=require("../core.cjs");
const start=(name="normal",locale="nl")=>{const f=fixture(name,locale),w=create(f),d=w.draft();a(w.register(d).ok);return {f,w,d,out:w.reflect()};};
for(const locale of ["nl","en","de"])for(const name of scenarios)test(locale+" "+name,()=>{
 const {out,w}=start(name,locale);a(out.ok);a(out.result.messages.length>0);a.equal(out.result.provider_calls,0);
 a.equal(out.result.automatic_actions_allowed,false);a.equal(out.result.physical_advice_authorized,false);
 a.equal(w.view().records.length,1);
 if(["normal","lb","type_rule","rir_zero","optional_effort_missing"].includes(name))a(out.result.plan_option);
 else if(name!=="all_maintain")a.equal(out.result.plan_option,null);
 if(name==="normal")a.deepEqual(out.result.rows.map(x=>x.kind),["increase_reps","increase_weight","maintain"]);
});
const cases={
 foreign_subject:d=>d.subject_id="syn-other",foreign_workspace:d=>d.workspace_id="syn-other",
 foreign_session:d=>d.session_id="syn-other",snapshot:d=>d.snapshot_id="syn-other",source_hash:d=>d.source_hash="0".repeat(64),
 snapshot_hash:d=>d.snapshot_hash="0".repeat(64),revision:d=>d.revision=99,extra:d=>d.token="synthetic-not-token",
 set_subject:d=>d.sets[0].subject_id="syn-other",set_session:d=>d.sets[0].session_id="syn-other",
 set_snapshot:d=>d.sets[0].snapshot_id="syn-other",set_id:d=>d.sets[0].id="syn-other",
 exercise:d=>d.sets[0].exercise_id="syn-other",set_index:d=>d.sets[0].set_index=99,
 duplicate:d=>d.sets[1]=clone(d.sets[0]),mixed_unit:d=>d.sets[0].load.unit="lb",
 unknown_unit:d=>d.sets[0].load.unit="plates",negative:d=>d.sets[0].load.value=-1,
 nan:d=>d.sets[0].load.value=NaN,rir:d=>d.sets[0].rir=-1,rpe_zero:d=>d.sets[0].rpe=0,
 extra_set:d=>d.sets[0].assessed_fit=true,missing_field:d=>delete d.sets[0].reps
};
for(const [name,mutate]of Object.entries(cases))test("reject "+name,()=>{
 const w=create(),d=w.draft(),before=hash(w.view());mutate(d);a.equal(w.register(d).ok,false);a.equal(hash(w.view()),before);
});
for(const field of ["reps","rir","rpe"])test("null is not zero "+field,()=>{
 const w=create(),d=w.draft();d.sets[0][field]=null;a(w.register(d).ok);a.equal(w.view().records[0].sets[0][field],null);
 const r=w.reflect();if(field==="reps")a.equal(r.result.plan_option,null);
});
test("manual reflection only",()=>{const w=create();a.equal(w.reflect().reason,"registration_required");a(w.register(w.draft()).ok);a.equal(w.view().workflow,null);});
test("immutable correction and old review invalidation",()=>{
 const {w}=start(),old=w.view(),e=w.event("member_accept","member","cmd-old");
 const d=w.draft();d.sets[0].rir=0;a(w.register(d).ok);a.equal(w.command(e).ok,false);
 const out=w.reflect();a(out.ok);a.equal(out.registration_ref.revision,2);a.deepEqual(w.view().records[0],old.records[0]);
 a.deepEqual(w.view().snapshot,old.snapshot);a.equal(w.view().workflow.proposal.member,"pending");
});
for(const what of ["plan","goal","rulebook","consent"])test("changed source "+what,()=>{
 const {f,w}=start();const e=w.event("member_accept","member","cmd-change"),before=clone(w.view().workflow.active);
 if(what==="rulebook")f.request.rulebook.revision++;
 else if(what==="consent")f.authority.ai_analysis_consent=false;
 else f.request.base.base.sources[what].revision++;
 a.equal(w.command(e).reason,"source_changed");a.deepEqual(w.view().workflow.active,before);
 a.equal(w.reflect().reason,"source_changed");
});
function step(w,action,role,id,target=null,options){return w.command(w.event(action,role,id,target),options);}
test("approval, atomic failure, replay and restore new version",()=>{
 const {w}=start(),base=clone(w.view().workflow.active);
 a.equal(step(w,"trainer_approve","trainer","cmd-early").ok,false);
 a(step(w,"member_accept","member","cmd-m").ok);a(step(w,"trainer_approve","trainer","cmd-t").ok);
 a.equal(w.view().workflow.active.revision,base.revision);
 const event=w.event("apply","trainer","cmd-apply"),before=hash(w.view());
 a.equal(w.command(event,{fault_before_commit:true}).ok,false);a.equal(hash(w.view()),before);
 a(w.command(event).ok);a(w.command(event).ok);a.equal(w.view().workflow.active.revision,base.revision+1);
 a.equal(w.command({...event,action:"trainer_reject"}).ok,false);
 a(step(w,"restore","member","cmd-r",base.revision).ok);a.equal(w.view().workflow.proposal.member,"pending");
 a(step(w,"member_accept","member","cmd-m2").ok);a(step(w,"trainer_approve","trainer","cmd-t2").ok);a(step(w,"apply","trainer","cmd-a2").ok);
 a.equal(w.view().workflow.active.revision,base.revision+2);a.deepEqual(w.view().workflow.history[0],base);
 a.deepEqual(w.view().workflow.active.options,base.options);
 a.equal(w.register(w.draft()).reason,"new_plan_source_required");
});
for(const action of ["member_reject","trainer_reject","trainer_block"])test(action,()=>{
 const {w}=start(),base=clone(w.view().workflow.active);
 if(action!=="member_reject")a(step(w,"member_accept","member","cmd-m").ok);
 a(step(w,action,action==="member_reject"?"member":"trainer","cmd-end").ok);
 a.equal(step(w,"apply","trainer","cmd-no").ok,false);a.deepEqual(w.view().workflow.active,base);
});
test("wrong actor and stale commands",()=>{
 const {w}=start(),e=w.event("member_accept","member","cmd-a");
 a.equal(w.command({...e,actor:"syn-other"}).ok,false);a(w.command(e).ok);
 a.equal(w.command({...e,id:"cmd-stale"}).ok,false);
});
test("facts only on missing registration",()=>{
 const w=create(),d=w.draft();d.sets.pop();a(w.register(d).ok);const r=w.reflect();a.equal(r.result.plan_option,null);
});

for(const name of ["unclassified","serious_recovered","recurring","new_after_recovery","unclear","technical","required_rir_missing","required_rpe_missing","current_rep_range","too_few_sessions","historical_plan_unmapped","historical_goal_unmapped","unknown_catalog","trainer_revoked","history_mixed_unit"])
test("fresh recorded session still respects "+name,()=>{
 const f=require("../../phase6e6/test/fixtures.cjs").setup(name,"nl"),w=create(f);a(w.register(w.draft()).ok);
 a.equal(w.reflect().result.plan_option,null);
});
test("missing current goal cannot be invented from snapshot",()=>{
 const f=fixture();f.request.base.base.sources.goal=null;const w=create(f);a(w.register(w.draft()).ok);
 a.equal(w.reflect().result.plan_option,null);
});
test("different valid registration recomputes instead of reusing initial proposal",()=>{
 const w=create(),d=w.draft();for(const t of d.sets)t.reps=1;a(w.register(d).ok);
 const result=w.reflect();a.equal(result.result.plan_option,null);
 a(result.result.rows.every(r=>r.kind==="maintain"));a.equal(result.pack.changes.length,0);
});
