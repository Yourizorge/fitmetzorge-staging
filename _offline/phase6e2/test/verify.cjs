"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../..");
const suite=(dir,exclude=[])=>fs.readdirSync(path.join(root,dir)).filter(f=>f.endsWith(".test.cjs")&&!exclude.includes(f)).sort().map(f=>dir+"/"+f);
const files=[...suite("_offline/phase6e2/test"),...suite("_offline/phase6e1/test",["isolation.test.cjs"]),
 "_offline/phase6e0/test/recognition-followup.test.cjs","_offline/phase6e0/test/limitations.test.cjs"];
const args=["--test","--test-reporter=tap",...files];
const r=cp.spawnSync(process.execPath,args,{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:30000000});
if(r.status!==0){process.stdout.write(r.stdout||"");process.stderr.write(r.stderr||"");process.exitCode=1;}
else{
 const counts={};for(const k of ["tests","pass","fail","cancelled","skipped","todo"])
  counts[k]=Number(r.stdout.match(new RegExp("^# "+k+" (\\d+)$","m"))?.[1]);
 assert.equal(counts.fail,0);assert.equal(counts.skipped,0);assert(counts.pass>=546);
 const examples=require("./examples.cjs");
 const result={checked_at:new Date().toISOString(),command:["node",...args],counts,
  groups:{phase6e2:counts.pass-382,frozen6e1_functional:292,frozen6e0_selected:90},
  frozen_scope_checks:"6E1's eight original scope/isolation tests are preserved, not replayed against the authorized new package. New 6E2 isolation checks protect both frozen packages and all current runtime.",
  original_expectations:122,medical_validation:false,tap:r.stdout,stderr:r.stderr,
  examples:examples.examples(),transitions:examples.transitions()};
 fs.writeFileSync(path.join(root,"supabase/.temp/phase6e2-test-evidence.json"),JSON.stringify(result,null,2)+"\n");
 console.log(JSON.stringify({counts,groups:result.groups,examples:result.examples.length,transition_scenarios:result.transitions.length,pass:true}));
}
