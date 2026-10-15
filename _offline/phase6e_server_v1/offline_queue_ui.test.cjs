'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
function setup(api=async()=>({})){
 const nodes=new Map(),calls=[],stored={unchanged:true},events={},messages=[];
 const ctx=vm.createContext({calls,stored,events,messages,console,structuredClone,crypto,WeakSet,
  current:null,views:[],csrf:'verified-test-csrf',busy:false,pendingRequest:null,language:1,
  $:id=>{if(!nodes.has(id))nodes.set(id,{hidden:true,children:[],replaceChildren(){this.children=[];},reset(){},append(node){this.children.push(node);}});return nodes.get(id);},
  document:{createElement:()=>({append(){},dataset:{},setAttribute(){}})},window:{addEventListener(name,fn){events[name]=fn;}},
  t:x=>x,message(text){messages.push(text);},error(err){messages.push('error:'+err.message);},render(){},refresh:async()=>{},api,submitRequest:async()=>{},
  FMZDraftQueue:{get:()=>new Promise(()=>{}),remove:()=>{stored.unchanged=false;}},
 });
 vm.runInContext("async function act(action){if(busy||pendingRequest)return;calls.push(action);}",ctx);
 vm.runInContext(fs.readFileSync(path.join(__dirname,'queue_ui.js'),'utf8'),ctx);
 vm.runInContext("current={actor:'actor',workspace:'workspace',role:'member'};views=[current];queueVerified.add(current);",ctx);
 return ctx;
}
for(const action of ['revoke','health'])for(const pending of ['register12','recovery'])test(`${action} proceeds during queue read with ${pending} pending`,async()=>{
 const ctx=setup();vm.runInContext(`pendingRequest={request:{action:'${pending}'}};queueCurrent={};void showQueue();`,ctx);
 assert.equal(vm.runInContext('queueCurrent',ctx),null);
 await vm.runInContext(`act('${action}')`,ctx);
 assert.deepEqual(ctx.calls,[action]);assert.equal(ctx.pendingRequest,null);assert.equal(ctx.stored.unchanged,true);
});
for(const pending of ['approve','apply','preferences'])test(`safety actions retain uncertain ${pending}`,async()=>{
 const ctx=setup();vm.runInContext(`pendingRequest={request:{action:'${pending}'}};queueCurrent={};void showQueue();`,ctx);
 await vm.runInContext("act('revoke');act('health');",ctx);
 assert.deepEqual(ctx.calls,[]);assert.equal(ctx.pendingRequest.request.action,pending);assert.equal(ctx.stored.unchanged,true);
});
test('unverified view never reads persisted account draft',async()=>{
 const ctx=setup();let reads=0;ctx.FMZDraftQueue.get=async()=>{reads++;};vm.runInContext('queueVerified=new WeakSet();',ctx);
 await vm.runInContext('showQueue()',ctx);assert.equal(reads,0);
});
async function recoverySetup(handler){
 const Q=require('./draft_queue.js'),actor='00000000-0000-4000-8000-000000000001',workspace='00000000-0000-4000-8000-000000000002';
 const view={actor,workspace,version:1,role:'member',state:{consent:true,sourceHash:'source'},capabilities:{registration12:false}};
 const payload={workspace,version:1,request_id:'00000000-0000-4000-8000-000000000003',request:{action:'recovery',data:{id:'sleep-1',version:0,value:0}}};
 const e=await Q.create(view,payload),ctx=setup(handler);ctx.current=view;ctx.views=[view];ctx.payload=payload;ctx.FMZDraftQueue={...Q,get:async()=>e,remove:async()=>{ctx.calls.push('removed');}};return {ctx,e,view,payload};
}
test('lost-response retry rechecks Auth and keeps exact original request',async()=>{
 let attempts=0,view;const sent=[],reads=[];
 const result=await recoverySetup(async(path,data)=>{
  if(path==='today'){reads.push('verified');return {views:[{...view,version:attempts?2:1}],csrf:'fresh'};}
  if(path==='action'){sent.push(structuredClone(data));if(++attempts===1)throw Error('lost_response');return {ok:true};}
 });view=result.view;
 await assert.rejects(vm.runInContext("api('action',payload)",result.ctx),/lost_response/);assert.deepEqual(result.ctx.calls,[]);
 await vm.runInContext("api('action',payload)",result.ctx);
 assert.equal(reads.length,2);assert.deepEqual(sent,[result.payload,result.payload]);assert.deepEqual(result.ctx.calls,['removed']);
});
test('changed account or withdrawn consent cannot replay a draft',async()=>{
 for(const change of [v=>({...v,actor:v.workspace}),v=>({...v,state:{...v.state,consent:false}})]){
  let view,posts=0;const {ctx,view:initial}=await recoverySetup(async path=>{if(path==='today')return {views:[change(view)],csrf:'fresh'};posts++;return {};});view=initial;
  await assert.rejects(vm.runInContext("api('action',payload)",ctx));assert.equal(posts,0);assert.deepEqual(ctx.calls,[]);
 }
});
test('confirmed server result stays confirmed when local deletion fails',async()=>{
 let view;const result=await recoverySetup(async path=>path==='today'?{views:[view],csrf:'fresh'}:{ok:true});view=result.view;
 result.ctx.FMZDraftQueue.remove=async()=>{throw Error('draft_storage');};
 assert.equal((await vm.runInContext("api('action',payload)",result.ctx)).ok,true);
 assert.equal(vm.runInContext('queueCleanupFailed',result.ctx),true);
});
test('auth denial clears all account and pending retry state',async()=>{
 const {ctx}=await recoverySetup(async()=>{throw Object.assign(Error('login_required'),{confirmed:true});});ctx.pendingRequest=ctx.payload;
 await assert.rejects(vm.runInContext("api('today')",ctx));assert.equal(ctx.current,null);assert.equal(ctx.pendingRequest,null);assert.equal(ctx.csrf,'');
 assert.equal(ctx.$('#app').hidden,true);assert.equal(ctx.$('#queued').hidden,true);
});
test('logout captures original csrf before clearing local account state',async()=>{
 let ctx;ctx=setup(async path=>{assert.equal(path,'logout');assert.equal(ctx.csrf,'verified-test-csrf');return {ok:true};});
 await vm.runInContext("api('logout',{})",ctx);assert.equal(ctx.csrf,'');assert.equal(ctx.current,null);
});
for(const action of ['approve','apply'])test(`discarding a local draft preserves uncertain ${action}`,async()=>{
 const {ctx,payload}=await recoverySetup(async()=>({}));ctx.pendingRequest={...payload,request:{action,data:{}}};
 vm.runInContext('queueVerified.add(current);',ctx);await vm.runInContext('showQueue()',ctx);
 const discard=ctx.$('#queued').children.find(n=>n.dataset&&'queueDiscard' in n.dataset);assert.ok(discard);
 await discard.onclick();assert.equal(ctx.pendingRequest.request.action,action);assert.deepEqual(ctx.calls,['removed']);
});
for(const csrf of [undefined,null,'','   '])test(`missing or invalid csrf (${String(csrf)}) cannot bind a view`,async()=>{
 let view;const {ctx,view:initial}=await recoverySetup(async()=>({views:[view],csrf}));view=initial;
 await assert.rejects(vm.runInContext("api('today')",ctx));assert.equal(ctx.current,null);assert.equal(ctx.$('#app').hidden,true);assert.equal(ctx.$('#queued').hidden,true);
});
test('wrong actor in fresh recovery auth clears previous account DOM',async()=>{
 let view;const {ctx,view:initial}=await recoverySetup(async()=>({views:[{...view,actor:view.workspace}],csrf:'fresh'}));view=initial;
 ctx.$('#app').hidden=false;ctx.$('#content').append({textContent:'previous-account'});
 await assert.rejects(vm.runInContext("api('action',payload)",ctx));assert.equal(ctx.current,null);assert.equal(ctx.$('#content').children.length,0);assert.equal(ctx.$('#app').hidden,true);
});
for(const outcome of ['resolve','reject'])test(`late old-session ${outcome} cannot alter a newer login`,async()=>{
 let resolve,reject;const pending=new Promise((yes,no)=>{resolve=yes;reject=no;});const ctx=setup(()=>pending);
 const request=vm.runInContext("api('today')",ctx);const checked=assert.rejects(request,e=>e.staleSession===true);
 vm.runInContext("lockQueueSession();current={actor:'new',workspace:'new'};views=[current];csrf='new-csrf';",ctx);ctx.$('#app').hidden=false;ctx.$('#content').append({textContent:'new-account'});
 if(outcome==='resolve')resolve({views:[{actor:'old',workspace:'old'}],csrf:'old'});else reject(Object.assign(Error('login_required'),{confirmed:true}));
 await checked;assert.equal(ctx.current.actor,'new');assert.equal(ctx.csrf,'new-csrf');assert.equal(ctx.$('#app').hidden,false);assert.equal(ctx.$('#content').children.length,1);
});
test('page restoration invalidates an in-flight response before it can rebind',async()=>{
 let resolve;const ctx=setup(()=>new Promise(yes=>{resolve=yes;}));ctx.$('#content').append({textContent:'old-account'});
 const request=vm.runInContext("api('today')",ctx),checked=assert.rejects(request,e=>e.staleSession===true);
 ctx.events.pageshow({persisted:true});resolve({views:[{actor:'old',workspace:'old'}],csrf:'old'});await checked;
 assert.equal(ctx.current,null);assert.equal(ctx.$('#content').children.length,0);assert.equal(ctx.$('#app').hidden,true);
});
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}
function switchSession(ctx,view,payload){
 vm.runInContext('lockQueueSession();',ctx);
 const next=structuredClone(view),pending=structuredClone(payload),marker={textContent:'new-session-draft'};
 ctx.current=next;ctx.views=[next];ctx.pendingRequest=pending;ctx.csrf='new-csrf';ctx.busy=true;ctx.lateReads=0;
 ctx.FMZDraftQueue.get=async()=>{ctx.lateReads++;return null;};
 vm.runInContext('queueVerified.add(current);queueCurrent={newSession:true};queueCleanupFailed=true;',ctx);
 ctx.$('#app').hidden=false;ctx.$('#queued').hidden=false;ctx.$('#queued').append(marker);
 const messages=ctx.messages.length;
 return ()=>{
  assert.equal(ctx.current,next);assert.equal(ctx.pendingRequest,pending);assert.equal(ctx.busy,true);assert.equal(ctx.csrf,'new-csrf');
  assert.equal(ctx.messages.length,messages);assert.equal(ctx.lateReads,0);assert.equal(ctx.$('#queued').hidden,false);assert.equal(ctx.$('#queued').children.at(-1),marker);
  assert.equal(vm.runInContext('queueCurrent.newSession&&queueCleanupFailed',ctx),true);
 };
}
async function queueButton(ctx,key){vm.runInContext('queueVerified.add(current);',ctx);await vm.runInContext('showQueue()',ctx);const button=ctx.$('#queued').children.find(n=>n.dataset&&key in n.dataset);assert.ok(button);return button;}
for(const outcome of ['resolve','reject'])test(`old IndexedDB get ${outcome} cannot repaint after relogin`,async()=>{
 const {ctx,e,view,payload}=await recoverySetup(async()=>({})),wait=deferred();let inspections=0;
 vm.runInContext('queueVerified.add(current);',ctx);ctx.FMZDraftQueue.get=()=>wait.promise;ctx.FMZDraftQueue.inspect=async()=>{inspections++;return 'pending';};
 const task=vm.runInContext('showQueue()',ctx),unchanged=switchSession(ctx,view,payload);
 if(outcome==='resolve')wait.resolve(e);else wait.reject(Error('draft_storage'));await task;unchanged();assert.equal(inspections,0);
});
for(const step of ['create','put'])for(const outcome of ['resolve','reject'])test(`old draft ${step} ${outcome} cannot submit or clear new pending`,async()=>{
 const {ctx,e,view,payload}=await recoverySetup(async()=>({})),wait=deferred(),entered=deferred();let puts=0,submits=0;
 vm.runInContext('queueVerified.add(current);',ctx);ctx.FMZDraftQueue.create=async()=>e;
 ctx.FMZDraftQueue.put=async()=>{puts++;};ctx.submitRequest=async()=>{submits++;};
 ctx.FMZDraftQueue[step]=()=>{if(step==='put')puts++;entered.resolve();return wait.promise;};
 const task=vm.runInContext("act('recovery',payload.request.data)",ctx);await entered.promise;const unchanged=switchSession(ctx,view,payload);
 if(outcome==='resolve')wait.resolve(e);else wait.reject(Error('draft_storage'));await task;unchanged();assert.equal(submits,0);assert.equal(puts,step==='put'?1:0);
});
for(const step of ['refresh','inspect'])for(const outcome of ['resolve','reject'])test(`old send ${step} ${outcome} cannot change new login state`,async()=>{
 const {ctx,view,payload}=await recoverySetup(async()=>({})),button=await queueButton(ctx,'queueSubmit'),wait=deferred(),entered=deferred();let submits=0;
 ctx.submitRequest=async()=>{submits++;};const stop=()=>{entered.resolve();return wait.promise;};
 if(step==='refresh')ctx.refresh=stop;else ctx.FMZDraftQueue.inspect=stop;
 const task=button.onclick();await entered.promise;const unchanged=switchSession(ctx,view,payload);
 if(outcome==='resolve')wait.resolve('pending');else wait.reject(Error('login_required'));await task;unchanged();assert.equal(submits,0);
});
for(const outcome of ['resolve','reject'])test(`old discard remove ${outcome} preserves new pending and busy`,async()=>{
 const {ctx,view,payload}=await recoverySetup(async()=>({})),button=await queueButton(ctx,'queueDiscard'),wait=deferred(),entered=deferred();
 ctx.FMZDraftQueue.remove=(actor,workspace)=>{assert.equal(actor,view.actor);assert.equal(workspace,view.workspace);entered.resolve();return wait.promise;};
 const task=button.onclick();await entered.promise;const unchanged=switchSession(ctx,view,payload);
 if(outcome==='resolve')wait.resolve();else wait.reject(Error('draft_storage'));await task;unchanged();
});
for(const outcome of ['resolve','reject'])test(`old API acknowledgement remove ${outcome} cannot change new queue state`,async()=>{
 let view;const result=await recoverySetup(async path=>path==='today'?{views:[view],csrf:'fresh'}:{ok:true});view=result.view;
 const {ctx,payload}=result,wait=deferred(),entered=deferred();ctx.FMZDraftQueue.remove=()=>{entered.resolve();return wait.promise;};
 const task=vm.runInContext("api('action',payload)",ctx),checked=assert.rejects(task,e=>e.staleSession===true);await entered.promise;const unchanged=switchSession(ctx,view,payload);
 if(outcome==='resolve')wait.resolve();else wait.reject(Error('draft_storage'));await checked;unchanged();
});
test('session invalidation releases the old busy operation immediately',()=>{
 const ctx=setup();ctx.busy=true;ctx.events.pageshow({persisted:true});assert.equal(ctx.busy,false);assert.equal(ctx.current,null);
});
