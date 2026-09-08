const test=require("node:test"),assert=require("node:assert/strict");
const m=require("../../assets/training-workout-model.js");
const ex=(id,sets=2,group="")=>({id,key:id,exerciseId:id,targetSets:sets,targetReps:"8-10",restSeconds:60,supersetId:group,supersetRestSeconds:120});
test("blank is missing; zero RIR is real; zero RPE invalid",()=>{
 for(const v of [""," ",null,undefined])assert.equal(m.number(v),null);
 assert.equal(m.number(0),0);
 assert(m.validTargets([{reps:"8",weight:null,rir:0,rpe:null}]));
 assert(!m.validTargets([{reps:"8",weight:null,rir:null,rpe:0}]));
 assert(!m.validTargets([{reps:"10-8",weight:null,rir:null,rpe:null}]));
 assert(!m.validTargets([{reps:"8",weight:null,rir:1.5,rpe:null}]));
});
test("legacy targets become independent set rows without mutating source",()=>{
 const e=ex("a");e.targetRir="";const rows=m.targets(e);assert.equal(rows.length,2);assert.equal(rows[0].rir,null);
 rows[0].reps="5";assert.equal(rows[1].reps,"8-10");assert.equal(e.setTargets,undefined);
});
test("superset rounds rotate exercises, group rest only at round end",()=>{
 const rows=m.sequence([ex("a",2,"g"),ex("b",3,"g"),ex("c",1)]);
 assert.deepEqual(rows.map(s=>[s.exerciseIndex,s.setIndex,s.restSeconds]),[[0,1,0],[1,1,120],[0,2,0],[1,2,120],[1,3,120],[2,1,60]]);
});
test("next skips registered sets but never failed writes",()=>{
 const session={plannedExercises:[ex("a",2,"g"),ex("b",2,"g")],setLogs:{"b__1":{completedAt:"x",syncedAt:"x"}}};
 assert.equal(m.next(session,0,1).exerciseIndex,0);assert.equal(m.next(session,0,1).setIndex,2);
 session.setLogs["b__1"].syncedAt="";assert.equal(m.next(session,0,1).exerciseIndex,1);
});
test("previous performance only exact ID and completed before current workout",()=>{
 const history=[{id:"wrong",completedAt:"2026-09-03",sets:[{exercise_id:"variant",actual_weight:999}]},
 {id:"future",completedAt:"2026-09-04",sets:[{exercise_id:"a",actual_weight:900}]},
 {id:"right",completedAt:"2026-09-01",sets:[{exercise_id:"a",set_index:1,actual_weight:20}]}];
 assert.equal(m.previous(history,ex("a"),"2026-09-03")[0].actual_weight,20);
 assert.deepEqual(m.previous(history,{slug:"a"}),[]);
});
test("unit roundtrip preserves missing and explicit zero",()=>{
 assert.equal(m.storedWeight("",true),null);assert.equal(m.displayWeight(null,true),"");
 assert.equal(m.storedWeight(0,true),0);
 assert(Math.abs(m.storedWeight(m.displayWeight(20,true),true)-20)<.005);
});
