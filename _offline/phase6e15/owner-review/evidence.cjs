"use strict";
const fs=require("node:fs"),p=require("node:path"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../../.."),out=process.argv[2],read=f=>JSON.parse(fs.readFileSync(f)),sha=f=>crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const latest=prefix=>p.join(out,"verified",fs.readdirSync(p.join(out,"verified")).filter(f=>f.startsWith(prefix)&&f.endsWith(".json")).sort().at(-1));
const files=[latest("review-tests-"),latest("local-owner-browser-"),latest("local-browser-")], [unit,ui,legacy]=files.map(read);
a.equal(unit.status,0);a.equal(unit.counts.fail,0);a.equal(ui.status,"OWNER_BROWSER_PASS");a.equal(legacy.status,"BROWSER_PASS");
const before=read(p.join(out,"before.json"));let count=0;
for(const [f,h]of Object.entries(before.files))if(!before.allowed.includes(f)){a.equal(sha(p.join(root,f)),h,f);count++;}
const sources=[...before.allowed,"independent-intake-demo/review.js",...fs.readdirSync(__dirname).filter(f=>fs.statSync(p.join(__dirname,f)).isFile()).map(f=>"_offline/phase6e15/owner-review/"+f)];
const evidence={package:"6E-15 owner test mode",status:"TECHNICAL PASS / READY FOR OWNER RETEST",owner_accepted:false,frozen:false,baseline:before.head,
 tests:{unit:unit.counts,new_unit:unit.counts.pass-245,existing_unit:245,new_browser:ui.checks.length,new_layouts:ui.layouts.length,legacy_browser:legacy.checks.length,legacy_layouts:legacy.layouts.length,settings_each:24,physical_phone:false},
 preserved_baseline_files:count,existing_allowed_changes:before.allowed,source_sha256:Object.fromEntries(sources.map(f=>[f,sha(p.join(root,f))])),
 evidence_sha256:Object.fromEntries([...files,p.join(out,"before.json")].map(f=>[p.relative(root,f).replaceAll("\\","/"),sha(f)])),
 runtime_changed:false,hosted_supabase_operations:0,external_ai_calls:0,external_ai_cost_eur:"0.00",real_member_ai_enabled:false,production_touched:false,support_hold:"6E-11 SU-487979"};
fs.writeFileSync(p.join(root,"docs/PHASE6E15_OWNER_TESTMODE_EVIDENCE.json"),JSON.stringify(evidence,null,2)+"\n",{flag:"wx"});console.log(JSON.stringify(evidence.tests));
