const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const {chromium}=require("playwright");
const {root,base,profile,probe,mockSetup,serverFixture}=require("./phase6d-owner-browser-check.cjs");
const before=process.env.FMZ_PLACEMENT_BEFORE==="1",live=process.env.FMZ_PLACEMENT_LIVE==="1";
const checks=[],layouts=[],cache=new Map();
const check=(name,pass)=>{checks.push({name,pass:!!pass});assert(pass,name);};
const id=n=>"50000000-0000-4000-8000-"+String(n).padStart(12,"0");
const result=n=>({id:id(n),user_id:profile.id,analysis_kind:n%3===0?"weekly":n%2===0?"daily":"post_workout",status:"ready",revision:1,
 created_at:new Date(Date.UTC(2026,8,7,12,n)).toISOString(),completed_at:new Date(Date.UTC(2026,8,7,12,n)).toISOString(),
 summary_text:n===1?"Je laatste training in beeld":"Langdurigetrainingsprestatievergelijking".repeat(4),model_tier:"luna",
 result_payload:{mock:true,actions:[],observations:[{text:"Synthetische observatie voor de dashboardtest."}],suggestions:[]}});
async function measure(page,label){
 await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));
 const data=await page.evaluate(()=>{
  const rect=n=>{const r=n.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top+scrollY,bottom:r.bottom+scrollY,width:r.width,height:r.height};};
  const style=n=>{const s=getComputedStyle(n);return Object.fromEntries(["borderRadius","paddingTop","paddingRight","paddingBottom","paddingLeft","borderTopWidth","borderTopColor","borderTopStyle","backgroundColor","boxShadow","fontSize","fontWeight","lineHeight"].map(k=>[k,s[k]]));};
  const home=document.getElementById("client-home"),shell=home.querySelector(".member-ux-today-simplified"),greeting=shell.querySelector(".member-ux-hero"),checkin=shell.querySelector(".member-ux-daily-checkin"),training=shell.querySelector(".member-ux-training-today"),inbox=document.getElementById("fmz-analysis-inbox");
  const cards=[...inbox.querySelectorAll(".fmz-inbox-item")];
  const order=[greeting,checkin,training,inbox].map(rect);
  const descendants=[inbox,...inbox.querySelectorAll("*")].filter(n=>n.getClientRects().length).map(n=>({tag:n.tagName,class:n.className,...rect(n),scroll:n.scrollWidth,client:n.clientWidth}));
  return {viewport:{width:innerWidth,height:innerHeight},html:{scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth},body:{scroll:document.body.scrollWidth,client:document.body.clientWidth},
   shellFirst:shell.firstElementChild===greeting,inShell:inbox.parentElement===shell,afterTraining:training.nextElementSibling===inbox,
   order,cards:cards.map(n=>({rect:rect(n),style:style(n),title:style(n.querySelector("h3")),button:style(n.querySelector("[data-fmz-analysis-open]"))})),
   reference:{rect:rect(checkin),style:style(checkin),title:style(checkin.querySelector("h2")),button:style(checkin.querySelector(".primary-btn"))},
   gaps:{shell:getComputedStyle(shell).gap,cards:getComputedStyle(inbox.querySelector(".fmz-inbox-items")).gap},
   descendants,overwide:descendants.filter(n=>n.left<0||n.right>innerWidth+1||n.scroll>n.client+1)};
 });
 layouts.push({label,...data});
 if(before)return data;
 check(label+" greeting first and analysis after training",data.shellFirst&&data.inShell&&data.afterTraining&&data.order.slice(1).every((r,i)=>r.top>=data.order[i].bottom-1));
 check(label+" viewport and every analysis descendant bounded",data.html.scroll<=data.html.client&&data.body.scroll<=data.body.client&&data.overwide.length===0);
 check(label+" equal card edges",data.cards.every(c=>Math.abs(c.rect.left-data.reference.rect.left)<1&&Math.abs(c.rect.right-data.reference.rect.right)<1));
 const keys=["borderRadius","paddingTop","paddingRight","paddingBottom","paddingLeft","borderTopWidth","borderTopColor","borderTopStyle","backgroundColor","boxShadow"];
 check(label+" same card surface padding radius border shadow",data.cards.every(c=>keys.every(k=>c.style[k]===data.reference.style[k])));
 check(label+" same card title typography",data.cards.every(c=>["fontSize","fontWeight","lineHeight"].every(k=>c.title[k]===data.reference.title[k])));
 check(label+" same primary button style",data.cards.every(c=>["backgroundColor","borderRadius","paddingLeft","paddingRight","fontSize","fontWeight"].every(k=>c.button[k]===data.reference.button[k])));
 check(label+" same stacked spacing",data.gaps.shell===data.gaps.cards);
 return data;
}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
 try{
 for(const [width,height] of (before?[[390,844]]:[[320,700],[360,800],[390,844],[820,1180],[1180,900],[1440,900]])){
  const server=serverFixture(),context=await browser.newContext({viewport:{width,height},hasTouch:width<1000}),errors=[],actualRequests=[];
  server.recovery.analysis_blocked=false;
  await context.addInitScript("const base="+JSON.stringify(base)+";("+mockSetup.toString()+")("+JSON.stringify(profile)+");");
  await context.route("**/*",async route=>{
   const url=new URL(route.request().url());
   if(url.pathname.endsWith("/__test_rpc")){
    const {name,args}=JSON.parse(route.request().postData());const data=server.rpc(name,args);
    if(name==="fmz_phase6d_get_inbox"&&server.delay)await new Promise(resolve=>setTimeout(resolve,300));
    return route.fulfill({json:{data,error:null}});
   }
   if(url.hostname.endsWith(".supabase.co")){actualRequests.push(url.pathname);return route.abort();}
   if(!route.request().url().startsWith(base))return route.fulfill({body:"",contentType:"application/javascript"});
   const file=decodeURIComponent(url.pathname.slice(new URL(base).pathname.length))||"index.html";assert(!file.includes(".."));
   let body;
   if(live){if(!cache.has(file)){const res=await fetch(base+file+"?placement="+Date.now());assert.equal(res.status,200,file);cache.set(file,Buffer.from(await res.arrayBuffer()));}body=cache.get(file);}
   else body=fs.readFileSync(path.join(root,file));
   if(file==="app.bundle.js")body=Buffer.from(body.toString().replace("\ninit();","\n"+probe+"\ninit();"));
   return route.fulfill({body,contentType:file.endsWith(".js")?"application/javascript":file.endsWith(".css")?"text/css":file.endsWith(".html")?"text/html":file.endsWith(".svg")?"image/svg+xml":file.endsWith(".webp")?"image/webp":"application/octet-stream"});
  });
  const page=await context.newPage();page.on("pageerror",e=>errors.push(e.message));page.on("console",m=>{if(m.type()==="error")errors.push(m.text());});
  await page.goto(base);await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());
  await page.waitForSelector(".member-ux-training-today");await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
  await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));
  const anchor=await page.locator(".member-ux-hero").evaluate(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y+scrollY,width:r.width,height:r.height};});
  server.results.push(result(1));server.notes.push({analysis_id:id(1),state:"new"});
  await page.evaluate(()=>window.dispatchEvent(new Event("fmz:ai-state")));
  await page.waitForSelector(".fmz-analysis-toast");
  await page.click("[data-fmz-analysis-later]");await page.waitForSelector(".fmz-analysis-toast",{state:"detached"});
  await measure(page,width+" Later");
  await page.screenshot({path:path.join(root,"supabase/.temp/placement-"+(before?"before":live?"live":"local")+"-"+width+".png"),fullPage:false});
  if(before){await context.close();continue;}
  const afterAnchor=await page.locator(".member-ux-hero").evaluate(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y+scrollY,width:r.width,height:r.height};});
  check(width+" event hydration leaves greeting fixed "+JSON.stringify({anchor,afterAnchor}),JSON.stringify(afterAnchor)===JSON.stringify(anchor));
  check(width+" Later retains one New card",await page.locator("#fmz-analysis-inbox .fmz-inbox-item").count()===1&&await page.locator("#fmz-analysis-inbox .fmz-inbox-state").textContent()==="Nieuw");
  const unreadHeight=await page.locator(".fmz-inbox-item").evaluate(n=>n.getBoundingClientRect().height);
  await page.locator('#fmz-analysis-inbox [data-fmz-analysis-open="'+id(1)+'"]').click();await page.waitForSelector("#fmz-analysis-detail main h2");
  check(width+" exact own detail",server.calls.filter(c=>c.name==="fmz_phase6d_read_analysis").at(-1).args.p_result_id===id(1));
  await page.click("[data-fmz-detail-close]");
  check(width+" opened card retained without New or size jump",await page.locator(".fmz-inbox-item").count()===1&&await page.locator("#fmz-analysis-inbox .fmz-inbox-state").count()===0&&await page.locator(".fmz-inbox-item").evaluate(n=>n.getBoundingClientRect().height)===unreadHeight);
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
  check(width+" refresh retains read card",await page.locator(".fmz-inbox-item").count()===1&&await page.locator("#fmz-analysis-inbox .fmz-inbox-state").count()===0);
  await page.evaluate(()=>__hotfix.logout());await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
  check(width+" new login retains card",await page.locator(".fmz-inbox-item").count()===1);
  await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));
  server.delay=true;
  const stable=await page.locator(".member-ux-hero,.member-ux-daily-checkin,.member-ux-training-today,.fmz-inbox-item").evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return [r.x,r.y,r.width,r.height];}));
  await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());server.delay=false;
  check(width+" delayed hydration does not shift existing layout",JSON.stringify(stable)===JSON.stringify(await page.locator(".member-ux-hero,.member-ux-daily-checkin,.member-ux-training-today,.fmz-inbox-item").evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return [r.x,r.y,r.width,r.height];}))));
  await page.evaluate(()=>__hotfix.dashboard());
  check(width+" direct dashboard rerender retains correctly mounted inbox",await page.locator(".member-ux-training-today + #fmz-analysis-inbox .fmz-inbox-item").count()===1);
  await page.evaluate(()=>__hotfix.view("trackers"));await page.evaluate(()=>__hotfix.view("client-home"));await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
  check(width+" return to Today retains placement",await page.locator(".member-ux-training-today + #fmz-analysis-inbox .fmz-inbox-item").count()===1);
  for(let n=2;n<=5;n++)server.results.push(result(n));
  server.notes.push(...[2,3,4,5].map(n=>({analysis_id:id(n),state:"later"})));
  await page.evaluate(()=>window.dispatchEvent(new Event("fmz:ai-state")));
  await page.waitForFunction(()=>FMZ_ANALYSIS_INBOX.snapshot().inbox.recent.length===3);
  check(width+" newest three and no duplicates",JSON.stringify(await page.locator("#fmz-analysis-inbox [data-fmz-analysis-open]").evaluateAll(nodes=>nodes.map(n=>n.dataset.fmzAnalysisOpen)))===JSON.stringify([id(5),id(4),id(3)]));
  for(const language of ["nl","en","de"]){
   server.settings.language=language;await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(()=>__hotfix.render());
   await measure(page,width+" "+language+" three");
   if(language==="nl"){await page.locator("#fmz-analysis-inbox").evaluate(n=>{n.scrollIntoView({block:"start",behavior:"instant"});window.scrollBy(0,-84);});await page.screenshot({path:path.join(root,"supabase/.temp/placement-cards-"+(live?"live":"local")+"-"+width+".png")});}
  }
  await page.evaluate(()=>document.body.classList.add("light"));await measure(page,width+" light");await page.evaluate(()=>document.body.classList.remove("light"));
  for(const side of ["right","left"]){
   server.settings.avatar.side=side;await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));
   for(const button of await page.locator("#fmz-analysis-inbox button").all()){
    await button.evaluate(n=>n.scrollIntoView({block:"center",behavior:"instant"}));
    const hit=await button.evaluate(node=>{const r=node.getBoundingClientRect(),a=document.getElementById("fmz-avatar"),v=a.getBoundingClientRect(),target=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {clear:a.hidden||r.right<=v.left||r.left>=v.right||r.bottom<=v.top||r.top>=v.bottom,hit:node.contains(target),button:node.textContent||node.title,interceptor:target?.className};});
    check(width+" "+side+" avatar leaves analysis action reachable "+JSON.stringify(hit),hit.clear&&hit.hit);
   }
  }
  await page.locator("[data-fmz-all-analyses]").click();await page.waitForSelector(".fmz-history-row");
  check(width+" full history accessible",await page.locator(".fmz-history-row").count()===5);
  await page.click('#fmz-youri-chat [data-fmz-close]');
  await page.evaluate(value=>{location.hash="analysis="+value;},id(4));await page.waitForSelector("#fmz-analysis-detail main h2");
  check(width+" deep link exact result",server.calls.filter(c=>c.name==="fmz_phase6d_read_analysis").at(-1).args.p_result_id===id(4));
  await page.click("[data-fmz-detail-close]");await page.evaluate(()=>__hotfix.incomplete(true));await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
  check(width+" incomplete onboarding never puts analyses before greeting",await page.locator(".member-ux-hero ~ .member-ux-profile-cta + #fmz-analysis-inbox").count()===1);
  await page.evaluate(()=>__hotfix.incomplete(false));await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());await measure(page,width+" restored onboarding");
  check(width+" no console errors",errors.length===0);check(width+" zero actual member/provider requests",actualRequests.length===0);
  await context.close();
 }
 }finally{await browser.close();}
 const evidence={mode:before?"before":live?"live-assets":"local",overall_pass:!before,pass_count:checks.length,checks,layouts,no_test_css_injected:true,actual_member_requests:0};
 fs.writeFileSync(path.join(root,"supabase/.temp/placement-"+(before?"before":live?"live":"local")+".json"),JSON.stringify(evidence,null,2));
 console.log(JSON.stringify({mode:evidence.mode,pass_count:checks.length,layouts:layouts.length,before:before?layouts[0]:undefined}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
