const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm"),cp=require("node:child_process"),path=require("node:path");
const root=path.resolve(__dirname,"../.."),source=fs.readFileSync(path.join(root,"assets/phase3-training-engine.js"),"utf8");
function timer(){
 let now=1000000;
 const c=vm.createContext({Date:{now:()=>now},Number,Boolean,Math,phase3State:{activeSession:{status:"active",plannedExercises:[{restSeconds:75}],setLogs:{},focus:null}},phase3FocusOpen:true,
  phase3TimerId:null,phase3TimerEndsAt:0,phase3LastVibrationSecond:null,phase3SetSaving:false,phase3FinishSaving:false,
  phase3SaveLocal(){},phase3SyncActiveSession(){},phase3SyncFocusPortal(){},phase3CancelVibration(){},phase3Text:x=>x,renderTraining(){},
  document:{querySelector:()=>null},window:{setInterval(){c.intervals++;return 1;},clearInterval(){}},intervals:0});
 const fn=name=>{const start=source.indexOf("  function "+name+"(");assert(start>=0,name);return source.slice(start,source.indexOf("\n  function ",start+1));};
 for(const name of ["phase3DefaultFocusState","phase3EnsureSessionFocus","phase3ApplyFocusStep","phase3StartTimer","phase3EnsureTimerRunning","phase3StopTimer","phase3FinishRestTimer","phase3SetTimerEnabled","phase3StartManualRest","phase3PauseRestTimer","phase3ResumeRestTimer","phase3AddRestSeconds","phase3SetRestExpanded"])
  vm.runInContext(fn(name),c);
 c.phase3UpdateTimerText=()=>{};
 c.tick=ms=>now+=ms;c.phase3State.activeSession.focus=c.phase3DefaultFocusState();return c;
}
test("manual Start opens large; minimizing/reopening never changes deadline, logs or completion",()=>{
 const c=timer(),s=c.phase3State.activeSession;
 c.phase3SetTimerEnabled(true);c.phase3StartManualRest();const end=s.focus.rest.endsAt;
 assert.equal(s.focus.rest.expanded,true);c.phase3SetRestExpanded(false);assert.equal(s.focus.rest.expanded,false);
 c.tick(5000);c.phase3SetRestExpanded(true);c.phase3StartManualRest();
 assert.equal(s.focus.rest.endsAt,end);assert.equal(c.intervals,1);assert.equal(Object.keys(s.setLogs).length,0);assert.equal(s.focus.allExercisesCompleted,false);
});
test("pause/add/resume and serialized view retain elapsed time and ring duration",()=>{
 const c=timer(),s=c.phase3State.activeSession;
 c.phase3SetTimerEnabled(true);c.phase3StartManualRest();c.tick(10000);c.phase3PauseRestTimer();
 assert.equal(s.focus.rest.remainingMs,65000);c.tick(10000);c.phase3AddRestSeconds(15);
 assert.equal(s.focus.rest.remainingMs,80000);assert.equal(s.focus.rest.durationSeconds,90);
 s.focus=JSON.parse(JSON.stringify(s.focus));c.phase3EnsureSessionFocus(s);assert.equal(s.focus.rest.expanded,true);
 c.phase3ResumeRestTimer();assert.equal(s.focus.rest.endsAt,1100000);
 c.phase3FinishRestTimer();assert.equal(s.focus.rest,null);assert.equal(s.focus.currentSetIndex,1);assert.equal(s.status,"active");
});
test("automatic rest stays compact; explicit off removes either presentation",()=>{
 const c=timer(),s=c.phase3State.activeSession;
 c.phase3SetTimerEnabled(true);c.phase3StartTimer(90,{exerciseIndex:0,setIndex:2});
 assert.equal(s.focus.rest.expanded,false);c.phase3SetRestExpanded(true);c.phase3SetTimerEnabled(false);
 assert.equal(s.focus.rest,null);assert.equal(s.focus.timerEnabled,false);assert.equal(Object.keys(s.setLogs).length,0);
});
test("new task changes only four authorized runtime paths, training tests and docs",()=>{
 const git=(...args)=>cp.execFileSync("git",args,{cwd:root,windowsHide:true,encoding:"utf8"}).trim();
 const baseline="dd3b4e8af6974e6f6bbf8e9ba8c1e2e53720aac8";
 const allowed=["app.js","index.html","assets/phase3-training-engine.js","assets/training-workout.css"];
 const paths=[...git("diff","--name-only",baseline).split("\n"),...git("ls-files","--others","--exclude-standard").split("\n")].filter(Boolean);
 assert(paths.every(p=>allowed.includes(p)||p.startsWith("docs/")||p.startsWith("_tests/training/")),paths.join("\n"));
 assert.equal(git("diff",baseline,"--","_offline","supabase",".github",".codex","AGENTS.md","assets/training-workout-ui.js","assets/training-workout-model.js","assets/phase6d-owner-settings.js"),"");
 for(const file of ["TRAINING_MOBILE_EVIDENCE.json","TRAINING_WORKOUT_EVIDENCE.json","PHASE6E1_EVIDENCE.json","PHASE6E0_FREEZE_RECEIPT.md","PACKAGE6D_CORRECTED_FREEZE_AND_6E_OWNER_DECISIONS.md"])
  assert.equal(git("diff",baseline,"--","docs/"+file),"",file);
});
