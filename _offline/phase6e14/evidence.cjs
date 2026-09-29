"use strict";
const fs=require("node:fs"),p=require("node:path"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../.."),[out,ui]=process.argv.slice(2),sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const read=f=>JSON.parse(fs.readFileSync(f)),latest=(dir,prefix)=>p.join(dir,fs.readdirSync(dir).filter(f=>f.startsWith(prefix)&&f.endsWith(".json")).sort().at(-1));
const unitFile=latest(out,"6e14-tests-"),f13File=latest(out,"6e13-tests-"),browserFile=latest(ui,"local-browser-"),frozenFile=p.join(out,"unit-regressions.json");
const units=read(unitFile),f13=read(f13File),browser=read(browserFile),frozen=read(frozenFile),before=read(p.join(out,"before.json"));
a.equal(units.status,0);a.equal(f13.exit,0);a.equal(browser.status,"BROWSER_PASS");a.equal(browser.errors.length,0);a(Object.values(frozen.groups).every(x=>x.exit===0&&x.counts.fail===0));
for(const [file,h]of Object.entries(before.files))a.equal(sha(fs.readFileSync(p.join(root,file))),h,file);
const histPath=p.join(root,"supabase/.temp/phase6e11-support-wait-74b97a33fa684a938c93397036c9b843/manifest.json"),hist=read(histPath);
for(const [file,h]of Object.entries(hist.evidence_sha256))a.equal(sha(fs.readFileSync(p.join(root,file))),h,file);
const sources={};for(const dir of ["_offline/phase6e14","bounded-adjustments-demo"])for(const f of fs.readdirSync(p.join(root,dir),{recursive:true}).filter(f=>fs.statSync(p.join(root,dir,f)).isFile())){const file=dir+"/"+f.replaceAll("\\","/");sources[file]=sha(fs.readFileSync(p.join(root,file)));}
const result={package:"6E-14",status:"TECHNICAL PASS / READY FOR OWNER REVIEW",owner_accepted:false,frozen:false,baseline:before.head,source_sha256:sources,
 tests:{new:units.counts,frozen6e13:f13.counts,earlier_frozen:Object.fromEntries(Object.entries(frozen.groups).map(([k,v])=>[k,v.counts])),total:units.counts.pass+f13.counts.pass+Object.values(frozen.groups).reduce((n,x)=>n+x.counts.pass,0),known_limitation_observations_are_not_recognition_success:true,medical_validation:false},
 browser:{checks:browser.checks.length,layouts:browser.layouts.length,errors:browser.errors.length,unexpected_egress:browser.requests.filter(x=>!x.allowed).length,physical_phone_test:false},
 preservation:{working_files:Object.keys(before.files).length,historical_evidence:Object.keys(hist.evidence_sha256).length,valid_old_pairs:112,step113:"historical incomplete",migrations:Object.fromEntries(Object.entries(before.files).filter(([f])=>/migrations\/.*phase6e11_(rpc_bridge|request_binding)\.sql$/.test(f)))},
 evidence_files:Object.fromEntries([unitFile,f13File,browserFile,frozenFile,p.join(out,"before.json"),histPath].map(f=>[p.relative(root,f).replaceAll("\\","/"),sha(fs.readFileSync(f))])),
 support_hold:"6E11 HOSTED / SU-487979",hosted_supabase_operations:0,external_ai_calls:0,external_ai_cost_eur:"0.00",real_member_ai_enabled:false,production_touched:false,publication:"separate post-push receipt"};
fs.writeFileSync(p.join(root,"docs/PHASE6E14_EVIDENCE.json"),JSON.stringify(result,null,2)+"\n",{flag:"wx"});
require("../../bounded-adjustments-demo/data.js");const examples={};for(const name of ["a_progression","a_maintain","a_lb","b_schedule","nutrition_partial","recovery_reflection","calorie_rule_missing","current","self_reported","missing_rule"])examples[name]=Object.fromEntries(["nl","en","de"].map(l=>[l,globalThis.FMZ14Data[name][l].initial]));
fs.writeFileSync(p.join(root,"docs/PHASE6E14_EXAMPLES.json"),JSON.stringify(examples,null,2)+"\n",{flag:"wx"});
console.log(JSON.stringify({tests:result.tests.total,new:units.counts.pass,browser:result.browser.checks,preserved:result.preservation.working_files,historical:result.preservation.historical_evidence}));
