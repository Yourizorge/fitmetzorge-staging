"use strict";
const fs=require('node:fs'),p=require('node:path'),cp=require('node:child_process'),c=require('node:crypto'),a=require('node:assert/strict');
const root=p.resolve(__dirname,'../..'),[mode,out]=process.argv.slice(2),git=(...v)=>cp.execFileSync(process.env.FMZ_GIT||'git',v,{cwd:root,maxBuffer:100000000}),sha=x=>c.createHash('sha256').update(x).digest('hex'),read=f=>JSON.parse(fs.readFileSync(p.join(root,f))),put=(f,x)=>fs.writeFileSync(f,JSON.stringify(x,null,2)+'\n',{flag:'wx'});
if(mode==='before'){
 fs.mkdirSync(out,{recursive:true});const files=git('ls-files','-z','--cached','--others','--exclude-standard').toString().split('\0').filter(Boolean).filter(f=>!f.startsWith('_offline/phase6e19/')&&!f.startsWith('recovery-checkin-demo/')&&!/^docs\/PHASE6E(18_FREEZE|19_)/.test(f));
 put(p.join(out,'before.json'),{head:git('rev-parse','HEAD').toString().trim(),files:Object.fromEntries(files.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))]))});console.log({baseline_files:files.length});
}else if(mode==='preserve'){
 const b=JSON.parse(fs.readFileSync(p.join(out,'before.json')));for(const [f,h]of Object.entries(b.files))a.equal(sha(fs.readFileSync(p.join(root,f))),h,f);
 const h=read('supabase/.temp/phase6e11-support-wait-74b97a33fa684a938c93397036c9b843/manifest.json');for(const [f,v]of Object.entries(h.evidence_sha256))a.equal(sha(fs.readFileSync(p.join(root,f))),v,f);
 const x={status:'PASS',files:Object.keys(b.files).length,historical:Object.keys(h.evidence_sha256).length};put(p.join(out,'preserve-'+Date.now()+'.json'),x);console.log(x);
}else if(mode==='freeze'){
 const old=read('docs/PHASE6E18_EVIDENCE.json'),pub=read('docs/PHASE6E18_PUBLICATION_EVIDENCE.json');
 const sources=Object.entries(old.source_sha256).map(([file,h])=>{a.equal(sha(fs.readFileSync(p.join(root,file))),h,file);const gh=sha(git('show','HEAD:'+file));a.equal(gh,pub.source_git_sha256[file],file);return {file,working_sha256:h,git_sha256:gh};});
 const reports=['docs/PHASE6E18_EVIDENCE.json','docs/PHASE6E18_PUBLICATION_EVIDENCE.json','docs/PHASE6E18_PUBLICATION_RECEIPT.md','docs/PHASE6E18_OWNER_OVERVIEW.md','docs/PHASE6E18_EXAMPLES.json','docs/PHASE6E18_INITIAL_EVIDENCE.json'];
 put(p.join(root,'docs/PHASE6E18_FREEZE_EVIDENCE.json'),{package:'6E-18',status:'COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY',accepted_on:'2026-10-04',owner_acceptance:'Physical phone test:16 scenarios PASS;18-R1/R2/R3 accepted for joint review, separate confirmation/activation and version restoration. No expert training/nutrition validation or real-member release.',source_commit:'36fdeeeb729f5f8e69c3838892c888d6aa75619a',publication_commit:'f6ddb4d4178d7eeda571771fa1bdd6c181e8ca43',sources,reports:Object.fromEntries(reports.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))])),tests:{total:4373,new18:335,frozen:4038,browser_local:2171,browser_published:2171,settings:24,layouts:385},pages_runs:[36880959450,36881740289],old_assets:125,new_assets:7,private404:81,expert_validation:false,live_release:false,whole_phase_complete:false,support_hold:'SU-487979'});console.log({frozen_sources:sources.length});
}else throw Error('mode');
