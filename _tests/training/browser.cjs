const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const {chromium}=require("playwright");
const {root,base,profile,probe,mockSetup,serverFixture}=require("../../assets/phase6d-owner-browser-check.cjs");
const catalog=JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp/training-catalog.json"),"utf8"));
const checks=[],screens=[],errors=[],writes=[],layouts=[];
const liveAssets=new Map();
function check(name,value){checks.push({name,pass:!!value});assert(value,name);}
function trainingSetup(profile){
 const original=window.supabase.createClient;
 window.supabase.createClient=(...args)=>{
  const client=original(...args);
  client.from=table=>{
   const ops=[];const chain=new Proxy({}, {get(t,key){
    if(key==="then")return(resolve,reject)=>fetch(base+"__training_query",{method:"POST",body:JSON.stringify({table,ops})}).then(r=>r.json()).then(resolve,reject);
    return(...args)=>{ops.push([key,args]);return chain;};
   }});return chain;
  };
  return client;
 };
}
function server(){
 const s=serverFixture(),db={training_plans:[],training_plan_days:[],training_plan_exercises:[],workout_sessions:[],workout_set_logs:[]};
 const pref={effort_mode:"rir",timer_enabled:true,revision:0};let revision=0;
 s.recovery.analysis_blocked=false;
 return {s,db,pref,failSave:false,failSet:false,failCompletion:false,completionEvents:0,
 rpc(name,args){
  if(name==="fmz_training_get_preferences")return {...pref};
  if(name==="fmz_training_set_preferences"){assert.equal(args.p_expected_revision,pref.revision);Object.assign(pref,{effort_mode:args.p_effort_mode,timer_enabled:args.p_timer_enabled,revision:pref.revision+1});return {...pref};}
  if(name==="fmz_training_save_workout"){
   if(this.failSave){this.failSave=false;throw Error("simulated_offline");}
   const existing=db.training_plans.find(p=>p.id===args.p_plan_id),updated_at=new Date(Date.UTC(2026,8,8,10,0,++revision)).toISOString();
   if(existing&&existing.save_id===args.p_save_id)return{id:existing.id,updated_at:existing.updated_at,replayed:true};
   if(existing&&existing.updated_at!==args.p_expected_updated_at)throw Error("training_stale_conflict");
   const plan={id:args.p_plan_id,user_id:profile.id,title:args.p_title,status:"active",source:"phase3_client",created_at:updated_at,updated_at,save_id:args.p_save_id};
   db.training_plans=db.training_plans.filter(p=>p.id!==plan.id).concat(plan);
   db.training_plan_days=db.training_plan_days.filter(d=>d.id!==args.p_day_id).concat({id:args.p_day_id,training_plan_id:plan.id,day_label:args.p_day_label,day_order:args.p_day_order,status:"active"});
   db.training_plan_exercises.forEach(e=>{if(e.training_plan_day_id===args.p_day_id)e.status="archived";});
   args.p_exercises.forEach(e=>{const i=db.training_plan_exercises.findIndex(x=>x.id===e.id);if(i>=0)db.training_plan_exercises[i]=e;else db.training_plan_exercises.push(e);});
   return {id:plan.id,updated_at,replayed:false};
  }
  if(name==="fmz_training_complete_workout"){
   const session=db.workout_sessions.find(s=>s.id===args.p_session_id);assert(session);
   if(session.status!=="completed"){session.status="completed";session.completed_at=args.p_completed_at;this.completionEvents++;}
   if(this.failCompletion){this.failCompletion=false;throw Error("simulated_response_lost");}
   return{completed_at:session.completed_at};
  }
  return s.rpc(name,args);
 },
 query(table,ops){
  if(table==="profiles")return profile;
  let data=table==="exercises"?catalog:db[table]||[];
  const mutation=ops.find(([key])=>["insert","upsert","update"].includes(key));
  if(mutation){
   if(table==="workout_set_logs"&&this.failSet){this.failSet=false;throw Error("simulated_set_failure");}
   writes.push(table);
   const row=mutation[1][0],existing=data.find(x=>x.id===row.id);
   if(existing)Object.assign(existing,row);else data.push({...row});
  }
  for(const [method,args] of ops){
   if(method==="eq")data=data.filter(row=>row[args[0]]===args[1]);
   if(method==="in")data=data.filter(row=>args[1].includes(row[args[0]]));
   if(method==="range")data=data.slice(args[0],args[1]+1);
   if(method==="order"){const [key,{ascending=true}={}]=args;data=data.slice().sort((a,b)=>String(a[key]).localeCompare(String(b[key]))*(ascending?1:-1));}
   if(method==="limit")data=data.slice(0,args[0]);
  }
  return ops.some(([key])=>["single","maybeSingle"].includes(key))?data[0]||null:data;
 }};
}
async function geometry(page,label,selector){
 const g=await page.locator(selector).evaluate(root=>{
  const bounds=root.getBoundingClientRect(),items=[root,...root.querySelectorAll("*")].filter(n=>n.getClientRects().length);
  const bad=items.filter(n=>{const r=n.getBoundingClientRect();return r.width>bounds.width+1||r.left<bounds.left-1||r.right>bounds.right+1||n.scrollWidth>n.clientWidth+2&&getComputedStyle(n).overflowX==="visible";})
   .map(n=>({tag:n.tagName,class:n.className,width:n.getBoundingClientRect().width,scroll:n.scrollWidth,client:n.clientWidth}));
  return{bad,html:document.documentElement.scrollWidth,viewport:innerWidth};
 });
 layouts.push({label,...g});check(label+" viewport",g.html<=g.viewport);check(label+" bounded controls "+JSON.stringify(g.bad.slice(0,3)),g.bad.length===0);
}
async function screenshot(page,label){
 const output=path.join(root,"supabase/.temp/training-"+label+".png");await page.screenshot({path:output,fullPage:false});screens.push(output);
}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
 try{
 for(const [width,height] of(process.env.FMZ_TRAINING_DESKTOP?[[1440,900]]:process.env.FMZ_TRAINING_SMOKE?[[390,844]]:[[320,700],[390,844],[820,1180],[1440,900]])){
  const backend=server(),context=await browser.newContext({viewport:{width,height},hasTouch:width<1000});
  await context.addInitScript("const base="+JSON.stringify(base)+";("+mockSetup.toString()+")("+JSON.stringify(profile)+");("+trainingSetup.toString()+")("+JSON.stringify(profile)+");");
  await context.route("**/*",async route=>{
   const url=new URL(route.request().url());
   try{
    if(url.pathname.endsWith("/__test_rpc")){const {name,args}=JSON.parse(route.request().postData());return route.fulfill({json:{data:backend.rpc(name,args),error:null}});}
    if(url.pathname.endsWith("/__training_query")){const {table,ops}=JSON.parse(route.request().postData());return route.fulfill({json:{data:backend.query(table,ops),error:null}});}
   }catch(e){return route.fulfill({json:{data:null,error:{message:e.message}}});}
   if(url.hostname.endsWith(".supabase.co"))throw Error("unexpected_live_supabase_request");
   if(!route.request().url().startsWith(base))return route.fulfill({body:"",contentType:"application/javascript"});
   const rel=decodeURIComponent(url.pathname.slice(new URL(base).pathname.length))||"index.html";assert(!rel.includes(".."));
   let body;
   if(process.env.FMZ_TRAINING_LIVE){
    if(!liveAssets.has(rel)){const response=await fetch(base+rel+"?training-verification="+process.env.FMZ_TRAINING_LIVE);assert.equal(response.status,200,rel);liveAssets.set(rel,Buffer.from(await response.arrayBuffer()));}
    body=liveAssets.get(rel);assert(body.equals(require("node:child_process").execFileSync("git",["cat-file","blob","HEAD:"+rel],{cwd:root,windowsHide:true,maxBuffer:30000000})),"published bytes "+rel);
   }else body=fs.readFileSync(path.join(root,rel));
   if(rel==="app.bundle.js")body=Buffer.from(body.toString().replace("\ninit();","\n"+probe+"\ninit();"));
   if(rel==="assets/phase3-training-engine.js")body=Buffer.from(body.toString().replace(/\}\)\(\);\s*$/,'window.__trainingTest={state:()=>phase3State,hydrate:()=>phase3HydrateTraining(onlineProfile),render:()=>renderTraining(),open:()=>phase3OpenFocus(),navigate:phase3Navigate,complete:phase3CompleteWorkout};})();'));
   return route.fulfill({body,contentType:rel.endsWith(".js")?"application/javascript":rel.endsWith(".css")?"text/css":rel.endsWith(".html")?"text/html":rel.endsWith(".svg")?"image/svg+xml":rel.endsWith(".png")?"image/png":rel.endsWith(".webp")?"image/webp":"application/octet-stream"});
  });
  const page=await context.newPage();page.on("pageerror",e=>errors.push(e.message));
  await page.goto(base);await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());
  await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));
  await page.click('[data-phase3-toggle-section="builder"]');await page.click("[data-phase3-maker-open]");
  await page.waitForSelector("[data-tw-select]");
  check(width+" canonical catalog",await page.evaluate(()=>document.querySelectorAll("[data-tw-select]").length)===72);
  const first=catalog[0],second=catalog[1];
  await page.locator('[data-tw-select="'+first.id+'"]').check();await page.locator('[data-tw-select="'+second.id+'"]').check();
  await page.fill('[data-tw-filter="search"]',first.name_en);check(width+" selection retained through search",await page.locator("[data-tw-count]").textContent()==="2 geselecteerd");
  await page.click('[data-tw-action="info"]');
  await page.waitForSelector(".tw-media-large");
  await page.click('[data-tw-action="back"]');
  check(width+" detail returns with search",await page.inputValue('[data-tw-filter="search"]')===first.name_en);
  await page.fill('[data-tw-filter="search"]',"");await geometry(page,width+" library","#fmz-workout-maker");await screenshot(page,width+"-library");
  for(const filter of ["muscle","equipment"]){
   await page.locator('[data-tw-filter="'+filter+'"]').selectOption({index:1});
   check(width+" selection through "+filter,await page.locator("[data-tw-count]").textContent()==="2 geselecteerd");
   await page.locator('[data-tw-filter="'+filter+'"]').selectOption("");
  }
  await page.click('[data-tw-action="selected"]');await page.fill("[data-tw-title]","Full body A");
  await page.click('[data-tw-action="down"][data-tw-index="0"]');
  check(width+" accessible reorder",await page.locator(".tw-exercise h3").first().textContent()!==first.name_en);
  await page.click('[data-tw-action="up"][data-tw-index="1"]');
  const beforeDrag=await page.locator(".tw-exercise h3").allTextContents();
  if(width>=1000){
   await page.locator('[data-tw-drag="0"]').scrollIntoViewIfNeeded();
   const box=await page.locator('[data-tw-drag="0"]').boundingBox();
   await page.mouse.move(box.x+22,box.y+22);await page.mouse.down();await page.mouse.move(box.x+22,box.y+36,{steps:5});
   await page.waitForSelector(".tw-dragging");
   const target=await page.locator('[data-tw-exercise="1"] header').boundingBox();
   await page.mouse.move(target.x+30,target.y+30,{steps:12});await page.mouse.move(target.x+32,target.y+32);
   await page.mouse.up();
  }
  else {
   const transfer=await page.evaluateHandle(()=>new DataTransfer());
   await page.locator('[data-tw-drag="0"]').dispatchEvent("dragstart",{dataTransfer:transfer});
   await page.locator('[data-tw-exercise="1"]').dispatchEvent("drop",{dataTransfer:transfer});
  }
  check(width+" drag reorder",JSON.stringify(await page.locator(".tw-exercise h3").allTextContents())===JSON.stringify(beforeDrag.slice().reverse()));
  await page.click('[data-tw-action="up"][data-tw-index="1"]');
  await page.click('[data-tw-action="add-set"][data-tw-index="0"]');
  check(width+" add set",await page.locator('[data-tw-exercise="0"] .tw-target-row').count()===4);
  await page.click('[data-tw-action="remove-set"][data-tw-index="0:3"]');
  await page.click('[data-tw-action="back"]');await page.click("[data-phase3-maker-open]");
  check(width+" draft reopen retained",await page.inputValue("[data-tw-title]")==="Full body A");
  await page.fill('[data-tw-target="0:0:reps"]',"10");await page.fill('[data-tw-target="0:0:rir"]',"0");
  await page.click('[data-tw-action="group"]');await page.fill('[data-tw-group-rest="0"]',"120");
  await page.locator("#fmz-workout-maker main").evaluate(n=>n.scrollTop=0);
  await geometry(page,width+" editor","#fmz-workout-maker");await screenshot(page,width+"-editor");
  backend.failSave=true;await page.click('[data-tw-action="save"]');await page.waitForFunction(()=>document.querySelector(".tw-feedback")?.textContent.includes("Niet opgeslagen"));
  check(width+" failed save is atomic",backend.db.training_plans.length===0);
  await page.click('[data-tw-action="save"]');await page.waitForSelector("#fmz-workout-maker",{state:"detached"});
  check(width+" saved same canonical IDs",backend.db.training_plan_exercises[0].exercise_id===first.id);
  check(width+" persisted per-set targets + group",backend.db.training_plan_exercises[0].set_targets[0].rir===0&&backend.db.training_plan_exercises[0].superset_rest_seconds===120);
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));
  await page.click("[data-phase3-start-workout]");await page.waitForSelector(".tw-live-set");
  check(width+" only RIR shown",await page.locator("[data-phase3-rpe]").count()===0&&await page.locator("[data-phase3-rir]").count()===3);
  await page.locator("[data-phase3-reps]").nth(1).fill("9");
  await page.locator("[data-phase3-reps]").first().fill("10");
  backend.failSet=true;await page.locator("[data-phase3-complete-set]").first().click();await page.waitForFunction(()=>!__trainingTest.state().activeSession.focus.rest);
  check(width+" failed set has no timer",!await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest));
  await page.locator("[data-phase3-complete-set]").first().click();
  await page.waitForFunction(()=>__trainingTest.state().activeSession.focus.currentExerciseIndex===1);
  check(width+" superset first exercise no rest",!await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest));
  await page.locator("[data-phase3-reps]").first().fill("10");await page.locator("[data-phase3-complete-set]").first().click();
  await page.waitForSelector("[data-phase3-rest-countdown]");
  check(width+" group rest 120",await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest.durationSeconds)===120);
  const timerDeadline=await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest.endsAt);
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));await page.evaluate(()=>__trainingTest.open());
  check(width+" refresh retains timer deadline",await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest.endsAt)===timerDeadline);
  const away=await context.newPage();await away.goto("about:blank");await page.bringToFront();
  await page.evaluate(()=>document.dispatchEvent(new Event("visibilitychange")));await away.close();
  check(width+" background return retains timer",await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest.endsAt)===timerDeadline);
  await page.click("[data-phase3-rest-pause]");check(width+" pause timer",await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest.paused));
  await page.click("[data-phase3-add-rest]");check(width+" +15 seconds",await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest.remainingMs)>130000);
  await page.click("[data-phase3-rest-pause]");await page.click("[data-phase3-skip-rest]");
  await page.waitForFunction(()=>__trainingTest.state().activeSession.focus.currentExerciseIndex===0);
  check(width+" unsaved input survived navigation",await page.locator("[data-phase3-reps]").nth(1).inputValue()==="9");
  check(width+" registered remains visible",await page.locator('[data-registered="true"]').count()===1);
  await geometry(page,width+" execution",".tw-focus");await screenshot(page,width+"-execution");
  // A registered correction updates the same set, without another rest or round.
  await page.locator("[data-phase3-reps]").first().fill("11");await page.locator("[data-phase3-complete-set]").first().click();
  await page.waitForFunction(()=>Object.values(__trainingTest.state().activeSession.setLogs).some(s=>s.actualReps===11&&s.syncedAt));
  check(width+" correction same set identity",backend.db.workout_set_logs.length===2&&!await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest));
  await page.locator("[data-phase3-reps]").nth(1).fill("9");await page.locator("[data-phase3-complete-set]").nth(1).click();
  await page.waitForFunction(()=>__trainingTest.state().activeSession.focus.currentExerciseIndex===1);
  await page.locator("[data-phase3-reps]").nth(1).fill("9");await page.locator("[data-phase3-complete-set]").nth(1).click();
  await page.waitForSelector("[data-phase3-rest-countdown]");
  await page.locator("[data-phase3-timer-enabled]").uncheck();await page.waitForFunction(()=>FMZ_TRAINING.preferences().timer_enabled===false);
  check(width+" disabling clears active timer",!await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest));
  await page.evaluate(()=>__trainingTest.navigate(0));
  for(const mode of ["rpe","none","rir"]){await page.evaluate(mode=>FMZ_TRAINING.setPreferences({effort_mode:mode}),mode);check(width+" effort mode "+mode,await page.locator("[data-phase3-rir]").count()===(mode==="rir"?3:0)&&await page.locator("[data-phase3-rpe]").count()===(mode==="rpe"?3:0));}
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));await page.evaluate(()=>__trainingTest.open());
  check(width+" timer preference persists",!await page.locator("[data-phase3-timer-enabled]").isChecked());
  check(width+" draft set input refresh",await page.locator("[data-phase3-reps]").nth(1).inputValue()==="9");
  backend.failCompletion=true;await page.click("[data-phase3-complete-workout]");await page.waitForFunction(()=>__trainingTest.state().activeSession?.focus.feedback);
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));await page.evaluate(()=>__trainingTest.open());
  check(width+" lost completion refresh permits retry",await page.locator("[data-phase3-complete-workout]").isEnabled());
  await page.click("[data-phase3-complete-workout]");await page.waitForSelector(".tw-focus",{state:"detached"});
  check(width+" one completion after response loss",backend.completionEvents===1&&backend.db.workout_sessions.length===1);
  check(width+" history retained",await page.evaluate(()=>__trainingTest.state().history.length)===1);
  await page.evaluate(()=>FMZ_OWNER_SETTINGS.open("training"));
  await page.check('#fmz-settings [name="training_effort_mode"][value="rpe"]');
  await page.waitForFunction(()=>FMZ_TRAINING.preferences().effort_mode==="rpe");
  check(width+" settings Training real radio saved",backend.pref.effort_mode==="rpe");
  await geometry(page,width+" training settings","#fmz-settings");
  await page.click("#fmz-settings [data-fmz-close]");
  await page.click("[data-phase3-edit-plan]");
  check(width+" existing same editor",await page.inputValue("[data-tw-title]")==="Full body A");
  await page.click('[data-tw-action="unlink"]');
  await page.click('[data-tw-action="replace"][data-tw-index="1"]');
  await page.locator('[data-tw-select="'+catalog[2].id+'"]').check();await page.click('[data-tw-action="selected"]');
  await page.click('[data-tw-action="library"]');await page.locator('[data-tw-select="'+catalog[3].id+'"]').check();await page.click('[data-tw-action="selected"]');
  await page.click('[data-tw-action="remove"][data-tw-index="2"]');
  await page.fill("[data-tw-title]","Edited workout");await page.click('[data-tw-action="save"]');await page.waitForSelector("#fmz-workout-maker",{state:"detached"});
  check(width+" existing edit no new plan",backend.db.training_plans.length===1&&backend.db.training_plans[0].title==="Edited workout");
  check(width+" replacement uses new canonical ID",backend.db.training_plan_exercises.some(e=>e.status==="active"&&e.exercise_id===catalog[2].id));
  check(width+" completed snapshot unchanged",backend.db.workout_sessions[0].title_snapshot==="Full body A"&&backend.db.workout_sessions[0].metadata.plannedExercises[1].exerciseId===second.id);
  for(const [language,theme,unit] of [["nl","light","metric"],["en","dark","imperial"],["de","system","metric"]]){
   backend.s.settings.language=language;backend.s.settings.display.theme_mode=theme;backend.s.settings.unit_system=unit;
   await page.emulateMedia({colorScheme:theme==="system"?"dark":theme});
   await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.click("[data-phase3-edit-plan]");
   check(width+" "+language+" weight units",await page.locator(".tw-target-row").first().textContent().then(t=>t.includes(unit==="imperial"?"lb":"kg")));
   check(width+" "+language+" catalog metadata",await page.locator(".tw-exercise header small").first().textContent().then(t=>t.length>5));
   await geometry(page,width+" "+language+" "+theme+" maker","#fmz-workout-maker");
   await page.locator("#fmz-workout-maker main").evaluate(n=>n.scrollTop=0);await screenshot(page,width+"-"+language+"-"+theme);
   await page.click('[data-tw-action="cancel"]');
  }
  backend.s.settings.language="nl";backend.s.settings.unit_system="imperial";await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));
  await page.click("[data-phase3-start-workout]");await page.waitForSelector(".tw-live-set");
  check(width+" previous exact set shown",await page.locator(".tw-live-set").first().textContent().then(t=>t.includes("11")));
  await page.locator("[data-phase3-weight]").first().fill("44.09");await page.locator("[data-phase3-reps]").first().fill("8");
  await page.locator("[data-phase3-complete-set]").first().click();
  await page.waitForFunction(()=>Object.values(__trainingTest.state().activeSession.setLogs).some(s=>s.syncedAt));
  check(width+" imperial input stored kg",Math.abs(backend.db.workout_set_logs.at(-1).actual_weight-20)<.005);
  await page.click("[data-phase3-close-focus]");
  await page.evaluate(()=>__hotfix.view("progress"));await page.evaluate(()=>__hotfix.view("client-home"));
  check(width+" post-workout dashboard retained",await page.locator("#client-home #clientSummary").isVisible()&&await page.locator("#clientSummary").textContent().then(t=>t.length>50));
  check(width+" no JS error "+JSON.stringify(errors),errors.length===0);
  await context.close();
 }
 const result={overall_pass:true,checks,layouts,screens,source:process.env.FMZ_TRAINING_LIVE?"published":"working_tree",synthetic_only:true,live_member_mutations:0};
 fs.writeFileSync(path.join(root,"supabase/.temp/training-browser-"+(process.env.FMZ_TRAINING_LIVE?"live":"local")+".json"),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);console.log(JSON.stringify({overall_pass:false,checks,layouts,screens,errors},null,2));process.exitCode=1;});
