const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const runtime = fs.readFileSync(path.join(root, "assets/phase5-progress.js"), "utf8");
const appStyles = fs.readFileSync(path.join(root, "styles.css"), "utf8");
const checks = [];
function check(name, pass) { checks.push({ name, pass: Boolean(pass) }); }

function harness(language = "nl") {
  return `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body class="client-mode">
    <style>.view { display:none; padding:12px; } .view.active { display:block; }</style>
    <nav id="nav"></nav><main class="content"><section id="progress" class="view active"></section></main>
    <script>
      let state = { ui:{ loggedIn:true, role:"client" }, accountSettings:{ language:${JSON.stringify(language)}, unitSystem:"metric" } };
      let onlineProfile = { id:"11111111-1111-4111-8111-111111111111", role:"client" };
      let currentView = "progress";
      const NAV = { client:[["client-home","Vandaag"],["training","Training"],["nutrition","Voeding"],["trackers","Trackers"]], trainer:[] };
      function isLoggedIn(){ return state.ui.loggedIn; } function isOnlineMode(){ return true; }
      function renderProgress(){} function renderAll(){} function renderNav(){ document.getElementById("nav").textContent = NAV.client.map(x=>x[1]).join("|"); }
      const mock = { calls:[], unit:"metric", weight:84.2, archived:false };
      function payload(){
        return { access:"free", history_window_days:30, history_locked:false, timezone_name:"Europe/Amsterdam", unit_system:mock.unit, today:"2026-08-31", window_start:"2026-08-02", window_end:"2026-08-31",
          goal:{ id:"20000000-0000-4000-8000-000000000001", goal_code:"fat_loss", baseline_weight_kg:90, target_weight_kg:80, target_date:"2026-12-31", updated_at:"2026-08-31T10:00:00Z" },
          weights:mock.archived?[]:[
            { id:"30000000-0000-4000-8000-000000000001", log_date:"2026-08-24", weight_kg:85.1, trend_kg:85.1, updated_at:"2026-08-24T10:00:00Z" },
            { id:"30000000-0000-4000-8000-000000000002", log_date:"2026-08-31", weight_kg:mock.weight, trend_kg:84.65, updated_at:"2026-08-31T10:00:00Z" }
          ],
          measurements:[{ id:"40000000-0000-4000-8000-000000000001", log_date:"2026-08-31", waist_cm:90, chest_cm:104, hips_cm:99, upper_arm_left_cm:37, upper_arm_right_cm:37.5, thigh_left_cm:59, thigh_right_cm:59.5, updated_at:"2026-08-31T10:00:00Z" }],
          strength:[{ exercise_key:"bench", exercise_name:"Barbell Bench Press", max_weight_kg:100, max_reps:8, estimated_one_rep_max_kg:126.67, completed_sets:12 }],
          consistency:{ completed_sessions:9, last_7_days:2, last_30_days:9 },
          recovery_context:{ days_logged:5, average_sleep_hours:7.4, average_steps:9300, average_recovery_feeling:7.6 },
          nutrition_context:{ days_logged:6, average_energy_kcal:2210, average_protein_grams:146.5 },
          bmi_context:25.2, running:{ authoritative_source_available:false, activities:[] }
        };
      }
      const supabaseClient = { rpc: async(name,args) => {
        mock.calls.push({name,args});
        if(name === "fmz_phase5_get_progress_dashboard") return { data:payload(), error:null };
        if(name === "fmz_phase5_set_unit_system"){ mock.unit=args.p_unit_system; return {data:{unit_system:mock.unit},error:null}; }
        if(name === "fmz_phase5_save_weight_log"){ mock.weight=args.p_weight_kg; return {data:{id:args.p_request_id},error:null}; }
        if(name === "fmz_phase5_archive_weight_log"){ mock.archived=true; return {data:{status:"archived"},error:null}; }
        return { data:{}, error:null };
      }};
      window.confirm = () => true;
    </script></body></html>`;
}

