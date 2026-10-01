/* Deterministic in-memory contract. No provider, storage, clinical calculation or live authority. */
(function(root){"use strict";
const C=typeof module==='object'?require('./catalog.js'):root.FMZ17Catalog,copy=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=x=>{throw Error(x);},int=Number.isSafeInteger;
const keys=['energy','protein','carb','fat'],optionalNA=['target','favorites','excluded','diet','restrictions','budget'],status=['known','not_applicable','missing'];
const exact=(x,k)=>x&&typeof x==='object'&&!Array.isArray(x)&&same(Object.keys(x).sort(),k.slice().sort()),list=(x,allowed)=>Array.isArray(x)&&new Set(x).size===x.length&&x.every(v=>allowed.includes(v));
function cell(x){if(!exact(x,['status','value'])||!status.includes(x.status)||(x.status!=='known'&&x.value!==null))fail('field_state');}
function value(i,k){cell(i[k]);if(i[k].status==='missing')fail('missing:'+k);if(i[k].status==='not_applicable'){if(!optionalNA.includes(k))fail('not_applicable:'+k);return null;}return i[k].value;}
function nutrients(x){if(!exact(x,keys)||!keys.every(k=>int(x[k])&&x[k]>=0))fail('nutrient');}
function resolve(c,x){if(typeof x!=='string')fail('identity');const q=x.toLowerCase().trim(),found=c.foods.filter(f=>f.id===q||f.aliases.includes(q));if(found.length!==1)fail('identity');return found[0].id;}
function uniqueIds(xs){if(!Array.isArray(xs)||new Set(xs.map(x=>x.id)).size!==xs.length)fail('source');}
function catalog(c,clock){
 if(!c||c.id!=='syn17-food-catalog'||!int(c.version)||c.version<1||c.synthetic_only!==true||c.validation!=='synthetic_unreviewed'||!int(c.effective)||!int(c.expires)||c.effective>clock||c.expires<=clock||!Array.isArray(c.calculationRules)||c.calculationRules.length)fail('source');
 for(const k of ['foods','recipes','rules','targets'])uniqueIds(c[k]);const aliases=new Map();
 for(const f of c.foods){if(!f.id||!int(f.version)||f.version<1||!Array.isArray(f.name)||f.name.length!==3||!f.name.every(x=>typeof x==='string'&&x.length)||!Array.isArray(f.aliases)||f.unit!=='g'||f.basis!==100||!['grain','protein','vegetable','fat'].includes(f.category)||f.review!=='synthetic_unreviewed'||!same(f.ingredients,[f.id])||!list(f.allergens,['peanut','soy','milk','gluten'])||!list(f.mayContain,['peanut','soy','milk','gluten'])||f.diet!=='plant'||!['low','standard'].includes(f.budget)||!int(f.prep)||f.prep<0)fail('food_source');nutrients(f.nutrients);
  for(const alias of new Set([f.id,...f.aliases])){if(typeof alias!=='string'||alias!==alias.toLowerCase().trim()||!alias||(aliases.has(alias)&&aliases.get(alias)!==f.id))fail('alias_conflict');aliases.set(alias,f.id);}
 }
 for(const r of c.recipes){if(!r.id||!int(r.version)||r.version<1||!Array.isArray(r.name)||r.name.length!==3||!r.name.every(x=>typeof x==='string'&&x.length)||!int(r.prep)||r.prep<0||!Array.isArray(r.items)||r.items.length!==4||new Set(r.items.map(x=>x.food)).size!==4)fail('recipe');
  r.items.forEach((x,j)=>{const f=c.foods.find(f=>f.id===x.food);if(!exact(x,['food','version'])||!f||f.version!==x.version||f.category!==['grain','protein','vegetable','fat'][j])fail('source_conflict');});
 }
 for(const r of c.rules){if(r.id!=='syn17-existing-target-rule'&& !r.id?.startsWith('syn17-'))fail('rule');if(!int(r.version)||r.version<1||!same(r.required,C.fields.filter(x=>x!=='budget'))||r.method!=='existing_target_only'||r.calculation_rule!==null||r.validation!=='synthetic_unreviewed'||r.rounding!=='exact_milli_no_rounding'||r.portionUnit!=='g'||!same(r.categories,['grain','protein','vegetable','fat'])||!list(r.excludedAllergens,['peanut','soy','milk','gluten'])||!list(r.excludedProducts,c.foods.map(f=>f.id)))fail('rule');
  for(const k of r.categories){const b=r.portions[k];if(!exact(b,['min','max','step'])||![b.min,b.max,b.step].every(int)||b.min<1||b.max<b.min||b.step<1||!list(r.substitutions[k],c.foods.filter(f=>f.category===k).map(f=>f.id))||!r.substitutions[k].length)fail('rule');}
  if(!Array.isArray(r.layouts)||!r.layouts.length||new Set(r.layouts.map(x=>x.meals)).size!==r.layouts.length)fail('rule');
  for(const l of r.layouts){if(![2,3,4].includes(l.meals)||!Array.isArray(l.distribution)||l.distribution.length!==l.meals||!l.distribution.every(x=>int(x)&&x>0)||l.distribution.reduce((a,b)=>a+b,0)!==100||!Array.isArray(l.grams)||l.grams.length!==4||!l.grams.every((v,j)=>within(v,r.portions[r.categories[j]])))fail('rule');}
  if(!Array.isArray(r.reason)||r.reason.length!==3)fail('rule');
 }
 for(const t of c.targets){if(!t.id||!int(t.version)||t.version<1||t.person!=='syn17-member'||t.source!=='synthetic-existing-record'||t.review!=='synthetic_unreviewed'||!int(t.at)||!int(t.expires)||t.expires<=t.at)fail('target_source');nutrients(t.totals);if(!exact(t.bounds,keys))fail('target_source');for(const k of keys){const b=t.bounds[k];if(!exact(b,['min','max'])||!int(b.min)||!int(b.max)||b.min<0||b.max<b.min||t.totals[k]<b.min||t.totals[k]>b.max)fail('target_source');}}
 return true;
}
function within(v,b){return int(v)&&v>=b.min&&v<=b.max&&(v-b.min)%b.step===0;}
function context(i,c,clock){
 if(!exact(i,C.fields))fail('intake');C.fields.forEach(k=>cell(i[k]));const v={};for(const k of C.fields)if(k==='budget'&&i[k].status==='missing')v[k]=null;else v[k]=value(i,k);
 if(v.consent!==true)fail('consent');if(v.health!=='none')fail('medical');if(v.eligible!==true||!int(v.age)||v.age<18)fail('audience');
 if(!['maintain','performance'].includes(v.goal)||!['nl','en','de'].includes(v.language)||!['metric','imperial'].includes(v.units)||!['low','moderate','high'].includes(v.activity)||!int(v.trainingFrequency)||v.trainingFrequency<0||v.trainingFrequency>7)fail('intake');
 for(const [k,units]of [['height',['cm','in']],['weight',['kg','lb']]]){const x=v[k];if(!exact(x,['value','unit'])||typeof x.value!=='number'||!Number.isFinite(x.value)||x.value<=0||!units.includes(x.unit))fail('unit');}
 if(![2,3,4].includes(v.meals)||!Array.isArray(v.moments)||v.moments.length<v.meals||new Set(v.moments).size!==v.moments.length||!v.moments.every(x=>typeof x==='string'&&/^([01]\d|2[0-3]):[0-5]\d$/.test(x))||!int(v.maxRecipes)||v.maxRecipes<1||v.maxRecipes>4||!int(v.prepMinutes)||v.prepMinutes<0)fail('schedule');
 if(!list(v.allergies,['peanut','soy','milk','gluten'])||!['plant','any',null].includes(v.diet)||!['low','standard',null].includes(v.budget)||!(v.restrictions===null||list(v.restrictions,['plant_only','no_cooking'])))fail('preferences');
 for(const k of ['favorites','excluded']){if(v[k]===null)v[k]=[];if(!Array.isArray(v[k]))fail('preferences');v[k]=v[k].map(x=>resolve(c,x));if(new Set(v[k]).size!==v[k].length)fail('preferences');}
 if(v.favorites.some(x=>v.excluded.includes(x)))fail('preference_conflict');
 if(c.rules.length!==1)fail(c.rules.length?'rule_conflict':'rule_missing');const rule=c.rules[0];
 const banned=[...v.excluded,...rule.excludedProducts],allergens=[...v.allergies,...rule.excludedAllergens];
 const safe=f=>!banned.includes(f.id)&&!f.ingredients.some(x=>banned.includes(x))&&!f.allergens.concat(f.mayContain).some(x=>allergens.includes(x))&&(!v.budget||v.budget!=='low'||f.budget==='low');
 if(v.favorites.some(id=>!safe(c.foods.find(f=>f.id===id))))fail('preference_conflict');
 const layout=rule.layouts.find(x=>x.meals===v.meals);if(!layout)fail('rule_missing');
 if(!v.target)fail('no_target_rule');if(!exact(v.target,['id','version']))fail('target_source');const t=c.targets.find(t=>t.id===v.target.id);
 if(!t||t.version!==v.target.version||t.person!=='syn17-member'||t.goal!==v.goal)fail('source_conflict');if(t.at>clock||t.expires<=clock)fail('expired_target');
 const foods=c.foods.filter(safe),recipes=c.recipes.filter(r=>r.items.every(x=>safe(c.foods.find(f=>f.id===x.food)))&&r.prep<=v.prepMinutes&&!(v.restrictions||[]).includes('no_cooking')).sort((a,b)=>b.items.filter(x=>v.favorites.includes(x.food)).length-a.items.filter(x=>v.favorites.includes(x.food)).length);
 if(!recipes.length)fail('no_recipe');if(v.favorites.some(id=>!recipes.some(r=>r.items.some(x=>x.food===id))))fail('preference_unavailable');
 return {v,rule,layout,target:t,foods,recipes};
}
const zero=()=>({energy:0,protein:0,carb:0,fat:0});
function amount(f,grams){const n={};for(const k of keys){const x=f.nutrients[k]*grams;if(!Number.isSafeInteger(x)||x%100)fail('rounding');n[k]=x/100;}return n;}
function sum(xs){return xs.reduce((s,x)=>{for(const k of keys){s[k]+=x[k];if(!Number.isSafeInteger(s[k]))fail('arithmetic');}return s;},zero());}
function meal(recipe,moment,ctx,c,oldItems){return {recipe:recipe.id,recipeVersion:recipe.version,moment,items:recipe.items.map((ref,j)=>({food:oldItems?.[j]?.food||ref.food,grams:oldItems?.[j]?.grams??ctx.layout.grams[j]}))};}
function calculate(raw,i,c,clock){
 const ctx=context(i,c,clock),{v,rule,layout,target}=ctx;
 if(!Array.isArray(raw)||raw.length!==v.meals||new Set(raw.map(m=>m.moment)).size!==raw.length||raw.some(m=>!v.moments.includes(m.moment)))fail('schedule');
 if(new Set(raw.map(m=>m.recipe)).size>v.maxRecipes)fail('recipe_limit');
 const meals=raw.map((m,index)=>{
  const r=ctx.recipes.find(r=>r.id===m.recipe);if(!r||r.version!==m.recipeVersion||!Array.isArray(m.items)||m.items.length!==4)fail('recipe');
  const items=m.items.map((x,j)=>{if(!exact(x,['food','grams']))fail('item');const f=ctx.foods.find(f=>f.id===x.food),category=rule.categories[j];if(!f||f.category!==category||!rule.substitutions[category].includes(x.food))fail('excluded');if(!within(x.grams,rule.portions[category]))fail('portion');
   return {food:f.id,foodVersion:f.version,name:copy(f.name),grams:x.grams,unit:'g',per100:copy(f.nutrients),nutrients:amount(f,x.grams),allergens:copy(f.allergens),mayContain:copy(f.mayContain),alternatives:ctx.foods.filter(f=>rule.substitutions[category].includes(f.id)).map(f=>({id:f.id,version:f.version})),bounds:copy(rule.portions[category])};
  });return {recipe:r.id,recipeVersion:r.version,name:copy(r.name),moment:m.moment,sharePercent:layout.distribution[index],planned:Object.fromEntries(keys.map(k=>{const n=target.totals[k]*layout.distribution[index];if(!Number.isSafeInteger(n)||n%100)fail('rounding');return [k,n/100];})),items,totals:sum(items.map(x=>x.nutrients)),alternatives:ctx.recipes.map(r=>({id:r.id,version:r.version}))};
 });
 if(v.favorites.some(id=>!meals.some(m=>m.items.some(x=>x.food===id))))fail('preference_unavailable');
 const total=sum(meals.map(m=>m.totals));for(const k of keys)if(total[k]<target.bounds[k].min||total[k]>target.bounds[k].max)fail('target_bounds');
 return {catalogId:c.id,catalogVersion:c.version,ruleId:rule.id,ruleVersion:rule.version,source:JSON.stringify(c),intake:JSON.stringify(i),target:copy(target),meals,total,difference:Object.fromEntries(keys.map(k=>[k,total[k]-target.totals[k]])),allergenHits:0,excludedHits:0,bodyWeight:copy(v.weight),height:copy(v.height),portionUnit:'g',validation:'synthetic_unreviewed'};
}
function raw(plan){return plan.meals.map(m=>({recipe:m.recipe,recipeVersion:m.recipeVersion,moment:m.moment,items:m.items.map(x=>({food:x.food,grams:x.grams}))}));}
function build(i,c,clock){catalog(c,clock);const ctx=context(i,c,clock);return calculate(Array.from({length:ctx.v.meals},(_,j)=>meal(ctx.recipes[0],ctx.v.moments[j],ctx,c)),i,c,clock);}
function validatePlan(p,i,c,clock){catalog(c,clock);if(!p||p.source!==JSON.stringify(c)||p.intake!==JSON.stringify(i)||!same(calculate(raw(p),i,c,clock),p))fail('plan_source');return true;}
function create(f){
 const input=copy(f);let seq=0,s={route:'B',person:'syn17-member',clock:input.clock,intake:copy(input.intake),catalog:copy(input.catalog),revision:1,epoch:0,version:0,status:'intake',draft:null,active:null,history:[],intakeHistory:[copy(input.intake)],audit:[],revoked:false,healthLatch:input.intake.health?.status!=='known'||input.intake.health.value!=='none',automatic_actions_allowed:false,medical_clearance:false,external_calls:0};const done=new Map(),view=()=>copy(s),binding=()=>JSON.stringify([s.epoch,s.version,s.revision,s.catalog]);
 function gate(){if(input.synthetic_only!==true||input.route!=='B'||input.person!=='syn17-member'||!int(s.clock))fail('binding');if(s.revoked||s.intake.consent?.status!=='known'||s.intake.consent.value!==true)fail('consent');if(s.healthLatch)fail('medical');catalog(s.catalog,s.clock);context(s.intake,s.catalog,s.clock);}
 const event=(action,data={})=>({id:'syn17-request-'+(++seq),person:s.person,route:'B',binding:binding(),action,data:copy(data)});
 function pending(p){validatePlan(p,s.intake,s.catalog,s.clock);s.draft=copy(p);s.status='pending';}
 function command(e,opt={}){const old=copy(s);try{
  if(input.synthetic_only!==true||input.route!=='B'||input.person!=='syn17-member'||!int(s.clock))fail('binding');
  if(!exact(e,['id','person','route','binding','action','data'])||!/^syn17-request-[\w-]+$/.test(e.id)||e.person!==s.person||e.route!=='B'||!e.data||typeof e.data!=='object')fail('binding');const fp=JSON.stringify(e);
  if(done.has(e.id)){if(done.get(e.id)!==fp)fail('duplicate_conflict');return {ok:true,reason:'idempotent',state:view()};}if(e.binding!==binding())fail('version_conflict');
  if(!['intake','source','edit','restore'].includes(e.action)&&!exact(e.data,[]))fail('payload');
  if(e.action==='revoke'){s.revoked=true;s.draft=null;s.status='blocked';}
  else if(s.revoked||s.intake.consent?.status!=='known'||s.intake.consent.value!==true)fail('consent');
  else if(e.action==='intake'){if(!exact(e.data,C.fields))fail('intake');C.fields.forEach(k=>cell(e.data[k]));s.intake=copy(e.data);s.revision++;s.intakeHistory.push(copy(e.data));s.healthLatch=s.healthLatch||e.data.health.status!=='known'||e.data.health.value!=='none';s.draft=null;s.status='reassess';}
  else if(e.action==='source'){catalog(e.data,s.clock);if(e.data.version<=s.catalog.version)fail('source_conflict');s.catalog=copy(e.data);s.draft=null;s.status='reassess';}
  else if(e.action==='reject'){if(!['pending','confirmed'].includes(s.status))fail('status');s.status='rejected';}
  else{gate();
   if(e.action==='build')pending(build(s.intake,s.catalog,s.clock));
   else if(e.action==='edit'){
    if(!['pending','confirmed'].includes(s.status))fail('status');const ms=raw(s.draft),d=e.data,ctx=context(s.intake,s.catalog,s.clock);if(!int(d.meal)||!ms[d.meal])fail('payload');
    if(d.kind==='moment'&&exact(d,['kind','meal','moment']))ms[d.meal].moment=d.moment;
    else if(d.kind==='recipe'&&exact(d,['kind','meal','recipe'])){const r=ctx.recipes.find(x=>x.id===d.recipe);if(!r)fail('recipe');ms[d.meal]=meal(r,ms[d.meal].moment,ctx,s.catalog);}
    else if(d.kind==='item'&&exact(d,['kind','meal','index','food','grams'])&&int(d.index)&&ms[d.meal].items[d.index])ms[d.meal].items[d.index]={food:d.food,grams:d.grams};else fail('payload');
    pending(calculate(ms,s.intake,s.catalog,s.clock));
   }else if(e.action==='confirm'){if(s.status==='confirmed')return {ok:true,reason:'idempotent',state:view()};if(s.status!=='pending')fail('status');validatePlan(s.draft,s.intake,s.catalog,s.clock);s.status='confirmed';}
   else if(e.action==='activate'){if(s.status!=='confirmed')fail('version_conflict');validatePlan(s.draft,s.intake,s.catalog,s.clock);s.version++;s.active={version:s.version,plan:copy(s.draft),intake:copy(s.intake),catalog:copy(s.catalog),at:s.clock};s.history.push(copy(s.active));s.status='active';}
   else if(e.action==='restore'){if(!exact(e.data,['version'])||!s.active||e.data.version===s.version)fail('version_conflict');const h=s.history.find(x=>x.version===e.data.version);if(!h)fail('version_conflict');pending(h.plan);}else fail('action');
  }
  if(opt.fault_before_commit)fail('atomic_fault');s.epoch++;s.clock+=1000;s.audit.push({id:e.id,action:e.action,from:old.version,to:s.version,revision:s.revision,catalog:s.catalog.version,status:s.status,at:s.clock});done.set(e.id,fp);return {ok:true,reason:'success',state:view()};
 }catch(err){s=old;return {ok:false,reason:err.message,state:view()};}}
 return Object.freeze({view,event,command});
}
const api={create,catalog,context,build,validatePlan,calculate,raw,resolve,amount,sum,keys,within,copy};if(typeof module==='object')module.exports=api;else root.FMZ17Model=api;
})(globalThis);
