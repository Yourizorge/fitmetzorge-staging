"use strict";
const fs=require("node:fs"),path=require("node:path"),a=require("node:assert/strict");
const {chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const {server,allowed}=require("../serve.cjs");
const root=path.resolve(__dirname,"../../.."),out=process.argv[2];if(!out)throw Error("output_required");
const remote=process.argv.includes("--published"),result={remote,checks:[],layouts:[],screenshots:[],errors:[],storage:[],requests:[]};
const check=(n,v)=>{result.checks.push({name:n,pass:!!v});a(v,n);};
(async()=>{let s,b;try{
 let base="https://yourizorge.github.io/fitmetzorge-staging";
 if(!remote){s=server();await new Promise(r=>s.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+s.address().port;}
 b=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
 for(const width of [320,390,768,1280])for(const locale of ["nl","en","de"])for(const theme of ["light","dark"]){
  const context=await b.newContext({viewport:{width,height:900},serviceWorkers:"block"}),page=await context.newPage();
  const label=width+"-"+locale+"-"+theme;
  await context.addInitScript(()=>{window.__writes=[];for(const key of ["localStorage","sessionStorage","indexedDB"]){Object.defineProperty(window,key,{get(){window.__writes.push(key);throw Error("storage_blocked");}});}Object.defineProperty(document,"cookie",{get(){return "";},set(){window.__writes.push("cookie");}});});
  await context.route("**/*",route=>{const r=route.request(),u=new URL(r.url()),prefix=remote?"/fitmetzorge-staging":"";
   const ok=r.method()==="GET"&&u.origin===new URL(base).origin&&allowed.includes(u.pathname.slice(prefix.length));
   result.requests.push({path:u.pathname,allowed:ok});if(!ok){result.errors.push("unexpected_egress");return route.abort();}return route.continue();});
  page.on("pageerror",e=>result.errors.push(label+":"+e.message));
  await page.goto(base+"/workout-reflection-demo/index.html",{waitUntil:"networkidle"});
  await page.selectOption("#language",locale);await page.selectOption("#theme",theme);
  check(label+" asset",await page.locator("header img").evaluate(e=>e.naturalWidth>0));
  check(label+" manual reflection",await page.locator("#reflect").isDisabled());
  await page.locator("#register").click();await page.locator("#reflect").click();
  check(label+" three exercises",await page.locator(".comparison-row").count()===3);
  await page.locator('[data-action="member_accept"]').click();check(label+" no premature apply",await page.locator('[data-action="apply"]').count()===0);
  await page.selectOption("#role","trainer");await page.locator('[data-action="trainer_approve"]').click();
  check(label+" plan still v3",(await page.locator("#plan-version").innerText()).endsWith("3"));
  await page.locator('[data-action="apply"]').click();check(label+" new version",(await page.locator("#plan-version").innerText()).endsWith("4"));
  await page.locator('[data-action="restore"]').click();await page.selectOption("#role","member");
  await page.locator('[data-action="member_accept"]').click();await page.selectOption("#role","trainer");await page.locator('[data-action="trainer_approve"]').click();await page.locator('[data-action="apply"]').click();
  check(label+" restored new version",(await page.locator("#plan-version").innerText()).endsWith("5"));
  check(label+" preserved history",await page.locator("#history .version").count()===2);
  const overflow=await page.evaluate(()=>[...document.querySelectorAll("main *,header *,.scope")].filter(e=>{
   const r=e.getBoundingClientRect(),s=getComputedStyle(e);return e.tagName!=="OPTION"&&r.width&&r.height&&s.visibility==="visible"&&(r.left<-.5||r.right>innerWidth+.5);
  }).map(e=>e.tagName+":"+e.className));
  result.layouts.push({label,overflow});check(label+" no overflow",overflow.length===0);
  if(width===390&&locale==="nl"||width===1280&&locale==="en"&&theme==="light"){
   const f=path.join(out,(remote?"published-":"local-")+label+".png");await page.screenshot({path:f,fullPage:true});result.screenshots.push(f);
  }
  await page.reload({waitUntil:"networkidle"});check(label+" refresh resets",(await page.locator("#reg-version").innerText())==="v0");
  const storage=await page.evaluate(()=>window.__writes);result.storage.push(...storage);check(label+" no storage",storage.length===0);
  await context.close();
 }
 const ctx=await b.newContext({viewport:{width:390,height:844},serviceWorkers:"block"}),page=await ctx.newPage();
 await ctx.route("**/*",route=>{if(!route.request().url().startsWith(base+"/")||route.request().method()!=="GET")return route.abort();return route.continue();});
 page.on("pageerror",e=>result.errors.push(e.message));await page.goto(base+"/workout-reflection-demo/index.html");
 for(const name of ["missing_set","missing_rule","ambiguous_rules","step_off_grid","no_trainer","current","self_reported","expired","missing","no_analysis_consent","book_expired","stale_request"]){
  await page.selectOption("#scenario",name);await page.locator("#register").click();await page.locator("#reflect").click();
  check(name+" no applicable action",await page.locator("#actions button").count()===0);
  if(name==="step_off_grid"){await page.locator("#reason-detail summary").click();check("W2 step visible",(await page.locator("#reasons").innerText()).includes("2,5"));}
 }
 await page.selectOption("#scenario","normal");const input=page.locator('input[data-field="rir"]').first();await input.fill("0");
 await page.selectOption("#language","de");check("language keeps zero",await page.locator('input[data-field="rir"]').first().inputValue()==="0");
 await page.locator("#register").click();await page.locator("#reflect").click();check("unlisted edit facts only",await page.locator("#actions button").count()===0);
 await page.selectOption("#scenario","normal");await page.locator("#register").click();await page.locator("#reflect").click();await page.locator('[data-action="member_reject"]').click();
 check("rejection no apply",await page.locator("#actions button").count()===0);
 await page.selectOption("#scenario","normal");await page.locator("#register").click();await page.locator("#reflect").click();await page.locator('[data-action="member_accept"]').click();
 await page.selectOption("#role","trainer");await page.locator('[data-action="trainer_block"]').click();check("trainer block terminal",await page.locator("#actions button").count()===0);
 await page.selectOption("#scenario","normal");await page.locator("#register").click();await page.locator("#reflect").click();
 await page.selectOption("#source-event","consent_revoked");await page.locator("#inject").click();check("revocation stops review",await page.locator("#actions button").count()===0);
 await ctx.close();check("no browser errors",result.errors.length===0);result.status="BROWSER_PASS";
 }catch(e){result.status="BROWSER_FAIL";result.failure=e.message;process.exitCode=1;}finally{if(b)await b.close();if(s)await new Promise(r=>s.close(r));fs.writeFileSync(path.join(out,(remote?"published":"local")+"-browser.json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify({status:result.status,checks:result.checks.length,layouts:result.layouts.length,failure:result.failure,screenshots:result.screenshots}));}})();
