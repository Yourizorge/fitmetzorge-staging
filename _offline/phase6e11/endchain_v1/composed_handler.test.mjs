import test from 'node:test';
import assert from 'node:assert/strict';
import {createComposedHandler} from './composed_handler.mjs';
import {BASE} from '../edge_bridge_v2/handler.mjs';
import {data} from '../edge/core.mjs';
const id=n=>'69000000-0000-4000-8000-'+String(n).padStart(12,'0');
const user={id:id(1),email:'zorgeyouri+6e9-b-lid@gmail.com'};
const b64=x=>Buffer.from(JSON.stringify(x)).toString('base64url');
const token=b64({alg:'HS256',typ:'JWT'})+'.'+b64({sub:user.id,session_id:id(2),exp:9999999999,
 role:'authenticated',aud:'authenticated',iss:BASE+'/auth/v1'})+'.synthetic_signature';
const command={op:'command',window:id(3),workspace:id(4),key:id(5),expected:2,action:'b_build',data:{}};
const row={route:'B',seed:Object.keys(data.seeds)[0],events:[],consent:true,guard:'clear',actor_role:'member',
 revision:1,basis:{model:'1993a8073f40c583f108cc6baa2ef78c1d522d52b81b0f6071f10f109ca4753b'}};
function setup(auth=200,failRead=false){
 const calls=[];
 const handler=createComposedHandler({key:'synthetic',proof:'private_proof',transport:{
  read:async args=>{calls.push({kind:'read',args});if(failRead)throw Error('postgres://secret');return {b_row:row};},
  invoke:async args=>{calls.push({kind:'invoke',args});return {status:'confirmed'};}
 },fetcher:async(url)=>{calls.push({kind:'auth',url});assert.equal(url,BASE+'/auth/v1/user');return Response.json(user,{status:auth});}});
 const send=(body=command,headers={Authorization:'Bearer '+token})=>handler(new Request('https://synthetic.invalid',{method:'POST',headers:{...headers,'Content-Type':'application/json','x-fmz6e11-request-id':id(6)},body:JSON.stringify(body)}));
 return {send,calls};
}
test('existing B handler verifies Auth, reads bound state, then computes and mutates',async()=>{
 const f=setup(),r=await f.send();assert.equal(r.status,200);
 assert.deepEqual(f.calls.map(x=>x.kind),['auth','read','invoke']);
 const [read,write]=f.calls.slice(1).map(x=>x.args);
 assert.equal(read.requestId,id(6));assert.equal(write.requestId,id(6));
 assert.deepEqual(read.claims,write.claims);assert.equal(write.input.op,'internal_b');
 assert.equal(write.input.computed.error,undefined);assert.equal(write.input.computed.row_revision,1);
});
test('A command has no extra B read or Data API request',async()=>{
 const f=setup();assert.equal((await f.send({...command,action:'propose'})).status,200);
 assert.deepEqual(f.calls.map(x=>x.kind),['auth','invoke']);
});
test('Auth rejection cannot reach either database path',async()=>{
 const f=setup(401);assert.equal((await f.send()).status,401);assert.equal(f.calls.length,1);
});
test('anonymous request never reaches Auth or SQL',async()=>{
 const f=setup();assert.equal((await f.send(command,{})).status,401);assert.equal(f.calls.length,0);
});
test('failed read stops before mutation without exposing transport error',async()=>{
 const f=setup(200,true),r=await f.send();assert.equal(r.status,503);
 assert.deepEqual(f.calls.map(x=>x.kind),['auth','read']);assert.ok(!(await r.text()).includes('secret'));
});
test('client proof injection remains denied',async()=>{
 const f=setup();const r=await f.send(command,{Authorization:'Bearer '+token,'x-fmz6e11-proof':'attacker'});
 assert.equal(r.status,400);assert.equal(f.calls.length,0);
});

for(const phase of ['call','commit','seal'])test('mutation failure retains server-only phase: '+phase,async()=>{
 const failures=[],handler=createComposedHandler({key:'synthetic',proof:'private_proof',
  transport:{read:async()=>({b_row:row}),invoke:async()=>{
   const error=new Error('postgres://secret');error.phase=phase;error.code='request_transaction_unconfirmed';throw error;
  }},fetcher:async()=>Response.json(user),onFailure:x=>failures.push(x)});
 const response=await handler(new Request('https://synthetic.invalid',{method:'POST',headers:{
  Authorization:'Bearer '+token,'Content-Type':'application/json','x-fmz6e11-request-id':id(6)},
  body:JSON.stringify({...command,action:'propose'})}));
 assert.equal(response.status,503);
 assert.deepEqual(failures,[{phase,code:'request_transaction_unconfirmed'}]);
 assert.ok(!(await response.text()).includes('secret'));
});
