"use strict";
const fs=require("fs"),path=require("path"),cp=require("child_process"),assert=require("assert/strict");
const root=path.resolve(__dirname,"../../..");
const suite=(p,skip=[])=>fs.readdirSync(path.join(root,p)).filter(f=>f.endsWith(".test.cjs")&&!skip.includes(f)).map(f=>p+"/"+f);
const groups={new6e10:["_offline/phase6e10/test/edge.test.mjs"],frozen6e9:["_offline/phase6e9/test/contract.test.mjs"],frozen6e8:suite("_offline/phase6e8/test",["isolation.test.cjs"]),frozen6e7:suite("_offline/phase6e7/test",["isolation.test.cjs"]),frozen6e6:suite("_offline/phase6e6/test",["isolation.test.cjs"]),frozen6e5:suite("_offline/phase6e5/test",["isolation.test.cjs"]),frozen6e4:suite("_offline/phase6e4/test",["isolation.test.cjs"]),frozen6e3:["_offline/phase6e3/test/contract.test.cjs"],frozen6e2:["_offline/phase6e2/test/contract.test.cjs"],frozen6e1:suite("_offline/phase6e1/test",["isolation.test.cjs"]),frozen6e0:["_offline/phase6e0/test/recognition-followup.test.cjs","_offline/phase6e0/test/limitations.test.cjs"]};
const results={};
for(const [name,files] of Object.entries(groups)){
 const r=cp.spawnSync(process.execPath,["--test","--test-reporter=tap",...(name==="frozen6e9"?["--test-skip-pattern=^entire change scope is only authorized new code and docs$"]:[]),...files,...(name==="new6e10"?["_offline/phase6e10/test/scope.test.mjs"]:[])],{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:60000000});
 const counts=Object.fromEntries(["tests","pass","fail","skipped"].map(k=>[k,Number(r.stdout.match(new RegExp("^# "+k+" (\\d+)$","m"))?.[1])]));
 results[name]={counts,files,exit:r.status,tap:r.stdout,stderr:r.stderr};console.log(name,JSON.stringify(counts));if(r.status!==0)console.log(r.stdout.slice(-7000),r.stderr);
}
const out={groups:results,counts:Object.fromEntries(["tests","pass","fail","skipped"].map(k=>[k,Object.values(results).reduce((sum,x)=>sum+x.counts[k],0)])),medical_validation:false,observation_tests_not_recognition_success:true};
fs.writeFileSync(path.join(root,"supabase/.temp/phase6e10-regressions.json"),JSON.stringify(out,null,2)+"\n");
assert(Object.values(results).every(x=>x.exit===0));assert.equal(out.counts.skipped,0);assert.equal(results.frozen6e9.counts.tests,254);console.log(JSON.stringify({...out.counts,superseded_scope_gate:1}));
