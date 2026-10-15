'use strict';
const FMZPanels=(()=>{
const words={progress:['Voortgang','Progress','Fortschritt'],settings:['Instellingen','Settings','Einstellungen'],
 historical:['Historische workout registreren','Record historical workout','Historisches Training erfassen'],
 historicalNote:['Afzonderlijke oorspronkelijke sessiesnapshot; geen uitvoering van het huidige plan.','Separate original session snapshot, not execution of the current plan.','Separater ursprünglicher Sitzungssnapshot, keine Ausführung des aktuellen Plans.'],
 preferences:['Persoonlijke voorkeuren','Personal preferences','Persönliche Vorlieben'],exercise:['Oefening','Exercise','Übung'],
 favorites:['Graag doen','Preferred exercises','Bevorzugte Übungen'],excluded:['Niet doen','Excluded exercises','Ausgeschlossene Übungen'],
 equipment:['Beschikbaar materiaal','Available equipment','Verfügbare Geräte'],frequency:['Trainingen per week','Workouts per week','Trainings pro Woche'],
 allergies:['Allergieën','Allergies','Allergien'],known:['Expliciet bekend','Explicitly known','Ausdrücklich bekannt'],unknown:['Onbekend','Unknown','Unbekannt'],
 language:['Taal','Language','Sprache'],theme:['Thema','Theme','Design'],units:['Eenhedenweergave','Unit display','Einheitenanzeige'],
 metric:['Metrisch','Metric','Metrisch'],imperial:['Imperiaal','Imperial','Imperial'],
 sourceUnits:['Bron- en invoereenheden blijven ongewijzigd.','Source and input units remain unchanged.','Quell- und Eingabeeinheiten bleiben unverändert.'],
 noRule:['Geen passende actuele bronregel. Het bestaande plan is bewaard; er is geen nieuw voorstel.','No matching current source rule. The existing plan is preserved; there is no new proposal.','Keine passende aktuelle Quellregel. Der bestehende Plan bleibt erhalten; kein neuer Vorschlag.'],
 missingWindow:['Nog geen complete vergelijkbare registratiereeks.','No complete comparable record series yet.','Noch keine vollständige vergleichbare Eintragsreihe.'],
 plannedTotal:['Gepland totaal, geen gegeten hoeveelheid','Planned total, not consumed amount','Geplante Summe, keine verzehrte Menge'],
 uncertain:['Opslag nog niet bevestigd. Controleer dezelfde aanvraag; maak geen tweede wijziging.','Save not confirmed. Check the same request; do not create a second change.','Speicherung nicht bestätigt. Dieselbe Anfrage prüfen; keine zweite Änderung erstellen.'],
 retry:['Dezelfde aanvraag controleren','Check same request','Dieselbe Anfrage prüfen'],
 savedReadFailed:['Opgeslagen; het bijgewerkte overzicht kon niet worden geladen.','Saved; the updated overview could not be loaded.','Gespeichert; die aktualisierte Übersicht konnte nicht geladen werden.']};
function panel(s,current,tab,h){
 const {esc,t,label,num,language,views}=h,w=k=>words[k]?.[language]||t(k),p=s.review?.target||s.active;
 const totals=v=>v?Object.entries(v).map(([k,n])=>`${esc(k)}: ${n/1000} ${k==='energy'?'kcal':'g'}`).join(' · '):t('missing');
 const select=(name,values,value)=>`<label>${w(name)}<select name="${name}">${values.map(([id,name])=>`<option value="${esc(id)}" ${id===value?'selected':''}>${esc(label(name))}</option>`).join('')}</select></label>`;
 const checks=(name,values,selected)=>`<fieldset><legend>${w(name)}</legend>${values.map(([id,name])=>`<label class="check"><input type="checkbox" name="${name}" value="${esc(id)}" ${selected.includes(id)?'checked':''}>${esc(label(name))}</label>`).join('')}</fieldset>`;
 if(tab==='training'&&!current.capabilities.full_day21){
  let html=`<h2>${t('planned')}</h2>`;
  for(const [si,session] of p.training.sessions.entries()){
   html+=`<section><h3>${esc(session.day)}</h3>`;
   for(const [ei,e] of session.exercises.entries()){
    const opt=s.editorOptions.training[si]?.[ei];
    html+=`<article><p>${esc(label(e.label||e.exercise))} · ${e.sets} × ${e.reps} · ${e.load??t('missing')} ${esc(e.requestedUnit||'')} · ${e.rest} s</p><p class="small">${esc(e.rule)} v${e.ruleVersion}</p>`;
    if(s.route==='B'&&opt)html+=`<form data-exercise="${si}:${ei}">${select('exercise',opt.choices.map(x=>[x.id,x.name]),e.exercise)}<div class="fields">${num('sets',e.sets,'min="1" step="1"')}${num('reps',e.reps,'min="1" step="1"')}${num('rest',e.rest,'min="0" step="1"')}${num('rir',e.rir,'min="0" max="10" step="1"')}${num('rpe',e.rpe,'min="1" max="10" step="0.5"')}</div><button>${t('review')}</button></form>`;
    html+='</article>';
   }
   html+='</section>';
  }
  if(s.editorOptions.reason&&s.route==='B')html+=`<p class="warning">${w('noRule')}</p>`;
  for(const v of views.filter(v=>v.capabilities.registration12))html+=`<section><h2>${w('historical')}</h2><p>${w('historicalNote')}</p><button data-workspace="${esc(v.workspace)}">${w('historical')}</button></section>`;
  return html;
 }
 if(tab==='nutrition'&&!current.capabilities.full_day21){
  const n=p.nutrition;if(!n)return `<p>${t('missing')}</p>`;
  return `<h2>${w('plannedTotal')}</h2><p>${totals(n.total)}</p><p>Δ ${totals(n.difference)}</p><p class="small">${esc(n.ruleId)} v${n.ruleVersion} · ${t('note')}</p>`+n.meals.map((m,mi)=>`<section><h2>${esc(m.moment)} · ${esc(label(m.name))}</h2><p>${totals(m.totals)}</p>${m.items.map((i,ii)=>`<article><h3>${esc(label(i.name))}</h3><p>${i.grams} g · ${esc(i.food)} v${i.foodVersion}</p><p>${totals(i.nutrients)}</p>${s.route==='B'?`<form data-portion="${mi}:${ii}"><div class="row">${num('grams',i.grams,`min="${i.bounds.min}" max="${i.bounds.max}" step="${i.bounds.step}"`)}<button>${t('review')}</button></div></form>`:''}</article>`).join('')}</section>`).join('');
 }
 if(tab==='intake'&&s.route==='B'){
  const f=s.pair.training.fixture,i=f.intake,n=s.pair.nutrition.fixture.intake;
  const choices=f.catalog.exercises.map(e=>[e.id,e.label]);
  return `<form id="intake-form"><h2>${w('preferences')}</h2><div class="form-grid">${select('goal',['fitness','strength','muscle'].map(x=>[x,x]),i.goal)}${select('experience',['beginner','experienced'].map(x=>[x,x]),i.experience)}${num('minutes',i.minutes,'min="0" step="1"')}${num('frequency',i.frequency,'min="1" step="1"')}</div>${checks('days',['mon','tue','wed','thu','fri','sat','sun'].map(x=>[x,x]),i.days)}${checks('equipment',[...new Set(f.catalog.exercises.map(x=>x.equipment))].map(x=>[x,x]),i.equipment)}${checks('favorites',choices,i.favorites)}${checks('excluded',choices,i.excluded)}<div class="row"><label class="check"><input type="checkbox" name="rir" ${i.rir?'checked':''}>RIR</label><label class="check"><input type="checkbox" name="rpe" ${i.rpe?'checked':''}>RPE</label></div><fieldset><legend>${w('allergies')}</legend>${select('allergyStatus',[['known',w('known')],['missing',w('unknown')]],n.allergies.status)}<label>${w('allergies')}<input name="allergies" value="${esc((n.allergies.value||[]).join(', '))}"></label></fieldset><button>${t('save')}</button></form><div class="actions"><button data-action="build">${t('build')}</button><button data-action="revoke">${t('revoke')}</button></div>`;
 }
 if(tab==='progress')return `<h2>${w('progress')}</h2><dl>${Object.entries(s.progress).filter(([k,v])=>typeof v==='number').map(([k,v])=>`<dt>${esc(({planVersions:t('history'),planVersion:t('planned'),registrationVersions:t('recorded'),recoveryVersions:t('recovery'),intakeVersions:t('intake')})[k])}</dt><dd>${v}</dd>`).join('')}</dl><h2>${t('facts')}</h2>${s.comparison?s.comparison.facts.map(f=>`<p>${esc(f.metric)} · ${JSON.stringify(f.delta)} ${esc(f.unit)}</p>`).join(''):`<p>${w('missingWindow')}</p>`}<button data-tab="history">${t('history')}</button>`;
 if(tab==='settings')return `<form data-preferences><h2>${w('settings')}</h2><div class="form-grid">${select('language',[['nl','Nederlands'],['en','English'],['de','Deutsch']],s.preferences.language)}${select('theme',[['light',t('light')],['dark',t('dark')]],s.preferences.theme)}${select('units',[['metric',w('metric')],['imperial',w('imperial')]],s.preferences.units)}</div><p>${w('sourceUnits')}</p><button>${t('save')}</button></form>`;
 return null;
}
return {words,panel};})();
