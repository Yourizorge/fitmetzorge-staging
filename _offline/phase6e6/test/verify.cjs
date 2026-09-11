"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),suite=(dir,exclude=[])=>fs.readdirSync(path.join(root,dir)).filter(f=>f.endsWith(".test.cjs")&&!exclude.includes(f)).sort().map(f=>dir+"/"+f);
const groups={
 phase6e6:suite("_offline/phase6e6/test"),
 frozen6e5:suite("_offline/phase6e5/test",["isolation.test.cjs"]),
 frozen6e4:suite("_offline/phase6e4/test",["isolation.test.cjs"]),
 frozen6e3:["_offline/phase6e3/test/contract.test.cjs"],
 frozen6e2:["_offline/phase6e2/test/contract.test.cjs"],
 frozen6e1:suite("_offline/phase6e1/test",["isolation.test.cjs"]),
 frozen6e0:["_offline/phase6e0/test/recognition-followup.test.cjs","_offline/phase6e0/test/limitations.test.cjs"]
};
const results={};
for(const [name,files]of Object.entries(groups)){
 const r=cp.spawnSync(process.execPath,["--test","--test-reporter=tap",...files],{cwd:root,windowsHide:true,encoding:"utf8",maxBuffer:60000000});
 const counts=Object.fromEntries(["tests","pass","fail","skipped"].map(k=>[k,Number(r.stdout.match(new RegExp("^# "+k+" (\\d+)$","m"))?.[1])]));
 results[name]={files,counts,exit:r.status,tap:r.stdout,stderr:r.stderr};console.log(name,JSON.stringify(counts));
}
const counts=Object.fromEntries(["tests","pass","fail","skipped"].map(k=>[k,Object.values(results).reduce((n,r)=>n+r.counts[k],0)]));
const output={counts,groups:results,known_limitations_not_recognition_success:["Frozen known_language_miss and historical limitation observations"],medical_validation:false,real_coaching_rule_validation:false,authentic_live_authority_proven:false,real_database_atomicity_proven:false};
if(Object.values(results).every(r=>r.exit===0))output.examples=require("./examples.cjs").generate();
fs.writeFileSync(path.join(root,"supabase/.temp/phase6e6-tests.json"),JSON.stringify(output,null,2)+"\n");
console.log(JSON.stringify({counts,examples:output.examples?.length}));
for(const r of Object.values(results))if(r.exit!==0){process.stdout.write(r.tap);process.stderr.write(r.stderr);}
assert(Object.values(results).every(r=>r.exit===0));assert.equal(counts.fail,0);assert.equal(counts.skipped,0);
