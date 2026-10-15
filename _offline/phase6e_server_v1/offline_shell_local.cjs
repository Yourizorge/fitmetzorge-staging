'use strict';
// Browser/cache/storage evidence only. Every API request is denied; no Auth or DB fixture.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {shellChecks}=require('./offline_shell_browser.cjs');
const files=new Map(['ui.html','ui.css','ui.js','panels.js','display.js','draft_queue.js','queue_ui.js','account_center.js','offline_shell.html','offline_shell.css','offline_shell.js','offline_sw.js'].map(n=>['/'+n,path.join(__dirname,n)]));
files.set('/',path.join(__dirname,'ui.html'));files.set('/workout-model.js',path.resolve(__dirname,'../../assets/training-workout-model.js'));files.set('/brand.png',path.resolve(__dirname,'../../assets/fit-met-zorge-logo-cropped.png'));
async function main(){
 const playwright=process.argv[2],out=path.resolve(process.argv[3]);
 const root=path.resolve(__dirname,'../..');if(!out.startsWith(root+path.sep))throw Error('output_scope');
 fs.mkdirSync(out,{recursive:true});
 const server=http.createServer((req,res)=>{
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Content-Security-Policy',"default-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'");
  if(req.method!=='GET'||req.url.startsWith('/api/')){res.writeHead(403,{'Content-Type':'application/json'}).end('{"code":"login_required"}');return;}
  const file=files.get(req.url);if(!file){res.writeHead(404).end();return;}
  const type=file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':file.endsWith('.png')?'image/png':'text/html';res.writeHead(200,{'Content-Type':type}).end(fs.readFileSync(file));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));let browser,checks=0;
 try{
  const chromium=require(playwright).chromium,options={headless:true};if(!fs.existsSync(chromium.executablePath()))options.channel='msedge';browser=await chromium.launch(options);
  const screenshots=await shellChecks(browser,{url:'http://127.0.0.1:'+server.address().port,screenshots:out},(value,label)=>{if(!value)throw Error(label);checks++;});
  const result={status:'PASS',checks,screenshots,real_local_auth:false,scope:'generic_shell_and_browser_storage_only',database_setup:false,hosted_calls:0};
  fs.writeFileSync(path.join(out,'offline-shell-local.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
}
main().catch(e=>{console.error(e.message);process.exitCode=2;});
