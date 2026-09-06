const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const runtime = fs.readFileSync(path.join(root, "assets/phase6c-private-ai-chat.js"), "utf8");
const checks = [];
const check = (name, pass) => checks.push({ name, pass: Boolean(pass) });

async function runViewport(browser, width, height) {
  const page = await browser.newPage({ viewport: { width, height } });
  await page.setContent('<!doctype html><html><head><base href="https://yourizorge.github.io/fitmetzorge-staging/"><style>:root{--line:#333;--surface:#181818;--panel:#222;--muted:#aaa;--text:#fff;--gold:#d7b24d;--shadow:0 12px 32px rgba(0,0,0,.35)}*{box-sizing:border-box}body{margin:0;background:#111;color:#fff;font:16px Arial}.view{display:none}.view.active{display:block}.primary-btn,.secondary-btn,button,input,textarea,select{font:inherit;color:inherit;background:#222;border:1px solid #555;border-radius:6px;padding:8px}.sr-only{position:absolute;clip:rect(0,0,0,0)}</style></head><body><nav id="nav"></nav><section id="ai-coach" class="view active"></section></body></html>');
  const harness = `
    const NAV={client:[["client-home","Vandaag"]],trainer:[["trainer-dashboard","Dashboard"]]};let currentView="ai-coach";
    const state={ui:{loggedIn:true,role:"client"},accountSettings:{language:"nl"}};const onlineProfile={role:"client",id:"10000000-0000-4000-8000-000000000010"};
    const isLoggedIn=()=>state.ui.loggedIn;let renderNav=()=>{};let renderAll=()=>{};const FMZ_CONFIG={SUPABASE_URL:"https://mokxyyullfhkfalopbzd.supabase.co",SUPABASE_ANON_KEY:"publishable-test"};
    window.__threads=[{id:"10000000-0000-4000-8000-000000000020",locale:"nl",status:"active",retention_state:"active",revision:1,last_message_sequence:0,created_at:"2026-09-04T08:00:00Z",updated_at:"2026-09-04T08:00:00Z",last_message:null,processing_status:"completed"}];
    window.__messages=[];
    window.__status={chat_write_allowed:true,deny_reason:"allowed",entitlement_code:"ai",consent_state:"granted",age_eligible:true,safety_status:"clear",mock_mode:true,external_ai_enabled:false,external_ai_calls:0,external_ai_cost_eur:0,conversation_count:1};
    window.__consent={contracts:[{consent_kind:"ai_processing",document_version:"phase6a-ai-processing-v1",content_text:"Ik begrijp dat mijn gegevens in deze beveiligde stagingtest worden verwerkt."}],current:{ai_processing:{consent_state:"granted"}}};
    window.__analysisConsent={contracts:[{consent_kind:"ai_analysis",document_version:"phase6d-analysis-v1",content_text:"Ik geef expliciet toestemming voor read-only AI-analyses in staging."}],current:{ai_analysis:{consent_state:"granted",document_active:true}}};
    window.__analysisStatus={schema_version:"phase6d.status.v1",preferences:{timezone_name:"Europe/Amsterdam",daily_enabled:true,daily_time:"07:30",post_workout_enabled:true,weekly_enabled:true,weekly_day:1,weekly_time:"08:00",revision:1},contract:window.__analysisConsent,kinds:{daily:{analysis_allowed:true,deny_reason:"allowed",model_tier:"luna",safety_status:"clear",budget:{fair_use_status:"normal"}},post_workout:{analysis_allowed:true,deny_reason:"allowed",model_tier:"luna",safety_status:"clear",budget:{fair_use_status:"normal"}},weekly:{analysis_allowed:true,deny_reason:"allowed",model_tier:"terra",safety_status:"clear",budget:{fair_use_status:"normal"}}},latest_completed_workout:{id:"10000000-0000-4000-8000-000000000030",title:"Upper body",completed_at:"2026-09-04T09:00:00Z"}};
    window.__analysisResults=[{id:"10000000-0000-4000-8000-000000000040",analysis_kind:"daily",status:"ready",summary:"Je daganalyse is klaar.",quality:{level:"sufficient"},model_tier:"luna",adapter_code:"mock",created_at:"2026-09-04T10:00:00Z",revision:2}];
    const supabaseClient={auth:{getSession:async()=>({data:{session:{access_token:"test-token"}}})},rpc:async(name,args)=>{window.__rpcCalls=(window.__rpcCalls||[]).concat([{name,args}]);if(name==="fmz_phase6c_get_chat_status")return{data:window.__status};if(name==="fmz_phase6a_read_consent_contract")return{data:window.__consent};if(name==="fmz_phase6c_list_threads")return{data:{threads:window.__threads}};if(name==="fmz_phase6c_read_thread")return{data:{thread:window.__threads[0],messages:window.__messages}};if(name==="fmz_phase6d_get_status")return{data:window.__analysisStatus};if(name==="fmz_phase6d_read_analysis_contract")return{data:window.__analysisConsent};if(name==="fmz_phase6d_list_analyses")return{data:{results:window.__analysisResults}};if(name==="fmz_phase6d_record_analysis_consent"){window.__analysisConsent.current.ai_analysis.consent_state=args.p_action;return{data:{replay:false}};}if(name==="fmz_phase6d_update_preferences"){window.__analysisStatus.preferences={...window.__analysisStatus.preferences,timezone_name:args.p_timezone_name,daily_time:args.p_daily_time,weekly_day:args.p_weekly_day,weekly_time:args.p_weekly_time,revision:2};return{data:window.__analysisStatus.preferences};}if(name==="fmz_phase6d_export_analyses")return{data:{schema_version:"phase6d.analysis-export.v1",analyses:window.__analysisResults}};if(name==="fmz_phase6d_delete_analysis"){window.__analysisResults=window.__analysisResults.map(item=>item.id===args.p_result_id?{...item,status:"deleted",summary:null,revision:item.revision+1}:item);return{data:{deleted:true}};}return{data:{}};}};
    window.fetch=async(_url,options)=>{window.__edgeBody=JSON.parse(options.body);window.__analysisResults.unshift({id:"10000000-0000-4000-8000-000000000041",analysis_kind:window.__edgeBody.analysis_kind,status:"ready",summary:"Nieuwe analyse opgeslagen.",quality:{level:"sufficient"},model_tier:window.__edgeBody.analysis_kind==="weekly"?"terra":"luna",adapter_code:"mock",created_at:new Date().toISOString(),revision:1});return new Response(JSON.stringify({mode:"deterministic_mock",external_ai_calls:0,external_ai_cost_eur:0,result_id:"10000000-0000-4000-8000-000000000041"}),{status:200,headers:{"Content-Type":"application/json"}});};
    URL.createObjectURL=()=>"blob:test";URL.revokeObjectURL=()=>{};HTMLAnchorElement.prototype.click=()=>{};window.confirm=()=>true;
  `;
  await page.addScriptTag({ content: `${harness}\n${runtime}\nrenderAll();` });
  await page.evaluate(() => window.FMZ_PHASE6C_PRIVATE_CHAT.hydrate({ force: true }));
  await page.click('[data-p6c-tab="analyses"]');
  await page.waitForSelector(".p6d-grid");
  const initial = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth > innerWidth,
    title: document.querySelector(".p6c-head h1")?.textContent,
    tabs: [...document.querySelectorAll(".p6c-tab")].map((node) => node.textContent),
    cards: document.querySelectorAll(".p6d-card").length,
    results: document.querySelectorAll(".p6d-result").length,
    terra: document.body.textContent.includes("terra"),
    external: document.body.textContent.includes("Live provider uit"),
  }));
  check(`viewport ${width} no overflow`, !initial.overflow);
  check(`viewport ${width} keeps Youri AI`, initial.title === "Youri AI");
  check(`viewport ${width} tabs`, initial.tabs.includes("Chat") && initial.tabs.includes("Analyses"));
  check(`viewport ${width} analysis cards`, initial.cards === 3);
  check(`viewport ${width} history visible`, initial.results >= 1);
  check(`viewport ${width} terra shown`, initial.terra);
  check(`viewport ${width} provider copy`, initial.external);

  await page.click('[data-p6d-run="post_workout"]');
  await page.waitForTimeout(100);
  const sent = await page.evaluate(() => ({ body: window.__edgeBody, count: document.querySelectorAll(".p6d-result").length }));
  check(`viewport ${width} edge body exact`, Object.keys(sent.body).sort().join(",") === "analysis_kind,event_id,locale,request_id");
  check(`viewport ${width} edge no authority`, !["provider", "model", "fixture", "entitlement", "user_id"].some((key) => key in sent.body));
  check(`viewport ${width} result added`, sent.count >= 2);

  await page.selectOption('[data-p6d-pref="weekly_day"]', "5");
  await page.click('[data-p6d-preferences-form] button[type="submit"]');
  await page.waitForTimeout(50);
  const calls = await page.evaluate(() => (window.__rpcCalls || []).map((item) => item.name));
  check(`viewport ${width} preferences RPC`, calls.includes("fmz_phase6d_update_preferences"));
  await page.click("[data-p6d-export]");
  await page.waitForTimeout(30);
  check(`viewport ${width} export RPC`, (await page.evaluate(() => (window.__rpcCalls || []).map((item) => item.name))).includes("fmz_phase6d_export_analyses"));
  await page.close();
}

(async () => {
  const edge = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
  const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(edge) ? edge : undefined });
  for (const [width, height] of [[320, 700], [390, 844], [820, 1180], [1440, 900]]) await runViewport(browser, width, height);
  await browser.close();
  const failed = checks.filter((item) => !item.pass);
  console.log(JSON.stringify({ scope: "phase6d_read_only_ai_analyses_browser", pass_count: checks.length - failed.length, fail_count: failed.length, overall_pass: failed.length === 0, failed }, null, 2));
  if (failed.length) process.exit(1);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
