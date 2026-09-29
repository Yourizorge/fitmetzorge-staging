"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),a=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),out=process.argv[2],cleanRoot=process.argv[3];if(!out)throw Error("output_required");
const suite=(n,ext=".test.cjs")=>fs.readdirSync(path.join(root,"_offline",n,"test")).filter(f=>f.endsWith(ext)&&!["isolation.test.cjs","scope.test.mjs"].includes(f)).map(f=>"_offline/"+n+"/test/"+f);
const groups={new6e12:suite("phase6e12"),...Object.fromEntries(Array.from({length:9},(_,i)=>["frozen6e"+i,suite("phase6e"+i)])),
 frozen6e9:["_offline/phase6e9/test/contract.test.mjs"],frozen6e10:["_offline/phase6e10/test/edge.test.mjs"]};
const guard=path.join(root,"_offline/phase6e12/no_network.cjs"),results={};
for(const [name,files]of Object.entries(groups)){
 if(!files.length)throw Error("empty_suite");
 const testFiles=files;
 const args=["--require",guard,"--test","--test-reporter=tap",...(name==="frozen6e9"?["--test-skip-pattern=^(entire change scope is only authorized new code and docs|frozen byte identity .*)$"]:[]),...testFiles];
 const p=cp.spawnSync(process.execPath,args,{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:50000000,timeout:180000});
 const counts=Object.fromEntries(["tests","pass","fail","skipped"].map(k=>[k,Number(p.stdout?.match(new RegExp("^# "+k+" (\\d+)$","m"))?.[1])]));
 results[name]={files,counts,runtime_basis:"preserved_worktree; historical checkout-byte guards replaced by accepted 6E10 Git/blob and offline checkout identities plus task baseline",exit:p.status,stdout:p.stdout,stderr:p.stderr};console.log(name,JSON.stringify(counts));
 if(p.status!==0){console.log((p.stdout||"").slice(-4000));break;}
}
const report={groups:results,obsolete_scope_gate_replaced_by_full_worktree_preservation:1,historical_6e9_checkout_byte_guards_replaced:JSON.parse(fs.readFileSync(path.join(root,"docs/PHASE6E8_FREEZE_EVIDENCE.json"))).sources.length,hosted_calls:0,medical_validation:false,
 known_limitations_tests_not_recognition_success:true};
fs.writeFileSync(path.join(out,"unit-regressions.json"),JSON.stringify(report,null,2),{flag:"wx"});
a.equal(Object.keys(results).length,Object.keys(groups).length);a(Object.values(results).every(x=>x.exit===0&&x.counts.fail===0));
