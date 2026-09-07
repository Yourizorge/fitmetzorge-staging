const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const {chromium}=require("playwright");
const {root,base,profile,probe,mockSetup,serverFixture}=require("./phase6d-owner-browser-check.cjs");
const live=process.env.FMZ_THEME_LIVE==="1",inspect=process.env.FMZ_THEME_INSPECT==="1";
const checks=[],layouts=[],cache=new Map();
const check=(name,pass)=>{checks.push({name,pass:!!pass});assert(pass,name);};
const nextFrame=page=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
async function measure(page,label,scope){
 await nextFrame(page);
 const data=await page.evaluate(selector=>{
  const parent=document.querySelector(selector);if(!parent)throw new Error("missing surface "+selector);
  const rgb=value=>{const n=value.match(/[\d.]+/g)?.map(Number);return n?.length>=3?[n[0],n[1],n[2],n[3]??1]:[0,0,0,0];};
  const mix=(front,back)=>[0,1,2].map(i=>front[i]*front[3]+back[i]*(1-front[3])).concat(1);
  const luminance=c=>c.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
  const issues=[],surfaces=[],overwide=[];
  for(const el of [parent,...parent.querySelectorAll("*")]){
   const s=getComputedStyle(el),r=el.getBoundingClientRect();
   if(!el.getClientRects().length||s.visibility!=="visible"||Number(s.opacity)===0||r.width<1||r.height<1)continue;
   if(r.left<-.5||r.right>innerWidth+.5)overwide.push({tag:el.tagName,cls:typeof el.className==="string"?el.className:"svg",left:r.left,right:r.right});
   const text=el.matches('input:not([type="radio"]):not([type="checkbox"]),textarea')?(el.value||el.placeholder):[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent.trim()).join(" ").trim();
   if(!text||el.matches("script,style,option")||el.closest("[disabled]"))continue;
   let backgrounds=[[255,255,255,1]],ancestors=[],node=el,gradient=false;
   while(node){ancestors.unshift(node);node=node.parentElement;}
   for(const ancestor of ancestors){
    const a=getComputedStyle(ancestor);backgrounds=backgrounds.map(bg=>mix(rgb(a.backgroundColor),bg));
    if(a.backgroundImage!=="none"){
     gradient=true;
     const stops=[...a.backgroundImage.matchAll(/rgba?\([^)]+\)/g)].map(m=>rgb(m[0]));
     if(stops.length)backgrounds=backgrounds.flatMap(bg=>stops.map(stop=>mix(stop,bg)));
    }
    backgrounds=[...new Map(backgrounds.map(bg=>[bg.join(),bg])).values()].slice(0,64);
   }
   const contrasts=backgrounds.map(bg=>{const a=luminance(mix(rgb(s.color),bg)),b=luminance(bg);return {bg,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};}).sort((a,b)=>a.ratio-b.ratio);
   const {bg,ratio}=contrasts[0];
   const large=parseFloat(s.fontSize)>=24||(parseFloat(s.fontSize)>=18.66&&Number(s.fontWeight)>=700),minimum=large?3:4.5;
   const item={text:text.slice(0,60),tag:el.tagName,cls:el.className,color:s.color,bg:bg.slice(0,3),ratio,minimum,gradient};
   surfaces.push(item);
   if(ratio<minimum)issues.push(item);
  }
  return {theme:document.documentElement.dataset.theme,mode:document.documentElement.dataset.themeMode,width:innerWidth,
   scroll:document.documentElement.scrollWidth,bodyClass:document.body.className,overwide,issues,surfaces:surfaces.length,
   rect:{width:parent.getBoundingClientRect().width},meta:document.querySelector('meta[name="theme-color"]').content};
 },scope);
 layouts.push({label,...data});
 check(label+" root bounded",data.scroll<=data.width);
 check(label+" surface exists",data.rect.width>0);
 if(!inspect)check(label+" text contrast (solid-color composite)",data.issues.length===0);
 return data;
}
async function setup(browser,width,height,bootstrap=null){
 const server=serverFixture();server.recovery.analysis_blocked=false;
 let active=server,failNext=false,delay=0;
 const context=await browser.newContext({viewport:{width,height},hasTouch:width<1000,colorScheme:"light",reducedMotion:"reduce"});
 await context.addInitScript("const base="+JSON.stringify(base)+";("+mockSetup.toString()+")("+JSON.stringify(profile)+");");
 if(bootstrap){
  server.settings.display.theme_mode=bootstrap;
  await context.addInitScript(({profile,mode})=>{
   localStorage.setItem('sb-mokxyyullfhkfalopbzd-auth-token',JSON.stringify({user:{id:profile.id},expires_at:Date.now()/1000+3600}));
   localStorage.setItem('fmz.theme.v1:'+profile.id,JSON.stringify({user:profile.id,mode}));
   window.__memberSession=true;
   const frame=()=>{if(!document.body)return requestAnimationFrame(frame);window.__firstThemeFrame={theme:document.documentElement.dataset.theme,bg:getComputedStyle(document.documentElement).backgroundColor,body:getComputedStyle(document.body).backgroundColor};};
   requestAnimationFrame(frame);
  },{profile,mode:bootstrap});
 }
 const errors=[],actual=[];
 await context.route("**/*",async route=>{
  const url=new URL(route.request().url());
  if(url.pathname.endsWith("/__test_rpc")){
   const {name,args}=JSON.parse(route.request().postData());
   if(name==="fmz_phase6d_update_member_settings"&&failNext){failNext=false;return route.fulfill({json:{data:null,error:{message:"synthetic_write_failure"}}});}
   const data=active.rpc(name,args);
   if(delay&&name==="fmz_phase6d_update_member_settings")await new Promise(r=>setTimeout(r,delay));
   return route.fulfill({json:{data,error:null}});
  }
  if(url.hostname.endsWith(".supabase.co")){actual.push(url.pathname);return route.abort();}
  if(!route.request().url().startsWith(base))return route.fulfill({body:"",contentType:"application/javascript"});
  const file=decodeURIComponent(url.pathname.slice(new URL(base).pathname.length))||"index.html";assert(!file.includes(".."));
  if(bootstrap&&file==="app.js")await new Promise(resolve=>setTimeout(resolve,800));
  let body;
  if(live){if(!cache.has(file)){const response=await fetch(base+file+"?theme-test="+Date.now());assert.equal(response.status,200,file);cache.set(file,Buffer.from(await response.arrayBuffer()));}body=cache.get(file);}
  else body=fs.readFileSync(path.join(root,file));
  if(file==="app.bundle.js")body=Buffer.from(body.toString().replace("\ninit();","\n"+probe+"\ninit();"));
  return route.fulfill({body,contentType:file.endsWith(".js")?"application/javascript":file.endsWith(".css")?"text/css":file.endsWith(".html")?"text/html":file.endsWith(".svg")?"image/svg+xml":file.endsWith(".webp")?"image/webp":"application/octet-stream"});
 });
 const page=await context.newPage();
 page.on("pageerror",e=>errors.push(e.message));
 page.on("console",m=>{if(m.type()==="error")errors.push(m.text());});
 return {context,page,server,errors,actual,swap:s=>{active=s;},fail:()=>{failNext=true;},delay:n=>{delay=n;}};
}
async function choose(page,value){
 await page.locator('#fmz-settings [name="theme_mode"][value="'+value+'"]').check();
 await page.waitForFunction(value=>FMZ_OWNER_SETTINGS.snapshot()?.display.theme_mode===value&&document.querySelector('#fmz-settings [name="theme_mode"]:checked')?.disabled===false,value);
}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
 try{
 for(const [width,height] of [[320,700],[390,844],[820,1180],[1440,900]]){
  const x=await setup(browser,width,height),{page,context,server}=x;
  await page.goto(base);await page.waitForFunction(()=>window.__hotfix).catch(e=>{throw new Error(e.message+JSON.stringify({errors:x.errors,actual:x.actual}));});
  check(width+" public light automatic",await page.evaluate(()=>FMZ_THEME.snapshot().mode==="system"&&document.documentElement.dataset.theme==="light"));
  for(const system of ["dark","light"]){
   await page.emulateMedia({colorScheme:system});await nextFrame(page);
   for(const mode of ["register","login","forgot","login"]){
    await page.locator('[data-auth-mode="'+mode+'"]').filter({visible:true}).first().click();
    await measure(page,width+" auth "+mode+" "+system,"#loginScreen");
   }
  }
  await page.evaluate(()=>__hotfix.enter());
  check(width+" new user defaults automatic",await page.evaluate(()=>FMZ_THEME.snapshot().mode==="system"));
  await page.click('[data-fmz-settings="home"]');
  check(width+" appearance row and subtitle",await page.locator('[data-fmz-section="appearance"]').textContent()==="WeergaveAutomatisch");
  await page.click('[data-fmz-section="appearance"]');
  check(width+" three vertical radio options",await page.locator('[name="theme_mode"]').count()===3);
  await choose(page,"dark");await page.emulateMedia({colorScheme:"light"});await nextFrame(page);
  check(width+" dark ignores light system",await page.evaluate(()=>document.documentElement.dataset.theme==="dark"));
  await choose(page,"light");await page.emulateMedia({colorScheme:"dark"});await nextFrame(page);
  check(width+" light ignores dark system",await page.evaluate(()=>document.documentElement.dataset.theme==="light"));
  await choose(page,"system");
  check(width+" system follows dark immediately",await page.evaluate(()=>document.documentElement.dataset.theme==="dark"));
  await page.emulateMedia({colorScheme:"light"});await nextFrame(page);
  check(width+" open app system switch immediate",await page.evaluate(()=>document.documentElement.dataset.theme==="light"));
  const oldGeometry=await page.locator(".fmz-theme-options").boundingBox();
  await choose(page,"dark");await nextFrame(page);
  check(width+" no theme layout shift",JSON.stringify(oldGeometry)===JSON.stringify(await page.locator(".fmz-theme-options").boundingBox()));
  check(width+" server persisted explicit mode",server.settings.display.theme_mode==="dark");
  await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());
  check(width+" refresh restores server choice",await page.evaluate(()=>FMZ_THEME.snapshot().mode==="dark"));
  await page.evaluate(()=>__hotfix.logout());await nextFrame(page);
  check(width+" logout returns system light",await page.evaluate(()=>FMZ_THEME.snapshot().mode==="system"&&document.documentElement.dataset.theme==="light"));
  await page.evaluate(()=>__hotfix.enter());
  check(width+" login restores own dark",await page.evaluate(()=>FMZ_THEME.snapshot().mode==="dark"));
  const other=serverFixture();other.recovery.analysis_blocked=false;x.swap(other);
  await page.evaluate(()=>{__hotfix.logout();window.__mockProfile={...window.__mockProfile,id:"30000000-0000-4000-8000-000000000002",email:"other@example.invalid"};return __hotfix.enter();});
  check(width+" different user independent system",await page.evaluate(()=>FMZ_THEME.snapshot().mode==="system"));
  await page.click('[data-fmz-settings="home"]');await page.click('[data-fmz-section="appearance"]');await choose(page,"light");
  check(width+" other write leaves first preference unchanged",server.settings.display.theme_mode==="dark");
  x.swap(server);await page.evaluate(p=>{__hotfix.logout();window.__mockProfile=p;return __hotfix.enter();},profile);
  check(width+" first user preference still dark",await page.evaluate(()=>FMZ_THEME.snapshot().mode==="dark"));
  await page.click('[data-fmz-settings="home"]');await page.click('[data-fmz-section="appearance"]');x.fail();
  await page.locator('[name="theme_mode"][value="light"]').focus();await page.keyboard.press("Space");
  try {await page.waitForSelector(".fmz-feedback.error",{timeout:5000});}
  catch(e){throw new Error(JSON.stringify({failureState:await page.evaluate(()=>({theme:FMZ_THEME.snapshot(),text:document.querySelector('#fmz-settings')?.textContent,feedback:[...document.querySelectorAll('.fmz-feedback')].map(n=>({text:n.textContent,cls:n.className,style:getComputedStyle(n).display})),radios:[...document.querySelectorAll('[name="theme_mode"]')].map(n=>({value:n.value,checked:n.checked,disabled:n.disabled}))})),errors:x.errors,calls:server.calls.slice(-5)}));}
  check(width+" failed write rolls back preview",await page.evaluate(()=>FMZ_THEME.snapshot().mode==="dark")&&server.settings.display.theme_mode==="dark");
  for(const language of ["nl","en","de"]){
   server.settings.language=language;await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));
   const labels=await page.locator(".fmz-theme-options label span").allTextContents();
   check(width+" translated options "+language,JSON.stringify(labels)===JSON.stringify({nl:["Automatisch","Licht","Donker"],en:["System / Automatic","Light","Dark"],de:["Automatisch / System","Hell","Dunkel"]}[language]));
  }
  server.settings.language="nl";
  for(const mode of ["light","dark"]){
   server.settings.display.theme_mode=mode;await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));
   await page.evaluate(()=>FMZ_OWNER_SETTINGS.open("appearance"));
   await page.locator('.fmz-theme-options label').first().hover();
   await measure(page,width+" appearance "+mode,"#fmz-settings");
   check(width+" appearance descendants bounded "+mode,layouts.at(-1).overwide.length===0);
   // Let the preceding language hydration finish its existing legacy save queue.
   await page.waitForTimeout(1800);
   const saveStart=server.calls.length;x.delay(300);
   await page.locator('[name="theme_mode"][value="'+(mode==="light"?"dark":"light")+'"]').focus();await page.keyboard.press("Space");
   check(width+" pending choice disabled "+mode,await page.locator('[name="theme_mode"]:disabled').count()===3);
   await page.waitForSelector('[name="theme_mode"]:enabled');x.delay(0);await choose(page,mode);
   await measure(page,width+" saved success "+mode,"#fmz-settings");
   const writes=server.calls.slice(saveStart).filter(c=>/(upsert|update|save|insert|delete|record|recover|edge)/.test(c.name));
   check(width+" theme changes write only own settings "+mode+" "+JSON.stringify(writes.map(c=>c.name)),writes.every(c=>c.name==="fmz_phase6d_update_member_settings"));
   x.fail();await page.locator('[name="theme_mode"][value="'+(mode==="light"?"dark":"light")+'"]').focus();await page.keyboard.press("Space");
   await page.waitForSelector('.fmz-feedback.error');
   await measure(page,width+" failed save error "+mode,"#fmz-settings");
   await page.screenshot({path:path.join(root,"supabase/.temp/theme-"+(live?"live":"local")+"-"+width+"-"+mode+"-settings.png")});
   for(const section of ["home","account","privacy","language","ai","subscription","terms","privacyDoc","logout","schedule","consent","avatar","chatData","analysisData"]){
    await page.evaluate(section=>FMZ_OWNER_SETTINGS.open(section),section);
    await measure(page,width+" settings "+section+" "+mode,"#fmz-settings");
   }
   await page.click('#fmz-settings [data-fmz-close]');
   await measure(page,width+" topbar "+mode,".topbar");
   await measure(page,width+" navigation "+mode,".sidebar");
   for(const view of ["client-home","training","nutrition","trackers","progress"]){
    await page.evaluate(view=>__hotfix.view(view),view);
    await measure(page,width+" "+view+" "+mode,"#"+view);
   }
   await page.evaluate(()=>__hotfix.view("trackers"));
   for(const detail of ["sleep","wellbeing"]){
    await page.locator('#trackers [data-member-open-detail="'+detail+'"]').first().click();
    await measure(page,width+" tracker detail "+detail+" "+mode,"#memberUxDetailPortal .member-ux-sheet");
    await page.locator('#memberUxDetailPortal .member-ux-close').click();
   }
   await page.evaluate(()=>__hotfix.view("client-home"));
   await page.evaluate(()=>{
    const samples=document.createElement('div');samples.id='theme-state-samples';samples.className='member-ux-card';
    samples.innerHTML='<span class="status ok">Success</span><span class="status warn">Warning</span><span class="status bad">Error</span><button class="primary-btn" disabled>Disabled</button>';
    document.querySelector('#client-home').append(samples);
   });
   await measure(page,width+" semantic state samples "+mode,"#theme-state-samples");
   await page.evaluate(()=>document.querySelector('#theme-state-samples').remove());
   await page.locator('#client-home [data-member-open-detail="recovery"]').click();
   await measure(page,width+" check-in "+mode,"#memberUxDetailPortal .member-ux-sheet");
   await page.locator('#memberUxDetailPortal .member-ux-close').click();
   await page.click('[data-fmz-language-toggle]');
   await measure(page,width+" language menu "+mode,".fmz-language-menu");
   await page.keyboard.press("Escape");
   server.results.length=0;server.notes.length=0;
   const id="30000000-0000-4000-8000-00000000003"+(mode==="light"?"1":"2"),created=new Date().toISOString();
   server.results.push({id,analysis_kind:"post_workout",status:"partial",created_at:created,completed_at:created,revision:1,model_tier:"luna",quality:{level:"partial",missing_sources:["nutrition"]},summary_text:"Synthetische trainingsreflectie",result_payload:{mock:true,actions:[],observations:[{text:"Opgeslagen metingen."}],suggestions:[{text:"Een reflectie op je training."}],comparison:{available:true,reason:"same_exercise_set",current:{id:"current-workout",completed_at:created,elapsed_seconds:1200},previous:{id:"previous-workout",completed_at:created,elapsed_seconds:1800},exercises:[{label:"goblet-squat",current:{sets:2,reps:20,max_weight_kg:35,volume_kg:700,rpe:8,rir:1},previous:{sets:2,reps:20,max_weight_kg:30,volume_kg:600},volume_change:"higher"}]}}});
   server.notes.push({analysis_id:id,state:"new",analysis_kind:"post_workout",created_at:created});
   await page.evaluate(()=>FMZ_ANALYSIS_INBOX.hydrate({force:true}));
   await page.waitForSelector(".fmz-analysis-toast");
   await measure(page,width+" notification "+mode,".fmz-analysis-toast");
   await measure(page,width+" avatar badge "+mode,"#fmz-avatar");
   await page.click('[data-fmz-analysis-later]');
   await measure(page,width+" analysis cards "+mode,"#fmz-analysis-inbox");
   await page.screenshot({path:path.join(root,"supabase/.temp/theme-"+(live?"live":"local")+"-"+width+"-"+mode+"-dashboard.png")});
   await page.click('#fmz-analysis-inbox [data-fmz-analysis-open="'+id+'"]');
   await page.waitForSelector("#fmz-analysis-detail table");
   await measure(page,width+" analysis detail "+mode,"#fmz-analysis-detail");
   check(width+" analysis detail bounded "+mode,await page.locator('#fmz-analysis-detail').evaluate(n=>n.scrollWidth<=n.clientWidth+1));
   await page.screenshot({path:path.join(root,"supabase/.temp/theme-"+(live?"live":"local")+"-"+width+"-"+mode+"-analysis.png")});
   await page.click('[data-fmz-detail-close]');
   await page.click("#fmz-avatar");await page.waitForSelector("#p6cMessage");
   await measure(page,width+" chat "+mode,"#fmz-youri-chat");
   await page.locator("#p6cMessage").focus();
   check(width+" composer focus visible "+mode,(await page.locator("#p6cMessage").evaluate(n=>getComputedStyle(n).outlineStyle))!=="none");
   await page.screenshot({path:path.join(root,"supabase/.temp/theme-"+(live?"live":"local")+"-"+width+"-"+mode+"-chat.png")});
   await page.click('#fmz-youri-chat [data-fmz-close]');
   server.recovery.analysis_blocked=true;await page.evaluate(()=>__hotfix.safety());
   await page.evaluate(()=>FMZ_OWNER_SETTINGS.openRecovery("reassessment"));
   await measure(page,width+" recovery "+mode,"#fmz-safety-recovery");
   check(width+" reduced motion dialog "+mode,await page.locator('#fmz-safety-recovery').evaluate(n=>getComputedStyle(n.querySelector('button')).transitionDuration==="0s"));
   await page.click('#fmz-safety-recovery [data-fmz-close]');server.recovery.analysis_blocked=false;
  }
  check(width+" no browser errors "+JSON.stringify(x.errors),x.errors.length===0);
  check(width+" no live member or provider calls",x.actual.length===0);
  await context.close();
  for(const mode of ["dark","light"]){
   const start=await setup(browser,width,height,mode);
   await start.page.emulateMedia({colorScheme:mode==="dark"?"light":"dark"});
   await start.page.goto(base);await start.page.waitForFunction(()=>window.__firstThemeFrame);
   const first=await start.page.evaluate(()=>window.__firstThemeFrame),expected=mode==="dark"?"rgb(7, 11, 18)":"rgb(247, 248, 250)";
   check(width+" cached "+mode+" first visible frame has no opposite flash",first.theme===mode&&first.bg===expected&&first.body===expected);
   await start.context.close();
  }
 }
 }finally{await browser.close();}
 const result={mode:live?"live-assets":"local",overall_pass:checks.every(c=>c.pass),pass_count:checks.length,checks,layouts,no_test_css_injected:true,actual_member_provider_requests:0};
 fs.writeFileSync(path.join(root,"supabase/.temp/theme-"+(live?"live":"local")+"-result.json"),JSON.stringify(result,null,2));
 console.log(JSON.stringify({overall_pass:result.overall_pass,pass_count:result.pass_count,layouts:layouts.length,contrast_issues:layouts.reduce((sum,x)=>sum+x.issues.length,0)}));
})().catch(e=>{fs.writeFileSync(path.join(root,"supabase/.temp/theme-failed.json"),JSON.stringify({checks,layouts,error:e.stack},null,2));console.error(e.stack);process.exitCode=1;});
