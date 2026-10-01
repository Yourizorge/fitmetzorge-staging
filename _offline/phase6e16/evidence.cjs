"use strict";
const fs=require("node:fs"),p=require("node:path"),crypto=require("node:crypto"),a=require("node:assert/strict");
const R=require("../../training-rules-demo/review.js"),C=require("../../training-rules-demo/copy.js"),root=p.resolve(__dirname,"../.."),out=process.argv[2];
const sha=f=>crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex"),read=f=>JSON.parse(fs.readFileSync(f));
const latest=prefix=>p.join(out,fs.readdirSync(out).filter(f=>f.startsWith(prefix)&&f.endsWith(".json")).sort().at(-1));
const files=[latest("contract-"),p.join(out,"unit-regressions.json"),latest("6e13-tests-"),latest("6e14-tests-")];
const groups=files.flatMap(f=>{const x=read(f);return x.groups?Object.entries(x.groups).map(([name,g])=>({name,counts:g.counts,exit:g.exit})): [{name:p.basename(f),counts:x.counts,exit:x.status??x.exit}];});
for(const g of groups){a.equal(g.exit,0,g.name);a.equal(g.counts.fail,0);a.equal(g.counts.skipped,0);a.equal(g.counts.tests,g.counts.pass);}
const total=groups.reduce((n,g)=>n+g.counts.tests,0);a.equal(total,3749);
const browserFile=latest("local-browser-"),b=read(browserFile),preserveFile=latest("preserve-"),preserve=read(preserveFile);
a.equal(b.status,"BROWSER_PASS");a(b.checks.every(x=>x.pass));a.equal(b.checks.length,1812);a.equal(b.layouts.length,385);a.equal(preserve.status,"PASS");
const sources=[];for(const dir of ["training-rules-demo","_offline/phase6e16"])for(const f of fs.readdirSync(p.join(root,dir)))if(fs.statSync(p.join(root,dir,f)).isFile())sources.push(dir+"/"+f);
const evidence={package:"6E-16",status:"LOCAL TECHNICAL PASS; publication verified separately",baseline:read(p.join(out,"before.json")).head,source_sha256:Object.fromEntries(sources.map(f=>[f,sha(p.join(root,f))])),tests:{total,new16:207,frozen:3542,groups,known_limitations_not_recognition_success:true,medical_validation:false},browser:{checks:1812,layouts:385,settings:24,emulated_only:true},preservation:preserve,raw_evidence:Object.fromEntries([...files,browserFile,preserveFile].map(f=>[p.relative(root,f).replaceAll("\\","/"),sha(f)])),owner_accepted:false,frozen:false,hosted_calls:0,external_ai_calls:0,real_member_ai:false,support_hold:"SU-487979"};
const examples=[];for(const spec of R.scenarios){const r=R.run(spec.id),s=r.model.view();a(R.assess(r,s).pass);for(const [i,language]of ["nl","en","de"].entries())examples.push({scenario:spec.id,language,title:spec.title[i],expected_message:spec.expected[i],intake:s.intake,catalog:{id:s.catalog.id,version:s.catalog.version},plan:s.draft?.plan??s.active?.plan??null,results:r.events.map(e=>({action:e.action,reason:e.reason,message:C.errors[e.reason]?.[i]??e.reason})),pass:true});}
for(const [file,data]of [["PHASE6E16_EVIDENCE.json",evidence],["PHASE6E16_EXAMPLES.json",examples]])fs.writeFileSync(p.join(root,"docs",file),JSON.stringify(data,null,2)+"\n",{flag:"wx"});
console.log(JSON.stringify({total,sources:sources.length,examples:examples.length}));
