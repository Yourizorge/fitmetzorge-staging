'use strict';
// Local UI evidence only: explicitly simulated HTTP/Auth, no PostgreSQL proof.
// Usage: node account_center_fixture_browser.cjs <playwright-module> [channel]
//   [--logout-delay-ms=1500] [--mapped-ab] [--no-screenshots]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {values:options,positionals}=require('node:util').parseArgs({allowPositionals:true,options:{
  'logout-delay-ms':{type:'string',default:'1500'},'mapped-ab':{type:'boolean',default:false},
  'no-screenshots':{type:'boolean',default:false}
}});
const logoutDelay=Number(options['logout-delay-ms']),mappedAB=options['mapped-ab'];
if(!positionals[0]||positionals.length>2||!/^\d+$/.test(options['logout-delay-ms'])||!Number.isSafeInteger(logoutDelay)||logoutDelay>10000)throw Error('fixture_arguments');
const D=require('./domain.cjs'),A=require('./account_center.cjs'),P=require('./access_policy.cjs');
const suite=require('./account_center_browser.cjs');
const root=path.resolve(__dirname,'../..');
const workspaces={a:'10000000-0000-4000-8000-000000000001',b:'10000000-0000-4000-8000-000000000002'};
const states={a:D.initial('A'),b:D.initial('B')};
// Match database_tests' UI snapshots after release_selection_http restores B.
if(mappedAB)for(const language of ['de','nl'])states.b=D.transition(states.b,{action:'preferences',data:{...states.b.preferences,language}},'member');
const at=Date.UTC(2026,0,24),start=Date.UTC(2026,0,1);
const explicitSource={id:'explicit-ui-test-source',version:1,synthetic_only:true,verified:true,
  grants:[{id:'test-trial',kind:'trial',tier:'ai',start,end:start+30*P.DAY,revoked:false}]};
const accounts=Object.fromEntries(['a','b','trainer','empty'].map(role=>[role,{email:role+'@example.invalid',password:'fixture-only'}]));
function views(role) {
  if(role==='empty')return [];
  const isTrainer=role==='trainer',key=isTrainer?'a':role,s=states[key];
  const state=isTrainer?{revision:s.revision,route:s.route,active:{version:s.active.version,training:s.active.training},review:null,status:s.status,reason:'no_review'}:D.view(s);
  return [{workspace:workspaces[key],version:s.revision,role:isTrainer?'trainer':'member',actor:isTrainer?'20000000-0000-4000-8000-000000000003':'20000000-0000-4000-8000-00000000000'+(key==='a'?'1':'2'),state,
    capabilities:{full_day21:mappedAB},notices:[],access:isTrainer?null:A.access(!mappedAB&&key==='b'?explicitSource:null,at),durable:true,hosted:false}];
}
const filenames=['ui.html','ui.js','ui.css','display.js','panels.js','draft_queue.js','queue_ui.js','account_center.js','offline_shell.js','offline_shell.html','offline_shell.css','offline_sw.js'];
const assets=new Map(filenames.map(name=>['/'+name,path.join(__dirname,name)]));
assets.set('/',path.join(__dirname,'ui.html'));assets.set('/brand.png',path.join(root,'assets/fit-met-zorge-logo-cropped.png'));
assets.set('/workout-model.js',path.join(root,'assets/training-workout-model.js'));
let pendingLogouts=0,completedLogouts=0,prematureNavigations=0;
const server=http.createServer(async(req,res)=>{
  const reply=(status,value,headers={})=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store',...headers});res.end(JSON.stringify(value));};
  if(req.url==='/'&&pendingLogouts)prematureNavigations++;
  if(req.url==='/api/login') {
    let raw='';for await(const chunk of req)raw+=chunk;const body=JSON.parse(raw),role=Object.keys(accounts).find(key=>accounts[key].email===body.email);
    return role?reply(200,{}, {'Set-Cookie':'fixture_actor='+role+'; Path=/; HttpOnly; SameSite=Strict'}):reply(403,{code:'workspace_denied'});
  }
  if(req.url==='/api/logout'){
    if(req.method!=='POST')return reply(405,{code:'fixture_method'});
    pendingLogouts++;
    await new Promise(resolve=>setTimeout(resolve,logoutDelay));
    reply(200,{}, {'Set-Cookie':'fixture_actor=; Max-Age=0; Path=/; HttpOnly'});
    pendingLogouts--;completedLogouts++;return;
  }
  if(req.url==='/api/today') {
    const role=/fixture_actor=(a|b|trainer|empty)(?:;|$)/.exec(req.headers.cookie||'')?.[1];
    return role?reply(200,{csrf:'fixture-csrf',views:views(role)}):reply(403,{code:'login_required'});
  }
  if(req.url==='/api/action')return reply(405,{code:'fixture_read_only'});
  const file=assets.get(req.url);
  if(!file)return reply(404,{code:'route'});
  const mime={'.js':'text/javascript','.css':'text/css','.html':'text/html','.png':'image/png'}[path.extname(file)];
  res.writeHead(200,{'Content-Type':mime,'Cache-Control':'no-store'});res.end(fs.readFileSync(file));
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const c={url:'http://127.0.0.1:'+server.address().port,playwright:positionals[0],channel:positionals[1],accounts,
    screenshots:options['no-screenshots']?undefined:path.join(root,'supabase/.temp/account-center-ui')};
  if(c.screenshots)fs.mkdirSync(c.screenshots,{recursive:true});
  const result=await suite.run(c);
  if(pendingLogouts||completedLogouts!==3||prematureNavigations)throw Error('logout_completion_order');
  result.checks++;
  const browser=await require(c.playwright).chromium.launch({headless:true,...(c.channel?{channel:c.channel}:{})});
  try {
    const page=await browser.newPage();await page.goto(c.url);
    await page.locator('[name=email]').fill(accounts.empty.email);await page.locator('[name=password]').fill(accounts.empty.password);await page.locator('#login button').click();
    await page.locator('#app').waitFor({state:'visible'});await page.locator('[data-no-workspaces]').waitFor();
    if(!await page.locator('#workspace').isDisabled())throw Error('empty_workspace_selector');
    if(await page.locator('#content [data-action]').count())throw Error('empty_workspace_action');
    result.checks+=2;
  } finally {await browser.close();}
  console.log(JSON.stringify({...result,evidence:'simulated_http_ui_only',database_auth_proof:false,screenshot_directory:c.screenshots,
    fixture_mode:mappedAB?'mapped_ab':'explicit_access',logout_delay_ms:logoutDelay,completed_logouts:completedLogouts,premature_navigations:prematureNavigations}));
})().catch(e=>{console.error(e.message);process.exitCode=1;}).finally(()=>server.close());
