"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),receipt=require("../../../docs/PHASE6E7_FREEZE_EVIDENCE.json");
const hash=b=>crypto.createHash("sha256").update(b).digest("hex");
for(const f of receipt.frozen_sources)test("frozen source byte identity "+f.file,()=>assert.equal(hash(fs.readFileSync(path.join(root,f.file))),f.working_sha256));
for(const f of receipt.runtime_assets.filter(x=>x.file!=="index.html"))test("protected runtime byte identity "+f.file,()=>assert.equal(hash(fs.readFileSync(path.join(root,f.file))),f.working_sha256));
test("only approved bootstrap differs in index",()=>{
 const old=cp.execFileSync("git",["show",receipt.baseline+":index.html"],{cwd:root,encoding:"utf8"}).replace(/\r\n/g,"\n");
 const now=fs.readFileSync(path.join(root,"index.html"),"utf8").replace(/\r\n/g,"\n");
 const expected=old.replace('<script src="assets/theme-authority.js?v=20260907-theme1"></script>','<script src="coach-review-demo/entry.js?v=6e8-1"></script>\n    <script>window.FMZ_6E8_BOOT.loadLive(["assets/theme-authority.js?v=20260907-theme1"]);</script>')
 .replace('<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n    <script src="config.js"></script>\n    <script src="assets/vendor/zxing-browser-0.2.1.min.js?v=20260827-phase4fd-owner-barcode1"></script>\n    <script src="app.js?v=20260910-effort-align1"></script>','<script>window.FMZ_6E8_BOOT.loadLive(["https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2","config.js","assets/vendor/zxing-browser-0.2.1.min.js?v=20260827-phase4fd-owner-barcode1","app.js?v=20260910-effort-align1"]);</script>');
 assert.equal(now,expected);
});
test("public code has no private imports, stores, external calls or uploads",()=>{
 for(const file of fs.readdirSync(path.join(root,"coach-review-demo"))){
  const source=fs.readFileSync(path.join(root,"coach-review-demo",file),"utf8");
  assert(!/_(offline|tests)\//.test(source),file);
  assert(!/\b(fetch|XMLHttpRequest|WebSocket|postMessage|indexedDB|localStorage|sessionStorage|serviceWorker)\s*[(.=]/.test(source),file);
  assert(!/type=["']file|supabase\.co|api\.openai|mailto:/.test(source),file);
 }
 const html=fs.readFileSync(path.join(root,"coach-review-demo/index.html"),"utf8");
 assert(html.includes("connect-src 'none'"));assert(html.includes("form-action 'none'"));assert(html.includes("frame-src 'none'"));
});
test("complete change allowlist",()=>{
 const changed=cp.execFileSync("git",["diff","--name-only",receipt.baseline],{cwd:root,encoding:"utf8"}).trim().split(/\r?\n/);
 const untracked=cp.execFileSync("git",["ls-files","--others","--exclude-standard"],{cwd:root,encoding:"utf8"}).trim().split(/\r?\n/);
 for(const file of [...changed,...untracked].filter(Boolean))assert(file==="index.html"||/^(docs\/|coach-review-demo\/|_offline\/phase6e8\/)/.test(file),file);
});
