'use strict';
// Deterministic real UI/queue execution; mocked DOM/HTTP, no browser/Auth/DB claim.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createRequire}=require('node:module');
const root=process.env.FMZ_OFFLINE_BROWSER_SOURCE||__dirname;
const candidate={exports:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'offline_shell_browser.cjs'),'utf8'),
 {module:candidate,require:createRequire(path.join(root,'offline_shell_browser.cjs')),console,URL});
const tick=()=>new Promise(resolve=>setImmediate(resolve));
for(const name of ['TimeoutError','Error','SECRET_NAME'])test(`NO_GO envelope omits raw error data: ${name}`,()=>{
 const error=Error('locator.fill: call log fill("SECRET_PASSWORD") https://SECRET_TOKEN.invalid');
 error.name=name;error.stack='SECRET_STACK';error.cause={secret:'SECRET_CAUSE'};
 error.auth_diagnostic={phase:'relogin',counter_limit:1000,saturated:false,response_counts:[]};
 const receipt=candidate.exports.failureReceipt(error,'real_auth',66);
 assert.equal(receipt.status,'NO_GO');assert.equal(receipt.checks,66);
 assert.equal(receipt.error,name==='TimeoutError'?'timeout':'browser_check_failed');
 assert.equal(JSON.stringify(receipt).includes('SECRET'),false);
 assert.equal(receipt.auth_diagnostic.phase,'relogin');
 const source=fs.readFileSync(path.join(__dirname,'offline_shell_browser.cjs'),'utf8');
 assert.match(source,/JSON\.stringify\(failureReceipt\(e,stage,checks\)\)/);
 assert.doesNotMatch(source,/error:e\.message|error:e\.stack/);
});
function deferred(){let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}
function setup(){
 const nodes=new Map(),events=new Map(),requests=[];
 function node(){return {hidden:false,value:'0',dataset:{},options:[{},{}],children:[],values:{},textContent:'',innerHTML:'',
  setAttribute(){},addEventListener(){},focus(){},replaceChildren(){this.children=[];this.textContent='';this.innerHTML='';},
  append(child){this.children.push(child);},reset(){this.values={};}};}
 const get=selector=>{if(!nodes.has(selector))nodes.set(selector,node());return nodes.get(selector);};
 get('#app').hidden=true;get('#queued').hidden=true;
 const context=vm.createContext({
  document:{querySelector:get,createElement:node,documentElement:{},body:{dataset:{}},
   addEventListener(name,handler){if(name==='DOMContentLoaded')events.set(name,handler);}},
  window:{addEventListener(){}},location:{origin:'http://127.0.0.1:8766'},
  fetch:(url,options)=>new Promise(resolve=>requests.push({url,options,resolve})),
  FormData:class{constructor(form){this.values=Object.entries(form.values);}[Symbol.iterator](){return this.values[Symbol.iterator]();}},
  crypto:require('node:crypto').webcrypto,structuredClone,console,Intl,Date,
  FMZDisplay:{caption:value=>value},FMZDraftQueue:{get:async()=>null,remove:async()=>{}}
 });
 for(const file of ['panels.js','account_center.js','ui.js','queue_ui.js'])
  vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),context,{filename:file});
 const run=code=>vm.runInContext(code,context);
 const fill=()=>{get('#login').values={email:'fixture@example.invalid',password:'fixture-only'};};
 return {get,run,requests,fill,ready:()=>events.get('DOMContentLoaded')(),
  submit:()=>get('#login').onsubmit({preventDefault(){},target:get('#login')})};
}
function response(request,status,value){request.resolve({ok:status<400,status,json:async()=>value});}

test('legacy visible-login ordering lets real bootstrap denial erase already filled credentials',async()=>{
 const h=setup();h.ready();assert.equal(h.get('#login').hidden,false);
 assert.equal(h.get('#queued').hidden,true); // Check 66 alone does not await bootstrap.
 h.fill();assert.equal(Object.keys(h.get('#login').values).length,2);
 response(h.requests[0],403,{code:'login_required'});await tick();
 assert.deepEqual(h.get('#login').values,{});
 assert.equal(h.get('#app').hidden,true);
 assert.equal(h.run('FMZQueueSession.epoch()'),1);
 assert.equal(h.requests.length,1); // No login was dispatched before the reset.
});

