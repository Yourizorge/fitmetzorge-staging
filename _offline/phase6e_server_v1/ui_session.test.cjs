'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');

// Run the real UI and queue scripts with controlled HTTP promises and no storage.
function setup(){
 const nodes=new Map(),requests=[],events=new Map(),windowEvents=new Map();
 function node(){
  let text='',html='';
  return {hidden:false,value:'0',dataset:{},options:[{},{}],children:[],attributes:{},values:{},resets:0,
   get textContent(){return text;},set textContent(value){text=value;this.children=[];},
   get innerHTML(){return html;},set innerHTML(value){html=value;this.children=[];},
   setAttribute(key,value){this.attributes[key]=value;},addEventListener(){},focus(){},
   replaceChildren(...children){text='';html='';this.children=children;},append(child){this.children.push(child);},
   reset(){this.resets++;this.values={};}};
 }
 const get=selector=>{if(!nodes.has(selector))nodes.set(selector,node());return nodes.get(selector);};
 get('#app').hidden=true;get('#logout').hidden=true;
 const context=vm.createContext({
  document:{querySelector:get,createElement:node,documentElement:{},body:{dataset:{}},
   addEventListener(name,handler,options){const list=events.get(name)||[];list.push({handler,once:options?.once});events.set(name,list);}},
  window:{addEventListener(name,handler){windowEvents.set(name,handler);}},
  location:{origin:'http://127.0.0.1:8766'},
  fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject})),
  FormData:class{constructor(form){this.values=Object.entries(form.values);}[Symbol.iterator](){return this.values[Symbol.iterator]();}},
  crypto:require('node:crypto').webcrypto,structuredClone,console,Intl,Date,
  FMZDisplay:{caption:value=>value},FMZDraftQueue:{get:async()=>null,remove:async()=>{}},
 });
 const run=code=>vm.runInContext(code,context);
 const load=file=>vm.runInContext(fs.readFileSync(path.join(__dirname,file),'utf8'),context,{filename:file});
 for(const file of ['panels.js','account_center.js','ui.js'])load(file);
 const beforeQueue=requests.length;load('queue_ui.js');
 function ready(){const list=events.get('DOMContentLoaded')||[];events.set('DOMContentLoaded',list.filter(x=>!x.once));for(const {handler} of list)handler();}
 function seed(actor,{advance=true,busy=false,pending=null,message=''}={}){
  context.nextView=view(actor);context.nextPending=pending;context.nextMessage=message;
  run(`${advance?'lockQueueSession();':''}current=nextView;views=[current];csrf='csrf-'+current.actor;queueVerified.add(current);tab='account';$('#app').hidden=false;$('#login').hidden=true;$('#logout').hidden=false;render();pendingRequest=nextPending;message(nextMessage);busy=${busy};`);
 }
 function login(actor){const form=get('#login');form.values={email:actor+'@example.invalid',password:'fixture-only'};return form.onsubmit({preventDefault(){},target:form});}
 function snapshot(){return JSON.parse(run(`JSON.stringify({actor:current?.actor,views:views.map(v=>v.actor),csrf,pendingRequest,busy,appHidden:$('#app').hidden,loginHidden:$('#login').hidden,logoutHidden:$('#logout').hidden,content:$('#content').innerHTML,title:$('#title').textContent,status:$('#status').textContent,message:$('#message').textContent,buttons:$('#message').children.length,formResets:$('#login').resets})`));}
 return {context,run,get,requests,beforeQueue,ready,seed,login,snapshot,windowEvents};
}
function view(actor){return {actor,workspace:'workspace-'+actor,role:'member',version:1,capabilities:{full_day21:false},state:{route:'A',consent:true}};}
function payload(actor='A'){return {workspace:'workspace-'+actor,request_id:'request-'+actor,version:1,request:{action:'preferences',data:{language:'nl',theme:'light',units:'metric'}}};}
function respond(request,value={},status=200){request.resolve({ok:status<400,status,json:async()=>value});}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
async function finishLogin(h,actor,requestIndex){respond(h.requests[requestIndex],{});await tick();respond(h.requests[requestIndex+1],{views:[view(actor)],csrf:'csrf-'+actor});await tick();}

test('bootstrap starts once after the queue wrapper is installed',async()=>{
 const h=setup();assert.equal(h.beforeQueue,0);assert.equal(h.requests.length,0);
 h.ready();h.ready();assert.equal(h.requests.length,1);
 respond(h.requests[0],{views:[view('A')],csrf:''});await tick();
 assert.equal(h.snapshot().appHidden,true);assert.equal(h.snapshot().actor,undefined);
 assert.equal(h.run('FMZQueueSession.epoch()'),1);
});

