"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),cases=require("../language-cases.json").cases;
const {engine,run}=require("./fixtures.cjs");
const errata=require("../preregistration-errata.json").changes;
for(const c of cases)test("language preregistered "+c.id,()=>{
  const a=engine.assess({synthetic_only:true,text:c.text,locale:c.locale,availability:c.availability});
  assert.equal(a.category,c.expected.category,c.text+"; "+JSON.stringify(a.original));
  const correction=errata.find(e=>e.id===c.id);
  if(correction){assert.equal(c.expected.adapted,correction.original);assert.equal(c.expected.category,"ordinary");assert.equal(a.original.category,"communication");}
  assert.equal(a.adapted,correction?correction.corrected:c.expected.adapted,c.id+" adaptation diagnostic");
  if(a.category==="health_report"){assert.equal(a.original.category,"health_report");assert.equal(a.level,a.original.level);}
});
for(const locale of ["nl","en","de"])test("complete ordinary review opens new candidate "+locale,()=>{
  const c=cases.find(c=>c.id==="normal-"+locale+"-0"),r=run({text:c.text,locale});
  assert.equal(r.status,"candidate_only");assert.equal(r.warnings.length,0);
});
for(const c of cases.filter(c=>c.expected.category==="health_report"))test("mixed complaint refuses candidate "+c.id,()=>{
  const r=run({text:c.text,locale:c.locale});assert.equal(r.reason,"current_health_report");assert(r.warnings.length>0);
  assert.equal(r.candidate,null);assert.equal(r.language_adapter_applied,false);
});
test("unknown compound outside narrow grammar remains a limitation, not recognition success",()=>{
  const a=engine.assess({synthetic_only:true,text:"Ik inspecteer mijn trainingslogboek",locale:"nl",availability:"available"});
  assert.equal(a.category,"communication");assert.equal(a.adapted,false);
});
