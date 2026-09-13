"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("fs"),cp=require("child_process"),crypto=require("crypto");
const git=(...a)=>cp.execFileSync("git",a,{encoding:"utf8",windowsHide:true,maxBuffer:60000000}).trim();
test("122 frozen sources and 60 runtime assets byte-identical",()=>{
 const e=JSON.parse(fs.readFileSync("docs/PHASE6E6_FREEZE_EVIDENCE.json")),m=new Map(git("ls-tree","-r","HEAD").split("\n").map(l=>{const[a,b]=l.split("\t");return[b,a.split(" ")[2]];}));
 assert.equal(e.frozen_sources.length,122);assert.equal(e.runtime_assets.length,60);
 for(const x of [...e.frozen_sources,...e.runtime_assets]){assert.equal(m.get(x.file),x.git_blob,x.file);assert.equal(crypto.createHash("sha256").update(fs.readFileSync(x.file)).digest("hex"),x.working_sha256,x.file);}
});
test("authorized new demo offline docs scope; no public private-code imports or storage/network calls",()=>{
 const files=[...git("diff","--name-only","ef42876164f82330de016cb38c5213034cd2f072").split("\n"),...git("ls-files","--others","--exclude-standard").split("\n")].filter(Boolean);
 assert(files.every(f=>f.startsWith("_offline/phase6e7/")||f.startsWith("training-review-demo/")||f.startsWith("docs/")),files.join("\n"));
 const source=fs.readdirSync("training-review-demo").filter(f=>/\.(js|html)$/.test(f)).map(f=>fs.readFileSync("training-review-demo/"+f,"utf8")).join("\n");
 assert.doesNotMatch(source,/_offline|_tests|supabase|fetch\(|XMLHttpRequest|WebSocket|EventSource|serviceWorker|localStorage|sessionStorage|indexedDB|document\.cookie|navigator\.sendBeacon|sourceMappingURL/);
 assert(source.includes("connect-src 'none'"));assert(!fs.existsSync("_offline/phase6e8"));
});
