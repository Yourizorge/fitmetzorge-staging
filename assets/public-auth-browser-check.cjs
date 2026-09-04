const fs = require("fs"), path = require("path"), assert = require("node:assert/strict");
const { chromium } = require("playwright");
const root = path.resolve(__dirname, "..");
const base = "https://yourizorge.github.io/fitmetzorge-staging/";
const checks = [];
function check(name, pass) { checks.push({ name, pass: Boolean(pass) }); if (!pass) throw new Error(name); }
const probe = `
  window.__memberCalls = [];
  for (const name of ["renderTrainerDashboard","renderClientHome","renderTraining","renderNutrition","renderTrackersOverview","renderProgress","renderSettingsPage"]) {
    const original = eval(name);
    eval(name + " = function(...args) { window.__memberCalls.push('" + name + "'); return original(...args); }");
  }
  document.getElementById("progressGoalStrip")?.remove();
  window.__authTest = {
    render: () => { renderNav(); renderAll(); showView("progress"); },
    language: language => { state.accountSettings.language = language; showAuthPanel("login"); },
    panel: mode => showAuthPanel(mode),
    stale: () => { state.ui.loggedIn=true; state.ui.role="client"; renderAll(); },
    recovery: () => requirePasswordSetup("recovery"),
    member: () => { passwordSetupRequired=false; state.ui.loggedIn=true; state.ui.role="client"; onlineProfile=window.__mock.profile; onlineReady=true; currentView="progress"; renderProgress(); },
    loggedIn: () => isLoggedIn(),
    hydrate: () => hydrateOnlineUser(),
    logout: () => { state.ui.loggedIn=false; onlineReady=false; onlineProfile=null; window.__memberCalls=[]; renderAll(); showAuthPanel("register"); },
  };
`;
function mockSetup() {
  const profile = { id:"10000000-0000-4000-8000-000000000001", email:"synthetic@example.invalid", role:"client", name:"Synthetic", trainer_id:null, email_confirmed_at:"2026-09-04T10:00:00Z" };
  const mock = window.__mock = { profile, calls:[], delay:150, loginFail:true, resendError:null, session:location.search.includes("type=")?{user:profile}:null, listeners:[] };
  const sleep = () => new Promise(resolve => setTimeout(resolve, mock.delay));
  const query = table => {
    const chain = new Proxy({}, { get(_, key) {
      if (key === "then") return resolve => { mock.calls.push(table); return Promise.resolve({data:table==="profiles"?profile:null,error:null}).then(resolve); };
      return () => chain;
    } });
    return chain;
  };
  const auth = {
    getSession:async()=>{await sleep();return{data:{session:mock.session},error:null};},
    getUser:async()=>({data:{user:mock.session?.user},error:null}),
    onAuthStateChange:fn=>{mock.listeners.push(fn);return{data:{subscription:{unsubscribe(){}}}};},
    signUp:async()=>{mock.calls.push("signup");await sleep();return{data:{session:null,user:profile},error:null};},
    signInWithPassword:async()=>{mock.calls.push("login");await sleep(); if(mock.loginFail)return{error:{code:"invalid_credentials",message:"DO_NOT_DISPLAY technical stack"}};
      mock.session={user:profile};return{data:{session:mock.session},error:null};},
    resetPasswordForEmail:async()=>{mock.calls.push("recover");await sleep();return{error:null};},
    updateUser:async()=>{mock.calls.push("password");await sleep();return{error:{message:"DO_NOT_DISPLAY technical stack"}};},
    signOut:async()=>{mock.session=null;mock.listeners.forEach(fn=>fn("SIGNED_OUT",null));return{error:null};},
    resend:async args=>{mock.calls.push("resend");mock.resendType=args.type;mock.redirect=args.options.emailRedirectTo;await sleep();return{error:mock.resendError};}
  };
  window.supabase={createClient:()=>({auth,from:query,rpc:async name=>{
    mock.calls.push(name);
    return{data:name==="fmz_phase5_get_progress_dashboard"?{access:"free",unit_system:"metric",today:"2026-09-04",weights:[],measurements:[],strength:[],consistency:{},recovery_context:{},nutrition_context:{}}:{},error:null};
  }})};
}
async function run() {
  const browser = await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
  try {
    for (const [width,height] of [[320,700],[390,844],[820,1180],[1440,900]]) {
      const context = await browser.newContext({viewport:{width,height}});
      await context.addInitScript(mockSetup);
      await context.route("**/*", async route => {
        const url = new URL(route.request().url());
        if (!route.request().url().startsWith(base)) return route.fulfill({body:"",contentType:"application/javascript"});
        const relative = decodeURIComponent(url.pathname.slice(new URL(base).pathname.length)) || "index.html";
        assert(!relative.includes(".."));
        const file = path.join(root,relative);
        let body = fs.readFileSync(file);
        if (relative==="app.bundle.js") body=Buffer.from(body.toString().replace("\ninit();","\n"+probe+"\ninit();"));
        await route.fulfill({body,contentType:relative.endsWith(".js")?"application/javascript":relative.endsWith(".css")?"text/css":relative.endsWith(".html")?"text/html":"application/octet-stream"});
      });
      const page=await context.newPage(), errors=[];
      page.on("pageerror",e=>errors.push(e.message));page.on("console",msg=>{if(msg.type()==="error")errors.push(msg.text());});
      await page.goto(base);
      await page.waitForFunction(()=>window.__authTest);
      await page.waitForTimeout(250);
      check(width+" public init no member render/hydration",await page.evaluate(()=>__memberCalls.length===0&&__mock.calls.length===0));
      await page.evaluate(()=>__authTest.stale());
      check(width+" stale stored login is not a session",!await page.evaluate(()=>__authTest.loggedIn()));
      await page.click('[data-auth-mode="register"]');
      await page.fill('#registerForm [name="name"]',"Synthetic");
      await page.fill('#registerForm [name="email"]',"synthetic@example.invalid");
      await page.fill('#registerForm [name="password"]',"synthetic-only-password");
      await page.click('#registerForm [type="submit"]');
      await page.waitForFunction(()=>document.getElementById("registerMessage").textContent.includes("Controleer"));
      check(width+" signup no member code and safe cooldown",await page.evaluate(()=>__memberCalls.length===0&&__mock.calls.join(",")==="signup"&&document.querySelector("#registerForm [data-phase1-resend]").disabled));
      await page.reload();await page.waitForFunction(()=>window.__authTest);
      check(width+" cooldown survives refresh",await page.isDisabled('#loginForm [data-phase1-resend]'));
      await page.fill('#loginForm [name="email"]',"synthetic@example.invalid");
      await page.fill('#loginForm [name="password"]',"synthetic-only-password");
      await page.click('#loginForm [type="submit"]');await page.waitForTimeout(250);
      check(width+" login errors sanitized",!(await page.textContent("#loginMessage")).includes("DO_NOT_DISPLAY"));
      await page.click('[data-auth-mode="forgot"]');await page.fill('#forgotPasswordForm [name="email"]',"synthetic@example.invalid");
      await page.click('#forgotPasswordForm [type="submit"]');await page.waitForTimeout(250);
      check(width+" reset public-only",await page.evaluate(()=>__memberCalls.length===0&&__mock.calls.every(n=>["login","recover"].includes(n))));
      await page.evaluate(()=>sessionStorage.removeItem("fmz.auth.resend-after.v1"));
      await page.reload();await page.waitForFunction(()=>window.__authTest);await page.waitForTimeout(250);
      await page.fill('#loginForm [name="email"]',"synthetic@example.invalid");
      await page.evaluate(()=>{const button=document.querySelector("#loginForm [data-phase1-resend]");button.click();button.click();});
      await page.waitForTimeout(250);
      check(width+" resend exactly once correct contract",await page.evaluate(()=>__mock.calls.filter(n=>n==="resend").length===1&&__mock.resendType==="signup"&&__mock.redirect==="https://yourizorge.github.io/fitmetzorge-staging/"));
      check(width+" resend enumeration safe",/Als bevestiging nodig/.test(await page.textContent("#loginMessage")));
      for(const language of ["nl","en","de"]){
        await page.evaluate(language=>__authTest.language(language),language);
        check(width+" "+language+" resend fits",await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.querySelector("[data-phase1-resend]").textContent.length>10));
      }
      await page.evaluate(()=>__authTest.recovery());
      await page.fill('#setPasswordForm [name="password"]',"synthetic-only-password");await page.fill('#setPasswordForm [name="passwordConfirm"]',"synthetic-only-password");
      await page.click('#setPasswordForm [type="submit"]');await page.waitForTimeout(250);
      check(width+" recovery no member code or raw error",await page.evaluate(()=>__memberCalls.length===0&&!document.getElementById("setPasswordMessage").textContent.includes("DO_NOT_DISPLAY")));
      for(const suffix of ["?type=signup","?type=recovery","#error=access_denied&error_description=DO_NOT_DISPLAY"]){
        await page.goto(base+suffix);await page.waitForFunction(()=>window.__authTest);await page.waitForTimeout(300);
        check(width+" callback "+suffix.split("=")[0]+" no member hydration",await page.evaluate(()=>__memberCalls.length===0&&__mock.calls.length===0));
        check(width+" callback no overflow",await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      }
      await page.evaluate(()=>sessionStorage.removeItem("fmz.auth.confirmation-login-required"));
      await page.goto(base);await page.waitForFunction(()=>window.__authTest);await page.waitForTimeout(250);
      await page.evaluate(()=>{__mock.loginFail=false;__mock.delay=300;});
      await page.selectOption('#loginForm [name="role"]',"client");
      await page.fill('#loginForm [name="email"]',"synthetic@example.invalid");
      await page.fill('#loginForm [name="password"]',"synthetic-only-password");
      await page.click('#loginForm [type="submit"]');
      await page.waitForFunction(()=>__authTest.loggedIn());
      check(width+" successful slow login enters member lifecycle",await page.evaluate(()=>__mock.calls.includes("profiles")&&__memberCalls.length>0));
      await page.evaluate(()=>__authTest.member());await page.waitForTimeout(250);
      check(width+" member progress still rendered",await page.locator(".phase5-shell").count()===1);
      await page.evaluate(()=>__authTest.logout());
      check(width+" member Progress to public route has no legacy fallback",await page.evaluate(()=>!document.getElementById("progressGoalStrip")&&__memberCalls.length===0&&!__authTest.loggedIn()));
      await page.screenshot({path:path.join(root,"supabase/.temp/auth-hotfix-"+width+".png"),fullPage:true});
      check(width+" no console errors",errors.length===0);
      await context.close();
    }
  } finally { await browser.close(); }
  console.log(JSON.stringify({suite:"public_auth_assembled_runtime",pass_count:checks.filter(c=>c.pass).length,fail_count:checks.filter(c=>!c.pass).length,checks},null,2));
}
run().catch(error=>{console.error(error.message);console.log(JSON.stringify(checks));process.exitCode=1;});
