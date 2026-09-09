const assert=require("node:assert/strict");
async function large(page,width,{check,geometry,screenshot}){
 const state=()=>page.evaluate(()=>__trainingTest.state().activeSession);
 check(width+" Start opens large circular timer",await page.locator(".tw-timer-dial").isVisible()&&(await state()).focus.rest.expanded);
 const first=await page.locator("[data-phase3-rest-countdown]").textContent();
 const fraction=()=>page.locator("[data-phase3-rest-ring]").evaluate(n=>Number(n.style.getPropertyValue("--rest-progress")));
 const initial=await fraction();await page.waitForTimeout(2200);
 check(width+" real countdown and ring decrease",await fraction()<initial&&await page.locator("[data-phase3-rest-countdown]").textContent()!==first);
 const circle=await page.locator(".tw-timer-dial").boundingBox();
 check(width+" large round dial, no tiny preview",circle.width>=280&&Math.abs(circle.width-circle.height)<1);
 await geometry(page,width+" circular timer",".tw-focus");await screenshot(page,width+"-circle-running");
 const portrait=page.viewportSize();await page.setViewportSize({width:844,height:390});
 check(width+" landscape ring fully framed",await page.locator(".tw-timer-dial").evaluate(n=>{const b=n.getBoundingClientRect(),p=n.closest("main").getBoundingClientRect();return Math.abs(b.width-b.height)<1&&b.top>=p.top&&b.bottom<=p.bottom;}));
 await geometry(page,width+" landscape timer",".tw-focus");await screenshot(page,width+"-circle-landscape");await page.setViewportSize(portrait);
 await page.locator("[data-phase3-stop-rest]").focus();await page.keyboard.press("Tab");
 check(width+" large timer keyboard stays in dialog",await page.locator("[data-phase3-rest-view]").evaluate(n=>n===document.activeElement));
 await page.click("[data-phase3-rest-view]");
 check(width+" minimize exposes editable sets without stopping",await page.locator(".tw-live-sets").isVisible()&&!(await state()).focus.rest.expanded);
 const end=(await state()).focus.rest.endsAt;
 await page.locator("[data-phase3-reps]").nth(1).fill("9");
 await page.click("[data-phase3-timer-open]");
 check(width+" reopen same running deadline",(await state()).focus.rest.endsAt===end&&await page.locator(".tw-timer-dial").isVisible());
 await page.click("[data-phase3-rest-pause]");const paused=await fraction();await page.waitForTimeout(1100);
 check(width+" paused circle stays still and control retains focus",await fraction()===paused&&await page.locator("[data-phase3-rest-pause]").evaluate(n=>n===document.activeElement));
 const before=(await state()).focus.rest.remainingMs;await page.click("[data-phase3-add-rest]");
 check(width+" paused +15 updates duration and ring",(await state()).focus.rest.remainingMs===before+15000&&(await state()).focus.rest.durationSeconds===90&&await fraction()>paused);
 await screenshot(page,width+"-circle-paused");
 const pausedMs=(await state()).focus.rest.remainingMs;
 await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));await page.evaluate(()=>__trainingTest.open());
 check(width+" large paused view survives refresh exactly",await page.locator(".tw-timer-dial").isVisible()&&(await state()).focus.rest.remainingMs===pausedMs&&(await state()).focus.rest.paused);
 await page.click("[data-phase3-rest-pause]");await page.keyboard.press("Escape");
 check(width+" Escape minimizes without stopping",await page.locator(".tw-live-sets").isVisible()&&!!(await state()).focus.rest);
}
async function effort(page,width,backend,{check,geometry,screenshot}){
 const get=()=>page.evaluate(()=>FMZ_TRAINING.preferences());
 const choose=async mode=>{await page.locator('label:has([data-phase3-effort-mode="'+mode+'"])').click();await page.waitForFunction(mode=>FMZ_TRAINING.preferences().effort_mode===mode,mode);};
 check(width+" effort selector immediately precedes sets",await page.locator(".tw-live-sets").evaluate(n=>n.previousElementSibling.id==="phase3-effort-help"&&n.previousElementSibling.previousElementSibling.classList.contains("tw-effort-choice")));
 await choose("rir");await page.locator("[data-phase3-rir]").first().fill("0");
 await choose("rpe");check(width+" visible RPE explanation",await page.locator("#phase3-effort-help").textContent().then(t=>t.includes("1 tot 10")));
 await page.locator("[data-phase3-rpe]").first().fill("9.5");
 await choose("none");check(width+" None hides only optional effort column",await page.locator("[data-phase3-rir],[data-phase3-rpe]").count()===0);
 await choose("rir");check(width+" RIR 0 preserved after RPE and None",await page.locator("[data-phase3-rir]").first().inputValue()==="0");
 await choose("rpe");check(width+" RPE 9.5 preserved without conversion",await page.locator("[data-phase3-rpe]").first().inputValue()==="9.5");
 check(width+" one authoritative settings preference",backend.pref.effort_mode==="rpe"&&(await get()).effort_mode==="rpe");
 await geometry(page,width+" effort selector",".tw-focus");await screenshot(page,width+"-effort-rpe");
 backend.failPreferences=true;await page.locator('label:has([data-phase3-effort-mode="rir"])').click();
 await page.waitForFunction(()=>!document.querySelector(".tw-effort-choice")?.disabled&&document.querySelector('[data-phase3-effort-mode="rpe"]')?.checked&&document.querySelector(".tw-feedback")?.textContent).catch(async e=>{
  console.log("preference failure diagnostic",backend.pref,backend.failPreferences,await page.locator(".tw-focus").innerText());throw e;
 });
 check(width+" failed preference shows original RPE without data loss",(await get()).effort_mode==="rpe"&&await page.locator("[data-phase3-rpe]").first().inputValue()==="9.5"&&await page.locator('[data-phase3-effort-mode="rpe"]').isChecked());
 await page.click("[data-phase3-close-focus]");await page.evaluate(()=>FMZ_OWNER_SETTINGS.open("training"));
 check(width+" in-workout choice visible in Settings",await page.locator('#fmz-settings [name="training_effort_mode"][value="rpe"]').isChecked());
 await page.locator('#fmz-settings [name="training_effort_mode"][value="none"]').check();
 await page.waitForFunction(()=>FMZ_TRAINING.preferences().effort_mode==="none");await page.click("#fmz-settings [data-fmz-close]");await page.evaluate(()=>__trainingTest.open());
 check(width+" Settings change reflected above active sets",await page.locator('[data-phase3-effort-mode="none"]').isChecked()&&await page.locator("[data-phase3-rpe],[data-phase3-rir]").count()===0);
 await choose("rpe");
 check(width+" Settings switch also retains RPE",await page.locator("[data-phase3-rpe]").first().inputValue()==="9.5");
 await choose("rir");
}
async function themeAndExpiry(page,width,backend,{check,geometry,screenshot}){
 for(const theme of ["light","dark"]){
  backend.s.settings.display.theme_mode=theme;await page.emulateMedia({colorScheme:theme});await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(()=>__trainingTest.render());
  await page.click("[data-phase3-start-manual-rest]");
  await geometry(page,width+" "+theme+" circle",".tw-focus");await screenshot(page,width+"-circle-"+theme);
  const controls=await page.locator(".tw-timer-actions button").evaluateAll(ns=>ns.map(n=>{const b=n.getBoundingClientRect();return {h:b.height,w:b.width,bottom:b.bottom,text:n.textContent};}));
  check(width+" "+theme+" timer controls reachable",controls.length===3&&controls.every(b=>b.h>=44&&b.w>=44&&b.bottom<=page.viewportSize().height));
  await page.click("[data-phase3-stop-rest]");
  check(width+" stop leaves workout and timer opt-in intact",await page.evaluate(()=>{const s=__trainingTest.state().activeSession;return s.status==="active"&&!s.focus.rest&&s.focus.timerEnabled&&Object.keys(s.setLogs).length===0;}));
 }
 await page.fill("[data-phase3-session-rest]","2");await page.click("[data-phase3-start-manual-rest]");
 await page.waitForFunction(()=>!__trainingTest.state().activeSession.focus.rest);
 check(width+" real expiry returns to sets, no set/completion",await page.locator(".tw-live-sets").isVisible()&&await page.evaluate(()=>{const s=__trainingTest.state().activeSession;return s.status==="active"&&Object.keys(s.setLogs).length===0&&!s.focus.allExercisesCompleted;}));
}
module.exports={large,effort,themeAndExpiry};
