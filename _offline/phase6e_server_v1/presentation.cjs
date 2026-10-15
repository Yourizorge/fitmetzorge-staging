'use strict';
const T=require('../../training-rules-demo/model.js');
const defaults={language:'nl',theme:'light',units:'metric'};
function preferences(value){
 if(!value||JSON.stringify(Object.keys(value).sort())!==JSON.stringify(Object.keys(defaults).sort())||
 !['nl','en','de'].includes(value.language)||!['light','dark'].includes(value.theme)||
 !['metric','imperial'].includes(value.units))throw Error('preferences');
 return structuredClone(value);
}
function options(s){
 if(s.route!=='B')return {training:[],nutrition:[],reason:'trainer_source_required'};
 try{
  const f=s.pair.training.fixture;T.catalog(f.catalog,s.clock);T.intake(f.intake,f.catalog,s.clock);
  const p=s.review?.target||s.active;
  return {training:p.training.sessions.map(w=>w.exercises.map(e=>{
   const rule=T.selectRule(f.catalog,f.intake,e.role);
   return {rule:rule.id,version:f.catalog.version,choices:T.eligible(f.catalog,f.intake,rule).map(x=>({id:x.id,name:x.label||x.id}))};
  })),nutrition:p.nutrition.meals.map(m=>m.items.map(i=>({id:i.food,version:i.foodVersion,bounds:i.bounds}))),reason:null};
 }catch(e){return {training:[],nutrition:[],reason:e.message};}
}
function nutrition(plan){
 if(!plan)return null;
 // The frozen calculator supplies exact integer milli-units; never re-estimate foods.
 return {totals:structuredClone(plan.total),goals:structuredClone(plan.target||null),difference:structuredClone(plan.difference),
  version:plan.ruleVersion,rule:plan.ruleId,meals:plan.meals.map(m=>({id:m.id,moment:m.moment,
   totals:structuredClone(m.totals),items:m.items.map(i=>({food:i.food,version:i.foodVersion,grams:i.grams}))}))};
}
function progress(s){return {planVersions:s.history.length,planVersion:s.active.version,
 registrationVersions:s.recordHistory.length,recoveryVersions:s.recoveryHistory.length,
 intakeVersions:s.intakeHistory.length,comparison:s.comparison||null,
 missingWindows:s.comparison?[]:['training','nutrition'],
 physical_advice_authorized:false,automatic_actions_allowed:false};}
module.exports={defaults,preferences,options,nutrition,progress};
