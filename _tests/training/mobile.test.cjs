const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm"),cp=require("node:child_process"),path=require("node:path");
const root=path.resolve(__dirname,"../.."),baseline="633e9f9ab50bd298a66088e6cc0cb824215e98f5";
const source=fs.readFileSync(path.join(root,"assets/phase3-training-engine.js"),"utf8");
const catalog=require("../../supabase/.temp/training-catalog.json");
const groups=[
 ["barbell-bench-press","dumbbell-bench-press","incline-dumbbell-press","machine-bench-press","butterfly","cable-chest-fly"],
 ["wide-grip-lat-pulldown","seated-cable-rows","bent-over-barbell-row","one-arm-dumbbell-row","pull-up"],
 ["dumbbell-shoulder-press","standing-military-press","leverage-shoulder-press","lateral-raise","reverse-machine-flyes","face-pull"],
 ["barbell-squat","leg-press","leg-extensions","seated-leg-curl","lying-leg-curls","deadlift","romanian-deadlift","hip-thrust","split-squat-with-dumbbells","thigh-abductor","standing-calf-raises"],
 ["dumbbell-bicep-curl","barbell-curl","hammer-curls","triceps-pushdown","triceps-pushdown-rope-attachment"],
 ["crunches","cable-crunch"]
];
test("35 explicit basic variants resolve to existing UUIDs, never fuzzy aliases",()=>{
 const context=vm.createContext({window:{FMZ_WORKOUT_MODEL:require("../../assets/training-workout-model.js")}});
 vm.runInContext(fs.readFileSync(path.join(root,"assets/training-workout-ui.js"),"utf8"),context);
 const actual=JSON.parse(JSON.stringify(context.window.FMZ_WORKOUT_UI.basicGroups));
 assert.deepEqual(actual.map(g=>g.exercises.map(e=>e.slug)),groups);
 const rows=actual.flatMap(g=>g.exercises);assert.equal(rows.length,35);assert.equal(new Set(rows.map(e=>e.id)).size,35);
 for(const row of rows){const c=catalog.find(c=>c.id===row.id);assert(c,row.slug);assert.equal(c.canonical_slug,row.slug);assert(c.is_active);assert.equal(row.names.length,3);}
});
test("material and execution evidence distinguishes easily confused basics",()=>{
 const row=slug=>catalog.find(c=>c.canonical_slug===slug);
 for(const [slug,material,words] of [
  ["machine-bench-press","Machine",/Chest Press Machine/],
  ["standing-military-press","Barbell",/step back/i],
  ["dumbbell-shoulder-press","Dumbbell",/sit on/i],
  ["reverse-machine-flyes","Machine",/rear delts/i],
  ["split-squat-with-dumbbells","Dumbbell",/rear foot elevated/i],
  ["seated-leg-curl","Machine",/sit on the machine/i],
  ["lying-leg-curls","Machine",/lie face down/i],
  ["triceps-pushdown","Cable",/bar to a high pulley/i],
  ["triceps-pushdown-rope-attachment","Cable",/rope/i]
 ]){assert.equal(row(slug).equipment,material);assert.match(row(slug).instructions_en,words);}
});
function timer(){
 const context=vm.createContext({Date,Number,Boolean,Math,phase3State:{activeSession:{status:"active",plannedExercises:[{restSeconds:90}],focus:null}},phase3TrainingPreferences:{timer_enabled:true},phase3FocusOpen:true,
  phase3TimerId:null,phase3TimerEndsAt:0,phase3LastVibrationSecond:null,phase3SetSaving:false,phase3FinishSaving:false,
  phase3SaveLocal(){},phase3SyncActiveSession(){},phase3SyncFocusPortal(){},phase3CancelVibration(){},phase3Text:x=>x,
  window:{setInterval(){context.intervals++;return 1;},clearInterval(){}},intervals:0});
 const fn=name=>{const start=source.indexOf("  function "+name+"(");assert(start>=0,name);const end=source.indexOf("\n  function ",start+1);return source.slice(start,end);};
 for(const name of ["phase3DefaultFocusState","phase3EnsureSessionFocus","phase3SessionFromDb","phase3ApplyFocusStep","phase3StartTimer","phase3EnsureTimerRunning","phase3StopTimer","phase3FinishRestTimer","phase3SetTimerEnabled","phase3StartManualRest"])
  vm.runInContext(fn(name),context);
 context.phase3UpdateTimerText=()=>{};
 context.phase3State.activeSession.focus=context.phase3DefaultFocusState();return context;
}
test("new workout ignores legacy global timer preference; disabled saves only advance",()=>{
 const c=timer(),s=c.phase3State.activeSession;
 assert.equal(s.focus.timerEnabled,false);c.phase3StartTimer(90,{exerciseIndex:0,setIndex:2});
 assert.equal(s.focus.rest,null);assert.equal(s.focus.currentSetIndex,2);assert.equal(c.intervals,0);
});
test("open and manual start before any set, double start, off, next workout",()=>{
 const c=timer(),s=c.phase3State.activeSession;
 c.phase3SetTimerEnabled(true);assert.equal(s.focus.timerEnabled,true);assert.equal(s.focus.rest,null);
 c.phase3StartManualRest();const deadline=s.focus.rest.endsAt;
 assert.equal(s.focus.rest.manual,true);c.phase3StartManualRest();assert.equal(s.focus.rest.endsAt,deadline);assert.equal(c.intervals,1);
 c.phase3FinishRestTimer();assert.equal(s.focus.rest,null);assert.equal(s.focus.currentSetIndex,1);assert.equal(s.focus.allExercisesCompleted,false);
 c.phase3StartManualRest();c.phase3SetTimerEnabled(false);assert.equal(s.focus.rest,null);assert.equal(s.focus.timerEnabled,false);
 assert.equal(c.phase3DefaultFocusState().timerEnabled,false);
});
test("same session retains explicit choice; already-running pre-upgrade rest is retained",()=>{
 const c=timer();
 for(const focus of [{timerEnabled:true,rest:null},{timerEnabled:false,rest:null},{rest:{endsAt:Date.now()+90000}}]){
  const s={focus:JSON.parse(JSON.stringify(focus))};c.phase3EnsureSessionFocus(s);
  assert.equal(s.focus.timerEnabled,focus.timerEnabled??true);assert.deepEqual(JSON.parse(JSON.stringify(s.focus.rest)),focus.rest);
 }
});
test("mobile scope retains every offline AI, SQL, Edge, workflow and unrelated runtime source",()=>{
 const git=(...args)=>cp.execFileSync("git",args,{cwd:root,windowsHide:true,encoding:"utf8"}).trim();
 const allowed=["app.js","index.html","assets/phase3-training-engine.js","assets/training-workout-ui.js","assets/training-workout.css","assets/vendor/lucide-clock.svg"];
 const changes=[...git("diff","--name-only",baseline).split("\n"),...git("ls-files","--others","--exclude-standard").split("\n")].filter(Boolean);
 assert(changes.every(f=>allowed.includes(f)||f.startsWith("docs/")||f.startsWith("_tests/training/")),changes.join("\n"));
 assert.equal(git("diff",baseline,"--","_offline","supabase",".github",".codex","AGENTS.md","assets/phase6d-owner-settings.js","assets/training-workout-model.js"),"");
 assert.equal(git("diff",baseline,"--","docs/TRAINING_WORKOUT_EVIDENCE.json","docs/PHASE6E0_FREEZE_RECEIPT.md","docs/PHASE6E0_OWNER_DECISIONS.md","docs/PACKAGE6D_CORRECTED_FREEZE_AND_6E_OWNER_DECISIONS.md"),"");
});
test("server-hydrated active timer from prior runtime survives the new default",()=>{
 const c=timer(),rest={endsAt:Date.now()+90000,durationSeconds:90,paused:false};
 const legacy=c.phase3SessionFromDb({metadata:{focus:{rest}}},[]);
 assert.equal(legacy.focus.timerEnabled,true);assert.equal(legacy.focus.rest.endsAt,rest.endsAt);
 const off=c.phase3SessionFromDb({metadata:{focus:{timerEnabled:false,rest:null}}},[]);
 assert.equal(off.focus.timerEnabled,false);assert.equal(off.focus.rest,null);
});
module.exports={groups};
