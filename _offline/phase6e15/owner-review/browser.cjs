"use strict";
const fs=require("node:fs"),p=require("node:path"),a=require("node:assert/strict");
const {chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const {server,allowed}=require("../serve.cjs"),R=require("../../../independent-intake-demo/review.js");
const out=process.argv[2],remote=process.argv.includes("--published"),result={remote,checks:[],layouts:[],errors:[],requests:[],screenshots:[]};
const check=(name,pass)=>{result.checks.push({name,pass:!!pass});a(pass,name);};
(async()=>{let s,b;try{
 let base="https://yourizorge.github.io/fitmetzorge-staging";
 if(!remote){s=server();await new Promise(r=>s.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+s.address().port;}
 b=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
 async function open(width,height=900){
  const ctx=await b.newContext({viewport:{width,height},serviceWorkers:"block"});
  await ctx.addInitScript(()=>{window.__writes=[];for(const k of ["localStorage","sessionStorage","indexedDB"])Object.defineProperty(window,k,{get(){window.__writes.push(k);throw Error("storage_blocked");}});Object.defineProperty(document,"cookie",{get(){return "";},set(){window.__writes.push("cookie");}});});
  await ctx.route("**/*",r=>{const q=r.request(),u=new URL(q.url()),prefix=remote?"/fitmetzorge-staging":"",ok=q.method()==="GET"&&u.origin===new URL(base).origin&&allowed.includes(u.pathname.slice(prefix.length));result.requests.push({path:u.pathname,allowed:ok});if(!ok){result.errors.push("egress");return r.abort();}return r.continue();});
  const page=await ctx.newPage();page.on("pageerror",e=>result.errors.push(e.message));await page.goto(base+"/independent-intake-demo/index.html",{waitUntil:"networkidle"});return {page,ctx};
 }
 async function layout(page,key){
  const overflow=await page.evaluate(()=>[...document.querySelectorAll("main *,header *")].filter(e=>{const r=e.getBoundingClientRect();return e.tagName!=="OPTION"&&r.width&&r.height&&(r.left<-.5||r.right>innerWidth+.5);}).map(e=>e.tagName+"."+e.className));
  result.layouts.push({key,overflow});check(key+" no overflow",overflow.length===0);
 }
 for(const width of [320,390,768,1280])for(const locale of ["nl","en","de"])for(const theme of ["light","dark"]){
  const {page,ctx}=await open(width),key=width+"-"+locale+"-"+theme;
  await page.selectOption("#language",locale);await page.selectOption("#theme",theme);
  check(key+" nine buttons",await page.locator("#test-buttons button").count()===9);
  check(key+" no automatic PASS",await page.locator("#review-verdict").getAttribute("data-result")===null);
  check(key+" button touch size",await page.locator("#test-buttons button").evaluateAll(es=>es.every(e=>e.getBoundingClientRect().height>=52)));
  for(const c of R.cases){
   await page.click("#test-"+c.id);
   check(key+" "+c.id+" PASS",await page.locator("#review-verdict").getAttribute("data-result")==="pass");
   check(key+" "+c.id+" active title",(await page.locator("#review-title").innerText())===c.title);
   check(key+" "+c.id+" explanations",await page.locator("#review-facts dd").count()===4);
   check(key+" "+c.id+" selected",await page.locator("#test-"+c.id).getAttribute("aria-pressed")==="true");
   await layout(page,key+" "+c.id);
  }
  await page.click("#test-allergy");
  check(key+" excluded food absent",await page.locator('#proposal [data-review-food="nuts"],#proposal [data-review-food="yogurt"],#proposal [data-review-food="tofu"],#proposal [data-review-exercise="squat"]').count()===0);
  check(key+" exclusions visible",(await page.locator("#review-checks").innerText()).includes("Noten in voedingsvoorstel - 0 keer"));
  await page.click("#test-health");check(key+" health no plan",await page.locator("#proposal .session,#activate,#confirm").count()===0);
  await page.click("#test-consent");check(key+" withdrawal no processing",await page.locator("#save").isDisabled()&&await page.locator("#proposal-warning").isVisible()&&await page.locator("#activate,#confirm").count()===0);
  await page.click("#build");check(key+" revoked build remains blocked",await page.locator("#activate,#confirm").count()===0&&await page.locator("#review-verdict").getAttribute("data-result")===null);
  await page.click("#test-source");check(key+" stale no proposal",await page.locator("#proposal .session,#activate,#confirm").count()===0);
  if(locale==="nl"&&(width===390||width===1280)){
   await page.click("#test-allergy");await page.locator("#review-summary").scrollIntoViewIfNeeded();
   const screenshot=p.join(out,(remote?"published":"local")+"-owner-"+key+".png");
   await page.screenshot({path:screenshot});result.screenshots.push(screenshot);
   if(theme==="light"){await page.evaluate(()=>scrollTo(0,0));const x=p.join(out,(remote?"published":"local")+"-buttons-"+width+".png");await page.screenshot({path:x});result.screenshots.push(x);}
  }
  check(key+" no storage",(await page.evaluate(()=>window.__writes)).length===0);
  await ctx.close();
 }
 const {page,ctx}=await open(390,480);
 await page.locator("#review-start").focus();await page.keyboard.press("Enter");
 check("keyboard starts at first step",await page.locator("#review-prev").isDisabled()&&(await page.locator("#review-step").innerText())==="Stap 1 van 9");
 for(let i=1;i<9;i++){await page.click("#review-next");check("guided step "+(i+1),(await page.locator("#review-step").innerText())==="Stap "+(i+1)+" van 9"&&await page.locator("#review-verdict").getAttribute("data-result")==="pass");}
 check("last step stops",await page.locator("#review-next").isDisabled());
 for(let i=7;i>=0;i--){await page.click("#review-prev");check("guided back "+(i+1),(await page.locator("#review-step").innerText())==="Stap "+(i+1)+" van 9"&&await page.locator("#review-verdict").getAttribute("data-result")==="pass");}
 await page.click("#test-allergy");
 await page.evaluate(()=>{document.querySelector("#proposal [data-review-food]").textContent="Noten | 20 g";renderOwnerTest();});
 check("wrong visible product RED",await page.locator("#review-verdict").getAttribute("data-result")==="fail"&&(await page.locator("#review-verdict").innerText()).includes("AFWIJKING"));
 await page.click("#test-valid");await page.evaluate(()=>{ownerTest.ledger.pop();renderOwnerTest();});
 check("missing evidence RED",await page.locator("#review-verdict").getAttribute("data-result")==="fail");
 await page.click("#test-valid");await page.selectOption("#f-goal","muscle");
 check("unsaved intake clears old PASS",await page.locator("#review-verdict").getAttribute("data-result")===null);
 await page.click("#test-valid");await page.fill("#reps-0-0","9");
 check("unsaved plan edit clears old PASS",await page.locator("#review-verdict").getAttribute("data-result")===null);
 await page.click("#test-valid");await page.click("#confirm");
 check("manual action clears old PASS",await page.locator("#review-verdict").getAttribute("data-result")===null&&await page.locator("#activate").count()===1);
 await layout(page,"390 keyboard space");
 await page.reload({waitUntil:"networkidle"});check("refresh clears test and plan",await page.locator("#review-verdict").getAttribute("data-result")===null&&await page.locator("#audit li").count()===0);
 await ctx.close();check("no errors or unexpected network",result.errors.length===0);result.status="OWNER_BROWSER_PASS";
}catch(e){result.status="OWNER_BROWSER_FAIL";result.failure=e.message;process.exitCode=1;}
finally{if(b)await b.close();if(s)await new Promise(r=>s.close(r));fs.writeFileSync(p.join(out,(remote?"published":"local")+"-owner-browser-"+Date.now()+".json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify({status:result.status,checks:result.checks.length,layouts:result.layouts.length,errors:result.errors,failure:result.failure,screenshots:result.screenshots}));}
})();
