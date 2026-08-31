const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const runtime = fs.readFileSync(path.join(root, "assets/phase5-progress.js"), "utf8");
const checks = [];
function check(name, pass) { checks.push({ name, pass: Boolean(pass) }); }

function harness() {
  return `
    <style>
      :root { --line:#36404a; --surface:#1c2228; --bg:#12161a; --text:#f5f5f5; --muted:#a9b0b7; --gold:#d7b24d; }
      * { box-sizing:border-box; } body { margin:0; background:var(--bg); color:var(--text); font:14px Arial; }
      button,input,select,textarea { font:inherit; } button { border:1px solid var(--line); color:var(--text); background:#242b31; border-radius:6px; padding:8px 12px; }
      .primary-btn { background:#d7b24d; color:#17120a; } .secondary-btn { background:#242b31; }
      .field { display:grid; gap:5px; } input,select,textarea { width:100%; min-width:0; padding:10px; border:1px solid var(--line); background:#101418; color:var(--text); }
      .muted { color:var(--muted); } .view { display:none; padding:12px; } .view.active { display:block; }
    </style>
    <nav id="nav"></nav><section id="progress" class="view active"></section>
    <script>
      let state = { ui:{ loggedIn:true, role:"client" }, accountSettings:{ language:"nl", unitSystem:"metric" } };
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
    </script>`;
}

(async () => {
  const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
  const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(edgePath) ? edgePath : undefined });
  try {
    const page = await browser.newPage({ viewport: { width:390, height:844 } });
    await page.setContent(harness());
    await page.addScriptTag({ content: runtime });
    await page.evaluate(async () => { renderNav(); renderProgress(); await window.FMZ_PHASE5_PROGRESS.hydrate({force:true}); });
    await page.waitForSelector(".phase5-shell .phase5-chart");

    check("runtime contract exposed", await page.evaluate(() => window.FMZ_PHASE5_PROGRESS.version === "20260831-phase5-progress1"));
    check("Progress nav inserted", await page.locator("#nav").textContent().then((text) => text.includes("Progressie")));
    check("goal first", await page.locator(".phase5-grid > section").first().textContent().then((text) => text.includes("Mijn doel")));
    check("weight chart rendered", await page.locator(".phase5-chart .raw").count() === 1 && await page.locator(".phase5-chart .trend").count() === 1);
    check("accessible chart label", Boolean(await page.locator(".phase5-chart").getAttribute("aria-label")));
    check("strength rendered", await page.getByText("Barbell Bench Press").count() === 1);
    check("truthful running empty state", await page.getByText(/betrouwbare hardloop/).count() === 1);
    check("photo gate no upload", await page.getByText("Progressiefoto's").count() === 1 && await page.locator('input[type="file"]').count() === 0);
    check("raw table alternative", await page.locator(".phase5-details .phase5-table").count() === 2);

    const width390 = await page.evaluate(() => ({ scroll:document.documentElement.scrollWidth, client:document.documentElement.clientWidth }));
    check("390px no horizontal overflow", width390.scroll <= width390.client + 1);
    await page.setViewportSize({ width:320, height:700 });
    const width320 = await page.evaluate(() => ({ scroll:document.documentElement.scrollWidth, client:document.documentElement.clientWidth }));
    check("320px no horizontal overflow", width320.scroll <= width320.client + 1);

    await page.getByRole("button", { name:/Gewicht corrigeren/ }).click();
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

    await page.setViewportSize({ width:820, height:1180 });
    const tablet = await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
    check("tablet no overflow", tablet);
    await page.setViewportSize({ width:1440, height:900 });
    const desktop = await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
    check("desktop no overflow", desktop);

    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    check("no runtime errors", errors.length === 0);
  } finally {
    await browser.close();
  }
  const failed = checks.filter((item) => !item.pass);
  console.log(JSON.stringify({ scope:"phase5_progress_browser", pass_count:checks.length-failed.length, fail_count:failed.length, overall_pass:failed.length===0, failed }, null, 2));
  if (failed.length) process.exit(1);
})().catch((error) => { console.error(error); process.exit(1); });
