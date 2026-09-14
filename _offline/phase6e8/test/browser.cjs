"use strict";
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),assert=require("node:assert/strict"),cp=require("node:child_process");
const {chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const root=path.resolve(__dirname,"../../.."),output=path.join(root,"supabase/.temp/phase6e8-browser"),remote=process.argv.includes("--published"),smoke=process.argv.includes("--smoke");
const results={published:remote,checks:[],layouts:[],screenshots:[],requests:[],errors:[],storage:[]},check=(name,value)=>{results.checks.push({name,pass:!!value});assert(value,name);};
const tracked=cp.execFileSync("git",["ls-files"],{cwd:root,encoding:"utf8"}).split(/\r?\n/);
const publicFiles=new Set([...tracked.filter(f=>/^assets\/|^training-review-demo\//.test(f)||(!f.includes("/")&&/\.(html|css|js|png|svg|ico)$/.test(f))),...fs.readdirSync(path.join(root,"coach-review-demo")).map(f=>"coach-review-demo/"+f)]);
const type=f=>f.endsWith(".html")?"text/html":f.endsWith(".css")?"text/css":f.endsWith(".png")?"image/png":f.endsWith(".svg")?"image/svg+xml":"application/javascript";
(async()=>{
 fs.mkdirSync(output,{recursive:true});let server,browser;
 try{
  let base="https://yourizorge.github.io/fitmetzorge-staging/";
  if(!remote){server=http.createServer((req,res)=>{
   const file=decodeURIComponent(new URL(req.url,"http://localhost").pathname).slice(1)||"index.html";
   if(!publicFiles.has(file)){res.writeHead(404);res.end();return;}
   res.setHeader("Content-Type",type(file));res.end(fs.readFileSync(path.join(root,file)));
  });await new Promise(r=>server.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+server.address().port+"/";}
  browser=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
  for(const width of (smoke?[390]:[320,390,768,1280]))for(const lang of(smoke?["nl"]:["nl","en","de"]))for(const theme of(smoke?["light"]:["light","dark"])){
   const label=width+"-"+lang+"-"+theme,context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();
   await context.addInitScript(()=>{
    window.__storage=[];
    for(const k of ["localStorage","sessionStorage","indexedDB"])Object.defineProperty(window,k,{get(){window.__storage.push(k);throw Error("Storage forbidden");},configurable:true});
    Object.defineProperty(document,"cookie",{get(){window.__storage.push("cookie-read");return "";},set(){window.__storage.push("cookie-write");},configurable:true});
   });
   await context.route("**/*",r=>{
    const req=r.request(),url=req.url(),file=url.startsWith(base)?new URL(url).pathname.slice(new URL(base).pathname.length):"";
    results.requests.push({url,method:req.method()});
    if(req.method()!=="GET"||!url.startsWith(base)||!publicFiles.has(file)||/^(app|config)\.js$|theme-authority\.js|supabase/.test(file)){
     results.errors.push("Unexpected request: "+url);return r.abort();
    }return r.continue();
   });
   page.on("pageerror",e=>results.errors.push(label+": "+e.message));
   await page.goto(base+"index.html?fmzDemo=6e8&lang="+lang+"&theme="+theme);
   const iframe=page.locator("#synthetic-panel iframe");await iframe.waitFor();
   check(label+" sandbox exactly allow-scripts",await iframe.getAttribute("sandbox")==="allow-scripts");
   const f=await (await iframe.elementHandle()).contentFrame();
   await f.locator('[data-action="build"]').waitFor();
   check(label+" actual index has no login or app shell",await page.locator("#loginScreen,.app-shell").count()===0);
   check(label+" language",await f.locator("html").getAttribute("lang")===lang);
   check(label+" theme",await f.locator("html").getAttribute("data-theme")===theme);
   check(label+" parent DOM forbidden",await f.evaluate(()=>{try{return !!parent.document&&false;}catch{return true;}}));
   check(label+" sandbox origin not shared",await f.evaluate(()=>{try{parent.localStorage;return false;}catch{return true;}}));
   async function layout(stage){
    const dims=await f.evaluate(()=>{
     const visible=[...document.querySelectorAll("button,select,input,h1,h2")].filter(e=>e.getClientRects().length);
     return {width:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:visible.filter(e=>{const r=e.getBoundingClientRect();return r.left< -1||r.right>innerWidth+1;}).map(e=>e.outerHTML.slice(0,130)),small:visible.filter(e=>e.tagName==="BUTTON"&&e.getBoundingClientRect().height<43).length};
    });results.layouts.push({label,stage,...dims});check(label+" "+stage+" no horizontal overflow",dims.scroll<=dims.width+1&&dims.body<=dims.width+1&&dims.overflow.length===0);check(label+" "+stage+" touch targets",dims.small===0);
   }
   await layout("intake");
   await f.locator('[data-action="build"]').click();check(label+" B proposal",await f.locator("#status").textContent()===(await f.evaluate(()=>FMZ8Copy[document.documentElement.lang].member_pending)));
   check(label+" B no approval action",await f.locator('#route-content [data-value*="trainer_"]').count()===0);
   check(label+" B no trainer approval step",!(await f.locator("#route-content .timeline").innerText()).match(/trainer|Trainer/));
   await layout("B training");
   for(const tab of ["nutrition","recovery"]){await f.locator('[data-tab="'+tab+'"]').click();await layout("B "+tab);}
   await f.locator('[data-action="confirm"]').click();check(label+" B confirmation does not activate",await f.evaluate(()=>FMZ8Diagnostics.view().independent.revision===0));
   await f.locator('[data-action="apply"]').click();check(label+" B activation",await f.evaluate(()=>FMZ8Diagnostics.view().independent.revision===1));
   await f.locator('[data-action="reopen"]').click();
   await f.locator("#sleep-edit").selectOption("9");await f.locator('[data-action="sleep"]').click();await f.locator('[data-action="confirm"]').click();await f.locator('[data-action="apply"]').click();
   check(label+" B v2",await f.evaluate(()=>FMZ8Diagnostics.view().independent.revision===2));
   await f.locator('[data-action="restore"]').first().click();check(label+" restore still proposal",await f.evaluate(()=>FMZ8Diagnostics.view().independent.revision===2));
   await f.locator('[data-action="confirm"]').click();await f.locator('[data-action="apply"]').click();check(label+" B restore v3",await f.evaluate(()=>FMZ8Diagnostics.view().independent.revision===3));
   if([390,1280].includes(width)&&lang==="nl"){
    await f.locator('[data-tab="training"]').click();await f.locator("h1").scrollIntoViewIfNeeded();
    const dest=path.join(output,(remote?"published":"local")+"-B-"+label+".png");await page.screenshot({path:dest});results.screenshots.push(dest);
   }
   if(width===390&&lang==="nl"&&theme==="light"){
    await f.locator('[data-action="reopen"]').click();
    await f.locator('[data-replace="0:0"]').selectOption("bandrow");await f.locator('[data-action="replace"]').first().click();
    check("B replace UI",await f.evaluate(()=>FMZ8Diagnostics.view().independent.draft.plan.training.sessions[0].exercises[0].id==="bandrow"));
    await f.locator('[data-add="0"]').selectOption("raise");await f.locator('[data-action="add"]').first().click();
    check("B add UI",await f.evaluate(()=>FMZ8Diagnostics.view().independent.draft.plan.training.sessions[0].exercises.length===4));
    await f.locator('[data-action="edit"][data-value*="\\"move\\""]').nth(3).click();
    check("B move UI",await f.evaluate(()=>FMZ8Diagnostics.view().independent.draft.plan.training.sessions[0].exercises[2].id==="raise"));
    await f.locator('[data-action="edit"][data-value*="\\"remove\\""]').first().click();
    check("B remove UI",await f.evaluate(()=>FMZ8Diagnostics.view().independent.draft.plan.training.sessions[0].exercises.length===3));
    await f.locator('[data-tab="nutrition"]').click();await f.locator('[data-meal="0"]').selectOption("ricebeans");await f.locator('[data-action="meal"]').first().click();
    await f.locator('[data-food="0:0"]').selectOption("lentils");await f.locator('[data-action="food"]').first().click();
    check("B meal and food replacement only in proposal",await f.evaluate(()=>{const s=FMZ8Diagnostics.view().independent;return s.revision===3&&s.draft.plan.nutrition.meals[0].items[0].food==="lentils";}));
    await f.locator('[data-action="confirm"]').click();await f.locator('[data-tab="recovery"]').click();await f.locator('[data-action="edit"][data-value*="light_week"]').click();
    check("B edit invalidates confirmed state",await f.locator('[data-action="apply"]').isDisabled());
    await f.locator('[data-action="reject"]').click();check("B rejected",await f.evaluate(()=>FMZ8Diagnostics.view().independent.status==="rejected"));
    await f.locator('[data-action="reopen"]').click();await f.locator('[data-action="confirm"]').click();await f.locator('[data-action="apply"]').click();
    check("B compound revision atomic",await f.evaluate(()=>{const s=FMZ8Diagnostics.view().independent;return s.revision===4&&s.active.plan.nutrition.meals[0].items[0].food==="lentils"&&s.active.plan.recovery.lightWeek.active;}));
    await f.locator("#safety-select").selectOption("current");await f.locator('[data-action="safety"]').click();
    check("health concept warning visible",await f.locator('[data-warning="warning_health"]').count()===1);
    await f.locator("#safety-select").selectOption("technical");await f.locator('[data-action="safety"]').click();
    check("technical error keeps health warning",await f.locator('[data-warning]').count()===2);
    await f.locator('[data-action="clarify"]').click();
    check("clarification keeps other health context",await f.evaluate(()=>FMZ8Diagnostics.view().independent.contextFixtures.join(",")==="current"));
    await f.locator('[data-action="reopen"]').click();check("current health context blocks new activation",await f.evaluate(()=>FMZ8Diagnostics.view().independent.revision===4));
    check("synthetic photo diagram renders",await f.locator(".photo-pair").evaluate(e=>e.complete&&e.naturalWidth===640));
   }
   await f.locator('[data-route="A"]').click();await layout("A proposal");
   const action=name=>f.locator('[data-action="a"][data-value*="\\"'+name+'\\""]');
   check(label+" A apply initially disabled",await action("apply").isDisabled());
   await action("member_accept").click();check(label+" A still requires trainer",await action("apply").isDisabled());
   await action("trainer_approve").click();await action("apply").click();
   check(label+" A v4",await f.evaluate(()=>FMZ8Diagnostics.view().human.active.revision===4));
   await action("restore").first().click();check(label+" A restore requires approvals",await action("apply").isDisabled());
   await action("member_accept").click();await action("trainer_approve").click();await action("apply").click();
   check(label+" A v5",await f.evaluate(()=>FMZ8Diagnostics.view().human.active.revision===5));
   if([390,1280].includes(width)&&lang==="nl"){
    await f.locator("h1").scrollIntoViewIfNeeded();const dest=path.join(output,(remote?"published":"local")+"-A-"+label+".png");await page.screenshot({path:dest});results.screenshots.push(dest);
   }
   await f.locator("#scenario").selectOption("no_trainer");check(label+" no trainer no fallback",await f.evaluate(()=>FMZ8Diagnostics.view().route==="A"&&FMZ8Diagnostics.view().human.proposal.status==="blocked"));
   await f.locator("#scenario").selectOption("step_off_grid");check(label+" W2 concrete step",await f.locator("#route-content").innerText().then(x=>x.includes("2.5")&&x.includes("W2")));
   check(label+" no uploads",await f.locator('input[type="file"]').count()===0);
   for(const frame of page.frames()){const attempts=await frame.evaluate(()=>window.__storage||[]);results.storage.push({label,attempts});check(label+" zero app storage access",attempts.length===0);}
   await page.reload();await page.locator("iframe").waitFor();const fresh=await(await page.locator("iframe").elementHandle()).contentFrame();await fresh.locator('[data-action="build"]').waitFor();
   check(label+" refresh reset",await fresh.evaluate(()=>FMZ8Diagnostics.view().independent.revision===0&&FMZ8Diagnostics.view().human.active.revision===3));
   await page.locator("#synthetic-panel>button").click();check(label+" close destroys frame",await page.locator("iframe").count()===0);await page.locator("#synthetic-panel>button").click();check(label+" reopen single frame",await page.locator("iframe").count()===1);
   await context.close();
  }
  // Normal bootstrap is verified with inert scripts, never with real auth or APIs.
  const normal=await browser.newContext({serviceWorkers:"block"}),page=await normal.newPage(),order=[];
  await normal.route("**/*",r=>{
   const u=r.request().url();
   if(/theme-authority\.js|supabase-js|\/config\.js$|zxing-browser|\/app\.js\?/.test(u)){order.push(u);return r.fulfill({contentType:"application/javascript",body:"(window.__bootstrapOrder ||= []).push("+JSON.stringify(u)+");"});}
   if(!u.startsWith(base))return r.abort();return r.continue();
  });
  await page.goto(base+"index.html");await page.waitForLoadState("load");
  const executed=await page.evaluate(()=>window.__bootstrapOrder||[]);results.bootstrapOrder=executed;
  check("normal script sequence preserved",executed.length===5&&executed[0].includes("theme-authority")&&executed[1].includes("supabase-js")&&executed[2].endsWith("/config.js")&&executed[3].includes("zxing-browser")&&executed[4].includes("/app.js?"));
  check("normal app DOM preserved",await page.locator("#loginScreen").count()===1&&await page.locator("iframe").count()===0);
  for(const q of ["fmzDemo=invalid","fmzDemo=6e8&lang=xx","fmzDemo=6e8&theme=unknown","fmzDemo=6e8&subject=syn-member","fmzDemo=6e8&lang=nl&lang=en"]){const n=order.length;await page.goto(base+"index.html?"+q);check("invalid query fails closed "+q,order.length===n&&await page.locator("iframe").count()===0&&await page.locator("#loginScreen").count()===0);}
  await normal.close();check("no browser errors or unauthorized requests",results.errors.length===0);
 }finally{
  if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));
  fs.writeFileSync(path.join(output,(remote?"published":"local")+(smoke?"-smoke":"")+".json"),JSON.stringify(results,null,2)+"\n");
 }
 console.log(JSON.stringify({checks:results.checks.length,passed:results.checks.filter(x=>x.pass).length,layouts:results.layouts.length,screenshots:results.screenshots,errors:results.errors}));
})().catch(e=>{console.error(e);process.exitCode=1;});
