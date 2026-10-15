'use strict';
const fs=require('node:fs'),path=require('node:path');
(async()=>{let raw='';for await(const chunk of process.stdin)raw+=chunk;const c=JSON.parse(raw);
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(c.url))throw Error('loopback');
const {chromium}=require(c.playwright),browser=await chromium.launch({headless:true});let checks=0,stage='login';const screenshots=[],http=[],errors=[];
const check=(v,m)=>{if(!v)throw Error(m);checks++;};
try{const context=await browser.newContext(),page=await context.newPage();page.on('pageerror',e=>errors.push(e.name));
page.on('response',async r=>{const p=new URL(r.url()).pathname;if(p.startsWith('/api/')){let detail={};try{const v=await r.json();if(typeof v.code==='string'&&/^[a-z_]+$/.test(v.code))detail={code:v.code,class:v.class,sqlstate:v.sqlstate,frames:v.frames};}catch{}http.push({path:p,status:r.status(),...detail});}});
await context.route('**/*',route=>{if(new URL(route.request().url()).origin!==c.url)return route.abort();return route.continue();});
async function login(role){await page.goto(c.url);await page.locator('#login').waitFor({state:'visible'});await page.locator('[name=email]').fill(c.accounts[role].email);await page.locator('[name=password]').fill(c.accounts[role].password);await page.locator('#login button').click();await page.locator('#app').waitFor({state:'visible'});}
await login('b');check(await page.locator('#status').innerText().then(x=>x.includes('Lid')),'member_role');
async function saved(locator){const [r]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/action'&&r.request().method()==='POST'),locator.click()]);if(r.status()!==200){const v=await r.json();http.push({path:'/api/action',status:r.status(),code:v.code,class:v.class,frames:v.frames});}check(r.status()===200,'action_saved');await page.waitForFunction(()=>!busy);}
async function logout(){const [r]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/logout'&&r.request().method()==='POST'),page.locator('#logout').click()]);check(r.status()===200,'logout_confirmed');await page.waitForFunction(()=>!authInFlight&&!busy);await page.locator('#login').waitFor({state:'visible'});}
async function snapshot(){return page.evaluate(()=>fetch('/api/today').then(r=>r.json()).then(j=>j.views[0].state));}
stage='viewport_matrix';for(const width of [320,390,768,1280])for(const lang of ['0','1','2'])for(const theme of ['light','dark']){
await page.setViewportSize({width,height:900});await page.locator('#lang').selectOption(lang);await page.locator('#theme').selectOption(theme);
for(const tab of ['today','training','nutrition','recovery','intake','review','history']){
await page.locator(`[data-tab=${tab}]`).click();check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'overflow_'+width+'_'+lang+'_'+tab);}
if(width===390||width===1280){await page.locator('[data-tab=training]').click();const file=`integration-${width}-${lang}-${theme}.png`;await page.screenshot({path:path.join(c.screenshots,file),fullPage:false});screenshots.push(file);}}
stage='record_reload_relogin';await page.locator('#lang').selectOption('0');await page.locator('[data-tab=training]').click();const first=page.locator('form[data-record]').first();
await first.locator('[name=load]').fill('0');await first.locator('[name=reps]').fill('8');await first.locator('[name=rir]').fill('0');await first.locator('[name=rpe]').fill('');await first.locator('button').click();await page.locator('#message').filter({hasText:'Opgeslagen'}).waitFor();
await page.reload();await page.locator('#app').waitFor({state:'visible'});await page.locator('[data-tab=training]').click();check(await page.locator('form[data-record]').first().locator('[name=rir]').inputValue()==='0','reload_zero');
await logout();await login('b');await page.locator('[data-tab=training]').click();check(await page.locator('form[data-record]').first().locator('[name=reps]').inputValue()==='8','relogin_durable');
stage='B_complete_review_apply_restore';await saved(page.locator('[data-action=finish_workout]').first());
check((await snapshot()).workoutClosures.length===1,'B_explicit_closure');
await page.locator('[data-tab=review]').click();const exercise=page.locator('form[data-exercise]').first();await exercise.locator('[name=reps]').fill('11');await saved(exercise.locator('button'));
let state=await snapshot();check(state.active.version===1&&state.review.target.training.sessions[0].exercises[0].reps===11,'B_draft_not_applied');
await page.setViewportSize({width:390,height:900});await page.screenshot({path:path.join(c.screenshots,'integration-B-review.png'),fullPage:true});screenshots.push('integration-B-review.png');
await saved(page.locator('[data-action=confirm]'));check((await snapshot()).active.version===1,'B_confirm_not_apply');await saved(page.locator('[data-action=apply]'));
const portion=page.locator('form[data-portion]').first();await portion.locator('[name=grams]').fill('225');await saved(portion.locator('button'));await saved(page.locator('[data-action=confirm]'));await saved(page.locator('[data-action=apply]'));
state=await snapshot();check(state.active.version===3&&state.active.nutrition.meals[0].items[0].grams===225,'B_exact_portion_applied');
await page.locator('[data-tab=history]').click();await saved(page.locator('[data-action=restore][data-version="2"]'));await page.locator('[data-tab=review]').click();await saved(page.locator('[data-action=confirm]'));await saved(page.locator('[data-action=apply]'));
state=await snapshot();check(state.active.version===4&&state.history.length===4&&state.history.at(-1).restores===2,'B_restore_new_version');
stage='server_boundaries';const boundaries=await page.evaluate(async()=>{const today=await fetch('/api/today').then(r=>r.json());const plain=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});const role=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF':today.csrf},body:JSON.stringify({workspace:today.views[0].workspace,request_id:crypto.randomUUID(),version:today.views[0].version,request:{action:'approve',data:{}}})});return [plain.status,role.status];});check(boundaries.every(x=>x===403),'csrf_and_client_role_denied');
await logout();await login('trainer');check((await page.locator('#tabs [data-tab]').evaluateAll(es=>es.map(e=>e.dataset.tab))).join(',')==='clients,today,review,account','trainer_minimal_tabs');check(!(await page.locator('#content').innerText()).includes('Rijst'),'trainer_no_food_log');
stage='A_separate_roles';await logout();await login('a');await page.locator('[data-tab=recovery]').click();const recovery=page.locator('form[data-recovery]').last();await recovery.locator('[name=value]').fill('6');await saved(recovery.locator('button'));await page.locator('[data-tab=review]').click();await saved(page.locator('[data-action=confirm]'));
check((await snapshot()).status==='trainer_pending','A_requires_trainer');await logout();await login('trainer');await page.locator('[data-tab=review]').click();await saved(page.locator('[data-action=approve]'));
check((await snapshot()).active.version===1,'A_approval_not_apply');await logout();await login('a');await page.locator('[data-tab=review]').click();await saved(page.locator('[data-action=apply]'));check((await snapshot()).active.version===2,'A_separate_application');
stage='comparison_outbox';await page.locator('[data-tab=today]').click();await saved(page.locator('[data-compare]'));
check((await snapshot()).comparison.facts.length===4,'complete_comparison');await saved(page.locator('[data-notice]').first());
await page.reload();await page.locator('#app').waitFor({state:'visible'});
check(await page.evaluate(()=>fetch('/api/today').then(r=>r.json()).then(j=>j.views[0].notices.some(n=>n.status==='seen'))),'notice_seen_survives_reload');
await page.locator('#content details').first().locator('summary').click();await page.locator('[data-guide="1"]').click();await page.locator('#content details').first().locator('summary').click();check(await page.locator('#content').innerText().then(x=>x.includes('herstelregistratie')),'guided_expectation');
await logout();await page.locator('#login').waitFor({state:'visible'});const noLogin=await page.evaluate(()=>fetch('/api/today').then(r=>r.status));check(noLogin===403,'signed_out_denied');check(errors.length===0,'browser_errors');
await context.close();console.log(JSON.stringify({status:'PASS',checks,viewports:[320,390,768,1280],languages:['NL','EN','DE'],themes:['light','dark'],screenshots,physical_phone_test:false,hosted_calls:0}));
}catch(e){console.log(JSON.stringify({status:'NO_GO',stage,checks,error:e.message.slice(0,150),http,errors}));process.exitCode=2;}finally{await browser.close();}})();
