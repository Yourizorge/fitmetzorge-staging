"use strict";
const fs=require("node:fs"),p=require("node:path"),a=require("node:assert/strict"),{chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright"),{server,allowed}=require("../serve.cjs");
const folder=process.argv[2],remote=process.argv.includes("--published"),result={remote,checks:[],layouts:[],requests:[],errors:[],storage:[],screenshots:[]},check=(name,pass)=>{result.checks.push({name,pass:!!pass});a(pass,name);};
(async()=>{let s,b;
try{
 let base="https://yourizorge.github.io/fitmetzorge-staging";
 if(!remote){s=server();await new Promise(r=>s.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+s.address().port;}
 b=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
 async function open(width,height=900){
  const ctx=await b.newContext({viewport:{width,height},serviceWorkers:"block"});
  await ctx.addInitScript(()=>{window.__writes=[];for(const k of ["localStorage","sessionStorage","indexedDB"])Object.defineProperty(window,k,{get(){window.__writes.push(k);throw Error("storage_blocked");}});Object.defineProperty(document,"cookie",{get(){return "";},set(){window.__writes.push("cookie");}});});
  await ctx.route("**/*",r=>{const q=r.request(),u=new URL(q.url()),prefix=remote?"/fitmetzorge-staging":"",ok=q.method()==="GET"&&u.origin===new URL(base).origin&&allowed.includes(u.pathname.slice(prefix.length));result.requests.push({path:u.pathname,allowed:ok});if(!ok){result.errors.push("egress");return r.abort();}return r.continue();});
  const page=await ctx.newPage();page.on("pageerror",e=>result.errors.push(e.message));await page.goto(base+"/independent-intake-demo/index.html",{waitUntil:"networkidle"});return {page,ctx};
 }
 async function overflow(page,key){const list=await page.evaluate(()=>[...document.querySelectorAll("main *,header *")].filter(e=>{const r=e.getBoundingClientRect();return e.tagName!=="OPTION"&&r.width&&r.height&&(r.left<-.5||r.right>innerWidth+.5);}).map(e=>e.tagName+"."+e.className));result.layouts.push({key,overflow:list});check(key+" no overflow",list.length===0);}
 for(const width of [320,390,768,1280])for(const locale of ["nl","en","de"])for(const theme of ["light","dark"]){
  const {page,ctx}=await open(width),key=width+"-"+locale+"-"+theme;
  await page.selectOption("#language",locale);await page.selectOption("#theme",theme);check(key+" image",await page.locator("header img").evaluate(x=>x.naturalWidth>0));
  check(key+" explicit intake",await page.locator("#f-goal").inputValue()==="strength");await overflow(page,key+" intake");
  await page.click("#build");check(key+" three sessions",await page.locator("#proposal .session").count()===3);check(key+" no trainer",await page.locator("#actor,#approve").count()===0);check(key+" no early activation",await page.locator("#activate").count()===0);
  await page.selectOption("#ex-0-0","bandrow");await page.fill("#reps-0-0","9");await page.click("#edit-ex-0-0");check(key+" edit",await page.locator("#ex-0-0").inputValue()==="bandrow"&&await page.locator("#reps-0-0").inputValue()==="9");
  await page.click("#confirm");await page.click("#double-confirm");check(key+" duplicate confirm no version",!(await page.locator("#versions").innerText()).includes("Plan: 1"));
  await page.click("#activate");const versions=await page.locator("#versions").innerText();check(key+" v1",versions.includes("Plan: 1"));await page.click("#double-activate");check(key+" duplicate activate",await page.locator("#versions").innerText()===versions);
  await page.click("#build");await page.fill("#reps-0-0","10");await page.click("#edit-ex-0-0");await page.click("#confirm");await page.click("#activate");check(key+" v2",(await page.locator("#versions").innerText()).includes("Plan: 1 / 2"));
  await page.click("#restore");check(key+" restore requires confirm",await page.locator("#activate").count()===0);await page.click("#confirm");await page.click("#activate");check(key+" v3 keeps history",(await page.locator("#versions").innerText()).includes("Plan: 1 / 2 / 3"));
  await overflow(page,key+" plan");
  if(width===390||width===1280&&locale==="nl"&&theme==="light"){const path=p.join(folder,(remote?"published-":"local-")+key+".png");await page.screenshot({path,fullPage:true});result.screenshots.push(path);}
  check(key+" no storage",(await page.evaluate(()=>window.__writes)).length===0);await page.reload({waitUntil:"networkidle"});check(key+" refresh resets",await page.locator("#audit li").count()===0&&await page.locator("#confirm").count()===0);await ctx.close();
 }
 const {page,ctx}=await open(390,480),positive=["complete","favorites","limited","allergy","imperial"];
 for(const locale of ["nl","en","de"]){await page.selectOption("#language",locale);const scenarios=await page.locator("#scenario option").evaluateAll(es=>es.map(e=>e.value));for(const name of scenarios){await page.selectOption("#scenario",name);await page.click("#build");check(locale+" "+name+" gate",await page.locator("#confirm").count()===(positive.includes(name)?1:0));}}
 await page.selectOption("#language","nl");await page.selectOption("#scenario","complete");await page.click("#build");await page.fill("#sets-0-0","3");await page.click("#edit-ex-0-0");check("unsupported sets explained, no partial",/geen passende bronregel/.test(await page.locator("#edit-result").innerText())&&await page.locator("#sets-0-0").inputValue()==="2");
 await page.locator("#intake details").nth(1).locator("summary").click();await page.locator('input[name=days][value=mon]').uncheck();await page.locator('input[name=days][value=tue]').check();await page.selectOption("#f-unit","lb");await page.click("#save");check("source update clears old proposal",await page.locator("#confirm").count()===0);await page.click("#build");check("new days and units",(await page.locator("#proposal").innerText()).includes("dinsdag")&&(await page.locator("#proposal").innerText()).includes("lb"));
 await page.selectOption("#meal-0","ricelentils");await page.click("#edit-meal-0");check("meal replacement",await page.locator("#meal-0").inputValue()==="ricelentils");await page.selectOption("#food-0-0","beans");await page.click("#edit-food-0-0");check("food replacement",await page.locator("#food-0-0").inputValue()==="beans");
 await page.locator("#confirm").focus();await page.keyboard.press("Enter");check("keyboard confirm",await page.locator("#activate").count()===1);await overflow(page,"keyboard-space");await page.click("#stale");check("source conflict disables activation",await page.locator("#activate").count()===0);
 await page.click("#reset");await page.click("#build");await page.click("#reject");check("reject",await page.locator("#activate").count()===0&&await page.locator("#confirm").count()===0);
 await page.click("#reset");await page.click("#revoke");check("revocation prevents intake processing",await page.locator("#save").isDisabled());await page.click("#build");check("revocation prevents plan",await page.locator("#confirm").count()===0);
 await page.selectOption("#scenario","incomplete");await page.selectOption("#f-goal","strength");await page.click("#save");await page.click("#build");check("explicit completion works",await page.locator("#confirm").count()===1);
 await ctx.close();check("no browser errors or egress",result.errors.length===0);result.status="BROWSER_PASS";
}catch(e){result.status="BROWSER_FAIL";result.failure=e.message;process.exitCode=1;}
finally{if(b)await b.close();if(s)await new Promise(r=>s.close(r));fs.writeFileSync(p.join(folder,(remote?"published":"local")+"-browser-"+Date.now()+".json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify({status:result.status,checks:result.checks.length,layouts:result.layouts.length,errors:result.errors,failure:result.failure,screenshots:result.screenshots}));}
})();
