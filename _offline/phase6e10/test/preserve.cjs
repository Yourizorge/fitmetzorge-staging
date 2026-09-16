const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto"),assert=require("node:assert/strict"),cp=require("node:child_process");
const root=path.resolve(__dirname,"../../.."),e=require("../../../docs/PHASE6E9_FREEZE_EVIDENCE.json");
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
const canonical=process.argv.includes("--canonical");
for(const f of e.protected){
 assert.equal(sha(fs.readFileSync(path.join(root,f.file))),canonical?f.sha256:f.checkout_sha256,f.file+" checkout changed");
 assert.equal(cp.execFileSync("git",["rev-parse",e.baseline+":"+f.file],{cwd:root,encoding:"utf8"}).trim(),f.blob);
}
console.log(JSON.stringify({protected_files:e.protected.length,unchanged:true,canonical,baseline:e.baseline}));
