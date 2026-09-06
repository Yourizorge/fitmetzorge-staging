const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,".."),source=fs.readFileSync(path.join(root,"assets/phase3-training-engine.js"),"utf8");
const match=source.match(/  async function phase3CompleteWorkout\(\) \{[\s\S]*?\n  \}/);
assert(match,"Completion entrypoint");
const checks=[];
async function run(failFlush=false,online=true){
 const session={id:"synthetic",status:"active",planTitle:"Synthetic",setLogs:{one:{syncedAt:null}},focus:{}},events=[];
 const context={phase3State:{activeSession:session,history:[]},phase3FocusOpen:true,Date,
  phase3EnsureSessionFocus:()=>session.focus,phase3UsesSupabase:()=>online,phase3Text:k=>k,
  phase3SyncActiveSession:async()=>{events.push({type:"sync",status:session.status,setsSaved:!!session.setLogs.one.syncedAt});
   if(!online)return{ok:false,skipped:true};
   if(failFlush)return{ok:false};session.setLogs.one.syncedAt="saved";return{ok:true};},
  phase3IsoNow:()=>"2026-09-06T08:00:00Z",phase3TimestampMs:()=>0,phase3StopTimer(){},
  phase3SaveLocal(){},renderTraining(){},phase3WorkoutElapsedSeconds:()=>1200,phase3RemoveFocusPortal(){}};
 vm.createContext(context);await vm.runInContext("("+match[0]+")()",context);
 return {session,events,context};
}
(async()=>{
 let value=await run();
 assert.equal(value.events[0].status,"active");checks.push("flush happens before completion");
 assert(value.events[1].setsSaved&&value.events[1].status==="completed");checks.push("authoritative completion sees saved sets");
 assert.equal(value.context.phase3State.activeSession,null);checks.push("success retains completion lifecycle");
 value=await run(true);assert.equal(value.events.length,1);assert.equal(value.session.status,"active");checks.push("failed flush never completes workout");
 assert.equal(value.context.phase3State.history.length,0);checks.push("failed flush adds no history");
 value=await run(false,false);assert.equal(value.context.phase3State.history.length,1);checks.push("local-only completion remains local, no invented server event");
 console.log(JSON.stringify({suite:"hotfix2_workout_event_order",overall_pass:true,pass_count:checks.length,checks}));
})().catch(error=>{console.error(error);process.exitCode=1;});
