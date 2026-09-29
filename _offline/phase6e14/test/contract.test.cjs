"use strict";
const t=require("node:test"),a=require("node:assert/strict"),F=require("../fixtures.cjs"),E=require("../engine.cjs"),{hash,clone,catalogs}=require("../catalog.cjs");
require("../../../bounded-adjustments-demo/data.js");
const M=require("../../../bounded-adjustments-demo/model.js"),D=globalThis.FMZ14Data;
const expected={a_progression:"candidate_only",a_maintain:"maintain",a_lb:"candidate_only",b_schedule:"candidate_only",nutrition_partial:"confirmation",recovery_reflection:"reflection",calorie_rule_missing:"facts_only",missing_rule:"facts_only",ambiguous_rule:"facts_only",no_trainer:"blocked",invalid_option:"blocked",missing_value:"blocked",expired:"blocked",conflict:"blocked",revoked:"blocked",current:"facts_only",self_reported:"facts_only",recurring:"facts_only",unclassified:"facts_only",expired_context:"facts_only",technical:"facts_only",b_current:"facts_only",b_partial:"confirmation",b_no_rule:"facts_only"};
const command=(m,action,data={},actor="member")=>m.command(m.event(action,data,actor));
function approve(m){const r=m.view().route;a(command(m,r==="A"?"accept":"confirm").ok);if(r==="A")a(command(m,"approve",{},"trainer").ok);}
for(const lang of ["nl","en","de"])for(const n of F.scenarios){
 t(n+" "+lang+" contract",()=>{const f=F.fixture(n,lang),o=E.evaluate(f.source,f.gate,lang);a.equal(o.status,expected[n]);a.deepEqual(o,D[n][lang].initial);a.equal(o.automatic_actions_allowed,false);a.equal(o.physical_advice_authorized,false);a.equal(o.medical_clearance,false);a.equal(o.provider_calls,0);if(o.status!=="candidate_only")a.equal(o.target,null);});
 t(n+" "+lang+" correction cannot erase safety",()=>{const f=F.corrected(F.fixture(n,lang)),o=E.evaluate(f.source,f.gate,lang);a.equal(o.status,expected[n]);a.deepEqual(o,D[n][lang].corrected);});
 t(n+" "+lang+" no direct apply",()=>{const m=M.create(D[n][lang]),before=m.view();a.equal(command(m,"apply").ok,false);a.deepEqual(m.view(),before);});
}
for(const lang of ["nl","en","de"])for(const n of ["a_progression","a_lb","b_schedule"]){
 t(n+" "+lang+" full approvals apply duplicate restore",()=>{
  const m=M.create(D[n][lang]),original=m.view();approve(m);a.equal(m.view().revision,original.revision);
  const e=m.event("apply"),r=m.command(e);a(r.ok);a.equal(m.view().revision,original.revision+1);a.deepEqual(m.view().history[0].plan,original.active);
  a.equal(m.command(e).reason,"idempotent");a.equal(m.view().revision,original.revision+1);a.equal(command(m,"apply").ok,false);
  a(command(m,"restore",{version:original.revision}).ok);a.equal(command(m,"apply").ok,false);approve(m);a(command(m,"apply").ok);
  a.equal(m.view().revision,original.revision+2);a.equal(m.view().history.length,3);a.deepEqual(m.view().active,original.active);
 });
 for(const action of ["revoke","expire","health","stale"])t(n+" "+lang+" "+action+" blocks approval and application",()=>{const m=M.create(D[n][lang]);approve(m);a(command(m,action).ok);const old=m.view();a.equal(command(m,"apply").ok,false);a.deepEqual(m.view(),old);a(command(m,"correct").ok);a(command(m,"reassess").ok);a.equal(command(m,n.startsWith("b_")?"confirm":"accept").ok,false);});
 t(n+" "+lang+" correction before apply requires approvals again",()=>{const m=M.create(D[n][lang]);approve(m);const e=m.event("apply");a(command(m,"correct").ok);a.equal(m.command(e).reason,"conflict");a(command(m,"reassess").ok);a.equal(m.view().member,false);a.equal(command(m,"apply").ok,false);approve(m);a(command(m,"apply").ok);});
 t(n+" "+lang+" correction after apply preserves and blocks obsolete source",()=>{const m=M.create(D[n][lang]);approve(m);a(command(m,"apply").ok);const old=m.view();a(command(m,"correct").ok);a(command(m,"reassess").ok);a.equal(m.view().status,"stale_source");a.deepEqual(m.view().active,old.active);a.deepEqual(m.view().history,old.history);a.equal(command(m,"apply").ok,false);});
 t(n+" "+lang+" atomic failed apply",()=>{const m=M.create(D[n][lang]);approve(m);const old=m.view(),e=m.event("apply");a.equal(m.command(e,{fault_before_commit:true}).reason,"atomic_fault");a.deepEqual(m.view(),old);a(m.command(e).ok);});
 t(n+" "+lang+" changed duplicate rejected",()=>{const m=M.create(D[n][lang]),e=m.event(n==="b_schedule"?"confirm":"accept");a(m.command(e).ok);e.data.extra=1;a.equal(m.command(e).reason,"duplicate_conflict");});
 for(const field of ["subject","route","basis","actor"])t(n+" "+lang+" wrong "+field,()=>{const m=M.create(D[n][lang]),e=m.event(n==="b_schedule"?"confirm":"accept"),old=m.view();e[field]="other";a.equal(m.command(e).ok,false);a.deepEqual(m.view(),old);});
 t(n+" "+lang+" reject no partial",()=>{const m=M.create(D[n][lang]),old=m.view();a(command(m,"reject").ok);a.equal(command(m,"apply").ok,false);a.deepEqual(m.view().active,old.active);});
}
for(const action of ["accept","approve","apply","reject","block","edit","restore","reassess","check"])t("B rejects trainer "+action,()=>{const m=M.create(D.b_schedule.nl),old=m.view();a.equal(command(m,action,{},"trainer").ok,false);a.deepEqual(m.view(),old);});
for(const action of ["approve","block"])t("A member cannot "+action,()=>{const m=M.create(D.a_progression.nl);a(command(m,"accept").ok);a.equal(command(m,action).reason,"actor");a(command(m,action,{},"trainer").ok);});
for(const action of ["reject","block"])t("A trainer "+action,()=>{const m=M.create(D.a_progression.nl),old=m.view();a(command(m,"accept").ok);a(command(m,action,{},"trainer").ok);a.equal(command(m,"apply").ok,false);a.deepEqual(m.view().active,old.active);});
for(const kind of ["days","exercise","favorite","avoid"])t("B edit "+kind+" invalidates confirmation",()=>{
 const m=M.create(D.b_schedule.nl);a(command(m,"confirm").ok);const d={days:["mon","wed","fri"],favorite:"row",avoid:"",exercise:""};
 if(kind==="days")d.days=["tue","thu"];if(kind==="exercise")d.exercise="bandrow";if(kind==="favorite")d.favorite="squat";if(kind==="avoid"){d.avoid="row";d.favorite="";}
 a(command(m,"edit",d).ok);a.equal(m.view().member,false);a.equal(command(m,"apply").ok,false);a(command(m,"confirm").ok);a(command(m,"apply").ok);a.equal(m.view().history.length,2);
 if(kind==="avoid")a.equal(command(m,"restore",{version:1}).ok,false);
});
t("B invalid preferences never partially mutate",()=>{const m=M.create(D.b_schedule.nl),old=m.view();a.equal(command(m,"edit",{days:["mon"],favorite:"row",avoid:"row",exercise:"missing"}).ok,false);a.deepEqual(m.view(),old);});
t("registration check does not fill missing values",()=>{const m=M.create(D.nutrition_partial.nl),before=m.result();a(command(m,"check").ok);a.deepEqual(m.result(),before);a.equal(command(m,"apply").ok,false);});
const mutations={foreign:s=>s.subject_id="syn-other",unknown:s=>s.template="other",nullrules:s=>s.rules=null,nullplan:s=>s.plan_ref=null,nullgoal:s=>s.goal_ref=null,nullsignal:s=>s.signal=null,
 changedtarget:s=>s.option.training.exercises[0].sets[0].load.value++,nullrir:s=>s.plan.training.exercises[0].sets[0].rir=0,
 rulesrev:s=>s.rules[0].revision++,wrongsession:s=>s.sessions[0].id="syn-other",extra:s=>s.untrusted=true,duplicates:s=>s.sessions.push(clone(s.sessions[0])),partial:s=>s.sessions[0].complete=false,
 sessionsets:s=>s.sessions[0].completed_sets=5,future:s=>s.issued_at_ms+=1000,expired:s=>s.valid_until_ms=s.issued_at_ms,excessvalid:s=>s.valid_until_ms+=1000};
