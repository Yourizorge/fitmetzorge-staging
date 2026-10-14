'use strict';
const path=require('node:path');
(async()=>{let raw='';for await(const c of process.stdin)raw+=c;const p=JSON.parse(raw);
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(p.url))throw Error('loopback');
const {chromium}=require(p.playwright),browser=await chromium.launch();let checks=0;
try{const context=await browser.newContext(),page=await context.newPage();const errors=[];
page.on('pageerror',e=>errors.push(e.name));
await context.route('**/*',r=>new URL(r.request().url()).origin===p.url?r.continue():r.abort());
await page.goto(p.url);await page.locator('[name=email]').fill(p.account.email);await page.locator('[name=password]').fill(p.account.password);await page.locator('#login button').click();await page.locator('[data-registration12]').waitFor();
for(const width of [390,1280])for(const language of ['0','1','2'])for(const theme of ['light','dark']){
 await page.setViewportSize({width,height:900});await page.locator('#lang').selectOption(language);await page.locator('#theme').selectOption(theme);
 if(!await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))throw Error('overflow');checks++;
 if(width===390&&language==='0')await page.screenshot({path:path.join(p.screenshots,'registration12-'+theme+'.png'),fullPage:true});
}
await page.locator('[name=load0]').fill('0');await page.locator('[name=reps0]').fill('0');await page.locator('[name=rir0]').fill('0');await page.locator('[name=rpe0]').fill('');
const [saved]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/action'),page.locator('[data-registration12] > button').click()]);
if(saved.status()!==200)throw Error('registration_save');checks++;
await page.waitForFunction(()=>!busy);await page.reload();await page.locator('[data-registration12]').waitFor();
if(await page.locator('[name=rir0]').inputValue()!=='0'||await page.locator('[name=rpe0]').inputValue()!=='')throw Error('null_zero_reload');checks++;
await page.locator('#logout').click();await page.locator('#login').waitFor({state:'visible'});
if(errors.length)throw Error('browser_error');checks++;
console.log(JSON.stringify({status:'PASS',checks,languages:['NL','EN','DE'],viewports:[390,1280],themes:['light','dark'],physical_phone:false}));
}catch(e){console.log(JSON.stringify({status:'NO_GO',checks,error:e.message}));process.exitCode=2;}finally{await browser.close();}})();
