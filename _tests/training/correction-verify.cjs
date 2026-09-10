const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),suite=(dir,exclude=[])=>fs.readdirSync(path.join(root,dir)).filter(f=>f.endsWith(".test.cjs")&&!exclude.includes(f)).map(f=>dir+"/"+f);
const files=["_tests/training/correction.test.cjs","_tests/training/model.test.cjs","assets/phase6d-theme-authority.test.cjs",
 "_offline/phase6e2/test/contract.test.cjs",...suite("_offline/phase6e1/test",["isolation.test.cjs"]),"_offline/phase6e0/test/recognition-followup.test.cjs","_offline/phase6e0/test/limitations.test.cjs"];
const r=cp.spawnSync(process.execPath,["--test","--test-reporter=tap",...files],{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:30000000});
fs.writeFileSync(path.join(root,"supabase/.temp/training-correction-regressions.tap"),r.stdout+"\n"+r.stderr);
if(r.status!==0){process.stdout.write(r.stdout);process.stderr.write(r.stderr);process.exitCode=1;}
else{
 const counts={};for(const k of ["tests","pass","fail","skipped"])counts[k]=Number(r.stdout.match(new RegExp("^# "+k+" (\\d+)$","m"))[1]);
 assert.equal(counts.skipped,0);assert.equal(counts.fail,0);
 fs.writeFileSync(path.join(root,"supabase/.temp/training-correction-regressions.json"),JSON.stringify({counts,files,medical_validation:false,historical_scope_tests:"Preserved; excluded because their original blanket scope predates this explicitly authorized Training correction. Replaced by correction.test.cjs exact runtime/SQL/frozen-source gates."},null,2));
 console.log(JSON.stringify(counts));
}

