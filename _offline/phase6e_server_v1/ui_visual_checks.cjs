'use strict';
// Focused presentation check. API state is synthetic; this is not database evidence.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require('playwright'),D=require('./domain.cjs'),R=require('./registration12.cjs');
const root=path.resolve(__dirname,'../..'),out=path.resolve(process.argv[2]);
if(path.dirname(out)!==path.join(root,'supabase','.temp')||!path.basename(out).startsWith('phase6e-ui-'))throw Error('output_scope');
fs.mkdirSync(out);let fixture='B';
const server=http.createServer((req,res)=>{
 if(req.method!=='GET'){res.writeHead(405).end();return;}
 if(req.url==='/api/today'){
  const view=fixture==='12'?{workspace:'synthetic12',role:'member',version:0,state:R.view(R.initial()),capabilities:{registration12:true,full_day21:false}}:
   {workspace:'synthetic'+fixture,role:'member',version:0,state:D.view(D.initial(fixture)),capabilities:{full_day21:true},notices:[]};
  res.setHeader('Content-Type','application/json');res.end(JSON.stringify({views:[view],csrf:'local-visual-not-auth'}));return;
 }
 const files={'/':'ui.html','/ui.js':'ui.js','/ui.css':'ui.css'};
 if(req.url==='/brand.png'){res.setHeader('Content-Type','image/png');res.end(fs.readFileSync(path.join(root,'assets/fit-met-zorge-logo-cropped.png')));return;}
 const file=files[req.url];if(!file){res.writeHead(404).end();return;}
 res.setHeader('Content-Type',file.endsWith('js')?'application/javascript':file.endsWith('css')?'text/css':'text/html');res.end(fs.readFileSync(path.join(__dirname,file)));
});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser,checks=0;const errors=[];
try{
 const options={headless:true};if(!fs.existsSync(chromium.executablePath()))options.channel='msedge';
 browser=await chromium.launch(options);const context=await browser.newContext(),page=await context.newPage(),url='http://127.0.0.1:'+server.address().port;
 await context.route('**/*',r=>new URL(r.request().url()).origin===url?r.continue():r.abort());page.on('pageerror',e=>errors.push(e.name));
 for(const slice of ['A','B','12'])for(const width of [390,1280])for(const lang of ['0','1','2'])for(const theme of ['light','dark']){
  fixture=slice;await page.setViewportSize({width,height:900});await page.goto(url);await page.locator('#app').waitFor({state:'visible'});
  await page.locator('#lang').selectOption(lang);await page.locator('#theme').selectOption(theme);
  if(slice!=='12'){
   const expected=['Intake','Intake','Angaben'][Number(lang)];if(await page.locator('[data-tab=intake]').innerText()!==expected)throw Error('navigation_label');checks++;
   await page.locator('[data-tab=training]').click();
  }
  const labels=await page.locator('#content label').allTextContents();if(labels.some(x=>/^(LOAD|REPS|RIR|RPE)\d/.test(x.trim())))throw Error('numeric_label');checks++;
  if(!await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))throw Error('overflow');checks++;
  if(lang==='0'&&width===390)await page.screenshot({path:path.join(out,'mobile-'+slice+'-'+theme+'.png'),fullPage:true});
 }
 if(errors.length)throw Error('browser_errors');
 const hashes=Object.fromEntries(['ui.js','ui.html','ui.css','ui_visual_checks.cjs'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,n))).digest('hex')]));
 const result={status:'PASS',checks,source_hashes:hashes,api:'synthetic_read_only_fixture_not_database_proof',physical_phone:false,external_calls:0};
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2),{flag:'wx'});console.log(JSON.stringify(result));
}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}})().catch(e=>{console.error(e.name+':'+e.message);process.exitCode=1;});
