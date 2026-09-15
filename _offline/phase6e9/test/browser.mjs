import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import assert from "node:assert/strict";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const {chromium}=require("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
export async function browserTest({root,transport,accounts,label="local",published=false}){
 const result={label,synthetic_only:true,physical_phone:false,checks:[],screenshots:[],layouts:0,errors:[]};
 const check=(name,condition)=>{assert(condition,name);result.checks.push(name);};
 const server=published?null:http.createServer((req,res)=>{
 const rel=decodeURIComponent(new URL(req.url,"http://local").pathname).replace(/^\//,"")||"coach-backend-demo/index.html";
 const file=path.resolve(root,rel);
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 const mime={".html":"text/html",".js":"application/javascript",".css":"text/css",".svg":"image/svg+xml",".png":"image/png",".webp":"image/webp"};
 res.writeHead(200,{"Content-Type":mime[path.extname(file)]||"text/plain"});fs.createReadStream(file).pipe(res);
 });
 if(server)await new Promise(r=>server.listen(5189,"127.0.0.1",r));
 const base=published?"https://yourizorge.github.io/fitmetzorge-staging/":"http://127.0.0.1:5189/";
 const browser=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},colorScheme:"light"});
 const page=await context.newPage();page.on("pageerror",e=>result.errors.push(e.message));
 result.responses=[];
 page.on("response",response=>{if(response.url().includes("mokxyyullfhkfalopbzd.supabase.co"))result.responses.push({path:new URL(response.url()).pathname,status:response.status()});});
 page.on("request",request=>{
 const u=new URL(request.url());
 if(u.origin!==new URL(base).origin&&u.origin!=="https://mokxyyullfhkfalopbzd.supabase.co")result.errors.push("unexpected_origin:"+u.origin);
 if(request.headers()["x-fmz6e9-proof"])result.errors.push("server_proof_in_browser");
 });
 let loseNextApply=false;
 await context.route("https://mokxyyullfhkfalopbzd.supabase.co/**",async route=>{
 const q=route.request();
 if(q.url().includes("/functions/v1/")&&q.method()==="POST"&&q.postDataJSON()?.command?.action==="open")await new Promise(resolve=>setTimeout(resolve,500));
 const lose=loseNextApply&&q.url().includes("/functions/v1/")&&q.method()==="POST"&&q.postDataJSON()?.command?.action==="apply";
 if(!transport){
 if(lose){loseNextApply=false;await route.fetch();await route.abort("failed");return;}
 await route.continue();return;
 }
 const response=await transport(new Request(q.url(),{method:q.method(),headers:q.headers(),body:["GET","HEAD"].includes(q.method())?undefined:q.postData()}));
 if(lose){loseNextApply=false;await route.abort("failed");return;}
 await route.fulfill({status:response.status,headers:Object.fromEntries(response.headers),body:await response.text()});
 });
 async function idle(){await page.waitForFunction(()=>!document.querySelector("#feedback")?.textContent.includes("Bezig")&&!document.querySelector("#feedback")?.textContent.includes("Working")&&!document.querySelector("#feedback")?.textContent.includes("verarbeitet..."));}
 async function login(account){
 await page.locator('input[name="email"]').fill(account.email);
 await page.locator('input[name="password"]').fill(account.password);
 await page.locator('#login button[type="submit"]').click();
 await page.locator("#route-content").waitFor();await idle();
 }
 async function logout(){await page.locator('[data-command="logout"]').click();await page.locator("#login").waitFor();}
 async function action(selector){await page.locator(selector).click();await idle();}
 const version=()=>page.locator(".backend-state").innerText();
 try{
 await page.goto(base+"coach-backend-demo/index.html?lang=nl&theme=light");
 await login(accounts.memberA);
 check("A has member role",/Route A.*Lid/.test(await version()));
 await page.locator('[data-command="open"]').click();
 check("loading state disables duplicate commands",await page.locator('[data-command="open"]').isDisabled()&&(await page.locator("#feedback").innerText()).includes("Bezig"));
 await idle();
 await action('[data-action="a"][data-value*="member_accept"]');
 check("A trainer approval not usable by member",await page.locator('[data-action="a"][data-value*="trainer_approve"]').isDisabled());
 await logout();await login(accounts.trainerA);
 await action('[data-action="a"][data-value*="trainer_approve"]');
 await action('[data-action="a"][data-value*="apply"]');
 check("A version 4",/v4/.test(await version()));
 await logout();await login(accounts.memberA);
 await action('[data-action="a"][data-value*="restore"][data-value*="3"]');
 await action('[data-action="a"][data-value*="member_accept"]');
 await logout();await login(accounts.trainerA);
 await action('[data-action="a"][data-value*="trainer_approve"]');await action('[data-action="a"][data-value*="apply"]');
 check("A restore version 5",/v5/.test(await version()));
 await matrix("A");
 await logout();await login(accounts.memberB);
 check("B never renders trainer approval",await page.locator('[data-action="a"]').count()===0);
 await page.locator('input[name="rir"]').uncheck();await page.locator('input[name="rpe"]').check();
 await page.locator("#theme").selectOption("dark");
 check("intake preserved across theme",!(await page.locator('input[name="rir"]').isChecked())&&await page.locator('input[name="rpe"]').isChecked());
 await action('[data-action="build"]');
 await action('[data-tab="recovery"]');await page.locator("#sleep-edit").selectOption("9");await action('[data-action="sleep"]');
 await action('[data-action="confirm"]');
 await page.locator("#sleep-edit").selectOption("8");await action('[data-action="sleep"]');
 check("edit invalidates confirmation",await page.locator('[data-action="apply"]').isDisabled());
 await action('[data-action="confirm"]');loseNextApply=true;await action('[data-action="apply"]');
 check("lost apply response offers explicit same-request retry",await page.locator('[data-command="retry"]').count()===1);
 await action('[data-command="retry"]');
 check("B version 1",/v1/.test(await version()));
 await page.reload();await page.locator("#route-content").waitFor();await idle();
 check("refresh retains backend version",/v1/.test(await version()));
 await action('[data-action="reopen"]');
 await action('[data-tab="recovery"]');await page.locator("#sleep-edit").selectOption("9");await action('[data-action="sleep"]');
 await action('[data-action="confirm"]');await action('[data-action="apply"]');
 check("B version 2",/v2/.test(await version()));
 await action('[data-action="restore"][data-value*="1"]');await action('[data-action="confirm"]');await action('[data-action="apply"]');
 check("B restore version 3",/v3/.test(await version()));
 await matrix("B");
 await page.keyboard.press("Tab");check("keyboard focus visible",await page.evaluate(()=>document.activeElement!==document.body));
 check("only dedicated synthetic browser session key",await page.evaluate(()=>Object.keys(sessionStorage).every(k=>k==="fmz6e9.synthetic.session.v1")&&localStorage.length===0));
 await logout();check("logout clears prior account view",await page.locator("#route-content").count()===0);
 await login(accounts.memberB);check("relogin retains version 3",/v3/.test(await version()));
 await context.setOffline(true);await action('[data-command="refresh"]');check("offline failure visible",(await page.locator("#feedback").innerText()).length>0);
 await context.setOffline(false);await action('[data-command="refresh"]');check("online recovery loads same version",/v3/.test(await version()));
 check("no unexpected page errors or external requests",result.errors.length===0);
 }catch(e){
 result.failure={message:e.message,feedback:await page.locator("#feedback").textContent().catch(()=>null)};
 throw e;
 }finally{
 await browser.close();if(server)await new Promise(r=>server.close(r));
 fs.mkdirSync(path.join(root,"supabase/.temp/phase6e9-browser"),{recursive:true});
 fs.writeFileSync(path.join(root,"supabase/.temp/phase6e9-browser/"+label+".json"),JSON.stringify(result,null,2)+"\n");
 }
 async function matrix(route){
 for(const width of [320,390,768,1280])for(const lang of ["nl","en","de"])for(const theme of ["light","dark","system"]){
 await page.setViewportSize({width,height:900});await page.locator("#lang").selectOption(lang);await page.locator("#theme").selectOption(theme);
 const dimensions=await page.evaluate(()=>({w:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth}));
 check(route+"/"+width+"/"+lang+"/"+theme+" no overflow",dimensions.scroll<=width&&dimensions.body<=width);
 if(route==="B")for(const tab of ["training","nutrition","recovery"]){await page.locator('[data-tab="'+tab+'"]').click();check("B/"+width+"/"+lang+"/"+theme+"/"+tab+" fits",await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
 result.layouts++;
 if(width===390&&lang==="nl"&&theme!=="system"){
 const name=label+"-"+route+"-"+width+"-"+lang+"-"+theme+".png",file=path.join(root,"supabase/.temp/phase6e9-browser",name);
 fs.mkdirSync(path.dirname(file),{recursive:true});await page.screenshot({path:file,fullPage:true});result.screenshots.push(file);
 }
 }
 await page.locator("#lang").selectOption("nl");await page.locator("#theme").selectOption("light");
 }
 return result;
}
