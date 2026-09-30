"use strict";
const t=require("node:test"),a=require("node:assert/strict"),fs=require("node:fs"),crypto=require("node:crypto");
const R=require("../../../independent-intake-demo/review.js"),M=require("../../../independent-intake-demo/model.js"),C=require("../../../coach-review-demo/catalog.js");
const clone=x=>JSON.parse(JSON.stringify(x));
function display(s,locale=0){
 const p=s.draft?.plan;
 return {locale,foods:(p?.nutrition.meals.flatMap(x=>x.items)||[]).map(x=>({id:x.food,text:C.foods.find(f=>f.id===x.food).label[locale]+" | "+x.g+" g"})),
 exercises:(p?.training.sessions.flatMap(x=>x.exercises)||[]).map(x=>({id:x.id,text:C.exercises.find(e=>e.id===x.id).label[locale]})),
 versions:"Intake: "+s.intakeHistory.map(x=>x.revision).join(" / ")+" | Plan: "+(s.history.map(x=>x.version).join(" / ")||"-"),confirm:s.status==="member_pending",activate:s.status==="confirmed",blockedNotice:s.status==="blocked"&&!!s.draft};
}
for(const c of R.cases){
 t(c.id+" executes unchanged model and actual display",()=>{const r=R.run(c.id);a(R.assess(r,r.model.view(),display(r.model.view())).pass,JSON.stringify(r.checks));a(r.ledger.length);a.equal(r.model.view().external_calls,0);});
 t(c.id+" no stale PASS after manual mutation",()=>{const r=R.run(c.id),s=r.model.view();s.intake.days=["sun"];a.equal(R.assess(r,s).pass,false);});
 t(c.id+" missing action proof fails closed",()=>{const r=R.run(c.id);r.ledger.pop();a.equal(R.assess(r,r.model.view()).pass,false);});
 t(c.id+" erased checks fail closed",()=>{const r=R.run(c.id);r.checks=[];a.equal(R.assess(r,r.model.view()).pass,false);});
 t(c.id+" unexpected engine error fails closed",()=>{const r=R.run(c.id,(f,d)=>{const m=M.create(f,d);return {...m,command:()=>({ok:false,reason:"injected_error",state:m.view()})};});a.equal(R.assess(r,r.model.view()).pass,false);});
 for(const locale of [0,1,2])t(c.id+" localized rendered result "+locale,()=>{const r=R.run(c.id);a(R.assess(r,r.model.view(),display(r.model.view(),locale)).pass);});
}
t("nine independent scenarios reset only local state",()=>{a.equal(R.cases.length,9);const s=R.run("restore").model.view(),r=R.run("valid");a.equal(s.version,3);a.equal(r.model.view().version,0);a.equal(r.model.view().history.length,0);});
t("allergy attempts are rejected and visible food choices exclude all hazards",()=>{const r=R.run("allergy"),s=r.model.view();a.deepEqual(r.ledger.slice(1).map(x=>x.reason),["excluded","excluded"]);for(const x of r.ledger.slice(1))a.deepEqual(x.before,x.after);const d=display(s);a(!d.foods.some(x=>["nuts","yogurt","tofu"].includes(x.id)));a(!d.exercises.some(x=>x.id==="squat"));});
t("excluded product or wrong label in rendered UI triggers AFWIJKING",()=>{const r=R.run("allergy"),s=r.model.view(),d=display(s);d.foods.push({id:"nuts",text:"Noten | 20 g"});a.equal(R.assess(r,s,d).pass,false);const x=display(s);x.foods[0].text="Noten | 20 g";a.equal(R.assess(r,s,x).pass,false);});
t("missing visible exercises/food/versions never earns PASS",()=>{const r=R.run("valid"),s=r.model.view();for(const field of ["foods","exercises","versions"]){const d=display(s);d[field]=field==="versions"?"": [];a.equal(R.assess(r,s,d).pass,false);}});
t("blocked physical complaint has no concept or activation control",()=>{const r=R.run("health"),s=r.model.view();a.equal(s.draft,null);a.equal(s.version,0);for(const key of ["confirm","activate"]){const d=display(s);d[key]=true;a.equal(R.assess(r,s,d).pass,false);}});
t("consent rejects all new processing and clearly labels retained concept",()=>{const r=R.run("consent"),s=r.model.view();a.deepEqual(r.ledger.slice(2).map(x=>x.reason),["consent","consent","consent"]);a(s.draft);const d=display(s);d.blockedNotice=false;a.equal(R.assess(r,s,d).pass,false);});
t("changed intake clears old confirmation and source conflict blocks new plan",()=>{const r=R.run("source"),s=r.model.view();a.equal(s.intakeRevision,2);a.deepEqual(s.intake.days,["tue","thu"]);a.equal(s.draft,null);a.equal(s.confirmed,false);a.equal(s.version,0);a.equal(r.ledger[3].reason,"version_conflict");a.equal(r.ledger.at(-1).reason,"rule_source");});
t("repeated requests do not change version/audit",()=>{const r=R.run("duplicate");for(const x of r.ledger.filter(x=>x.reason==="idempotent"||!x.ok))a.deepEqual(x.before,x.after);a.equal(r.model.view().history.length,1);});
t("restoration requires confirmation then separate activation",()=>{const r=R.run("restore"),s=r.model.view();a.equal(r.ledger[8].reason,"version_conflict");a.equal(s.history.length,3);a.deepEqual(s.history[0].plan,s.history[2].plan);a.notDeepEqual(s.history[1].plan,s.history[2].plan);});
t("incorrect model activation cannot produce PASS",()=>{const r=R.run("duplicate",(f,d)=>{const m=M.create(f,d);return {...m,command:e=>e.action==="activate"?{ok:true,reason:"success",state:m.view()}:m.command(e)};});a.equal(R.assess(r,r.model.view()).pass,false);});
t("existing model/data/copy/catalog and old245 tests are byte-identical",()=>{const e=JSON.parse(fs.readFileSync("docs/PHASE6E15_EVIDENCE.json"));for(const f of ["independent-intake-demo/model.js","independent-intake-demo/data.js","independent-intake-demo/copy.js","_offline/phase6e15/test/contract.test.cjs"]){a.equal(crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex"),e.source_sha256[f],f);}});
t("unknown test identifier is refused",()=>a.throws(()=>R.run("invented")));
