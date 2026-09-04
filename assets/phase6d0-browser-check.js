const fs=require("fs"),path=require("path"),vm=require("vm"),assert=require("node:assert/strict");
const {chromium}=require("playwright");
const root=path.resolve(__dirname,"..");
const runtime=fs.readFileSync(path.join(root,"assets/phase6d0-legacy-auth.js"),"utf8");
const checks=[];const check=(name,pass)=>{checks.push({name,pass:Boolean(pass)});};
const patches=["phase6d0-legacy-auth.js","phase1-foundation.js","phase2-home-recovery.js","phase3-training-engine.js","phase4-nutrition-slice2.js","phase4-nutrition-slice3.js","member-ux-consistency.js","phase5-progress.js","phase6c-private-ai-chat.js"].map(f=>fs.readFileSync(path.join(root,"assets",f),"utf8"));
new vm.Script(fs.readFileSync(path.join(root,"app.bundle.js"),"utf8").replace("\ninit();","\n"+patches.join("\n")+"\ninit();"));
check("real assembled nine-patch bundle parses",true);
check("no metadata role authority",!runtime.includes("user_metadata?.role"));
check("no full workspace write in member patch",!runtime.includes('.from("coach_workspaces")'));
check("frozen chat unchanged by auth patch",!runtime.includes("phase6c_")&&!runtime.includes("OpenAI"));
check("no polling or observers",!/(MutationObserver|setInterval|location.reload)/.test(runtime));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
 for(const [width,height] of [[320,700],[390,844],[820,1180],[1440,900]]){
  const page=await browser.newPage({viewport:{width,height}});const errors=[];page.on("pageerror",e=>errors.push(e.message));
  await page.route("https://staging-test.invalid/**",route=>route.fulfill({contentType:"text/html",body:"<!doctype html><html><body><main>Staging authorization fixture</main></body></html>"}));
  await page.goto("https://staging-test.invalid/?fmz_invite="+"a".repeat(64));
  await page.addScriptTag({content:`
   let onlineProfile=null,onlineErrorMessage="";
   let state={clients:[{id:"slot-a",name:"A",email:"member@example.invalid",water:1,password:"never-send"}]};
   let ensureOnlineProfile=()=>{},loadOnlineWorkspace=async()=>{window.__legacyLoads++;},saveStateToCloud=async()=>{window.__legacySaves++;return{ok:true};};
   let applyOnlineState=(s,p)=>{state=s;onlineProfile=p;};const profileDisplayName=()=>"Synthetic";const syncStatus=()=>{};
   window.__calls=[];window.__legacyLoads=0;window.__legacySaves=0;window.__events=[];window.__existing=true;window.__conflict=false;
   const supabaseClient={auth:{getUser:async()=>({data:{user:{id:"member",user_metadata:{role:"trainer"}}}}),onAuthStateChange:f=>window.__events.push(f)},
    from:()=>({select:()=>({eq:()=>({maybeSingle:async()=>({data:window.__existing?{id:"member",role:"client",trainer_id:"trainer",client_id:"slot-a"}:null})})})}),
    rpc:async(name,args)=>{window.__calls.push({name,args});
     if(name==="fmz_phase6d0_read_own_workspace")return{data:{state:{clients:[{id:"slot-a",email:"member@example.invalid",water:1}]},revision:"r1"}};
     if(name==="fmz_phase6d0_save_own_workspace")return window.__conflict?{error:{code:"40001"}}:{data:{revision:"r2"}};
     return{data:{id:"member",role:"client"}};}};
   `+runtime+`
   window.__api={ensure:()=>ensureOnlineProfile("trainer"),load:p=>loadOnlineWorkspace(p),save:()=>saveStateToCloud(),
    change:()=>state.clients[0].water=2,clearProfile:()=>onlineProfile=null,setTrainer:()=>onlineProfile={id:"trainer",role:"trainer"}};
  `});
  await page.evaluate(()=>window.__api.ensure());
  const initial=await page.evaluate(()=>({calls:window.__calls,clean:!location.search.includes("fmz_invite"),token:sessionStorage.getItem("fmz.staging.verified-invite.v1")}));
  check(width+" invite consumed once",initial.calls.filter(x=>x.name==="fmz_phase6d0_accept_client_invite").length===1);
  check(width+" invite removed from URL/storage",initial.clean&&initial.token===null);
  await page.evaluate(()=>window.__api.load({id:"member",role:"client",trainer_id:"trainer",client_id:"slot-a"}));
  await page.evaluate(()=>window.__api.change());await page.evaluate(()=>window.__api.save());
  const saved=await page.evaluate(()=>window.__calls.find(x=>x.name==="fmz_phase6d0_save_own_workspace"));
  check(width+" only own client payload/revision",Object.keys(saved.args).sort().join(",")==="p_client,p_expected_revision"&&saved.args.p_client.id==="slot-a"&&saved.args.p_expected_revision==="r1"&&!saved.args.p_client.password);
  await page.evaluate(()=>window.__conflict=true);
  check(width+" conflict preserved",!(await page.evaluate(()=>window.__api.save())).ok);
  await page.evaluate(()=>{window.__events.forEach(fn=>fn("SIGNED_OUT"));});
  check(width+" logout invalidates workspace revision",!(await page.evaluate(()=>window.__api.save())).ok);
  await page.evaluate(()=>{window.__api.setTrainer();});
  await page.evaluate(()=>window.__api.save());await page.evaluate(()=>window.__api.load({id:"trainer",role:"trainer"}));
  check(width+" trainer delegate preserved",await page.evaluate(()=>window.__legacyLoads===1&&window.__legacySaves===1));
  await page.evaluate(()=>{window.__existing=false;window.__api.clearProfile();});
  check(width+" metadata trainer hint does not create trainer",(await page.evaluate(()=>window.__api.ensure())).role==="client");
  check(width+" no errors/overflow",errors.length===0&&await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.close();
 }
 await browser.close();
 const failed=checks.filter(x=>!x.pass);console.log(JSON.stringify({scope:"phase6d0_browser",pass_count:checks.length-failed.length,fail_count:failed.length,failed},null,2));
 if(failed.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
