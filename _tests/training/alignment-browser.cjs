"use strict";
const fs = require("node:fs"), path = require("node:path"), assert = require("node:assert/strict");
const { chromium } = require("playwright");
const { setup, backendFixture, enter, create, start } = require("./correction-browser.cjs");
const root = path.resolve(__dirname, "../.."), mode = process.argv[2] || "local", before = mode === "baseline";
const checks = [], geometry = [], screens = [];
function check(label, pass) { checks.push({label, pass:!!pass}); if (!before) assert(pass, label); }
async function shot(page, label) {
  const file = path.join(root, "supabase/.temp/training-alignment-" + mode + "-" + label + ".png");
  await page.screenshot({path:file}); screens.push(file);
}
async function measure(page, flags, label) {
  const rows = await page.locator(".tw-live-set").evaluateAll(nodes => nodes.map(n => {
    const rect = e => { const r=e.getBoundingClientRect(); return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}; };
    const main = [...n.children].slice(0,5).map(rect);
    const fields = ["rir","rpe"].map(key => {
      const e=n.querySelector("[data-phase3-"+key+"]"), above=n.querySelector("[data-phase3-"+(key==="rir"?"weight":"reps")+"]");
      return e ? {key,field:rect(e),above:rect(above),label:rect(e.closest("label"))} : {key,field:null};
    });
    return {main,fields,extra:n.querySelector(".tw-set-effort")!==null,overflow:n.scrollWidth>n.clientWidth+1};
  }));
  const pageOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  geometry.push({label,rows,pageOverflow});
  rows.forEach((r,i) => {
    check(label+" set "+i+" main compact", r.main.every(a=>a.top<r.main[0].bottom&&a.bottom>r.main[0].top));
    check(label+" set "+i+" optional row", r.extra===(flags.rir||flags.rpe));
    check(label+" set "+i+" no horizontal overflow", !r.overflow&&!pageOverflow);
    for(const f of r.fields) {
      check(label+" set "+i+" "+f.key+" visible", !!f.field===flags[f.key]);
      if(!f.field) continue;
      check(label+" set "+i+" "+f.key+" left/right exact", Math.abs(f.field.left-f.above.left)<.6&&Math.abs(f.field.right-f.above.right)<.6);
      check(label+" set "+i+" "+f.key+" label bound", Math.abs(f.label.left-f.above.left)<.6&&Math.abs(f.label.right-f.above.right)<.6);
      check(label+" set "+i+" "+f.key+" below and tappable", f.field.top>=Math.max(...r.main.map(a=>a.bottom))&&f.field.width>=44&&f.field.height>=44);
    }
  });
}
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"});
  try {
    for(const width of (before?[390]:[320,390,1440])) for(const flags of [{rir:false,rpe:false},{rir:true,rpe:false},{rir:false,rpe:true},{rir:true,rpe:true}]) {
      const label=width+"-"+Number(flags.rir)+Number(flags.rpe),backend=backendFixture();
      const {page,context}=await setup(browser,backend,width,width===1440?900:844);
      const errors=[];page.on("pageerror",e=>errors.push(e.message));
      await create(page,flags,label);await start(page);
      const original=JSON.stringify(backend.db.workout_sessions[0].metadata.effortTracking);
      await page.locator("[data-phase3-weight]").first().fill("55.5");
      await page.locator("[data-phase3-reps]").first().fill("8");
      if(flags.rir) await page.locator("[data-phase3-rir]").first().fill("0");
      if(flags.rpe) await page.locator("[data-phase3-rpe]").first().fill("9.5");
      await page.locator("[data-phase3-complete-set]").first().click();
      await page.waitForFunction(()=>Object.values(__trainingTest.state().activeSession.setLogs).some(s=>s.syncedAt));
      for(const theme of ["light","dark"]) {
        backend.s.settings.display.theme_mode=theme;
        await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(()=>__trainingTest.render());
        check(label+" theme "+theme,await page.locator("body").evaluate((n,t)=>n.classList.contains("light")===(t==="light"),theme));
        await measure(page,flags,label+"-"+theme);await shot(page,label+"-"+theme);
      }
      await enter(page);await page.evaluate(()=>__trainingTest.open());
      await measure(page,flags,label+"-reload");
      check(label+" snapshot untouched",JSON.stringify(backend.db.workout_sessions[0].metadata.effortTracking)===original);
      const log=backend.db.workout_set_logs[0];
      check(label+" separate values retained",log.rir===(flags.rir?0:null)&&log.rpe===(flags.rpe?9.5:null));
      check(label+" no JS errors",errors.length===0);
      await context.close();
    }
    if(!before) {
      const backend=backendFixture(),{page,context}=await setup(browser,backend,390,844);
      await create(page,{rir:false,rpe:false},"Timer");await start(page);
      check("optional timer absent",await page.locator(".tw-rest-panel").count()===0);
      await page.click("[data-phase3-timer-open]");await page.fill("[data-phase3-session-rest]","75");await page.click("[data-phase3-start-manual-rest]");
      const end=await page.evaluate(()=>__trainingTest.state().activeSession.focus.rest.endsAt);
      for(const theme of ["light","dark"]) {
        backend.s.settings.display.theme_mode=theme;await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(()=>__trainingTest.render());
        const g=await page.locator(".tw-timer-dial").evaluate(n=>{const r=n.getBoundingClientRect();return{w:r.width,h:r.height,x:r.x,y:r.y};});
        check("accepted timer "+theme+" unchanged",g.w===300&&g.h===300&&g.x===45&&g.y===272);await shot(page,"timer-"+theme);
      }
      await page.waitForFunction(()=>document.querySelector("[data-phase3-rest-countdown]")?.textContent!=="01:15",null,{timeout:5000});
      check("timer counts down",await page.locator("[data-phase3-rest-countdown]").textContent()!=="01:15");
      await page.click("[data-phase3-rest-view]");await page.click("[data-phase3-timer-open]");
      check("same running timer",await page.evaluate(e=>__trainingTest.state().activeSession.focus.rest.endsAt===e,end));
      await page.click("[data-phase3-stop-rest]");
      check("no set/completion from timer",await page.evaluate(()=>Object.keys(__trainingTest.state().activeSession.setLogs).length===0&&__trainingTest.state().activeSession.status==="active"));
      await context.close();
    }
    const output={mode,checks,geometry,screens,synthetic_backend_and_auth:true,physical_phone:false};
    fs.writeFileSync(path.join(root,"supabase/.temp/training-alignment-"+mode+".json"),JSON.stringify(output,null,2));
    console.log(JSON.stringify({mode,passed:checks.filter(c=>c.pass).length,failed:checks.filter(c=>!c.pass).length,checks:checks.length,screens:screens.length}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
