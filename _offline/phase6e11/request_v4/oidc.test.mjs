import test from 'node:test';
import assert from 'node:assert/strict';
import {verifyCI,ISSUER,AUDIENCE} from './oidc.mjs';
const now=1800000000000;
const expected={sha:'a'.repeat(40),run:'123',expires:now/1000+600};
const pair=await crypto.subtle.generateKey({name:'RSASSA-PKCS1-v1_5',modulusLength:2048,
 publicExponent:new Uint8Array([1,0,1]),hash:'SHA-256'},true,['sign','verify']);
const key={...await crypto.subtle.exportKey('jwk',pair.publicKey),kid:'test',use:'sig'};
const enc=x=>Buffer.from(JSON.stringify(x)).toString('base64url');
const base={iss:ISSUER,aud:AUDIENCE,sub:'repo:Yourizorge@292557331/fitmetzorge-staging@1330119916:ref:refs/heads/main',
 repository_id:'1330119916',repository_owner_id:'292557331',
 repository:'Yourizorge/fitmetzorge-staging',ref:'refs/heads/main',event_name:'workflow_dispatch',sha:expected.sha,
 run_id:'123',run_attempt:'1',workflow_ref:'Yourizorge/fitmetzorge-staging/.github/workflows/phase6e11-proof.yml@refs/heads/main',
 exp:now/1000+300,iat:now/1000,nbf:now/1000};
async function token(overrides={}){
 const message=enc({alg:'RS256',kid:'test'})+'.'+enc({...base,...overrides});
 const signature=await crypto.subtle.sign('RSASSA-PKCS1-v1_5',pair.privateKey,new TextEncoder().encode(message));
 return 'Bearer '+message+'.'+Buffer.from(signature).toString('base64url');
}
const options={now:()=>now,fetcher:async url=>{
 assert.equal(url,ISSUER+'/.well-known/jwks');return Response.json({keys:[key]});}};
test('signed exact run admitted without application claims',async()=>{
 assert.deepEqual(await verifyCI(await token(),expected,options),{run:'123',sha:expected.sha,verified:true});
});
for(const [name,value] of Object.entries({aud:'other',iss:'other',sub:'other',repository:'other',ref:'refs/heads/other',
 event_name:'pull_request',sha:'b'.repeat(40),run_id:'124',run_attempt:'2',workflow_ref:'other',exp:now/1000,
 nbf:now/1000+1,iat:now/1000+1,repository_id:'1',repository_owner_id:'1'}))test('reject '+name,async()=>{
 await assert.rejects(verifyCI(await token({[name]:value}),expected,options),/ci_authorization_denied/);
});
test('reject forged signature',async()=>{
 const t=await token();await assert.rejects(verifyCI(t.slice(0,-5)+'xxxxx',expected,options),/denied/);
});
test('reject expired deployment',async()=>{
 await assert.rejects(verifyCI(await token(),{...expected,expires:now/1000},options),/denied/);
});
test('reject missing auth',async()=>{await assert.rejects(verifyCI(null,expected,options),/denied/);});
