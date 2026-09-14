"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),vm=require("node:vm"),fs=require("node:fs"),path=require("node:path");
const root=path.resolve(__dirname,"../../.."),M=require("../../../coach-review-demo/model.js"),C=require("../../../coach-review-demo/catalog.js"),copy=require("../../../coach-review-demo/copy.js"),A=require("../../../training-review-demo/model.js");
const context={window:{}};vm.runInNewContext(fs.readFileSync(path.join(root,"training-review-demo/data.js"),"utf8"),context);
const seeds=JSON.parse(JSON.stringify(context.window.FMZDemoData.seeds)),clone=x=>JSON.parse(JSON.stringify(x));
const run=(m,a,d={})=>m.command(m.event(a,d)),ok=r=>{assert.equal(r.ok,true,r.reason);return r;};
function ready(){const m=M.create();ok(run(m,"build"));return m;}
function active(){const m=ready();ok(run(m,"confirm"));ok(run(m,"apply"));return m;}
test("B complete plan, explicit sources, separate confirmation and apply",()=>{
 const m=ready();assert.equal(m.view().active,null);assert.equal(run(m,"apply").ok,false);
 ok(run(m,"confirm"));assert.equal(m.view().active,null);ok(run(m,"apply"));
 const s=m.view();assert.equal(s.revision,1);assert.equal(s.history.length,1);
 for(const k of ["training","nutrition","recovery"])assert(s.active.plan[k]);
 assert.equal(s.active.refs.policy,C.policy.id);assert.equal(s.automatic_actions_allowed,false);
 assert.equal(s.physical_advice_authorized,false);assert.equal(s.medical_clearance,false);
 assert.equal(s.trainer,undefined);assert(!s.audit.some(x=>x.action.includes("trainer")));
});
for(const key of Object.keys(C.defaults))test("required intake field "+key,()=>{const i=clone(C.defaults);delete i[key];assert.throws(()=>M.build(i));});
for(const key of Object.keys(M.enums))test("unknown intake enum "+key,()=>{const i=clone(C.defaults);i[key]="unknown";assert.throws(()=>M.build(i));});
for(const key of Object.keys(M.arrays))test("unknown intake array value "+key,()=>{const i=clone(C.defaults);i[key]=["unknown"];assert.throws(()=>M.build(i));});
for(const [key,values]of Object.entries(M.enums))for(const value of values)test("valid intake "+key+"="+value,()=>{
 const i=clone(C.defaults);i[key]=value;const p=M.build(i);assert(M.validatePlan(p,i));
});
test("all intake domains have meaningful plan use or constraints",()=>{
 const i=clone(C.defaults);i.goal="muscle";i.secondary=["endurance"];i.experience="regular";i.days=["tue","sat"];i.minutes=20;i.equipment=["mat","band"];i.favorites=["bandrow"];i.avoided=["wallpress"];i.movement=["overhead"];i.rir=false;i.rpe=true;i.diet="plant";i.allergies=["gluten","nuts","dairy","soy"];i.excludedFoods=["rice"];i.meals=4;i.kitchen="none";i.budget="low";i.rhythm="late";i.sleep=6;i.recovery="low";i.unit="lb";
 // With this strict exclusion catalog cannot provide three complete meal alternatives.
 assert.throws(()=>M.build(i),/catalog_gap/);
 i.excludedFoods=[];const p=M.build(i);assert.equal(p.training.sessions.length,2);
 assert.equal(p.training.sessions[0].exercises.length,2);assert.equal(p.training.sessions[0].exercises[0].id,"bandrow");
 assert.equal(p.training.sessions[0].exercises[0].sets,3);assert.equal(p.training.sessions[0].exercises[0].reps,10);
 assert.equal(p.training.sessions[0].exercises[0].unit,"lb");assert.equal(p.training.sessions[0].exercises[0].rir,null);
 assert.equal(p.training.sessions[0].exercises[0].rpe,7);assert.equal(p.nutrition.meals.length,4);assert.equal(p.nutrition.meals[0].at,10);
 assert.equal(p.recovery.baselineSleep,6);assert.equal(p.recovery.checkins,"daily");assert.deepEqual(p.recovery.secondary,["endurance"]);
});
for(const id of C.exercises.map(x=>x.id))test("exercise exclusion persists across every alternative "+id,()=>{
 const i=clone(C.defaults);i.favorites=[];i.avoided=[id];const p=M.build(i);
 assert(!p.training.sessions.some(s=>s.exercises.some(x=>x.id===id)));assert(!M.eligibleExercises(i).some(x=>x.id===id));
});
for(const allergy of ["nuts","dairy","soy","gluten"])test("allergy excludes all meal and food alternatives "+allergy,()=>{
 const i=clone(C.defaults);i.diet="omnivore";i.allergies=[allergy];const p=M.build(i);
 for(const meal of [...p.nutrition.meals,...M.eligibleMeals(i)])for(const x of meal.items)assert(!C.foods.find(f=>f.id===x.food).allergens.includes(allergy));
});
test("favorites versus exclusions conflict, no silent winner",()=>{const i=clone(C.defaults);i.avoided=["row"];assert.throws(()=>M.build(i),/conflicting_preferences/);});
for(const [rir,rpe]of [[false,false],[true,false],[false,true],[true,true]])test("independent RIR RPE "+rir+"/"+rpe,()=>{
 const i={...clone(C.defaults),rir,rpe},p=M.build(i),x=p.training.sessions[0].exercises[0];
 assert.equal(x.rir,rir?2:null);assert.equal(x.rpe,rpe?7:null);x.rir=0;x.rpe=null;assert(M.validatePlan(p,i));assert.equal(x.rir,0);
});
for(const edit of [{kind:"replace",session:0,index:0,id:"bridge"},{kind:"add",session:0,id:"bridge"},{kind:"remove",session:0,index:0},{kind:"move",session:0,index:1,to:0},{kind:"meal",index:0,id:"ricelentils"},{kind:"food",meal:0,index:0,id:"beans"},{kind:"sleep",hours:9},{kind:"light_week"}])test("edit invalidates confirmation: "+edit.kind,()=>{
 const m=ready();ok(run(m,"confirm"));ok(run(m,"edit",edit));assert.equal(m.view().status,"member_pending");assert.equal(m.view().confirmed,null);assert.equal(run(m,"apply").ok,false);ok(run(m,"confirm"));ok(run(m,"apply"));
});
test("exclusion cannot be bypassed by add, replace, food or meal",()=>{
 const m=M.create(),i=clone(C.defaults);i.avoided=["overhead"];i.allergies=["dairy"];i.excludedFoods=["tofu"];
 ok(run(m,"intake",i));ok(run(m,"build"));
 for(const d of [{kind:"add",session:0,id:"overhead"},{kind:"replace",session:0,index:0,id:"overhead"},{kind:"food",meal:0,index:0,id:"tofu"},{kind:"meal",index:0,id:"yogurtbowl"}]){
  const before=m.view();assert.equal(run(m,"edit",d).ok,false);assert.deepEqual(m.view(),before);
 }
});
test("no partial apply, duplicate command idempotency, stale basis and old versions",()=>{
 const m=ready();ok(run(m,"confirm"));const e=m.event("apply"),before=m.view();
 assert.equal(m.command(e,{fault_before_commit:true}).ok,false);assert.deepEqual(m.view(),before);
 ok(m.command(e));const applied=m.view();ok(m.command(e));assert.deepEqual(m.view(),applied);
 assert.equal(m.command({...e,data:{changed:true}}).ok,false);
 assert.equal(m.command({...e,id:"cmd-b-old"}).ok,false);
});
for(const action of ["trainer_approve","trainer_block","trainer_reject","member_accept","unknown"])test("B rejects foreign action "+action,()=>assert.equal(run(ready(),action).ok,false));
for(const patch of [{subject:"syn-member"},{route:"human"},{id:"cmd-a-1"}])test("cross-route identity denied "+JSON.stringify(patch),()=>{
 const m=ready();assert.equal(m.command({...m.event("confirm"),...patch}).ok,false);
});
test("reject, reopen, immutable history and restore new version",()=>{
 const m=ready();ok(run(m,"reject"));assert.equal(run(m,"apply").ok,false);ok(run(m,"reopen"));ok(run(m,"confirm"));ok(run(m,"apply"));
 const original=clone(m.view().history[0]);ok(run(m,"reopen"));ok(run(m,"edit",{kind:"sleep",hours:9}));ok(run(m,"confirm"));ok(run(m,"apply"));
 assert.equal(m.view().revision,2);ok(run(m,"restore",{version:1}));assert.equal(m.view().revision,2);assert.equal(run(m,"apply").ok,false);
 ok(run(m,"confirm"));ok(run(m,"apply"));assert.equal(m.view().revision,3);assert.deepEqual(m.view().history[0],original);
 assert.deepEqual(m.view().active.plan,original.plan);assert.equal(m.view().active.componentVersions.training,1);assert.equal(m.view().active.componentVersions.recovery,3);
 const external=m.view();external.history[0].plan.training.days=[];assert.deepEqual(m.view().history[0],original);
});
for(const code of ["current","serious","recurring","unclassified","self_reported","missing","expired_context","misunderstanding","technical","consent_revoked","version_conflict","expired"])test("source/safety hard stop "+code,()=>{
 const m=active(),before=m.view().active;ok(run(m,"reopen"));ok(run(m,"confirm"));m.inject(code);
 for(const a of ["apply","confirm","build","reopen"])assert.equal(run(m,a).ok,false);
 assert.deepEqual(m.view().active,before);assert.equal(m.view().medical_clearance,false);
});
test("clarification never removes other health context",()=>{
 const m=ready();m.inject("current");m.inject("misunderstanding");m.inject("technical");
 ok(run(m,"clarify",{source:"syn-new-clear-context@1"}));assert.deepEqual(m.view().contextFixtures,["current"]);assert.equal(run(m,"confirm").ok,false);
});
for(const code of ["misunderstanding","technical"])test("optional clarification isolated to "+code,()=>{
 const m=ready();m.inject(code);assert.equal(run(m,"clarify",{source:"unknown"}).ok,false);
 ok(run(m,"clarify",{source:"syn-new-clear-context@1"}));ok(run(m,"confirm"));ok(run(m,"apply"));assert.equal(m.view().medical_clearance,false);
});
for(const id of Object.keys(C.signals))test("proactive linked fixture "+id,()=>{
 const m=active();
 const before=m.view().active;ok(run(m,"signal",{id}));assert.deepEqual(m.view().active,before);
 const s=m.view();assert.equal(s.signal.base,s.revision);assert(s.signal.source);assert(s.signal.window);assert.deepEqual(s.signal.values,C.signals[id].values);
 if(C.signals[id].kind==="facts"){assert.equal(s.status,"facts");assert.equal(run(m,"apply").ok,false);}
 else{assert.equal(s.status,"member_pending");ok(run(m,"confirm"));ok(run(m,"apply"));}
});
test("same improvement evidence cannot repeatedly increase reps",()=>{
 const m=active();ok(run(m,"signal",{id:"improvement"}));ok(run(m,"confirm"));ok(run(m,"apply"));
 const s=m.view();assert.equal(s.active.plan.training.sessions[0].exercises[0].reps,9);
 assert.equal(s.active.refs.evidence,"syn-signal-improvement@1");
 assert.equal(run(m,"signal",{id:"improvement"}).ok,false);assert.deepEqual(m.view(),s);
 const p=M.build(C.defaults);p.training.sessions[0].exercises[0].reps=13;assert.throws(()=>M.validatePlan(p,C.defaults));
});
test("photo requires corroboration, eligible same-muscle alternative and member activation",()=>{
 const m=M.create(),i=clone(C.defaults);i.favorites=["raise"];ok(run(m,"intake",i));ok(run(m,"build"));ok(run(m,"confirm"));ok(run(m,"apply"));
 const before=m.view().active;assert.equal(run(m,"photo",{corroborated:false}).ok,false);
 ok(run(m,"photo",{corroborated:true}));assert.deepEqual(m.view().active,before);
 assert.equal(m.view().draft.plan.training.temporary.weeks,2);assert.deepEqual(m.view().signal.effect.muscle,["shoulders","shoulders"]);
 ok(run(m,"confirm"));ok(run(m,"apply"));assert.equal(m.view().revision,2);
});
test("photo with missing exercise context fails closed",()=>assert.equal(run(active(),"photo",{corroborated:true}).ok,false));
test("A keeps distinct approvals, restore, and refuses member apply",()=>{
 const m=A.create(seeds.normal);let n=0;const cmd=(a,r,target=null)=>m.command(m.event(a,r,"cmd-test-"+(++n),target));
 assert.equal(cmd("apply","trainer").ok,false);ok(cmd("member_accept","member"));assert.equal(cmd("apply","trainer").ok,false);
 ok(cmd("trainer_approve","trainer"));assert.equal(cmd("apply","member").ok,false);ok(cmd("apply","trainer"));assert.equal(m.view().active.revision,4);
 ok(cmd("restore","member",3));assert.equal(cmd("apply","trainer").ok,false);ok(cmd("member_accept","member"));ok(cmd("trainer_approve","trainer"));ok(cmd("apply","trainer"));assert.equal(m.view().active.revision,5);
});
for(const id of ["no_trainer","step_off_grid","current","self_reported","expired","missing","stale_request"])test("A frozen blocked fixture "+id,()=>{
 const m=A.create(seeds[id]);assert.notEqual(m.view().proposal.status,"approved");assert.equal(m.command(m.event("apply","trainer","cmd-denied")).ok,false);
});
for(const locale of ["nl","en","de"])test("complete concept copy "+locale,()=>{
 assert.deepEqual(Object.keys(copy[locale]),Object.keys(copy.nl));
 assert(Object.values(copy[locale]).every(s=>typeof s==="string"&&s.length>0));
 for(const id of Object.keys(C.signals))assert(copy[locale]["why_"+id]);
});
for(const locale of ["nl","en","de"])test("accepted warning copy stays exact "+locale,()=>{
 const old=require("../../phase6e0/warning-recovery-proposal.json");
 assert.equal(copy[locale].warning_health,old.warnings.current_unclassified[locale]);
 assert.equal(copy[locale].warning_unclear,old.warnings.unclear[locale]);
 assert.equal(copy[locale].warning_technical,old.warnings.technical[locale]);
 assert.equal(copy[locale].warning_recovered,old.recovery_messages.report_recorded[locale]);
});
test("33 saved executable concept answers reproduce exactly",()=>{
 const output=require("../examples.cjs").generate(),saved=require("../../../docs/PHASE6E8_EXAMPLES.json");
 assert.equal(output.examples.length,33);assert.deepEqual(output,saved);
});
