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
 async function logout(){const [r]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/logout'&&r.request().method()==='POST'),page.locator('#logout').click()]);ok(r.status()===200,'logout_confirmed');await page.waitForFunction(()=>!authInFlight&&!busy);await page.locator('#login').waitFor({state:'visible'});}
 await login();let all=await state();ok(all.length===2,'one_login_two_explicit_sources');
 const main=all.find(v=>!v.capabilities.registration12),historical=all.find(v=>v.capabilities.registration12);
 ok(main.capabilities.full_day21===false&&historical.capabilities.full_day21===false,'21_off_both');
 stage='comparison_before_edit';await page.locator('[data-tab=today]').click();await click(page.locator('[data-compare]'));
 const beforeRebuild=(await state()).find(v=>v.workspace===main.workspace).state;
 stage='comparison_after_rebuild';await page.locator('[data-tab=intake]').click();await click(page.locator('[data-action=build]'));
 await page.locator('[data-tab=review]').click();await click(page.locator('[data-action=confirm]'));await click(page.locator('[data-action=apply]'));
 const rebuilt=(await state()).find(v=>v.workspace===main.workspace).state;
 ok(rebuilt.active.version===beforeRebuild.active.version+1,'rebuilt_plan_applied_separately');
 ok(rebuilt.comparison===null&&rebuilt.facts.length===0,'apply_expires_old_plan_comparison');
 ok(JSON.stringify(rebuilt.comparisonHistory)===JSON.stringify(beforeRebuild.comparisonHistory),'apply_preserves_comparison_history');
 await page.reload();await page.locator('#app').waitFor({state:'visible'});
 ok((await state()).find(v=>v.workspace===main.workspace).state.comparison===null,'applied_comparison_expiry_survives_reload');
 await page.locator('[data-tab=today]').click();await click(page.locator('[data-compare]'));
 const compared=(await state()).find(v=>v.workspace===main.workspace).state;
 ok(compared.comparison.revision===beforeRebuild.comparison.revision+1,'fresh_comparison_after_apply');
 ok(compared.facts.length===4,'current_comparison_before_edit');
 stage='accepted_plan';await page.locator('[data-tab=training]').click();ok(await page.locator('[data-exercise]').count()>0,'plan_editor_with_21_off');ok(await page.locator('[data-record]').count()===0,'no_full_day_registration');
 const form=page.locator('[data-exercise]').first();await form.locator('[name=reps]').fill('11');await click(form.locator('button'));
 ok((await state()).find(v=>v.workspace===main.workspace).state.active.version===compared.active.version,'edit_not_applied');
 const edited=(await state()).find(v=>v.workspace===main.workspace).state;
 ok(edited.comparison===null&&edited.facts.length===0,'edit_removes_current_facts');
 ok(JSON.stringify(edited.comparisonHistory)===JSON.stringify(compared.comparisonHistory),'edit_preserves_comparison_history');
 await page.locator('[data-tab=today]').click();ok(!/training:|nutrition:|sleep:|recovery:/.test(await page.locator('#content').innerText()),'today_has_no_stale_comparison');
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
 stage='large_text_keyboard';await page.setViewportSize({width:390,height:844});
 await page.evaluate(()=>document.documentElement.style.fontSize='200%');
 for(const language of ['0','1','2'])for(const theme of ['light','dark']){
  await page.locator('#lang').selectOption(language);await page.locator('#theme').selectOption(theme);
  for(const tab of ['today','training','nutrition','intake','progress','settings']){
   await page.locator(`[data-tab=${tab}]`).click();
   ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'large_text_'+language+'_'+theme+'_'+tab);
  }
  await page.locator('[data-tab=today]').click();await page.locator('[data-tab=today]').press('ArrowRight');
  ok(await page.locator('[data-tab=training]').getAttribute('aria-selected')==='true','keyboard_tabs_'+language+'_'+theme);
 }
 await page.screenshot({path:path.join(c.screenshots,'composed-large-text-de-dark.png')});screenshots.push('composed-large-text-de-dark.png');
 await page.evaluate(()=>document.documentElement.style.fontSize='');
 stage='slow_connection';await page.locator('[data-tab=settings]').click();await page.locator('[name=language]').selectOption('en');
 const slowBefore=(await state()).find(v=>v.workspace===main.workspace).version;let slowRequests=0;
 await page.route('**/api/action',async route=>{slowRequests++;await new Promise(resolve=>setTimeout(resolve,600));await route.continue();});
 const slowResult=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/action');
 await page.locator('[data-preferences] button').dblclick();ok((await slowResult).status()===200,'slow_save');await page.waitForFunction(()=>!busy);
 ok(slowRequests===1,'slow_double_click_single_request');await page.unroute('**/api/action');
 ok((await state()).find(v=>v.workspace===main.workspace).version===slowBefore+1,'slow_single_durable_version');
 stage='historical';await page.locator('#workspace').selectOption(historical.workspace);ok(await page.locator('[data-registration12]').count()===1,'same_login_registration12');
 ok((await page.locator('[data-weight-display]').first().innerText()).includes('lb'),'imperial_display_visible');
 ok((await page.locator('[data-weight-display]').first().innerText()).includes('kg)'),'original_unit_preserved');
 const snapshot=JSON.stringify((await state()).find(v=>v.workspace===historical.workspace).state.snapshot);
 ok(await page.locator('[name=load0]').isDisabled(),'explicit_start_required');await click(page.locator('[data-action=start12]'));
 await page.locator('[name=load0]').fill('0');await page.locator('[name=reps0]').fill('8');await page.locator('[name=rir0]').fill('0');await page.locator('[name=rpe0]').fill('');await page.locator('[name=done0]').check();await click(page.locator('[data-registration12] button'));
 ok((await state()).find(v=>v.workspace===historical.workspace).state.session12.status==='started','save_not_finish');await click(page.locator('[data-action=finish12]'));
 ok((await state()).find(v=>v.workspace===historical.workspace).state.session12.closures[0].completed===1,'partial_finish_facts');
 await logout();await login();await page.locator('#workspace').selectOption(historical.workspace);
 ok(await page.locator('[name=rir0]').inputValue()==='0','relogin_rir_zero');ok(await page.locator('[name=rpe0]').inputValue()==='','relogin_rpe_missing');
 ok(JSON.stringify((await state()).find(v=>v.workspace===historical.workspace).state.snapshot)===snapshot,'historical_snapshot_preserved');
 stage='durable_offline_registration';await click(page.locator('[data-action=start12]'));
 const draftBefore=(await state()).find(v=>v.workspace===historical.workspace).version;
 await page.locator('[name=rir0]').fill('2');await context.setOffline(true);
 await page.locator('[data-registration12] button').click();await page.waitForFunction(()=>!busy&&pendingRequest!==null);
 const pending=await page.evaluate(async()=>FMZDraftQueue.get(current.actor,current.workspace));
 ok(pending.payload.request.data.input.sets[0].rir===2,'offline_value_retained');
 ok(pending.payload.request.data.input.sets[0].rpe===null,'offline_null_retained');
 ok(!/password|access_token|refresh_token|csrf/.test(JSON.stringify(pending)),'draft_no_credentials');
 await context.setOffline(false);await page.reload();await page.locator('#app').waitFor({state:'visible'});await page.locator('#workspace').selectOption(historical.workspace);await page.locator('[data-queue-submit]').waitFor();
 ok((await state()).find(v=>v.workspace===historical.workspace).version===draftBefore,'offline_no_partial_write_or_autosync');
 await logout();await login();await page.locator('#workspace').selectOption(historical.workspace);await page.locator('[data-queue-submit]').waitFor();
 const duplicate=await page.evaluate(async()=>{const e=await FMZDraftQueue.get(current.actor,current.workspace);const next=await FMZDraftQueue.create(current,{...e.payload,request_id:crypto.randomUUID()});try{await FMZDraftQueue.put(next);return false;}catch(_){return true;}});
 ok(duplicate,'pending_draft_not_overwritten');await click(page.locator('[data-queue-submit]'));
 ok((await state()).find(v=>v.workspace===historical.workspace).version===draftBefore+1,'explicit_sync_once');
 ok(await page.evaluate(async()=>await FMZDraftQueue.get(current.actor,current.workspace)===null),'confirmed_draft_removed');
 stage='offline_conflict';await page.locator('[name=rir0]').fill('3');await context.setOffline(true);await page.locator('[data-registration12] button').click();await page.waitForFunction(()=>!busy&&pendingRequest!==null);await context.setOffline(false);
 const concurrent=await page.evaluate(async()=>{const p=structuredClone(pendingRequest);p.request_id=crypto.randomUUID();p.request.data.input.sets[0].rir=4;return fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF':csrf},body:JSON.stringify(p)}).then(r=>r.status);});ok(concurrent===200,'independent_source_correction');
 await page.reload();await page.locator('#app').waitFor({state:'visible'});await page.locator('#workspace').selectOption(historical.workspace);await page.locator('[data-queue-submit]').waitFor();
 const [conflicted]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/action'),page.locator('[data-queue-submit]').click()]);ok(conflicted.status()===403,'stale_queue_refused');await page.waitForFunction(()=>!busy);
 ok((await state()).find(v=>v.workspace===historical.workspace).state.registrations.at(-1).sets[0].rir===4,'correction_not_overwritten');
 await page.locator('[data-queue-discard]').click();await page.waitForFunction(()=>!busy);ok(await page.locator('#queued').isHidden(),'only_local_draft_discarded');
 stage='uncertain_commit';await page.locator('#workspace').selectOption(main.workspace);await page.locator('[data-tab=settings]').click();
 const beforeView=(await state()).find(v=>v.workspace===main.workspace),before=beforeView.version;
 const changedLanguage=beforeView.state.preferences.language==='en'?'nl':'en';
 await page.locator('[name=language]').selectOption(changedLanguage);
 await page.route('**/api/action',async route=>{await route.fetch();await route.abort();});
 await page.locator('[data-preferences] button').click();await page.waitForFunction(()=>!busy&&pendingRequest!==null);
 ok((await state()).find(v=>v.workspace===main.workspace).version===before+1,'commit_before_lost_response');
 await page.unroute('**/api/action');await click(page.locator('#message button'));
 ok((await state()).find(v=>v.workspace===main.workspace).version===before+1,'same_request_no_duplicate');
 stage='server_21_boundary';const denied=await page.evaluate(async()=>{const j=await fetch('/api/today').then(r=>r.json()),v=j.views.find(v=>!v.capabilities.registration12);return fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF':j.csrf},body:JSON.stringify({workspace:v.workspace,request_id:crypto.randomUUID(),version:v.version,request:{action:'finish_day',data:{}}})}).then(r=>r.status);});ok(denied===403,'21_still_server_denied');
 stage='comparison_before_intake';await page.locator('[data-tab=today]').click();await click(page.locator('[data-compare]'));
 const intakeComparison=(await state()).find(v=>v.workspace===main.workspace).state;
 ok(intakeComparison.facts.length===4,'current_comparison_before_intake');
 stage='intake_source';await page.locator('[data-tab=intake]').click();await page.locator('[name=excluded][value=squat]').check();await page.locator('[name=allergyStatus]').selectOption('missing');await click(page.locator('#intake-form button'));
 const changed=(await state()).find(v=>v.workspace===main.workspace).state;ok(changed.review===null&&changed.intakeHistory.length===2,'intake_retains_history_invalidates_review');
 ok(changed.comparison===null&&changed.facts.length===0,'intake_removes_current_facts');
 ok(JSON.stringify(changed.comparisonHistory)===JSON.stringify(intakeComparison.comparisonHistory),'intake_preserves_comparison_history');
 await page.reload();await page.locator('#app').waitFor({state:'visible'});
 ok((await state()).find(v=>v.workspace===main.workspace).state.facts.length===0,'invalidated_facts_survive_reload');
 await page.locator('[data-tab=intake]').click();
 await page.locator('[data-action=build]').click();await page.waitForFunction(()=>!busy);ok((await state()).find(v=>v.workspace===main.workspace).state.review===null,'unknown_allergy_no_plan');
 stage='queued_consent';await page.locator('[data-tab=recovery]').click();const recovery=page.locator('[data-recovery]').first();await recovery.locator('[name=value]').fill('420');await context.setOffline(true);await recovery.locator('button').click();await page.waitForFunction(()=>!busy&&pendingRequest!==null);await context.setOffline(false);
 await page.locator('[data-tab=intake]').click();await click(page.locator('[data-action=revoke]'));await page.locator('[data-queue-submit]').waitFor();
 ok(await page.locator('[data-queue-submit]').isDisabled(),'revocation_blocks_queued_processing');
 const revokedVersion=(await state()).find(v=>v.workspace===main.workspace).version;await page.locator('[data-queue-discard]').click();await page.waitForFunction(()=>!busy);
 ok((await state()).find(v=>v.workspace===main.workspace).version===revokedVersion,'discard_not_database_mutation');
 stage='denial';await logout();await page.locator('[name=email]').fill(c.accounts.trainer.email);await page.locator('[name=password]').fill(c.accounts.trainer.password);
 const [deniedLogin]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/login'),page.locator('#login button').click()]);
 ok(deniedLogin.status()===403,'unmapped_trainer_denied');ok(errors.length===0,'no_browser_errors');
 console.log(JSON.stringify({status:'PASS',checks,screenshots,full_day21:false,real_local_auth:true,physical_phone_test:false,hosted_calls:0}));
}catch(e){
 console.log(JSON.stringify({status:'NO_GO',stage,checks,error:e.message.slice(0,150),errors}));process.exitCode=2;
}finally{await browser.close();}
})();
