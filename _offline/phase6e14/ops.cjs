"use strict";
const fs=require("node:fs"),p=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../.."),git=(...args)=>cp.execFileSync(process.env.FMZ_GIT||"git",args,{cwd:root,maxBuffer:100000000});
const sha=x=>crypto.createHash("sha256").update(x).digest("hex"),read=f=>fs.readFileSync(p.join(root,f));
const [mode,folder]=process.argv.slice(2);if(!folder)throw Error("folder_required");
const put=(name,value)=>fs.writeFileSync(p.join(folder,name),JSON.stringify(value,null,2)+"\n",{flag:"wx"});
if(mode==="before"){
 fs.mkdirSync(folder,{recursive:true});
 const names=[...new Set(git("ls-files","-z","--cached","--others","--exclude-standard").toString().split("\0").filter(Boolean))];
 const existing=names.filter(n=>!n.startsWith("_offline/phase6e14/")&&!n.startsWith("bounded-adjustments-demo/")&&!/^docs\/PHASE6E(13_FREEZE|14_)/.test(n));
 put("before.json",{head:git("rev-parse","HEAD").toString().trim(),files:Object.fromEntries(existing.map(n=>[n,sha(read(n))]))});
 console.log(JSON.stringify({folder,files:existing.length}));
}else if(mode==="preserve"){
 const b=JSON.parse(fs.readFileSync(p.join(folder,"before.json")));
 for(const [n,h] of Object.entries(b.files))a.equal(sha(read(n)),h,n);
 const result={status:"PASS",files:Object.keys(b.files).length,before_sha256:sha(fs.readFileSync(p.join(folder,"before.json")))};
 put("preservation-"+Date.now()+".json",result);console.log(JSON.stringify(result));
}else if(mode==="freeze"){
 const e=JSON.parse(read("docs/PHASE6E13_EVIDENCE.json"));
 const sources=Object.entries(e.source_sha256).map(([file,hash])=>{a.equal(sha(read(file)),hash,file);return {file,working_sha256:hash,git_sha256:sha(git("show","HEAD:"+file))};});
 const result={package:"6E-13",status:"COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY",accepted_on:"2026-09-29",
 source_commit:"cde2008801e2482f0dffc4dea50d38ba6307d50e",publication_commit:"2a0bb0abae2e12f7993bf6abe90698a4e27ead40",
 owner_physical_test:"S1-S3 explicitly accepted: proactive bounded signals, corrections, dedupe, versions, restore, missing data, complaints, expiry and withdrawal",
 sources,technical_evidence_sha256:sha(read("docs/PHASE6E13_EVIDENCE.json")),publication_receipt_sha256:sha(read("docs/PHASE6E13_PUBLICATION_RECEIPT.md")),
 technical_tests:2824,browser_checks_per_run:451,browser_layouts:24,limitation_observation_not_recognition_success:true,
 runtime_assets_frozen:90,live_server_integration_authorized:false,hosted_6e11:"SUPPORT HOLD SU-487979",
 expert_reviews_open:["medical","privacy","legal","language"],whole_phase6e_complete:false};
 fs.writeFileSync(p.join(root,"docs/PHASE6E13_FREEZE_EVIDENCE.json"),JSON.stringify(result,null,2)+"\n",{flag:"wx"});console.log(JSON.stringify({freeze:"PASS",sources:sources.length}));
}else throw Error("mode");
