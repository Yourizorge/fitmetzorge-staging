import postgres from 'npm:postgres@3.4.7';
import {createRequestTransport} from '../request_v4/transport.mjs';
let text='';for await(const chunk of Deno.stdin.readable)text+=new TextDecoder().decode(chunk);
const p=JSON.parse(text);
if(!Number.isSafeInteger(p.port)||p.port<56110||p.port>=56140)throw Error('local_port_only');
const ca=await Deno.readTextFile(p.ca);
// The local CA certifies localhost, not a Supabase name. Verification stays on.
const real=(options:any)=>postgres({...options,host:'127.0.0.1',port:p.port,username:'postgres',password:'unused-local-only',
  ssl:{...options.ssl,servername:'localhost',rejectUnauthorized:true}});
const transport=createRequestTransport({postgres:real,connectionUrl:'postgres://postgres:local-only@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',ca,sessionHost:'aws-0-eu-west-2.pooler.supabase.com'});
try{
 const receipt=await transport({input:p.input,claims:p.claims,proof:'synthetic-only-local-proof',requestId:p.request_id});
 console.log(JSON.stringify({receipt}));
}catch(e){
 const x=e as {code?:string};
 console.log(JSON.stringify({failure:'local_driver_failure',code:/^[0-9A-Z_]{1,50}$/.test(x.code||'')?x.code:null}));Deno.exitCode=1;
}
