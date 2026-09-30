"use strict";
const fs=require("node:fs"),p=require("node:path"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../.."),out=process.argv[2],sha=x=>crypto.createHash("sha256").update(x).digest("hex"),read=f=>JSON.parse(fs.readFileSync(f));
const latest=prefix=>p.join(out,fs.readdirSync(out).filter(f=>f.startsWith(prefix)&&f.endsWith(".json")).sort().at(-1));
const paths=[latest("6e15-tests-"),latest("6e14-tests-"),latest("6e13-tests-"),p.join(out,"unit-regressions.json"),latest("local-browser-"),p.join(out,"before.json")];
const [n,f14,f13,old,b,before]=paths.map(read);a.equal(n.status,0);a.equal(f14.status,0);a.equal(f13.exit,0);a.equal(b.status,"BROWSER_PASS");a(Object.values(old.groups).every(g=>g.exit===0));
for(const [f,h]of Object.entries(before.files))a.equal(sha(fs.readFileSync(p.join(root,f))),h,f);
const histPath=p.join(root,"supabase/.temp/phase6e11-support-wait-74b97a33fa684a938c93397036c9b843/manifest.json"),hist=read(histPath);
for(const [f,h]of Object.entries(hist.evidence_sha256))a.equal(sha(fs.readFileSync(p.join(root,f))),h,f);
const source_sha256={};for(const dir of ["_offline/phase6e15","independent-intake-demo"])for(const f of fs.readdirSync(p.join(root,dir),{recursive:true}).filter(f=>fs.statSync(p.join(root,dir,f)).isFile())){const path=dir+"/"+f.replaceAll("\\","/");source_sha256[path]=sha(fs.readFileSync(p.join(root,path)));}
const total=n.counts.pass+f14.counts.pass+f13.counts.pass+Object.values(old.groups).reduce((s,g)=>s+g.counts.pass,0);
const e={package:"6E-15",status:"TECHNICAL PASS / READY FOR OWNER REVIEW",owner_accepted:false,frozen:false,baseline:before.head,source_sha256,
 tests:{new:n.counts,frozen14:f14.counts,frozen13:f13.counts,earlier:Object.fromEntries(Object.entries(old.groups).map(([k,g])=>[k,g.counts])),total,medical_validation:false,known_limitation_observations_not_recognition_success:true},
 browser:{checks:b.checks.length,settings:24,layout_inspections:b.layouts.length,errors:b.errors.length,unexpected_egress:b.requests.filter(x=>!x.allowed).length,physical_owner_test:false},
 preserved:{working_files:Object.keys(before.files).length,historical_evidence:Object.keys(hist.evidence_sha256).length,pairs:112,step113:"historical incomplete",migrations:Object.fromEntries(Object.entries(before.files).filter(([f])=>/migrations\/.*phase6e11_(rpc_bridge|request_binding)\.sql$/.test(f)))},
 evidence_files:Object.fromEntries([...paths,histPath].map(f=>[p.relative(root,f).replaceAll("\\","/"),sha(fs.readFileSync(f))])),
 support_hold:"6E11 hosted / SU-487979",hosted_supabase_operations:0,external_ai_calls:0,external_ai_cost_eur:"0.00",real_member_ai_enabled:false,production_touched:false};
fs.writeFileSync(p.join(root,"docs/PHASE6E15_EVIDENCE.json"),JSON.stringify(e,null,2)+"\n",{flag:"wx"});
require("../../independent-intake-demo/data.js");const D=FMZ15Data,M=require("../../independent-intake-demo/model.js"),L=require("../../independent-intake-demo/copy.js"),examples={};
for(const name of ["complete","limited","allergy","incomplete","complaint","imperial","unsupported_diet"])for(const [index,locale]of ["nl","en","de"].entries()){
 const f=JSON.parse(JSON.stringify(D.fixtures[name]));f.intake.locale=locale;const m=M.create(f,D.registry),r=m.command(m.event("build"));
 (examples[name]??={})[locale]={ok:r.ok,reason:r.reason,message:r.ok?L.words.proposalText[index]:L.words.errors[r.reason]?.[index],nutrition_note:L.words.nutritionText[index],recovery_note:L.words.recoveryText[index],draft:r.state.draft};
}
fs.writeFileSync(p.join(root,"docs/PHASE6E15_EXAMPLES.json"),JSON.stringify(examples,null,2)+"\n",{flag:"wx"});console.log(JSON.stringify({total,new:n.counts.pass,browser:b.checks.length,preserved:e.preserved.working_files,historical:e.preserved.historical_evidence}));
