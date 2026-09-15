import {next,present,validate} from "./core.mjs";
const PROJECT="https://mokxyyullfhkfalopbzd.supabase.co";
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const known=new Set(["synthetic_access_denied","synthetic_session_required","synthetic_authority_conflict",
"synthetic_actor_denied","synthetic_consent_required","synthetic_command_invalid","synthetic_idempotency_conflict",
"synthetic_version_conflict","synthetic_source_conflict","synthetic_session_limit","synthetic_safety_block",
"synthetic_acceptance_order","synthetic_approval_order","synthetic_application_order","actor_denied","consent_required",
"safety_block","payload_invalid","command_invalid","route_action_denied","source_invalid","incomplete","catalog_gap",
"budget","excluded","conflicting_preferences","member_confirmation_required","not_pending","version_conflict"]);
export function createHandler({url,key,proof,fetcher=fetch}){
 if(url!==PROJECT)throw Error("staging_target_required");
 return async function handle(req){
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
 try{
 const reader=req.body?.getReader(),chunks=[];let size=0;
 if(reader)for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;
 if(size>16384){await reader.cancel();return reply(413,{error:"payload_too_large"});}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
 const text=new TextDecoder("utf-8",{fatal:true}).decode(bytes);
 const body=JSON.parse(text);
 const shape=body?.op==="home"?["op"]:body?.op==="read"?["op","workspace"]:["op","workspace","expected","key","command"];
 if(!body||Array.isArray(body)||Object.keys(body).sort().join()!==shape.sort().join()||!["home","read","command"].includes(body.op))return reply(400,{error:"payload_invalid"});
 if(body.op!=="home"&&!UUID.test(body.workspace))return reply(400,{error:"payload_invalid"});
 if(body.op==="command"&&(!UUID.test(body.key)||!Number.isSafeInteger(body.expected)||body.expected<0))return reply(400,{error:"payload_invalid"});
 const auth=await fetcher(url+"/auth/v1/user",{headers:{Authorization:token,apikey:key},signal:AbortSignal.timeout(10000)});
 if(!auth.ok)return reply(401,{error:"authentication_required"});
 const user=await auth.json();if(!UUID.test(user.id))return reply(401,{error:"authentication_required"});
 const h={Authorization:token,apikey:key,"Content-Type":"application/json","x-fmz6e9-proof":proof};
 async function rpc(name,args){
 const r=await fetcher(url+"/rest/v1/rpc/"+name,{method:"POST",headers:h,body:JSON.stringify(args),signal:AbortSignal.timeout(15000)});
 const d=await r.json();
 if(!r.ok)throw Error(known.has(d.message)?d.message:"synthetic_operation_denied");return d;
 }
 if(body.op==="home")return reply(200,{workspaces:await rpc("fmz6e9_home",{})});
 let receipt=null;
 let row=await rpc("fmz6e9_read",{p_workspace:body.workspace});
 if(body.op==="command"){
 validate(body.command,row.route);
 receipt=await rpc("fmz6e9_replay",{p_workspace:body.workspace,p_key:body.key,p_expected:body.expected,p_action:body.command.action,p_payload:body.command.data});
 if(!receipt){
 if(row.revision!==body.expected)throw Error("synthetic_version_conflict");
 const result=await next(row,body.command);
 receipt=await rpc("fmz6e9_commit",{p_workspace:body.workspace,p_key:body.key,p_expected:body.expected,
 p_action:body.command.action,p_payload:body.command.data,p_basis:row.basis,
 p_next:{event:result.event,status:result.status,version:result.version,content:result.content,candidate_hash:result.candidate_hash}});
 }
 row=await rpc("fmz6e9_read",{p_workspace:body.workspace});
 }
 const view=present(row);
 const lists={};
 for(const [name,table] of [["audit","fmz6e9_audit"],["notices","fmz6e9_notices"]]){
 const res=await fetcher(url+"/rest/v1/"+table+"?workspace=eq."+body.workspace+"&order=id.asc&limit=500",{headers:h,signal:AbortSignal.timeout(10000)});
 if(!res.ok)throw Error("synthetic_operation_denied");lists[name]=await res.json();
 }
 return reply(200,{...view,receipt,...lists});
 }catch(e){
 const code=known.has(e?.message)?e.message:"synthetic_operation_denied";
 const status=/version|source|idempotency/.test(code)?409:/payload|command_invalid/.test(code)?400:403;
 return reply(status,{error:code});
 }
 };
}
