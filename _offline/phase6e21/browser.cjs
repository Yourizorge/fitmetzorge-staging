'use strict';
const fs=require('node:fs'),p=require('node:path'),a=require('node:assert/strict'),c=require('node:crypto'),{chromium}=require('C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {server,allowed}=require('./serve.cjs'),R=require('../../complete-recording-demo/review.js'),C=require('../../complete-recording-demo/copy.js'),out=process.argv[2],remote=process.argv.includes('--published'),smoke=process.argv.includes('--smoke'),stamp=Date.now();
const result={remote,checks:[],layouts:[],errors:[],screenshots:[],source_sha256:Object.fromEntries(fs.readdirSync('complete-recording-demo').map(f=>[f,c.createHash('sha256').update(fs.readFileSync('complete-recording-demo/'+f)).digest('hex')]))},check=(name,pass)=>{result.checks.push({name,pass:!!pass});a(pass,name);};
(async()=>{let instance,browser;try{
 let base='https://yourizorge.github.io/fitmetzorge-staging';if(!remote){instance=server();await new Promise(r=>instance.listen(0,'127.0.0.1',r));base='http://127.0.0.1:'+instance.address().port;}
 browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 async function open(width,height=900){
  const ctx=await browser.newContext({viewport:{width,height},serviceWorkers:'block'});
  await ctx.addInitScript(()=>{window.__writes=[];for(const key of ['localStorage','sessionStorage','indexedDB'])Object.defineProperty(window,key,{get(){window.__writes.push(key);throw Error('storage');}});Object.defineProperty(document,'cookie',{get(){return '';},set(){window.__writes.push('cookie');}});});
  await ctx.route('**/*',r=>{const q=r.request(),u=new URL(q.url()),prefix=remote?'/fitmetzorge-staging':'',ok=q.method()==='GET'&&u.origin===new URL(base).origin&&allowed.includes(u.pathname.slice(prefix.length));if(!ok){result.errors.push('unexpected request');return r.abort();}return r.continue();});
  const page=await ctx.newPage();page.on('pageerror',e=>result.errors.push(e.message));await page.goto(base+'/complete-recording-demo/index.html',{waitUntil:'networkidle'});return {ctx,page};
 }
 async function layout(page,key){
  const bad=await page.evaluate(()=>[...document.querySelectorAll('main *,header *')].filter(e=>{const r=e.getBoundingClientRect();return e.tagName!=='OPTION'&&r.width&&r.height&&(r.left<-.5||r.right>innerWidth+.5);}).map(e=>e.tagName+'.'+e.className));
  result.layouts.push({key,bad});check(key+' overflow',bad.length===0);check(key+' unique IDs',await page.locator('[id]').evaluateAll(es=>new Set(es.map(e=>e.id)).size===es.length));
 }
 for(const width of smoke?[390]:[320,390,768,1280])for(const language of smoke?['nl']:['nl','en','de'])for(const theme of smoke?['light']:['light','dark']){
  const {page,ctx}=await open(width),key=width+'-'+language+'-'+theme,l=['nl','en','de'].indexOf(language);
  await page.selectOption('#language',language);await page.selectOption('#theme',theme);
  check(key+'20 scenarios',await page.locator('#scenario-buttons button').count()===20);check(key+' brand bitmap',await page.locator('header img').evaluate(e=>e.naturalWidth>0));check(key+' no trainer B',await page.locator('#actor-label').isHidden());
  for(const spec of R.scenarios){
   await page.click('#test-'+spec.id);check(key+' '+spec.id+' visible result',await page.locator('#verdict').getAttribute('data-result')==='pass');
   check(key+' '+spec.id+' title',await page.locator('#scenario-title').innerText()===spec.title[l]);check(key+' '+spec.id+' explanation',await page.locator('#expectation').innerText().then(x=>x.includes(C.reason(spec.reason,l))));await layout(page,key+' '+spec.id);
  }
  await page.click('#test-zero');check(key+' zero not missing',await page.locator('.set-row .reps').first().innerText()==='0'&&await page.locator('.set-row .load').first().innerText()==='0');check(key+' independent RIR/RPE',await page.locator('.set-row .rir').first().innerText()==='0'&&await page.locator('.set-row .rpe').first().innerText()===(l===1?'7.5':'7,5'));
  await page.click('#test-uneaten');check(key+' uneaten visible',await page.locator('.food-row').first().innerText().then(x=>x.includes(C.get('not_eaten',l))&&x.includes('0 g')));check(key+' remaining missing',await page.locator('.food-row').nth(1).innerText().then(x=>x.includes(C.get('missing',l))));
  await page.click('#test-reopen');check(key+' corrected completion reopened',await page.locator('#workout-status').getAttribute('data-closed')==='false');
  await page.click('#test-consent');check(key+' blocks new processing',await page.locator('#save').isDisabled()&&await page.locator('#save-food').isDisabled()&&await page.locator('#finish-day').isDisabled());
  if(language==='nl'&&(width===390||width===1280))for(const [scene,section]of [['full','registrations'],['food','food-log'],['correct','proposal']]){
   await page.click('#test-'+scene);await page.locator('#'+section).scrollIntoViewIfNeeded();const file=p.join(out,(remote?'published':'local')+'-'+stamp+'-'+key+'-'+section+'.png');await page.screenshot({path:file});result.screenshots.push(file);
  }
  check(key+' no storage',(await page.evaluate(()=>window.__writes)).length===0);await ctx.close();
 }
 const {page,ctx}=await open(390,740);
 await page.click('#start');check('guided previous disabled',await page.locator('#previous').isDisabled());for(let i=1;i<20;i++){await page.click('#next');check('guided '+i,await page.locator('#step').innerText()===(i+1)+' / 20'&&await page.locator('#verdict').getAttribute('data-result')==='pass');}
 check('guided last',await page.locator('#next').isDisabled());await page.click('#previous');check('guided back',await page.locator('#step').innerText()==='19 / 20');
 await page.click('#reset');
 const ws=await page.locator('#workout option').evaluateAll(es=>es.map(e=>e.value));check('two manual workouts',ws.length===2);
 for(const w of ws){await page.selectOption('#workout',w);const sets=await page.locator('#record option').evaluateAll(es=>es.map(e=>e.value));for(const id of sets){await page.selectOption('#record',id);await page.fill('#weight','0');await page.fill('#value','10');await page.fill('#rir','0');await page.fill('#rpe','7.5');await page.click('#save');check('manual set '+id,await page.locator('.set-row[data-id="'+id+'"] .reps').innerText()==='10');}
  check(w+' not auto-completed',await page.locator('#workout-status').getAttribute('data-closed')==='false');await page.click('#finish');check(w+' explicit completion',await page.locator('#workout-status').getAttribute('data-closed')==='true');
 }
 const meals=await page.locator('#meal-select option').evaluateAll(es=>es.map(e=>e.value));check('three manual meals',meals.length===3);
 const grams={rice:200,beans:150,vegetables:200,oil:10};for(const meal of meals){await page.selectOption('#meal-select',meal);const foods=await page.locator('#product option').evaluateAll(es=>es.map(e=>e.value));for(const id of foods){await page.selectOption('#product',id);await page.selectOption('#food-state','eaten');await page.fill('#grams',String(grams[id.split(':')[1]]));await page.click('#save-food');check('manual food '+id,await page.locator('.food-row[data-id="'+id+'"]').innerText().then(x=>x.includes('Gegeten')));}}
 check('manual subtotal',await page.locator('#food-summary').innerText().then(x=>x.includes('1725')&&x.includes('-75')));await page.click('#finish-day');check('manual planlog completion',await page.locator('#day-status').innerText().then(x=>x.includes('Expliciet')));
 await page.click('#arrive');await page.click('#accept');await page.fill('#value','9');await page.click('#save');check('source correction invalidates approval',await page.locator('#apply').count()===0&&await page.locator('#accept').count()===1);check('correction reopens workout',await page.locator('#workout-status').getAttribute('data-closed')==='false');
 await page.locator('#audit-title').click();check('old closure visible',await page.locator('#record-history').innerText().then(x=>x.includes('syn21-finish-')));
 for(const route of ['A','B']){
  await page.selectOption('#route',route);await page.click('#arrive');await page.click('#accept');check(route+' no automatic apply',await page.locator('#versions').getAttribute('data-count')==='1');
  if(route==='A'){check('A role separation',await page.locator('#approve').isDisabled());await page.selectOption('#actor','trainer');await page.click('#approve');check('A separate member apply',await page.locator('#apply').isDisabled());await page.selectOption('#actor','member');}
  await page.click('#apply');check(route+' v2',await page.locator('#versions').getAttribute('data-count')==='2');
  await page.selectOption('#time','20:00');await page.click('#edit-time');await page.click('#accept');if(route==='A'){await page.selectOption('#actor','trainer');await page.click('#approve');await page.selectOption('#actor','member');}await page.click('#apply');
  await page.click('#restore');await page.click('#accept');if(route==='A'){await page.selectOption('#actor','trainer');await page.click('#approve');await page.selectOption('#actor','member');}await page.click('#apply');check(route+' restore v4',await page.locator('#versions').getAttribute('data-count')==='4');
 }
 await layout(page,'manual');await page.reload({waitUntil:'networkidle'});check('refresh reset',await page.locator('#versions').getAttribute('data-count')==='1'&&await page.locator('#value').inputValue()===''&&await page.locator('#food-summary').getAttribute('data-count')==='0');
 await ctx.close();check('no errors/egress',result.errors.length===0);result.status='BROWSER_PASS';
 }catch(e){result.status='BROWSER_FAIL';result.failure=e.message;process.exitCode=1;}finally{if(browser)await browser.close();if(instance)await new Promise(r=>instance.close(r));fs.writeFileSync(p.join(out,(remote?'published':'local')+'-browser-'+Date.now()+'.json'),JSON.stringify(result,null,2),{flag:'wx'});console.log(JSON.stringify({status:result.status,checks:result.checks.length,layouts:result.layouts.length,errors:result.errors,failure:result.failure}));}
})();
