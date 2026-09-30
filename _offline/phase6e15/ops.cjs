"use strict";
const fs=require("node:fs"),p=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../.."),git=(...x)=>cp.execFileSync(process.env.FMZ_GIT||"git",x,{cwd:root,maxBuffer:100000000}),sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const [mode,out]=process.argv.slice(2),put=(file,x)=>fs.writeFileSync(file,JSON.stringify(x,null,2)+"\n",{flag:"wx"});
if(mode==="before"){
 fs.mkdirSync(out,{recursive:true});const files=git("ls-files","-z","--cached","--others","--exclude-standard").toString().split("\0").filter(Boolean).filter(f=>!f.startsWith("_offline/phase6e15/")&&!f.startsWith("independent-intake-demo/")&&!/^docs\/PHASE6E(14_FREEZE|15_)/.test(f));
 put(p.join(out,"before.json"),{head:git("rev-parse","HEAD").toString().trim(),files:Object.fromEntries(files.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))]))});console.log(JSON.stringify({files:files.length}));
}else if(mode==="preserve"){
 const b=JSON.parse(fs.readFileSync(p.join(out,"before.json")));for(const [f,h]of Object.entries(b.files))a.equal(sha(fs.readFileSync(p.join(root,f))),h,f);
 put(p.join(out,"preservation-"+Date.now()+".json"),{status:"PASS",files:Object.keys(b.files).length});console.log(JSON.stringify({preserved:Object.keys(b.files).length}));
}else if(mode==="freeze"){
 const e=JSON.parse(fs.readFileSync(p.join(root,"docs/PHASE6E14_EVIDENCE.json")));
 const sources=Object.entries(e.source_sha256).map(([file,h])=>{a.equal(sha(fs.readFileSync(p.join(root,file))),h,file);return {file,working_sha256:h,git_sha256:sha(git("show","HEAD:"+file))};});
 put(p.join(root,"docs/PHASE6E14_FREEZE_EVIDENCE.json"),{package:"6E-14",status:"COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY",accepted_on:"2026-09-30",owner_physical_test:"Explicit P1-P3 acceptance: proposals/explanation, bounded registration/recovery, source corrections/history/idempotent application/restoration",
 source_commit:"cd2bc1ad3a6fcba9aa89b7be28b276db832c70b7",publication_commit:"5a96c303e037beaf1183b2c0073de922f886fd7c",sources,
 evidence_sha256:sha(fs.readFileSync(p.join(root,"docs/PHASE6E14_EVIDENCE.json"))),publication_receipt_sha256:sha(fs.readFileSync(p.join(root,"docs/PHASE6E14_PUBLICATION_RECEIPT.md"))),
 tests:3213,browser_checks_per_run:490,settings:24,layout_inspections:49,pages_runs:[36552675167,36553295825],old_runtime_assets_preserved:96,live_server_authorized:false,whole_phase6e_complete:false,
 open_reviews:["medical","privacy","legal","language"],hosted_6e11:"SUPPORT HOLD SU-487979"});console.log(JSON.stringify({frozen_sources:sources.length}));
}else throw Error("mode");
