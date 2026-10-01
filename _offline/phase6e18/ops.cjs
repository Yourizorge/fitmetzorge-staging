"use strict";
const fs=require('node:fs'),p=require('node:path'),cp=require('node:child_process'),c=require('node:crypto'),a=require('node:assert/strict');
const root=p.resolve(__dirname,'../..'),[mode,out]=process.argv.slice(2),git=(...v)=>cp.execFileSync(process.env.FMZ_GIT||'git',v,{cwd:root,maxBuffer:100000000}),sha=x=>c.createHash('sha256').update(x).digest('hex'),read=f=>JSON.parse(fs.readFileSync(p.join(root,f))),put=(f,x)=>fs.writeFileSync(f,JSON.stringify(x,null,2)+'\n',{flag:'wx'});
if(mode==='before'){
 fs.mkdirSync(out,{recursive:true});const files=git('ls-files','-z','--cached','--others','--exclude-standard').toString().split('\0').filter(Boolean).filter(f=>!f.startsWith('_offline/phase6e18/')&&!f.startsWith('combined-plan-demo/')&&!/^docs\/PHASE6E(17_FREEZE|18_)/.test(f));
 put(p.join(out,'before.json'),{head:git('rev-parse','HEAD').toString().trim(),files:Object.fromEntries(files.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))]))});console.log({baseline_files:files.length});
}else if(mode==='preserve'){
 const b=JSON.parse(fs.readFileSync(p.join(out,'before.json')));for(const [f,h]of Object.entries(b.files))a.equal(sha(fs.readFileSync(p.join(root,f))),h,f);
 const h=read('supabase/.temp/phase6e11-support-wait-74b97a33fa684a938c93397036c9b843/manifest.json');for(const [f,v]of Object.entries(h.evidence_sha256))a.equal(sha(fs.readFileSync(p.join(root,f))),v,f);
 const x={status:'PASS',files:Object.keys(b.files).length,historical:Object.keys(h.evidence_sha256).length};put(p.join(out,'preserve-'+Date.now()+'.json'),x);console.log(x);
}else if(mode==='freeze'){
 const old=read('docs/PHASE6E17_EVIDENCE.json'),pub=read('docs/PHASE6E17_PUBLICATION_EVIDENCE.json');
 const sources=Object.entries(old.source_sha256).map(([file,h])=>{a.equal(sha(fs.readFileSync(p.join(root,file))),h,file);const gh=sha(git('show','HEAD:'+file));a.equal(gh,pub.source_git_sha256[file],file);return {file,working_sha256:h,git_sha256:gh};});
 const reports=['docs/PHASE6E17_EVIDENCE.json','docs/PHASE6E17_PUBLICATION_EVIDENCE.json','docs/PHASE6E17_PUBLICATION_RECEIPT.md','docs/PHASE6E17_OWNER_OVERVIEW.md','docs/PHASE6E17_EXAMPLES.json'];
 put(p.join(root,'docs/PHASE6E17_FREEZE_EVIDENCE.json'),{package:'6E-17',status:'COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY',accepted_on:'2026-10-01',owner_acceptance:'Physical phone test of all20 scenarios;17-R1/17-R2/17-R3 accepted for operation and safety boundaries; synthetic nutrition values are NOT substantively or professionally validated',source_commit:'aafa5e7cfcef21e6c993be9da7f40898f276a39d',publication_commit:'dfa3dac9d3e3b3cd326eda28b867b84eed94587b',sources,reports:Object.fromEntries(reports.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))])),tests:{total:4038,new17:289,frozen:3749,browser_local:2682,browser_published:2682,settings:24,layouts:481},pages_runs:[36869290225,36870106318],old_assets:117,new_assets:8,private404:73,expert_validation:false,live_release:false,whole_phase_complete:false,support_hold:'SU-487979'});console.log({frozen_sources:sources.length});
}else throw Error('mode');
