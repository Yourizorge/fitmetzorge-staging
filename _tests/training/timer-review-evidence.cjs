const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict"),vm=require("node:vm");
const root=path.resolve(__dirname,"../.."),baseline="dd3b4e8af6974e6f6bbf8e9ba8c1e2e53720aac8";
const files=["app.js","index.html","assets/phase3-training-engine.js","assets/training-workout.css"];
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
const read=f=>fs.readFileSync(path.join(root,f));
const sourceHashes=()=>Object.fromEntries(files.map(f=>[f,sha(read(f).toString().replace(/\r\n/g,"\n"))]));
function run(command,args){const r=cp.spawnSync(command,args,{cwd:root,windowsHide:true,encoding:"utf8",maxBuffer:30000000});assert.equal(r.status,0,command+" "+args.join(" ")+"\n"+r.stdout+"\n"+r.stderr);return r.stdout.trim();}
const git=(...args)=>run("git",args);
const load=f=>JSON.parse(read(f));
const summary=b=>({pass:b.overall_pass,checks:b.checks.length,fail:b.checks.filter(c=>!c.pass).length,layouts:b.layouts.length,screens:new Set(b.screens).size,source:b.source});
if(process.argv[2]==="pre"){
 const args=["--test","--test-reporter=tap","_tests/training/timer-review.test.cjs","_tests/training/mobile.test.cjs","_tests/training/model.test.cjs","_tests/training/preservation.test.cjs","assets/phase6d-theme-authority.test.cjs"];
 const output=run(process.execPath,args),count=Number(output.match(/# tests (\d+)/)[1]);
 assert.match(output,/# fail 0/);
 const recognition=run(process.execPath,["--test","--test-reporter=tap","_offline/phase6e1/test/training-followup.test.cjs"]);
 assert.match(recognition,/# fail 0/);
 const examples=require("../../_offline/phase6e1/test/examples.cjs").examples();
 assert.equal(examples.length,5);
 for(const example of examples)for(const stage of [example.before,example.after]){
  assert.equal(stage.medical_clearance,false);assert.equal(stage.automatic_actions_allowed,false);assert.equal(stage.recommendations.length,0);assert.equal(stage.actions.length,0);
 }
 const completion=JSON.parse(run(process.execPath,["_tests/training/completion-regression.cjs"]));
 assert(completion.overall_pass);
 for(const f of ["app.js","assets/phase3-training-engine.js","assets/training-workout-ui.js"])run(process.execPath,["--check",f]);
 git("diff","--check");
 const result={checked_at:new Date().toISOString(),head:git("rev-parse","HEAD"),command:"node "+args.join(" "),tests:count,passed:count,failed:0,output,completion,recognition,examples,
  syntax:["app.js","assets/phase3-training-engine.js","assets/training-workout-ui.js"],source_normalized_lf_hashes:sourceHashes()};
 fs.writeFileSync(path.join(root,"supabase/.temp/training-timer-review-unit.json"),JSON.stringify(result,null,2)+"\n");
 console.log(JSON.stringify({tests:count,completion:completion.pass_count,pass:true}));
}else{
 const unit=load("supabase/.temp/training-timer-review-unit.json"),local=load("supabase/.temp/training-timer-review-browser-local.json"),live=load("supabase/.temp/training-timer-review-browser-live.json"),publication=load("supabase/.temp/training-timer-review-publication.json");
 assert.deepEqual(unit.source_normalized_lf_hashes,sourceHashes(),"runtime changed since preflight tests");
 for(const b of [local,live]){assert(b.overall_pass);assert(b.checks.every(c=>c.pass));assert(b.layouts.every(l=>!l.bad.length));assert(b.checks.some(c=>c.name.startsWith("320 ")));assert(b.checks.some(c=>c.name.startsWith("360 ")));assert(b.checks.some(c=>c.name.startsWith("390 ")));assert(b.checks.some(c=>c.name.startsWith("1440 ")));}
 const head=git("rev-parse","HEAD");assert.equal(publication.head,head);
 for(const dir of ["_offline","supabase",".github",".codex"])assert.equal(git("diff",baseline,"--",dir),"",dir);
 const context=vm.createContext({window:{FMZ_WORKOUT_MODEL:require("../../assets/training-workout-model.js")}});
 vm.runInContext(read("assets/training-workout-ui.js").toString(),context);
 const result={checked_at:new Date().toISOString(),baseline,source_head:head,scope:files,cache:"20260909-training-timer1",unit,local_summary:summary(local),published_summary:summary(live),local_browser:local,published_browser:live,
  publication,catalog:{count:load("supabase/.temp/training-catalog.json").length,sha256:sha(read("supabase/.temp/training-catalog.json"))},
  preservation:{offline_tree:git("rev-parse","HEAD:_offline"),baseline_offline_tree:git("rev-parse",baseline+":_offline"),offline_source_changes:0,database_changes:0,migration_changes:0,edge_changes:0,real_member_calls:0,production_touched:false,cleanup:false},
  limitations:["Keyboard: real focus/typing with reduced viewport, not physical iOS/Android OS keyboard.","Browser data is synthetic; no new live member fingerprint comparison.","No closed-app notification or cross-device real-time timer guarantee.","Owner phone acceptance is pending; 6E-1 remains offline."]};
 fs.writeFileSync(path.join(root,"docs/TRAINING_TIMER_REVIEW_EVIDENCE.json"),JSON.stringify(result,null,2)+"\n");
 console.log(JSON.stringify({head,unit:unit.tests,completion:unit.completion.pass_count,local:summary(local),published:summary(live),runtime_assets:publication.assets.length,private_404:publication.private_source_probes.length,pass:true}));
}
