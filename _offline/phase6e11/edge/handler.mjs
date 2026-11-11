import {next,present,C,validate} from './core.mjs';
const URL='https://mokxyyullfhkfalopbzd.supabase.co';
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
export function createHandler({url,key,proof,fetcher=fetch}){
 if(url!==URL)throw Error('staging_target_required');
 return async req=>{
  const origin=req.headers.get('Origin'),allowed=origin==='https://yourizorge.github.io'||/^http:\/\/127\.0\.0\.1:\d+$/.test(origin||'');
  const headers={'Content-Type':'application/json','Cache-Control':'no-store','Vary':'Origin'};
  if(allowed)Object.assign(headers,{'Access-Control-Allow-Origin':origin,'Access-Control-Allow-Headers':'authorization,content-type,apikey,x-client-info','Access-Control-Allow-Methods':'POST,OPTIONS'});
  const reply=(status,data)=>new Response(JSON.stringify(data),{status,headers});
  if(origin&&!allowed)return reply(403,{error:'origin_denied'});
  if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
  if(req.method!=='POST')return reply(405,{error:'method_denied'});
  if(!proof||!key)return reply(503,{error:'synthetic_disabled'});
  const authorization=req.headers.get('Authorization');
  if(!/^Bearer [A-Za-z0-9_.-]+$/.test(authorization||''))return reply(401,{error:'authentication_required'});
  let stage='input';
  try{
   const reader=req.body?.getReader(),chunks=[];let n=0;
   if(reader)for(;;){const r=await reader.read();if(r.done)break;n+=r.value.length;if(n>32768){await reader.cancel();return reply(413,{error:'payload_too_large'});}chunks.push(r.value);}
   const bytes=new Uint8Array(n);let off=0;for(const c of chunks){bytes.set(c,off);off+=c.length;}
   const p=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
   const shape=p?.op==='home'?['op']:p?.op==='read'?['op','window','workspace']:['op','window','workspace','key','expected','action','data'];
   if(!p||Array.isArray(p)||!['home','read','command'].includes(p.op)||Object.keys(p).sort().join()!==shape.sort().join())return reply(400,{error:'payload_invalid'});
   if(p.op==='read'&&(!uuid.test(p.window)||!uuid.test(p.workspace)))return reply(400,{error:'payload_invalid'});
   if(p.op==='command'&&(!uuid.test(p.key)||!Number.isSafeInteger(p.expected)||p.expected<0||typeof p.action!=='string'||
    p.window!==null&&!uuid.test(p.window)||p.workspace!==null&&!uuid.test(p.workspace)||!p.data||Array.isArray(p.data)||typeof p.data!=='object'))return reply(400,{error:'payload_invalid'});
   stage='auth';
   const auth=await fetcher(url+'/auth/v1/user',{headers:{Authorization:authorization,apikey:key},signal:AbortSignal.timeout(12000)});
   if(auth.status===429||auth.status>=500)return reply(503,{error:'auth_temporarily_unavailable'});
   if(!auth.ok||!uuid.test((await auth.json()).id))return reply(401,{error:'authentication_required'});
   stage='database';
   const rpc=async q=>{
    const r=await fetcher(url+'/rest/v1/rpc/fmz6e11_call',{method:'POST',headers:{Authorization:authorization,apikey:key,'Content-Type':'application/json','x-fmz6e11-proof':proof},body:JSON.stringify({p:q}),signal:AbortSignal.timeout(20000)});
    const d=await r.json();
    if(!r.ok){
     const known=/^synthetic_[a-z0-9_]{1,100}$/.test(d?.message||'');
     throw {status:r.status>=500||r.status===429?503:known?/stale|conflict/.test(d.message)?409:403:400,
      code:known?d.message:r.status>=500?'database_temporarily_unavailable':'payload_invalid'};
    }
    return d;
   };
   let result;
   if(p.op==='command'&&p.action.startsWith('b_')){
    const data=await rpc({op:'read',window:p.window,workspace:p.workspace});
    if(!data.b_row)throw {status:403,code:'synthetic_route_denied'};
    let computed;
    try{
     const action=p.action.slice(2);
     if(!['build','edit','confirm','apply','reject','restore','reopen'].includes(action))throw Error('route_action_denied');
     if(action==='build'&&Object.keys(p.data).length)throw Error('payload_invalid');
     if(action==='edit'&&!['replace','add','remove','move'].includes(p.data.kind))throw Error('route_action_denied');
     const command={action,data:action==='build'?{intake:C.defaults}:p.data};
     validate(command,'B');
     const value=await next(data.b_row,command);
     computed={event:value.event,status:value.status,version:value.version,content:value.content,
      candidate_hash:value.candidate_hash,row_revision:data.b_row.revision,source_hash:data.b_row.basis.model};
    }catch(e){computed={error:/^[a-z0-9_]{1,80}$/.test(e.message||'')?e.message:'computation_failed'};}
    result=await rpc({op:'internal_b',request:p,computed});
   }else result=await rpc(p);
   if(result?.http_status)return reply(result.http_status,{error:result.error});
   if(result.b_row){
    const row=result.b_row;
    result={...result,...present(row),window:row.window,role:'b_member',b_revision:row.revision,b_proposal_version:row.proposal_version,
     source_name:row.source_name,source_version:row.source_version,source_hash:row.source_hash,
     catalog:C.exercises.map(e=>({id:e.id,label:e.label}))};
    delete result.b_row;
   }
   return reply(200,result);
  }catch(e){return reply(e?.status|| (stage==='input'?400:503),{error:e?.code||(stage==='input'?'payload_invalid':stage+'_temporarily_unavailable')});}
 };
}
