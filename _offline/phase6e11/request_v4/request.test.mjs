import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequestHandler} from './handler.mjs';
import {createRequestTransport} from './transport.mjs';
import {BASE} from '../edge_bridge_v2/handler.mjs';
const uid='64000000-0000-4000-8000-000000000001',sid='64000000-0000-4000-8000-000000000101';
const command={op:'command',window:uid,workspace:uid,key:uid,expected:0,action:'propose',data:{}};
const claims={sub:uid,session_id:sid,iss:BASE+'/auth/v1',aud:'authenticated',role:'authenticated',exp:2000000000};
const enc=x=>Buffer.from(JSON.stringify(x)).toString('base64url');
const token='Bearer '+enc({alg:'ES256'})+'.'+enc(claims)+'.c3ludGhldGlj';
const proof='synthetic-local-proof';
const req=id=>new Request(BASE,{method:'POST',headers:{Authorization:token,...(id?{'x-fmz6e11-request-id':id}:{})},body:JSON.stringify(command)});
function handler(authStatus=200){
 const state={auth:0,native:[]};
 const h=createRequestHandler({url:BASE,key:'synthetic-public',proof,now:()=>1800000000000,
  fetcher:async()=>{state.auth++;return Response.json({id:uid,email:'zorgeyouri+6e9-a-lid@gmail.com'},{status:authStatus});},
  transport:async args=>{state.native.push(args);return {status:'ok'};}});
 return {h,state};
}
test('request ID is distinct from idempotency key and freshly generated per request',async()=>{
 const {h,state}=handler();assert.equal((await h(req())).status,200);assert.equal((await h(req())).status,200);
 assert.equal(state.auth,2);assert.equal(state.native[0].input.key,uid);
 assert.notEqual(state.native[0].requestId,uid);assert.notEqual(state.native[0].requestId,state.native[1].requestId);
});
test('valid request ID is retained, malformed ID rejected before Auth',async()=>{
 const {h,state}=handler();assert.equal((await h(req(sid))).status,200);assert.equal(state.native[0].requestId,sid);
 assert.equal((await h(req('not-a-uuid'))).status,400);assert.equal(state.auth,1);
});
test('Auth server rejection cannot reach native transport',async()=>{
 const {h,state}=handler(401);assert.equal((await h(req())).status,401);assert.equal(state.native.length,0);
});
function driver(failure){
 const state={commits:0,rollbacks:0,ends:0,queries:[]};
 const postgres=()=>({begin:async fn=>{try{const v=await fn({unsafe:async(q,p)=>{
  state.queries.push(q);if(q.includes('pg_stat_ssl'))return [{identity:true,safe:true}];
  if(q.includes('.call(')){if(failure==='mutation')throw Error('local_fault');return [{value:{status:'ok'}}];}
  if(q.includes('.seal(')&&failure==='seal')throw Error('local_fault');return [];
 }});state.commits++;return v;}catch(e){state.rollbacks++;throw e;}},end:async()=>{state.ends++;}});
 const transport=createRequestTransport({postgres,connectionUrl:'postgres://postgres:synthetic@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres',
 ca:'-----BEGIN CERTIFICATE-----\nlocal\n-----END CERTIFICATE-----',sessionHost:'aws-0-eu-west-2.pooler.supabase.com'});
 return {state,transport};
}
const context={input:command,claims,proof,requestId:sid};
test('intent/mutation in first transaction; durable pair seal in second',async()=>{
 const {state,transport}=driver();await transport(context);assert.equal(state.commits,2);assert.equal(state.ends,1);
 assert(state.queries.findIndex(q=>q.includes('.call('))<state.queries.findIndex(q=>q.includes('.seal(')));
 assert(state.queries.every(q=>!q.includes(proof)&&!q.includes(token)));
});
test('failed mutation rolls back, never seals and never retries',async()=>{
 const {state,transport}=driver('mutation');await assert.rejects(transport(context));
 assert.equal(state.commits,0);assert.equal(state.rollbacks,1);assert.equal(state.ends,1);
 assert(!state.queries.some(q=>q.includes('.seal(')));
});
test('lost seal is not claimed successful or automatically retried',async()=>{
 const {state,transport}=driver('seal');await assert.rejects(transport(context));
 assert.equal(state.commits,1);assert.equal(state.rollbacks,1);assert.equal(state.ends,1);
 assert.equal(state.queries.filter(q=>q.includes('.call(')).length,1);
 assert.equal(state.queries.filter(q=>q.includes('.seal(')).length,1);
});
