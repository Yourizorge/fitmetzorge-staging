'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'offline_sw.js'),'utf8');
function worker({online=false,cached=new Response('generic shell'),network=async()=>new Response('network root')}={}){
 const handlers={},calls={fetch:0,cache:0,match:0};
 const context=vm.createContext({URL,Map,Response,
  self:{location:{origin:'http://127.0.0.1:12345'},navigator:{onLine:online},addEventListener:(name,fn)=>{handlers[name]=fn;}},
  fetch:async(...args)=>{calls.fetch++;return network(...args);},
  caches:{open:async name=>{assert.equal(name,'fmz-local-offline-shell-v1');calls.cache++;return {match:async key=>{assert.equal(key,'/offline_shell.html');calls.match++;return cached;}};}}
 });
 vm.runInContext(source,context);
 const request=(overrides={})=>{let result;handlers.fetch({request:{url:'http://127.0.0.1:12345/',method:'GET',mode:'navigate',...overrides},respondWith:value=>{result=value;}});return result;};
 return {calls,request};
}
test('offline root never fetches even if the network would return account HTML',async()=>{
 const w=worker();assert.equal(await (await w.request()).text(),'generic shell');assert.deepEqual(w.calls,{fetch:0,cache:1,match:1});
});
test('missing offline shell fails closed without trying network',async()=>{
 const w=worker({cached:null});assert.equal((await w.request()).type,'error');assert.equal(w.calls.fetch,0);
});
test('online root remains network-first and is never cached',async()=>{
 const w=worker({online:true});assert.equal(await (await w.request()).text(),'network root');assert.deepEqual(w.calls,{fetch:1,cache:0,match:0});
});
for(const network of [async()=>{throw Error('disconnected');},async()=>new Response('',{status:503})])test('online hint cannot prevent generic fallback on actual network failure',async()=>{
 const w=worker({online:true,network});assert.equal(await (await w.request()).text(),'generic shell');assert.equal(w.calls.fetch,1);assert.equal(w.calls.match,1);
});
for(const request of [{url:'http://127.0.0.1:12345/?probe=1'},{url:'http://127.0.0.1:12345/api/today'},{url:'http://127.0.0.1:12345/ui.js'},{url:'http://127.0.0.1:12345/account_center.js'},{method:'POST'},{mode:'cors'},{url:'http://other.invalid/'}])test(`offline fallback excludes ${JSON.stringify(request)}`,()=>{
 const w=worker();assert.equal(w.request(request),undefined);assert.deepEqual(w.calls,{fetch:0,cache:0,match:0});
});
