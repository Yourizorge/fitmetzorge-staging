"use strict";
const fs=require("node:fs"),p=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto");
const root=p.resolve(__dirname,"../.."),git=(...a)=>cp.execFileSync(process.env.FMZ_GIT||"git",a,{cwd:root,maxBuffer:80000000}).toString().trim();
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
const out=process.argv[3]||p.join(root,"supabase/.temp/phase6e12-"+crypto.randomUUID());
const ignored=n=>n.startsWith("_offline/phase6e12/")||n.startsWith("workout-reflection-demo/")||/^docs\/PHASE6E12_(DEPENDENCIES_AND_CASES|REPORT|OWNER_REVIEW|EVIDENCE)\./.test(n);
if(process.argv[2]==="before"){
 fs.mkdirSync(out,{recursive:true});
 const names=git("ls-files","-z","--cached","--others","--exclude-standard").split("\0").filter(Boolean);
 const sources=Object.fromEntries([...new Set(names)].filter(n=>!ignored(n)).sort().map(n=>[n,sha(fs.readFileSync(p.join(root,n)))]));
 fs.writeFileSync(p.join(out,"before.json"),JSON.stringify({head:git("rev-parse","HEAD"),branch:git("branch","--show-current"),sources},null,2),{flag:"wx"});
 console.log(JSON.stringify({folder:out,files:Object.keys(sources).length}));
}else{
 const b=JSON.parse(fs.readFileSync(p.join(out,"before.json")));
 const changed=Object.entries(b.sources).filter(([n,h])=>!fs.existsSync(p.join(root,n))||sha(fs.readFileSync(p.join(root,n)))!==h).map(([n])=>n);
 if(changed.length)throw Error("preservation:"+changed.join(","));
 const result={status:"EXISTING_FILES_BYTE_IDENTICAL",files:Object.keys(b.sources).length,head:git("rev-parse","HEAD"),before_sha256:sha(fs.readFileSync(p.join(out,"before.json")))};
 fs.writeFileSync(p.join(out,"preservation-"+crypto.randomUUID()+".json"),JSON.stringify(result),{flag:"wx"});console.log(JSON.stringify(result));
}
