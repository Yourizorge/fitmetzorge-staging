'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const D=require('./domain.cjs'),UI=require('./presentation.cjs');
const vm=require('node:vm'),fs=require('node:fs');
const act=(s,a,data={})=>D.transition(s,{action:a,data},'member');
test('preferences are durable state but do not invalidate sources or approvals',()=>{
 let s=D.initial('B');s=act(s,'build');s=act(s,'confirm');
 const before=structuredClone(s);s=act(s,'preferences',{language:'de',theme:'dark',units:'imperial'});
 assert.deepEqual(s.review,before.review);assert.deepEqual(s.active,before.active);assert.equal(s.sourceHash,before.sourceHash);
 assert.equal(D.view(s).preferences.language,'de');assert.equal(s.revision,before.revision+1);
 assert.deepEqual(act(s,'preferences',s.preferences),s);
});
test('preferences cannot grant rights, change medical state, bypass consent or trainer role',()=>{
 let s=D.initial('A');const p={language:'nl',theme:'light',units:'metric'};
 for(const bad of [{...p,role:'trainer'},{...p,theme:'purple'},{...p,units:'x'},{}])assert.throws(()=>act(s,'preferences',bad));
 assert.throws(()=>D.transition(s,{action:'preferences',data:p},'trainer'),/actor/);
 s=act(s,'revoke');assert.throws(()=>act(s,'preferences',p),/consent/);
});
test('plan options come from eligible catalogue; excluded exercises never offered',()=>{
 let s=D.initial('B');s.pair.training.fixture.intake.excluded=['squat'];
 assert.ok(UI.options(s).training.flat().every(x=>x.choices.every(v=>v.id!=='squat')));
 s.clock=s.pair.training.fixture.catalog.expires;
 assert.equal(UI.options(s).training.length,0);assert.ok(UI.options(s).reason);
 assert.equal(UI.options(D.initial('A')).training.length,0);
});
test('planned nutrition is exact source totals, distinct from missing intake',()=>{
 const s=D.initial('B'),v=D.view(s);
 assert.deepEqual(v.plannedNutrition.totals,s.active.nutrition.total);
 assert.deepEqual(v.plannedNutrition.difference,s.active.nutrition.difference);
 assert.equal(v.foodSummary.recorded,0);assert.equal(v.progress.physical_advice_authorized,false);
});
test('changed intake invalidates review and retains previous intake and plan',()=>{
 let s=act(D.initial('B'),'build');s=act(s,'confirm');const old=structuredClone(s.active);
 const training=structuredClone(s.pair.training.fixture.intake),nutrition=structuredClone(s.pair.nutrition.fixture.intake);
 training.excluded=['squat'];nutrition.allergies={status:'missing',value:null};
 s=act(s,'intake',{training,nutrition});assert.equal(s.review,null);assert.equal(s.intakeHistory.length,2);
 assert.deepEqual(s.active,old);assert.throws(()=>act(s,'build'));assert.throws(()=>act(s,'apply'));
});
test('food substitution uses exact existing version, bounds, separate confirmation and original history',()=>{
 let s=D.initial('B'),old=structuredClone(s.active);
 s=act(s,'edit',{domain:'nutrition_item',value:{meal:0,item:0,food:'potato',foodVersion:1,grams:200}});
 assert.equal(s.review.target.nutrition.meals[0].items[0].food,'potato');assert.deepEqual(s.active,old);
 assert.throws(()=>act(s,'apply'),/approvals/);s=act(s,'confirm');s=act(s,'apply');assert.equal(s.active.version,2);
 assert.deepEqual(s.history[0].nutrition,old.nutrition);
 for(const value of [{meal:0,item:0,food:'potato',foodVersion:2,grams:200},{meal:0,item:0,food:'peanut',foodVersion:1,grams:200},{meal:0,item:0,food:'rice',foodVersion:1,grams:201}])
  assert.throws(()=>act(s,'edit',{domain:'nutrition_item',value}));
});
test('editing any session day is catalogue-bound, no silent schedule overwrite',()=>{
 const s=D.initial('B'),second=s.active.training.sessions[1].day;
 const next=act(s,'edit',{domain:'training_session',value:{session:1,day:'fri'}});
 assert.equal(next.active.training.sessions[1].day,second);assert.equal(next.review.target.training.sessions[1].day,'fri');
 assert.throws(()=>act(s,'edit',{domain:'training_session',value:{session:1,day:'sun'}}));
 assert.throws(()=>act(s,'edit',{domain:'training_session',value:{session:0,day:second}}));
});
test('intake checkbox names are stable technical fields, never translated captions',()=>{
 const context=vm.createContext({});vm.runInContext(fs.readFileSync(__dirname+'/panels.js','utf8')+'; globalThis.panels=FMZPanels;',context);
 for(const language of [0,1,2]){
  const s=D.view(D.initial('B')),html=context.panels.panel(s,{capabilities:{full_day21:false}},'intake',
   {esc:x=>String(x??''),t:x=>x,label:x=>Array.isArray(x)?x[language]:x,num:()=>'',language,views:[]});
  assert.match(html,/name="excluded" value="squat"/);assert.match(html,/name="days" value="mon"/);
  assert.match(html,/name="equipment" value="dumbbell"/);assert.doesNotMatch(html,/name="Goblet/);
 }
});
