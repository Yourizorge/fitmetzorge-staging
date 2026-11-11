// In-memory HTTP framing models, never a live Auth/PG proof.
import test from 'node:test';
import assert from 'node:assert/strict';
import {completeResponse,createHttpLedger} from './runtime_http.mjs';
const origin='https://mokxyyullfhkfalopbzd.supabase.co/auth/v1';
const response=(text='{}',status=200)=>new Response(text,{status,headers:{'content-length':String(Buffer.byteLength(text))}});
const url=origin+'/verify',options={method:'POST'};

test('exact framed body consumed and original payload preserved',async()=>{
 const complete=await completeResponse(response('{"synthetic":"secret"}'));
 assert.equal(await complete.text(),'{"synthetic":"secret"}');
});
test('missing ambiguous compressed oversize and truncated bodies rejected',async()=>{
 for(const headers of [{},{'content-length':'2','transfer-encoding':'chunked'},
  {'content-length':'2','content-encoding':'gzip'},{'content-length':'65537'},
  {'content-length':'-1'},{'content-length':'02'},{'transfer-encoding':'gzip'}]){
  await assert.rejects(completeResponse(new Response('{}',{headers})),/http_/);
 }
 await assert.rejects(completeResponse(new Response('{}',{headers:{'content-length':'3'}})),/http_body_incomplete/);
});
test('chunked eof and bodyless status accepted without invented content',async()=>{
 const a=await completeResponse(new Response('{}',{headers:{'transfer-encoding':'chunked'}}));
 assert.equal(await a.text(),'{}');
 assert.equal((await completeResponse(new Response(null,{status:204}))).status,204);
});
test('headers alone never terminal and read failure retains attempted status',async()=>{
 let controller;
 const body=new ReadableStream({start(value){controller=value;}});
 const ledger=createHttpLedger(async()=>new Response(body,{headers:{'content-length':'2'}}));
 ledger.begin('a_member','verify');
 const pending=ledger.fetcher(url,options);
 await Promise.resolve();await Promise.resolve();
 assert.deepEqual(ledger.snapshot().rows[0],{ordinal:1,role:'a_member',operation:'verify',safety:false,attempted:true,terminal:false,status:200});
 const original=Error('unit truncated response');controller.error(original);
 await assert.rejects(pending,error=>error===original);
 assert.throws(()=>ledger.begin('a_member','logout',true),/http_previous_unknown/);
 ledger.seal();assert.equal(ledger.snapshot().rows[0].terminal,false);
});
test('network rejection keeps intent attempted and forbids a retry',async()=>{
 let calls=0;const original=Error('unit lost response');
 const ledger=createHttpLedger(async()=>{calls++;throw original;});
 ledger.begin('a_member','verify');
 await assert.rejects(ledger.fetcher(url,options),error=>error===original);
 await assert.rejects(ledger.fetcher(url,options),/http_intent_required/);
 assert.equal(calls,1);assert.equal(ledger.snapshot().rows[0].status,null);
});
test('route scope rejects before transport and evidence contains no credentials',async()=>{
 let calls=0;const ledger=createHttpLedger(async()=>{calls++;return response();});
 ledger.begin('a_member','verify');
 for(const target of [origin+'/user','https://example.invalid/auth/v1/verify',url+'#fragment']){
  await assert.rejects(ledger.fetcher(target,options),/http_intent_route/);
 }
 assert.equal(calls,0);
 await ledger.fetcher(url,{...options,headers:{Authorization:'Bearer unit-secret'},body:'unit-secret'});
 assert.equal(calls,1);assert.ok(!JSON.stringify(ledger.snapshot()).includes('secret'));
});
test('exact eighteen normal plus three safety calls fit unchanged bound',async()=>{
 const routes={issue:['POST','/admin/generate_link'],verify:['POST','/verify'],getUser:['GET','/user'],
  refresh:['POST','/token?grant_type=refresh_token'],logout:['POST','/logout?scope=local'],revoked_denial:['GET','/user']};
 let calls=0;const ledger=createHttpLedger(async()=>{calls++;return response();});
 for(const role of ['a_member','a_trainer','b_member'])for(const [op,[method,path]] of Object.entries(routes)){
  ledger.begin(role,op);await ledger.fetcher(origin+path,{method});
 }
 for(const role of ['a_member','a_trainer','b_member']){
  ledger.begin(role,'logout',true);await ledger.fetcher(origin+routes.logout[1],{method:'POST'});
 }
 assert.equal(calls,21);assert.throws(()=>ledger.begin('a_member','logout',true),/http_intent_scope/);
 ledger.seal();assert.ok(ledger.snapshot().sealed);
 assert.ok(ledger.snapshot().rows.every(row=>row.terminal));
 const copy=ledger.snapshot();copy.rows[0].terminal=false;
 assert.equal(ledger.snapshot().rows[0].terminal,true);
});
test('safety cannot mint and sealed ledger cannot dispatch',async()=>{
 let calls=0;const ledger=createHttpLedger(async()=>{calls++;return response();});
 assert.throws(()=>ledger.begin('a_member','verify',true),/http_intent_scope/);
 ledger.begin('a_member','verify');ledger.seal();
 await assert.rejects(ledger.fetcher(url,options),/http_intent_required/);
 assert.throws(()=>ledger.begin('a_member','logout',true),/http_intent_scope/);
 assert.equal(calls,0);
});
