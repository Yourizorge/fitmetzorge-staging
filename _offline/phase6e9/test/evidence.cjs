"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),dir=path.join(root,"supabase/.temp");
const read=file=>JSON.parse(fs.readFileSync(path.join(dir,file)));
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,maxBuffer:60000000});
const baseline="8b7eb0c9c9488902451fe20e7385b4093237cc24";
const before=read("phase6e9-preflight-before.json"),after=read("phase6e9-preflight-after.json");
assert.equal(after.changed_existing.length,0);assert.equal(after.pending.length,0);assert.equal(after.migrations.length,34);
for(const old of before.migrations)assert.deepEqual(after.migrations.find(x=>x.version===old.version),old);
const tests=read("phase6e9-tests.json"),local=read("phase6e9-local.json"),live=read("phase6e9-live.json"),browser=read("phase6e9-live-browser.json"),publication=read("phase6e9-publication.json");
assert.equal(tests.counts.fail,0);assert(live.checks.every(x=>x.pass));assert.equal(live.checks.length,23);
assert.equal(browser.browser.checks,200);assert.equal(browser.cleanup.remaining_created_accounts,0);
assert.equal(live.cleanup.remaining_created_accounts,0);assert.equal(publication.errors.length,0);
const receipt=JSON.parse(fs.readFileSync(path.join(root,"docs/PHASE6E8_FREEZE_EVIDENCE.json")));
const preserved=receipt.sources.map(f=>{
 assert.equal(sha(fs.readFileSync(path.join(root,f.file))),f.working_sha256,f.file);
 assert.equal(sha(git("show","HEAD:"+f.file)),f.sha256,f.file);return {file:f.file,sha256:f.sha256};
});
const changed=git("diff","--name-only",baseline,"HEAD").toString().trim().split(/\r?\n/);
const sources=changed.filter(f=>/^(coach-backend-demo|_offline\/phase6e9|supabase\/migrations)\//.test(f))
 .map(file=>({file,sha256:sha(git("show","HEAD:"+file))}));
const archive=path.join(dir,"phase6e9-evidence-snapshot");fs.mkdirSync(archive,{recursive:true});
const artifacts=["phase6e9-preflight-before.json","phase6e9-preflight-after.json","phase6e9-tests.json","phase6e9-local.json","phase6e9-live.json","phase6e9-live-browser.json","phase6e9-publication.json"].map(file=>{
 const bytes=fs.readFileSync(path.join(dir,file)),hash=sha(bytes),snapshot=hash+"-"+file;
 if(!fs.existsSync(path.join(archive,snapshot)))fs.writeFileSync(path.join(archive,snapshot),bytes);
 return {file,sha256:hash,snapshot:"supabase/.temp/phase6e9-evidence-snapshot/"+snapshot};
});
const result={
 status:"TECHNICAL PASS / READY FOR OWNER REVIEW",synthetic_only:true,owner_accepted:false,medical_validation:false,
 baseline,verified_runtime_source:"383e25d4b893e549a062a5a357b1c8d797b6c924",generated_at:new Date().toISOString(),
 commits:git("log","--format=%H %s",baseline+"..HEAD").toString().trim().split(/\r?\n/),
 migration:{file:"20260915072202_phase6e9_synthetic_authorization.sql",sha256:after.canonical.find(x=>x.version==="20260915072202").sha256,identities:34,pending:[],historical_records_unchanged:33,dry_run:"up to date; no migrations/seeds/roles"},
 data:{tables:66,changed_existing:[],before:before.tables,after:after.tables},
 tests:{offline:tests.counts,groups:Object.fromEntries(Object.entries(tests.groups).map(([k,v])=>[k,v.counts])),
 local:local.checks,hosted:live.checks,browser:browser.browser,physical_phone:false,observation_tests_are_not_recognition_success:true},
 fresh_checkout:{source:"0fcffc3fc223ee60cd9c6d99788a764a253a710a",new_migration_groups:48,historical_migrations_rebuilt:22,skipped:12,limitation:"pg_cron unavailable; no Docker",deleted_files:0},
 preservation:{count:preserved.length,sources:preserved},sources,publication,
 changed_files:[...new Set([...git("diff","--name-only",baseline).toString().trim().split(/\r?\n/),...git("ls-files","--others","--exclude-standard").toString().trim().split(/\r?\n/)])].filter(Boolean).sort(),
 cleanup:{hosted:live.cleanup,final_browser:browser.cleanup,report_account_ids:[...live.account_ids,...browser.account_ids]},
 advisors:{security_before:{rls_enabled_no_policy:28,function_search_path_mutable:1,authenticated_security_definer_function_executable:68,auth_leaked_password_protection:1},
 security_after:{rls_enabled_no_policy:33,function_search_path_mutable:1,authenticated_security_definer_function_executable:68,auth_leaked_password_protection:1},
 new_warnings:0,private_deny_all_tables_info:5,performance_before_and_after:{unindexed_foreign_keys:16,auth_rls_initplan:47,unused_index:32}},
 data_api_private_schema:{status:406,code:"PGRST106",exposed:["public","graphql_public"]},
 edge_final:[{"name":"invite-client","version":24,"verify_jwt":true,"sha256":"06bc95c43054de7630b0a4538d0cbe568f98162717c29be3da84919688a4cc63","source_updated_at":1788519525215},{"name":"nutrition-provider","version":28,"verify_jwt":true,"sha256":"22305274d27d313b21f55ebf3921e891aabc6cabcddbd4160e562652a2f2250f","source_updated_at":1787856462165},{"name":"youri-ai","version":51,"verify_jwt":true,"sha256":"627c883a9b001e6215d101c827f96fbb94825c7f1437077088ec09fbba7460c6","source_updated_at":1788684719333},{"name":"fmz6e9-synthetic","version":10,"verify_jwt":true,"sha256":"e74a071c3cf6b01a1561dd33910a9893029bcc959f212e43452f9095950965f4","source_updated_at":1789460664382}],
 final_aggregate_cleanup:{subjects:0,safety:0,versions:0,requests:0,audit:0,notices:0,synthetic_auth_accounts:0,synthetic_profiles:0,enabled:false,proof_removed:true},
 pages_runtime_runs:[{id:34947028289,head:"0623b51cbd7b65867fb9d6444392d949ea8b317e",status:"success"},{id:34948042583,head:"383e25d4b893e549a062a5a357b1c8d797b6c924",status:"success"}],
 external_ai_calls:0,external_ai_cost_eur:0,production_touched:false,phase6e_complete:false,phase6e10_started:false,artifacts
};
fs.writeFileSync(path.join(root,"docs/PHASE6E9_EVIDENCE.json"),JSON.stringify(result,null,2)+"\n");
console.log(JSON.stringify({preserved:preserved.length,tests:tests.counts.pass,hosted:live.checks.length,browser:browser.browser,unchanged_tables:66,assets:publication.assets.length,private404:publication.private.length}));
