'use strict';
// Only synthetic registration drafts. No credentials, auth decisions or auto-sync.
const queueWords={
 draft:['Concept bewaard op dit apparaat. Opslag in de database is nog niet bevestigd; controleer en verzend zelf.','Draft saved on this device. Database storage is not confirmed; explicitly check and submit it.','Entwurf auf diesem Gerät gespeichert. Speicherung in der Datenbank nicht bestätigt; selbst prüfen und senden.'],
 changed:['Er zijn nieuwere brongegevens. Dezelfde aanvraag kan alleen worden gecontroleerd; een conflict vereist opnieuw beoordelen.','Newer source data exists. Only the same request can be checked; a conflict requires review.','Neuere Quelldaten vorhanden. Nur dieselbe Anfrage prüfen; ein Konflikt erfordert erneute Prüfung.'],
 consent:['Toestemming is ingetrokken. Deze registratie wordt niet aangeboden.','Consent was withdrawn. This record will not be submitted.','Einwilligung widerrufen. Dieser Eintrag wird nicht übermittelt.'],
 submit:['Registratie controleren / verzenden','Check / submit record','Eintrag prüfen / senden'],
 discard:['Alleen lokaal concept verwijderen','Remove local draft only','Nur lokalen Entwurf entfernen'],
 invalid:['Lokaal concept kan niet worden gecontroleerd. Het wordt niet verzonden.','Local draft cannot be verified. It will not be sent.','Lokaler Entwurf nicht prüfbar. Er wird nicht gesendet.'],
 removed:['Lokaal concept verwijderd. Een al opgeslagen databaseversie is niet teruggedraaid.','Local draft removed. A saved database version was not reversed.','Lokaler Entwurf entfernt. Eine gespeicherte Datenbankversion wurde nicht zurückgesetzt.'],
 preview:['Bewaarde waarden bekijken','View saved values','Gespeicherte Werte ansehen'],
 storage:['Concept kon niet op dit apparaat worden bewaard. Er is niets verzonden. Bewaar de invoer en probeer opnieuw.','Draft could not be saved on this device. Nothing was sent. Keep the input and try again.','Entwurf konnte nicht auf diesem Gerät gespeichert werden. Nichts wurde gesendet. Eingaben behalten und erneut versuchen.'],
 exists:['Er staat al een concept voor deze werkruimte. Controleer of verwijder dat eerst; de nieuwe invoer is niet bewaard.','A draft already exists for this workspace. Check or remove it first; the new input was not saved.','Für diesen Arbeitsbereich besteht bereits ein Entwurf. Zuerst prüfen oder entfernen; die neue Eingabe wurde nicht gespeichert.'],
 capacity:['Dit apparaat heeft tien concepten. Verwijder eerst een gecontroleerd concept; de nieuwe invoer is niet bewaard of verzonden.','This device has ten drafts. Remove a reviewed draft first; the new input was not saved or sent.','Auf diesem Gerät liegen zehn Entwürfe. Zuerst einen geprüften Entwurf entfernen; die neue Eingabe wurde weder gespeichert noch gesendet.'],
 cleanup:['De server heeft de aanvraag bevestigd. Het lokale concept kon niet worden verwijderd; controleer later dezelfde aanvraag.','The server confirmed the request. The local draft could not be removed; check the same request later.','Der Server hat die Anfrage bestätigt. Der lokale Entwurf konnte nicht entfernt werden; dieselbe Anfrage später prüfen.'],
 binding:['Meld opnieuw aan om je toegang en je concepten te controleren. Er is niets automatisch verzonden.','Sign in again to verify access and recover your drafts. Nothing was sent automatically.','Erneut anmelden, um Zugriff und Entwürfe zu prüfen. Nichts wurde automatisch gesendet.']};
