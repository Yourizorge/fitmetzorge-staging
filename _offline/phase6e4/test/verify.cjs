"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),suite=(dir,exclude=[])=>fs.readdirSync(path.join(root,dir)).filter(f=>f.endsWith(".test.cjs")&&!exclude.includes(f)).sort().map(f=>dir+"/"+f);
const groups={
  phase6e4:suite("_offline/phase6e4/test"),
  frozen6e3:["_offline/phase6e3/test/contract.test.cjs"],
  frozen6e2:["_offline/phase6e2/test/contract.test.cjs"],
  frozen6e1:suite("_offline/phase6e1/test",["isolation.test.cjs"]),
  frozen6e0:["_offline/phase6e0/test/recognition-followup.test.cjs","_offline/phase6e0/test/limitations.test.cjs"]
};
const results={};
for(const [name,files]of Object.entries(groups)){
  const r=cp.spawnSync(process.execPath,["--test","--test-reporter=tap",...files],{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:60000000});
  const counts={};for(const k of ["tests","pass","fail","skipped"])counts[k]=Number(r.stdout.match(new RegExp("^# "+k+" (\\d+)$","m"))?.[1]);
  results[name]={files,counts,exit:r.status,tap:r.stdout,stderr:r.stderr};
}
const counts=Object.fromEntries(["tests","pass","fail","skipped"].map(k=>[k,Object.values(results).reduce((n,r)=>n+r.counts[k],0)]));
const cases=require("../language-cases.json").cases,engine=require("../engine.cjs");
const language=cases.map(c=>{const a=engine.assess({synthetic_only:true,text:c.text,locale:c.locale,availability:c.availability});return {id:c.id,text:c.text,locale:c.locale,expected:c.expected.category,original:a.original.category,current:a.category,adapted:a.adapted,original_level:a.original.level,current_level:a.level};});
const output={at:new Date().toISOString(),counts,groups:results,language,
  new_preregistered_ordinary_repairs:language.filter(c=>c.expected==="ordinary"&&c.original==="communication"&&c.current==="ordinary").length,
  preregistered_mixed_health_preserved:language.filter(c=>c.expected==="health_report"&&c.original==="health_report"&&c.current==="health_report"&&c.original_level===c.current_level).length,
  current_known_limitation_observations:1,medical_validation:false,authentic_live_trainer_authority_proven:false,
  historical_scope_tests:"Frozen earlier task-scope/isolation tests remain unchanged. Six current isolation tests protect ALL 69 frozen files and ALL 60 runtime assets. Functional frozen tests are executed separately."};
if(Object.values(results).every(r=>r.exit===0)){
  output.examples=require("./examples.cjs").examples();output.boundaries=require("./examples.cjs").boundaries();
}
fs.writeFileSync(path.join(root,"supabase/.temp/phase6e4-tests.json"),JSON.stringify(output,null,2)+"\n");
console.log(JSON.stringify({counts,groups:Object.fromEntries(Object.entries(results).map(([k,r])=>[k,r.counts])),language_repairs:output.new_preregistered_ordinary_repairs,mixed_health_preserved:output.preregistered_mixed_health_preserved,limitation_observations:1}));
for(const r of Object.values(results))if(r.exit!==0){process.stdout.write(r.tap);process.stderr.write(r.stderr);process.exitCode=1;}
assert.equal(counts.fail,0);assert.equal(counts.skipped,0);
