"use strict";
const M=FMZ18Model,F=FMZ18Fixtures,R=FMZ18Review,L=FMZ18Copy,$=id=>document.getElementById(id);
let lang=0,index=-1,review=null,model=M.create(F.base),last=null,replay=null;
const text=(id,value)=>$(id).textContent=value,t=k=>L.get(k,lang),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function button(id,key,disabled=false){return '<button id="'+id+'"'+(disabled?' disabled':'')+'>'+esc(t(key))+'</button>';}
function choose(i){index=i;review=R.run(R.scenarios[i].id);model=review.model;last=review.events.at(-1);replay=null;render();$('review').scrollIntoView({block:'start'});}
function dispatch(action,data={}){review=null;const event=model.event(action,data);last=model.command(event);if(action==='activate'&&last.ok)replay=event;render();}
function plan(p,prefix){
 if(!p)return '<p class="empty">'+esc(t('none'))+'</p>';
 const tr=p.training,nu=p.nutrition;
 let html='<h4>'+esc(t('training'))+'</h4><p class="source-id">'+esc(tr.catalogId)+' / v'+tr.catalogVersion+' / '+esc(t(tr.goal))+'</p>';
 for(const s of tr.sessions){html+='<div class="exercise"><strong>'+esc(t(s.day))+'</strong><p>'+s.seconds+' sec / '+tr.budget+' sec</p>';
 for(const e of s.exercises){const label=FMZ16Catalog.data.exercises.find(x=>x.id===e.exercise)?.label[lang]||e.exercise;html+='<p>'+esc(label)+' &middot; '+e.sets+' &times; '+e.reps+' &middot; '+e.rest+' '+esc(t('rest'))+'</p><p>RIR '+(e.rir??esc(t('empty')))+' / RPE '+(e.rpe??esc(t('empty')))+' / '+esc(t('load'))+': '+esc(t('none'))+'</p>';
 if(e.history)html+='<p>'+esc(t('history'))+': '+esc(e.history.weight.value)+' '+esc(e.history.weight.unit)+', RIR '+(e.history.rir??esc(t('empty')))+', RPE '+(e.history.rpe??esc(t('empty')))+'</p>';}html+='</div>';}
 html+='<h4>'+esc(t('nutrition'))+'</h4><p class="source-id">'+esc(nu.catalogId)+' / v'+nu.catalogVersion+'</p><p>'+esc(t('unit'))+': '+nu.bodyWeight.value+' '+esc(nu.bodyWeight.unit)+'</p><table><thead><tr><th></th><th>'+esc(t('target'))+'</th><th>'+esc(t('actual'))+'</th><th>'+esc(t('difference'))+'</th></tr></thead><tbody>';
 for(const k of ['energy','protein','carb','fat'])html+='<tr><th>'+esc(t(k))+'</th><td>'+nu.target.totals[k]/1000+'</td><td id="'+prefix+'-'+k+'">'+nu.total[k]/1000+'</td><td>'+nu.difference[k]/1000+'</td></tr>';
 html+='</tbody></table>';
 for(const meal of nu.meals){html+='<div class="meal"><strong>'+esc(meal.moment)+' &middot; '+esc(meal.name[lang])+'</strong><ul>';for(const item of meal.items)html+='<li>'+item.grams+' g '+esc(item.name[lang])+'</li>';html+='</ul><p>'+meal.totals.energy/1000+' kcal</p></div>';}return html;
}
function expectedPlans(s){const d=document.createElement("div");d.innerHTML='<article><h3>'+esc(t("current"))+(s.active?" "+s.active.version:"")+'</h3>'+plan(s.active,"current")+'</article><article><h3>'+esc(t("proposal"))+'</h3>'+plan(s.draft,"proposal")+'</article>';return d.innerHTML;}
function renderReview(){
 const s=model.view(),spec=review?.spec;text('scenario-title',spec?spec.title[lang]:t('neutral'));
 text('step',index<0?'6E-18':t('step')+' '+(index+1)+' '+t('of')+' '+R.scenarios.length);
 $('previous').disabled=index<=0;$('next').disabled=index>=R.scenarios.length-1;
 $('verdict').removeAttribute('data-result');
 if(!review){text('verdict',t('neutral'));$('review-details').innerHTML='';return;}
 const check=R.assess(review,s),p=s.draft||s.active,actualNode=$('proposal-energy')||$('current-energy');
 const visible=(!p||actualNode?.textContent===String(p.nutrition.total.energy/1000))&&$('versions').dataset.count===String(s.history.length)&&$('status').dataset.status===s.status&&$('plans').innerHTML===expectedPlans(s);
 const pass=check.pass&&visible;
 text('verdict',t(pass?'pass':'fail'));$('verdict').dataset.result=pass?'pass':'fail';
 const expectation=['pending','active','confirmed'].includes(spec.status)?t('allowed'):t('blocked');
 $('review-details').innerHTML='<dt>'+esc(t('changed'))+'</dt><dd>'+esc(spec.changed[lang])+'</dd><dt>'+esc(t('expected'))+'</dt><dd>'+esc(expectation)+'</dd><dt>'+esc(t('result'))+'</dt><dd>'+esc(L.reason(check.reason,lang))+'</dd>';
}
function render(){
 const s=model.view();document.documentElement.lang=['nl','en','de'][lang];
 for(const [id,key]of Object.entries({title:'title',subtitle:'subtitle',notice:'notice','tests-title':'tests',start:'start',previous:'previous',next:'next','source-title':'source','proposal-title':'proposal','history-title':'history','audit-title':'audit','source-change':'change',revoke:'revoke',reset:'reset','no-prediction':'noPrediction'}))text(id,t(key));
 $('theme').options[0].text=['Licht','Light','Hell'][lang];$('theme').options[1].text=['Donker','Dark','Dunkel'][lang];
 $('scenario-buttons').innerHTML=R.scenarios.map((x,i)=>'<button id="test-'+x.id+'" aria-pressed="'+(i===index)+'"><b>'+String(i+1).padStart(2,'0')+'</b><span>'+esc(x.title[lang])+'</span></button>').join('');
 R.scenarios.forEach((x,i)=>$('test-'+x.id).onclick=()=>choose(i));
 text('source-caption',t('mapping')+': syn18-member = syn16-member + syn17-member. '+t('version')+' '+s.sources.link.version);
 $('sources').innerHTML=['training','nutrition'].map(k=>{const a=s.sources[k],f=a.fixture;return '<div class="source-row"><strong>'+esc(t(k))+' / '+esc(f.person)+'</strong><span>'+esc(t('revision'))+' '+a.revision+' / '+esc(t('version'))+' '+f.catalog.version+'</span><span>'+esc(t('goal'))+': '+esc(k==='training'?f.intake.goal:f.intake.goal.value)+' / '+esc(t('frequency'))+': '+esc(k==='training'?f.intake.frequency:f.intake.trainingFrequency.value)+'</span></div>';}).join('');
 text('status',t(s.status));$('status').dataset.status=s.status;text('message',last?L.reason(last.reason,lang):t('noPrediction'));
 $('controls').innerHTML=button('build','build',s.revoked)+(s.status==='pending'?button('confirm','confirm'):'')+(s.status==='confirmed'?button('activate','activate'):'')+(['pending','confirmed'].includes(s.status)?button('reject','reject'):'')+(s.version>=2?button('restore','restore',s.revoked):'')+(replay?button('duplicate','duplicate',s.revoked):'');
 for(const a of ['build','confirm','activate','reject'])if($(a))$(a).onclick=()=>dispatch(a);
 if($('restore'))$('restore').onclick=()=>dispatch('restore',{version:1});
 if($('duplicate'))$('duplicate').onclick=()=>{review=null;last=model.command(replay);render();};
 $('plans').innerHTML='<article><h3>'+esc(t('current'))+(s.active?' '+s.active.version:'')+'</h3>'+plan(s.active,'current')+'</article><article><h3>'+esc(t('proposal'))+'</h3>'+plan(s.draft,'proposal')+'</article>';
 $('editors').innerHTML='';
 if(s.draft&&['pending','confirmed'].includes(s.status)){
  for(const [domain,key,values,current]of [['training_day','day',s.sources.training.fixture.intake.days,s.draft.training.sessions[0].day],['nutrition_moment','moment',s.sources.nutrition.fixture.intake.moments.value,s.draft.nutrition.meals[0].moment]]){
   $('editors').innerHTML+='<div class="edit-row"><label>'+esc(t(key))+'<select id="edit-'+domain+'">'+values.map(v=>'<option'+(v===current?' selected':'')+'>'+esc(v)+'</option>').join('')+'</select></label>'+button('save-'+domain,'save')+'</div>';
  }
  for(const domain of ['training_day','nutrition_moment']){$('save-'+domain).onclick=()=>dispatch('edit',{domain,value:$('edit-'+domain).value});$('edit-'+domain).onchange=()=>{review=null;renderReview();};}
 }
 $('versions').dataset.count=String(s.history.length);$('versions').innerHTML=s.history.map(h=>'<div class="version">'+esc(t('version'))+' '+h.version+' &middot; '+esc(h.training.sessions[0].day)+' &middot; '+h.nutrition.meals[0].moment+' &middot; '+esc(t('source'))+' '+h.source.revision+(h.restores?' / restore '+h.restores:'')+'</div>').join('')||esc(t('none'));
 $('audit').innerHTML=s.audit.map(a=>'<li>'+esc(a.action)+' / '+a.from+' &rarr; '+a.to+' / source '+a.source+' / '+esc(new Date(a.at).toISOString())+' / '+esc(a.request)+'</li>').join('');
 $('revoke').disabled=s.revoked;$('source-change').disabled=s.revoked;renderReview();
}
$('start').onclick=()=>choose(0);$('previous').onclick=()=>choose(Math.max(0,index-1));$('next').onclick=()=>choose(Math.min(R.scenarios.length-1,index+1));
$('language').onchange=()=>{lang=['nl','en','de'].indexOf($('language').value);render();};$('theme').onchange=()=>document.body.classList.toggle('dark',$('theme').value==='dark');
$('reset').onclick=()=>{index=-1;review=null;model=M.create(F.base);last=null;replay=null;render();};
$('revoke').onclick=()=>dispatch('revoke');$('source-change').onclick=()=>{const f=model.view().sources;f.revision++;f.training.revision++;f.training.fixture.intake.minutes=f.training.fixture.intake.minutes===30?45:30;dispatch('sources',f);};
render();