let queueEpoch=0,queueCurrent=null,queueSessionEpoch=0,queueVerified=new WeakSet(),queueCleanupFailed=false;
globalThis.FMZQueueSession=Object.freeze({epoch:()=>queueSessionEpoch});
function checkQueueSession(epoch){if(epoch!==queueSessionEpoch)throw Object.assign(Error('login_required'),{staleSession:true});}
function clearQueue(){queueEpoch++;queueCurrent=null;$('#queued').hidden=true;$('#queued').replaceChildren();}
function lockQueueSession(){
 queueSessionEpoch++;queueVerified=new WeakSet();queueCleanupFailed=false;clearQueue();
 current=null;views=[];csrf='';pendingRequest=null;busy=false;
 for(const id of ['content','tabs','status','workspace','message'])$('#'+id).replaceChildren();
 $('#app').hidden=true;$('#logout').hidden=true;$('#login').hidden=false;$('#login').reset();
}
function queueError(err){if(err.staleSession)return;const key=err.message==='draft_capacity'?'capacity':err.message==='draft_exists'||err.message==='draft_changed'?'exists':err.message==='draft_storage'?'storage':err.message==='draft_actor'||err.message==='login_required'?'binding':null;if(key)message(queueWords[key][language],true);else error(err);}
function queuePreview(e,panel){
 const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent=queueWords.preview[language];details.append(summary);
 const data=e.payload.request.data;
 const rows=e.payload.request.action==='register12'?data.input.sets.map((row,i)=>`${t('set')} ${i+1}: ${row.load.value??t('missing')} ${row.load.unit}; ${t('reps')} ${row.reps??t('missing')}; RIR ${row.rir??t('missing')}; RPE ${row.rpe??t('missing')}`):[`${t('recoveryvalue')}: ${data.value??t('missing')}`];
 for(const text of rows){const p=document.createElement('p');p.textContent=text;details.append(p);}panel.append(details);
}
async function showQueue(){
 const epoch=++queueEpoch,sessionEpoch=queueSessionEpoch,view=current,panel=$('#queued');queueCurrent=null;panel.hidden=true;panel.replaceChildren();
 if(!view?.actor||view.role!=='member'||!csrf||!views.includes(view))return;
 // The initial ui.js refresh may have started before this module loaded.
 // Obtain a new verified response before reading any durable account draft.
 if(!queueVerified.has(view)){try{await refresh();}catch(_){}return;}
 let e,state;
 try{e=await FMZDraftQueue.get(view.actor,view.workspace);if(sessionEpoch!==queueSessionEpoch||epoch!==queueEpoch||current!==view)return;if(e)state=await FMZDraftQueue.inspect(e,view);}catch(_){e=null;state='invalid';}
 if(sessionEpoch!==queueSessionEpoch||epoch!==queueEpoch||current!==view||!state)return;
 queueCurrent=e||{invalid:true};panel.hidden=false;
 const p=document.createElement('p');p.textContent=queueWords[state==='pending'?'draft':state][language];panel.append(p);
 if(queueCleanupFailed){const warning=document.createElement('p');warning.textContent=queueWords.cleanup[language];panel.append(warning);}
 if(e){
  const detail=document.createElement('p');detail.className='small';detail.textContent=(e.payload.request.action==='register12'?t('historical'):t('recovery'))+' · '+t('version')+' '+e.payload.version;panel.append(detail);
  queuePreview(e,panel);
  const send=document.createElement('button');send.type='button';send.dataset.queueSubmit='';send.textContent=queueWords.submit[language];send.disabled=state==='consent';
  send.onclick=async()=>{
   if(sessionEpoch!==queueSessionEpoch||busy||current!==view||send.disabled)return;
   busy=true;
   try{
    await refresh();checkQueueSession(sessionEpoch);
    const latest=views.find(v=>v.workspace===e.workspace),status=await FMZDraftQueue.inspect(e,latest);
    checkQueueSession(sessionEpoch);
    if(status==='consent')throw Error('consent');
    if(current?.actor!==e.actor||current?.workspace!==e.workspace)return;
    pendingRequest=e.payload;await submitRequest(e.payload);
   }catch(err){if(sessionEpoch===queueSessionEpoch)queueError(err);}
   finally{if(sessionEpoch===queueSessionEpoch){busy=false;await showQueue();}}
  };panel.append(send);
 }
 const discard=document.createElement('button');discard.type='button';discard.dataset.queueDiscard='';discard.textContent=queueWords.discard[language];
 discard.onclick=async()=>{
  if(sessionEpoch!==queueSessionEpoch||busy||current!==view)return;
  busy=true;
  try{
   await FMZDraftQueue.remove(view.actor,view.workspace,e?.hash);checkQueueSession(sessionEpoch);
   if(current?.actor!==view.actor||current?.workspace!==view.workspace)return;
   if(pendingRequest?.workspace===view.workspace&&['register12','recovery'].includes(pendingRequest.request?.action)&&(!e||pendingRequest.request_id===e.payload.request_id))pendingRequest=null;
   queueCleanupFailed=false;message(queueWords.removed[language]);
  }catch(err){if(sessionEpoch===queueSessionEpoch)queueError(err);}
  finally{if(sessionEpoch===queueSessionEpoch){busy=false;await showQueue();}}
 };panel.append(discard);
}
const queueRender=render;render=function(){queueRender();void showQueue();};
const queueAPI=api;api=async function(path,data){
 if(path==='logout'){
  const request=queueAPI(path,data);lockQueueSession();const epoch=queueSessionEpoch;
  try{const result=await request;checkQueueSession(epoch);return result;}
  catch(err){if(epoch!==queueSessionEpoch)err.staleSession=true;throw err;}
 }
 if(path==='login')lockQueueSession();
 const actor=current?.actor,sessionEpoch=queueSessionEpoch;
 let e;
 try{
  if(path==='action'&&['register12','recovery'].includes(data?.request?.action)){
   if(!actor)throw Error('login_required');
   e=await FMZDraftQueue.get(actor,data.workspace);
   checkQueueSession(sessionEpoch);
   if(!e)throw Error('draft_binding');
   await FMZDraftQueue.checked({...e,payload:data});
   checkQueueSession(sessionEpoch);
   // All retries, including the general lost-response button, recheck real Auth.
   const fresh=await api('today'),latest=fresh.views.find(v=>v.workspace===e.workspace);
   if(await FMZDraftQueue.inspect(e,latest)==='consent')throw Object.assign(Error('consent'),{confirmed:true});
   checkQueueSession(sessionEpoch);
   if(current?.actor!==actor)throw Error('draft_actor');
   csrf=fresh.csrf;
  }
  const result=await queueAPI(path,data);
  checkQueueSession(sessionEpoch);
  if(path==='today'){
   if(!result||typeof result.csrf!=='string'||!result.csrf.trim()||!Array.isArray(result.views))throw Error('csrf');
   if(result.views.some(v=>!v||typeof v.actor!=='string'||!v.actor||typeof v.workspace!=='string'||!v.workspace||v.actor!==result.views[0].actor||actor&&v.actor!==actor))throw Error('draft_actor');
   for(const view of result.views)queueVerified.add(view);
  }
  if(e){let failed=false;try{await FMZDraftQueue.remove(e.actor,e.workspace,e.hash);}catch(_){failed=true;}checkQueueSession(sessionEpoch);queueCleanupFailed=failed;}
  return result;
 }catch(err){
  // An old completion must never clear a newer verified login. Preserve a
  // current request's deliberate invalidation through nested API checks.
  if(sessionEpoch!==queueSessionEpoch){if(err.invalidatedEpoch!==queueSessionEpoch)err.staleSession=true;throw err;}
  if(path==='today'&&err.confirmed||/login_required|auth_|session|csrf|workspace_denied|draft_actor/.test(err.message)){
   lockQueueSession();err.invalidatedSession=true;err.invalidatedEpoch=queueSessionEpoch;message(queueWords.binding[language],true);
  }
  throw err;
 }
};
const queueAct=act;act=async function(action,data={}){
 if(!['register12','recovery'].includes(action)){
  const safety=['revoke','health'].includes(action);
  if(queueCurrent&&!safety)return message(queueWords.draft[language],true);
  // showQueue clears queueCurrent while IndexedDB is pending. The durable
  // registration remains intact even when an explicit safety action proceeds.
  if(safety&&['register12','recovery'].includes(pendingRequest?.request?.action))pendingRequest=null;
  return queueAct(action,data);
 }
 if(busy||pendingRequest||queueCurrent)return;
 const sessionEpoch=queueSessionEpoch,view=current;
 busy=true;
 try{
  if(!view||!queueVerified.has(view))throw Error('login_required');
  const payload={workspace:view.workspace,request_id:crypto.randomUUID(),version:view.version,request:{action,data}};
  const e=await FMZDraftQueue.create(view,payload);checkQueueSession(sessionEpoch);
  await FMZDraftQueue.put(e);checkQueueSession(sessionEpoch);
  if(current!==view)throw Error('draft_actor');
  await submitRequest(payload);
 }catch(err){if(sessionEpoch===queueSessionEpoch)queueError(err);}
 finally{if(sessionEpoch===queueSessionEpoch){busy=false;await showQueue();}}
};
window.addEventListener('pageshow',event=>{if(event.persisted){lockQueueSession();message(queueWords.binding[language],true);}});
void showQueue();
