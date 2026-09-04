const fs=require("fs"),path=require("path"),crypto=require("crypto"),{execFileSync}=require("child_process"),{chromium}=require("playwright");
const root=path.resolve(__dirname,".."),base="https://yourizorge.github.io/fitmetzorge-staging/";
const commit=process.env.FMZ_VERIFY_COMMIT,git=process.env.FMZ_GIT||"git";
if(!/^[0-9a-f]{40}$/.test(commit||""))throw new Error("immutable_commit_required");
async function main(){
  const files=[];
  for(const name of ["index.html","app.js","app.bundle.js","assets/phase1-foundation.js","assets/phase5-progress.js","assets/phase6d0-legacy-auth.js","assets/phase6c-private-ai-chat.js"]){
    const expected=execFileSync(git,["show",commit+":"+name],{cwd:root,windowsHide:true,maxBuffer:5000000});
    let verified=false;
    for(let attempt=0;attempt<8;attempt++){
      const response=await fetch(base+name+"?verify="+commit,{cache:"no-store"});
      const bytes=Buffer.from(await response.arrayBuffer());
      if(response.status===200&&bytes.equals(expected)){
        files.push({file:name,http:200,commit_identical:true,sha256:crypto.createHash("sha256").update(bytes).digest("hex")});verified=true;break;
      }
      await new Promise(resolve=>setTimeout(resolve,15000));
    }
    if(!verified)throw new Error("live_asset_not_yet_matching:"+name);
  }
  const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"}),viewports=[];
  try{
    for(const [width,height] of [[320,700],[390,844],[820,1180],[1440,900]]){
      const context=await browser.newContext({viewport:{width,height}});
      const page=await context.newPage(),errors=[],writes=[],wrongProjects=[];
      page.on("pageerror",error=>errors.push(error.name));
      page.on("console",msg=>{if(msg.type()==="error")errors.push(msg.text().replace(/https?:\/\/\S+/g,"[url]").slice(0,180));});
      page.on("response",response=>{if(response.status()>=400){const url=new URL(response.url());console.log(JSON.stringify({resourceStatus:response.status(),host:url.hostname,path:url.pathname}));}});
      await page.route("**/*.supabase.co/**",route=>{
        const request=route.request();
        if(new URL(request.url()).hostname!=="mokxyyullfhkfalopbzd.supabase.co"){wrongProjects.push(true);return route.abort();}
        if(!["GET","OPTIONS","HEAD"].includes(request.method())){writes.push(request.method());return route.abort();}
        return route.continue();
      });
      await page.goto(base+"?verify="+commit,{waitUntil:"networkidle"});
      await page.waitForFunction(()=>window.FMZ_PUBLIC_AUTH&&window.FMZ_PHASE5_PROGRESS);
      for(const mode of ["register","login","forgot","login"]){
        await page.locator('[data-auth-mode="'+mode+'"]').filter({visible:true}).first().click();
        if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error("overflow:"+width);
      }
      await page.reload({waitUntil:"networkidle"});
      const result=await page.evaluate(()=>({public:document.body.classList.contains("logged-out"),resendButtons:document.querySelectorAll("[data-phase1-resend]").length,memberNavEmpty:document.getElementById("nav").children.length===0}));
      if(!result.public||result.resendButtons!==2||!result.memberNavEmpty||errors.length||writes.length||wrongProjects.length)throw new Error("public_runtime_failed:"+width+":"+JSON.stringify({result,errors,writes,wrongProjects}));
      viewports.push({width,height,...result,errors:0,mutatingRequests:0});
      await context.close();
    }
  }finally{await browser.close();}
  const result={overall_pass:true,commit,cache:"20260904-auth-lifecycle2",files,viewports,databaseMutation:false};
  fs.writeFileSync(path.join(root,"supabase/.temp/public-auth-live-result.json"),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
