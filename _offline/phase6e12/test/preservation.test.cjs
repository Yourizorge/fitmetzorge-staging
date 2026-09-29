"use strict";
const test=require("node:test"),a=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),receipt=JSON.parse(fs.readFileSync(path.join(root,"docs/PHASE6E10_FREEZE_EVIDENCE.json")));
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
for(const f of receipt.protected)test("accepted Git source preserved "+f.file,()=>{
 const blob=cp.execFileSync(process.env.FMZ_GIT||"git",["show","HEAD:"+f.file],{cwd:root,maxBuffer:20000000,windowsHide:true});
 a.equal(sha(blob),f.sha256);
 if(f.file.startsWith("_offline/"))a.equal(sha(fs.readFileSync(path.join(root,f.file))),f.checkout_sha256);
});
