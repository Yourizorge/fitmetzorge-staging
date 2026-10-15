'use strict';
// Only synthetic registration drafts. No credentials, auth decisions or auto-sync.
const queueWords={
 draft:['Registratie wacht op controle; nog niet bevestigd opgeslagen in de database.','Record awaits checking; database storage is not confirmed.','Eintrag wartet auf Prüfung; Datenbankspeicherung nicht bestätigt.'],
 changed:['Er zijn nieuwere brongegevens. Dezelfde aanvraag kan alleen worden gecontroleerd; een conflict vereist opnieuw beoordelen.','Newer source data exists. Only the same request can be checked; a conflict requires review.','Neuere Quelldaten vorhanden. Nur dieselbe Anfrage prüfen; ein Konflikt erfordert erneute Prüfung.'],
 consent:['Toestemming is ingetrokken. Deze registratie wordt niet aangeboden.','Consent was withdrawn. This record will not be submitted.','Einwilligung widerrufen. Dieser Eintrag wird nicht übermittelt.'],
 submit:['Registratie controleren / verzenden','Check / submit record','Eintrag prüfen / senden'],
 discard:['Alleen lokaal concept verwijderen','Remove local draft only','Nur lokalen Entwurf entfernen'],
 invalid:['Lokaal concept kan niet worden gecontroleerd. Het wordt niet verzonden.','Local draft cannot be verified. It will not be sent.','Lokaler Entwurf nicht prüfbar. Er wird nicht gesendet.'],
 removed:['Lokaal concept verwijderd. Een al opgeslagen databaseversie is niet teruggedraaid.','Local draft removed. A saved database version was not reversed.','Lokaler Entwurf entfernt. Eine gespeicherte Datenbankversion wurde nicht zurückgesetzt.']};
let queueEpoch=0,queueCurrent=null;
async function showQueue(){
 const epoch=++queueEpoch,view=current,panel=$('#queued');queueCurrent=null;panel.hidden=true;panel.replaceChildren();
 if(!view?.actor||view.role!=='member')return;
 let e,state;
 try{e=await FMZDraftQueue.get(view.actor,view.workspace);if(e)state=await FMZDraftQueue.inspect(e,view);}catch(_){state='invalid';}
 if(epoch!==queueEpoch||current!==view||!state)return;
 queueCurrent=e||{invalid:true};panel.hidden=false;
 const p=document.createElement('p');p.textContent=queueWords[state==='pending'?'draft':state][language];panel.append(p);
 if(e){
  const detail=document.createElement('p');detail.className='small';detail.textContent=(e.payload.request.action==='register12'?t('historical'):t('recovery'))+' · '+t('version')+' '+e.payload.version;panel.append(detail);
  const send=document.createElement('button');send.type='button';send.dataset.queueSubmit='';send.textContent=queueWords.submit[language];send.disabled=state==='consent';
  send.onclick=async()=>{if(busy||current!==view||send.disabled)return;busy=true;try{await refresh();const latest=views.find(v=>v.workspace===e.workspace);const status=await FMZDraftQueue.inspect(e,latest);if(status==='consent')throw Error('consent');pendingRequest=e.payload;await submitRequest(e.payload);}catch(err){error(err);}finally{busy=false;await showQueue();}};panel.append(send);
 }
 const discard=document.createElement('button');discard.type='button';discard.dataset.queueDiscard='';discard.textContent=queueWords.discard[language];discard.onclick=async()=>{if(busy||current!==view)return;busy=true;try{await FMZDraftQueue.remove(view.actor,view.workspace);if(pendingRequest?.workspace===view.workspace)pendingRequest=null;message(queueWords.removed[language]);await showQueue();}catch(err){error(err);}finally{busy=false;}};panel.append(discard);
}
const queueRender=render;render=function(){queueRender();void showQueue();};
const queueAPI=api;api=async function(path,data){const actor=current?.actor;const result=await queueAPI(path,data);if(path==='action'&&actor&&['register12','recovery'].includes(data?.request?.action)){const e=await FMZDraftQueue.get(actor,data.workspace);if(e?.payload.request_id===data.request_id)await FMZDraftQueue.remove(actor,data.workspace);}return result;};
const queueAct=act;act=async function(action,data={}){
 if(!['register12','recovery'].includes(action)){if(queueCurrent&&!['revoke','health'].includes(action))return message(queueWords.draft[language],true);if(queueCurrent&&['revoke','health'].includes(action))pendingRequest=null;return queueAct(action,data);}
 if(busy||pendingRequest||queueCurrent)return;
 busy=true;
 try{const payload={workspace:current.workspace,request_id:crypto.randomUUID(),version:current.version,request:{action,data}};const e=await FMZDraftQueue.create(current,payload);await FMZDraftQueue.put(e);await submitRequest(payload);}catch(err){error(err);}finally{busy=false;await showQueue();}
};
void showQueue();
