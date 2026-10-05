/* No fetch, storage or real user input. All choices concern synthetic fixtures. */
(function(){'use strict';const M=FMZ20Model,R=FMZ20Review,C=FMZ20Copy,$=id=>document.getElementById(id),escape=x=>String(x).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
let m=M.create(),lang=0,scenario=null,step=0,feedback=null;
const t=k=>C.get(k,lang),reason=k=>C.reason(k,lang),val=x=>x===null?t('missing'):String(x),cad=x=>t(x.option)+' '+x.at;
const btn=(id,label,disabled=false)=>'<button id="'+id+'" '+(disabled?'disabled':'')+'>'+escape(t(label))+'</button>';
function perform(a,d={},actor=$('actor').value||'member',opt){scenario=null;feedback=m.command(m.event(a,d,actor),opt);render();}
function loadRecord(){const x=m.view().records.find(x=>x.id===$('record').value);if(!x)return;$('value').value=x.value??'';$('rir').value=x.actualRir??'';$('rpe').value=x.actualRpe??'';$('rir').disabled=$('rpe').disabled=x.kind!=='training'||!m.view().consent;}
function render(){
 const s=m.view(),p=s.proposal?.target,l=['nl','en','de'][lang];document.documentElement.lang=l;
 for(const [id,key]of Object.entries({'title':'title','demo-note':'demo','today-title':'today','route-label':'route','actor-title':'actor','training-title':'training','nutrition-title':'nutrition','records-title':'actual','record-label':'actual','actual-label':'actual','partial':'partial','recovery-title':'recovery','proposal-title':'review','manual-title':'edit','history-title':'history','audit-title':'audit','tests-title':'tests','limits':'limits'}))$(id).textContent=t(key);
 for(const id of ['reset','arrive','correct','complete','save','start','previous','next','health','resolved','revoke'])$(id).textContent=t(id);
 $('route').value=s.route;$('actor-label').hidden=s.route==='B';const actor=$('actor').value||'member';$('actor').innerHTML='<option value="member">'+t('member')+'</option><option value="trainer">'+t('trainer')+'</option>';$('actor').value=s.route==='B'?'member':actor;
 $('binding').textContent='Alex / syn20-member / '+t('source')+' '+s.sourceRevision+' / '+t('version')+' '+s.active.version+' / '+s.link.id+' v'+s.link.version;
 const day=s.route==='B'?s.active.training.sessions[0].day:'mon',date=day==='mon'?'2026-10-05 / 18:00':(['Datum nog niet gekoppeld','Date not yet linked','Datum noch nicht verknuepft'][lang]);
 $('agenda').innerHTML='<strong>2026-10-01 / UTC</strong><p>'+t('nextTraining')+': '+t(day)+' / '+date+'</p><p>'+t('checkin')+': <b>'+cad(s.active.cadence)+'</b></p><small>'+t('oldCheckin')+': 2026-09-30 / 19:00</small><p>'+t('actual')+': '+s.records.filter(x=>x.value!==null).length+' / '+s.records.length+'; '+t('recovery')+': '+s.recovery.rows.filter(x=>x.value!==null).length+' / 12</p><p><strong>'+t(s.status)+'</strong> / <a href="#proposal">'+t('seeProposal')+'</a></p>';
 const training=s.route==='B'?s.active.training.sessions.map(x=>'<div class="plan-item"><b>'+t(x.day)+'</b><br>'+x.exercises.map(e=>escape(FMZ16Catalog.data.exercises.find(x=>x.id===e.exercise).label[lang])+' '+e.sets+' x '+e.reps+' / '+(e.load===null?t('noLoad'):escape(JSON.stringify(e.load)))).join('<br>')+'</div>').join(''):s.active.training.exercises.map(e=>'<div class="plan-item">'+escape(e.labels[l])+' '+e.sets.length+' x '+e.sets[0].reps.min+' / '+e.sets[0].load.value+' kg</div>').join('');
 $('training-plan').innerHTML='<small>'+t('planned')+'</small>'+training;
 $('nutrition-plan').innerHTML='<small>'+t('planned')+' / '+escape(s.active.nutrition.ruleId)+' v'+s.active.nutrition.ruleVersion+'</small>'+s.active.nutrition.meals.map(x=>'<div class="plan-item"><b>'+x.moment+' '+escape(x.name[lang])+'</b><br>'+x.items.map(y=>escape(y.name[lang])+' '+y.grams+'g').join(', ')+'</div>').join('');
 $('records').innerHTML='<div class="record head"><span>'+t('training')+' / '+t('nutrition')+'</span><span>'+t('planned')+'</span><span>'+t('actual')+'</span></div>'+s.records.map(x=>'<div class="record" data-id="'+x.id+'"><strong>'+escape(x.label)+'</strong><span>'+x.planned+' '+x.unit+'</span><span class="actual">'+val(x.value)+'</span><small>v'+x.revision+' / '+t('version')+' '+x.planVersion+' / RIR '+val(x.actualRir)+' / RPE '+val(x.actualRpe)+(x.value!==null?' / '+t('saved'):'')+'</small></div>').join('');
 const sel=$('record').value;$('record').innerHTML=s.records.map(x=>'<option value="'+x.id+'">'+escape(x.label)+' ('+x.unit+')</option>').join('');if(s.records.some(x=>x.id===sel))$('record').value=sel;loadRecord();
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
 $('record-history').innerHTML=s.recordHistory.map(x=>'<details><summary>r'+x.revision+' / plan v'+x.plan.version+' / '+x.rows.filter(y=>y.value!==null).length+' '+t('actual')+'</summary>'+x.rows.map(y=>'<p>'+escape(y.label)+' v'+y.revision+': '+y.planned+' '+y.unit+' / '+val(y.value)+' / RIR '+val(y.actualRir)+' / RPE '+val(y.actualRpe)+'</p>').join('')+'</details>').join('')+'<details><summary>'+t('recovery')+' / '+t('history')+'</summary>'+s.recoveryHistory.map(xs=>'<p>'+xs.filter(x=>x.id.endsWith('-5')).map(x=>x.metric+' v'+x.version+': '+val(x.value)).join(' / ')+'</p>').join('')+'</details>';
 for(const id of ['save','arrive','correct','complete','health','resolved'])$(id).disabled=!s.consent||s.conflict||s.clock>=s.pair.link.expires||!member;
 $('revoke').disabled=!s.consent||!member;
 $('scenario-buttons').innerHTML=R.scenarios.map((x,i)=>'<button id="test-'+x.id+'">'+(i+1)+'. '+escape(x.title[lang])+'</button>').join('');for(const x of R.scenarios)$('test-'+x.id).onclick=()=>select(x.id);
 $('review').hidden=!scenario;$('previous').disabled=step===0;$('next').disabled=step===R.scenarios.length-1;
 $('verdict').removeAttribute('data-result');$('verdict').textContent='';
 if(scenario){
  const spec=R.scenarios[step];$('step').textContent=(step+1)+' / '+R.scenarios.length;$('scenario-title').textContent=spec.title[lang];$('expectation').textContent=t('expected')+': '+reason(spec.reason);
  $('changed').textContent=t('changes')+': '+s.audit.map(x=>x.action).join(' → ')+'. '+t('source')+' '+s.sourceRevision;
  const test=R.assess(scenario),visible=$('state').dataset.state===test.status&&Number($('versions').dataset.count)===test.version&&$('message').textContent===(feedback&&!feedback.ok?reason(feedback.reason):reason(s.reason));
  const pass=test.pass&&visible;$('verdict').dataset.result=pass?'pass':'fail';$('verdict').textContent=t(pass?'pass':'fail');
 }
}
function select(id){scenario=R.run(id);m=scenario.model;step=R.scenarios.findIndex(x=>x.id===id);feedback=scenario.last;$('actor').value='member';render();}
$('language').onchange=()=>{lang=['nl','en','de'].indexOf($('language').value);render();};
$('theme').onchange=()=>document.documentElement.dataset.theme=$('theme').value;
$('route').onchange=()=>{m=M.create(M.base($('route').value));scenario=null;feedback=null;render();};
$('actor').onchange=render;$('reset').onclick=()=>{m=M.create(M.base($('route').value));scenario=null;feedback=null;render();};
$('record').onchange=loadRecord;
$('save').onclick=()=>{const x=m.view().records.find(x=>x.id===$('record').value),n=id=>$(id).value===''?null:Number($(id).value);perform('record',{id:x.id,version:x.revision,planVersion:x.planVersion,unit:x.unit,value:n('value'),rir:n('rir'),rpe:n('rpe')});};
$('arrive').onclick=()=>{scenario=null;feedback=R.arrive(m);render();};$('correct').onclick=()=>{scenario=null;feedback=R.arrive(m,8);render();};
$('complete').onclick=()=>perform('complete');$('health').onclick=()=>perform('health',{value:'current'});$('resolved').onclick=()=>perform('health',{value:'reported_resolved'});$('revoke').onclick=()=>perform('revoke');
$('start').onclick=()=>{select('today');$('review').scrollIntoView({block:'center'});};$('previous').onclick=()=>select(R.scenarios[Math.max(0,step-1)].id);$('next').onclick=()=>select(R.scenarios[Math.min(R.scenarios.length-1,step+1)].id);
render();
})();