for(const [name,mut]of Object.entries(mutations))t("invalid source "+name,()=>{const f=F.fixture();mut(f.source);const o=E.evaluate(f.source,f.gate);a.notEqual(o.status,"candidate_only");a.equal(o.target,null);});
t("unissued safety receipt cannot authorize",()=>{const f=F.fixture();a.equal(E.evaluate(f.source,clone(f.gate)).status,"blocked");});
t("wrong expected source hash blocks",()=>{const f=F.fixture();a.equal(E.evaluate(f.source,f.gate,"nl","0".repeat(64)).status,"blocked");});
t("null and zero retained as distinct, no unit conversion",()=>{a.equal(catalogs.a_progression.before.training.exercises[0].sets[0].rir,null);a.equal(catalogs.a_lb.after.training.exercises[0].sets[0].load.unit,"lb");a.notEqual(hash(null),hash(0));});
t("locale change has same workflow binding",()=>{for(const n of F.scenarios)for(const lang of ["en","de"])a.equal(D[n][lang].initial.source_hash,D[n].nl.initial.source_hash);});
t("trainer restore starts fresh member and trainer approval",()=>{const m=M.create(D.a_progression.nl);approve(m);a(command(m,"apply").ok);a(command(m,"restore",{version:3},"trainer").ok);a.equal(m.view().member,false);a.equal(m.view().trainer,false);a.equal(command(m,"apply").ok,false);approve(m);a(command(m,"apply").ok);a.equal(m.view().revision,5);});
