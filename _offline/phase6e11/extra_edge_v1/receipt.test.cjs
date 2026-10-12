'use strict';
const {test}=require('node:test'),a=require('node:assert/strict'),{validate}=require('./receipt.cjs');
function fixture(){
  const steps=[['dns_resolution','entered'],['readonly_begin','requested'],['tcp_connection','entered'],
    ['tls_upgrade','entered'],['tls_handshake','entered'],['pooler_or_postgres_authentication','entered'],
    ['readonly_begin','confirmed'],['readonly_guard','requested'],['readonly_guard','confirmed'],
    ['readonly_identity','requested'],['readonly_identity','confirmed'],['rollback','requested'],['rollback','confirmed']];
  return [{result:{status:'EDGE_READONLY_CONNECTION_PASS',application_writes:0,auth_calls:0,secrets_returned:false,
    transport:{tcp:true,tls:true,authenticated:true,readonly:true,bound:true,rollback:true,ended:true,explicit_handshake:true,
      phase:'metadata_complete',transport_phase:'pooler_or_postgres_authentication',code:null,failure:null,
      attempts:1,commands:4,driver:'deno_native_3_4_7',mode:'session_ipv4',elapsed_ms:14,
      events:steps.map(([phase,state],ms)=>({phase,state,ms}))}}},
    {temporary_function_http:404,jit:{state:'disabled',mappings:0},application_writes:0,auth_calls:0}];
}
test('complete connection does not release workflow, owner window, 12 or 21',()=>{
  const v=validate(...fixture());a.equal(v.connection,'HOSTED_READONLY_PASS');
  for(const k of ['workflowAllowed','ownerWindowAllowed','phase12ServerAllowed','phase21Accepted'])a.equal(v[k],false);
});
for(const field of ['tcp','tls','authenticated','readonly','bound','rollback','ended','explicit_handshake'])
test('reject absent '+field,()=>{const [r,c]=fixture();r.result.transport[field]=false;a.throws(()=>validate(r,c));});
for(const [field,value]of [['attempts',2],['commands',5],['code','DEADLINE'],['failure',{}],['mode','transaction_ipv4'],
 ['driver','unknown'],['elapsed_ms',15000],['phase','readonly_begin']])
test('reject altered '+field,()=>{const [r,c]=fixture();r.result.transport[field]=value;a.throws(()=>validate(r,c));});
test('missing confirmation fails',()=>{const [r,c]=fixture();r.result.transport.events.splice(8,1);a.throws(()=>validate(r,c));});
test('reordered SQL fails',()=>{const [r,c]=fixture();const e=r.result.transport.events;[e[7].phase,e[9].phase]=[e[9].phase,e[7].phase];a.throws(()=>validate(r,c));});
test('non-monotonic timing fails',()=>{const [r,c]=fixture();r.result.transport.events[9].ms=0;a.throws(()=>validate(r,c));});
test('raw output field fails',()=>{const [r,c]=fixture();r.result.transport.events[0].message='synthetic-only';a.throws(()=>validate(r,c));});
for(const field of ['application_writes','auth_calls'])test('reject '+field,()=>{const [r,c]=fixture();r.result[field]=1;a.throws(()=>validate(r,c));});
test('diagnostic still exists fails',()=>{const [r,c]=fixture();c.temporary_function_http=200;a.throws(()=>validate(r,c));});
test('live JIT fails',()=>{const [r,c]=fixture();c.jit={state:'enabled',mappings:1};a.throws(()=>validate(r,c));});
