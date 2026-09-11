"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),{generate}=require("./examples.cjs");
test("30 exact executable NL/EN/DE concepts cover allowed, refused, maintained and review states",()=>{
 const e=generate();assert.equal(e.length,30);
 for(const locale of ["nl","en","de"]){
  const subset=e.filter(x=>x.locale===locale);assert.equal(subset.length,10);
  assert.equal(subset.find(x=>x.scenario==="normal").output.rows[0].kind,"increase_reps");
  assert.equal(subset.find(x=>x.scenario==="normal").output.rows[1].kind,"increase_weight");
  for(const s of ["no_trainer","rulebook_missing","effort_conflict","current"])assert.equal(subset.find(x=>x.scenario===s).output.plan_option,null);
  assert.equal(subset.find(x=>x.scenario==="approval_timeline").timeline.at(-1).applications,1);
  assert.equal(subset.find(x=>x.scenario==="rejection").timeline.at(-1).status,"rejected");
  assert.equal(subset.find(x=>x.scenario==="version_conflict").timeline.at(-1).status,"needs_recheck");
 }
 assert(e.every(x=>x.output.messages.length>0&&!x.output.messages.some(t=>/undefined|\{[a-z_]+\}/.test(t))));
});
test("example output is deterministic and no physical advice/automatic action is authorized",()=>{
 const a=generate(),b=generate();assert.deepEqual(a,b);assert(a.every(x=>x.output.automatic_actions_allowed===false&&x.output.physical_advice_authorized===false&&x.output.provider_calls===0));
});
test("exact NL normal values and independent approval copy are executable",()=>{
 const e=generate().find(x=>x.locale==="nl"&&x.scenario==="normal");
 assert(e.output.messages.some(t=>t.includes("2")&&t.includes("9")&&t.includes("55")));
 assert(e.output.messages.some(t=>t.includes("32,5")));
 assert(e.output.messages.includes("Wacht op afzonderlijke lidbevestiging en trainergoedkeuring; daarna is nog expliciete toepassing nodig."));
});
