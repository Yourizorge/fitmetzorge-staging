"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),suite=(dir,exclude=[])=>fs.readdirSync(path.join(root,dir)).filter(f=>f.endsWith(".test.cjs")&&!exclude.includes(f)).sort().map(f=>dir+"/"+f);
const files=[...suite("_offline/phase6e3/test"),"_offline/phase6e2/test/contract.test.cjs",
 ...suite("_offline/phase6e1/test",["isolation.test.cjs"]),"_offline/phase6e0/test/recognition-followup.test.cjs",
 "_offline/phase6e0/test/limitations.test.cjs","_tests/training/model.test.cjs","assets/phase6d-theme-authority.test.cjs"];
const r=cp.spawnSync(process.execPath,["--test","--test-reporter=tap",...files],{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:30000000});
const counts={};for(const k of ["tests","pass","fail","skipped"])counts[k]=Number(r.stdout.match(new RegExp("^# "+k+" (\\d+)$","m"))?.[1]);
const output={at:new Date().toISOString(),counts,files,tap:r.stdout,stderr:r.stderr,
 medical_validation:false,recognition_expansion:false,limitation_observations:1,
 historical_scope_tests:"Frozen historical blanket task-scope tests not replayed or modified. The eight new isolation checks protect current three-file alignment scope and all 57 frozen sources.",
 examples:r.status===0?require("./examples.cjs").examples():[],boundaries:r.status===0?require("./examples.cjs").boundaries():[]};
fs.writeFileSync(path.join(root,"supabase/.temp/phase6e3-tests.json"),JSON.stringify(output,null,2));
if(r.status!==0){process.stdout.write(r.stdout);process.stderr.write(r.stderr);process.exitCode=1;}
else{assert.equal(counts.fail,0);assert.equal(counts.skipped,0);console.log(JSON.stringify({counts,limitation_observations:1,examples:output.examples.length,pass:true}));}