test('valid wrapped bootstrap binds and renders the verified account',async()=>{
 const h=setup();h.ready();respond(h.requests[0],{views:[view('A')],csrf:'csrf-A'});await tick();
 assert.equal(h.snapshot().actor,'A');assert.equal(h.snapshot().appHidden,false);
 assert.equal(h.run('queueVerified.has(current)'),true);assert.equal(h.requests.length,1);
});

for(const outcome of ['success','auth_denied','network_failure'])test(`delayed startup ${outcome} cannot replace a completed login B`,async()=>{
 const h=setup();h.ready();const login=h.login('B');await finishLogin(h,'B',1);await login;
 h.run("message('new-account-message');busy=true");const before=h.snapshot();
 if(outcome==='success')respond(h.requests[0],{views:[view('A')],csrf:'csrf-A'});
 else if(outcome==='auth_denied')respond(h.requests[0],{code:'login_required'},403);
 else h.requests[0].reject(new TypeError('Failed to fetch'));
 await tick();assert.deepEqual(h.snapshot(),before);assert.equal(h.requests.length,3);
});

test('refresh checks generation again after an already resolved API promise',async()=>{
 const h=setup();h.seed('A');h.context.oldResponse={views:[view('A')],csrf:'old'};
 h.run('api=()=>Promise.resolve(oldResponse)');
 const refresh=h.run('refresh()'),checked=assert.rejects(refresh,e=>e.staleSession===true);
 h.seed('B',{busy:true,pending:payload('B'),message:'new'});const before=h.snapshot();
 await checked;assert.deepEqual(h.snapshot(),before);
});

for(const outcome of ['success','auth_denied','network_failure'])test(`old action ${outcome} cannot restore pending or clear newer busy/message`,async()=>{
 const h=setup();h.seed('A');h.context.oldPayload=payload();const submit=h.run('submitRequest(oldPayload)');
 h.seed('B',{busy:true,pending:payload('B'),message:'B-saving'});const before=h.snapshot();
 if(outcome==='success')respond(h.requests[0],{ok:true});
 else if(outcome==='auth_denied')respond(h.requests[0],{code:'login_required'},403);
 else h.requests[0].reject(new TypeError('Failed to fetch'));
 await submit;assert.deepEqual(h.snapshot(),before);assert.equal(h.requests.length,1);
});

test('action completion checks generation even after the API has resolved',async()=>{
 const h=setup();h.seed('A');h.context.oldPayload=payload();h.run('api=()=>Promise.resolve({ok:true})');
 const submit=h.run('submitRequest(oldPayload)');h.seed('B',{busy:true,pending:payload('B'),message:'new'});const before=h.snapshot();
 await submit;assert.deepEqual(h.snapshot(),before);
});

for(const outcome of ['success','network_failure'])test(`old committed action with delayed refresh ${outcome} cannot alter B`,async()=>{
 const h=setup();h.seed('A');h.context.oldPayload=payload();const submit=h.run('submitRequest(oldPayload)');
 respond(h.requests[0],{ok:true});await tick();assert.equal(h.requests[1].url,'/api/today');
 h.seed('B',{busy:true,pending:payload('B'),message:'B-saving'});const before=h.snapshot();
 if(outcome==='success')respond(h.requests[1],{views:[view('A')],csrf:'csrf-A'});else h.requests[1].reject(new TypeError('Failed to fetch'));
 await submit;assert.deepEqual(h.snapshot(),before);
});

test('current session expiry clears UI and releases busy without creating a retry',async()=>{
 const h=setup();h.seed('A');h.context.oldPayload=payload();const submit=h.run('submitRequest(oldPayload)');
 respond(h.requests[0],{code:'login_required'},403);await submit;
 const after=h.snapshot();assert.equal(after.appHidden,true);assert.equal(after.pendingRequest,null);assert.equal(after.busy,false);assert.equal(after.buttons,0);
 assert.equal(after.message,h.run('queueWords.binding[language]'));
 const login=h.login('B');assert.equal(h.requests[1].url,'/api/login');await finishLogin(h,'B',1);await login;
 assert.equal(h.snapshot().actor,'B');
});

test('nested recovery auth invalidation never resurrects an uncertain action',async()=>{
 const h=setup();h.seed('A');h.context.oldPayload={...payload(),request:{action:'recovery',data:{id:'sleep',version:0,value:0}}};
 h.context.FMZDraftQueue={get:async()=>({actor:'A',workspace:'workspace-A'}),checked:async()=>{},inspect:async()=>{throw Error('unexpected');}};
 const submit=h.run('submitRequest(oldPayload)');await tick();assert.equal(h.requests[0].url,'/api/today');
 respond(h.requests[0],{code:'login_required'},403);await submit;
 assert.equal(h.snapshot().pendingRequest,null);assert.equal(h.snapshot().busy,false);assert.equal(h.snapshot().appHidden,true);
 assert.equal(h.requests.some(r=>r.url==='/api/action'),false);
});

