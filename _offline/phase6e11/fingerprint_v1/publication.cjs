'use strict';
// Staging static files and Git metadata only. Never contacts Supabase.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..'),repo='Yourizorge/fitmetzorge-staging';
const baseline='96fc380e47420474efde5509eab0a944398b1190';
const bin='C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/mingw64/bin';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const git=(args,input)=>cp.execFileSync(path.join(bin,'git.exe'),['--exec-path='+bin,...args],{
 cwd:root,input,windowsHide:true,timeout:30000,maxBuffer:60000000,env:{...process.env,GIT_TERMINAL_PROMPT:'0'}});
async function main(){
 assert.equal(git(['remote','get-url','origin']).toString().trim(),'https://github.com/'+repo+'.git');
 assert.equal(git(['branch','--show-current']).toString().trim(),'main');
 const head=git(['rev-parse','HEAD']).toString().trim();
 const evidence=JSON.parse(git(['show',baseline+':docs/PHASE6E10_FREEZE_EVIDENCE.json']));
 const assets=evidence.publication_before_docs_push.assets;
 assert.equal(assets.length,84);
 const report={at:new Date().toISOString(),baseline,head,assets:[],private:[],candidate:[],supabase_calls:0};
 for(const {file} of assets){
  const expected=hash(git(['show',baseline+':'+file]));
  assert.equal(hash(git(['show',head+':'+file])),expected,'committed runtime changed: '+file);
  const r=await fetch('https://yourizorge.github.io/fitmetzorge-staging/'+file.split('/').map(encodeURIComponent).join('/')+'?offline-fp='+Date.now(),{redirect:'error',signal:AbortSignal.timeout(20000)});
  const actual=hash(Buffer.from(await r.arrayBuffer()));
  report.assets.push({file,status:r.status,sha256:actual,expected});
  assert(r.status===200&&actual===expected,'published runtime differs: '+file);
 }
 const knownCandidate=path.join(root,'supabase/.temp/phase6e11-candidate-runtime-1789988635543.json');
 if(fs.existsSync(knownCandidate)){
  for(const row of JSON.parse(fs.readFileSync(knownCandidate)).assets){
   const actual=hash(fs.readFileSync(path.join(root,row.file)));
   report.candidate.push({file:row.file,unchanged:actual===row.checkout_sha256});
   assert.equal(actual,row.checkout_sha256,'retained candidate changed: '+row.file);
  }
 }
 const privateFiles=[...new Set(git(['ls-files','--cached','--others','--exclude-standard']).toString().trim().split(/\r?\n/).filter(f=>/^_(offline|tests)\//.test(f)))];
 for(const file of privateFiles){
  const r=await fetch('https://yourizorge.github.io/fitmetzorge-staging/'+file.split('/').map(encodeURIComponent).join('/')+'?offline-fp='+Date.now(),{redirect:'error',signal:AbortSignal.timeout(20000)});
  await r.arrayBuffer();report.private.push({file,status:r.status});
  assert.equal(r.status,404,'private path exposed: '+file);
 }
 report.pass=true;
 const target=path.join(root,'supabase/.temp/phase6e11-fingerprint-publication-'+crypto.randomUUID()+'.json');
 const bytes=JSON.stringify(report,null,2)+'\n';
 fs.writeFileSync(target,bytes,{flag:'wx'});fs.writeFileSync(target+'.sha256',hash(bytes),{flag:'wx'});
 console.log(JSON.stringify({pass:true,head,assets:report.assets.length,private404:report.private.length,
  candidateUnchanged:report.candidate.length,report:target}));
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
