(function(root){
'use strict';
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
const actions=new Set(['register12','recovery']);
const HASH=/^[a-f0-9]{64}$/;
const exact=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).sort().join(',')===keys.slice().sort().join(',');
const canonical=x=>JSON.stringify(x===null||typeof x!=='object'?x:Array.isArray(x)?x.map(v=>JSON.parse(canonical(v))):Object.fromEntries(Object.keys(x).sort().map(k=>[k,JSON.parse(canonical(x[k]))])));
async function hash(x){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(x))))).map(x=>x.toString(16).padStart(2,'0')).join('');}
function dataShape(action,data){
 const id=x=>typeof x==='string'&&/^[a-zA-Z0-9_-]{1,160}$/.test(x);
 const version=x=>Number.isSafeInteger(x)&&x>=0;
 const number=x=>x===null||typeof x==='number'&&Number.isFinite(x)&&x>=0;
 if(action==='recovery')return exact(data,['id','version','value'])&&id(data.id)&&version(data.version)&&number(data.value);
 if(!exact(data,['input']))return false;
 const p=data.input;
 if(!exact(p,['synthetic_only','subject_id','workspace_id','id','revision','session_id','snapshot_id','source_hash','snapshot_hash','sets'])||p.synthetic_only!==true||!version(p.revision)||!HASH.test(p.source_hash)||!HASH.test(p.snapshot_hash)||!['subject_id','workspace_id','id','session_id','snapshot_id'].every(k=>id(p[k]))||!Array.isArray(p.sets)||p.sets.length>1000)return false;
 return p.sets.every(r=>exact(r,['id','subject_id','session_id','snapshot_id','exercise_id','set_index','completed','reps','load','rir','rpe','quality'])&&['id','subject_id','session_id','snapshot_id','exercise_id'].every(k=>id(r[k]))&&version(r.set_index)&&typeof r.completed==='boolean'&&['confirmed','disputed'].includes(r.quality)&&['reps','rir','rpe'].every(k=>number(r[k]))&&exact(r.load,['value','unit'])&&number(r.load.value)&&['kg','lb'].includes(r.load.unit));
}
function validate(e){
 if(!exact(e,['format','actor','workspace','source','payload','hash'])||e.format!==1||!UUID.test(e.actor)||!UUID.test(e.workspace)||!HASH.test(e.source)||!HASH.test(e.hash))throw Error('draft_binding');
 const p=e.payload;
 if(!exact(p,['workspace','request_id','version','request'])||p.workspace!==e.workspace||!UUID.test(p.request_id)||!Number.isSafeInteger(p.version)||p.version<0||!exact(p.request,['action','data'])||!actions.has(p.request.action))throw Error('draft_action');
 const raw=canonical(p);
 if(new TextEncoder().encode(raw).length>131072||!dataShape(p.request.action,p.request.data))throw Error('draft_content');
}
async function checked(input){const e=structuredClone(input);validate(e);const {hash:actual,...bound}=e;if(actual!==await hash(bound))throw Error('draft_integrity');return e;}
async function create(view,payload){
 view=structuredClone(view);payload=structuredClone(payload);
 if(!view||view.role!=='member'||view.state.consent!==true||view.workspace!==payload.workspace||view.version!==payload.version)throw Error('draft_context');
 if(payload.request.action==='register12'&&!view.capabilities.registration12)throw Error('draft_scope');
 if(payload.request.action==='recovery'&&view.capabilities.registration12)throw Error('draft_scope');
 const source=await sourceHash(view);
 const bound={format:1,actor:view.actor,workspace:view.workspace,source,payload:structuredClone(payload)};
 return checked({...bound,hash:await hash(bound)});
}
async function inspect(e,view){
 e=await checked(e);
 if(!view||view.actor!==e.actor||view.workspace!==e.workspace||view.role!=='member')throw Error('draft_actor');
 if(view.state.consent!==true)return 'consent';
 if((e.payload.request.action==='register12')!==(view.capabilities?.registration12===true))throw Error('draft_scope');
 const source=await sourceHash(view);
 return view.version===e.payload.version&&source===e.source?'pending':'changed';
}
async function sourceHash(view){const source=view.capabilities.registration12?view.state.snapshot:view.state.sourceHash;if(source===undefined||source===null)throw Error('draft_source');return hash(source);}
const key=e=>e.actor+':'+e.workspace;
async function db(){return new Promise((resolve,reject)=>{const q=indexedDB.open('fmz-local-synthetic-drafts-v1',1);q.onupgradeneeded=()=>q.result.createObjectStore('drafts');q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(Error('draft_storage'));q.onblocked=()=>reject(Error('draft_storage'));});}
async function operation(mode,fn){const store=await db();try{return await new Promise((resolve,reject)=>{const tx=store.transaction('drafts',mode);let value;try{const q=fn(tx.objectStore('drafts'));q.onsuccess=()=>{value=q.result;};}catch(e){tx.abort();reject(e);return;}tx.oncomplete=()=>resolve(value);tx.onabort=()=>reject(Error('draft_storage'));tx.onerror=()=>reject(Error('draft_storage'));});}finally{store.close();}}
async function put(e){e=await checked(e);const store=await db();try{await new Promise((resolve,reject)=>{const tx=store.transaction('drafts','readwrite'),s=tx.objectStore('drafts');let reason='draft_storage';const q=s.get(key(e));q.onsuccess=()=>{if(q.result&&q.result.hash!==e.hash){reason='draft_exists';tx.abort();}else{const n=s.count();n.onsuccess=()=>{if(!q.result&&n.result>=10){reason='draft_capacity';tx.abort();}else s.put(e,key(e));};}};tx.oncomplete=resolve;tx.onabort=()=>reject(Error(reason));tx.onerror=()=>reject(Error(reason));});}finally{store.close();}}
async function get(actor,workspace){if(!UUID.test(actor)||!UUID.test(workspace))throw Error('draft_binding');const e=await operation('readonly',s=>s.get(actor+':'+workspace));if(!e)return null;if(e.actor!==actor||e.workspace!==workspace)throw Error('draft_binding');return checked(e);}
async function remove(actor,workspace,expectedHash){
 if(!UUID.test(actor)||!UUID.test(workspace)||expectedHash!==undefined&&!HASH.test(expectedHash))throw Error('draft_binding');
 const store=await db();try{await new Promise((resolve,reject)=>{
  const tx=store.transaction('drafts','readwrite'),s=tx.objectStore('drafts');let reason='draft_storage';
  const q=s.get(actor+':'+workspace);q.onsuccess=()=>{if(q.result&&expectedHash!==undefined&&q.result.hash!==expectedHash){reason='draft_changed';tx.abort();}else s.delete(actor+':'+workspace);};
  tx.oncomplete=resolve;tx.onabort=()=>reject(Error(reason));tx.onerror=()=>reject(Error(reason));
 });}finally{store.close();}
}
const api={create,checked,inspect,put,get,remove};
if(typeof module==='object')module.exports=api;else root.FMZDraftQueue=api;
})(globalThis);
