"use strict";
const fs=require("node:fs"),p=require("node:path"),a=require("node:assert/strict");
const {chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const {server,allowed}=require("../serve.cjs"),{scenarios}=require("../fixtures.cjs");
const folder=process.argv[2],remote=process.argv.includes("--published");
if(!folder)throw Error("output_required");
const result={remote,checks:[],layouts:[],screenshots:[],errors:[],storage:[],requests:[]},check=(name,pass)=>{result.checks.push({name,pass:!!pass});a(pass,name);};
(async()=>{let s,b;
 try{
  let base="https://yourizorge.github.io/fitmetzorge-staging";
  if(!remote){s=server();await new Promise(r=>s.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+s.address().port;}
  b=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
  async function pageFor(width,height=900){
   const ctx=await b.newContext({viewport:{width,height},serviceWorkers:"block"});
   await ctx.addInitScript(()=>{
    window.__writes=[];
    for(const key of ["localStorage","sessionStorage","indexedDB"])Object.defineProperty(window,key,{get(){window.__writes.push(key);throw Error("storage_blocked");}});
    Object.defineProperty(document,"cookie",{get(){return "";},set(){window.__writes.push("cookie");}});
   });
   await ctx.route("**/*",r=>{const q=r.request(),u=new URL(q.url()),prefix=remote?"/fitmetzorge-staging":"";
    const ok=q.method()==="GET"&&u.origin===new URL(base).origin&&allowed.includes(u.pathname.slice(prefix.length));
    result.requests.push({path:u.pathname,allowed:ok});if(!ok){result.errors.push("unexpected_egress");return r.abort();}return r.continue();});
   const page=await ctx.newPage();page.on("pageerror",e=>result.errors.push(e.message));
   await page.goto(base+"/proactive-signals-demo/index.html",{waitUntil:"networkidle"});
   return {ctx,page};
  }
  for(const width of [320,390,768,1280])for(const locale of ["nl","en","de"])for(const theme of ["light","dark"]){
   const {ctx,page}=await pageFor(width),label=width+"-"+locale+"-"+theme;
   await page.selectOption("#language",locale);await page.selectOption("#theme",theme);
   check(label+" asset",await page.locator("header img").evaluate(e=>e.naturalWidth>0));
   check(label+" automatic card before any question",await page.locator("#count").innerText()==="1");
   check(label+" four comparable facts",await page.locator(".metric").count()===4);
   check(label+" no apply action",await page.locator("#apply,[data-action=apply]").count()===0);
   await page.locator("#calculation-detail summary").click();check(label+" traceable calculation",(await page.locator("#calculations").innerText()).includes("450 + 450 + 450"));
   if(width===390||width===1280&&locale==="en"&&theme==="light"){
    const file=p.join(folder,(remote?"published-":"local-")+label+".png");await page.screenshot({path:file,fullPage:true});result.screenshots.push(file);
   }
   await page.locator("#replay").click();check(label+" duplicate source no card",await page.locator("#count").innerText()==="1");check(label+" duplicate source no revision",await page.locator("#history li").count()===1);
   await page.locator("#review").click();check(label+" reviewed",await page.locator("#count").innerText()==="0");
   await page.locator("#correct").click();check(label+" new source new review",await page.locator("#count").innerText()==="1"&&await page.locator("#history li").count()===2);
   await page.locator("#restore").click();check(label+" restore v3 not deletion",await page.locator("#history li").count()===3);
   await page.locator("#dismiss").click();check(label+" dismiss keeps history",await page.locator("#count").innerText()==="0"&&await page.locator("#history li").count()===3);
   const overflow=await page.evaluate(()=>[...document.querySelectorAll("main *,header *")].filter(e=>{const r=e.getBoundingClientRect();return e.tagName!=="OPTION"&&r.width&&r.height&&(r.left<-.5||r.right>innerWidth+.5);}).map(e=>e.tagName+":"+e.className));
   result.layouts.push({label,overflow});check(label+" no overflow",overflow.length===0);
   const stores=await page.evaluate(()=>window.__writes);result.storage.push(...stores);check(label+" no storage",stores.length===0);
   await page.reload({waitUntil:"networkidle"});check(label+" refresh resets",await page.locator("#history li").count()===1&&await page.locator("#count").innerText()==="1");
   await ctx.close();
  }
  const {ctx,page}=await pageFor(390,844);
  for(const locale of ["nl","en","de"]){
   await page.selectOption("#language",locale);
   for(const n of scenarios){
    await page.selectOption("#scenario",n);
    const candidate=["changes","sleep_only","recovery_only","nutrition_only","training_only","zero","independent","self_reported"].includes(n);
    check(locale+" "+n+" pending matches contract",await page.locator("#count").innerText()===(candidate?"1":"0"));
    if(["current","unclassified","recurring","expired_context","missing_context","technical","unclear"].includes(n))check(locale+" "+n+" facts retained",await page.locator(".metric").count()===4);
    if(["missing","partial","conflict","expired_source","no_trainer","consent_revoked","entitlement_revoked"].includes(n))check(locale+" "+n+" no partial result",await page.locator(".metric").count()===0);
   }
  }
  await page.selectOption("#scenario","changes");await page.selectOption("#language","nl");await page.locator("#review").click();
  await page.selectOption("#language","de");check("language preserves review state",await page.locator("#count").innerText()==="0");
  await page.locator("#correct").click();await page.locator("#expire").click();check("expiry withdraws",await page.locator("#review").count()===0&&await page.locator(".metric").count()===0);
  await page.locator("#reset").click();await page.locator("#revoke").click();check("revocation withdraws but chat remains",(await page.locator("#access").innerText()).includes("Verfuegbar")&&await page.locator(".metric").count()===0);
  await ctx.close();check("no errors or unexpected egress",result.errors.length===0);result.status="BROWSER_PASS";
 }catch(e){result.status="BROWSER_FAIL";result.failure=e.message;process.exitCode=1;}
 finally{if(b)await b.close();if(s)await new Promise(r=>s.close(r));fs.writeFileSync(p.join(folder,(remote?"published":"local")+"-browser-"+Date.now()+".json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify({status:result.status,checks:result.checks.length,layouts:result.layouts.length,failure:result.failure,screenshots:result.screenshots}));}
})();
