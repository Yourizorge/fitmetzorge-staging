"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),{generate}=require("../examples.cjs");
test("15 new exact workflow concepts in three languages are deterministic",()=>{
 const a=generate();assert.equal(a.length,15);assert.deepEqual(a,generate());
 for(const l of ["nl","en","de"]){
 const restore=a.find(x=>x.locale===l&&x.scenario==="restore");assert.equal(restore.active_version,5);assert.deepEqual(restore.previous_versions,[3,4]);
 assert.equal(a.find(x=>x.locale===l&&x.scenario==="step_off_grid").active_version,3);
 }
 assert.deepEqual(a,JSON.parse(fs.readFileSync("docs/PHASE6E7_EXAMPLES.json")));
 assert(a.every(e=>!JSON.stringify(e.messages).includes("undefined")&&!e.automatic_actions_allowed&&!e.physical_advice_authorized));
});