async function initializePage(page, language = "nl") {
  await page.setContent(harness(language));
  await page.addStyleTag({ content: appStyles });
  await page.addScriptTag({ content: runtime });
  await page.evaluate(async () => { renderNav(); renderProgress(); await window.FMZ_PHASE5_PROGRESS.hydrate({force:true}); });
  await page.waitForSelector(".phase5-shell .phase5-chart");
}

async function inspectOpenForm(page, formType, expectedColumns) {
  await page.locator(`[data-phase5-open="${formType}"]`).click();
  await page.waitForSelector(`[data-phase5-form="${formType}"]`);
  const layout = await page.evaluate(({ formType, expectedColumns }) => {
    const form = document.querySelector(`[data-phase5-form="${formType}"]`);
    const sheet = form.closest(".phase5-sheet");
    const grid = form.querySelector(".phase5-form-grid");
    const fields = [...form.querySelectorAll("label.field")];
    const viewportWidth = document.documentElement.clientWidth;
    const sheetRect = sheet.getBoundingClientRect();
    const headingRect = sheet.querySelector("h2").getBoundingClientRect();
    const closeRect = sheet.querySelector(".phase5-close").getBoundingClientRect();
    const results = fields.map((field) => {
      const label = field.querySelector(":scope > span");
      const control = field.querySelector("input,select,textarea");
      const fieldRect = field.getBoundingClientRect();
      const labelRect = label.getBoundingClientRect();
      const controlRect = control.getBoundingClientRect();
      return {
        separated: labelRect.bottom <= controlRect.top + 0.5,
        gap: controlRect.top - labelRect.bottom,
        controlContained: controlRect.left >= fieldRect.left - 0.5 && controlRect.right <= fieldRect.right + 0.5,
        fieldContained: fieldRect.left >= sheetRect.left - 0.5 && fieldRect.right <= sheetRect.right + 0.5,
        touchHeight: controlRect.height,
        labelLineHeight: Number.parseFloat(getComputedStyle(label).lineHeight)
      };
    });
    const columns = getComputedStyle(grid).gridTemplateColumns.split(/\s+/).filter(Boolean).length;
    const actions = form.querySelector(".phase5-actions");
    const feedback = actions.querySelector(".save-feedback");
    feedback.textContent = "Controleer de ingevulde waarden voordat je opnieuw opslaat.";
    const buttonRect = actions.querySelector("button").getBoundingClientRect();
    const feedbackRect = feedback.getBoundingClientRect();
    const feedbackOverlaps = !(buttonRect.right <= feedbackRect.left || feedbackRect.right <= buttonRect.left || buttonRect.bottom <= feedbackRect.top || feedbackRect.bottom <= buttonRect.top);
    return {
      expectedColumns,
      columns,
      allSeparated: results.every((result) => result.separated && result.gap >= 5),
      allControlsContained: results.every((result) => result.controlContained && result.fieldContained),
      allTouchFriendly: results.every((result) => result.touchHeight >= 44),
      allLabelsReadable: results.every((result) => result.labelLineHeight >= 17),
      headingClear: headingRect.right <= closeRect.left + 0.5 || headingRect.bottom <= closeRect.top + 0.5,
      feedbackClear: !feedbackOverlaps,
      sheetContained: sheetRect.left >= -0.5 && sheetRect.right <= viewportWidth + 0.5 && sheet.scrollWidth <= sheet.clientWidth + 1,
      pageContained: document.documentElement.scrollWidth <= viewportWidth + 1
    };
  }, { formType, expectedColumns });
  await page.locator(`[data-phase5-form="${formType}"] input, [data-phase5-form="${formType}"] select`).first().focus();
  layout.focusVisible = await page.evaluate((formType) => {
    const control = document.querySelector(`[data-phase5-form="${formType}"] input, [data-phase5-form="${formType}"] select`);
    const style = getComputedStyle(control);
    return document.activeElement === control && style.outlineStyle !== "none" && Number.parseFloat(style.outlineWidth) >= 2;
  }, formType);
  await page.locator(".phase5-close").click();
  return layout;
}

