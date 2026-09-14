"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),suite=(p,skip=[])=>fs.readdirSync(path.join(root,p)).filter(f=>f.endsWith(".test.cjs")&&!skip.includes(f)).map(f=>p+"/"+f);
const groups={phase6e8:suite("_offline/phase6e8/test"),frozen6e7:suite("_offline/phase6e7/test",["isolation.test.cjs"]),frozen6e6:suite("_offline/phase6e6/test",["isolation.test.cjs"]),frozen6e5:suite("_offline/phase6e5/test",["isolation.test.cjs"]),frozen6e4:suite("_offline/phase6e4/test",["isolation.test.cjs"]),frozen6e3:["_offline/phase6e3/test/contract.test.cjs"],frozen6e2:["_offline/phase6e2/test/contract.test.cjs"],frozen6e1:suite("_offline/phase6e1/test",["isolation.test.cjs"]),frozen6e0:["_offline/phase6e0/test/recognition-followup.test.cjs","_offline/phase6e0/test/limitations.test.cjs"]},results={};
for(const [group,files]of Object.entries(groups)){
 const r=cp.spawnSync(process.execPath,["--test","--test-reporter=tap",...files],{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:60000000});
 const counts=Object.fromEntries(["tests","pass","fail","skipped"].map(k=>[k,Number(r.stdout.match(new RegExp("^# "+k+" (\\d+)$","m"))?.[1])]));
 results[group]={files,counts,exit:r.status,tap:r.stdout,stderr:r.stderr};console.log(group,JSON.stringify(counts));
 if(r.status!==0)console.log(r.stdout,r.stderr);
}
const counts=Object.fromEntries(["tests","pass","fail","skipped"].map(k=>[k,Object.values(results).reduce((n,r)=>n+r.counts[k],0)]));
const out={counts,groups:results,medical_validation:false,external_ai_calls:0,limitations:["Frozen observation tests are not language recognition success","Manual synthetic context selection is not message classification","Fixture plans and numbers are not validated coaching norms","In-memory events are not live auth, concurrency or O5 storage"]};
fs.mkdirSync(path.join(root,"supabase/.temp"),{recursive:true});fs.writeFileSync(path.join(root,"supabase/.temp/phase6e8-tests.json"),JSON.stringify(out,null,2)+"\n");
assert(Object.values(results).every(r=>r.exit===0));assert.equal(counts.fail,0);assert.equal(counts.skipped,0);console.log(JSON.stringify(counts));
