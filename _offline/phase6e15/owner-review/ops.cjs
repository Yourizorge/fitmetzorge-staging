"use strict";
const fs=require("node:fs"),p=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../../.."),[mode,out]=process.argv.slice(2),git=(...v)=>cp.execFileSync(process.env.FMZ_GIT||"git",v,{cwd:root,maxBuffer:100000000}).toString(),sha=f=>crypto.createHash("sha256").update(fs.readFileSync(p.join(root,f))).digest("hex");
const allowed=["independent-intake-demo/app.js","independent-intake-demo/index.html","independent-intake-demo/demo.css","_offline/phase6e15/serve.cjs"];
if(mode==="before"){
 fs.mkdirSync(out,{recursive:true});
 const files=git("ls-files","-z","--cached","--others","--exclude-standard").split("\0").filter(Boolean);
 fs.writeFileSync(p.join(out,"before.json"),JSON.stringify({head:git("rev-parse","HEAD").trim(),allowed,files:Object.fromEntries(files.map(f=>[f,sha(f)]))},null,2),{flag:"wx"});
 console.log(JSON.stringify({recorded:files.length,allowed_existing_edits:allowed}));
}else if(mode==="preserve"){
 const b=JSON.parse(fs.readFileSync(p.join(out,"before.json")));let preserved=0;const changed=[];
 for(const [f,h]of Object.entries(b.files)){const now=sha(f);if(b.allowed.includes(f)){if(now!==h)changed.push(f);}else{a.equal(now,h,f);preserved++;}}
 const result={status:"PASS",preserved,changed,head:git("rev-parse","HEAD").trim()};
 fs.writeFileSync(p.join(out,"preservation-"+Date.now()+".json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify(result));
}else throw Error("mode");