function controlledPage(h,{status=403}={}){
 const headers=deferred(),body=deferred(),order=[];let predicate;
 const page={
  waitForResponse(fn){order.push('observe');predicate=fn;return headers.promise;},
  async waitForFunction(fn){
   order.push('settle');
   for(let n=0;n<100;n++){if(h.run('('+fn.toString()+')()'))return;await tick();}
   throw Error('fixture_condition_not_met');
  },
  locator(selector){assert.equal(selector,'#login');return {async waitFor(){assert.equal(h.get(selector).hidden,false);order.push('visible');}}}
 };
 const observed={url:()=> 'http://127.0.0.1:8766/api/today',request:()=>({method:()=> 'GET'}),status:()=>status};
 async function navigate(){order.push('navigate');h.ready();}
 function deliverHeaders(){
  assert.ok(predicate(observed));
  assert.equal(predicate({...observed,url:()=> 'http://other.invalid/api/today'}),false);
  assert.equal(predicate({...observed,request:()=>({method:()=> 'POST'})}),false);
  h.requests[0].resolve({ok:status<400,status,json:()=>body.promise});headers.resolve(observed);
 }
 return {page,navigate,deliverHeaders,body,order};
}

for(const timing of ['before-navigation-resolves','after-navigation-resolves'])
 test(`anonymous navigation waits for processed bootstrap before filling: ${timing}`,async()=>{
  const h=setup(),p=controlledPage(h);let settled=false;
  const navigate=async()=>{await p.navigate();if(timing==='before-navigation-resolves')p.deliverHeaders();};
  const ready=candidate.exports.anonymousNavigation(p.page,'http://127.0.0.1:8766',navigate).then(()=>{settled=true;});
  await tick();
  if(timing==='after-navigation-resolves')p.deliverHeaders();
  await tick();assert.equal(settled,false);assert.equal(h.run('FMZQueueSession.epoch()'),0);
  p.body.resolve({code:'login_required'});await ready;
  assert.deepEqual(p.order,['observe','navigate','settle','visible']);
  assert.equal(h.requests.length,1);
  h.fill();h.run("tab='account'");const submitted=h.submit();
  assert.equal(h.requests.length,2);assert.equal(h.requests[1].url,'/api/login');
  assert.deepEqual(JSON.parse(h.requests[1].options.body),{email:'fixture@example.invalid',password:'fixture-only'});
  response(h.requests[1],200,{});await tick();
  response(h.requests[2],200,{csrf:'fixture-csrf',views:[{actor:'fixture-actor',workspace:'fixture-workspace',
   role:'member',version:1,capabilities:{full_day21:false},state:{route:'A',consent:true}}]});
  await submitted;assert.equal(h.get('#app').hidden,false);
  assert.equal(h.requests.filter(r=>r.url==='/api/login').length,1);
 });

for(const status of [200,401,500])test(`unexpected anonymous bootstrap ${status} fails closed`,async()=>{
 const h=setup(),p=controlledPage(h,{status});
 const ready=candidate.exports.anonymousNavigation(p.page,'http://127.0.0.1:8766',p.navigate);
 const rejected=assert.rejects(ready,/anonymous_bootstrap_status/);
 p.deliverHeaders();p.body.resolve({code:'login_required'});await rejected;
 assert.equal(h.requests.length,1);assert.equal(p.order.includes('settle'),false);
});

test('bootstrap state wait failure is propagated without navigation or HTTP retry',async()=>{
 const h=setup(),p=controlledPage(h);
 p.page.waitForFunction=async()=>{throw Error('fixture_wait_timeout');};
 const ready=candidate.exports.anonymousNavigation(p.page,'http://127.0.0.1:8766',p.navigate);
 const rejected=assert.rejects(ready,/fixture_wait_timeout/);
 p.deliverHeaders();p.body.resolve({code:'login_required'});await rejected;
 assert.equal(p.order.filter(x=>x==='navigate').length,1);assert.equal(h.requests.length,1);
});

