'use strict';
// Independent, read-only suite. Run with fresh mapped A/B/member + trainer
// accounts before composed_browser's intentional unmapped-trainer teardown.
// Same stdin shape as browser_checks: {url,playwright,accounts,screenshots}.
// Ordinary route A must have no accessSource; optional verified B source is read only.
const path=require('node:path');
async function run(c) {
  if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(c.url))throw Error('loopback');
  const browser=await require(c.playwright).chromium.launch({headless:true,...(c.channel?{channel:c.channel}:{})});
  let checks=0,stage='login';const screenshots=[],errors=[],actions=[];
  const check=(value,name)=>{if(!value)throw Error(name);checks++;};
  try {
    const context=await browser.newContext(),page=await context.newPage();
    page.on('pageerror',e=>errors.push(e.name));
    page.on('request',r=>{if(new URL(r.url()).pathname==='/api/action')actions.push(r.method());});
    await context.route('**/*',r=>new URL(r.request().url()).origin===c.url?r.continue():r.abort());
    async function login(role) {
      await page.goto(c.url);await page.locator('#login').waitFor({state:'visible'});
      await page.locator('[name=email]').fill(c.accounts[role].email);
      await page.locator('[name=password]').fill(c.accounts[role].password);
      await page.locator('#login button').click();await page.locator('#app').waitFor({state:'visible'});
    }
    async function views(){return page.evaluate(()=>fetch('/api/today').then(r=>r.json()).then(j=>j.views));}
    async function logout(){await page.locator('#logout').click();await page.locator('#login').waitFor({state:'visible'});check(await page.locator('#content').innerText()==='','logout_clears_account_dom');}
    async function keyboard() {
      const tabs=page.locator('#tabs [role=tab]');await tabs.first().focus();await page.keyboard.press('Home');
      check(await tabs.first().getAttribute('aria-selected')==='true','keyboard_home');
      await page.keyboard.press('End');check(await tabs.last().getAttribute('aria-selected')==='true','keyboard_end');
      await page.keyboard.press('ArrowRight');check(await tabs.first().getAttribute('aria-selected')==='true','keyboard_wrap');
      await page.keyboard.press('ArrowLeft');check(await tabs.last().getAttribute('aria-selected')==='true','keyboard_reverse');
      check(await page.locator('#tabs [tabindex="0"]').count()===1,'single_tab_stop');
      check(await page.locator('#content').getAttribute('aria-labelledby')===await tabs.last().getAttribute('id'),'panel_label');
      await page.keyboard.press('Tab');check(await page.locator('#content').evaluate(el=>el===document.activeElement),'keyboard_enters_panel');
    }
    stage='ordinary_missing_source';await login(c.missingSourceRole||'a');
    const ordinary=await views();check(ordinary.every(v=>!v.access||v.access.status==='source_missing'),'ordinary_has_no_entitlement_source');
    await page.locator('[data-tab=account]').click();check(await page.locator('[data-access-status=source_missing]').count()===1,'missing_source_explicit');
    check(await page.locator('.account-access dd').count()===0,'missing_source_not_free');
    await keyboard();await logout();
    stage='member_settings';await login('b');const before=await views();
    const main=before.find(v=>!v.capabilities.registration12);
    await page.locator('#workspace').selectOption(main.workspace);
    await page.locator('[data-tab=settings]').click();
    check((await page.locator('[data-preferences] [name]').evaluateAll(es=>es.map(e=>e.name).sort())).join(',')==='language,theme,units','preference_contract_unchanged');
    check(await page.locator('.account-notifications input').count()===0,'notification_status_read_only');
    await page.locator('[data-tab=account]').click();
    check(await page.locator('[data-access-status]').getAttribute('data-access-status')===(main.access?.status||'source_missing'),'server_access_projection');
    if(main.access?.status==='verified_synthetic') {
      check(await page.locator('.account-access').innerText().then(s=>s.includes(main.access.source.id)),'exact_access_source');
      check(await page.locator('.account-access button').count()===0,'no_trial_or_billing_controls');
    }
    stage='mobile_language_theme';
    for(const width of [320,390,1280])for(const lang of ['0','1','2'])for(const theme of ['light','dark']) {
      await page.setViewportSize({width,height:900});await page.locator('#lang').selectOption(lang);await page.locator('#theme').selectOption(theme);
      for(const tab of ['account','settings']) {
        await page.locator(`[data-tab=${tab}]`).click();
        check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no_overflow_'+width+'_'+lang+'_'+tab);
      }
      await page.locator('[data-tab=account]').click();
      if(c.screenshots&&((width===320&&lang==='2'&&theme==='dark')||(width===1280&&lang==='0'&&theme==='light'))) {
        const file=`account-${width}-${lang}-${theme}.png`;await page.screenshot({path:path.join(c.screenshots,file),fullPage:true});screenshots.push(file);
      }
    }
    const historical=before.find(v=>v.capabilities.registration12);
    if(historical) {
      await page.locator('#workspace').selectOption(historical.workspace);
      await page.locator('[data-tab=account]').click();await page.locator(`[data-workspace="${main.workspace}"]`).click();
      check(await page.locator('#workspace').inputValue()===main.workspace,'return_from_historical');
    }
    check(JSON.stringify((await views()).map(v=>[v.workspace,v.version,v.state.preferences]))===JSON.stringify(before.map(v=>[v.workspace,v.version,v.state.preferences])),'navigation_does_not_write');
    await logout();stage='trainer_directory';await login('trainer');
    const trainerViews=await views();check(trainerViews.length>0&&trainerViews.every(v=>v.role==='trainer'),'mapped_trainer');
    check(trainerViews.every(v=>!v.state.preferences&&!v.state.records&&!v.state.active.nutrition),'server_trainer_minimal_data');
    check((await page.locator('#tabs [data-tab]').evaluateAll(es=>es.map(e=>e.dataset.tab))).join(',')==='clients,today,review,account','trainer_navigation');
    check(await page.locator('[data-tab=clients]').getAttribute('aria-selected')==='true','trainer_starts_at_directory');
    for(const view of trainerViews)check(await page.locator('.workspace-list').innerText().then(s=>s.includes(view.workspace)),'directory_identifies_workspace');
    await page.locator('.workspace-list [data-destination=today]').first().click();
    check(await page.locator('[data-tab=today]').getAttribute('aria-selected')==='true','directory_opens_overview');
    await page.locator('[data-tab=review]').click();check(await page.locator('[data-action=confirm],[data-action=apply],[data-preferences]').count()===0,'trainer_no_member_actions');
    await keyboard();await page.locator('[data-tab=account]').click();
    check(await page.locator('.account-notifications').count()===0,'trainer_no_member_notifications');
    for(const lang of ['0','1','2']) {
      await page.setViewportSize({width:320,height:900});await page.locator('#lang').selectOption(lang);
      for(const tab of ['clients','account']){await page.locator(`[data-tab=${tab}]`).click();check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'trainer_mobile_'+lang+'_'+tab);}
    }
    await logout();check(actions.length===0,'zero_action_requests');check(errors.length===0,'no_browser_errors');
    await context.close();return {status:'PASS',checks,screenshots,action_requests:0,viewports:[320,390,1280],languages:['NL','EN','DE'],themes:['light','dark'],physical_phone_test:false,hosted_calls:0};
  } catch(error) {error.message=stage+': '+error.message;throw error;}
  finally {await browser.close();}
}
module.exports={run};
if(require.main===module)(async()=>{let raw='';for await(const chunk of process.stdin)raw+=chunk;console.log(JSON.stringify(await run(JSON.parse(raw))));})().catch(e=>{console.error(JSON.stringify({status:'FAIL',error:e.message}));process.exitCode=1;});
