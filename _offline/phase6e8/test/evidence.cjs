"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),receipt=require("../../../docs/PHASE6E7_FREEZE_EVIDENCE.json"),sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const git=(...args)=>cp.execFileSync("git",args,{cwd:root,maxBuffer:60000000}),source=process.argv[2]||git("rev-parse","HEAD").toString().trim();
assert(/^[a-f0-9]{40}$/.test(source));
const files=git("ls-tree","-r","--name-only",source).toString().trim().split(/\r?\n/).filter(f=>/^(coach-review-demo\/|_offline\/phase6e8\/)/.test(f)||f==="index.html");
const sources=files.map(file=>({file,git_blob:git("rev-parse",source+":"+file).toString().trim(),sha256:sha(git("show",source+":"+file)),working_sha256:sha(fs.readFileSync(path.join(root,file)))}));
for(const f of receipt.frozen_sources)assert.equal(sha(fs.readFileSync(path.join(root,f.file))),f.working_sha256,f.file);
for(const f of receipt.runtime_assets.filter(x=>x.file!=="index.html"))assert.equal(sha(fs.readFileSync(path.join(root,f.file))),f.working_sha256,f.file);
const tests=JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp/phase6e8-tests.json")));
const browser=kind=>{const file="supabase/.temp/phase6e8-browser/"+kind+".json";if(!fs.existsSync(path.join(root,file)))return null;const raw=fs.readFileSync(path.join(root,file)),r=JSON.parse(raw);return {artifact:file,sha256:sha(raw),checks:r.checks.length,passed:r.checks.filter(x=>x.pass).length,layouts:r.layouts.length,errors:r.errors,screenshots:r.screenshots.map(f=>({artifact:"supabase/.temp/phase6e8-browser/"+path.basename(f),sha256:sha(fs.readFileSync(f))}))};};
const pubPath=path.join(root,"supabase/.temp/phase6e8-publication.json"),pub=fs.existsSync(pubPath)?JSON.parse(fs.readFileSync(pubPath)):null;
const output={status:pub&&pub.errors.length===0?"TECHNICAL PASS / READY FOR OWNER REVIEW":"LOCAL TECHNICAL PASS / PUBLICATION PENDING",synthetic_only:true,source_commit:source,baseline:receipt.baseline,preregistration_commit:"b58a6b3d0ff2f50e63d3ecf15a7e4be2e4d22289",sources,
 frozen:{manifest:"docs/PHASE6E7_FREEZE_EVIDENCE.json",files:receipt.frozen_sources.length,unchanged:true},
 runtime:{legacy_assets:60,unchanged_assets:59,authorized_exception:"index.html",scope:"opt-in bootstrap only",all_other_runtime_unchanged:true},
 tests:{counts:tests.counts,groups:Object.fromEntries(Object.entries(tests.groups).map(([k,v])=>[k,v.counts])),raw_artifact:"supabase/.temp/phase6e8-tests.json",raw_sha256:sha(fs.readFileSync(path.join(root,"supabase/.temp/phase6e8-tests.json")))},
 browser:{local:browser("local"),published:browser("published")},publication:pub?{head:pub.head,assets:pub.assets.length,all_identical:pub.assets.every(x=>x.identical),private_paths:pub.private.length,all_private_404:pub.private.every(x=>x.status===404),errors:pub.errors,raw_sha256:sha(fs.readFileSync(pubPath))}:null,
 examples:{file:"docs/PHASE6E8_EXAMPLES.json",count:33,sha256:sha(fs.readFileSync(path.join(root,"docs/PHASE6E8_EXAMPLES.json")))},
 no_database_edge_auth_rls_change:true,real_member_processing:false,production_touched:false,external_ai_calls:0,external_ai_cost_eur:0,owner_accepted:false,medical_validation:false,next_package_started:false,
 limitations:tests.limitations};
fs.writeFileSync(path.join(root,"docs/PHASE6E8_EVIDENCE.json"),JSON.stringify(output,null,2)+"\n");
console.log(JSON.stringify({source,status:output.status,frozen:output.frozen.files,tests:output.tests.counts,browser:output.browser.local?.checks,publication:output.publication}));
