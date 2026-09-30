"use strict";
const t=require("node:test"),a=require("node:assert/strict"),fs=require("node:fs"),crypto=require("node:crypto");
require("../../../independent-intake-demo/data.js");
const D=FMZ15Data,M=require("../../../independent-intake-demo/model.js"),B=require("../../../coach-review-demo/model.js"),C=require("../../../coach-review-demo/catalog.js"),clone=x=>JSON.parse(JSON.stringify(x));
const create=(n="complete")=>M.create(D.fixtures[n],D.registry),cmd=(m,action,data={})=>m.command(m.event(action,data));
const reasons={complete:"success",incomplete:"incomplete",favorites:"success",limited:"success",too_limited:"catalog_gap",allergy:"success",conflict:"conflicting_preferences",imperial:"success",complaint:"safety",recurring:"safety",self_reported:"safety",expired_context:"safety",technical:"safety",revoked:"consent",expired:"rule_source",missing_rule:"rule_source",conflicting_rule:"rule_source",missing_record:"incomplete",conflicting_record:"conflicting_records",expired_record:"record_source",unsupported_diet:"diet_rule_missing",unsupported_machine:"machine_rule_missing"};
function built(n){const m=create(n);a(cmd(m,"build").ok);return m;}
function activate(m){a(cmd(m,"confirm").ok);a(cmd(m,"activate").ok);}
for(const lang of ["nl","en","de"])for(const [name,reason]of Object.entries(reasons)){
 t(name+" "+lang+" exact gate",()=>{const f=clone(D.fixtures[name]);f.intake.locale=lang;const m=M.create(f,D.registry),old=m.view(),r=cmd(m,"build");a.equal(r.reason,reason);a.equal(r.state.automatic_actions_allowed,false);a.equal(r.state.physical_advice_authorized,false);a.equal(r.state.medical_clearance,false);if(reason!=="success")a.deepEqual(m.view(),old);});
 t(name+" "+lang+" no direct activation",()=>{const m=create(name),old=m.view();a.equal(cmd(m,"activate").ok,false);a.deepEqual(m.view(),old);});
}
for(const field of M.fields)t("missing required "+field,()=>{const f=clone(D.fixtures.complete);f.intake[field]=null;const m=M.create(f,D.registry);a.equal(cmd(m,"build").ok,false);a.equal(m.view().draft,null);});
for(const field of ["id","revision","subject","at","expires","coverage","sleep","recovery","activity_minutes"])t("missing record "+field,()=>{const f=clone(D.fixtures.complete);delete f.intake.records[field];a.equal(cmd(M.create(f,D.registry),"build").ok,false);});
for(const key of ["favorites","disliked","avoided","secondary","allergies","excludedFoods","movement","machines","dietLimits"])t("explicit empty "+key+" retained",()=>{const f=clone(D.fixtures.complete);f.intake[key]=[];const m=M.create(f,D.registry);a(cmd(m,"build").ok);a.deepEqual(m.view().intake[key],[]);});
for(const name of ["complete","favorites","limited","allergy","imperial"])for(const lang of ["nl","en","de"]){
 t(name+" "+lang+" full workflow duplicate and restore",()=>{const f=clone(D.fixtures[name]);f.intake.locale=lang;const m=M.create(f,D.registry);a(cmd(m,"build").ok);const first=clone(m.view().draft.plan);
  const confirm=m.event("confirm");a(m.command(confirm).ok);const confirmed=m.view();a.equal(m.command(confirm).reason,"idempotent");a.deepEqual(m.view(),confirmed);a.equal(cmd(m,"confirm").reason,"idempotent");
  const apply=m.event("activate");a(m.command(apply).ok);a.equal(m.view().version,1);a.equal(m.command(apply).reason,"idempotent");a.equal(cmd(m,"activate").ok,false);a.equal(m.view().history.length,1);
  a(cmd(m,"build").ok);const ex=m.view().draft.plan.training.sessions[0].exercises[0];a(cmd(m,"edit",{kind:"exercise",session:0,index:0,id:ex.id,sets:ex.sets,reps:9}).ok);activate(m);a.equal(m.view().version,2);
  a(cmd(m,"restore",{version:1}).ok);a.equal(cmd(m,"activate").ok,false);activate(m);a.equal(m.view().version,3);a.equal(m.view().history.length,3);a.deepEqual(m.view().active.plan,first);a.deepEqual(m.view().history[0].plan,first);
 });
 t(name+" "+lang+" atomic activation failure",()=>{const m=built(name);a(cmd(m,"confirm").ok);const old=m.view(),e=m.event("activate");a.equal(m.command(e,{fault_before_commit:true}).reason,"atomic_fault");a.deepEqual(m.view(),old);a(m.command(e).ok);});
}
for(const action of ["revoke","stale","expire"])t(action+" invalidates confirm and no partial write",()=>{const m=built();a(cmd(m,"confirm").ok);a(cmd(m,action).ok);const before=m.view();a.equal(cmd(m,"activate").ok,false);a.deepEqual(m.view(),before);});
t("missing information can be completed explicitly",()=>{const m=create("incomplete");a.equal(cmd(m,"build").ok,false);const i=m.view().intake;i.goal="strength";a(cmd(m,"intake",i).ok);a(cmd(m,"build").ok);});
t("no processing after consent withdrawal",()=>{const m=built();a(cmd(m,"revoke").ok);const before=m.view();a.equal(cmd(m,"intake",D.fixtures.complete.intake).ok,false);a.equal(cmd(m,"build").ok,false);a.deepEqual(m.view(),before);});
t("health cannot be cleared by a later intake field",()=>{const m=create("complaint"),i=m.view().intake;i.health="none";a(cmd(m,"intake",i).ok);a.equal(cmd(m,"build").reason,"safety");});
t("disliked sorts behind alternatives, exclusions never return",()=>{const f=clone(D.fixtures.complete);f.intake.disliked=["squat"];f.intake.avoided=["press"];const m=M.create(f,D.registry);a(cmd(m,"build").ok);const ids=m.view().draft.plan.training.sessions[0].exercises.map(x=>x.id);a(!ids.includes("squat"));a(!ids.includes("press"));a.equal(ids[0],"row");});
t("allergies enforced in every meal and alternatives",()=>{const m=built("allergy"),s=m.view();for(const meal of s.draft.plan.nutrition.meals)for(const item of meal.items)a(B.foodAllowed(item.food,s.intake));a(!B.eligibleMeals(s.intake).some(x=>x.id==="yogurtbowl"));const old=m.view();a.equal(cmd(m,"edit",{kind:"food",meal:0,index:0,id:"yogurt"}).ok,false);a.deepEqual(m.view(),old);});
for(const kind of ["exercise","meal","food"])t(kind+" editable and re-confirm required",()=>{const m=built();a(cmd(m,"confirm").ok);
 const data={exercise:{kind,session:0,index:0,id:"bandrow",sets:2,reps:10},meal:{kind,index:0,id:"ricelentils"},food:{kind,meal:0,index:0,id:"lentils"}}[kind];
 a(cmd(m,"edit",data).ok);a.equal(m.view().confirmed,false);a.equal(cmd(m,"activate").ok,false);activate(m);
});
t("unsupported sets reject entire edit, explicit experience selects existing3",()=>{const m=built(),before=m.view();a.equal(cmd(m,"edit",{kind:"exercise",session:0,index:0,id:"bandrow",sets:3,reps:10}).reason,"sets_rule");a.deepEqual(m.view(),before);const i=m.view().intake;i.experience="regular";a(cmd(m,"intake",i).ok);a(cmd(m,"build").ok);a.equal(m.view().draft.plan.training.sessions[0].exercises[0].sets,3);});
for(const reps of [0,13,1.5,null])t("invalid reps "+reps,()=>{const m=built(),before=m.view();a.equal(cmd(m,"edit",{kind:"exercise",session:0,index:0,id:"row",sets:2,reps}).ok,false);a.deepEqual(m.view(),before);});
for(const mode of ["days","unit","preference","experience"])t("intake change "+mode+" invalidates and preserves active history",()=>{const m=built();activate(m);const old=m.view().history;const i=m.view().intake;
 if(mode==="days")i.days=["tue","thu"];if(mode==="unit")i.unit="lb";if(mode==="preference"){i.favorites=["bridge"];i.avoided=["row"];}if(mode==="experience")i.experience="regular";
 a(cmd(m,"intake",i).ok);a.equal(m.view().draft,null);a.deepEqual(m.view().history,old);a.equal(cmd(m,"activate").ok,false);a(cmd(m,"build").ok);activate(m);
 if(mode==="unit"){a.equal(m.view().active.plan.training.sessions[0].exercises[0].unit,"lb");a.equal(m.view().history[0].plan.training.sessions[0].exercises[0].unit,"kg");a.equal(m.view().active.plan.training.sessions[0].exercises[0].load,null);}
 a.equal(cmd(m,"restore",{version:1}).ok,false);
});
t("source edit before activation rejects stale command",()=>{const m=built();a(cmd(m,"confirm").ok);const e=m.event("activate"),i=m.view().intake;i.days=["tue","thu"];a(cmd(m,"intake",i).ok);a.equal(m.command(e).reason,"version_conflict");a.equal(m.view().version,0);});
for(const field of ["id","route","subject","binding"])t("wrong request "+field,()=>{const m=built(),e=m.event("confirm"),old=m.view();e[field]="other";a.equal(m.command(e).ok,false);a.deepEqual(m.view(),old);});
t("payload replay conflict no writes",()=>{const m=built(),e=m.event("confirm");a(m.command(e).ok);e.data.extra=true;const old=m.view();a.equal(m.command(e).reason,"duplicate_conflict");a.deepEqual(m.view(),old);});
t("rejection prevents activation",()=>{const m=built();a(cmd(m,"reject").ok);a.equal(cmd(m,"activate").ok,false);a.equal(m.view().active,null);});
t("no calorie needs or macro targets",()=>{const s=built().view();a.equal(s.draft.refs.nutrition.energy_requirement_calculated,false);a.equal(s.draft.refs.nutrition.macro_target_calculated,false);a.equal(s.draft.refs.nutrition.portions_unit,"g");});
t("zero activity is not missing",()=>{const f=clone(D.fixtures.complete);f.intake.records.activity_minutes=0;const m=M.create(f,D.registry);a(cmd(m,"build").ok);a.equal(m.view().draft.refs.recovery.activity_minutes_record,0);});
t("frozen19 source bytes remain identical",()=>{const e=JSON.parse(fs.readFileSync("docs/PHASE6E14_FREEZE_EVIDENCE.json"));a.equal(e.sources.length,19);for(const x of e.sources)a.equal(crypto.createHash("sha256").update(fs.readFileSync(x.file)).digest("hex"),x.working_sha256,x.file);});
t("public demo no network/storage/secrets/private imports",()=>{for(const f of fs.readdirSync("independent-intake-demo")){const s=fs.readFileSync("independent-intake-demo/"+f,"utf8");a.doesNotMatch(s,/\b(fetch|XMLHttpRequest|WebSocket|localStorage|sessionStorage|indexedDB)\b|_offline\/|supabase\.co|service_role|sb_secret_/);}});
for(const field of ["subject","route","clock"])t("bad fixture "+field,()=>{const f=clone(D.fixtures.complete);f[field]="other";a.equal(cmd(M.create(f,D.registry),"build").ok,false);});
t("bad catalog fingerprint blocks",()=>{const f=clone(D.fixtures.complete);f.source.catalog_sha256="0".repeat(64);a.equal(cmd(M.create(f,D.registry),"build").reason,"rule_source");});
t("string set linkage rejected atomically",()=>{const m=built(),old=m.view();a.equal(cmd(m,"edit",{kind:"exercise",session:"0",index:0,id:"row",sets:2,reps:9}).reason,"payload");a.deepEqual(m.view(),old);});
