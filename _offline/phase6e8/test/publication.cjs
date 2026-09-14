"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),base="https://yourizorge.github.io/fitmetzorge-staging/",receipt=require("../../../docs/PHASE6E7_FREEZE_EVIDENCE.json"),sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,maxBuffer:60000000}),tracked=git("ls-files").toString().trim().split(/\r?\n/),head=git("rev-parse","HEAD").toString().trim();
const publicFiles=[...receipt.runtime_assets.map(x=>x.file),...tracked.filter(x=>/^(training-review-demo|coach-review-demo)\//.test(x))];
const privateFiles=tracked.filter(x=>/^_(offline|tests)\//.test(x)),results={head,base,at:new Date().toISOString(),assets:[],private:[],protected_runtime:59,authorized_runtime_exception:"index.html",errors:[]};
async function request(file){const response=await fetch(base+file.split("/").map(encodeURIComponent).join("/")+"?verify6e8="+head.slice(0,10),{redirect:"error",signal:AbortSignal.timeout(30000)});return response;}
(async()=>{
 try{
  for(const file of [...new Set(publicFiles)]){
   const expected=git("show","HEAD:"+file),response=await request(file),bytes=Buffer.from(await response.arrayBuffer());
   const row={file,status:response.status,expected:sha(expected),published:sha(bytes),identical:response.status===200&&sha(expected)===sha(bytes)};results.assets.push(row);
   const protectedFile=receipt.runtime_assets.find(x=>x.file===file&&file!=="index.html");if(protectedFile)assert.equal(sha(expected),protectedFile.sha256,file);
   assert(row.identical,file+" bytes differ");console.log("asset",file);
  }
  for(const file of privateFiles){const response=await request(file);await response.arrayBuffer();results.private.push({file,status:response.status});assert.equal(response.status,404,file+" unexpectedly public");}
  console.log(JSON.stringify({head,assets:results.assets.length,private404:results.private.length,protectedRuntime:59,index:"authorized change"}));
 }catch(e){results.errors.push(e.message);throw e;}
 finally{fs.writeFileSync(path.join(root,"supabase/.temp/phase6e8-publication.json"),JSON.stringify(results,null,2)+"\n");}
})().catch(e=>{console.error(e);process.exitCode=1;});
