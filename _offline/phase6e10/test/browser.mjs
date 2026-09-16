import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import assert from "node:assert/strict";
import {createRequire} from "node:module";
import {broker,makeApi,root,BASE} from "./live.mjs";
import * as followup from "../ops/followup-audit.mjs";
const require=createRequire(import.meta.url);
const {chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const published=process.argv.includes("--published"),label=published?"published":"local-ui";
if(fs.existsSync(path.join(root,"supabase/.temp/phase6e10-owner-window.json")))throw Error("owner_window_receipt_requires_explicit_owner_followup");
const out=path.join(root,"supabase/.temp/phase6e10-browser-"+label);fs.mkdirSync(out,{recursive:true});
const report={scope:label,physical_phone:false,password_login_tested:false,standard_auth_sessions:true,checks:[],layouts:[],screenshots:[],errors:[]};
const b=broker();let api,browser,server,windowId;
const check=async(name,value)=>{await followup.checkpoint(name,value);assert(value,name);report.checks.push(name);console.log("PASS",name);};
try{
 await followup.begin('browser-'+label);
 api=await makeApi(b);
 if(!published){
  server=http.createServer((req,res)=>{
   const rel=decodeURIComponent(new URL(req.url,"http://local").pathname).replace(/^\//,"");
   if(!/^coach-source-demo\/(index\.html|demo\.css|app\.mjs|strings\.mjs)$/.test(rel)&&!["assets/fit-met-zorge-logo-cropped.png","assets/vendor/lucide-rotate-cw.svg"].includes(rel)){res.writeHead(404);res.end();return;}
   res.writeHead(200,{"Content-Type":rel.endsWith(".mjs")?"text/javascript":rel.endsWith(".css")?"text/css":rel.endsWith(".png")?"image/png":rel.endsWith(".svg")?"image/svg+xml":"text/html"});
   res.end(fs.readFileSync(path.join(root,rel)));
  });
  await new Promise(resolve=>server.listen(5190,"127.0.0.1",resolve));
 }
 const base=published?"https://yourizorge.github.io/fitmetzorge-staging/":"http://127.0.0.1:5190/";
 browser=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},colorScheme:"light"});
 const page=await context.newPage();
 let currentSession,currentRole,loseApply=false;
 await page.route(BASE+"/**",async route=>{
  const request=route.request(),url=new URL(request.url());
  let event=null;
  if(request.method()==='POST'){
   if(url.pathname==='/functions/v1/fmz6e10-synthetic')event=followup.request(currentRole,request.postDataJSON(),'browser_edge');
   else if(url.pathname==='/auth/v1/logout')event=followup.record(currentRole,'logout','browser_auth');
   else throw Error('unexpected_browser_auth_write');
  }
  if(loseApply&&route.request().method()==="POST"&&route.request().postDataJSON()?.action==="apply"){
   loseApply=false;const r=await route.fetch();followup.response(event,r.status());await route.abort("failed");return;
  }
  const r=await route.fetch();followup.response(event,r.status());await route.fulfill({response:r});
 });
 page.on("pageerror",e=>report.errors.push(e.message));
 page.on("request",r=>{
  const origin=new URL(r.url()).origin;
  if(![new URL(base).origin,"https://mokxyyullfhkfalopbzd.supabase.co"].includes(origin))report.errors.push("unexpected_origin");
  if(r.headers()["x-fmz6e10-proof"])report.errors.push("proof_in_browser");
 });
 await page.goto(base+"coach-source-demo/index.html?lang=nl&theme=light");
 await check("signed-out page contains no synthetic plan data",await page.locator("#login").count()===1&&await page.locator(".proposal").count()===0);
 async function idle(){await page.waitForFunction(()=>!["Bezig...","Working...","Wird verarbeitet..."].some(s=>document.querySelector("#feedback")?.textContent.startsWith(s)));}
 async function login(role){
  currentRole=role;
  const s=await b.call({op:"session",role});
  currentSession=s;
  await page.evaluate(s=>sessionStorage.setItem("fmz6e10-session",JSON.stringify(s)),s);
  await page.reload();await page.locator("#identity").waitFor();await idle();
 }
 async function click(selector){await page.locator(selector).click();await idle();}
 await login("trainer");
 await page.locator("#management summary").first().click();
 await page.locator('#prepare input[name="hours"]').fill("2");
 await page.locator('#prepare button[type="submit"]').click();await idle();
 await click('[data-action="activate"]:not([disabled])');
 await page.locator("#route-content").waitFor();
 let home=(await api.raw("trainer",{op:"home"})).data;
 windowId=home.workspaces[0].window;
 await check("operator creates and activates a fresh managed window",!!windowId);
 await click('[data-action="new-source"]');
 await page.locator('#source-form input[name="note"]').fill("Synthetische trainerbron v1 voor de ownerretest.");
 await page.locator('#source-form button[type="submit"]').click();await idle();
 await check("v1 created by authenticated trainer",await page.locator(".source").count()===1);
 await click('[data-action="propose"]');
 await login("member");
 await click('[data-action="member_accept"]:not([disabled])');
 await check("member cannot act as trainer",await page.locator('[data-action="trainer_approve"]').count()===0);
 await page.reload();await page.locator(".member_accepted").waitFor();await idle();
 await check("refresh preserves server member acceptance",await page.locator(".member_accepted").count()===1);
 await click('[data-action="logout"]');await page.locator("#login").waitFor();
 const oldJwt=await fetch(BASE+"/functions/v1/fmz6e10-synthetic",{method:"POST",headers:{Authorization:"Bearer "+currentSession.access_token,"Content-Type":"application/json"},body:'{"op":"home"}'});
 await oldJwt.text();await check("logout denies still-signed browser JWT", [401,403].includes(oldJwt.status));
 await login("trainer");
 await click('[data-action="new-source"]');
 await page.locator('[data-rule="0"][data-field="reps_step"]').fill("2");
 await page.locator('#source-form input[name="note"]').fill("Synthetische trainerbron v2: expliciet twee reps.");
 await page.locator('#source-form button[type="submit"]').click();await idle();
 await check("v2 leaves v1 proposal stale and application unavailable",await page.locator(".source").count()===2&&await page.locator(".warning").count()>0&&await page.locator('[data-action="apply"]:not([disabled])').count()===0);
 await click('[data-action="propose"]');
 await login("member");
 await click('[data-action="member_accept"]:not([disabled])');
 await login("trainer");
 await click('[data-action="trainer_approve"]:not([disabled])');
 await check("trainer approval leaves separate apply button",await page.locator(".approved").count()===1&&await page.locator('[data-action="apply"]:not([disabled])').count()===1);
 const active=(await api.raw("trainer",{op:"home"})).data.workspaces.find(x=>x.window===windowId);
 const approved=(await api.raw("trainer",{op:"read",window:windowId,workspace:active.workspace})).data;
 const latest=approved.proposals.at(-1);
 const applyAttempt=()=>api.raw("trainer",{op:"command",window:windowId,workspace:active.workspace,key:crypto.randomUUID(),expected:approved.window.revision,action:"apply",data:{proposal:latest.id,proposal_version:latest.version}});
 try{
  await api.sql("update public.profiles set trainer_id=null where id="+api.lit(api.ids.member));
  await check("trainer unlinked after approval cannot apply",[401,403].includes((await applyAttempt()).status));
 }finally{await api.sql("update public.profiles set trainer_id="+api.lit(api.ids.trainer)+" where id="+api.lit(api.ids.member));}
 try{
  await api.sql("update fmz6e10_private.workspaces set consent=false where id="+api.lit(active.workspace));
  await check("withdrawn consent after approval cannot apply",(await applyAttempt()).status===403);
  await api.sql("update fmz6e10_private.workspaces set consent=true,guard='self_reported' where id="+api.lit(active.workspace));
  await check("self-reported recovery is not application clearance",(await applyAttempt()).status===403);
 }finally{await api.sql("update fmz6e10_private.workspaces set consent=true,guard='clear' where id="+api.lit(active.workspace));}
 await check("all blocked apply attempts preserve plan version",(await api.raw("member",{op:"read",window:windowId,workspace:active.workspace})).data.active_version===1);
 for(const [width,height,name] of [[390,844,"mobile"],[768,1024,"tablet"],[1440,1000,"desktop"]]){
  await page.setViewportSize({width,height});
  for(const lang of ["nl","en","de"])for(const theme of ["light","dark"]){
   await page.locator("#language").selectOption(lang);await page.locator("#theme").selectOption(theme);
   const layout=await page.evaluate(()=>{
    const bad=[...document.querySelectorAll("button,input,select,.comparison,.source,.proposal")].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.left<0||r.right>innerWidth+1||e.scrollWidth>e.clientWidth+2);}).map(e=>e.tagName+":"+e.className);
    return {overflow:document.documentElement.scrollWidth>innerWidth+1,bad,logo:document.querySelector(".brand img").naturalWidth};
   });
   assert(!layout.overflow&&layout.bad.length===0&&layout.logo>0,JSON.stringify({name,lang,theme,layout}));
   report.layouts.push({name,width,height,lang,theme,pass:true});
   if(lang==="nl"){
    await page.locator(".proposal").first().scrollIntoViewIfNeeded();
    const file=path.join(out,name+"-"+lang+"-"+theme+".png");await page.screenshot({path:file});report.screenshots.push(file);
   }
  }
 }
 await check("18 responsive language/theme layouts",report.layouts.length===18);
 await page.locator("#language").selectOption("nl");
 loseApply=true;
 await click('[data-action="apply"]:not([disabled])');
 await check("uncertain application offers same-request retry",await page.locator('[data-action="retry"]').count()===1);
 await click('[data-action="retry"]');
 await check("separate application creates v2 and disables duplicate action",await page.locator(".applied").count()===1&&await page.locator('[data-action="apply"]:not([disabled])').count()===0);
 await login("member");
 const first=page.locator(".plan").filter({hasText:"v1"}).first();
 await first.locator("summary").click();
 await click('[data-action="restore"][data-plan="1"]');
 await click('[data-action="member_accept"]:not([disabled])');
 await login("trainer");await click('[data-action="trainer_approve"]:not([disabled])');await click('[data-action="apply"]:not([disabled])');
 await check("restore creates version 3 with source history retained",await page.locator(".plan").count()===3);
 async function fresh(action,data={},role="trainer"){
  const v=(await api.raw(role,{op:"read",window:windowId,workspace:active.workspace})).data;
  const r=await api.raw(role,{op:"command",window:windowId,workspace:active.workspace,key:crypto.randomUUID(),expected:v.window.revision,action,data});
  assert.equal(r.status,200,JSON.stringify(r.data));return r.data;
 }
 // Rejection and blocking are committed workflow states, not transport failures.
 const current=structuredClone(approved.sources.at(-1).body);current.comparable_plan_versions=[1,3];
 await fresh("source_append",{body:current,valid_from:approved.window.starts_at,valid_until:approved.window.ends_at});
 for(const action of ["member_reject","trainer_reject","trainer_block"]){
  const p=await fresh("propose");
  const data={proposal:p.proposal,proposal_version:p.proposal_version};
  if(action!=="member_reject")await fresh("member_accept",data,"member");
  const r=await fresh(action,data,action==="member_reject"?"member":"trainer");
  await check(action+" commits its terminal status",r.status===(action==="trainer_block"?"blocked":"rejected"));
  const v=(await api.raw("trainer",{op:"read",window:windowId,workspace:active.workspace})).data;
  const denied=await api.raw("trainer",{op:"command",window:windowId,workspace:active.workspace,key:crypto.randomUUID(),expected:v.window.revision,action:"apply",data});
  await check(action+" cannot be applied",denied.status===403&&v.active_version===3);
 }
 await click('[data-action="refresh"]');
 await click('[data-action="new-source"]');
 await page.locator('#source-form input[name="comparable_plan_versions"]').fill("1,3");
 await page.locator('[data-rule="1"][data-field="weight_step"]').fill("3");
 await page.locator('#source-form button[type="submit"]').click();await idle();
 await click('[data-action="propose"]');
 const blocked=await page.locator(".proposal").first().innerText();
 await check("W2 displays full configured step and attempted weight without partial apply",blocked.includes("Ingestelde stap: 3 kg")&&blocked.includes("Berekend gewicht: 43 kg")&&await page.locator('[data-action="apply"]:not([disabled])').count()===0);
 await click('[data-action="withdraw"]');
 await click('[data-action="propose"]');
 await check("withdrawn source gives explicit server refusal",/synthetic_source_unavailable/.test(await page.locator("#feedback").innerText()));
 await login("b");
 await check("B has neither sources nor A actions nor management",await page.locator(".source").count()===0&&await page.locator(".proposal").count()===0&&await page.locator("#management").count()===0);
 await login("trainer");
 await page.locator("#management summary").first().click();
 await click('[data-action="revoke"]:not([disabled])');
 await check("revoke removes active workspace on refresh",await page.locator("#route-content").count()===0);
 await click('[data-action="cleanup"]:not([disabled])');
 await check("cleanup is visible and disabled after completion",await page.locator(".cleaned").count()>0);
 assert.equal(report.errors.length,0,report.errors.join(","));
 report.pass=true;
}catch(e){report.errors.push(e.message);console.error(e.message);process.exitCode=1;}
finally{
 if(api&&windowId){
  try{
   let h=(await api.raw("trainer",{op:"home"})).data,w=h.windows.find(x=>x.id===windowId);
   if(w?.status==="active"){await api.raw("trainer",{op:"command",window:windowId,workspace:null,key:crypto.randomUUID(),expected:w.revision,action:"revoke",data:{}});}
   h=(await api.raw("trainer",{op:"home"})).data;w=h.windows.find(x=>x.id===windowId);
   if(w&&w.status!=="cleaned")await api.raw("trainer",{op:"command",window:windowId,workspace:null,key:crypto.randomUUID(),expected:w.revision,action:"cleanup",data:{}});
  }catch{report.errors.push("cleanup_check_required");report.pass=false;process.exitCode=1;}
 }
 try{await followup.cleanupSessions();await followup.finish(report.pass===true);}catch(e){report.errors.push(e.message);report.pass=false;process.exitCode=1;}
 if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));b.assertQuiet();await b.close();
 fs.writeFileSync(path.join(out,"report.json"),JSON.stringify(report,null,2)+"\n");
}
console.log(JSON.stringify({pass:report.pass,checks:report.checks.length,layouts:report.layouts.length,errors:report.errors}));
