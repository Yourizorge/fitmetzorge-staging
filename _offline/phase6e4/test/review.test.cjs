"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),{setup,run,clone,engine}=require("./fixtures.cjs");
for(const [locale,text]of [
  ["en","I am reviewing my workout log but my fingers tingle"],
  ["en","I am reviewing my workout log and flurbel"],
  ["nl","Ik bekijk mijn trainingsregistratie en flurbel workout"],
  ["de","Ich sehe mir mein Trainingsprotokoll an und flurbel Training"]
])test("unconsumed review context never becomes a candidate "+locale+" "+text,()=>{
  const r=run({locale,text});assert.equal(r.status,"clarification");assert.equal(r.candidate,null);assert.equal(r.warnings.length,0);
  assert(r.nonclinical_options.some(o=>o.choices.includes("continue_chat")));
});
for(const text of ["Ich m\u00f6chte mein Trainingsprotokoll ansehen","Ich pr\u00fcfe meine Trainingsaufzeichnungen"])test("natural German orthography "+text,()=>{
  assert.equal(run({locale:"de",text}).status,"candidate_only");
});
test("one selected option containing kg and lb is explicitly refused without conversion",()=>{
  const f=setup(),s=f.request.sources,second=clone(s.plan.options[0].exercises[0].sets[0]);
  second.index=2;second.load={value:121.25,unit:"lb"};s.plan.options[0].exercises[0].sets.push(second);
  const limit=clone(s.limits.rules[0]);limit.id="syn-rule-2";limit.set_index=2;limit.load={min:110,max:130,unit:"lb"};s.limits.rules.push(limit);
  const r=engine.suggest(f.request,f.context,f.authority);assert.equal(r.reason,"mixed_units");assert.equal(r.candidate,null);
});
test("a historical goal-link cannot be added after plan capture",()=>{
  const f=setup();f.request.sources.plan.captured_at_ms=f.clock-1000;
  assert.equal(engine.suggest(f.request,f.context,f.authority).reason,"goal_link_unavailable");
});
for(const value of [NaN,Infinity,undefined])test("invalid numeric payload "+value,()=>{
  const f=setup();f.request.sources.plan.options[0].exercises[0].sets[0].load.value=value;
  assert.equal(engine.suggest(f.request,f.context,f.authority).status,"invalid_input");
});
test("multiple options with explicit selection never choose the highest weight",()=>{
  const f=setup(),s=f.request.sources,other=clone(s.plan.options[0]);other.id="syn-option-b";other.workout_id="syn-workout-b";
  other.exercises[0].sets[0].load.value=999;s.plan.options.push(other);
  const r=engine.suggest(f.request,f.context,f.authority);assert.equal(r.candidate.option_id,"syn-option-a");assert.equal(r.candidate.rows[0].target.load.value,55);
});
test("wrong set value cannot contaminate a previous returned candidate",()=>{
  const f=setup(),r=engine.suggest(f.request,f.context,f.authority);f.request.sources.plan.options[0].exercises[0].sets[0].rir=null;
  assert.equal(r.candidate.rows[0].target.rir,0);assert.equal(engine.suggest(f.request,f.context,f.authority).candidate.rows[0].target.rir,null);
});
