const fs=require("fs"),path=require("path"),crypto=require("crypto"),{execFileSync}=require("child_process"),{chromium}=require("playwright");
const root=path.resolve(__dirname,".."),base="https://yourizorge.github.io/fitmetzorge-staging/";
const git=process.env.FMZ_GIT||"git",commit=process.env.FMZ_VERIFY_COMMIT||"ab9b3f186898522ae91dba230e8df0adf1f9d895";
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
(async()=>{
 const files=[];
 for(const name of ["index.html","app.js","assets/phase6d0-legacy-auth.js","assets/phase6c-private-ai-chat.js","assets/youri-ai-avatar-3d-v3-256.webp"]){
  const response=await fetch(base+name+"?verify="+commit,{cache:"no-store"});
  const bytes=Buffer.from(await response.arrayBuffer()),expected=execFileSync(git,["show",commit+":"+name],{cwd:root,encoding:null,maxBuffer:5000000,windowsHide:true});
  if(response.status!==200||!bytes.equals(expected))throw new Error("asset_mismatch:"+name);
  files.push({name,status:response.status,sha256:sha(bytes)});
 }
 const preflight=await fetch("https://mokxyyullfhkfalopbzd.supabase.co/functions/v1/invite-client",{method:"OPTIONS",headers:{Origin:"https://yourizorge.github.io","Access-Control-Request-Method":"POST"}});
 if(preflight.status!==204)throw new Error("invite_preflight_failed");
 const unauthorized=await fetch("https://mokxyyullfhkfalopbzd.supabase.co/functions/v1/invite-client",{method:"POST",headers:{"Content-Type":"application/json",Origin:"https://yourizorge.github.io"},body:"{}"});
 if(unauthorized.status!==401)throw new Error("invite_unauthorized_failed");
 const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
 const viewports=[];
 try{
 for(const [width,height] of [[320,700],[390,844],[820,1180],[1440,900]]){
  const page=await browser.newPage({viewport:{width,height}});
  const errors=[],blockedWrites=[];page.on("pageerror",e=>errors.push(e.message));
  await page.route("https://mokxyyullfhkfalopbzd.supabase.co/**",route=>{
   if(!["GET","HEAD","OPTIONS"].includes(route.request().method())){blockedWrites.push(route.request().method());return route.abort();}
   return route.continue();
  });
  await page.goto(base+"?verify="+commit,{waitUntil:"networkidle"});
  await page.waitForFunction(()=>window.FMZ_PHASE6D0_LEGACY_AUTH&&window.FMZ_PHASE6C_PRIVATE_CHAT);
  const state=await page.evaluate(()=>({security:window.FMZ_PHASE6D0_LEGACY_AUTH.version,overflow:document.documentElement.scrollWidth>innerWidth,loggedOut:document.body.classList.contains("logged-out")}));
  if(errors.length||state.overflow||blockedWrites.length)throw new Error("live_runtime_failed:"+width+":"+errors.join("|"));
  viewports.push({width,height,...state,pageErrors:errors.length,writeRequests:blockedWrites.length});
  await page.close();
 }
 }finally{await browser.close();}
 console.log(JSON.stringify({overall_pass:true,commit,files,invitePreflight:preflight.status,inviteUnauthorized:unauthorized.status,viewports,ownerDataMutated:false},null,2));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
