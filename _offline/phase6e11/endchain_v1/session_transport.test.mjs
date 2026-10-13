import test from 'node:test';
import assert from 'node:assert/strict';
import {createSessionTransport} from './session_transport.mjs';
const id=n=>'69000000-0000-4000-8000-'+String(n).padStart(12,'0');
const args={input:{op:'synthetic'},claims:{sub:id(1)},proof:'synthetic',requestId:id(2)};
function fixture(fail,guard=true,now=()=>0){
 const commands=[],queries=[],claims=[];let options,created=0,closes=0;
 const t=createSessionTransport({connectionUrl:'postgres://postgres:synthetic@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',
  ca:'-----BEGIN CERTIFICATE----- synthetic-only',sessionHost:'aws-0-eu-west-2.pooler.supabase.com',
  now,onCommand:phase=>commands.push(phase),postgres:o=>{
   options=o;created++;
   assert.equal(o.max,1);assert.equal(o.fetch_types,false);assert.equal(o.prepare,false);
   assert.equal(o.connect_timeout,5);assert.equal(o.connection.statement_timeout,5000);
   return {unsafe:async(q,p)=>{
    queries.push(q);if(fail===commands.at(-1))throw Error('postgres://secret');
    if(q.includes('as identity'))return [{identity:guard,safe:guard}];
    if(q.includes('set_config'))claims.push(p);
    if(q.includes('as locks_allowed'))return [{locks_allowed:guard}];
    return q.includes('.call(')||q.includes('.fmz6e11_call(')?[{value:{status:'confirmed'}}]:[];
   },end:async()=>{closes++;}};
  }});
 return {t,commands,queries,claims,lost:()=>options.onclose(),created:()=>created,closes:()=>closes};
}
test('one attestation, fresh claims and separate committed seal per action',async()=>{
 const f=fixture();await f.t.invoke(args);await f.t.invoke({...args,claims:{sub:id(3)},requestId:id(4)});await f.t.close();
 assert.deepEqual(f.commands,['begin','identity','binding','call','commit','seal','begin','binding','call','commit','seal']);
 assert.equal(f.created(),1);assert.equal(f.closes(),1);assert.notDeepEqual(f.claims[0],f.claims[1]);
});
test('71 normal calls use 356 commands, not 426',async()=>{
 const f=fixture();for(let i=0;i<71;i++)await f.t.invoke({...args,requestId:id(i+10)});
 assert.equal(f.commands.length,356);await f.t.close();
});
test('lost socket is final, without a reconnect or a repeated query',async()=>{
 const f=fixture();await f.t.invoke(args);f.lost();
 await assert.rejects(()=>f.t.invoke(args),/transport_closed_or_busy/);
 assert.equal(f.commands.length,6);assert.equal(f.created(),1);await f.t.close();
});
test('failed project/logging guard prevents claim transmission',async()=>{
 const f=fixture(null,false);await assert.rejects(()=>f.t.invoke(args),/request_database_guard/);
 assert.deepEqual(f.commands,['begin','identity','rollback']);assert.equal(f.claims.length,0);
});
for(const phase of ['begin','identity','binding','call','commit','seal'])test('terminal error and bounded rollback: '+phase,async()=>{
 const f=fixture(phase);await assert.rejects(()=>f.t.invoke(args),e=>e.phase===phase&&!e.message.includes('secret'));
 assert.equal(f.commands.filter(x=>x==='rollback').length,phase==='seal'?0:1);
 await assert.rejects(()=>f.t.invoke(args),/transport_closed_or_busy/);assert.equal(f.closes(),1);
});
test('explicit close is idempotent and prevents reuse',async()=>{
 const f=fixture();await f.t.close();await f.t.close();assert.equal(f.closes(),1);
 await assert.rejects(()=>f.t.invoke(args),/transport_closed_or_busy/);
});
test('concurrent invocation cannot open another session',async()=>{
 const f=fixture();const a=f.t.invoke(args);
 await assert.rejects(()=>f.t.invoke(args),/transport_closed_or_busy/);await a;await f.t.close();
 assert.equal(f.created(),1);
});
test('120-second worker bound prevents later requests without extending SQL timeouts',async()=>{
 let time=0;const f=fixture(null,true,()=>time);await f.t.invoke(args);time=120000;
 await assert.rejects(()=>f.t.invoke(args),/session_lifetime/);
 assert.equal(f.commands.filter(x=>x==='call').length,1);assert.equal(f.closes(),1);
});

const readArgs={...args,input:{op:'read',window:id(20),workspace:id(21)}};
test('Route B preparatory read counts four commands on the same bound session',async()=>{
 const f=fixture();await f.t.invoke(args);await f.t.read(readArgs);await f.t.invoke({...args,requestId:id(3)});await f.t.close();
 assert.equal(f.commands.length,15);
 assert.deepEqual(f.commands.slice(6,10),['read_begin','read_binding','read_call','rollback']);
 assert.equal(f.queries[6],'BEGIN TRANSACTION READ WRITE');assert.equal(f.created(),1);
});
test('first read attests the database before transmitting verified claims',async()=>{
 const f=fixture();await f.t.read(readArgs);await f.t.close();
 assert.deepEqual(f.commands,['read_begin','identity','read_binding','read_call','rollback']);
});
test('read transport refuses a command disguised as a read',async()=>{
 const f=fixture();await assert.rejects(()=>f.t.read(args),/read_context_missing/);
 assert.equal(f.commands.length,0);await f.t.close();
});
for(const phase of ['read_begin','read_binding','read_call','rollback'])test('read error is terminal and retains phase: '+phase,async()=>{
 const f=fixture(phase);await assert.rejects(()=>f.t.read(readArgs),e=>e.phase===phase);
 await assert.rejects(()=>f.t.invoke(args),/transport_closed_or_busy/);assert.equal(f.closes(),1);
});
