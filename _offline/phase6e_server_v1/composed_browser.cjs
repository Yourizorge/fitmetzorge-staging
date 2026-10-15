'use strict';
const path=require('node:path');
(async()=>{let raw='';for await(const chunk of process.stdin)raw+=chunk;const c=JSON.parse(raw);
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(c.url))throw Error('loopback');
const browser=await require(c.playwright).chromium.launch({headless:true});let checks=0,stage='login';const errors=[],screenshots=[];
const ok=(v,n)=>{if(!v)throw Error(n);checks++;};
try{
 const context=await browser.newContext(),page=await context.newPage();page.on('pageerror',e=>errors.push(e.name));
 await context.route('**/*',r=>new URL(r.request().url()).origin===c.url?r.continue():r.abort());
 async function login(role='b'){await page.goto(c.url);await page.locator('#login').waitFor({state:'visible'});await page.locator('[name=email]').fill(c.accounts[role].email);await page.locator('[name=password]').fill(c.accounts[role].password);await page.locator('#login button').click();await page.locator('#app').waitFor({state:'visible'});}
 async function state(){return page.evaluate(()=>fetch('/api/today').then(r=>r.json()).then(j=>j.views));}
 async function click(locator){const [r]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/action'),locator.click()]);ok(r.status()===200,'saved_'+stage);await page.waitForFunction(()=>!busy);}
 async function logout(){await page.locator('#logout').click();await page.locator('#login').waitFor({state:'visible'});}
 await login();let all=await state();ok(all.length===2,'one_login_two_explicit_sources');
 const main=all.find(v=>!v.capabilities.registration12),historical=all.find(v=>v.capabilities.registration12);
 ok(main.capabilities.full_day21===false&&historical.capabilities.full_day21===false,'21_off_both');
 stage='accepted_plan';await page.locator('[data-tab=training]').click();ok(await page.locator('[data-exercise]').count()>0,'plan_editor_with_21_off');ok(await page.locator('[data-record]').count()===0,'no_full_day_registration');
 const form=page.locator('[data-exercise]').first();await form.locator('[name=reps]').fill('11');await click(form.locator('button'));
 ok((await state()).find(v=>v.workspace===main.workspace).state.active.version===1,'edit_not_applied');
 await page.locator('[data-tab=review]').click();await click(page.locator('[data-action=confirm]'));await click(page.locator('[data-action=apply]'));
 stage='nutrition';await page.locator('[data-tab=nutrition]').click();ok(await page.locator('#content').innerText().then(x=>x.includes('geen gegeten')),'planned_not_consumed');
 const portion=page.locator('[data-portion]').first();await portion.locator('[name=grams]').fill('225');await click(portion.locator('button'));
 await page.locator('[data-tab=review]').click();await click(page.locator('[data-action=confirm]'));await click(page.locator('[data-action=apply]'));
 stage='preferences';await page.locator('[data-tab=settings]').click();await page.locator('[name=language]').selectOption('de');await page.locator('[name=theme]').selectOption('dark');await page.locator('[name=units]').selectOption('imperial');await click(page.locator('[data-preferences] button'));
 await page.reload();await page.locator('#app').waitFor({state:'visible'});ok(await page.locator('html').getAttribute('lang')==='de','persistent_language');ok(await page.locator('body').getAttribute('data-theme')==='dark','persistent_theme');
 stage='viewport';for(const width of [390,1280])for(const language of ['0','1','2'])for(const theme of ['light','dark']){
  await page.setViewportSize({width,height:900});await page.locator('#lang').selectOption(language);await page.locator('#theme').selectOption(theme);
  for(const tab of ['today','training','nutrition','intake','progress','settings']){await page.locator(`[data-tab=${tab}]`).click();ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'viewport_'+tab);}
  await page.locator('[data-tab=training]').click();const name=`composed-${width}-${language}-${theme}.png`;await page.screenshot({path:path.join(c.screenshots,name)});screenshots.push(name);
 }
 stage='historical';await page.locator('[data-workspace]').click();ok(await page.locator('[data-registration12]').count()===1,'same_login_registration12');
 const snapshot=JSON.stringify((await state()).find(v=>v.workspace===historical.workspace).state.snapshot);
 ok(await page.locator('[name=load0]').isDisabled(),'explicit_start_required');await click(page.locator('[data-action=start12]'));
 await page.locator('[name=load0]').fill('0');await page.locator('[name=reps0]').fill('8');await page.locator('[name=rir0]').fill('0');await page.locator('[name=rpe0]').fill('');await page.locator('[name=done0]').check();await click(page.locator('[data-registration12] button'));
 ok((await state()).find(v=>v.workspace===historical.workspace).state.session12.status==='started','save_not_finish');await click(page.locator('[data-action=finish12]'));
 ok((await state()).find(v=>v.workspace===historical.workspace).state.session12.closures[0].completed===1,'partial_finish_facts');
 await logout();await login();await page.locator('#workspace').selectOption(historical.workspace);
 ok(await page.locator('[name=rir0]').inputValue()==='0','relogin_rir_zero');ok(await page.locator('[name=rpe0]').inputValue()==='','relogin_rpe_missing');
 ok(JSON.stringify((await state()).find(v=>v.workspace===historical.workspace).state.snapshot)===snapshot,'historical_snapshot_preserved');
 stage='uncertain_commit';await page.locator('#workspace').selectOption(main.workspace);await page.locator('[data-tab=settings]').click();
 const before=(await state()).find(v=>v.workspace===main.workspace).version;
 await page.locator('[name=language]').selectOption('en');
 await page.route('**/api/action',async route=>{await route.fetch();await route.abort();});
 await page.locator('[data-preferences] button').click();await page.waitForFunction(()=>!busy&&pendingRequest!==null);
 ok((await state()).find(v=>v.workspace===main.workspace).version===before+1,'commit_before_lost_response');
 await page.unroute('**/api/action');await click(page.locator('#message button'));
 ok((await state()).find(v=>v.workspace===main.workspace).version===before+1,'same_request_no_duplicate');
 stage='server_21_boundary';const denied=await page.evaluate(async()=>{const j=await fetch('/api/today').then(r=>r.json()),v=j.views.find(v=>!v.capabilities.registration12);return fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF':j.csrf},body:JSON.stringify({workspace:v.workspace,request_id:crypto.randomUUID(),version:v.version,request:{action:'finish_day',data:{}}})}).then(r=>r.status);});ok(denied===403,'21_still_server_denied');
 stage='intake_source';await page.locator('[data-tab=intake]').click();await page.locator('[name=excluded][value=squat]').check();await page.locator('[name=allergyStatus]').selectOption('missing');await click(page.locator('#intake-form button'));
 const changed=(await state()).find(v=>v.workspace===main.workspace).state;ok(changed.review===null&&changed.intakeHistory.length===2,'intake_retains_history_invalidates_review');
 await page.locator('[data-action=build]').click();await page.waitForFunction(()=>!busy);ok((await state()).find(v=>v.workspace===main.workspace).state.review===null,'unknown_allergy_no_plan');
 stage='denial';await logout();await page.locator('[name=email]').fill(c.accounts.trainer.email);await page.locator('[name=password]').fill(c.accounts.trainer.password);
 const [deniedLogin]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/login'),page.locator('#login button').click()]);
 ok(deniedLogin.status()===403,'unmapped_trainer_denied');ok(errors.length===0,'no_browser_errors');
 console.log(JSON.stringify({status:'PASS',checks,screenshots,full_day21:false,real_local_auth:true,physical_phone_test:false,hosted_calls:0}));
}catch(e){
 console.log(JSON.stringify({status:'NO_GO',stage,checks,error:e.message.slice(0,150),errors}));process.exitCode=2;
}finally{await browser.close();}
})();
