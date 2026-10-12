import test from 'node:test';import assert from 'node:assert/strict';
import {createTransport,IDENTITY} from './request_transport.mjs';
const id='69000000-0000-4000-8000-000000000001';
const input={input:{op:'synthetic'},claims:{sub:id},proof:'synthetic-only',requestId:id};
function fixture(failAt,identity={identity:true,safe:true},failClose=false,disconnect=false){
 const calls=[],counts=[];let ended=0,opens=0;
 const postgres=options=>{
  opens++;assert.equal(options.fetch_types,false);assert.equal(options.prepare,false);
  assert.equal(options.ssl.rejectUnauthorized,true);assert.equal(options.connect_timeout,5);
  assert.equal(options.connection.statement_timeout,5000);
  return {unsafe:async(q)=>{
   calls.push(q);
   if([failAt].flat().includes(counts.at(-1))){if(disconnect)options.onclose();throw Error('secret-not-to-log');}
   if(q===IDENTITY)return [identity];
   return q.includes('.call(')?[{value:{ok:true}}]:[];
  },end:async()=>{ended++;if(failClose)throw Error('secret-close');},
  reserve:()=>assert.fail('reserve forbidden'),begin:()=>assert.fail('implicit begin forbidden')};
 };
 const transport=createTransport({postgres,onCommand:p=>counts.push(p),
  connectionUrl:'postgres://postgres:synthetic@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',
  ca:'-----BEGIN CERTIFICATE----- synthetic',sessionHost:'aws-0-eu-west-2.pooler.supabase.com'});
 return {transport,calls,counts,get ended(){return ended;},get opens(){return opens;}};
}
test('six SQL commands; separately committed seal; no reserve or implicit begin',async()=>{
 const r=fixture();assert.deepEqual(await r.transport(input),{ok:true});
 assert.deepEqual(r.counts,['begin','identity','binding','call','commit','seal']);
 assert.equal(r.calls[0],'BEGIN');assert.equal(r.calls[4],'COMMIT');
 assert.equal(r.ended,1);assert.equal(r.opens,1);
});

test('call remains the primary failure when rollback and close also fail',async()=>{
 const r=fixture(['call','rollback'],undefined,true);
 await assert.rejects(r.transport(input),e=>{
  assert.equal(e.phase,'call');assert.equal(e.code,'request_transaction_unconfirmed');
  assert.deepEqual(e.cleanupFailures,[{phase:'rollback',code:'rollback_unconfirmed'},
   {phase:'close',code:'connection_close_unconfirmed'}]);
  assert.ok(!JSON.stringify(e).includes('secret'));return true;
 });
 assert.equal(r.ended,1);assert.equal(r.opens,1);
 await assert.rejects(r.transport(input),/transport_closed_or_busy/);
});
test('confirmed commit with failed seal retains seal phase despite close failure',async()=>{
 const r=fixture('seal',undefined,true);
 await assert.rejects(r.transport(input),e=>e.phase==='seal'&&e.code==='committed_seal_unconfirmed'&&e.cleanupFailures[0].phase==='close');
 assert.ok(!r.calls.includes('ROLLBACK'));
});
test('close failure after a sealed action is never reported as success',async()=>{
 const r=fixture(undefined,undefined,true);
 await assert.rejects(r.transport(input),e=>e.phase==='close'&&e.code==='connection_close_unconfirmed');
 assert.equal(r.counts.at(-1),'seal');assert.equal(r.ended,1);
});
test('lost socket cannot reconnect for rollback or repeat a request',async()=>{
 const r=fixture('call',undefined,false,true);
 await assert.rejects(r.transport(input),e=>e.phase==='call'&&e.cleanupFailures[0].code==='rollback_unconfirmed');
 assert.ok(!r.calls.includes('ROLLBACK'));assert.equal(r.ended,1);
 await assert.rejects(r.transport(input),/transport_closed_or_busy/);assert.equal(r.opens,1);
});
for(const p of ['begin','identity','binding','call','commit','seal'])test('fails once at '+p,async()=>{
 const r=fixture(p);await assert.rejects(r.transport(input),e=>e.phase===p&&!e.message.includes('secret'));
 assert.equal(r.ended,1);assert.equal(r.opens,1);
 assert.equal(r.calls.includes('ROLLBACK'),p!=='seal');
 if(p!=='seal')assert.ok(!r.counts.includes('seal'));
 await assert.rejects(r.transport(input),/transport_closed_or_busy/);assert.equal(r.opens,1);
});
for(const identity of [{identity:false,safe:true},{identity:true,safe:false}])
test('wrong database or unsafe parameter logging stops before claims',async()=>{
 const r=fixture(undefined,identity);await assert.rejects(r.transport(input),/request_database_guard/);
 assert.ok(!r.counts.includes('binding'));assert.equal(r.calls.at(-1),'ROLLBACK');
});
