'use strict';
const fs=require('node:fs'),p=require('node:path'),cp=require('node:child_process'),c=require('node:crypto'),a=require('node:assert/strict');
const root=p.resolve(__dirname,'../..'),[mode,out]=process.argv.slice(2),git=(...v)=>cp.execFileSync(process.env.FMZ_GIT||'git',v,{cwd:root,maxBuffer:100000000}),sha=x=>c.createHash('sha256').update(x).digest('hex'),read=f=>JSON.parse(fs.readFileSync(p.join(root,f))),put=(f,x)=>fs.writeFileSync(f,JSON.stringify(x,null,2)+'\n',{flag:'wx'});
if(mode==='before'){
 fs.mkdirSync(out,{recursive:true});const files=[...new Set(git('ls-files','-z','--cached','--others','--exclude-standard').toString().split('\0').filter(Boolean))].filter(f=>!f.startsWith('_offline/phase6e21/')&&!f.startsWith('complete-recording-demo/')&&!/^docs\/PHASE6E(20_FREEZE|21_)/.test(f));
 put(p.join(out,'before.json'),{head:git('rev-parse','HEAD').toString().trim(),at:new Date().toISOString(),files:Object.fromEntries(files.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))]))});console.log({baseline_files:files.length});
}else if(mode==='preserve'){
 const b=JSON.parse(fs.readFileSync(p.join(out,'before.json')));for(const [f,h]of Object.entries(b.files))a.equal(sha(fs.readFileSync(p.join(root,f))),h,f);
 const h=read('supabase/.temp/phase6e11-support-wait-74b97a33fa684a938c93397036c9b843/manifest.json');for(const [f,v]of Object.entries(h.evidence_sha256))a.equal(sha(fs.readFileSync(p.join(root,f))),v,f);
 const x={status:'PASS',files:Object.keys(b.files).length,historical:Object.keys(h.evidence_sha256).length};put(p.join(out,'preserve-'+Date.now()+'.json'),x);console.log(x);
}else if(mode==='freeze'){
 const old=read('docs/PHASE6E20_EVIDENCE.json'),pub=read('docs/PHASE6E20_PUBLICATION_EVIDENCE.json');
 const sources=Object.entries(old.source_sha256).map(([file,h])=>{a.equal(sha(fs.readFileSync(p.join(root,file))),h,file);const gh=sha(git('show','HEAD:'+file));a.equal(gh,pub.source_git_sha256[file],file);return {file,working_sha256:h,git_sha256:gh};});
 const reports=['EVIDENCE.json','PUBLICATION_EVIDENCE.json','PUBLICATION_RECEIPT.md','OWNER_OVERVIEW.md','EXAMPLES.json','TECHNICAL_REPORT.md','STATUS_AND_CONTRACT.md'].map(f=>'docs/PHASE6E20_'+f);
 put(p.join(root,'docs/PHASE6E20_FREEZE_EVIDENCE.json'),{package:'6E-20',status:'COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY',accepted_on:'2026-10-08',owner_acceptance:'Owner reports physical phone test PASS everywhere; 20-R1,20-R2,20-R3 accepted. No additional physical actions claimed. No expert validation or live release.',source_commit:'4527c00b5b4bb0542f18b1284f31e5d9f81be47d',publication_commit:'2fdb7b6cf4529b7b6143ffe846ac0bf151981baf',sources,reports:Object.fromEntries(reports.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))])),tests:{total:4947,new20:231,frozen:4716,browser_local:2413,browser_published:2413,settings:24,layouts:433},pages_runs:[37323586458,37763793689],old_assets:140,new_assets:6,private404:99,expert_validation:false,live_release:false,whole_phase_complete:false,support_hold:'SU-487979'});console.log({frozen_sources:sources.length});
}else throw Error('mode');
