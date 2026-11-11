// Private local worker evidence. No tokens, headers, bodies or new requests.
const ROUTES=Object.freeze({
 issue:['POST','/admin/generate_link'],verify:['POST','/verify'],
 getUser:['GET','/user'],refresh:['POST','/token?grant_type=refresh_token'],
 logout:['POST','/logout?scope=local'],revoked_denial:['GET','/user']
});
const roles=new Set(['a_member','a_trainer','b_member']);
const require=(ok,code)=>{if(!ok)throw Error(code);};

export async function completeResponse(response){
 require(response&&Number.isInteger(response.status),'http_response_shape');
 const length=response.headers.get('content-length'),transfer=response.headers.get('transfer-encoding');
 require(!response.headers.get('content-encoding')||response.headers.get('content-encoding')==='identity','http_encoded_body');
 require(!(length!==null&&transfer!==null),'http_ambiguous_framing');
 require(length===null||/^(0|[1-9][0-9]*)$/.test(length),'http_length');
 require(transfer===null||transfer.toLowerCase()==='chunked','http_transfer');
 const noBody=[204,304].includes(response.status);
 require(length!==null||transfer!==null||noBody,'http_framing_missing');
 const expected=length===null?null:Number(length);
 require(expected===null||Number.isSafeInteger(expected)&&expected<=65536,'http_body_bound');
 const chunks=[];let size=0;
 const reader=response.body?.getReader();
 if(reader){
  try{
   while(true){
    const part=await reader.read();
    if(part.done)break;
    size+=part.value.byteLength;
    require(size<=65536,'http_body_bound');chunks.push(part.value);
   }
  }catch(error){try{await reader.cancel();}catch{}throw error;}
  finally{reader.releaseLock();}
 }
 require((expected===null||size===expected)&&(!noBody||size===0),'http_body_incomplete');
 const body=new Uint8Array(size);let offset=0;
 for(const chunk of chunks){body.set(chunk,offset);offset+=chunk.byteLength;}
 return new Response(noBody?null:body,{status:response.status,statusText:response.statusText,headers:response.headers});
}

export function createHttpLedger(fetcher){
 require(typeof fetcher==='function','http_fetcher');
 const rows=[];let sealed=false;
 function begin(role,operation,safety=false){
  require(!sealed&&roles.has(role)&&Object.hasOwn(ROUTES,operation)&&typeof safety==='boolean'
   &&(!safety||operation==='logout')&&rows.length<21,'http_intent_scope');
  require(rows.length===0||rows.at(-1).terminal===true,'http_previous_unknown');
  rows.push({ordinal:rows.length+1,role,operation,safety,attempted:false,terminal:false,status:null});
 }
 const network=async(url,options={})=>{
  const row=rows.at(-1),target=new URL(url);
  require(!sealed&&row&&!row.attempted&&!row.terminal,'http_intent_required');
  const [method,path]=ROUTES[row.operation];
  require(target.origin==='https://mokxyyullfhkfalopbzd.supabase.co'&&!target.username&&!target.password
   &&!target.hash&&target.pathname+target.search==='/auth/v1'+path&&options.method===method,'http_intent_route');
  row.attempted=true;
  let response=await fetcher(url,{...options,headers:{...options.headers,'accept-encoding':'identity'}});
  row.status=response.status;
  response=await completeResponse(response);
  row.terminal=true;
  return response;
 };
 return Object.freeze({begin,fetcher:network,
  seal:()=>{sealed=true;},
  snapshot:()=>({format:'case-auth-http-v1',sealed,rows:structuredClone(rows)})});
}

