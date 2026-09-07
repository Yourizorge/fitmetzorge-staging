const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const {chromium}=require("playwright");
const {root,base,profile,probe,mockSetup,serverFixture}=require("./phase6d-owner-browser-check.cjs");
const before=process.env.FMZ_MOBILE_BEFORE==="1",live=process.env.FMZ_MOBILE_LIVE==="1";
const checks=[],layouts=[],resourceCache=new Map();
function check(name,pass){checks.push({name,pass:!!pass});assert(pass,name);}
const id=n=>"40000000-0000-4000-8000-"+String(n).padStart(12,"0");
function analysis(n,kind="post_workout",previous=true){
 const created=new Date(Date.UTC(2026,8,6,12,0,n)).toISOString(),long="Langdurigetrainingsprestatievergelijking".repeat(8);
 return {id:id(n),user_id:profile.id,analysis_kind:kind,status:"ready",created_at:created,completed_at:created,revision:1,model_tier:kind==="weekly"?"terra":"luna",
  period_start_local:"2026-09-06",period_end_local:"2026-09-06",timezone_name:"Europe/Amsterdam",quality:{level:"partial",missing_sources:["nutrition"]},
  summary_text:long+" <script>notExecuted()</script> Een uitgebreide beschrijving met lange Nederlandstalige woorden en grote getallen.",
  result_payload:{mock:true,actions:[],observations:[{text:"LangeNederlandstaligeAnalysetekst".repeat(20)},{text:"Krafttrainingsleistungsentwicklungszusammenfassung".repeat(20)},{text:"LongEnglishWorkoutComparison".repeat(20)}],suggestions:[{text:"Een lager volume bewijst geen vermoeidheid. Vraag bij aanhoudende klachten ondersteuning. ".repeat(8)}],
   comparison:{available:previous,reason:previous?"same_exercise_set":"first_suitable_workout",current:{id:id(100),completed_at:created,elapsed_seconds:123456789},previous:previous?{id:id(101),completed_at:created,elapsed_seconds:987654321}:null,
    exercises:[{label:"Langdurigeoefennaamzonderafbrekingen".repeat(12),current:{sets:12345,reps:123456789,max_weight_kg:123456789.5,volume_kg:987654321987654,rpe:8,rir:2},previous:previous?{sets:4,reps:12,max_weight_kg:123456789.5,volume_kg:987654321987600,rpe:7,rir:3}:null,volume_change:previous?"higher":null}]}}};
}
async function geometry(page,label){
 const data=await page.evaluate(()=>{
  const dialog=document.getElementById("fmz-analysis-detail"),main=dialog.querySelector("main"),bounds=dialog.getBoundingClientRect();
  const descendants=[dialog,...dialog.querySelectorAll("*")].filter(n=>n.getClientRects().length).map(n=>{
   const r=n.getBoundingClientRect(),s=getComputedStyle(n);
   return {tag:n.tagName,class:n.className,left:r.left,right:r.right,width:r.width,client:n.clientWidth,scroll:n.scrollWidth,minWidth:s.minWidth,overflowX:s.overflowX};
  });
  return {viewport:innerWidth,html:{scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth},body:{scroll:document.body.scrollWidth,client:document.body.clientWidth},
   bounds:{left:bounds.left,right:bounds.right},main:{scroll:main.scrollWidth,client:main.clientWidth},descendants,
   overwide:descendants.filter(n=>n.width>bounds.width+1||n.left<bounds.left-1||n.right>bounds.right+1||n.scroll>n.client+1),
   titleVisible:dialog.querySelector("header h2").getBoundingClientRect().left>=0,
   closeVisible:dialog.querySelector("[data-fmz-detail-close]").getBoundingClientRect().right<=innerWidth};
 });
 layouts.push({label,...data});
 if(!before){check(label+" html/body viewport",data.html.scroll<=data.html.client&&data.body.scroll<=data.body.client);check(label+" every detail descendant bounded: "+JSON.stringify(data.overwide.slice(0,3)),data.overwide.length===0);check(label+" header/close visible",data.titleVisible&&data.closeVisible);}
 return data;
}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
 try{
 for(const [width,height] of (before?[[320,700]]:[[320,700],[360,800],[390,844],[820,1180],[1440,900]])){
  const server=serverFixture(),context=await browser.newContext({viewport:{width,height},hasTouch:width<1000}),errors=[],writes=[];
  server.recovery.analysis_blocked=false;
  await context.addInitScript("const base="+JSON.stringify(base)+";("+mockSetup.toString()+")("+JSON.stringify(profile)+");");
  await context.route("**/*",async route=>{
   const url=new URL(route.request().url());
   if(url.pathname.endsWith("/__test_rpc")){
    const {name,args}=JSON.parse(route.request().postData());
    const data=server.rpc(name,args);
    if(name==="fmz_phase6d_get_inbox"&&server.pauseInbox){server.pauseInbox=false;await new Promise(resolve=>{server.resumeInbox=resolve;});}
    return route.fulfill({json:{data,error:null}});
   }
   if(url.hostname.endsWith(".supabase.co")){writes.push(url.pathname);return route.abort();}
   if(!route.request().url().startsWith(base))return route.fulfill({body:"",contentType:"application/javascript"});
   const relative=decodeURIComponent(url.pathname.slice(new URL(base).pathname.length))||"index.html";
   assert(!relative.includes(".."));let body;
   if(live){
    if(!resourceCache.has(relative)){const response=await fetch(base+relative+"?mobile-final="+Date.now());assert.equal(response.status,200,relative);resourceCache.set(relative,Buffer.from(await response.arrayBuffer()));}
    body=resourceCache.get(relative);
   }else body=fs.readFileSync(path.join(root,relative));
   if(relative==="app.bundle.js")body=Buffer.from(body.toString().replace("\ninit();","\n"+probe+"\ninit();"));
   return route.fulfill({body,contentType:relative.endsWith(".js")?"application/javascript":relative.endsWith(".css")?"text/css":relative.endsWith(".html")?"text/html":relative.endsWith(".svg")?"image/svg+xml":relative.endsWith(".webp")?"image/webp":"application/octet-stream"});
  });
  const page=await context.newPage();
  page.on("pageerror",e=>errors.push(e.message));page.on("console",m=>{if(m.type()==="error")errors.push(m.text());});
  await page.goto(base);await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());
  const current=analysis(1);server.results.push(current);server.notes.push({analysis_id:current.id,state:"opened",analysis_kind:current.analysis_kind,created_at:current.created_at});
  await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
  if(before){
   const openedCard=await page.locator('#fmz-analysis-inbox [data-fmz-analysis-open="'+current.id+'"]').count();
   await page.evaluate(value=>FMZ_ANALYSIS_INBOX.open(value),current.id);await page.waitForSelector("#fmz-analysis-detail table");
   await geometry(page,"before-320");await page.screenshot({path:path.join(root,"supabase/.temp/final-mobile-before-320.png"),fullPage:false});
   layouts[0].opened_dashboard_card_count=openedCard;
  }else{
   check(width+" previously opened analysis is recent",await page.locator('#fmz-analysis-inbox [data-fmz-analysis-open="'+current.id+'"]').count()===1);
   check(width+" read card has no New badge",await page.locator("#fmz-analysis-inbox .fmz-inbox-state").count()===0);
   server.notes[0].state="new";
   await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());await page.waitForSelector(".fmz-analysis-toast");
   check(width+" new analysis card without login",await page.locator("#fmz-analysis-inbox .fmz-inbox-state").textContent()==="Nieuw");
   await page.click("[data-fmz-analysis-later]");await page.waitForSelector(".fmz-analysis-toast",{state:"detached"});
   check(width+" Later keeps New card",server.notes[0].state==="later"&&await page.locator("#fmz-analysis-inbox .fmz-inbox-state").textContent()==="Nieuw");
   server.notes[0].state="new";await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
   server.pauseInbox=true;
   const pending=page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
   for(let tries=0;!server.resumeInbox&&tries<100;tries++)await new Promise(resolve=>setTimeout(resolve,20));
   assert(server.resumeInbox,"delayed inbox request captured");
   await page.click(".fmz-analysis-toast [data-fmz-analysis-open]");
   for(let tries=0;server.notes[0].state!=="opened"&&tries<100;tries++)await new Promise(resolve=>setTimeout(resolve,20));
   server.resumeInbox();server.resumeInbox=null;await pending;
   await page.waitForSelector("#fmz-analysis-detail table");await page.waitForFunction(()=>FMZ_ANALYSIS_INBOX.snapshot().inbox.unread_count===0);
   check(width+" Now exact ID",server.calls.filter(c=>c.name==="fmz_phase6d_read_analysis").at(-1).args.p_result_id===current.id);
   check(width+" viewed stays recent without New",await page.locator("#fmz-analysis-inbox .fmz-inbox-item").count()===1&&await page.locator("#fmz-analysis-inbox .fmz-inbox-state").count()===0);
   check(width+" stale in-flight inbox cannot resurrect New",server.notes[0].state==="opened"&&await page.locator(".fmz-analysis-toast").count()===0);
   await geometry(page,width+" NL comparison");
   check(width+" escaped content",await page.locator("#fmz-analysis-detail script").count()===0);
   const download=page.waitForEvent("download");await page.click("[data-fmz-detail-export]");check(width+" exact export",(await download).suggestedFilename().includes(current.id));
   await page.screenshot({path:path.join(root,"supabase/.temp/final-mobile-detail-"+width+".png"),fullPage:false});
   await page.locator(".fmz-exercise-comparison").scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(root,"supabase/.temp/final-mobile-comparison-"+width+".png"),fullPage:false});
   for(const language of ["en","de"]){
    server.settings.language=language;await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(value=>FMZ_ANALYSIS_INBOX.open(value),current.id);
    await geometry(page,width+" "+language+" comparison");
   }
   current.result_payload.comparison=analysis(1,"post_workout",false).result_payload.comparison;
   await page.evaluate(value=>FMZ_ANALYSIS_INBOX.open(value),current.id);await geometry(page,width+" first comparison");
   check(width+" first comparison honest",(await page.locator("#fmz-analysis-detail").textContent()).includes("kein verlaessliches"));
   await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.waitForSelector("#fmz-analysis-detail table");
   await geometry(page,width+" refresh deep link");check(width+" refresh preserves read card",await page.locator("#fmz-analysis-inbox .fmz-inbox-item").count()===1);
   await page.click("[data-fmz-detail-close]");await page.evaluate(()=>__hotfix.logout());await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
   check(width+" new login preserves card",await page.locator("#fmz-analysis-inbox .fmz-inbox-item").count()===1);
   for(let n=2;n<=5;n++)server.results.push(analysis(n,n%2?"daily":"weekly"));
   await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
   check(width+" three recent including missing notification",await page.locator("#fmz-analysis-inbox .fmz-inbox-item").count()===3);
   check(width+" newest exact three",JSON.stringify(await page.locator("#fmz-analysis-inbox [data-fmz-analysis-open]").evaluateAll(nodes=>nodes.map(n=>n.dataset.fmzAnalysisOpen)))===JSON.stringify([id(5),id(4),id(3)]));
   await page.screenshot({path:path.join(root,"supabase/.temp/final-mobile-dashboard-"+width+".png"),fullPage:false});
   await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate());
   check(width+" retry no duplicate",await page.locator("#fmz-analysis-inbox .fmz-inbox-item").count()===3);
   await page.click('#fmz-analysis-inbox [data-fmz-analysis-archive="'+id(5)+'"]');
   await page.waitForFunction(value=>!FMZ_ANALYSIS_INBOX.snapshot().inbox.recent.some(r=>r.analysis_id===value),id(5));
   check(width+" archive exact card only",server.results.length===5&&server.notes.find(n=>n.analysis_id===id(5)).state==="archived");
   await page.evaluate(()=>FMZ_ANALYSIS_INBOX.openHistory());await page.waitForSelector(".fmz-history-row");
   check(width+" all analyses includes archive",await page.locator(".fmz-history-row").count()===5);
   await page.click('#fmz-youri-chat [data-fmz-close]');await page.evaluate(value=>FMZ_ANALYSIS_INBOX.open(value),id(999));
   await page.waitForSelector("#fmz-analysis-detail .error");check(width+" cross ID unavailable",await page.locator("#fmz-analysis-detail table").count()===0);
   await page.click("[data-fmz-detail-close]");await page.evaluate(value=>FMZ_ANALYSIS_INBOX.open(value),id(4));await page.waitForSelector("#fmz-analysis-detail table");
   await page.click("[data-fmz-detail-delete]");await page.waitForSelector("#fmz-analysis-detail",{state:"detached"});
   check(width+" delete exact own result only",server.results.length===4&&!server.results.some(r=>r.id===id(4))&&server.results.some(r=>r.id===id(3)));
   check(width+" no console errors",errors.length===0);check(width+" no actual member request",writes.length===0);
  }
  await context.close();
 }
 }finally{await browser.close();}
 const evidence={mode:before?"before":live?"live-assets":"local",overall_pass:!before,pass_count:checks.length,checks,layouts,no_css_injected:true,real_member_requests:0};
 fs.writeFileSync(path.join(root,"supabase/.temp/final-mobile-"+(before?"before":live?"live":"local")+".json"),JSON.stringify(evidence,null,2));
 console.log(JSON.stringify({mode:evidence.mode,pass_count:checks.length,layouts:layouts.length,before_overwide:before?layouts[0].overwide:undefined,opened_card:before?layouts[0].opened_dashboard_card_count:undefined}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
