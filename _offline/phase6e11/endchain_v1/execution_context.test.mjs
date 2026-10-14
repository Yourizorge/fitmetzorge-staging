import test from 'node:test';
import assert from 'node:assert/strict';
import {executionContext,AUTH_ORIGIN} from './execution_context.mjs';
import {EMAILS} from '../controller_v1/auth.mjs';
function config(environment='disposable_ci'){
 const ids=Object.fromEntries(Object.keys(EMAILS).map((r,i)=>[r,`69000000-0000-4000-8000-${String(i+1).padStart(12,'0')}`]));
 return {mode:'registered_synthetic',environment,authBase:environment==='disposable_ci'?'http://127.0.0.1:59999':AUTH_ORIGIN+'/auth/v1',ids,
  identityBinding:{project:'mokxyyullfhkfalopbzd',preexisting:true,identities:Object.fromEntries(Object.keys(ids).map(role=>[role,{id:ids[role],email:EMAILS[role],registered:true}]))}};
}
test('local and staging adapters use only the exact bound Auth origin',async()=>{
 for(const environment of ['disposable_ci','staging']){
  const c=config(environment),calls=[];const x=executionContext(c,async(...v)=>{calls.push(v);return {status:200};});
  await x.fetcher(AUTH_ORIGIN+'/auth/v1/user',{method:'GET'});
  assert.equal(calls[0][0],c.authBase+'/user');assert.equal(calls[0][1].redirect,'error');
  assert.ok(calls[0][1].signal instanceof AbortSignal);
 }
});
test('registered execution cannot create/delete accounts, follow redirects, or send to another service',async()=>{
 let calls=0;const x=executionContext(config(),async()=>{calls++;});
 for(const u of ['/admin/users','/admin/users/abc','/signup','/recover','/otp','/settings','/token?grant_type=password','/user?secret=x'])
  await assert.rejects(x.fetcher(AUTH_ORIGIN+'/auth/v1'+u));
 for(const u of ['https://example.com/auth/v1/user',AUTH_ORIGIN+'/rest/v1/user',AUTH_ORIGIN+'/auth/v1/user#x'])
  await assert.rejects(x.fetcher(u));
 assert.equal(calls,0);
});
test('missing, different, duplicate or unregistered identity fails before network',()=>{
 const mutations=[c=>delete c.ids.a_member,c=>c.ids.b_member=c.ids.a_member,
  c=>c.identityBinding.preexisting=false,c=>c.identityBinding.identities.a_member.email='different@example.invalid',
  c=>c.identityBinding.identities.a_member.registered=false,c=>c.identityBinding.project='other',
  c=>c.environment='production',c=>c.authBase='http://localhost:59999'];
 for(const mutate of mutations){const c=config();mutate(c);assert.throws(()=>executionContext(c));}
});
