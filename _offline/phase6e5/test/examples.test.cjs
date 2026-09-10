"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),{generate}=require("./examples.cjs"),F=require("./fixtures.cjs");
for(const locale of ["nl","en","de"])test("executable concept coverage and review transitions: "+locale,()=>{
 const examples=generate().filter(e=>e.locale===locale);assert.equal(examples.length,10);
 for(const e of examples){
  const o=e.output||e.initial;assert.equal(o.physical_advice_authorized,false);assert.equal(o.automatic_actions_allowed,false);
  assert(o.messages[0].includes(locale==="de"?"OFFLINE-KONZEPT":"OFFLINE CONCEPT"));
  assert(o.messages.every(m=>typeof m==="string"&&!/undefined|NaN|\{[a-z_]+\}/.test(m)));
 }
 const normal=examples.find(e=>e.scenario==="normal").output;
 assert.deepEqual(normal.rows.map(r=>r.kind),["increase_reps","increase_weight","maintain"]);
 assert.equal(examples.find(e=>e.scenario==="accept").timeline.at(-1).state.applications,1);
 assert.equal(examples.find(e=>e.scenario==="reject").timeline.at(-1).state.status,"rejected");
 const conflict=examples.find(e=>e.scenario==="version_conflict_and_reassessment").timeline;
 assert.equal(conflict.at(-2).state.status,"needs_recheck");assert.deepEqual(conflict.at(-1).state.approvals,[]);
});
test("all example outputs are deterministic across independent simulations",()=>assert.deepEqual(generate(),generate()));
test("normal language correction remains read-only and complaints still win",()=>{
 for(const text of ["Ik bekijk mijn trainingsregistratie","Ich sehe mir mein Trainingsprotokoll an"]){
  const a=F.engine.assess({synthetic_only:true,text,locale:text.startsWith("Ik")?"nl":"de",availability:"available"});assert.equal(a.category,"ordinary");
 }
 const a=F.engine.assess({synthetic_only:true,text:"Ik bekijk mijn trainingsregistratie. Mijn borst voelt loodzwaar",locale:"nl",availability:"available"});
 assert.equal(a.category,"health_report");
});
