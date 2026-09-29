"use strict";
const fs=require("node:fs"),p=require("node:path"),a=require("node:assert/strict"),{chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const {server,allowed}=require("../serve.cjs"),{scenarios}=require("../fixtures.cjs"),folder=process.argv[2],remote=process.argv.includes("--published");
const result={remote,checks:[],layouts:[],screenshots:[],errors:[],storage:[],requests:[]};
const check=(name,pass)=>{result.checks.push({name,pass:!!pass});a(pass,name);};
(async()=>{let s,b;
try{
 let base="https://yourizorge.github.io/fitmetzorge-staging";
 if(!remote){s=server();await new Promise(r=>s.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+s.address().port;}
 b=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
 async function open(width,height=900){
  const ctx=await b.newContext({viewport:{width,height},serviceWorkers:"block"});
  await ctx.addInitScript(()=>{window.__writes=[];for(const key of ["localStorage","sessionStorage","indexedDB"])Object.defineProperty(window,key,{get(){window.__writes.push(key);throw Error("storage_blocked");}});Object.defineProperty(document,"cookie",{get(){return "";},set(){window.__writes.push("cookie");}});});
  await ctx.route("**/*",r=>{const q=r.request(),u=new URL(q.url()),prefix=remote?"/fitmetzorge-staging":"",ok=q.method()==="GET"&&u.origin===new URL(base).origin&&allowed.includes(u.pathname.slice(prefix.length));
   result.requests.push({path:u.pathname,allowed:ok});if(!ok){result.errors.push("egress");return r.abort();}return r.continue();});
  const page=await ctx.newPage();page.on("pageerror",e=>result.errors.push(e.message));
  await page.goto(base+"/bounded-adjustments-demo/index.html",{waitUntil:"networkidle"});return {ctx,page};
 }
 async function overflow(page,label){const list=await page.evaluate(()=>[...document.querySelectorAll("main *,header *")].filter(e=>{const r=e.getBoundingClientRect();return !["OPTION","PRE"].includes(e.tagName)&&r.width&&r.height&&(r.left<-.5||r.right>innerWidth+.5);}).map(e=>e.tagName+"."+e.className));result.layouts.push({label,overflow:list});check(label+" no overflow",list.length===0);}
 for(const width of [320,390,768,1280])for(const locale of ["nl","en","de"])for(const theme of ["light","dark"]){
  const {ctx,page}=await open(width),label=width+"-"+locale+"-"+theme;
  await page.selectOption("#language",locale);await page.selectOption("#theme",theme);
  check(label+" image",await page.locator("header img").evaluate(e=>e.naturalWidth>0));
  check(label+" proactive option before question",await page.locator("#accept").count()===1);
  check(label+" four facts",await page.locator(".fact").count()===4);
  check(label+" separate RIR RPE",/RIR/.test(await page.locator("#after").innerText())&&/RPE/.test(await page.locator("#after").innerText()));
  await overflow(page,label+" A");
  if(width===390||width===1280&&locale==="nl"&&theme==="light"){const path=p.join(folder,(remote?"published-":"local-")+label+"-A.png");await page.screenshot({path,fullPage:true});result.screenshots.push(path);}
  await page.click("#accept");check(label+" no early apply",await page.locator("#apply").count()===0);
  await page.selectOption("#actor","trainer");await page.click("#approve");check(label+" trainer no apply",await page.locator("#apply").count()===0);
  await page.selectOption("#actor","member");await page.click("#apply");check(label+" v4",/4/.test(await page.locator("#versions").innerText()));
  const versions=await page.locator("#versions").innerText();await page.click("#double");check(label+" duplicate no version",await page.locator("#versions").innerText()===versions);
  await page.click("#restore");await page.click("#accept");await page.selectOption("#actor","trainer");await page.click("#approve");await page.selectOption("#actor","member");await page.click("#apply");check(label+" restore v5",/5/.test(await page.locator("#versions").innerText()));
  await page.selectOption("#scenario","b_schedule");check(label+" B no trainer selector",await page.locator("#actor-label").isHidden());
  await page.click("#accept");await page.click("#apply");check(label+" B v2",/2/.test(await page.locator("#versions").innerText()));await page.click("#restore");await page.click("#accept");await page.click("#apply");check(label+" B restore v3",/3/.test(await page.locator("#versions").innerText()));
  await page.click("#reset");await page.selectOption("#exercise","bandrow");await page.locator("#edit-form button").click();check(label+" B edit",(await page.locator("#after").innerText()).includes({nl:"Elastiek roeien",en:"Band row",de:"Bandrudern"}[locale])&&await page.locator("#result").innerText()==="");
  await overflow(page,label+" B");
  if(width===390&&locale==="nl"){const path=p.join(folder,(remote?"published-":"local-")+label+"-B.png");await page.screenshot({path,fullPage:true});result.screenshots.push(path);}
  check(label+" zero storage",(await page.evaluate(()=>window.__writes)).length===0);
  await page.reload({waitUntil:"networkidle"});check(label+" refresh reset",await page.locator("#audit li").count()===0&&await page.locator("#accept").count()===1);
  await ctx.close();
 }
 const {ctx,page}=await open(390,480);
 for(const locale of ["nl","en","de"]){await page.selectOption("#language",locale);for(const name of scenarios){await page.selectOption("#scenario",name);check(locale+" "+name+" apply gate",await page.locator("#accept").count()===(["a_progression","a_lb","b_schedule"].includes(name)?1:0));}}
 await page.selectOption("#language","nl");await page.selectOption("#scenario","a_progression");await page.click("#accept");await page.click("#correct");check("correction removes approval action",await page.locator("#approve").count()===0);await page.click("#reassess");check("correction new acceptance",await page.locator("#accept").count()===1);
 await page.click("#accept");await page.selectOption("#actor","trainer");await page.click("#block");check("trainer blocked",await page.locator("#apply").count()===0);
 await page.click("#reset");await page.click("#reject");check("member reject",await page.locator("#accept").count()===0);
 await page.click("#reset");await page.click("#stale");check("stale blocked",await page.locator("#accept").count()===0);
 await page.selectOption("#scenario","b_schedule");await page.locator("#days input[value=mon]").uncheck();await page.locator("#days input[value=tue]").check();await page.locator("#edit-form button").click();check("day edit succeeds",await page.locator("#result").innerText()==="");await overflow(page,"keyboard-space");
 await page.selectOption("#scenario","nutrition_partial");await page.locator("#check").focus();await page.keyboard.press("Enter");check("keyboard confirmation no apply",/ontbrekende waarden blijven/.test(await page.locator("#message").innerText())&&await page.locator("#apply").count()===0);
 await page.keyboard.press("Tab");check("keyboard focus exists",await page.evaluate(()=>document.activeElement.tagName!=="BODY"));
 await ctx.close();check("no errors or egress",result.errors.length===0);result.status="BROWSER_PASS";
}catch(e){result.status="BROWSER_FAIL";result.failure=e.message;process.exitCode=1;}
finally{if(b)await b.close();if(s)await new Promise(r=>s.close(r));fs.writeFileSync(p.join(folder,(remote?"published":"local")+"-browser-"+Date.now()+".json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify({status:result.status,checks:result.checks.length,layouts:result.layouts.length,errors:result.errors,failure:result.failure,screenshots:result.screenshots}));}
})();