async function checkFormsAtViewport(page, width, height, expectedColumns) {
  await page.setViewportSize({ width, height });
  const scenarios = ["goal", "weight", "measurement"];
  const results = [];
  for (const formType of scenarios) {
    results.push(await inspectOpenForm(page, formType, expectedColumns));
  }
  return {
    columns: results.every((result) => result.columns === result.expectedColumns),
    separated: results.every((result) => result.allSeparated),
    contained: results.every((result) => result.allControlsContained && result.sheetContained && result.pageContained),
    touch: results.every((result) => result.allTouchFriendly),
    readable: results.every((result) => result.allLabelsReadable),
    headings: results.every((result) => result.headingClear),
    feedback: results.every((result) => result.feedbackClear),
    focus: results.every((result) => result.focusVisible)
  };
}

async function inspectUnitSelector(page, width, height) {
  await page.setViewportSize({ width, height });
  return page.evaluate(() => {
    const fieldset = document.querySelector(".phase5-unit-setting");
    const buttons = [...fieldset.querySelectorAll("[data-phase5-unit]")];
    const rect = fieldset.getBoundingClientRect();
    return {
      visible: rect.width > 0 && rect.height > 0,
      contained: rect.left >= 0 && rect.right <= innerWidth && document.documentElement.scrollWidth <= innerWidth + 1,
      touch: buttons.every((button) => button.getBoundingClientRect().height >= 44),
      selected: buttons.filter((button) => button.getAttribute("aria-pressed") === "true").length === 1,
      labelled: Boolean(fieldset.querySelector("legend")?.textContent.trim()) && buttons.every((button) => button.textContent.trim()),
      feedback: fieldset.querySelector('[role="status"][aria-live="polite"]') !== null
    };
  });
}

