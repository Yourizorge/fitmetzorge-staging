'use strict';
// Preparation only: no browser persistence, credential storage or automatic sync.
const crypto=require('node:crypto');
const digest=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const actions=new Set(['register12','recovery']);
const uuid=x=>typeof x==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(x);
function draft({actor,workspace,version,source,request,request_id}){
 if(!uuid(actor)||!uuid(workspace)||!uuid(request_id)||!Number.isSafeInteger(version)||version<0||
 !/^[a-f0-9]{64}$/.test(source)||!request||Object.keys(request).sort().join(',')!=='action,data'||!actions.has(request.action))throw Error('draft_scope');
 const envelope={actor,workspace,version,source,request:structuredClone(request),request_id};
 const raw=JSON.stringify(envelope);
 if(raw.length>131072||/"(?:password|token|authorization|role|service_role|access_token|refresh_token)"\s*:/i.test(raw))throw Error('draft_content');
 return {...envelope,hash:digest(envelope),status:'local_draft_not_server_saved'};
}
function reconcile(saved,current,receipt=null){
 const {hash,status,...envelope}=saved;
 if(hash!==digest(envelope)||status!=='local_draft_not_server_saved')throw Error('draft_integrity');
 draft(envelope);
 if(!current||current.authenticated!==true||current.actor!==saved.actor||current.workspace!==saved.workspace)throw Error('auth_binding');
 if(current.consent!==true)throw Error('consent');
 if(receipt){
  if(receipt.request_id!==saved.request_id||receipt.payload_hash!==digest({expected:saved.version,request:saved.request}))throw Error('receipt_conflict');
  return {status:'already_saved',version:receipt.version,submit:false};
 }
 if(current.version!==saved.version||current.source!==saved.source)return {status:'conflict_review_required',submit:false,keep_draft:true};
 return {status:'ready_for_explicit_sync',submit:false,payload:{workspace:saved.workspace,request_id:saved.request_id,version:saved.version,request:structuredClone(saved.request)}};
}
module.exports={draft,reconcile,digest};
