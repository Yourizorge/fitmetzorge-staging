'use strict';
const fs=require('node:fs'),p=require('node:path'),a=require('node:assert/strict'),c=require('node:crypto'),{chromium}=require('C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {server,allowed}=require('./serve.cjs'),R=require('../../daily-coach-demo/review.js'),C=require('../../daily-coach-demo/copy.js'),out=process.argv[2],remote=process.argv.includes('--published'),smoke=process.argv.includes('--smoke'),stamp=Date.now();
const result={remote,checks:[],layouts:[],errors:[],screenshots:[],source_sha256:Object.fromEntries(fs.readdirSync('daily-coach-demo').map(f=>[f,c.createHash('sha256').update(fs.readFileSync('daily-coach-demo/'+f)).digest('hex')]))},check=(name,pass)=>{result.checks.push({name,pass:!!pass});a(pass,name);};
(async()=>{let instance,browser;try{
 let base='https://yourizorge.github.io/fitmetzorge-staging';if(!remote){instance=server();await new Promise(r=>instance.listen(0,'127.0.0.1',r));base='http://127.0.0.1:'+instance.address().port;}
 browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 async function open(width,height=900){
  const ctx=await browser.newContext({viewport:{width,height},serviceWorkers:'block'});
  await ctx.addInitScript(()=>{window.__writes=[];for(const key of ['localStorage','sessionStorage','indexedDB'])Object.defineProperty(window,key,{get(){window.__writes.push(key);throw Error('storage');}});Object.defineProperty(document,'cookie',{get(){return '';},set(){window.__writes.push('cookie');}});});
  await ctx.route('**/*',r=>{const q=r.request(),u=new URL(q.url()),prefix=remote?'/fitmetzorge-staging':'',ok=q.method()==='GET'&&u.origin===new URL(base).origin&&allowed.includes(u.pathname.slice(prefix.length));if(!ok){result.errors.push('unexpected request');return r.abort();}return r.continue();});
  const page=await ctx.newPage();page.on('pageerror',e=>result.errors.push(e.message));await page.goto(base+'/daily-coach-demo/index.html',{waitUntil:'networkidle'});return {ctx,page};
 }
 async function layout(page,key){
  const bad=await page.evaluate(()=>[...document.querySelectorAll('main *,header *')].filter(e=>{const r=e.getBoundingClientRect();return e.tagName!=='OPTION'&&r.width&&r.height&&(r.left<-.5||r.right>innerWidth+.5);}).map(e=>e.tagName+'.'+e.className));
  result.layouts.push({key,bad});check(key+' overflow',bad.length===0);check(key+' unique IDs',await page.locator('[id]').evaluateAll(es=>new Set(es.map(e=>e.id)).size===es.length));
 }
 for(const width of smoke?[390]:[320,390,768,1280])for(const language of smoke?['nl']:['nl','en','de'])for(const theme of smoke?['light']:['light','dark']){
  const {page,ctx}=await open(width),key=width+'-'+language+'-'+theme,l=['nl','en','de'].indexOf(language);
  await page.selectOption('#language',language);await page.selectOption('#theme',theme);
  check(key+'18 scenarios',await page.locator('#scenario-buttons button').count()===18);check(key+' brand bitmap',await page.locator('header img').evaluate(e=>e.naturalWidth>0));check(key+' no trainer B',await page.locator('#actor-label').isHidden());
  for(const spec of R.scenarios){
   await page.click('#test-'+spec.id);check(key+' '+spec.id+' visible result',await page.locator('#verdict').getAttribute('data-result')==='pass');
   check(key+' '+spec.id+' title',await page.locator('#scenario-title').innerText()===spec.title[l]);check(key+' '+spec.id+' explanation',await page.locator('#expectation').innerText().then(x=>x.includes(C.reason(spec.reason,l))));await layout(page,key+' '+spec.id);
  }
  await page.click('#test-record');check(key+' actual zero not missing',await page.locator('.record[data-id^="training:"] .actual').first().innerText()==='0');check(key+' independent self-report',await page.locator('.record[data-id^="training:"]').first().innerText().then(x=>x.includes('RIR 0 / RPE 7')));
  await page.click('#test-edit');check(key+' pending edit not applied',await page.locator('#training-plan').innerText().then(x=>x.includes(C.get('mon',l)))&&await page.locator('#delta').innerText().then(x=>x.includes(C.get('fri',l))));check(key+' approvals retired',await page.locator('#apply').count()===0&&await page.locator('#accept').count()===1);
  await page.click('#test-consent');check(key+' consent blocks controls',await page.locator('#save').isDisabled()&&await page.locator('#arrive').isDisabled());
  if(language==='nl'&&(width===390||width===1280)){await page.click('#test-arrive');for(const id of ['today','registrations','proposal']){await page.locator('#'+id).scrollIntoViewIfNeeded();const file=p.join(out,(remote?'published':'local')+'-'+stamp+'-'+key+'-'+id+'.png');await page.screenshot({path:file});result.screenshots.push(file);}}
  check(key+' no storage',(await page.evaluate(()=>window.__writes)).length===0);await ctx.close();
 }
 const {page,ctx}=await open(390,700);
 await page.click('#start');check('guided first previous disabled',await page.locator('#previous').isDisabled());
 for(let i=1;i<18;i++){await page.click('#next');check('guided'+i,await page.locator('#step').innerText()===(i+1)+' / 18'&&await page.locator('#verdict').getAttribute('data-result')==='pass');}
 check('guided last next disabled',await page.locator('#next').isDisabled());await page.click('#previous');check('guided back',await page.locator('#step').innerText()==='17 / 18');
 for(const route of ['A','B']){
  await page.selectOption('#route',route);await page.click('#arrive');await page.click('#accept');check(route+' no automatic apply',await page.locator('#versions').getAttribute('data-count')==='1');
  if(route==='A'){check('A approval wrong actor disabled',await page.locator('#approve').isDisabled());await page.selectOption('#actor','trainer');await page.click('#approve');check('A separate member apply',await page.locator('#apply').isDisabled());await page.selectOption('#actor','member');}
  await page.click('#apply');check(route+' new version',await page.locator('#versions').getAttribute('data-count')==='2');
  await page.selectOption('#time','20:00');await page.click('#edit-time');await page.click('#accept');if(route==='A'){await page.selectOption('#actor','trainer');await page.click('#approve');await page.selectOption('#actor','member');}await page.click('#apply');await page.click('#restore');await page.click('#accept');if(route==='A'){await page.selectOption('#actor','trainer');await page.click('#approve');await page.selectOption('#actor','member');}await page.click('#apply');check(route+' restore new v4',await page.locator('#versions').getAttribute('data-count')==='4');
 }
 await page.selectOption('#route','B');await page.click('#arrive');await page.click('#accept');await page.fill('#value','0');await page.fill('#rir','0');await page.fill('#rpe','7');await page.click('#save');
 check('manual registration invalidates approval',await page.locator('#apply').count()===0&&await page.locator('#accept').count()===1);
 check('manual record kept',await page.locator('.record .actual').first().innerText()==='0');
 await page.selectOption('#day','fri');await page.click('#edit-day');await page.selectOption('#meal','20:00');await page.click('#edit-meal');await page.click('#accept');await page.click('#apply');
 check('manual both plans applied',await page.locator('#training-plan').innerText().then(x=>x.includes('Vrijdag'))&&await page.locator('#nutrition-plan .plan-item').first().innerText().then(x=>x.startsWith('20:00')));
 await page.locator('#audit-title').click();
 check('old actual retained history',await page.locator('#record-history').innerText().then(x=>x.includes('1 Geregistreerd')));
 await page.click('#correct');check('new source cannot reuse old checkin rule',await page.locator('#state').getAttribute('data-state')==='facts'&&await page.locator('#message').innerText().then(x=>x.includes('regel ontbreekt')));
 await layout(page,'manual');await page.reload({waitUntil:'networkidle'});check('refresh reset',await page.locator('#versions').getAttribute('data-count')==='1'&&await page.locator('#value').inputValue()===''&&await page.locator('#audit li').count()===0);
 await ctx.close();check('no errors/egress',result.errors.length===0);result.status='BROWSER_PASS';
 }catch(e){result.status='BROWSER_FAIL';result.failure=e.message;process.exitCode=1;}finally{if(browser)await browser.close();if(instance)await new Promise(r=>instance.close(r));fs.writeFileSync(p.join(out,(remote?'published':'local')+'-browser-'+Date.now()+'.json'),JSON.stringify(result,null,2),{flag:'wx'});console.log(JSON.stringify({status:result.status,checks:result.checks.length,layouts:result.layouts.length,errors:result.errors,failure:result.failure}));}
})();
