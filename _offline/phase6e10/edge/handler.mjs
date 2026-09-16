const PROJECT="https://mokxyyullfhkfalopbzd.supabase.co";
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export function createHandler({url,key,proof,fetcher=fetch}){
 if(url!==PROJECT)throw Error("staging_target_required");
 return async req=>{
 const origin=req.headers.get("Origin");
 const cors=origin==="https://yourizorge.github.io"||/^http:\/\/127\.0\.0\.1:[0-9]+$/.test(origin||"")?origin:"";
 const headers={"Content-Type":"application/json","Cache-Control":"no-store","Vary":"Origin"};
 if(cors)Object.assign(headers,{"Access-Control-Allow-Origin":cors,"Access-Control-Allow-Headers":"authorization,content-type","Access-Control-Allow-Methods":"POST,OPTIONS"});
 const reply=(status,data)=>new Response(JSON.stringify(data),{status,headers});
 if(origin&&!cors)return reply(403,{error:"origin_denied"});
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers});
 if(req.method!=="POST")return reply(405,{error:"method_denied"});
 if(!proof||!key)return reply(503,{error:"synthetic_disabled"});
 const token=req.headers.get("Authorization");
 if(!/^Bearer [A-Za-z0-9_.-]+$/.test(token||""))return reply(401,{error:"authentication_required"});
 let stage="input";
 try{
  const reader=req.body?.getReader(),chunks=[];let size=0;
  if(reader)for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;
   if(size>32768){await reader.cancel();return reply(413,{error:"payload_too_large"});}chunks.push(value);}
  const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}
  const p=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
  const shape=p?.op==="home"?["op"]:p?.op==="read"?["op","window","workspace"]:["op","window","workspace","key","expected","action","data"];
  if(!p||Array.isArray(p)||Object.keys(p).sort().join()!==shape.sort().join()||!["home","read","command"].includes(p.op))
   return reply(400,{error:"payload_invalid"});
  if(p.op==="read"&&(!UUID.test(p.window)||!UUID.test(p.workspace)))return reply(400,{error:"payload_invalid"});
  if(p.op==="command"&&(!UUID.test(p.key)||!Number.isSafeInteger(p.expected)||p.expected<0||
   (p.window!==null&&!UUID.test(p.window))||(p.workspace!==null&&!UUID.test(p.workspace))||
   typeof p.action!=="string"||!p.data||Array.isArray(p.data)||typeof p.data!=="object"))return reply(400,{error:"payload_invalid"});
  stage="auth";
  const auth=await fetcher(url+"/auth/v1/user",{headers:{Authorization:token,apikey:key},signal:AbortSignal.timeout(12000)});
  if(auth.status>=500||auth.status===429)return reply(503,{error:"synthetic_auth_temporarily_unavailable"});
  if(!auth.ok)return reply(401,{error:"authentication_required"});
  if(!UUID.test((await auth.json()).id))return reply(401,{error:"authentication_required"});
  stage="database";
  const r=await fetcher(url+"/rest/v1/rpc/fmz6e10_call",{method:"POST",headers:{Authorization:token,apikey:key,"Content-Type":"application/json","x-fmz6e10-proof":proof},body:JSON.stringify({p}),signal:AbortSignal.timeout(20000)});
  const d=await r.json();
  if(!r.ok){
   // Forward only a complete machine code, never SQL detail, values or headers.
   if(r.status>=500||r.status===429)return reply(503,{error:"synthetic_database_temporarily_unavailable"});
   if(!/^synthetic_[a-z0-9_]{1,80}$/.test(d?.message||"")){
    if(/^(22|23)/.test(d?.code||""))return reply(400,{error:"payload_invalid"});
    return reply(503,{error:"synthetic_database_temporarily_unavailable"});
   }
   const code=d.message;
   return reply(/stale|conflict/.test(code)?409:403,{error:code});
  }
  return reply(200,d);
 }catch{return stage==="input"?reply(400,{error:"payload_invalid"}):reply(503,{error:"synthetic_"+stage+"_temporarily_unavailable"});}
 };
}
