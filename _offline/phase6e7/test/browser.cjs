"use strict";
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),assert=require("node:assert/strict");
const {chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const root=path.resolve(__dirname,"../../.."),output=path.join(root,"supabase/.temp/phase6e7-browser");
const remote=process.argv.includes("--published"),allowed=new Set(["index.html","demo.css","app.js","model.js","copy.js","data.js","brand.png"]);
const results={published:remote,checks:[],layouts:[],requests:[],errors:[],screenshots:[],storage_attempts:[]};
const check=(name,value)=>{results.checks.push({name,pass:!!value});assert(value,name);};
(async()=>{
 fs.mkdirSync(output,{recursive:true});let server,browser;
 try{
  let base="https://yourizorge.github.io/fitmetzorge-staging/training-review-demo/";
  if(!remote){
   server=http.createServer((req,res)=>{
    const file=decodeURIComponent(new URL(req.url,"http://localhost").pathname).replace(/^\/training-review-demo\//,"")||"index.html";
    if(!allowed.has(file)){res.writeHead(404);res.end();return;}
    res.setHeader("Content-Type",file.endsWith(".html")?"text/html":file.endsWith(".css")?"text/css":file.endsWith(".png")?"image/png":"application/javascript");
    res.end(fs.readFileSync(path.join(root,"training-review-demo",file)));
   });
   await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
   base="http://127.0.0.1:"+server.address().port+"/training-review-demo/";
  }
  browser=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
  for(const width of [320,390,768,1280])for(const locale of ["nl","en","de"])for(const theme of ["light","dark"]){
   const context=await browser.newContext({viewport:{width,height:900},serviceWorkers:"block"});
   const page=await context.newPage(),label=width+"-"+locale+"-"+theme;
   await context.addInitScript(()=>{
    window.__storageAttempts=[];
    for(const key of ["localStorage","sessionStorage","indexedDB"]){
     Object.defineProperty(window,key,{get(){window.__storageAttempts.push(key);throw Error("forbidden_storage:"+key);},configurable:true});
    }
    Object.defineProperty(document,"cookie",{get(){window.__storageAttempts.push("cookie-read");return "";},set(){window.__storageAttempts.push("cookie-write");},configurable:true});
   });
   await context.route("**/*",route=>{
    const req=route.request(),url=req.url();results.requests.push({url,method:req.method()});
    if(!url.startsWith(base)||req.method()!=="GET"){results.errors.push("unexpected egress "+url);return route.abort();}
    return route.continue();
   });
   page.on("pageerror",e=>results.errors.push(label+": "+e.message));
   await page.goto(base+"index.html",{waitUntil:"networkidle"});
   await page.selectOption("#language",locale);await page.selectOption("#theme",theme);
   const measured=await page.evaluate(()=>{
    const over=[];
    for(const e of document.querySelectorAll("main *,header *,.demo-band *")){
     const r=e.getBoundingClientRect(),s=getComputedStyle(e);
     if(!e.getClientRects().length||r.width===0||s.visibility!=="visible"||e.tagName==="OPTION")continue;
     if(r.right>innerWidth+.6||r.left<-.6)over.push({tag:e.tagName,cls:e.className,right:r.right,left:r.left});
    }
    return {width:innerWidth,scroll:document.documentElement.scrollWidth,over,
     logo:document.querySelector("header img").naturalWidth,
     theme:document.documentElement.dataset.theme,deltas:document.querySelectorAll("td.delta").length,
     storage:window.__storageAttempts,background:getComputedStyle(document.body).backgroundColor};
   });
   results.layouts.push({label,...measured});check(label+" bounded",measured.scroll<=width&&measured.over.length===0);
   check(label+" visual assets and exact six changed cells",measured.logo>0&&measured.deltas===6);
   check(label+" reset boundary visible",await page.locator("#reset-note").isVisible());
   if((width===390&&locale==="nl")||(width===1280&&locale==="en"&&theme==="light")){
    const dest=path.join(output,(remote?"published-":"local-")+label+".png");
    await page.screenshot({path:dest,fullPage:true});results.screenshots.push(dest);
   }
   await page.locator('[data-action="member_accept"]').click();
   check(label+" separate trainer action",await page.locator('[data-action="apply"]').count()===0);
   await page.locator('input[value="trainer"]').check();
   await page.locator('[data-action="trainer_approve"]').click();
   check(label+" both approve do not apply",(await page.locator("#status").innerText()).includes("3"));
   await page.locator('[data-action="apply"]').click();
   check(label+" apply v4",(await page.locator("#status").innerText()).includes("4"));
   await page.locator('[data-action="restore"]').first().click();
   check(label+" restore does not reuse approval",await page.locator('[data-action="apply"]').count()===0);
   await page.locator('input[value="member"]').check();await page.locator('[data-action="member_accept"]').click();
   await page.locator('input[value="trainer"]').check();await page.locator('[data-action="trainer_approve"]').click();
   await page.locator('[data-action="apply"]').click();
   check(label+" restore v5",(await page.locator("#status").innerText()).includes("5"));
   check(label+" historical v3/v4 preserved",await page.locator("#history .history-item").count()===2);
   check(label+" audit complete",await page.locator(".audit-entry").count()===8);
   await page.selectOption("#language",locale==="nl"?"en":"nl");check(label+" language preserves state",(await page.locator("#status").innerText()).includes("5"));
   await page.reload({waitUntil:"networkidle"});
   check(label+" refresh v3 and no history",(await page.locator("#status").innerText()).includes("3")&&await page.locator("#history .history-item").count()===0);
   const attempts=await page.evaluate(()=>window.__storageAttempts);results.storage_attempts.push(...attempts);check(label+" no browser storage",attempts.length===0);
   await context.close();
  }
  const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage();
  page.on("pageerror",e=>results.errors.push(e.message));
  await page.goto(base+"index.html");
  for(const scenario of ["step_off_grid","ambiguous_rules","no_trainer","missing_set","no_analysis_consent","book_expired","current","self_reported","expired","missing"]){
   await page.selectOption("#scenario",scenario);
   check(scenario+" no apply",await page.locator('[data-action="apply"]').count()===0);
   check(scenario+" clear warning",(await page.locator("#warning").innerText()).length>0);
   if(scenario==="step_off_grid"){
    check("W2 numeric step",(await page.locator("#w2").innerText()).includes("2,5 kg"));
    const dest=path.join(output,(remote?"published-":"local-")+"W2-mobile.png");await page.screenshot({path:dest,fullPage:true});results.screenshots.push(dest);
   }
  }
  for(const action of ["member_reject","trainer_reject","trainer_block"]){
   await page.selectOption("#scenario","normal");await page.locator('input[value="member"]').check();
   if(action!=="member_reject"){await page.locator('[data-action="member_accept"]').click();await page.locator('input[value="trainer"]').check();}
   await page.locator('[data-action="'+action+'"]').click();
   check(action+" terminal UI",await page.locator("#actions button").count()===0);
   check(action+" notification reason",(await page.locator("#inbox").innerText()).includes(action==="trainer_block"?"geblokkeerd":"ingestemd"));
  }
  await page.selectOption("#scenario","normal");await page.locator('input[value="member"]').check();
  await page.locator('[data-action="member_accept"]').click();await page.locator('input[value="trainer"]').check();
  await page.locator('[data-action="trainer_approve"]').click();
  await page.selectOption("#source-event","consent_revoked");await page.locator("#inject").click();
  check("withdrawal prevents UI apply",await page.locator('[data-action="apply"]').count()===0);
  await page.locator("#reset").click();check("explicit reset",await page.locator(".audit-entry").count()===1);
  await page.locator("#language").focus();check("keyboard focus",await page.locator("#language").evaluate(e=>e===document.activeElement));
  await context.close();check("no browser errors",results.errors.length===0);
 }finally{
  if(browser)await browser.close();
  if(server)await new Promise(resolve=>server.close(resolve));
  fs.writeFileSync(path.join(output,remote?"published.json":"local.json"),JSON.stringify(results,null,2)+"\n");
 }
 console.log(JSON.stringify({published:remote,checks:results.checks.length,pass:results.checks.filter(x=>x.pass).length,layouts:results.layouts.length,errors:results.errors,storage_attempts:results.storage_attempts.length,screenshots:results.screenshots},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