test('current lost response keeps the exact request for explicit retry',async()=>{
 const h=setup();h.seed('A');h.context.oldPayload=payload();const submit=h.run('submitRequest(oldPayload)');
 h.requests[0].reject(new TypeError('Failed to fetch'));await submit;
 assert.deepEqual(h.snapshot().pendingRequest,payload());assert.equal(h.snapshot().busy,false);
 const retry=h.get('#message').children[0];assert.ok(retry);retry.onclick();
 assert.equal(h.requests[1].options.body,h.requests[0].options.body);
 respond(h.requests[1],{ok:true});await tick();respond(h.requests[2],{views:[view('A')],csrf:'csrf-A'});await tick();
 assert.equal(h.snapshot().pendingRequest,null);assert.equal(h.snapshot().busy,false);
});

test('current committed save with failed refresh stays saved and cannot be retried',async()=>{
 const h=setup();h.seed('A');h.context.oldPayload=payload();const submit=h.run('submitRequest(oldPayload)');
 respond(h.requests[0],{ok:true});await tick();respond(h.requests[1],{code:'server_unavailable'},503);await submit;
 assert.equal(h.snapshot().pendingRequest,null);assert.equal(h.snapshot().busy,false);
 assert.equal(h.snapshot().message,h.run("t('savedReadFailed')"));assert.equal(h.snapshot().buttons,0);
});

test('login is blocked while logout is pending, then allowed after completion',async()=>{
 const h=setup();h.seed('A');const logout=h.get('#logout').onclick();
 assert.equal(h.snapshot().loginHidden,false);assert.equal(h.requests[0].options.headers['X-CSRF'],'csrf-A');
 await h.login('B');assert.equal(h.requests.length,1);
 respond(h.requests[0],{});await logout;assert.equal(h.snapshot().busy,false);
 const login=h.login('B');await finishLogin(h,'B',1);await login;
 assert.equal(h.snapshot().actor,'B');assert.equal(h.snapshot().busy,false);
});

test('concurrent login submissions serialize and preserve credentials captured before lock',async()=>{
 const h=setup();const login=h.login('A');await h.login('B');assert.equal(h.requests.length,1);
 assert.deepEqual(JSON.parse(h.requests[0].options.body),{email:'A@example.invalid',password:'fixture-only'});
 await finishLogin(h,'A',0);await login;assert.equal(h.snapshot().actor,'A');
});

for(const kind of ['login','logout'])for(const outcome of ['success','auth_denied','network_failure'])test(`stale ${kind} ${outcome} cannot reset B's form, message or busy state`,async()=>{
 const h=setup();if(kind==='logout')h.seed('A');
 const auth=kind==='login'?h.login('A'):h.get('#logout').onclick();
 h.seed('B',{busy:true,pending:payload('B'),message:'B-saving'});h.get('#login').values={email:'retained@example.invalid'};const before=h.snapshot();
 if(outcome==='success')respond(h.requests[0],{});
 else if(outcome==='auth_denied')respond(h.requests[0],{code:'login_required'},403);
 else h.requests[0].reject(new TypeError('Failed to fetch'));
 await auth;assert.deepEqual(h.snapshot(),before);assert.deepEqual(h.get('#login').values,{email:'retained@example.invalid'});
 assert.equal(h.requests.length,1);
});

test('current denied login stays retryable with the explicit workspace message',async()=>{
 const h=setup();const login=h.login('A');respond(h.requests[0],{code:'workspace_denied'},403);await login;
 assert.equal(h.snapshot().message,h.run("t('workspace_denied')"));assert.equal(h.snapshot().busy,false);
 const next=h.login('B');await finishLogin(h,'B',1);await next;assert.equal(h.snapshot().actor,'B');
});

test('BFCache lock clears old busy and a late action cannot touch the next session',async()=>{
 const h=setup();h.seed('A');h.context.oldPayload=payload();const submit=h.run('submitRequest(oldPayload)');
 h.windowEvents.get('pageshow')({persisted:true});assert.equal(h.snapshot().busy,false);
 const login=h.login('B');await finishLogin(h,'B',1);await login;
 h.run("message('B-saving');busy=true");const before=h.snapshot();
 h.requests[0].reject(new TypeError('Failed to fetch'));await submit;assert.deepEqual(h.snapshot(),before);
});
