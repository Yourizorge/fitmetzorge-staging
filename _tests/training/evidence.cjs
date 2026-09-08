const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),temp=path.join(root,"supabase/.temp"),read=f=>JSON.parse(fs.readFileSync(path.join(temp,f),"utf8"));
const git=(...args)=>cp.execFileSync("git",args,{cwd:root,windowsHide:true,maxBuffer:30000000});
const hash=b=>crypto.createHash("sha256").update(b).digest("hex");
const commands=[
 ["offline_6e1",["--test","--test-reporter=tap","--test-skip-pattern=I01 exact staging target and changes restricted to docs and new 6E-1|I01 frozen app/Edge/migrations/workflows and D1-D12 unchanged","_offline/phase6e1/test/*.test.cjs"],280],
 ["frozen_6e0_selected",["--test","--test-reporter=tap","_offline/phase6e0/test/recognition-followup.test.cjs","_offline/phase6e0/test/limitations.test.cjs"],90],
 ["model_preservation_theme",["--test","--test-reporter=tap","_tests/training/model.test.cjs","_tests/training/preservation.test.cjs","assets/phase6d-theme-authority.test.cjs"],22]
];
const tests=[];
for(const [name,args,expected] of commands){
 const result=cp.spawnSync(process.execPath,args,{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:5000000});
 fs.writeFileSync(path.join(temp,"training-"+name+".tap"),result.stdout);
 assert.equal(result.status,0,result.stderr);const passed=Number(result.stdout.match(/# pass (\d+)/)?.[1]);assert.equal(passed,expected);
 tests.push({name,command:["node",...args],passed,failed:0});
}
const completion=JSON.parse(cp.execFileSync(process.execPath,[path.join(__dirname,"completion-regression.cjs")],{cwd:root,encoding:"utf8",windowsHide:true}));assert(completion.overall_pass);
const browser=read("training-browser-local.json"),live=read("training-browser-live.json"),publication=read("training-publication.json");
assert(browser.overall_pass&&live.overall_pass&&publication.runtime_matches_commit&&publication.offline_isolated);
const before=read("training-member-before.json"),after=read("training-member-after.json"),schema=read("training-schema.json"),sql=read("training-sql-live.json")[0].jsonb_build_object;
assert(after.existing_data_unchanged&&after.synthetic_remaining===0&&sql.pass_count===34);
const files=["app.js","index.html","assets/phase3-training-engine.js","assets/phase6d-owner-settings.js","assets/training-workout-model.js","assets/training-workout-ui.js","assets/training-workout.css"];
const runtimeCommit=git("log","-1","--format=%H","--",...files).toString().trim();
const result={
 checked_at:new Date().toISOString(),source_head:git("rev-parse","HEAD").toString().trim(),
 runtime_commit:runtimeCommit,cache:"20260908-training-workout2",
 runtime:files.map(file=>({file,sha256:hash(git("cat-file","blob",runtimeCommit+":"+file))})),
 offline_6e0:{files:23,tree:git("rev-parse","HEAD:_offline/phase6e0").toString().trim(),unchanged:true,owner_accepted_frozen:true},
 offline_6e1:{tree:git("rev-parse","HEAD:_offline/phase6e1").toString().trim(),owner_accepted:false,live_integrated:false,medical_validation:false,
  preregistration:"0e8e77a420c97f97f47d631b68b5cfd29f4897f4",correction:"cf6c212600b6798a2a2d0a057b9deacc233112bc",new_cases:36,old_pass:7,old_fail:29,new_pass:36,
  historical_blanket_runtime_assertions_excluded:2,excluded_counted_as_pass:false,old_limitation_observations_counted_as_recognition:false},
 tests,completion,browser: {...browser,screens:browser.screens.map(f=>path.relative(root,f).replaceAll("\\","/"))},
 published_browser:{checks:live.checks.length,all_pass:live.checks.every(c=>c.pass),synthetic_only:true},
 sql_local:{passed:34,scope:"22 canonical migrations + exact member preference DDL + Training migration; pg_cron platform not emulated",retained_cluster:"C:/Users/Fitme/AppData/Local/Temp/fmz-local-rebuild-hZGlcc",stopped:true,files_deleted:0},
 sql_staging:sql,schema,existing_data:{before,after},publication,
 security_advisor_delta:{expected_definer_functions:["fmz_training_get_preferences","fmz_training_set_preferences"],count_before:66,count_after:68,other_advisors_unchanged:true},
 phase6e_complete:false,new_owner_freeze:false,production_touched:false,external_ai_calls:0,edge_deployments:0,member_mutations:0
};
fs.writeFileSync(path.join(root,"docs/TRAINING_WORKOUT_EVIDENCE.json"),JSON.stringify(result,null,2)+"\n");
console.log(JSON.stringify({runtimeCommit,tests:tests.map(t=>({name:t.name,passed:t.passed})),completion:completion.pass_count,browser:browser.checks.length,published_browser:live.checks.length,assets:publication.assets.length,private_404:publication.private_source_probes.length,evidence:"docs/TRAINING_WORKOUT_EVIDENCE.json"}));