const {EventEmitter}=require('node:events');
function diagnosticFixture(){
 const page=new EventEmitter(),diagnostic=candidate.exports.authDiagnostics(page,'http://127.0.0.1:8766');
 const forbidden=()=>{throw Error('SECRET_ACCESS');};
 function req(url='http://127.0.0.1:8766/api/login?token=SECRET_QUERY',method='POST'){
  return {url:()=>url,method:()=>method,headers:forbidden,postData:forbidden,failure:forbidden};
 }
 function res(request,status){return {request:()=>request,status:()=>status,url:forbidden,
  headers:forbidden,body:forbidden,text:forbidden,json:forbidden};}
 return {page,diagnostic,req,res,snapshot:()=>JSON.parse(JSON.stringify(diagnostic.snapshot()))};
}
test('diagnostics retain only enum metadata and aggregate status categories',()=>{
 const h=diagnosticFixture();
 for(const status of [101,200,302,401,403,429,500,600,'SECRET_STATUS']){
  const req=h.req();h.page.emit('request',req);h.page.emit('response',h.res(req,status));
 }
 const receipt=h.snapshot(),row=receipt.response_counts[0];
 assert.deepEqual(row,{phase:'initial_login',path:'login',method:'POST',requests:9,failed:0,
  responses:{http_1xx:1,http_2xx:1,http_3xx:1,unauthorized:1,forbidden:1,http_4xx:1,http_5xx:1,invalid:2}});
 assert.equal(JSON.stringify(receipt).includes('SECRET'),false);
 assert.equal(JSON.stringify(receipt).includes('127.0.0.1'),false);
 assert.deepEqual(Object.keys(receipt).sort(),['counter_limit','phase','response_counts','saturated']);
 h.diagnostic.close();
});
test('diagnostics reject foreign origins, wrong methods and unlisted paths',()=>{
 const h=diagnosticFixture();
 for(const [url,method] of [
  ['http://foreign.invalid/api/login','POST'],['http://127.0.0.1:9999/api/login','POST'],
  ['https://127.0.0.1:8766/api/login','POST'],['http://SECRET:SECRET@127.0.0.1:8766/api/login','POST'],
  ['http://127.0.0.1:8766/api/login','GET'],['http://127.0.0.1:8766/api/today','POST'],
  ['http://127.0.0.1:8766/api/action','POST'],['http://127.0.0.1:8766/api/login/SECRET','POST'],
  ['SECRET_MALFORMED','POST']]){
  const req=h.req(url,method);h.page.emit('request',req);h.page.emit('response',h.res(req,200));
 }
 assert.deepEqual(h.snapshot().response_counts,[]);
 h.diagnostic.close();
});
test('late responses retain request phase; failed and unanswered requests stay distinct',()=>{
 const h=diagnosticFixture(),first=h.req('http://127.0.0.1:8766/api/today','GET');
 h.page.emit('request',first);h.diagnostic.phase('relogin');
 h.page.emit('response',h.res(first,403));
 const failed=h.req(),unanswered=h.req();
 h.page.emit('request',failed);h.page.emit('request',unanswered);h.page.emit('requestfailed',failed);
 // A terminal event is counted only once, without inspecting transport error strings.
 h.page.emit('requestfailed',failed);h.page.emit('response',h.res(failed,500));
 const receipt=h.snapshot();
 assert.equal(receipt.phase,'relogin');
 assert.equal(receipt.response_counts[0].phase,'initial_login');
 assert.equal(receipt.response_counts[0].responses.forbidden,1);
 assert.equal(receipt.response_counts[1].requests,2);
 assert.equal(receipt.response_counts[1].failed,1);
 assert.equal(Object.values(receipt.response_counts[1].responses).reduce((a,b)=>a+b,0),0);
 h.diagnostic.close();
});
test('diagnostics are bounded, snapshots detached, and listeners removed',()=>{
 const h=diagnosticFixture();
 for(let i=0;i<1002;i++){
  const req=h.req();h.page.emit('request',req);h.page.emit('response',h.res(req,200));
 }
 const receipt=h.diagnostic.snapshot();
 assert.equal(receipt.saturated,true);assert.equal(receipt.response_counts.length,1);
 assert.equal(receipt.response_counts[0].requests,1000);
 assert.equal(receipt.response_counts[0].responses.http_2xx,1000);
 receipt.response_counts[0].responses.http_2xx=0;
 assert.equal(h.snapshot().response_counts[0].responses.http_2xx,1000);
 assert.throws(()=>h.diagnostic.phase('SECRET_PHASE'),/^Error: diagnostic_phase$/);
 h.diagnostic.close();
 for(const event of ['request','response','requestfailed'])assert.equal(h.page.listenerCount(event),0);
 assert.throws(()=>candidate.exports.authDiagnostics(h.page,'https://SECRET.invalid'),/^Error: diagnostic_origin$/);
});
test('authChecks attaches safe phase metadata on failure and closes its listeners',async()=>{
 const page=new EventEmitter(),sentinel=Error('fixture_navigation_failure');let closed=0;
 page.waitForResponse=()=>Promise.resolve({status:()=>403});
 page.goto=async()=>{throw sentinel;};
 const context={newPage:async()=>page,on(){},route:async()=>{},close:async()=>{closed++;}};
 await assert.rejects(candidate.exports.authChecks({newContext:async()=>context},
  {url:'http://127.0.0.1:8766'},()=>{}),error=>{
   assert.equal(error,sentinel);
   assert.deepEqual(JSON.parse(JSON.stringify(error.auth_diagnostic)),
    {phase:'initial_login',counter_limit:1000,saturated:false,response_counts:[]});
   return true;
  });
 assert.equal(closed,1);
 for(const event of ['request','response','requestfailed'])assert.equal(page.listenerCount(event),0);
});
