import postgres from 'npm:postgres@3.4.7';
import {createRequestTransport} from './transport.mjs';
let text='';for await(const chunk of Deno.stdin.readable)text+=new TextDecoder().decode(chunk);
const p=JSON.parse(text);
const ca=await Deno.readTextFile(p.ca);
const real=(options:any)=>postgres({...options,host:'127.0.0.1',port:p.port,username:'postgres',password:'unused-local-only'});
const transport=createRequestTransport({postgres:real,connectionUrl:'postgres://postgres:local-only@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',ca,sessionHost:'aws-0-eu-west-2.pooler.supabase.com'});
try {
 const receipt=await transport({input:p.input,claims:p.claims,proof:'synthetic-only-local-proof',requestId:p.request_id});
 console.log(JSON.stringify({receipt}));
} catch(e) {
 const failure=e instanceof Error?e.message:'local_driver_failure';
 const code=e instanceof Error && 'code' in e?String(e.code):null;
 console.log(JSON.stringify({failure,code}));Deno.exitCode=1;
}
