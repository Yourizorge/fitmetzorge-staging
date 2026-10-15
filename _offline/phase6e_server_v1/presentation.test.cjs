'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const D=require('./domain.cjs'),UI=require('./presentation.cjs');
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
