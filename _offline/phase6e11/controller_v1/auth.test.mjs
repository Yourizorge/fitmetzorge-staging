import test from 'node:test';
import assert from 'node:assert/strict';
import {SyntheticAuth,EMAILS} from './auth.mjs';
import {metadata} from './core.mjs';
const id=n=>'65200000-0000-4000-8000-'+String(n).padStart(12,'0'),now=1791801900000;
const expected={id:id(1),role:'a_member',trainer_id:id(2)};
const identity={id:id(1),email:EMAILS.a_member,registered_role:'a_member',profile_role:'client',trainer_id:id(2),enabled:true,operator:false};
const b64=o=>Buffer.from(JSON.stringify(o)).toString('base64url');
const jwt=(sub=id(1),session=id(10))=>b64({alg:'HS256'})+'.'+b64({sub,session_id:session,iss:'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1',aud:'authenticated',role:'authenticated',exp:now/1000+3600})+'.LOCAL_FAKE_SIGNATURE';
const user={id:id(1),email:EMAILS.a_member};
function rig({changeIdentity={},changeExpected={},responseTransform=x=>x,failPath=null}={}){
 const calls=[];let refresh=0;
 const fetcher=async(url,opt)=>{
  assert.equal(new URL(url).origin,'https://mokxyyullfhkfalopbzd.supabase.co');assert.equal(opt.redirect,'error');
  const path=new URL(url).pathname+new URL(url).search;
  const body=opt.body?JSON.parse(opt.body):null;calls.push({path,method:opt.method,body,headers:opt.headers});
  if(path===failPath)throw Error('postgres://private-value@host');
  let value;
  if(path.endsWith('/admin/generate_link')){assert.equal(opt.headers.apikey,'admin-private');assert.deepEqual(body,{type:'magiclink',email:EMAILS.a_member});value={...user,hashed_token:'link-private'};}
  else if(path.endsWith('/verify')){assert.deepEqual(body,{type:'magiclink',token_hash:'link-private'});value={user,access_token:jwt(),refresh_token:'refresh-private-1'};}
  else if(path.endsWith('/user'))value=user;
  else if(path.endsWith('/token?grant_type=refresh_token')){assert.deepEqual(body,{refresh_token:'refresh-private-1'});refresh++;value={user,access_token:jwt(),refresh_token:'refresh-private-2'};}
  else if(path.endsWith('/logout?scope=local'))return new Response(null,{status:204,headers:{'x-request-id':id(90)}});
  else assert.fail('unregistered_auth_path');
  return Response.json(responseTransform(value,path),{headers:{'x-request-id':id(90)}});
 };
 return {calls,auth:new SyntheticAuth({expected:{...expected,...changeExpected},identity:{...identity,...changeIdentity},key:'anon-fixture',admin:'admin-private',fetcher,now:()=>now,
   guard:async(_identity,action)=>action()}),get refresh(){return refresh;}};
}
test('complete synthetic Auth lifecycle returns metadata only and local logout',async()=>{
 const r=rig(),proof=[];
 for(const op of ['issue','verify','getUser','refresh','getUser','logout'])proof.push(metadata(await r.auth[op]()));
 assert.equal(r.calls.length,6);assert.equal(r.refresh,1);
 const serialized=JSON.stringify(proof)+JSON.stringify(r.auth);
 for(const secret of ['admin-private','refresh-private','link-private','LOCAL_FAKE_SIGNATURE'])assert.ok(!serialized.includes(secret));
 await assert.rejects(r.auth.withToken(()=>{}),/auth_sequence/);
 assert.equal(r.calls.at(-1).path,'/auth/v1/logout?scope=local');
});
for(const changeIdentity of [{id:id(99)},{email:'unapproved@example.invalid'},{registered_role:'a_trainer'},
 {profile_role:'trainer'},{trainer_id:null},{enabled:false},{operator:true}])
test('identity mismatch '+Object.keys(changeIdentity)+' makes zero calls',()=>assert.throws(()=>rig({changeIdentity}),/identity_not_allowlisted/));
for(const changeExpected of [{id:id(99)},{role:'unknown'},{trainer_id:null}])
test('manifest identity mismatch '+Object.keys(changeExpected),()=>assert.throws(()=>rig({changeExpected}),/identity_not_allowlisted/));
test('user metadata cannot override registered role',()=>{
 assert.throws(()=>rig({changeIdentity:{registered_role:'b_member',user_metadata:{role:'a_member'}}}),/identity_not_allowlisted/);
});
test('issue cannot be replayed',async()=>{const r=rig();await r.auth.issue();await assert.rejects(r.auth.issue(),/auth_sequence/);assert.equal(r.calls.length,1);});
for(const op of ['verify','getUser','refresh','logout'])
test('out of order '+op+' performs no request',async()=>{const r=rig();await assert.rejects(r.auth[op](),/auth_sequence/);assert.equal(r.calls.length,0);});
test('network failure neither retries nor leaks error',async()=>{
 const r=rig({failPath:'/auth/v1/admin/generate_link'});await assert.rejects(r.auth.issue(),e=>e.message==='auth_transport_failed');
 assert.equal(r.calls.length,1);await assert.rejects(r.auth.issue(),/auth_sequence/);
});
test('wrong issuance account fails before verification',async()=>{
 const r=rig({responseTransform:v=>({...v,id:id(99)})});await assert.rejects(r.auth.issue(),/issued_identity_mismatch/);assert.equal(r.calls.length,1);
});
for(const alteration of [{user:{id:id(99),email:EMAILS.a_member},access_token:jwt(id(99))},{access_token:jwt(id(99))},{refresh_token:null}])
test('untrusted verification result '+Object.keys(alteration),async()=>{
 const r=rig({responseTransform:(v,p)=>p.endsWith('/verify')?{...v,...alteration}:v});await r.auth.issue();await assert.rejects(r.auth.verify());
 await assert.rejects(r.auth.withToken(()=>{}));
});
test('refresh cannot silently substitute another session',async()=>{
 const r=rig({responseTransform:(v,p)=>p.includes('refresh_token')?{...v,access_token:jwt(id(1),id(11))}:v});
 await r.auth.issue();await r.auth.verify();await assert.rejects(r.auth.refresh(),/session_identity_mismatch/);
 await assert.rejects(r.auth.refresh(),/auth_sequence/);assert.equal(r.refresh,1);
});
test('clearing secrets is not a claim of server signout',async()=>{
 const r=rig();await r.auth.issue();await r.auth.verify();r.auth.clear();await assert.rejects(r.auth.withToken(()=>{}));
 assert.equal(r.calls.length,2);
});
