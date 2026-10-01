"use strict";
const fs=require("node:fs"),p=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../.."),[mode,out]=process.argv.slice(2),git=(...v)=>cp.execFileSync(process.env.FMZ_GIT||"git",v,{cwd:root,maxBuffer:100000000}),sha=x=>crypto.createHash("sha256").update(x).digest("hex"),read=f=>JSON.parse(fs.readFileSync(p.join(root,f))),put=(f,x)=>fs.writeFileSync(f,JSON.stringify(x,null,2)+"\n",{flag:"wx"});
if(mode==="before"){
 fs.mkdirSync(out,{recursive:true});const files=git("ls-files","-z","--cached","--others","--exclude-standard").toString().split("\0").filter(Boolean).filter(f=>!f.startsWith("_offline/phase6e16/")&&!f.startsWith("training-rules-demo/")&&!/^docs\/PHASE6E(15_FREEZE|16_)/.test(f));
 put(p.join(out,"before.json"),{head:git("rev-parse","HEAD").toString().trim(),files:Object.fromEntries(files.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))]))});console.log(JSON.stringify({baseline_files:files.length}));
}else if(mode==="preserve"){
 const b=JSON.parse(fs.readFileSync(p.join(out,"before.json")));for(const [f,h]of Object.entries(b.files))a.equal(sha(fs.readFileSync(p.join(root,f))),h,f);
 const h=read("supabase/.temp/phase6e11-support-wait-74b97a33fa684a938c93397036c9b843/manifest.json");for(const [f,v]of Object.entries(h.evidence_sha256))a.equal(sha(fs.readFileSync(p.join(root,f))),v,f);
 const x={status:"PASS",files:Object.keys(b.files).length,historical:Object.keys(h.evidence_sha256).length};put(p.join(out,"preserve-"+Date.now()+".json"),x);console.log(JSON.stringify(x));
}else if(mode==="freeze"){
 const original=read("docs/PHASE6E15_EVIDENCE.json"),followup=read("docs/PHASE6E15_OWNER_TESTMODE_EVIDENCE.json"),expected={...original.source_sha256,...followup.source_sha256};
 const sources=Object.entries(expected).map(([file,h])=>{const bytes=fs.readFileSync(p.join(root,file));a.equal(sha(bytes),h,file);return {file,working_sha256:h,git_sha256:sha(git("show","HEAD:"+file))};});
 const reports=["docs/PHASE6E15_EVIDENCE.json","docs/PHASE6E15_PUBLICATION_RECEIPT.md","docs/PHASE6E15_OWNER_TESTMODE_EVIDENCE.json","docs/PHASE6E15_OWNER_TESTMODE_PUBLICATION.md"];
 put(p.join(root,"docs/PHASE6E15_FREEZE_EVIDENCE.json"),{package:"6E-15",status:"COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY",accepted_on:"2026-10-01",owner_physical_test:"Explicit Q1-Q3 acceptance; all nine guided phone scenarios correct, exclusions zero, health and withdrawn consent block",source_commits:["acdc17acca6718d19e74def7f0cc3058891b6b71","739fd3192ddccde82e7c0ebbc74c929e5d09bebd"],publication_commit:"968b4f0257303af5c60e8a7370a252c20641a806",sources,reports:Object.fromEntries(reports.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))])),test_evidence:{original_total:3458,followup_unit:329,followup_browser_local:1346,followup_browser_published:1346,existing_browser:463,settings:24,owner_layouts:217},pages_runs:[36748181732,36748845641],live_integration_authorized:false,expert_validation:false,whole_phase_complete:false,hosted_hold:"SU-487979"});console.log(JSON.stringify({frozen_sources:sources.length}));
}else throw Error("mode");
