const assert=require("node:assert/strict");
async function basics(page,width,{check,geometry,screenshot},language="nl"){
 const info=await page.locator(".tw-basics").evaluate(section=>{
  const inputs=[...section.querySelectorAll("[data-tw-select]")],main=section.closest("main"),heading=section.querySelector("h3").getBoundingClientRect();
  return {ids:inputs.map(n=>n.dataset.twSelect),head:section.querySelector("h3").textContent,visible:heading.top>=main.getBoundingClientRect().top&&heading.bottom<=main.getBoundingClientRect().bottom,
   groups:section.querySelectorAll("h4").length,extra:section.querySelectorAll("[data-tw-action=more],details").length,
   images:[...section.querySelectorAll("img")].every(n=>n.complete&&n.naturalWidth>0)};
 });
 check(width+" 35 expanded basics in six groups",info.ids.length===35&&info.groups===6&&info.extra===0);
 check(width+" basic heading initially visible",info.visible&&info.head===({nl:"Basisoefeningen",en:"Basic exercises",de:"Grunduebungen"})[language]);
 check(width+" exact first/last basic and no duplicate identity",info.ids[0]==="bfcda5e1-5a31-551b-ab00-a34e1d51d9be"&&info.ids.at(-1)==="300b0022-6c14-5b99-91fb-9f5bb49ce3e5"&&new Set(info.ids).size===35);
 const all=await page.locator("[data-tw-select]").evaluateAll(ns=>ns.map(n=>n.dataset.twSelect));
 check(width+" basics not repeated in remainder",all.length===new Set(all).size);
 await page.locator(".tw-basics [data-tw-select]").last().scrollIntoViewIfNeeded();
 check(width+" final basic reachable by plain vertical scrolling",await page.locator(".tw-basics [data-tw-select]").last().isVisible());
 await page.locator("#fmz-workout-maker main").evaluate(n=>n.scrollTop=0);
 await page.waitForFunction(()=>[...document.querySelectorAll(".tw-basics img")].every(n=>n.complete&&n.naturalWidth>0));
 await geometry(page,width+" basic list","#fmz-workout-maker");await screenshot(page,width+"-basics");
 const pecDeck="065131ba-6d12-53f9-a737-6b501bda164f";
 await page.locator('[data-tw-select="'+pecDeck+'"]').check();
 await page.fill('[data-tw-filter="search"]',"pec deck");
 check(width+" familiar alias searches whole catalog",await page.locator('[data-tw-select="'+pecDeck+'"]').isChecked()&&await page.locator('[data-tw-select="e7669f95-1624-5f4a-a5ab-08fc82e15208"]').count()===1);
 await page.click('[data-tw-action="info"][data-tw-index="'+pecDeck+'"]');
 check(width+" basic name consistent in details",await page.locator("#fmz-workout-maker h2").textContent()===(language==="de"?"Butterfly (Maschine)":"Pec deck"));
 await page.click('[data-tw-action="back"]');
 check(width+" basic selection/search retained from details",await page.inputValue('[data-tw-filter="search"]')==="pec deck"&&await page.locator('[data-tw-select="'+pecDeck+'"]').isChecked());
 await page.fill('[data-tw-filter="search"]',"");await page.locator('[data-tw-select="'+pecDeck+'"]').uncheck();
 await page.locator("#fmz-workout-maker main").evaluate(n=>n.scrollTop=0);
}
async function manualTimer(page,width,{check,geometry,screenshot}){
 const state=()=>page.evaluate(()=>__trainingTest.state().activeSession);
 check(width+" new workout has no timer panel/activity",(await page.locator(".tw-rest-panel").count())===0&&!(await state()).focus.timerEnabled&&!(await state()).focus.rest);
 await page.locator("[data-phase3-reps]").nth(1).fill("9");
 await page.click("[data-phase3-timer-open]");await page.click("[data-phase3-timer-open]");
 check(width+" explicit open before set registration",(await page.locator(".tw-rest-panel").count())===1&&(await state()).focus.timerEnabled&&!(await state()).focus.rest&&Object.keys((await state()).setLogs).length===0);
 await page.fill("[data-phase3-session-rest]","75");
 await page.locator("[data-phase3-start-manual-rest]").dblclick({force:true});
 await page.waitForSelector("[data-phase3-rest-countdown]");
 check(width+" manual double start one countdown without sets",(await state()).focus.rest.durationSeconds===75&&(await state()).focus.rest.manual===true&&Object.keys((await state()).setLogs).length===0&&await page.locator("[data-phase3-rest-countdown]").count()===1);
 await require("./timer-review-browser.cjs").large(page,width,{check,geometry,screenshot});
 const deadline=(await state()).focus.rest.endsAt;
 await page.click("[data-phase3-close-focus]");await page.evaluate(()=>__trainingTest.open());
 check(width+" close/reopen retains live manual timer",(await state()).focus.rest.endsAt===deadline);
 await page.click("[data-phase3-rest-pause]");
 await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));await page.evaluate(()=>__trainingTest.open());
 check(width+" manual timer choice and pause survive refresh",(await state()).focus.timerEnabled&&(await state()).focus.rest.paused);
 const remaining=(await state()).focus.rest.remainingMs;
 await page.click("[data-phase3-add-rest]");check(width+" manual +15 retained",(await state()).focus.rest.remainingMs===remaining+15000);
 await page.click("[data-phase3-rest-pause]");
 await page.locator(".tw-focus main").evaluate(n=>n.scrollTop=0);
 await geometry(page,width+" timer panel",".tw-focus");await screenshot(page,width+"-timer");
 await page.click("[data-phase3-skip-rest]");
 check(width+" manual skip does not advance/complete",(await state()).focus.currentExerciseIndex===0&&(await state()).focus.currentSetIndex===1&&!(await state()).focus.allExercisesCompleted&&!(await state()).focus.rest);
 await page.click("[data-phase3-start-manual-rest]");await page.click("[data-phase3-rest-view]");await page.click("[data-phase3-timer-off]");
 check(width+" off stops and removes panel",(await page.locator(".tw-rest-panel").count())===0&&!(await state()).focus.timerEnabled&&!(await state()).focus.rest);
 check(width+" timer controls retain set draft",await page.locator("[data-phase3-reps]").nth(1).inputValue()==="9");
 await page.reload();await page.waitForFunction(()=>window.__hotfix);await page.evaluate(()=>__hotfix.enter());await page.evaluate(()=>__trainingTest.hydrate());await page.evaluate(()=>__hotfix.view("training"));await page.evaluate(()=>__trainingTest.open());
 check(width+" explicit off survives refresh",(await page.locator(".tw-rest-panel").count())===0&&!(await state()).focus.rest);
 // Enable automatic rest only after the explicit click; restore this fixture's group duration.
 await page.click("[data-phase3-timer-open]");await page.fill("[data-phase3-session-rest]","120");await page.locator("[data-phase3-session-rest]").blur();
}
async function rowGeometry(page,label,{check}){
 const g=await page.locator(".tw-live-set").first().evaluate(row=>{
  const fields=[row.querySelector(".tw-set-no"),row.querySelector(".tw-previous"),...row.querySelectorAll("input"),row.querySelector(".tw-set-save")];
  const boxes=fields.map(n=>{const b=n.getBoundingClientRect();return{x:b.x,y:b.y,w:b.width,h:b.height,center:b.y+b.height/2};});
  const canvas=document.createElement("canvas").getContext("2d");
  const inputs=[...row.querySelectorAll("input")].map(n=>{const s=getComputedStyle(n);canvas.font=s.font;return{size:parseFloat(s.fontSize),fits:canvas.measureText(n.value||n.placeholder).width<=n.clientWidth-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)+1,label:!!n.getAttribute("aria-label")};});
  const heads=row.parentElement.querySelectorAll(".tw-set-headings");
  return{boxes,inputs,headings:heads.length,columns:heads[0]?.children.length,overflow:getComputedStyle(row).overflowX};
 });
 check(label+" all fields same horizontal row",Math.max(...g.boxes.map(b=>b.center))-Math.min(...g.boxes.map(b=>b.center))<1&&g.boxes.every((b,i)=>i===0||b.x>=g.boxes[i-1].x+g.boxes[i-1].w-1));
 check(label+" one header per column, readable full values",g.headings===1&&g.columns===g.boxes.length&&g.inputs.every(i=>i.size>=12&&i.fits&&i.label));
 check(label+" tap targets and no hidden row overflow",g.boxes.at(-1).h>=44&&g.boxes.at(-1).w>=44&&g.overflow==="visible");
}
async function executionMatrix(page,width,height,backend,{check,geometry,screenshot}){
 const context=page.context();
 for(const language of ["nl","en","de"])for(const theme of ["light","dark"]){
  backend.s.settings.language=language;backend.s.settings.display.theme_mode=theme;backend.s.settings.unit_system=language==="en"?"imperial":"metric";
  await page.emulateMedia({colorScheme:theme});await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(()=>__trainingTest.render());
  // All fixture modifications below are local synthetic state, never live database calls.
  await page.evaluate(()=>{const s=__trainingTest.state();const h=s.history.find(h=>h.sets?.length);if(h){h.sets[0].actualWeight=1234.56;h.sets[0].actualReps=999;h.sets[0].actual_weight=1234.56;h.sets[0].actual_reps=999;}__trainingTest.render();});
  check(width+" "+language+" "+theme+" full previous fixture",await page.locator(".tw-previous").first().textContent().then(t=>t.includes("999")&&t.includes(language==="en"?"2721.74":"1234.56")));
  for(const mode of ["rir","rpe","none"]){
   await page.locator('label:has([data-phase3-effort-mode="'+mode+'"])').click();await page.waitForFunction(mode=>FMZ_TRAINING.preferences().effort_mode===mode,mode);
   await page.locator("[data-phase3-weight]").first().fill(language==="en"?"22046.22":"9999.99");
   await page.locator("[data-phase3-reps]").first().fill("999");
   if(mode!=="none")await page.locator("[data-phase3-"+mode+"]").first().fill(mode==="rir"?"0":"9.5");
   await rowGeometry(page,width+" "+language+" "+theme+" "+mode,{check});
   check(width+" "+language+" "+theme+" "+mode+" exact zero/blank",mode==="none"?await page.locator(".tw-effort").count()===0:await page.locator("[data-phase3-"+mode+"]").nth(2).inputValue()==="");
  }
  await page.evaluate(()=>FMZ_TRAINING.setPreferences({effort_mode:"rir"}));
  await page.locator("[data-phase3-weight]").first().fill(language==="en"?"110.23":"50");
  await page.locator("[data-phase3-reps]").first().fill("8");
  await page.locator("[data-phase3-rir]").first().fill("0");
  await page.locator(".tw-focus main").evaluate(n=>n.scrollTop=0);
  await geometry(page,width+" "+language+" "+theme+" execution",".tw-focus");
  await screenshot(page,width+"-"+language+"-"+theme+"-sets");
  if(width<1000){
   // Desktop automation cannot open an OS phone keyboard. Model its reduced visual viewport.
   await page.setViewportSize({width,height:Math.min(400,height-260)});
   await page.locator("[data-phase3-reps]").first().focus();await page.keyboard.press("ControlOrMeta+A");await page.keyboard.type("12");
   check(width+" "+language+" "+theme+" keyboard input",await page.locator("[data-phase3-reps]").first().inputValue()==="12"&&await page.locator("[data-phase3-reps]").first().evaluate(n=>document.activeElement===n&&n.getBoundingClientRect().bottom<=innerHeight));
   await rowGeometry(page,width+" "+language+" "+theme+" keyboard",{check});await geometry(page,width+" "+language+" "+theme+" keyboard",".tw-focus");
   if(language==="nl"&&theme==="light")await screenshot(page,width+"-keyboard");
   await page.locator("[data-phase3-reps]").first().blur();await page.setViewportSize({width,height});
  }
 }
 backend.s.settings.language="nl";backend.s.settings.display.theme_mode="light";backend.s.settings.unit_system="imperial";
 await page.emulateMedia({colorScheme:"light"});await page.evaluate(()=>FMZ_OWNER_SETTINGS.hydrate(true));await page.evaluate(()=>__trainingTest.render());
 await page.locator("[data-phase3-weight]").first().fill("");await page.locator("[data-phase3-rir]").first().fill("");
 check(width+" optional clears retained",await page.locator("[data-phase3-weight]").first().inputValue()===""&&await page.locator("[data-phase3-rir]").first().inputValue()==="");
 await page.click("[data-phase3-timer-open]");await page.click("[data-phase3-start-manual-rest]");
 await page.locator(".tw-focus main").evaluate(n=>n.scrollTop=0);await screenshot(page,width+"-timer");
 await page.click("[data-phase3-rest-view]");await page.click("[data-phase3-timer-off]");
 assert((await context.pages()).length>=1);
}
module.exports={basics,manualTimer,rowGeometry,executionMatrix};
