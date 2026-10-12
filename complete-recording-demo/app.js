/* No fetch, storage or real user input. All choices concern synthetic fixtures. */
(function(){'use strict';const M=FMZ21Model,R=FMZ21Review,C=FMZ21Copy,$=id=>document.getElementById(id),escape=x=>String(x).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
let m=M.create(),lang=0,scenario=null,step=0,feedback=null;
const t=k=>C.get(k,lang),reason=k=>C.reason(k,lang),val=x=>x===null?t('missing'):String(x).replace('.',lang===1?'.':','),cad=x=>t(x.option)+' '+x.at;
const btn=(id,label,disabled=false)=>'<button id="'+id+'" '+(disabled?'disabled':'')+'>'+escape(t(label))+'</button>';
function perform(a,d={},actor=$('actor').value||'member',opt){scenario=null;feedback=m.command(m.event(a,d,actor),opt);render();}
function loadRecord(){const x=m.view().records.find(x=>x.id===$('record').value);if(!x)return;for(const [id,key]of [['weight','load'],['value','reps'],['rir','rir'],['rpe','rpe']])$(id).value=x.actual[key]??'';$('load-label').textContent=x.unit.toUpperCase();}
function loadFood(){const x=m.view().records.find(x=>x.id===$('product').value);if(!x)return;$('food-state').value=x.actual.state;$('grams').value=x.actual.grams??'';foodState();$('food-source').textContent=t('catalog')+': '+x.planned.food+' v'+x.planned.foodVersion+' / '+x.recipe+' v'+x.recipeVersion+' / '+x.planned.bounds.min+'-'+x.planned.bounds.max+' g / step '+x.planned.bounds.step+' g';}
function foodState(){const state=$('food-state').value;$('grams').disabled=state!=='eaten'||!m.view().consent;if(state==='missing')$('grams').value='';if(state==='not_eaten')$('grams').value='0';}
function optionList(el,rows,label){const old=el.value;el.innerHTML=rows.map(x=>'<option value="'+escape(x.id)+'">'+escape(label(x))+'</option>').join('');if(rows.some(x=>x.id===old))el.value=old;}
function renderRecords(s){
 const ts=s.records.filter(x=>x.kind==='training'),workouts=[...new Map(ts.map(x=>[x.workout,{id:x.workout,day:x.day}])).values()];
 optionList($('workout'),workouts,x=>t(x.day)+' / '+x.id);
 const rows=ts.filter(x=>x.workout===$('workout').value);
 $('records').innerHTML=rows.map(x=>'<div class="set-row" data-id="'+x.id+'"><strong>'+escape(x.label[lang])+' / '+t('set')+' '+x.index+'</strong><div class="numbers"><span>'+t('planned')+': '+x.planned.reps.min+'-'+x.planned.reps.max+' REPS<br>'+(x.planned.load==null?t('noLoad'):x.planned.load.value+' '+x.unit)+'</span><span class="actual-line">'+t('actual')+': <b class="reps">'+val(x.actual.reps)+'</b> REPS<br><b class="load">'+val(x.actual.load)+'</b> '+x.unit+'</span></div><small>RIR <span class="rir">'+val(x.actual.rir)+'</span> / RPE <span class="rpe">'+val(x.actual.rpe)+'</span> / '+t('version')+' '+x.planVersion+' / r'+x.revision+'</small></div>').join('');
 optionList($('record'),rows,x=>x.label[lang]+' / '+t('set')+' '+x.index);loadRecord();
 const active=s.closed[$('workout').value],closure=active?s.workoutClosures.find(x=>x.id===active.id):null;
 $('workout-status').textContent=t(closure?closure.summary.complete?'closed':'partialFinish':'open');$('workout-status').dataset.closed=!!closure;
 $('workout-summary').innerHTML=closure?'<p>'+closure.summary.recorded+' / '+closure.summary.total+' '+t('setsReps')+'; '+closure.summary.weights+' / '+closure.summary.total+' '+t('setsLoad')+'</p>'+closure.summary.lines.map(x=>'<div class="summary-line">'+escape(x.label[lang])+' #'+x.index+': '+val(x.actual.reps)+' / '+x.planned.reps.min+'-'+x.planned.reps.max+' REPS. '+t(x.repsRelation)+'. '+(x.loadDelta===null?t('missingLoad'):'Delta '+x.loadDelta+' '+x.unit)+'<small>'+t('version')+' '+x.planVersion+' / r'+x.recordVersion+'</small></div>').join(''):'<p>'+t('noSummary')+'</p>';
 const foods=s.records.filter(x=>x.kind==='nutrition'),meals=[...new Map(foods.map(x=>[x.meal,{id:x.meal,moment:x.moment}])).values()];
 optionList($('meal-select'),meals,x=>x.moment+' / '+x.id);const meal=foods.filter(x=>x.meal===$('meal-select').value);
 $('food-records').innerHTML=meal.map(x=>'<div class="food-row" data-id="'+x.id+'"><b>'+escape(x.label[lang])+'</b><p>'+t('planned')+': '+x.planned.grams+' g / <span class="actual-line">'+t(x.actual.state==='missing'?'missing':x.actual.state)+(x.actual.grams===null?'':' / '+x.actual.grams+' g')+'</span></p><small>'+x.planned.food+' v'+x.planned.foodVersion+' / '+x.recipe+' v'+x.recipeVersion+' / r'+x.revision+' / '+t('version')+' '+x.planVersion+'</small></div>').join('');
 optionList($('product'),meal,x=>x.label[lang]);for(const o of $('food-state').options)o.textContent=t(o.value);loadFood();
 const f=M.foodSummary(s.records,s.active.nutrition);
 $('food-summary').dataset.count=f.recorded;$('food-summary').innerHTML='<p><b>'+f.recorded+' / '+f.total+'</b> '+t('actual')+' / '+f.notEaten+' '+t('not_eaten')+'</p><table class="nutrients"><thead><tr><th></th><th>'+t('actualShort')+'</th><th>'+t('goalShort')+'</th><th>'+t('differenceShort')+'</th></tr></thead><tbody>'+['energy','protein','carb','fat'].map(k=>'<tr><td>'+t(k)+'</td><td>'+val(f.totals===null?null:f.totals[k]/1000)+'</td><td>'+val(f.goal.totals[k]/1000)+'</td><td>'+val(f.delta===null?null:f.delta[k]/1000)+'</td></tr>').join('')+'</tbody></table><small>'+f.goal.id+' v'+f.goal.version+' / '+f.source.catalog+' v'+f.source.version+'</small>';
 $('day-status').textContent=t(s.dayClose?f.completePlan?'closed':'partialDay':'open')+' / '+t('foodLog');
}
function render(){
 const s=m.view(),p=s.proposal?.target,l=['nl','en','de'][lang];document.documentElement.lang=l;
 for(const [id,key]of Object.entries({'title':'title','demo-note':'demo','today-title':'today','route-label':'route','actor-title':'actor','training-title':'training','nutrition-title':'nutrition','records-title':'records','record-label':'actual','partial':'registrationNote','recovery-title':'recovery','proposal-title':'review','manual-title':'edit','history-title':'history','audit-title':'audit','tests-title':'tests','tests-link':'tests','limits':'limits'}))$(id).textContent=t(key);
 for(const id of ['reset','arrive','correct','complete','start','previous','next','health','resolved','revoke'])$(id).textContent=t(id);
 for(const [id,key]of Object.entries({'workout-label':'chooseWorkout','load-label':'load','self-note':'self','summary-title':'summary','reflection-note':'reflectionLimit','food-title':'foodLog','meal-label':'chooseMeal','product-label':'product','food-state-label':'foodState','food-summary-title':'foodSummary','food-scope':'scope','save':'saveSet','finish':'finish','save-food':'saveFood','finish-day':'finishDay'}))$(id).textContent=t(key);
 $('save-feedback').textContent=feedback?(feedback.ok?t('saved'):reason(feedback.reason)):'';
 $('route').value=s.route;$('actor-label').hidden=s.route==='B';const actor=$('actor').value||'member';$('actor').innerHTML='<option value="member">'+t('member')+'</option><option value="trainer">'+t('trainer')+'</option>';$('actor').value=s.route==='B'?'member':actor;
 $('binding').textContent='Alex / syn21-member / '+t('source')+' '+s.sourceRevision+' / '+t('version')+' '+s.active.version+' / '+s.link.id+' v'+s.link.version;
 const day=s.route==='B'?s.active.training.sessions[0].day:'mon',date=day==='mon'?'2026-10-05 / 18:00':(['Datum nog niet gekoppeld','Date not yet linked','Datum noch nicht verknuepft'][lang]);
 $('agenda').innerHTML='<strong>2026-10-01 / UTC</strong><p>'+t('nextTraining')+': '+t(day)+' / '+date+'</p><p>'+t('checkin')+': <b>'+cad(s.active.cadence)+'</b></p><small>'+t('oldCheckin')+': 2026-09-30 / 19:00</small><p>'+t('actual')+': '+s.records.filter(x=>x.kind==='training'?x.actual.reps!==null:x.actual.state!=='missing').length+' / '+s.records.length+'; '+t('recovery')+': '+s.recovery.rows.filter(x=>x.value!==null).length+' / 12</p><p><strong>'+t(s.status)+'</strong> / <a href="#proposal">'+t('seeProposal')+'</a></p>';
 const training=s.route==='B'?s.active.training.sessions.map(x=>'<div class="plan-item"><b>'+t(x.day)+'</b><br>'+x.exercises.map(e=>escape(FMZ16Catalog.data.exercises.find(x=>x.id===e.exercise).label[lang])+' '+e.sets+' x '+e.reps+' / '+(e.load===null?t('noLoad'):escape(JSON.stringify(e.load)))).join('<br>')+'</div>').join(''):s.active.training.exercises.map(e=>'<div class="plan-item">'+escape(e.labels[l])+' '+e.sets.length+' x '+e.sets[0].reps.min+' / '+e.sets[0].load.value+' kg</div>').join('');
 $('training-plan').innerHTML='<small>'+t('planned')+'</small>'+training;
 $('nutrition-plan').innerHTML='<small>'+t('planned')+' / '+escape(s.active.nutrition.ruleId)+' v'+s.active.nutrition.ruleVersion+'</small>'+s.active.nutrition.meals.map(x=>'<div class="plan-item"><b>'+x.moment+' '+escape(x.name[lang])+'</b><br>'+x.items.map(y=>escape(y.name[lang])+' '+y.grams+'g').join(', ')+'</div>').join('');
 renderRecords(s);
 $('recovery-records').innerHTML=s.recovery.rows.filter(x=>x.id.endsWith('-5')).map(x=>'<p>'+t(x.metric==='sleep'?'sleep':'recoveryMetric')+': <b>'+val(x.value)+'</b> / v'+x.version+' / 2026-09-30</p>').join('');
 $('completion').textContent=s.completion?t('saved')+' / '+s.completion.record+' v'+s.completion.version:t('oldCheckin');
 $('facts').innerHTML=s.facts.map(x=>'<div class="fact" data-metric="'+x.metric+'">'+t(x.metric==='sleep'?'sleep':'recoveryMetric')+': <b>'+x.previous.sum+' / 3 → '+x.current.sum+' / 3</b><p class="difference">Δ '+x.delta.numerator+' / 3</p><small>'+x.refs.map(y=>y.id+' v'+y.version).join(', ')+'</small></div>').join('');
 $('state').textContent=t(s.status);$('state').dataset.state=s.status;
 $('message').textContent=feedback&&!feedback.ok?reason(feedback.reason):reason(s.reason);
 $('notices').innerHTML=s.notices.map(n=>'<p class="signal" data-state="'+n.status+'">'+t(n.status==='superseded'?'superseded':'notice')+' / '+t('source')+' '+n.sourceRevision+'</p>').join('');
 const rule=s.proposal?.rule,ruleLabel=rule?(rule.id?rule.id+' v'+rule.version:rule.training+' v'+rule.trainingVersion+' / '+rule.nutrition+' v'+rule.nutritionVersion):'';
 $('delta').innerHTML=!p?'<p>'+t('none')+'</p>':'<p>'+t('checkin')+': '+cad(s.active.cadence)+' → '+cad(p.cadence)+'</p>'+(s.route==='B'?'<p>'+t('day')+': '+t(s.active.training.sessions[0].day)+' → '+t(p.training.sessions[0].day)+'</p><p>'+t('meal')+': '+s.active.nutrition.meals[0].moment+' → '+p.nutrition.meals[0].moment+'</p>':'')+'<small class="source">'+t('why')+': '+escape(ruleLabel)+' / '+t('source')+' '+s.proposal.sourceRevision+'</small>';
 const member=$('actor').value==='member';
 $('actions').innerHTML=(s.status==='pending'?btn('accept','accept',!member):'')+(s.status==='trainer_pending'?btn('approve','approve',member)+btn('block','block',member):'')+(['confirmed','approved'].includes(s.status)?btn('apply',s.route==='A'?'apply':'activate',!member):'')+(p?btn('reject','reject',!member):'');
 for(const id of ['accept','approve','apply','reject','block'])if($(id))$(id).onclick=()=>perform(id);
 const disabled=!s.consent||s.health||s.conflict||s.clock>=s.pair.link.expires;
 $('editors').innerHTML='<label>'+t('time')+'<select id="time"><option>08:00</option><option>20:00</option></select></label>'+btn('edit-time','edit',disabled||!member)+(s.route==='B'?'<label>'+t('day')+'<select id="day"><option value="mon">'+t('mon')+'</option><option value="fri">'+t('fri')+'</option></select></label>'+btn('edit-day','edit',disabled||!member)+'<label>'+t('meal')+'<select id="meal"><option>08:00</option><option>20:00</option></select></label>'+btn('edit-meal','edit',disabled||!member):'<p>'+t('noeditA')+'</p>')+btn('restore','restore',disabled||s.active.version<3||!member);
 $('edit-time').onclick=()=>perform('edit',{domain:'time',value:$('time').value});if($('edit-day'))$('edit-day').onclick=()=>perform('edit',{domain:'training_day',value:$('day').value});if($('edit-meal'))$('edit-meal').onclick=()=>perform('edit',{domain:'nutrition_moment',value:$('meal').value});$('restore').onclick=()=>perform('restore',{version:s.active.version-1});
 $('versions').dataset.count=s.history.length;$('versions').innerHTML=s.history.map(h=>'<div class="version">'+t('version')+' '+h.version+' / '+cad(h.cadence)+' / '+t('source')+' '+h.sourceRevision+(s.route==='B'?' / '+t(h.training.sessions[0].day)+' / '+h.nutrition.meals[0].moment:'')+(h.restores?' / restore v'+h.restores:'')+'</div>').join('');
 $('audit').innerHTML=s.audit.map(x=>'<li>'+escape(JSON.stringify(x))+'</li>').join('');
 $('record-history').innerHTML=s.recordHistory.map(x=>'<details><summary>r'+x.revision+' / plan v'+x.plan.version+' / '+t('actual')+'</summary>'+x.rows.map(y=>'<p>'+escape(y.label[lang])+' / '+(y.workout||y.meal)+' / r'+y.revision+': '+escape(JSON.stringify(y.actual))+' / '+t('version')+' '+y.planVersion+'</p>').join('')+'</details>').join('')+'<h3>'+t('closures')+'</h3>'+s.workoutClosures.map(x=>'<details><summary>'+x.summary.workout+' / '+x.id+' / '+x.summary.recorded+'/'+x.summary.total+'</summary>'+x.summary.lines.map(z=>'<p>'+escape(z.label[lang])+' #'+z.index+': '+val(z.actual.reps)+' REPS / '+val(z.actual.load)+' '+z.unit+' / plan v'+z.planVersion+'</p>').join('')+'</details>').join('')+s.dayHistory.map(x=>'<p>'+x.id+': '+x.summary.recorded+'/'+x.summary.total+' / '+val(x.summary.totals?.energy===undefined?null:x.summary.totals.energy/1000)+' kcal</p>').join('');
 for(const id of ['save','finish','save-food','finish-day','arrive','correct','complete','health','resolved'])$(id).disabled=!s.consent||s.conflict||s.clock>=s.pair.link.expires||!member;
 $('revoke').disabled=!s.consent||!member;
 $('scenario-buttons').innerHTML=R.scenarios.map((x,i)=>'<button id="test-'+x.id+'">'+(i+1)+'. '+escape(x.title[lang])+'</button>').join('');for(const x of R.scenarios)$('test-'+x.id).onclick=()=>select(x.id);
 $('review').hidden=!scenario;$('previous').disabled=step===0;$('next').disabled=step===R.scenarios.length-1;
 $('verdict').removeAttribute('data-result');$('verdict').textContent='';
 if(scenario){
  const spec=R.scenarios[step];$('step').textContent=(step+1)+' / '+R.scenarios.length;$('scenario-title').textContent=spec.title[lang];$('expectation').textContent=t('expected')+': '+reason(spec.reason);
  $('changed').textContent=t('changes')+': '+s.audit.map(x=>x.action).join(' → ')+'. '+t('source')+' '+s.sourceRevision;
  const test=R.assess(scenario),visible=$('state').dataset.state===test.status&&Number($('versions').dataset.count)===test.version&&$('message').textContent===(feedback&&!feedback.ok?reason(feedback.reason):reason(s.reason));
  const pass=test.pass&&visible&&Number($('food-summary').dataset.count)===test.food;$('verdict').dataset.result=pass?'pass':'fail';$('verdict').textContent=t(pass?'pass':'fail');
 }
}
function select(id){scenario=R.run(id);m=scenario.model;step=R.scenarios.findIndex(x=>x.id===id);feedback=scenario.last;$('actor').value='member';render();}
$('language').onchange=()=>{lang=['nl','en','de'].indexOf($('language').value);render();};
$('theme').onchange=()=>document.documentElement.dataset.theme=$('theme').value;
$('route').onchange=()=>{m=M.create(M.base($('route').value));scenario=null;feedback=null;render();};
$('actor').onchange=render;$('reset').onclick=()=>{m=M.create(M.base($('route').value));scenario=null;feedback=null;render();};
$('record').onchange=loadRecord;$('workout').onchange=render;$('meal-select').onchange=render;$('product').onchange=loadFood;$('food-state').onchange=foodState;
$('save').onclick=()=>{const x=m.view().records.find(x=>x.id===$('record').value),n=id=>$(id).value===''?null:Number($(id).value);perform('record',R.data(x,{load:n('weight'),reps:n('value'),rir:n('rir'),rpe:n('rpe')}));};
$('save-food').onclick=()=>{const x=m.view().records.find(x=>x.id===$('product').value);perform('record',R.data(x,{state:$('food-state').value,grams:$('grams').value===''?null:Number($('grams').value)}));};
$('finish').onclick=()=>perform('finish_workout',{workout:$('workout').value});$('finish-day').onclick=()=>perform('finish_day');
$('arrive').onclick=()=>{scenario=null;feedback=R.arrive(m);render();};$('correct').onclick=()=>{scenario=null;feedback=R.arrive(m,8);render();};
$('complete').onclick=()=>perform('complete');$('health').onclick=()=>perform('health',{value:'current'});$('resolved').onclick=()=>perform('health',{value:'reported_resolved'});$('revoke').onclick=()=>perform('revoke');
$('start').onclick=()=>{select('full');$('review').scrollIntoView({block:'center'});};$('previous').onclick=()=>select(R.scenarios[Math.max(0,step-1)].id);$('next').onclick=()=>select(R.scenarios[Math.min(R.scenarios.length-1,step+1)].id);
render();
})();
