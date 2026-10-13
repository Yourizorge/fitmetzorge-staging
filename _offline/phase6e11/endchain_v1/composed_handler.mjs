// Reuse the existing HTTP/Auth/product handler, with no uncounted Data API read.
import {createRequestHandler} from '../request_v4/handler.mjs';
import {verifiedClaims,BASE} from '../edge_bridge_v2/handler.mjs';
export function createComposedHandler({key,proof,transport,fetcher=fetch,now=Date.now,onFailure=()=>{}}){
 if(typeof transport?.read!=='function'||typeof transport?.invoke!=='function')throw Error('composed_transport_required');
 const failed=(error,fallback)=>onFailure({
  phase:/^[a-z_]{1,63}$/.test(error?.phase)?error.phase:fallback,
  code:/^[a-z0-9_]{1,63}$/.test(error?.code)?error.code:'transport_unconfirmed'});
 return async request=>{
  const id=request.headers.get('x-fmz6e11-request-id')||crypto.randomUUID();
  let claims=null,authorization=null;
  const scoped=async(url,options={})=>{
   if(url===BASE+'/auth/v1/user'){
    if(claims||authorization)throw Error('repeated_auth_denied');
    const response=await fetcher(url,options);
    if(response.ok){
     const user=await response.clone().json();
     authorization=options.headers.Authorization;
     claims=verifiedClaims(authorization,user,now());
    }
    return response;
   }
   if(url!==BASE+'/rest/v1/rpc/fmz6e11_call'||options.method!=='POST'||
      !claims||options.headers.Authorization!==authorization||claims.exp*1000<=now())
    return Response.json({message:'synthetic_session_required'},{status:403});
   const body=JSON.parse(options.body);
   if(Object.keys(body).join()!=='p'||body.p?.op!=='read')
    return Response.json({message:'synthetic_audited_route_required'},{status:403});
   try{
    const result=await transport.read({input:body.p,claims,proof,requestId:id});
    return Response.json(result);
   }catch(error){
    failed(error,'read_transport');
    return Response.json({message:'synthetic_bridge_unavailable'},{status:503});
   }
  };
  const headers=new Headers(request.headers);headers.set('x-fmz6e11-request-id',id);
  return createRequestHandler({url:BASE,key,proof,fetcher:scoped,now,
   transport:async args=>{
    try{return await transport.invoke(args);}catch(error){failed(error,'mutation_transport');throw error;}
   }})(new Request(request,{headers}));
 };
}
