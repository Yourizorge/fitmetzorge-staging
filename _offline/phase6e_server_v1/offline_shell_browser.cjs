'use strict';
const path=require('node:path'),R=require('./registration12.cjs');
const allowed=['/offline_shell.css','/offline_shell.html','/offline_shell.js'];
const actor='00000000-0000-4000-8000-000000000001',workspace='00000000-0000-4000-8000-000000000002';
function fixture(){return {view:{actor,workspace,version:1,role:'member',state:{consent:true,snapshot:{synthetic:1}},capabilities:{registration12:true}},payload:{workspace,request_id:'00000000-0000-4000-8000-000000000003',version:1,request:{action:'register12',data:{input:R.view(R.initial()).draft}}}};}
async function coldShell(page,response,phase){
 // Only structural markers and allowlisted cache paths; never DOM/account text.
 const diagnostic=await page.evaluate(async()=>{
  const expected=['/offline_shell.css','/offline_shell.html','/offline_shell.js'];
  const names=await caches.keys(),keys=[];
  for(const name of names)if(name==='fmz-local-offline-shell-v1'){
   const cache=await caches.open(name);
   for(const req of await cache.keys()){
    const url=new URL(req.url);keys.push(url.origin===location.origin&&!url.search&&expected.includes(url.pathname)?url.pathname:'other');
   }
  }
  return {url_category:location.pathname==='/'&&!location.search?'root':'other',controller:Boolean(navigator.serviceWorker.controller),online:navigator.onLine,root_marker:document.querySelector('[data-offline-shell]')?'offline_shell':document.querySelector('#login')?'online_login':'other',cache_keys:keys.sort(),other_cache_count:names.filter(n=>n!=='fmz-local-offline-shell-v1').length};
 });
 diagnostic.phase=phase;diagnostic.from_service_worker=response?.fromServiceWorker()??false;diagnostic.status=response?.status()??null;
 diagnostic.worker_online=await Promise.all(page.context().serviceWorkers().map(w=>w.evaluate(()=>navigator.onLine).catch(()=>null)));
 try{await page.locator('[data-offline-shell]').waitFor();}
 catch(e){e.cold_diagnostic=diagnostic;throw e;}
 return diagnostic;
}
async function storageChecks(page,ok){
 const result=await page.evaluate(async({view,payload})=>{
  const Q=FMZDraftQueue,e=await Q.create(view,payload),results=[];
  const check=(value,label)=>results.push([Boolean(value),label]);
  const rejects=async fn=>{try{await fn();return false;}catch(_){return true;}};
  await Q.put(e);await Q.put(e);check((await Q.get(view.actor,view.workspace)).hash===e.hash,'durable_exact_request');
  check(await Q.get('00000000-0000-4000-8000-000000000099',view.workspace)===null,'other_actor_isolated');
  const next=await Q.create(view,{...payload,request_id:crypto.randomUUID()});
  check(await rejects(()=>Q.put(next)),'pending_not_replaced');
  check(await rejects(()=>Q.remove(view.actor,view.workspace,next.hash)),'compare_delete_blocks_replacement');
  check((await Q.get(view.actor,view.workspace)).hash===e.hash,'compare_delete_keeps_original');
  await Q.remove(view.actor,view.workspace,e.hash);
  const race=await Promise.allSettled([Q.put(e),Q.put(next)]);check(race.filter(r=>r.status==='fulfilled').length===1,'concurrent_put_one_winner');
  await Q.remove(view.actor,view.workspace);
  const entries=[];
  for(let i=0;i<10;i++){
   const w='00000000-0000-4000-8000-'+String(i+10).padStart(12,'0');
   const item=await Q.create({...view,workspace:w},{...payload,workspace:w});await Q.put(item);entries.push(item);
  }
  check(await rejects(()=>Q.put(e)),'capacity_ten');
  for(const item of entries)await Q.remove(item.actor,item.workspace,item.hash);
  // Storage corruption never grants access to the envelope's actor.
  await new Promise((resolve,reject)=>{const q=indexedDB.open('fmz-local-synthetic-drafts-v1',1);q.onsuccess=()=>{const db=q.result,tx=db.transaction('drafts','readwrite');tx.objectStore('drafts').put({...e,actor:'00000000-0000-4000-8000-000000000099'},view.actor+':'+view.workspace);tx.oncomplete=()=>{db.close();resolve();};tx.onerror=reject;};q.onerror=reject;});
  check(await rejects(()=>Q.get(view.actor,view.workspace)),'storage_key_binding');await Q.remove(view.actor,view.workspace);
  await Q.put(e);
  return results;
 },fixture());
 for(const [value,label] of result)ok(value,label);
}
async function shellChecks(browser,c,ok){
 const context=await browser.newContext(),page=await context.newPage(),screenshots=[],errors=[];let actions=0;
 context.on('request',r=>{if(new URL(r.url()).pathname==='/api/action')actions++;});
 await context.route('**/*',r=>new URL(r.request().url()).origin===c.url?r.continue():r.abort());
 page.on('pageerror',e=>errors.push(e.name));
 try{
  await page.goto(c.url);await page.locator('#login').waitFor();
  await page.evaluate(()=>navigator.serviceWorker.ready.then(()=>true));
  await page.waitForFunction(()=>navigator.serviceWorker.controller!==null);
  await storageChecks(page,ok);
  await page.reload();await page.locator('#login').waitFor();
  ok(await page.evaluate(async({actor,workspace})=>(await FMZDraftQueue.get(actor,workspace))!==null,{actor,workspace}),'draft_survives_reload');
  ok(await page.locator('#queued').isHidden(),'anonymous_drafts_hidden');
  const inventory=await page.evaluate(async()=>{const out=[];for(const name of await caches.keys())if(name.startsWith('fmz-local-offline-shell-')){const cache=await caches.open(name);for(const req of await cache.keys()){const res=await cache.match(req);out.push({path:new URL(req.url).pathname,cookie:res.headers.has('set-cookie'),text:await res.text()});}}return out;});
  ok(JSON.stringify(inventory.map(x=>x.path).sort())===JSON.stringify(allowed),'cache_exact_generic_allowlist');
  ok(inventory.every(x=>!x.cookie&&!x.text.includes(actor)&&!x.text.includes(workspace)),'cache_no_account_or_cookie');
  await page.locator('#lang').selectOption('2');await page.locator('#theme').selectOption('dark');
  await context.addInitScript(()=>{window.shellIDBReads=0;const open=indexedDB.open.bind(indexedDB);indexedDB.open=(...args)=>{window.shellIDBReads++;return open(...args);};});
  await context.setOffline(true);
  const cold=await context.newPage();cold.on('pageerror',e=>errors.push(e.name));await coldShell(cold,await cold.goto(c.url),'anonymous_cold_start');
  ok(await cold.locator('html').getAttribute('lang')==='de','offline_device_language');
  ok(await cold.locator('body').getAttribute('data-theme')==='dark','offline_device_theme');
  ok(await cold.locator('#login,#app,#queued,input').count()===0,'cold_has_no_login_or_account_controls');
  ok(await cold.evaluate(()=>shellIDBReads)===0,'cold_never_opens_drafts');
  for(const width of [390,1280])for(const language of ['0','1','2'])for(const theme of ['light','dark']){
   await cold.setViewportSize({width,height:900});await cold.locator('#lang').selectOption(language);await cold.locator('#theme').selectOption(theme);
   ok(await cold.locator('#shell-title').innerText()===['Toegang geblokkeerd','Access blocked','Zugriff gesperrt'][Number(language)],'offline_language_'+language);
   ok(await cold.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'offline_width_'+width);
   ok(await cold.evaluate(()=>{const b=document.querySelector('#shell-reconnect').getBoundingClientRect();return b.width>0&&b.height>=44&&b.right<=innerWidth;}),'offline_button_bounds');
   const filename=`offline-shell-${width}-${language}-${theme}.png`;await cold.screenshot({path:path.join(c.screenshots,filename),fullPage:true});screenshots.push(filename);
  }
  for(const url of ['/api/today','/ui.js','/account_center.js','/offline_shell.html?probe=1'])ok(await cold.evaluate(async url=>{try{await fetch(url);return false;}catch(_){return true;}},url),'network_only_'+url);
  ok(!(await cold.locator('body').innerText()).includes(actor),'cold_no_actor');
  await coldShell(cold,await cold.reload(),'anonymous_cold_reload');ok(await cold.evaluate(()=>shellIDBReads)===0,'cold_reload_no_draft_read');
  await context.setOffline(false);await cold.waitForFunction(()=>navigator.onLine);
  ok(await cold.locator('[data-offline-shell]').count()===1,'reconnect_does_not_sign_in');
  await cold.locator('#shell-reconnect').focus();await cold.keyboard.press('Enter');await cold.locator('#login').waitFor();
  ok(await cold.locator('#app').isHidden(),'real_auth_required_after_reconnect');
  ok(actions===0,'generic_shell_never_posts_action');ok(errors.length===0,'shell_no_browser_errors');
  return screenshots;
 }finally{await context.close();}
}
async function authChecks(browser,c,ok){
 const context=await browser.newContext(),page=await context.newPage();let actions=0;
 context.on('request',r=>{if(new URL(r.url()).pathname==='/api/action')actions++;});
 await context.route('**/*',r=>new URL(r.request().url()).origin===c.url?r.continue():r.abort());
 try{
  await page.goto(c.url);await page.locator('[name=email]').fill(c.accounts.b.email);await page.locator('[name=password]').fill(c.accounts.b.password);await page.locator('#login button').click();await page.locator('#app').waitFor();
  await page.waitForFunction(()=>current&&queueVerified.has(current));
  const state=await page.evaluate(()=>fetch('/api/today').then(r=>r.json()));
  const revoked=state.views.find(v=>!v.capabilities.registration12&&v.state.consent===false);
  ok(Boolean(revoked),'post_composed_revoked_workspace');
  await page.locator('#workspace').selectOption(revoked.workspace);
  // Model a draft retained from before revocation. This seeds only IndexedDB;
  // the actual server view remains revoked and no action is submitted.
  await page.evaluate(async view=>{
   const row=view.state.recovery.rows[0],payload={workspace:view.workspace,request_id:crypto.randomUUID(),version:view.version,request:{action:'recovery',data:{id:row.id,version:row.version,value:row.value}}};
   const e=await FMZDraftQueue.create({...view,state:{...view.state,consent:true}},payload);await FMZDraftQueue.put(e);await showQueue();
  },revoked);
  await page.locator('[data-queue-submit]').waitFor();ok(await page.locator('[data-queue-submit]').isDisabled(),'verified_revocation_blocks_submit');
  await page.evaluate(()=>navigator.serviceWorker.ready.then(()=>true));await page.waitForFunction(()=>navigator.serviceWorker.controller!==null);
  await context.setOffline(true);await coldShell(page,await page.reload(),'authenticated_cold_reload');
  ok(await page.locator('#app,#queued,input').count()===0,'authenticated_cold_start_hides_account');
  await context.setOffline(false);await context.clearCookies();await page.locator('#shell-reconnect').click();await page.locator('#login').waitFor();
  ok(await page.locator('#queued').isHidden(),'expired_session_cannot_recover_drafts');
  await page.locator('[name=email]').fill(c.accounts.b.email);await page.locator('[name=password]').fill(c.accounts.b.password);await page.locator('#login button').click();await page.locator('#app').waitFor();
  await page.locator('#workspace').selectOption(revoked.workspace);await page.locator('[data-queue-submit]').waitFor();
  const [signedOut]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/logout'&&r.request().method()==='POST'),page.locator('#logout').click()]);
  ok(signedOut.status()===200,'logout_confirmed');await page.waitForFunction(()=>!authInFlight&&!busy);await page.locator('#login').waitFor();
  ok(await page.locator('#queued').isHidden()&&await page.locator('#content').innerText()==='','logout_clears_account_and_draft_ui');
  await page.locator('[name=email]').fill(c.accounts.trainer.email);await page.locator('[name=password]').fill(c.accounts.trainer.password);await page.locator('#login button').click();
  await page.waitForFunction(()=>document.querySelector('#message').textContent.length>0);
  await page.waitForFunction(()=>!authInFlight&&!busy);
  ok(await page.locator('#app').isHidden()&&await page.locator('#queued').isHidden(),'unmapped_account_cannot_recover_drafts');
  await page.locator('[name=email]').fill(c.accounts.b.email);await page.locator('[name=password]').fill(c.accounts.b.password);await page.locator('#login button').click();await page.locator('#app').waitFor();
  await page.locator('#workspace').selectOption(revoked.workspace);await page.locator('[data-queue-submit]').waitFor();
  ok(await page.locator('[data-queue-submit]').isDisabled(),'exact_actor_relogin_recovers_revoked_draft');
  await page.locator('[data-queue-discard]').click();await page.waitForFunction(()=>!busy&&document.querySelector('#queued').hidden);
  const after=await page.evaluate(()=>fetch('/api/today').then(r=>r.json()));
  ok(state.views.every(v=>after.views.find(x=>x.workspace===v.workspace)?.version===v.version),'no_server_version_changes');
  ok(actions===0,'revoked_recovery_no_action_posts');
  const [closed]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/logout'&&r.request().method()==='POST'),page.locator('#logout').click()]);
  ok(closed.status()===200,'final_logout_confirmed');await page.waitForFunction(()=>!authInFlight&&!busy);await page.locator('#login').waitFor();
 }finally{await context.close();}
}
async function main(){
 let raw='';for await(const chunk of process.stdin)raw+=chunk;const c=JSON.parse(raw);
 if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(c.url))throw Error('loopback');
 const browser=await require(c.playwright).chromium.launch({headless:true});let checks=0,stage='shell';
 const ok=(value,label)=>{if(!value)throw Error(label);checks++;};
 try{const screenshots=await shellChecks(browser,c,ok);stage='real_auth';await authChecks(browser,c,ok);console.log(JSON.stringify({status:'PASS',checks,screenshots,real_local_auth:true,database_writes:0,hosted_calls:0,physical_phone_test:false}));}
 catch(e){console.log(JSON.stringify({status:'NO_GO',stage,checks,error:e.message.slice(0,160),...(e.cold_diagnostic?{cold_diagnostic:e.cold_diagnostic}:{})}));process.exitCode=2;}
 finally{await browser.close();}
}
module.exports={shellChecks,storageChecks,authChecks,coldShell};
if(require.main===module)main().catch(()=>{console.log(JSON.stringify({status:'NO_GO',stage:'setup'}));process.exitCode=2;});
