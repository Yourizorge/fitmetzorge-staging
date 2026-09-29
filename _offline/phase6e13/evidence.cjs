"use strict";
const fs=require("node:fs"),p=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../.."),[tests,browser]=process.argv.slice(2);
if(!tests||!browser)throw Error("paths");
const sha=x=>crypto.createHash("sha256").update(x).digest("hex"),read=f=>JSON.parse(fs.readFileSync(f));
const latest=(dir,prefix)=>p.join(dir,fs.readdirSync(dir).filter(n=>n.startsWith(prefix)&&n.endsWith(".json")).sort().at(-1));
const unitFile=latest(tests,"6e13-tests-"),browserFile=latest(browser,"local-browser-"),units=read(unitFile),b=read(browserFile),frozen=read(p.join(tests,"unit-regressions.json")),before=read(p.join(tests,"before.json"));
a.equal(units.exit,0);a.equal(b.status,"BROWSER_PASS");a.equal(b.layouts.length,24);
a(Object.values(frozen.groups).every(x=>x.exit===0&&x.counts.fail===0));
for(const [file,h]of Object.entries(before.files))a.equal(sha(fs.readFileSync(p.join(root,file))),h,file);
const sources={};
for(const dir of ["_offline/phase6e13","proactive-signals-demo"])for(const f of fs.readdirSync(p.join(root,dir),{recursive:true}).filter(f=>fs.statSync(p.join(root,dir,f)).isFile())){
 const file=dir+"/"+f.replaceAll("\\","/");sources[file]=sha(fs.readFileSync(p.join(root,file)));
}
const histPath=p.join(root,"supabase/.temp/phase6e11-support-wait-74b97a33fa684a938c93397036c9b843/manifest.json"),hist=read(histPath);
for(const [file,h]of Object.entries(hist.evidence_sha256))a.equal(sha(fs.readFileSync(p.join(root,file))),h,file);
const evidence={package:"6E-13",status:"OFFLINE TECHNICAL PASS / READY FOR OWNER REVIEW",owner_accepted:false,frozen:false,baseline:before.head,
 source_sha256:sources,tests:{new_technical:units.counts,limitation_observations:1,not_medical_recognition_validation:true,frozen_groups:Object.fromEntries(Object.entries(frozen.groups).map(([k,v])=>[k,v.counts])),
 frozen_total:Object.values(frozen.groups).reduce((n,x)=>n+x.counts.pass,0)},
 browser:{checks:b.checks.length,layouts:b.layouts.length,errors:b.errors.length,storage_attempts:b.storage.length,unexpected_egress:b.requests.filter(x=>!x.allowed).length,physical_phone_test:false},
 preserved:{existing_files:Object.keys(before.files).length,prior_evidence_hashes:Object.keys(hist.evidence_sha256).length,old_pairs:112,old_step113:"incomplete historical evidence",
 migrations:Object.fromEntries(Object.entries(before.files).filter(([n])=>/migrations\/.*phase6e11_(rpc_bridge|request_binding)\.sql$/.test(n)))},
 evidence_files:Object.fromEntries([unitFile,browserFile,p.join(tests,"before.json"),p.join(tests,"unit-regressions.json"),histPath].map(f=>[p.relative(root,f).replaceAll("\\","/"),sha(fs.readFileSync(f))])),
 limitations:["Fixed synthetic three-day policy; not validated notification cadence or health thresholds","One known German ordinary paraphrase remains clarification; observation not recognition success","Source manifests are synthetic integrity, not authentic server authority","No calorie/load adjustment, independent plan builder or live scheduler","No real data or medical/privacy/legal/language expert validation"],
 support_hold:"6E11 HOSTED ONLY / SU-487979",hosted_supabase_operations:0,migration_auth_edge_cleanup_operations:0,external_ai_calls:0,external_ai_cost_eur:"0.00",real_member_ai_enabled:false,production_touched:false,
 publication:"Separate post-push receipt required"};
fs.writeFileSync(p.join(root,"docs/PHASE6E13_EVIDENCE.json"),JSON.stringify(evidence,null,2)+"\n",{flag:"wx"});
console.log(JSON.stringify({new_tests:units.counts.pass,frozen_tests:evidence.tests.frozen_total,browser:b.checks.length,preserved:evidence.preserved.existing_files,historical:evidence.preserved.prior_evidence_hashes}));
