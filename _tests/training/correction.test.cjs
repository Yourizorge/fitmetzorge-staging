const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),vm=require("node:vm");
const root=path.resolve(__dirname,"../.."),baseline="037a338a84a6144a149d44238cd936630cfbe503",M=require("../../assets/training-workout-model.js");
const allowed=["app.js","index.html","assets/phase3-training-engine.js","assets/training-workout-model.js","assets/training-workout-ui.js","assets/training-workout.css"];
const migration="supabase/migrations/20260909215122_training_plan_effort_tracking.sql";
const git=(...args)=>cp.execFileSync("git",args,{cwd:root,windowsHide:true,maxBuffer:30000000});
const text=(...args)=>git(...args).toString().trim(),read=f=>fs.readFileSync(path.join(root,f)),sha=b=>crypto.createHash("sha256").update(b).digest("hex");
test("exact Training scope; no other runtime, policy, Edge, migration or offline edit",()=>{
 const paths=[...text("diff","--name-only",baseline).split("\n"),...text("ls-files","--others","--exclude-standard").split("\n")].filter(Boolean);
 assert(paths.every(f=>allowed.includes(f)||f===migration||f.startsWith("_tests/training/")||f.startsWith("docs/")),paths.join("\n"));
 assert.equal(text("diff",baseline,"--","_offline",".codex",".github","AGENTS.md"),"");
 const prior=text("ls-tree","-r","--name-only",baseline,"supabase").split("\n");
 for(const f of prior)assert.equal(text("diff",baseline,"--",f),"",f);
});
for(const phase of ["0","1"])test("frozen 6E"+phase+" exact source bytes",()=>{
 const receipt=JSON.parse(read("docs/PHASE6E"+phase+"_FREEZE_EVIDENCE.json"));
 for(const f of receipt.offline_sources)assert.equal(sha(read(f.file)),f.working_sha256||f.sha256,f.file);
});
test("54 unrelated runtime assets remain identical",()=>{
 const files=text("ls-tree","-r","--name-only",baseline).split("\n").filter(f=>(!f.includes("/")&&/\.(html|css|js|png)$/.test(f))||(f.startsWith("assets/")&&!/(-check|-benchmark|\.test)\.(cjs|js)$/.test(f)));
 const unchanged=files.filter(f=>!allowed.includes(f));assert.equal(unchanged.length,54);
 for(const f of unchanged){assert.equal(text("diff",baseline,"--",f),"",f);assert.equal(text("hash-object",f),text("rev-parse",baseline+":"+f),f);}
});
test("HTML only changes Training cache references",()=>{
 const normalize=b=>b.toString().replace(/\r\n/g,"\n").replaceAll("20260909-training-correction2","20260909-training-timer1");
 assert.equal(normalize(read("index.html")),normalize(git("cat-file","blob",baseline+":index.html")));
 const app=read("app.js").toString();assert.match(app,/trainingCss\.onerror/);assert.match(app,/await ready/);
});
for(const flags of [{rir:false,rpe:false},{rir:true,rpe:false},{rir:false,rpe:true},{rir:true,rpe:true}])test("independent choice "+JSON.stringify(flags),()=>{
 const ex=[{setTargets:[{reps:"8",weight:10,rir:0,rpe:9.5}]}],before=JSON.stringify(ex),snapshot=M.effortTracking(flags,ex);
 assert.deepEqual(snapshot,flags);flags.rir=!flags.rir;assert.notEqual(snapshot.rir,flags.rir);assert.equal(JSON.stringify(ex),before);
});
test("legacy score visibility preserves 0 versus blank, not global preferences",()=>{
 assert.deepEqual(M.effortTracking(null,[{targetSets:1,targetRir:0,targetRpe:9.5}]),{rir:true,rpe:true});
 assert.deepEqual(M.effortTracking(null,[{targetSets:1,targetRir:"",targetRpe:null}]),{rir:false,rpe:false});
 assert.deepEqual(M.effortTracking(null,[],[{rir:0,rpe:9.5}]),{rir:true,rpe:true});
});
function timer(){
 const file=path.join(__dirname,"timer-review.test.cjs"),source=fs.readFileSync(file,"utf8").split('test("manual Start')[0],context={require,__dirname,module:{exports:{}}};
 vm.runInNewContext(source+"\nmodule.exports=timer;",context);return context.module.exports();
}
test("large countdown, singleton, pause, serialized restart and explicit minimize",()=>{
 const c=timer(),s=c.phase3State.activeSession;c.phase3StartManualRest();assert.equal(s.focus.rest,null);
 c.phase3SetTimerEnabled(true);c.phase3StartManualRest();const end=s.focus.rest.endsAt;assert.equal(s.focus.rest.expanded,true);
 c.phase3StartManualRest();assert.equal(c.intervals,1);c.tick(5000);c.phase3SetRestExpanded(false);assert.equal(s.focus.rest.endsAt,end);
 c.phase3SetRestExpanded(true);c.phase3PauseRestTimer();assert.equal(s.focus.rest.remainingMs,70000);
 c.tick(10000);c.phase3AddRestSeconds(15);assert.equal(s.focus.rest.remainingMs,85000);
 s.focus=JSON.parse(JSON.stringify(s.focus));c.phase3ResumeRestTimer();assert.equal(s.focus.rest.endsAt,1100000);
 c.phase3FinishRestTimer();assert.equal(s.focus.rest,null);assert.equal(s.status,"active");assert.equal(Object.keys(s.setLogs).length,0);
});
test("opted-in set rest also large until explicit minimize; off removes it",()=>{
 const c=timer(),s=c.phase3State.activeSession;c.phase3SetTimerEnabled(true);c.phase3StartTimer(90,{exerciseIndex:0,setIndex:2});
 assert.equal(s.focus.rest.expanded,true);c.phase3SetRestExpanded(false);assert.equal(s.focus.rest.expanded,false);
 c.phase3SetTimerEnabled(false);assert.equal(s.focus.rest,null);assert.equal(s.focus.timerEnabled,false);
});
test("additive migration creates one invoker wrapper, no backfill or old function replacement",()=>{
 const sql=read(migration).toString();assert.equal((sql.match(/create function/g)||[]).length,1);assert.match(sql,/security invoker/);
 assert.doesNotMatch(sql,/alter table|drop |create or replace|delete from|security definer/i);
 assert.match(sql,/training_retry_payload_conflict/);assert.match(sql,/from public,anon/);
});

