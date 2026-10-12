import postgres from 'https://deno.land/x/postgresjs@v3.4.7/mod.js';
import {createTransport} from './request_transport.mjs';
let text='';for await(const chunk of Deno.stdin.readable)text+=new TextDecoder().decode(chunk);
const p=JSON.parse(text);
if(!Number.isSafeInteger(p.port)||p.port<56110||p.port>=56140)throw Error('local_port_only');
const ca=await Deno.readTextFile(p.ca);
const real=(options:any)=>postgres({...options,host:'127.0.0.1',port:p.port,username:'postgres',
 password:'unused-local-only',ssl:{caCerts:[ca],hostname:'127.0.0.1'}});
const commands:string[]=[];
const transport=createTransport({postgres:real,onCommand:(phase:string)=>{commands.push(phase);console.error(JSON.stringify({phase}));},
 connectionUrl:'postgres://postgres:synthetic@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',
 ca,sessionHost:'aws-0-eu-west-2.pooler.supabase.com'});
try{
 const receipt=await transport({input:p.input,claims:p.claims,proof:'synthetic-only-local-proof',requestId:p.request_id});
 if(JSON.stringify(commands)!==JSON.stringify(['begin','identity','binding','call','commit','seal']))throw Error('command_shape');
 console.log(JSON.stringify({receipt,commands:commands.length,driver:'native',separate_seal:true}));
}catch(e){
 const x=e as {phase?:string,code?:string};
 console.log(JSON.stringify({status:'NO_GO',phase:x.phase||'local_driver',code:x.code||'local_driver_failure',commands:commands.length}));
 Deno.exitCode=1;
}
