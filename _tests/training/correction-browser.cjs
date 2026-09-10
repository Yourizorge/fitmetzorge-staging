const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict"),cp=require("node:child_process");
const {chromium}=require("playwright");
const {root,base,profile,probe,mockSetup}=require("../../assets/phase6d-owner-browser-check.cjs");
const {trainingSetup,server}=require("./browser.cjs");
const catalog=JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp/training-catalog.json"),"utf8"));
const checks=[],geometry=[],screens=[],errors=[],cache=new Map();
const mode=process.argv[2]||"local",before=mode==="before",live=mode==="live";
function check(label,value){checks.push({label,pass:!!value});assert(value,label);}
async function setup(browser,backend,width=390,height=844,oldHtml=false){
 const context=await browser.newContext({viewport:{width,height},hasTouch:width<1000,isMobile:width<1000});
 await context.addInitScript("const base="+JSON.stringify(base)+";("+mockSetup.toString()+")("+JSON.stringify(profile)+");("+trainingSetup.toString()+")("+JSON.stringify(profile)+");");
 await context.route("**/*",async route=>{
  const url=new URL(route.request().url());
  try{
   if(url.pathname.endsWith("/__test_rpc")){const {name,args}=JSON.parse(route.request().postData());return route.fulfill({json:{data:backend.rpc(name,args),error:null}});}
   if(url.pathname.endsWith("/__training_query")){const {table,ops}=JSON.parse(route.request().postData());return route.fulfill({json:{data:backend.query(table,ops),error:null}});}
  }catch(e){return route.fulfill({json:{data:null,error:{message:e.message}}});}
  if(url.hostname.endsWith(".supabase.co")){errors.push("unexpected live backend");return route.abort();}
  if(!route.request().url().startsWith(base))return route.fulfill({body:"",contentType:"application/javascript"});
  const rel=decodeURIComponent(url.pathname.slice(new URL(base).pathname.length))||"index.html";assert(!rel.includes(".."));
  let body;
  if(live||before){
   if(!cache.has(rel)){const r=await fetch(base+rel+"?training-correction="+mode);assert.equal(r.status,200,rel);
    const bytes=Buffer.from(await r.arrayBuffer()),git=cp.execFileSync("git",["cat-file","blob","HEAD:"+rel],{cwd:root,windowsHide:true,maxBuffer:30000000});assert(bytes.equals(git),rel+" Git/published parity");cache.set(rel,bytes);}
   body=cache.get(rel);
  }else body=fs.readFileSync(path.join(root,rel));
  if(oldHtml&&rel==="index.html")body=Buffer.from(body.toString().replaceAll("20260909-training-correction2","20260909-training-timer1"));
  if(rel==="app.bundle.js")body=Buffer.from(body.toString().replace("\ninit();","\n"+probe+"\ninit();"));
  if(rel==="assets/phase3-training-engine.js")body=Buffer.from(body.toString().replace(/\}\)\(\);\s*$/,'window.__trainingTest={state:()=>phase3State,hydrate:()=>phase3HydrateTraining(onlineProfile),render:()=>renderTraining(),open:()=>phase3OpenFocus(),navigate:phase3Navigate,complete:phase3CompleteWorkout};})();'));
  return route.fulfill({body,contentType:rel.endsWith(".js")?"application/javascript":rel.endsWith(".css")?"text/css":rel.endsWith(".html")?"text/html":rel.endsWith(".svg")?"image/svg+xml":rel.endsWith(".png")?"image/png":"application/octet-stream"});
 });
 const page=await context.newPage();page.on("pageerror",e=>errors.push(e.message));
 await enter(page);return{page,context};
}
async function enter(page){await page.goto(base);await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));}
async function shot(page,label){const file=path.join(root,"supabase/.temp/training-correction-"+mode+"-"+label+".png");await page.screenshot({path:file});screens.push(file);}
async function timerGeometry(page,label,enforce=true){
 const g=await page.locator(".tw-timer-dial").evaluate(n=>{
  const b=n.getBoundingClientRect(),v=visualViewport,rect={x:b.x,y:b.y,w:b.width,h:b.height};
  return{rect,viewport:{w:v.width,h:v.height,x:v.offsetLeft,y:v.offsetTop},dx:b.x+b.width/2-(v.offsetLeft+v.width/2),dy:b.y+b.height/2-(v.offsetTop+v.height/2),
   position:getComputedStyle(n.closest(".phase3-focus-sheet")).position,display:getComputedStyle(n.parentElement).display,
   styles:[...document.styleSheets].map(s=>s.href||s.ownerNode.id),sw:navigator.serviceWorker?.controller?.scriptURL||null};
 });geometry.push({label,...g});console.log(label,JSON.stringify(g));
 if(enforce){check(label+" centered",Math.abs(g.dx)<=2&&Math.abs(g.dy)<=2);check(label+" round",Math.abs(g.rect.w-g.rect.h)<1);if(g.viewport.w===390&&g.viewport.h>600)check(label+" 280-320px",g.rect.w>=280&&g.rect.w<=320);
 check(label+" fully visible",g.rect.x>=0&&g.rect.y>=0&&g.rect.x+g.rect.w<=g.viewport.w&&g.rect.y+g.rect.h<=g.viewport.h);}
 await shot(page,label);return g;
}
function backendFixture(){
 const b=server();b.failSession=false;const rpc=b.rpc;
 b.rpc=function(name,args){
  if(name!=="fmz_training_save_workout_v2")return rpc.call(this,name,args);
  const result=rpc.call(this,"fmz_training_save_workout",args);
  this.db.training_plans.find(p=>p.id===result.id).metadata={effort_tracking:args.p_effort_tracking};
  return result;
 };return b;
}
async function create(page,flags,title){
 await page.click('[data-phase3-toggle-section="builder"]');await page.click("[data-phase3-maker-open]");
 await page.locator('[data-tw-select="'+catalog[0].id+'"]').check();await page.click('[data-tw-action="selected"]');
 await page.fill("[data-tw-title]",title);
 if(!before){check("new defaults off "+title,!await page.locator('[data-tw-tracking="rir"]').isChecked()&&!await page.locator('[data-tw-tracking="rpe"]').isChecked());
 for(const key of ["rir","rpe"])await page.locator('[data-tw-tracking="'+key+'"]').setChecked(flags[key]);}
 await page.click('[data-tw-action="save"]');await page.waitForSelector("#fmz-workout-maker",{state:"detached"});
}
async function start(page){await page.locator("[data-phase3-start-workout]").first().click();await page.waitForSelector(".tw-live-set");}
async function timerChecks(page,backend,width){
 const state=()=>page.evaluate(()=>__trainingTest.state().activeSession);
 check("timer initially absent",await page.locator(".tw-rest-panel").count()===0);
 await page.click("[data-phase3-timer-open]");await page.fill("[data-phase3-session-rest]","75");await page.click("[data-phase3-start-manual-rest]");
 await timerGeometry(page,width+"-timer-light",!before);
 if(before){
  await page.locator('link[href*="training-workout.css"]').evaluate(n=>n.disabled=true);
  await timerGeometry(page,"390-timer-missing-stylesheet",false);
  return;
 }
 const rest=(await state()).focus.rest,end=rest.endsAt,id=(await state()).id;
 await page.waitForTimeout(2100);check("countdown moves",await page.locator("[data-phase3-rest-countdown]").textContent()!=="01:15");
 check("ring decreases",await page.locator("[data-phase3-rest-ring]").evaluate(n=>Number(n.style.getPropertyValue("--rest-progress"))<1));
 await page.click("[data-phase3-rest-view]");check("minimize same timer",(await state()).focus.rest.endsAt===end&&await page.locator(".tw-live-set").count()===3);
 await page.click("[data-phase3-timer-open]");check("reopen same deadline",(await state()).focus.rest.endsAt===end);
 await page.click("[data-phase3-rest-pause]");const paused=(await state()).focus.rest.remainingMs;await page.waitForTimeout(1100);
 check("pause stable",(await state()).focus.rest.remainingMs===paused);await page.click("[data-phase3-add-rest]");check("plus15",(await state()).focus.rest.remainingMs===paused+15000);
 await enter(page);await page.evaluate(()=>__trainingTest.open());check("refresh pause/view",(await state()).focus.rest.remainingMs===paused+15000&&await page.locator(".tw-timer-dial").count()===1);
 await page.click("[data-phase3-rest-pause]");
 await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));await page.waitForTimeout(7100);
 check("background wallclock",await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest.endsAt-Date.now())<paused+9000);
 await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));
 backend.s.settings.display.theme_mode="dark";await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(()=>__trainingTest.render());await timerGeometry(page,width+"-timer-dark");
 for(const [w,h] of [[844,390],[390,650]]){await page.setViewportSize({width:w,height:h});await timerGeometry(page,width+"-"+w+"x"+h);}
 await page.setViewportSize({width,height:width===390?844:700});
 check("controls reachable",await page.locator(".tw-timer-actions button").evaluateAll(ns=>ns.length===3&&ns.every(n=>{const b=n.getBoundingClientRect();return b.height>=44&&b.width>=44&&b.bottom<=innerHeight;})));
 await page.click("[data-phase3-stop-rest]");check("stop no sets",(await state()).id===id&&(await state()).status==="active"&&Object.keys((await state()).setLogs).length===0);
 await page.fill("[data-phase3-session-rest]","2");await page.click("[data-phase3-start-manual-rest]");await page.waitForFunction(()=>!__trainingTest.state().activeSession.focus.rest);
 check("expiry no completion",(await state()).status==="active"&&Object.keys((await state()).setLogs).length===0);
}
async function fields(page,flags,label){
 for(const key of ["rir","rpe"])check(label+" "+key+" visibility",await page.locator("[data-phase3-"+key+"]").count()===(flags[key]?3:0));
 check(label+" no global selector",await page.locator("[data-phase3-effort-mode]").count()===0);
 const g=await page.locator(".tw-live-set").first().evaluate(n=>{
  const top=[...n.children].slice(0,5).map(e=>e.getBoundingClientRect()),extras=[...n.querySelectorAll(".tw-set-effort input")].map(e=>e.getBoundingClientRect());
  return{mainAligned:top.every(r=>r.top<top[0].bottom&&r.bottom>top[0].top),extraBelow:extras.every(r=>r.top>=Math.max(...top.map(r=>r.bottom))),tap:extras.every(r=>r.width>=44&&r.height>=44),noOverlap:extras.length<2||extras[0].right<extras[1].left,extraCount:extras.length,overflow:n.scrollWidth>n.clientWidth+1,pageOverflow:document.documentElement.scrollWidth>innerWidth};
 });
 check(label+" compact main plus own lower fields",g.mainAligned&&g.extraBelow&&g.tap&&g.noOverlap&&!g.overflow&&!g.pageOverflow);
 check(label+" no empty subrow",await page.locator(".tw-live-set").first().locator(".tw-set-effort").count()===(flags.rir||flags.rpe?1:0));
}
async function combination(browser,width,flags){
 const label=width+"-"+Number(flags.rir)+Number(flags.rpe),b=backendFixture(),{page,context}=await setup(browser,b,width,width===1440?900:844);
 await create(page,flags,label);let plan=b.db.training_plans[0];
 check(label+" atomic saved flags",JSON.stringify(plan.metadata.effort_tracking)===JSON.stringify(flags));
 await enter(page);await page.locator("[data-phase3-edit-plan]").first().click();
 for(const k of ["rir","rpe"])check(label+" editor rehydrated "+k,await page.locator('[data-tw-tracking="'+k+'"]').isChecked()===flags[k]);
 // Populate both targets, then switch back: hiding is never data deletion.
 for(const k of ["rir","rpe"])await page.locator('[data-tw-tracking="'+k+'"]').check();
 await page.fill('[data-tw-target="0:0:rir"]',"0");await page.fill('[data-tw-target="0:0:rpe"]',"9.5");
 for(const k of ["rir","rpe"])await page.locator('[data-tw-tracking="'+k+'"]').setChecked(flags[k]);
 await shot(page,label+"-maker");
 await page.click('[data-tw-action="save"]');await page.waitForSelector("#fmz-workout-maker",{state:"detached"});
 check(label+" hidden targets retained",b.db.training_plan_exercises[0].set_targets[0].rir===0&&b.db.training_plan_exercises[0].set_targets[0].rpe===9.5);
 await start(page);await fields(page,flags,label);
 const sessionId=b.db.workout_sessions[0].id;
 check(label+" persisted snapshot",JSON.stringify(b.db.workout_sessions[0].metadata.effortTracking)===JSON.stringify(flags));
 await page.locator("[data-phase3-weight]").first().fill("55.5");await page.locator("[data-phase3-reps]").first().fill("8");
 if(flags.rir)await page.locator("[data-phase3-rir]").first().fill("0");
 if(flags.rpe)await page.locator("[data-phase3-rpe]").first().fill("9.5");
 b.failSet=true;await page.locator("[data-phase3-complete-set]").first().click();
 await page.waitForFunction(()=>document.querySelector(".tw-focus .tw-feedback")?.textContent);
 check(label+" failed set retains entry",await page.locator("[data-phase3-reps]").first().inputValue()==="8");
 await page.locator("[data-phase3-complete-set]").first().click();await page.waitForFunction(()=>Object.values(__trainingTest.state().activeSession.setLogs).some(s=>s.syncedAt));
 let saved=b.db.workout_set_logs[0];check(label+" distinct actual values",saved.rir===(flags.rir?0:null)&&saved.rpe===(flags.rpe?9.5:null)&&saved.actual_reps===8);
 await enter(page);await page.evaluate(()=>__trainingTest.open());await fields(page,flags,label+" reload");
 check(label+" reload values",(!flags.rir||await page.locator("[data-phase3-rir]").first().inputValue()==="0")&&(!flags.rpe||await page.locator("[data-phase3-rpe]").first().inputValue()==="9.5"));
 if(flags.rir)check(label+" blank different from zero",await page.locator("[data-phase3-rir]").nth(1).inputValue()==="");
 for(const theme of ["light","dark"]){b.s.settings.display.theme_mode=theme;await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(()=>__trainingTest.render());await fields(page,flags,label+theme);await shot(page,label+"-sets-"+theme);}
 await page.click("[data-phase3-close-focus]");await page.locator("[data-phase3-edit-plan]").first().click();
 const inverse={rir:!flags.rir,rpe:!flags.rpe};
 for(const k of ["rir","rpe"])await page.locator('[data-tw-tracking="'+k+'"]').setChecked(inverse[k]);
 await page.click('[data-tw-action="save"]');await page.waitForSelector("#fmz-workout-maker",{state:"detached"});
 check(label+" plan edit saves both choices",JSON.stringify(b.db.training_plans[0].metadata.effort_tracking)===JSON.stringify(inverse));
 await page.evaluate(()=>__trainingTest.open());await fields(page,flags,label+" immutable active snapshot");
 check(label+" edit preserves logs",b.db.workout_set_logs[0].rir===saved.rir&&b.db.workout_set_logs[0].rpe===saved.rpe);
 await page.click("[data-phase3-close-focus]");await page.evaluate(()=>FMZ_OWNER_SETTINGS.open("training"));
 check(label+" contradictory Settings removed",await page.locator('#fmz-settings [name="training_effort_mode"]').count()===0);
 await page.click("#fmz-settings [data-fmz-close]");
 await page.evaluate(()=>FMZ_OWNER_SETTINGS.open("logout"));await page.locator("#fmz-settings [data-fmz-logout]").click();
 await page.waitForSelector("#loginForm",{state:"visible"});
 check(label+" actual logout control",await page.evaluate(()=>__authCalls.some(c=>c.startsWith("member_signout"))));
 await page.locator('#loginForm [name="role"]').selectOption("client");
 await page.fill('#loginForm [name="email"]',profile.email);await page.fill('#loginForm [name="password"]',"valid-synthetic-current");
 await page.click('#loginForm [type="submit"]');await page.waitForFunction(()=>!document.body.classList.contains("logged-out"));
 await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));await page.evaluate(()=>__trainingTest.open());
 await fields(page,flags,label+" real form synthetic relogin");
 check(label+" same session after login",await page.evaluate(id=>__trainingTest.state().activeSession.id===id,sessionId));
 await context.close();
 // A fresh browser has no local drafts: flags and scores must come from server metadata.
 const fresh=await setup(browser,b,width,844);await fresh.page.evaluate(()=>__trainingTest.open());await fields(fresh.page,flags,label+" fresh storage");
 check(label+" server-only scores",(!flags.rir||await fresh.page.locator("[data-phase3-rir]").first().inputValue()==="0")&&(!flags.rpe||await fresh.page.locator("[data-phase3-rpe]").first().inputValue()==="9.5"));
 await fresh.page.click("[data-phase3-complete-workout]");await fresh.page.waitForFunction(()=>!__trainingTest.state().activeSession);
 check(label+" immediate local history snapshot",await fresh.page.evaluate(flags=>JSON.stringify(__trainingTest.state().history[0].metadata.effortTracking)===JSON.stringify(flags),flags));
 await start(fresh.page);await fields(fresh.page,inverse,label+" next session new flags");
 check(label+" history values preserved",b.db.workout_set_logs[0].rir===saved.rir&&b.db.workout_set_logs[0].rpe===saved.rpe);
 await fresh.context.close();
}
module.exports={setup,backendFixture,enter,create,start,timerGeometry};
if(require.main===module)(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
 try{
 const b=backendFixture(),{page,context}=await setup(browser,b,390,844,!before);await create(page,{rir:false,rpe:false},"Timer");await start(page);
 if(!before)check("stale HTML uses one matching current Training stylesheet",await page.locator('link[href*="training-workout.css"]').count()===1&&await page.locator('link[href*="training-workout.css"]').evaluate(n=>n.href.endsWith("20260909-training-correction2")&&!!n.sheet));
 await timerChecks(page,b,390);await context.close();
 if(!before)for(const width of (process.env.FMZ_CORRECTION_SMOKE?[390]:[320,390,1440]))for(const flags of [{rir:false,rpe:false},{rir:true,rpe:false},{rir:false,rpe:true},{rir:true,rpe:true}])await combination(browser,width,flags);
 check("no JavaScript/live backend errors",errors.length===0);
 const result={mode,checks,geometry,screens,errors,synthetic_only:true,physical_phone:false};fs.writeFileSync(path.join(root,"supabase/.temp/training-correction-"+mode+".json"),JSON.stringify(result,null,2));console.log(JSON.stringify({mode,passed:checks.length,screens:screens.length}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
