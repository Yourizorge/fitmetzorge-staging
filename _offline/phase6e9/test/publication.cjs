"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),base="https://yourizorge.github.io/fitmetzorge-staging/",sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,maxBuffer:60000000});
const head=git("rev-parse","HEAD").toString().trim(),tracked=git("ls-files").toString().trim().split(/\r?\n/);
const runtime=require("../../../docs/PHASE6E7_FREEZE_EVIDENCE.json").runtime_assets.map(x=>x.file);
const frozen=require("../../../docs/PHASE6E8_FREEZE_EVIDENCE.json");
const old=[...new Set([...runtime,...tracked.filter(x=>/^(training-review-demo|coach-review-demo)\//.test(x))])];
const newer=tracked.filter(x=>/^coach-backend-demo\//.test(x));
const privateFiles=tracked.filter(x=>/^_(offline|tests)\//.test(x));
const results={head,at:new Date().toISOString(),base,assets:[],private:[],errors:[]};
async function req(file){return fetch(base+file.split("/").map(encodeURIComponent).join("/")+"?verify6e9="+head.slice(0,12),{redirect:"error",signal:AbortSignal.timeout(30000)});}
(async()=>{
try{
 for(const file of [...old,...newer]){
 const bytes=git("show","HEAD:"+file),expected=sha(bytes);
 if(old.includes(file))assert.equal(expected,sha(git("show",frozen.baseline+":"+file)),file+" frozen runtime changed");
 const response=await req(file),published=sha(Buffer.from(await response.arrayBuffer()));
 const row={file,status:response.status,expected,published,identical:response.status===200&&expected===published};results.assets.push(row);assert(row.identical,file);
 }
 for(const file of privateFiles){const response=await req(file);await response.arrayBuffer();results.private.push({file,status:response.status});assert.equal(response.status,404,file);}
 console.log(JSON.stringify({head,assets:results.assets.length,unchanged_existing:old.length,new_assets:newer.length,private404:results.private.length}));
} catch(e){results.errors.push(e.message);throw e;}
finally{fs.writeFileSync(path.join(root,"supabase/.temp/phase6e9-publication.json"),JSON.stringify(results,null,2)+"\n");}
})().catch(e=>{console.error(e);process.exitCode=1;});