(async () => {
  const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
  const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(edgePath) ? edgePath : undefined });
  try {
    const page = await browser.newPage({ viewport: { width:390, height:844 } });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await initializePage(page);

    check("runtime contract exposed", await page.evaluate(() => window.FMZ_PHASE5_PROGRESS.version === "20260901-phase5-unit-switch1"));
    check("Voortgang nav inserted", await page.locator("#nav").textContent().then((text) => text.includes("Voortgang") && !text.includes("Progressie")));
    check("Voortgang page title", await page.locator(".phase5-head h1").textContent().then((text) => text.trim() === "Voortgang"));
    check("goal first", await page.locator(".phase5-grid > section").first().textContent().then((text) => text.includes("Mijn doel")));
    check("weight chart rendered", await page.locator(".phase5-chart .raw").count() === 1 && await page.locator(".phase5-chart .trend").count() === 1);
    check("accessible chart label", Boolean(await page.locator(".phase5-chart").getAttribute("aria-label")));
    check("strength rendered", await page.getByText("Barbell Bench Press").count() === 1);
    check("truthful running empty state", await page.getByText(/betrouwbare hardloop/).count() === 1);
    check("photo gate no upload", await page.getByText("Progressiefoto's").count() === 1 && await page.locator('input[type="file"]').count() === 0);
    check("raw table alternative", await page.locator(".phase5-details .phase5-table").count() === 2);
    const initialSelector = await inspectUnitSelector(page, 390, 844);
    check("unit selector visible and labelled", initialSelector.visible && initialSelector.labelled && initialSelector.feedback);
    check("unit selector starts metric", await page.locator('[data-phase5-unit="metric"]').getAttribute("aria-pressed") === "true");

    const mobile390 = await checkFormsAtViewport(page, 390, 844, 1);
    check("390px forms single column", mobile390.columns);
    check("390px labels and inputs separated", mobile390.separated);
    check("390px forms contained without overflow", mobile390.contained);
    check("390px touch targets", mobile390.touch);
    check("390px labels readable", mobile390.readable);
    check("390px headings clear", mobile390.headings);
    check("390px feedback does not collide", mobile390.feedback);
    check("390px focus visible", mobile390.focus);

    const mobile320 = await checkFormsAtViewport(page, 320, 700, 1);
    check("320px forms single column", mobile320.columns);
    check("320px labels and inputs separated", mobile320.separated);
    check("320px forms contained without overflow", mobile320.contained);
    check("320px touch targets", mobile320.touch);
    check("320px labels readable", mobile320.readable);
    check("320px headings clear", mobile320.headings);
    check("320px feedback does not collide", mobile320.feedback);
    check("320px focus visible", mobile320.focus);

    await page.setViewportSize({ width:390, height:420 });
    await page.locator('[data-phase5-open="measurement"]').click();
    const keyboardLayout = await page.evaluate(() => {
      const textarea = document.querySelector('[data-phase5-form="measurement"] textarea');
      textarea.focus();
      textarea.scrollIntoView({ block:"center" });
      const rect = textarea.getBoundingClientRect();
      const sheet = textarea.closest(".phase5-sheet");
      return document.activeElement === textarea && rect.left >= 0 && rect.right <= innerWidth && rect.top >= 0 && rect.bottom <= innerHeight && sheet.scrollWidth <= sheet.clientWidth + 1;
    });
    check("reduced keyboard viewport remains stable", keyboardLayout);
    await page.keyboard.press("Escape");

    await page.setViewportSize({ width:390, height:844 });
    await page.locator('[data-phase5-open="weight"]').click();
    check("weight dialog semantic", await page.locator('.phase5-sheet[role="dialog"][aria-modal="true"]').count() === 1);
    await page.locator('[data-phase5-form="weight"] input[name="weight"]').fill("83.7");
    await page.locator('[data-phase5-form="weight"] button[type="submit"]').click();
    await page.waitForFunction(() => document.body.textContent.includes("83,7 kg"));
    check("weight save RPC", await page.evaluate(() => mock.calls.some((call) => call.name === "fmz_phase5_save_weight_log" && call.args.p_weight_kg === 83.7)));
    check("authoritative refresh after save", await page.evaluate(() => mock.calls.filter((call) => call.name === "fmz_phase5_get_progress_dashboard").length >= 2));

    await page.getByRole("button", { name:"Imperiaal" }).click();
    await page.waitForFunction(() => document.body.textContent.includes("lb"));
    check("unit RPC", await page.evaluate(() => mock.calls.some((call) => call.name === "fmz_phase5_set_unit_system" && call.args.p_unit_system === "imperial")));
    check("imperial display only", await page.getByText(/lb/).count() > 0 && await page.evaluate(() => mock.weight === 83.7));
    check("imperial selection and feedback", await page.locator('[data-phase5-unit="imperial"]').getAttribute("aria-pressed") === "true" && await page.locator("[data-phase5-unit-feedback]").textContent() === "Eenheden opgeslagen");
    check("global account setting synchronized", await page.evaluate(() => state.accountSettings.unitSystem === "imperial"));
    check("chart and strength converted", await page.locator(".phase5-chart").getAttribute("aria-label").then((label) => label.includes("lb")) && await page.getByText(/279,3 lb/).count() > 0);

    await page.locator(".phase5-details summary").click();
    await page.locator('[data-phase5-edit-weight="2026-08-31"]').click();
    const imperialWeightForm = await page.evaluate(() => ({
      label: document.querySelector('[data-phase5-form="weight"] input[name="weight"]')?.closest("label")?.textContent,
      value: document.querySelector('[data-phase5-form="weight"] input[name="weight"]')?.value
    }));
    check("imperial weight form", imperialWeightForm.label.includes("lb") && imperialWeightForm.value === "184.5");
    await page.locator(".phase5-close").click();
    await page.locator('[data-phase5-edit-measurement="2026-08-31"]').click();
    const imperialMeasurementForm = await page.evaluate(() => ({
      label: document.querySelector('[data-phase5-form="measurement"] input[name="waist_cm"]')?.closest("label")?.textContent,
      value: document.querySelector('[data-phase5-form="measurement"] input[name="waist_cm"]')?.value
    }));
    check("imperial measurement form", imperialMeasurementForm.label.includes("in") && imperialMeasurementForm.value === "35.4");
    await page.locator(".phase5-close").click();

    await page.evaluate(async () => {
      window.FMZ_PHASE5_PROGRESS.reset();
      renderProgress();
      await window.FMZ_PHASE5_PROGRESS.hydrate({ force:true });
    });
    await page.waitForFunction(() => document.querySelector('[data-phase5-unit="imperial"]')?.getAttribute("aria-pressed") === "true");
    check("unit preference persists after refresh hydration", await page.evaluate(() => mock.unit === "imperial" && state.accountSettings.unitSystem === "imperial"));

    for (let round = 0; round < 3; round += 1) {
      await page.locator('[data-phase5-unit="metric"]').click();
      await page.waitForFunction(() => document.querySelector('[data-phase5-unit="metric"]')?.getAttribute("aria-pressed") === "true");
      await page.locator('[data-phase5-unit="imperial"]').click();
      await page.waitForFunction(() => document.querySelector('[data-phase5-unit="imperial"]')?.getAttribute("aria-pressed") === "true");
    }
    check("repeated unit round trips preserve canonical kg", await page.evaluate(() => mock.weight === 83.7));

    await page.locator('[data-phase5-unit="metric"]').click();
    await page.waitForFunction(() => document.querySelector('[data-phase5-unit="metric"]')?.getAttribute("aria-pressed") === "true");
    check("metric round trip restores kg display", await page.getByText(/83,7 kg/).count() > 0 && await page.evaluate(() => mock.weight === 83.7));

    const selector320 = await inspectUnitSelector(page, 320, 700);
    check("320px unit selector", selector320.visible && selector320.contained && selector320.touch && selector320.selected);
    const selector390 = await inspectUnitSelector(page, 390, 844);
    check("390px unit selector", selector390.visible && selector390.contained && selector390.touch && selector390.selected);

    const tablet = await checkFormsAtViewport(page, 820, 1180, 2);
    check("tablet forms use bounded two-column layout", tablet.columns && tablet.separated && tablet.contained && tablet.touch && tablet.headings && tablet.feedback);
    const selectorTablet = await inspectUnitSelector(page, 820, 1180);
    check("tablet unit selector", selectorTablet.visible && selectorTablet.contained && selectorTablet.touch && selectorTablet.selected);
    const desktop = await checkFormsAtViewport(page, 1440, 900, 2);
    check("desktop forms use bounded two-column layout", desktop.columns && desktop.separated && desktop.contained && desktop.touch && desktop.headings && desktop.feedback);
    const selectorDesktop = await inspectUnitSelector(page, 1440, 900);
    check("desktop unit selector", selectorDesktop.visible && selectorDesktop.contained && selectorDesktop.touch && selectorDesktop.selected);

    for (const [language, expected] of [["en","Progress"],["de","Fortschritt"]]) {
      const localePage = await browser.newPage({ viewport: { width:390, height:844 } });
      await initializePage(localePage, language);
      const localeResult = await localePage.evaluate(() => ({ nav:document.getElementById("nav").textContent, title:document.querySelector(".phase5-head h1")?.textContent }));
      check(`${language.toUpperCase()} section label preserved`, localeResult.nav.includes(expected) && localeResult.title === expected);
      check(`${language.toUpperCase()} unit selector localized`, await localePage.locator(".phase5-unit-setting").textContent().then((text) => language === "en" ? text.includes("Metric") && text.includes("Imperial") : text.includes("Metrisch") && text.includes("Imperial")));
      await localePage.close();
    }

    check("no runtime errors", errors.length === 0);
  } finally {
    await browser.close();
  }
  const failed = checks.filter((item) => !item.pass);
  console.log(JSON.stringify({ scope:"phase5_progress_browser", pass_count:checks.length-failed.length, fail_count:failed.length, overall_pass:failed.length===0, failed }, null, 2));
  if (failed.length) process.exit(1);
})().catch((error) => { console.error(error); process.exit(1); });
