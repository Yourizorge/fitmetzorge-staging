const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const {chromium}=require("playwright");
const root=path.resolve(__dirname,".."),base="https://yourizorge.github.io/fitmetzorge-staging/";
const checks=[];function check(name,pass){checks.push({name,pass:!!pass});assert(pass,name);}
const profile={id:"30000000-0000-4000-8000-000000000001",role:"client",name:"Synthetic",email:"synthetic@example.invalid",trainer_id:null,email_confirmed_at:"2026-09-06T06:00:00Z"};
const probe=String.raw`
window.__hotfix={
 enter:async()=>{window.__memberSession=true;window.FMZ_PUBLIC_AUTH.enterApp();passwordSetupRequired=false;onlineProfile=window.__mockProfile;onlineReady=true;state.ui.loggedIn=true;state.ui.role="client";currentView="client-home";renderNav();renderAll();showView("client-home");await window.FMZ_OWNER_SETTINGS.hydrate(true);},
 view:id=>showView(id),current:()=>currentView,render:()=>renderAll(),logout:()=>{state.ui.loggedIn=false;onlineProfile=null;onlineReady=false;renderAll();},
 safety:()=>window.FMZ_PHASE6C_PRIVATE_CHAT.hydrate({force:true})
};
`;
function mockSetup(profile) {
 window.__mockProfile=profile;
 const query=table=>{
  const chain=new Proxy({}, {get(_target,key){if(key==="then")return resolve=>Promise.resolve({data:table==="profiles"?profile:null,error:null}).then(resolve);return()=>chain;}});
  return chain;
 };
 const listeners=[];
 window.__authCalls=[];
 window.supabase={createClient:(_url,_key,options)=>({
  auth:{getSession:async()=>({data:{session:window.__memberSession?{user:profile,access_token:'synthetic-token'}:null}}),getUser:async()=>({data:{user:profile}}),
   onAuthStateChange:fn=>{listeners.push(fn);return{data:{subscription:{unsubscribe(){}}}};},
   signInWithPassword:async input=>{window.__authCalls.push("verify_current_password");return{error:input.password==="valid-synthetic-current"?null:{message:"invalid synthetic password"}};},
   signOut:async input=>{const isolated=options?.auth?.persistSession===false;window.__authCalls.push((isolated?"isolated_":"member_")+"signout_"+(input?.scope||"global"));if(!isolated)listeners.forEach(fn=>fn("SIGNED_OUT"));return{error:null};},
   updateUser:async()=>{window.__authCalls.push("update_password");return{error:null};},reauthenticate:async()=>({error:null})},
  from:query,rpc:async(name,args={})=>fetch(base+"__test_rpc",{method:"POST",body:JSON.stringify({name,args})}).then(r=>r.json())
 })};
 window.confirm=()=>true;
}
function serverFixture(){
 const settings={profile:{name:"Synthetic",email:profile.email,role:"client",trainer_linked:false},language:"nl",country:"Nederland",unit_system:"metric",
 display:{date_format:"locale",hour_cycle:"24"},avatar:{visible:true,side:"right",y:.72},revision:0,
 subscription:{plan:"ai",status:"active",starts_at:"2026-09-01",ends_at:"2026-10-01",trial_status:"not_recorded",billing_available:false},account_deletion_available:false};
 const pref={timezone_name:"Europe/Amsterdam",daily_enabled:true,daily_time:"07:30",post_workout_enabled:true,weekly_enabled:true,weekly_day:1,weekly_time:"08:00",revision:0};
 const recovery={safety_revision:2,historical_status:"hard_stop",analysis_blocked:true,automatic_execution_blocked:true,analysis_status:"hard_stop"};
 const contracts=["ai_processing","private_chat","ai_analysis"].map(k=>({consent_kind:k,document_version:k==="ai_processing"?"phase6a-ai-processing-v1":k==="private_chat"?"phase6d-private-chat-v1":"phase6d-analysis-v1",content_text:"Synthetic consent contract for "+k,effective_at:"2026-09-06"}));
 const current=Object.fromEntries(contracts.map(c=>[c.consent_kind,{consent_state:"granted",document_version:c.document_version,document_active:true,consented_at:"2026-09-06"}]));
 const threads=[{id:"30000000-0000-4000-8000-000000000010",created_at:"2026-09-06T08:00:00Z",updated_at:"2026-09-06T08:00:00Z",revision:1,last_message:"Synthetic private reply"}];
 const messages=[{message_role:"user",content_text:"Een gewone vraag",created_at:"2026-09-06T08:00:00Z"},{message_role:"assistant",content_text:"Een gewone reactie",created_at:"2026-09-06T08:00:01Z"}];
 const results=[];const calls=[];
 const status=()=>({preferences:pref,recovery,kinds:Object.fromEntries(["daily","post_workout","weekly"].map(k=>[k,{analysis_allowed:!recovery.analysis_blocked,deny_reason:recovery.analysis_blocked?"safety_hard_stop":"allowed",safety_status:recovery.analysis_status,model_tier:k==="weekly"?"terra":"luna",budget:{fair_use_status:"normal"}}])),latest_completed_workout:{id:"30000000-0000-4000-8000-000000000020"}});
 function rpc(name,args) {
  calls.push({name,args});
  if(name==="fmz_phase6d_get_member_settings")return {...settings,analysis_preferences:pref};
  if(name==="fmz_phase6d_update_member_settings"){
   assert.equal(args.p_expected_revision,settings.revision);
   for(const [key,value] of Object.entries(args.p_patch)){
    if(["language","country"].includes(key))settings[key]=value;
    if(key==="name")settings.profile.name=value;
    if(["date_format","hour_cycle"].includes(key))settings.display[key]=value;
    if(key.startsWith("avatar_"))settings.avatar[key.slice(7)]=value;
   }settings.revision++;return {...settings,analysis_preferences:pref};
  }
  if(name==="fmz_phase6c_get_chat_status")return {chat_write_allowed:current.private_chat.consent_state==="granted",deny_reason:current.private_chat.consent_state==="granted"?"allowed":"ai_consent_required",entitlement_code:"ai",safety_status:"hard_stop",conversation_count:threads.length};
  if(name==="fmz_phase6a_read_consent_contract")return {contracts:contracts.filter(c=>c.consent_kind!=="ai_analysis"),current};
  if(name==="fmz_phase6d_read_analysis_contract")return {contracts:contracts.filter(c=>c.consent_kind==="ai_analysis"),current:{ai_analysis:current.ai_analysis}};
  if(name==="fmz_phase6c_list_threads")return {threads};
  if(name==="fmz_phase6c_read_thread")return {thread:threads.find(t=>t.id===args.p_thread_id),messages};
  if(name==="fmz_phase6c_create_thread"){const thread={id:args.p_thread_id,revision:1,created_at:new Date().toISOString()};threads.unshift(thread);return thread;}
  if(name==="fmz_phase6d_get_status")return status();
  if(name==="fmz_phase6d_list_analyses")return {results};
  if(name==="fmz_phase6d_update_preferences"){assert.equal(args.p_expected_revision,pref.revision);for(const [k,v] of Object.entries(args))if(k.startsWith("p_")&&k.slice(2) in pref)pref[k.slice(2)]=v;pref.revision++;return pref;}
  if(name==="fmz_phase6d_recover_analysis_safety"){assert(args.p_no_previous_symptoms&&args.p_no_current_serious_symptoms&&args.p_understands_support);assert.equal(args.p_expected_safety_revision,recovery.safety_revision);recovery.analysis_blocked=false;recovery.analysis_status="recovered";return recovery;}
  if(name==="fmz_phase6a_record_consent"){current[args.p_consent_kind].consent_state=args.p_action;return {};}
  if(name==="fmz_phase6d_record_analysis_consent"){current.ai_analysis.consent_state=args.p_action;return {};}
  if(name==="fmz_phase6c_delete_thread"){threads.splice(threads.findIndex(t=>t.id===args.p_thread_id),1);return {deleted:true};}
  if(name==="fmz_phase6d_delete_analysis"){results.splice(results.findIndex(t=>t.id===args.p_result_id),1);return {deleted:true};}
  if(name.includes("export"))return {synthetic:true};
  if(name==="fmz_phase5_get_progress_dashboard")return {access:"free",unit_system:"metric",today:"2026-09-06",weights:[],measurements:[],strength:[],consistency:{},recovery_context:{},nutrition_context:{}};
  return {};
 }
 return {settings,pref,recovery,calls,messages,rpc};
}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
 try {
 for(const [width,height] of [[320,700],[390,844],[820,1180],[1440,900]]){
  const server=serverFixture(),context=await browser.newContext({viewport:{width,height},hasTouch:true});
  await context.addInitScript("const base="+JSON.stringify(base)+";("+mockSetup.toString()+")("+JSON.stringify(profile)+");");
  await context.route("**/*",async route=>{
   const url=new URL(route.request().url());
   if(url.pathname.endsWith("/__test_rpc")){
    const {name,args}=JSON.parse(route.request().postData());return route.fulfill({json:{data:server.rpc(name,args),error:null}});
   }
   if(url.pathname.includes("/functions/v1/youri-ai")){
    const args=JSON.parse(route.request().postData());server.calls.push({name:"edge",args});
    assert(!["model","provider","user_id","entitlement"].some(k=>k in args));
    const recovery=args.content==="Ik heb geen klachten meer";
    if(args.content?.includes("nog pijn op de borst")){server.recovery.safety_revision++;server.recovery.analysis_blocked=true;server.recovery.analysis_status="hard_stop";}
    if(args.content)server.messages.push({message_role:"user",content_text:args.content,created_at:new Date().toISOString()});
    return route.fulfill({json:{recovery_requested:recovery,recovery_reason:"symptoms_resolved",external_ai_calls:0}});
   }
   if(!route.request().url().startsWith(base))return route.fulfill({body:"",contentType:"application/javascript"});
   const relative=decodeURIComponent(url.pathname.slice(new URL(base).pathname.length))||"index.html";
   assert(!relative.includes(".."));const file=path.join(root,relative);
   if(!fs.existsSync(file))return route.fulfill({status:404,body:"not found"});
   let body=fs.readFileSync(file);
   if(relative==="app.bundle.js")body=Buffer.from(body.toString().replace("\ninit();","\n"+probe+"\ninit();"));
   return route.fulfill({body,contentType:relative.endsWith(".js")?"application/javascript":relative.endsWith(".css")?"text/css":relative.endsWith(".html")?"text/html":relative.endsWith(".svg")?"image/svg+xml":relative.endsWith(".webp")?"image/webp":"application/octet-stream"});
  });
  const page=await context.newPage(),errors=[];
  page.on("pageerror",e=>errors.push(e.message));page.on("console",m=>{if(m.type()==="error")errors.push(m.text());});
  await page.goto(base);await page.waitForFunction(()=>window.__hotfix);
  check(width+" auth hides avatar",!await page.locator("#fmz-avatar").isVisible());
  await page.evaluate(()=>__hotfix.enter());await page.waitForSelector("#fmz-avatar:visible");
  check(width+" AI removed from bottom nav",await page.locator('#nav [data-view="ai-coach"]').count()===0);
  check(width+" top gear and language visible",await page.locator('[data-fmz-settings="account"]').isVisible()&&await page.locator("[data-fmz-language-toggle]").isVisible());
  const original=await page.evaluate(()=>__hotfix.current());
  await page.click("#fmz-avatar");await page.waitForSelector("#fmz-youri-chat[open]");
  check(width+" approved avatar loaded",await page.evaluate(()=>[...document.querySelectorAll(".p6c-avatar img")].every(i=>i.complete&&i.naturalWidth===256)));
  await page.waitForSelector("#p6cMessage");
  await page.fill("#p6cMessage","Ik heb geen klachten meer");await page.click(".p6c-send");
  await page.waitForSelector("#fmz-safety-recovery[open]");
  check(width+" recovery starts without silently clearing block",server.recovery.analysis_blocked);
  await page.locator('#fmz-safety-recovery [name="confirm0"]').check();
  await page.locator('#fmz-safety-recovery [name="confirm1"]').check();
  check(width+" all confirmations required",await page.locator('#fmz-safety-recovery [type="submit"]').isDisabled());
  await page.locator('#fmz-safety-recovery [name="confirm2"]').check();await page.click('#fmz-safety-recovery [type="submit"]');
  await page.waitForSelector("#fmz-safety-recovery",{state:"detached"});
  check(width+" recovery lifts only analysis block",!server.recovery.analysis_blocked&&server.recovery.automatic_execution_blocked);
  await page.click('#fmz-youri-chat [data-fmz-close]');await page.waitForSelector("#fmz-youri-chat",{state:"detached"});
  check(width+" chat returns exact previous screen",await page.evaluate(()=>__hotfix.current())===original);
  const before=await page.locator("#fmz-avatar").boundingBox();
  await page.mouse.move(before.x+30,before.y+30);await page.mouse.down();await page.mouse.move(30,180,{steps:8});await page.mouse.up();
  await page.waitForFunction(()=>window.FMZ_OWNER_SETTINGS.snapshot().avatar.side==="left");
  check(width+" drag does not open chat",await page.locator("#fmz-youri-chat").count()===0);
  check(width+" position saved per user",server.settings.avatar.side==="left");
  const touch=await context.newCDPSession(page),touchBox=await page.locator("#fmz-avatar").boundingBox();
  await touch.send("Input.dispatchTouchEvent",{type:"touchStart",touchPoints:[{x:touchBox.x+30,y:touchBox.y+30}]});
  await touch.send("Input.dispatchTouchEvent",{type:"touchMove",touchPoints:[{x:1,y:1}]});
  await touch.send("Input.dispatchTouchEvent",{type:"touchEnd",touchPoints:[]});
  await page.waitForFunction(()=>window.FMZ_OWNER_SETTINGS.snapshot().avatar.y===0);
  check(width+" real touch drag stays bounded without opening",(await page.locator("#fmz-avatar").boundingBox()).y>=76&&await page.locator("#fmz-youri-chat").count()===0);
  await page.locator("#fmz-avatar").focus();await page.keyboard.press("ArrowRight");
  await page.waitForFunction(()=>window.FMZ_OWNER_SETTINGS.snapshot().avatar.side==="right");
  await page.keyboard.press("ArrowLeft");await page.keyboard.press("ArrowDown");
  await page.waitForFunction(()=>window.FMZ_OWNER_SETTINGS.snapshot().avatar.side==="left"&&window.FMZ_OWNER_SETTINGS.snapshot().avatar.y>0);
  check(width+" keyboard placement saved",server.settings.avatar.side==="left"&&server.settings.avatar.y>0);
  await page.evaluate(()=>__hotfix.view("training"));check(width+" avatar across navigation",await page.locator("#fmz-avatar").isVisible());
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());
  await page.waitForFunction(()=>window.FMZ_OWNER_SETTINGS.snapshot()?.avatar.side==="left");
  check(width+" position survives refresh",server.settings.avatar.side==="left");
  await page.click('[data-fmz-settings="account"]');await page.waitForSelector("#fmz-settings[open]");
  for(const key of ["account","privacy","time","language","ai","subscription","legal"]){await page.click('[data-fmz-section="'+key+'"]');check(width+" settings "+key+" reachable",await page.locator(".fmz-settings-content h2").count()===1);}
  check(width+" legal destinations reachable",await page.locator(".fmz-disclosure summary").count()>=2);
  await page.locator(".fmz-disclosure summary").first().click();
  check(width+" legal draft accurate",(await page.textContent("#fmz-settings")).includes("niet juridisch goedgekeurd"));
  await page.click('[data-fmz-section="ai"]');
  check(width+" avatar hidden during settings",!await page.locator("#fmz-avatar").isVisible());
  await page.locator('[data-fmz-consent-block="ai_processing"] summary').click();
  await page.click('[data-fmz-consent="ai_processing"][data-action="withdrawn"]');
  await page.waitForFunction(()=>window.FMZ_PHASE6C_PRIVATE_CHAT.snapshot().consent.current.ai_processing.consent_state==="withdrawn");
  check(width+" general consent withdrawal leaves chat and analyses separate",await page.evaluate(()=>window.FMZ_PHASE6C_PRIVATE_CHAT.snapshot().status.chat_write_allowed&&window.FMZ_PHASE6C_PRIVATE_CHAT.snapshot().analysisConsent.current.ai_analysis.consent_state==="granted"));
  await page.fill('[name="daily_time"]',"10:40");await page.selectOption('[name="weekly_day"]',"5");await page.fill('[name="weekly_time"]',"19:20");await page.selectOption('[name="timezone_name"]',"Europe/London");
  await page.click('[data-fmz-form="schedule"] [type="submit"]');await page.waitForFunction(()=>document.querySelector('[name="daily_time"]')?.value==="10:40");
  check(width+" schedule saved all fields",server.pref.daily_time==="10:40"&&server.pref.weekly_day===5&&server.pref.weekly_time==="19:20"&&server.pref.timezone_name==="Europe/London");
  await page.click('[data-fmz-section="time"]');
  check(width+" AI and time use same source",await page.inputValue('[name="daily_time"]')==="10:40"&&await page.inputValue('[name="weekly_day"]')==="5");
  await page.selectOption('[name="date_format"]',"iso");await page.selectOption('[name="hour_cycle"]',"12");await page.click('[data-fmz-form="display"] [type="submit"]');
  await page.click('[data-fmz-section="ai"]');await page.click("[data-fmz-avatar-reset]");
  await page.waitForFunction(()=>window.FMZ_OWNER_SETTINGS.snapshot().avatar.side==="right");
  await page.uncheck("[data-fmz-avatar-visible]");await page.click('#fmz-settings [data-fmz-close]');
  check(width+" hide avatar persists",!await page.locator("#fmz-avatar").isVisible());
  await page.click('[data-fmz-settings="account"]');await page.click('[data-fmz-section="ai"]');await page.check("[data-fmz-avatar-visible]");
  await page.click('#fmz-settings [data-fmz-close]');await page.waitForSelector("#fmz-avatar:visible");
  check(width+" avatar restored",await page.locator("#fmz-avatar").isVisible());
  for(const language of ["en","de","nl"]){
   await page.click("[data-fmz-language-toggle]");await page.click('[data-fmz-language="'+language+'"]');
   await page.waitForFunction(language=>document.documentElement.lang===language,language);
   check(width+" quick language "+language+" saved",server.settings.language===language);
  }
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());
  await page.click('[data-fmz-settings="account"]');await page.click('[data-fmz-section="language"]');
  check(width+" language source agrees after refresh",await page.inputValue('#fmz-settings [name="language"]')===server.settings.language);
  await page.click('[data-fmz-section="ai"]');
  check(width+" schedule survives reload",await page.inputValue('[name="daily_time"]')==="10:40");
  await page.screenshot({path:path.join(root,"supabase/.temp/owner-hotfix-settings-"+width+".png"),fullPage:true});
  check(width+" settings no overflow",await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.getElementById("fmz-settings").scrollWidth<=document.getElementById("fmz-settings").clientWidth+1));
  await page.click('#fmz-settings [data-fmz-close]');
  await page.evaluate(()=>{document.body.classList.add("phase4-s3-dialog-open");});
  await page.waitForFunction(()=>document.getElementById("fmz-avatar").hidden);
  check(width+" scanner hides avatar",!await page.locator("#fmz-avatar").isVisible());
  await page.evaluate(()=>document.body.classList.remove("phase4-s3-dialog-open"));
  await page.click("#fmz-avatar");await page.waitForSelector("#p6cMessage");
  check(width+" chat has no settings forms",await page.locator('#fmz-youri-chat [data-fmz-form],#fmz-youri-chat [data-p6d-preferences-form]').count()===0);
  await page.fill("#p6cMessage","Het gaat goed, maar ik heb nog pijn op de borst");await page.click(".p6c-send");
  await page.waitForFunction(()=>window.FMZ_PHASE6C_PRIVATE_CHAT.snapshot().analysisStatus?.recovery?.analysis_blocked);
  check(width+" contradictory message keeps block and no recovery",server.recovery.analysis_blocked&&await page.locator("#fmz-safety-recovery").count()===0);
  await page.click('[data-p6c-tab="analyses"]');await page.screenshot({path:path.join(root,"supabase/.temp/owner-hotfix-analyses-"+width+".png"),fullPage:true});
  check(width+" analyses no horizontal overflow",await page.evaluate(()=>document.getElementById("ai-coach").scrollWidth<=document.getElementById("ai-coach").clientWidth+1));
  await page.click('#fmz-youri-chat [data-fmz-close]');
  await page.evaluate(()=>location.hash="ai-coach");await page.waitForSelector("#fmz-youri-chat[open]");
  check(width+" deep link route works",await page.locator("#fmz-youri-chat").isVisible());
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());
  await page.waitForSelector("#fmz-youri-chat[open]");
  check(width+" deep link survives refresh and late session hydration",await page.locator("#fmz-youri-chat").isVisible());
  await page.click('#fmz-youri-chat [data-fmz-settings="ai"]');await page.waitForSelector("#fmz-settings[open]");
  await page.click('#fmz-settings [data-fmz-close]');
  check(width+" nested settings returns focus to chat",await page.evaluate(()=>document.activeElement.closest("#fmz-youri-chat")!==null));
  await page.click('#fmz-youri-chat [data-fmz-close]');
  await page.evaluate(()=>window.FMZ_OWNER_SETTINGS.hydrate(true));
  check(width+" closing deep link does not reopen during hydration",await page.locator("#fmz-youri-chat").count()===0);
  await page.click('[data-fmz-settings="account"]');
  await page.locator('.fmz-disclosure summary').click();
  for(const [name,value] of [["current_password","invalid-synthetic"],["password","synthetic-new-password"],["repeat","synthetic-new-password"]])await page.fill('[data-fmz-form="password"] [name="'+name+'"]',value);
  await page.click('[data-fmz-form="password"] [type="submit"]');
  await page.waitForFunction(()=>document.querySelector(".fmz-feedback.error")?.textContent.includes("Wachtwoord niet gewijzigd"));
  check(width+" invalid current password cannot update password",await page.evaluate(()=>!window.__authCalls.includes("update_password")));
  check(width+" password error releases busy controls",!await page.locator('[data-fmz-logout]').isDisabled());
  await page.click("[data-fmz-logout]");
  await page.waitForFunction(()=>document.getElementById("fmz-avatar").hidden);
  check(width+" logout clears private surfaces",await page.locator("#fmz-settings,#fmz-youri-chat").count()===0);
  await page.evaluate(()=>{location.hash="";});await page.evaluate(()=>__hotfix.enter());
  await page.click('[data-fmz-settings="account"]');await page.locator('.fmz-disclosure summary').click();
  for(const [name,value] of [["current_password","valid-synthetic-current"],["password","synthetic-new-password"],["repeat","synthetic-new-password"]])await page.fill('[data-fmz-form="password"] [name="'+name+'"]',value);
  await page.click('[data-fmz-form="password"] [type="submit"]');
  await page.waitForFunction(()=>window.__authCalls.includes("member_signout_global"));
  check(width+" password verifies separately and revokes sessions",await page.evaluate(()=>window.__authCalls.slice(-4).join(",")==="verify_current_password,isolated_signout_local,update_password,member_signout_global"));
  check(width+" password change clears member surfaces",await page.locator("#fmz-settings,#fmz-youri-chat").count()===0);
  check(width+" no page or console errors",errors.length===0);
  await context.close();
 }
 } finally {await browser.close();}
 console.log(JSON.stringify({overall_pass:true,pass_count:checks.length,checks},null,2));
})().catch(error=>{console.error(error.stack);console.log(JSON.stringify(checks));process.exitCode=1;});
