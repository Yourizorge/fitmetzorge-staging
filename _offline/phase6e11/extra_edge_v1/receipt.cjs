'use strict';
// Offline receipt consistency only, not an authentication or deployment API.
const assert=require('node:assert/strict');
const commands=['readonly_begin','readonly_guard','readonly_identity','rollback'];
const physical=['dns_resolution','tcp_connection','tls_upgrade','tls_handshake','pooler_or_postgres_authentication'];
function validate(receipt,closure){
  const r=receipt.result,t=r?.transport;
  assert.equal(r?.status,'EDGE_READONLY_CONNECTION_PASS');
  assert.equal(r.application_writes,0);assert.equal(r.auth_calls,0);assert.equal(r.secrets_returned,false);
  for(const k of ['tcp','tls','authenticated','readonly','bound','rollback','ended','explicit_handshake'])assert.equal(t?.[k],true,k);
  assert.equal(t.phase,'metadata_complete');assert.equal(t.transport_phase,physical.at(-1));
  assert.equal(t.code,null);assert.equal(t.failure,null);
  assert.equal(t.attempts,1);assert.equal(t.commands,4);
  assert.equal(t.driver,'deno_native_3_4_7');assert.equal(t.mode,'session_ipv4');
  assert(Number.isSafeInteger(t.elapsed_ms)&&t.elapsed_ms>0&&t.elapsed_ms<=14000);
  assert.equal(t.events.length,13);let last=-1;
  for(const event of t.events){
    assert.deepEqual(Object.keys(event).sort(),['ms','phase','state']);
    assert(Number.isSafeInteger(event.ms)&&event.ms>=last&&event.ms<=t.elapsed_ms);last=event.ms;
    assert((event.state==='entered'&&physical.includes(event.phase))||
      (['requested','confirmed'].includes(event.state)&&commands.includes(event.phase)));
  }
  assert.deepEqual(t.events.filter(x=>x.state==='entered').map(x=>x.phase),physical);
  const events=t.events.filter(x=>x.state!=='entered');
  assert.deepEqual(events.map(x=>[x.phase,x.state]),commands.flatMap(x=>[[x,'requested'],[x,'confirmed']]));
  const index=(phase,state)=>t.events.findIndex(x=>x.phase===phase&&x.state===state);
  assert(index('tls_handshake','entered')<index('pooler_or_postgres_authentication','entered'));
  assert(index('pooler_or_postgres_authentication','entered')<index('readonly_begin','confirmed'));
  assert.equal(closure.temporary_function_http,404);
  assert.deepEqual(closure.jit,{state:'disabled',mappings:0});
  assert.equal(closure.application_writes,0);assert.equal(closure.auth_calls,0);
  return {connection:'HOSTED_READONLY_PASS',diagnosticClosed:true,workflowAllowed:false,
    ownerWindowAllowed:false,phase12ServerAllowed:false,phase21Accepted:false,
    remaining:['bounded_mutating_controller_authority','hosted_Auth','request_audit_pairs',
      'Route_A_B','protected_preservation','synthetic_cleanup','current_dry_run']};
}
module.exports={validate};
