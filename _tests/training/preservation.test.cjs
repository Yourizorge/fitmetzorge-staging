const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),vm=require("node:vm");
const root=path.resolve(__dirname,"../.."),base="1af2e04fc4418876e5591dd45cf522fb23667daf";
const git=(...args)=>cp.execFileSync("git",args,{cwd:root,encoding:"utf8",windowsHide:true}).trim();
const runtime=["app.js","index.html","assets/phase3-training-engine.js","assets/phase6d-owner-settings.js","assets/training-workout-model.js","assets/training-workout-ui.js","assets/training-workout.css"];
const migration="supabase/migrations/20260908100106_training_workout_editor.sql";
test("current owner-authorized diff only; no historical freeze assertion weakened",()=>{
 assert.equal(git("remote","get-url","origin"),"https://github.com/Yourizorge/fitmetzorge-staging.git");
 assert.equal(git("branch","--show-current"),"main");
 const allowed=f=>runtime.includes(f)||f===migration||f.startsWith("docs/")||f.startsWith("_tests/training/")||
 ["_offline/phase6e1/context.cjs","_offline/phase6e1/training-followup-cases.json","_offline/phase6e1/test/training-followup.test.cjs"].includes(f);
 const changes=[...git("diff","--name-only",base).split("\n"),...git("ls-files","--others","--exclude-standard").split("\n")].filter(Boolean);
 assert(changes.every(allowed),changes.filter(f=>!allowed(f)).join("\n"));
 for(const f of ["_offline/phase6e1/test/isolation.test.cjs","docs/PHASE6E0_OWNER_DECISIONS.md","docs/PACKAGE6D_CORRECTED_FREEZE_AND_6E_OWNER_DECISIONS.md","docs/PHASE6E0_FREEZE_RECEIPT.md","docs/PHASE6E0_FREEZE_EVIDENCE.json","docs/PHASE6E1_EVIDENCE.json"])
  assert.equal(git("diff",base,"--",f),"",f);
});
test("23 frozen 6E0 working bytes, and all other tracked runtime bytes retained",()=>{
 const receipt=require("../../docs/PHASE6E0_FREEZE_EVIDENCE.json");
 assert.equal(receipt.offline_sources.length,23);
 for(const f of receipt.offline_sources)assert.equal(crypto.createHash("sha256").update(fs.readFileSync(path.join(root,f.file))).digest("hex"),f.sha256,f.file);
 const files=git("ls-tree","-r","--name-only",base).split("\n").filter(f=>!runtime.includes(f)&&
  ((!f.includes("/")&&/\.(html|css|js|png)$/.test(f))||(f.startsWith("assets/")&&!/(-check|-benchmark|\.test)\.(cjs|js)$/.test(f))));
 assert(files.length>=50);
 for(const f of files) {
  const bytes=cp.execFileSync("git",["cat-file","blob",base+":"+f],{cwd:root,windowsHide:true,maxBuffer:30000000});
  const actual=fs.readFileSync(path.join(root,f));
  if(/\.(?:js|cjs|css|html|json|md|sql|toml|txt|yml|yaml|py|ps1|svg|csv|gitignore|gitattributes)$/.test(f)||path.basename(f).startsWith("."))
   assert.equal(actual.toString().replace(/\r\n/g,"\n"),bytes.toString().replace(/\r\n/g,"\n"),f);
  else assert(actual.equals(bytes),f);
 }
});
test("authorized runtime does not import offline AI and new model is pure",()=>{
 for(const f of runtime)assert.doesNotMatch(fs.readFileSync(path.join(root,f),"utf8"),/_offline|phase6e[01]\./,f);
 assert.doesNotMatch(fs.readFileSync(path.join(root,"assets/training-workout-model.js"),"utf8"),/\bfetch\b|supabase|localStorage|sessionStorage/);
});
test("overload blank/null RPE and RIR never imply room for more load",()=>{
 const src=fs.readFileSync(path.join(root,"assets/phase3-training-engine.js"),"utf8");
 const fn=src.slice(src.indexOf("  function phase3OverloadSignal("),src.indexOf("  function phase3CancelVibration("));
 const context=vm.createContext({window:{FMZ_WORKOUT_MODEL:require("../../assets/training-workout-model.js")},phase3Text:x=>x});
 vm.runInContext(fn,context);
 for(const v of [""," ",null,undefined,0])assert.equal(context.phase3OverloadSignal({key:"a",targetSets:1},{setLogs:{"a__1":{rir:v,rpe:v}}}),"overloadRepeat");
 assert.equal(context.phase3OverloadSignal({key:"a",targetSets:1},{setLogs:{"a__1":{rir:2,rpe:null}}}),"overloadPotential");
});
test("migration only additive Training schema with RLS and no member backfill",()=>{
 const sql=fs.readFileSync(path.join(root,migration),"utf8");
 assert.doesNotMatch(sql,/\bdrop\s+(?:table|column|schema)|\btruncate\b|disable\s+row\s+level|create\s+table|\bdelete\s+from\b/i);
 assert.equal((sql.match(/security definer/g)||[]).length,2);
 assert(sql.includes("fmz_phase3_training_day_limit:"));
 assert(sql.includes("fmz_member_settings:"));
 assert.doesNotMatch(sql,/supabase_migrations|hgoygcviutmynaihcvpd|vault\./);
});
test("new recognition cases were committed before corrections",()=>{
 assert.equal(git("diff","0e8e77a","--","_offline/phase6e1/training-followup-cases.json","_offline/phase6e1/test/training-followup.test.cjs","docs/TRAINING_FOLLOWUP_PREREGISTRATION.md"),"");
 assert.equal(git("diff",base,"0e8e77a","--","_offline/phase6e1/context.cjs"),"");
});
