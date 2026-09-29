"use strict";
const test=require("node:test"),a=require("node:assert/strict"),fs=require("node:fs"),p=require("node:path"),crypto=require("node:crypto");
const root=p.resolve(__dirname,"../../.."),sha=f=>crypto.createHash("sha256").update(fs.readFileSync(p.join(root,f))).digest("hex");
const freeze=JSON.parse(fs.readFileSync(p.join(root,"docs/PHASE6E12_FREEZE_EVIDENCE.json")));
for(const row of freeze.sources)test("6E12 frozen byte "+row.file,()=>a.equal(sha(row.file),row.working_sha256));
test("existing historical evidence unchanged by owner acceptance",()=>a.equal(sha("docs/PHASE6E12_EVIDENCE.json"),freeze.technical_evidence_sha256));
test("public static files cannot connect, store, invoke backend or import offline",()=>{
 const names=fs.readdirSync(p.join(root,"proactive-signals-demo"));
 a.equal(names.length,6);
 for(const f of names){
  const s=fs.readFileSync(p.join(root,"proactive-signals-demo",f),"utf8");
  a(!/fetch\s*\(|XMLHttpRequest|WebSocket|EventSource|localStorage|sessionStorage|indexedDB|sendBeacon|service_role|supabase\.co|_offline\//.test(s),f);
  a(!/eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+\./.test(s),f);
 }
 const html=fs.readFileSync(p.join(root,"proactive-signals-demo/index.html"),"utf8");
 a(html.includes("connect-src 'none'")&&html.includes("form-action 'none'")&&html.includes("worker-src 'none'"));
});
test("Jekyll private paths stay excluded",()=>{const c=fs.readFileSync(p.join(root,"_config.yml"),"utf8");a(c.includes("- _offline")&&c.includes("- supabase"));});
test("private demo server is GET-only explicit static allowlist",async()=>{
 const {allowed}=require("../serve.cjs");a.equal(allowed.length,7);a(allowed.every(x=>x.startsWith("/proactive-signals-demo/")||x==="/training-review-demo/brand.png"));
});
test("immutable receipt says synthetic only and no server release",()=>{
 a.equal(freeze.live_server_integration_authorized,false);a.equal(freeze.whole_phase6e_complete,false);a.equal(freeze.sources.length,19);
});
