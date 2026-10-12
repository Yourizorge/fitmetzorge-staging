import test from 'node:test';
import assert from 'node:assert/strict';
import {verifyCI,ISSUER,AUDIENCE} from './oidc.mjs';
const now=1791801900000,epoch=now/1000;
const g={project:'mokxyyullfhkfalopbzd',id:'65000000-0000-4000-8000-000000000001',sha:'a'.repeat(40),run:'123',manifest_sha:'b'.repeat(64),starts:now,expires:now+600000};
const pair=await crypto.subtle.generateKey({name:'RSASSA-PKCS1-v1_5',modulusLength:2048,publicExponent:new Uint8Array([1,0,1]),hash:'SHA-256'},true,['sign','verify']);
const jwk={...await crypto.subtle.exportKey('jwk',pair.publicKey),kid:'local-test',use:'sig'};
const base={iss:ISSUER,aud:AUDIENCE,sub:'repo:Yourizorge@292557331/fitmetzorge-staging@1330119916:ref:refs/heads/main',
 repository:'Yourizorge/fitmetzorge-staging',repository_id:'1330119916',repository_owner_id:'292557331',ref:'refs/heads/main',
 event_name:'workflow_dispatch',sha:g.sha,run_id:'123',run_attempt:'1',
 workflow_ref:'Yourizorge/fitmetzorge-staging/.github/workflows/phase6e11-controller.yml@refs/heads/main',
 iat:epoch,nbf:epoch,exp:epoch+300};
const b64=x=>Buffer.from(typeof x==='string'?x:JSON.stringify(x)).toString('base64url');
async function token(changes={},head={}){
 const data=b64({alg:'RS256',kid:'local-test',...head})+'.'+b64({...base,...changes});
 return 'Bearer '+data+'.'+Buffer.from(await crypto.subtle.sign('RSASSA-PKCS1-v1_5',pair.privateKey,new TextEncoder().encode(data))).toString('base64url');
}
const fetcher=async(url,options)=>{assert.equal(url,ISSUER+'/.well-known/jwks');assert.equal(options.redirect,'error');return Response.json({keys:[jwk]});};
test('real signature verification for exact new controller grant',async()=>assert.equal((await verifyCI(await token(),g,{now:()=>now,fetcher})).verified,true));
for(const change of [{aud:'fmz6e11-mokxyyullfhkfalopbzd-proof'},{iss:'other'},{repository:'other'},{repository_id:'1'},
 {repository_owner_id:'1'},{sub:'other'},{ref:'refs/heads/other'},{sha:'c'.repeat(40)},{run_id:'124'},{run_attempt:'2'},
 {event_name:'pull_request'},{workflow_ref:'Yourizorge/fitmetzorge-staging/.github/workflows/phase6e11-proof.yml@refs/heads/main'},
 {exp:epoch},{exp:epoch+601},{nbf:epoch+1},{iat:epoch+1}])
test('signed but wrong '+Object.keys(change),async()=>assert.rejects(verifyCI(await token(change),g,{now:()=>now,fetcher}),/ci_authorization_denied/));
for(const head of [{alg:'none'},{alg:'HS256'},{jku:'https://invalid.example'},{x5u:'https://invalid.example'}])
test('untrusted header '+Object.keys(head),async()=>assert.rejects(verifyCI(await token({},head),g,{now:()=>now,fetcher}),/ci_authorization_denied/));
test('modified signature denied',async()=>{
 const t=await token();await assert.rejects(verifyCI(t.slice(0,-5)+'abcde',g,{now:()=>now,fetcher}),/ci_authorization_denied/);
});
test('key fetch failure closed without retry',async()=>{
 let calls=0;await assert.rejects(verifyCI(await token(),g,{now:()=>now,fetcher:async()=>{calls++;throw Error('secret');}}));assert.equal(calls,1);
});
