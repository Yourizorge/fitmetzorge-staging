"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),[tests,browser,baseline]=process.argv.slice(2);
const read=f=>JSON.parse(fs.readFileSync(f)),sha=f=>crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const u=read(path.join(tests,"unit-regressions.json")),b=read(path.join(browser,"local-browser.json"));
a(Object.values(u.groups).every(x=>x.exit===0&&x.counts.fail===0));a.equal(b.status,"BROWSER_PASS");a.equal(b.layouts.length,24);a.equal(b.checks.length,283);
const before=read(path.join(baseline,"before.json"));
for(const [f,h]of Object.entries(before.sources))a.equal(sha(path.join(root,f)),h,f);
const priorPath=path.join(root,"supabase/.temp/phase6e11-support-wait-74b97a33fa684a938c93397036c9b843/manifest.json");
const prior=read(priorPath);for(const [f,h]of Object.entries(prior.evidence_sha256))a.equal(sha(path.join(root,f)),h,"historical:"+f);
const sources={};for(const dir of ["_offline/phase6e12","workout-reflection-demo"]){
 for(const f of fs.readdirSync(path.join(root,dir),{recursive:true}).filter(f=>fs.statSync(path.join(root,dir,f)).isFile())){
  const name=dir+"/"+f.replaceAll("\\","/");sources[name]=sha(path.join(root,name));
 }}
const report={status:"OFFLINE_TECHNICAL_PASS_READY_FOR_OWNER_REVIEW",ticket:"SU-487979",hosted6e11:"NO_GO",
 baseline:before.head,owner_accepted:false,frozen:false,unit_tests:Object.values(u.groups).reduce((n,x)=>n+x.counts.tests,0),
 new_behavior_tests:179,source_identity_tests:278,groups:Object.fromEntries(Object.entries(u.groups).map(([k,v])=>[k,v.counts])),
 historical_checkout_byte_guards_replaced:u.historical_6e9_checkout_byte_guards_replaced,
 browser:{checks:b.checks.length,layouts:b.layouts.length,storage_attempts:b.storage.length,errors:b.errors.length,physical_phone_test:false},
 existing_worktree_files_unchanged:Object.keys(before.sources).length,historical_evidence_files_unchanged:Object.keys(prior.evidence_sha256).length,
 historical_pairs:112,historical_step113:"incomplete",
 migrations:Object.fromEntries(fs.readdirSync(path.join(root,"supabase/migrations")).filter(f=>/phase6e11_rpc_bridge|phase6e11_request_binding/.test(f)).map(f=>[f,sha(path.join(root,"supabase/migrations",f))])),
 evidence:{unit_sha256:sha(path.join(tests,"unit-regressions.json")),browser_sha256:sha(path.join(browser,"local-browser.json")),before_sha256:sha(path.join(baseline,"before.json")),historical_manifest_sha256:sha(priorPath)},
 source_sha256:sources,hosted_database_calls:0,jit_attempts:0,hosted_auth_tests:0,hosted_fixture_cleanup:false,
 external_ai_calls:0,external_ai_cost_eur:"0.00",real_member_ai_enabled:false,production_touched:false,
 limits:["Browser examples are bounded build-time outputs; arbitrary input is facts-only","Roles are simulated, not authentication","No hosted security, database or physical-phone proof","No medical/privacy/legal/language expert approval"],
 publication:"Pending controlled commit/push, then independent Pages verification"};
fs.writeFileSync(path.join(root,"docs/PHASE6E12_EVIDENCE.json"),JSON.stringify(report,null,2)+"\n",{flag:"wx"});
console.log(JSON.stringify({status:report.status,unit_tests:report.unit_tests,existing_files:report.existing_worktree_files_unchanged,historical_evidence:report.historical_evidence_files_unchanged}));
