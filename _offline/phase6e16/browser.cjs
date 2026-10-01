"use strict";
const fs=require("node:fs"),p=require("node:path"),a=require("node:assert/strict"),{chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const {server,allowed}=require("./serve.cjs"),R=require("../../training-rules-demo/review.js"),out=process.argv[2],remote=process.argv.includes("--published");
const result={remote,checks:[],layouts:[],errors:[],requests:[],screenshots:[]},check=(name,pass)=>{result.checks.push({name,pass:!!pass});a(pass,name);};
(async()=>{let s,b;try{
 let base="https://yourizorge.github.io/fitmetzorge-staging";if(!remote){s=server();await new Promise(r=>s.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+s.address().port;}
 b=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
 async function open(width,height=900){
  const ctx=await b.newContext({viewport:{width,height},serviceWorkers:"block"});
  await ctx.addInitScript(()=>{window.__writes=[];for(const k of ["localStorage","sessionStorage","indexedDB"])Object.defineProperty(window,k,{get(){window.__writes.push(k);throw Error("storage_blocked");}});Object.defineProperty(document,"cookie",{get(){return "";},set(){window.__writes.push("cookie");}});});
  await ctx.route("**/*",r=>{const q=r.request(),u=new URL(q.url()),prefix=remote?"/fitmetzorge-staging":"",ok=q.method()==="GET"&&u.origin===new URL(base).origin&&allowed.includes(u.pathname.slice(prefix.length));result.requests.push({path:u.pathname,allowed:ok});if(!ok){result.errors.push("egress");return r.abort();}return r.continue();});
  const page=await ctx.newPage();page.on("pageerror",e=>result.errors.push(e.message));await page.goto(base+"/training-rules-demo/index.html",{waitUntil:"networkidle"});return {page,ctx};
 }
 async function layout(page,key){
  const items=await page.evaluate(()=>[...document.querySelectorAll("main *,header *")].filter(e=>{const r=e.getBoundingClientRect();return e.tagName!=="OPTION"&&r.width&&r.height&&(r.left<-.5||r.right>innerWidth+.5);}).map(e=>e.tagName+"."+e.className));
  result.layouts.push({key,overflow:items});check(key+" no overflow",items.length===0);
  const duplicates=await page.locator("[id]").evaluateAll(es=>es.map(e=>e.id).filter((id,i,ids)=>ids.indexOf(id)!==i));check(key+" unique IDs",duplicates.length===0);
 }
 for(const width of [320,390,768,1280])for(const lang of ["nl","en","de"])for(const theme of ["light","dark"]){
  const {page,ctx}=await open(width),key=width+"-"+lang+"-"+theme;
  await page.selectOption("#language",lang);await page.selectOption("#theme",theme);
  check(key+" sixteen buttons",await page.locator("#scenario-buttons button").count()===16);check(key+" brand renders",await page.locator("header img").evaluate(e=>e.naturalWidth>0));
  check(key+" targets",await page.locator("#scenario-buttons button").evaluateAll(es=>es.every(e=>e.getBoundingClientRect().height>=52)));
  for(const c of R.scenarios){
   await page.click("#test-"+c.id);check(key+" "+c.id+" PASS",await page.locator("#verdict").getAttribute("data-result")==="pass");
   check(key+" "+c.id+" title",await page.locator("#scenario-title").innerText()===c.title[["nl","en","de"].indexOf(lang)]);
   await layout(page,key+" "+c.id);
  }
  await page.click("#test-valid_edit");check(key+" sets changed",await page.locator("#sets-0-0").inputValue()==="3");check(key+" rest changed",await page.locator("#rest-0-0").inputValue()==="75");
  check(key+" prior values retained",await page.locator("#before-sets-0-0").inputValue()==="2");
  await page.click("#test-units");check(key+" original20kg",(await page.locator("#proposal .history-value").first().innerText()).includes("20 kg")&&(await page.locator("#proposal .history-value").first().innerText()).includes("RIR 0"));
  await page.click("#test-rir");check(key+" only RIR",await page.locator("#rir-0-0").getAttribute("type")==="number"&&await page.locator("#rpe-0-0").innerText()==="-");
  await page.click("#test-safety");check(key+" blocked",await page.locator("#confirm,#activate").count()===0&&await page.locator("#save").isDisabled());
  if(lang==="nl"&&(width===390||width===1280)){
   await page.click("#test-valid_edit");await page.locator("#review-result").scrollIntoViewIfNeeded();const x=p.join(out,(remote?"published":"local")+"-"+key+".png");await page.screenshot({path:x});result.screenshots.push(x);
   await page.locator("#proposal").scrollIntoViewIfNeeded();const y=p.join(out,(remote?"published":"local")+"-plan-"+key+".png");await page.screenshot({path:y});result.screenshots.push(y);
  }
  check(key+" storage untouched",(await page.evaluate(()=>window.__writes)).length===0);await ctx.close();
 }
 const {page,ctx}=await open(390,480);
 await page.locator("#start").focus();await page.keyboard.press("Enter");check("guided first",await page.locator("#previous").isDisabled());
 for(let i=1;i<16;i++){await page.click("#next");check("guided next "+i,(await page.locator("#step").innerText())==="Stap "+(i+1)+" van 16"&&await page.locator("#verdict").getAttribute("data-result")==="pass");}
 check("guided last",await page.locator("#next").isDisabled());await page.click("#previous");check("guided back",(await page.locator("#step").innerText())==="Stap 15 van 16");
 await page.click("#test-beginner");await page.evaluate(()=>{document.querySelector("#sets-0-0").value="99";renderReview();});check("visible mismatch red",await page.locator("#verdict").getAttribute("data-result")==="fail");
 await page.click("#test-beginner");await page.evaluate(()=>{review.events.pop();renderReview();});check("missing proof red",await page.locator("#verdict").getAttribute("data-result")==="fail");
 await page.click("#test-beginner");await page.fill("#sets-0-0","3");check("manual edit clears PASS",await page.locator("#verdict").getAttribute("data-result")===null);
 await page.fill("#reps-0-0","11");await page.fill("#rest-0-0","75");await page.selectOption("#ex-0-0","press");await page.click("#edit-ex-0-0");
 check("real editor changed",await page.locator("#sets-0-0").inputValue()==="3"&&await page.locator("#reps-0-0").inputValue()==="11");
 await page.selectOption("#proposal .session-day >> nth=0","fri");await page.click("#edit-day-0");check("day moved",await page.locator("#proposal .session-day").first().inputValue()==="fri");
 await page.fill("#sets-0-0","99");await page.click("#edit-ex-0-0");check("invalid no clamp/no partial",await page.locator("#sets-0-0").inputValue()==="3"&&(await page.locator("#feedback").innerText()).includes("Geweigerd"));
 await page.locator("#confirm").focus();await page.keyboard.press("Enter");check("separate activation",await page.locator("#activate").count()===1&&(await page.locator("#versions").innerText())==="-");
 await page.click("#activate");await page.click("#duplicate");check("one version",await page.locator("#versions").innerText()==="1");
 await page.click("#build");await page.fill("#reps-0-0","12");await page.click("#edit-ex-0-0");await page.click("#confirm");await page.click("#activate");await page.click("#restore");
 check("restore needs approval",await page.locator("#confirm").count()===1&&await page.locator("#activate").count()===0);
 await page.click("#confirm");await page.click("#activate");check("restore3",await page.locator("#versions").innerText()==="1 / 2 / 3");
 await page.click("#source");check("source clears draft",await page.locator("#proposal .exercise").count()===0&&await page.locator("#activate").count()===0);
 await page.click("#reset");await page.locator("#intake-details summary").click();await page.selectOption("#f-goal","muscle");await page.selectOption("#f-experience","experienced");await page.selectOption("#f-rir","true");await page.selectOption("#f-rpe","true");await page.click("#save");await page.click("#build");check("new intake reassessed",await page.locator("#sets-0-0").inputValue()==="4"&&await page.locator("#rpe-0-0").inputValue()==="7");
 await page.fill("#rir-0-0","0");await page.click("#edit-ex-0-0");check("RIR0 stays0",await page.locator("#rir-0-0").inputValue()==="0");
 await layout(page,"keyboard-space");await page.click("#revoke");await page.click("#build");check("revoked blocks",await page.locator("#confirm,#activate").count()===0&&await page.locator("#save").isDisabled());
 await page.reload({waitUntil:"networkidle"});check("refresh reset",await page.locator("#audit li").count()===0&&await page.locator("#verdict").getAttribute("data-result")===null);await ctx.close();
 check("no errors/extra egress",result.errors.length===0);result.status="BROWSER_PASS";
}catch(e){result.status="BROWSER_FAIL";result.failure=e.message;process.exitCode=1;}finally{if(b)await b.close();if(s)await new Promise(r=>s.close(r));fs.writeFileSync(p.join(out,(remote?"published":"local")+"-browser-"+Date.now()+".json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify({status:result.status,checks:result.checks.length,layouts:result.layouts.length,errors:result.errors,failure:result.failure,screenshots:result.screenshots}));}})();
