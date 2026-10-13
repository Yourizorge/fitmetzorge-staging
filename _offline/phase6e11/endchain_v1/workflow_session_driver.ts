// Disposable local PG17 only. Real native SQL + existing HTTP/product handler;
// the Auth response is explicitly a local stub, never a hosted admission.
import postgres from 'https://deno.land/x/postgresjs@v3.4.7/mod.js';
import readline from 'node:readline';
import {createSessionTransport} from './session_transport.mjs';
import {createComposedHandler} from './composed_handler.mjs';
const lines=readline.createInterface({input:process.stdin,terminal:false})[Symbol.asyncIterator]();
const read=async()=>JSON.parse((await lines.next()).value);
const p=await read();
if(p.mode!=='disposable_local'||!Number.isInteger(p.port)||p.port<56110||p.port>=56140)throw Error('local_only');
const ca=await Deno.readTextFile(p.ca),commands:string[]=[];
const started=performance.now();
const t=createSessionTransport({postgres:(o:any)=>postgres({...o,host:'127.0.0.1',port:p.port,
 username:'postgres',password:'',ssl:{caCerts:[ca],hostname:'127.0.0.1'}}),
 connectionUrl:'postgres://postgres:synthetic@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',
 ca,sessionHost:'aws-0-eu-west-2.pooler.supabase.com',onCommand:(phase:string)=>commands.push(phase)});
let requests=0,reads=0,failure:any=null;
try{
 for(;;){
  const req=await read();if(req.op==='close')break;
  if(req.op!=='invoke'||++requests>71)throw Error('local_request_budget');
  const before=commands.length;
  let receipt:any=null;
  const q=req.input.op==='internal_b'?req.input.request:req.input;
  if(['revoke','cleanup_batch'].includes(q.action)){
   receipt=await t.invoke({...req,proof:'synthetic-only-local-proof'});
  }else{
   const emails:any={1:'zorgeyouri+6e9-a-lid@gmail.com',2:'zorgeyouri+6e9-a-trainer@gmail.com',3:'zorgeyouri+6e9-b-lid@gmail.com'};
   const role=Number(req.claims.sub.slice(-1));
   const encode=(v:any)=>btoa(JSON.stringify(v)).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
   const token=encode({alg:'HS256',typ:'JWT'})+'.'+encode(req.claims)+'.local_synthetic_signature';
   const handler=createComposedHandler({key:'local_synthetic',proof:'synthetic-only-local-proof',onFailure:(v:any)=>{failure=v;},transport:{
    read:async(args:any)=>{reads++;return t.read(args);},
    invoke:async(args:any)=>{receipt=await t.invoke(args);return receipt;}
   },fetcher:async()=>Response.json({id:req.claims.sub,email:emails[role]})});
   const result=await handler(new Request('https://synthetic.invalid',{method:'POST',headers:{
    'Content-Type':'application/json',Authorization:'Bearer '+token,'x-fmz6e11-request-id':req.requestId},body:JSON.stringify(q)}));
   if(!receipt||result.status!==(receipt.http_status||200))throw Error('local_handler_response');
  }
  console.log(JSON.stringify({receipt,commands:commands.length-before,total:commands.length,reads}));
 }
 await t.close();
 console.log(JSON.stringify({status:'LOCAL_COMPOSED_WORKFLOW_TRANSPORT_PASS',requests,reads,
  commands:commands.length,seconds:(performance.now()-started)/1000,hosted_admitted:false,auth:'local_stubs'}));
}catch(e){
 console.log(JSON.stringify({status:'NO_GO',phase:failure?.phase||(e as any).phase||'local_handler',code:failure?.code||(e as any).code||'composed_local_failure',
  requests,commands:commands.length,reads}));Deno.exitCode=2;
}finally{await t.close();process.stdin.destroy();}
