import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import cp from "node:child_process";
import {fileURLToPath} from "node:url";
import {next,present,replay,validate,C} from "../edge/core.mjs";
import {createHandler} from "../edge/handler.mjs";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../../..");
const row=(route="B")=>({workspace:"69000000-0000-4000-8000-000000000001",revision:0,route,actor_role:"member",consent:true,guard:"clear",seed:"normal",events:[]});
for(const route of ["A","B"])test(route+" immutable frozen view can be safely projected",()=>{
 const r=row(route),before=replay(r).view(),p=present(r);
 assert(!("audit" in p.view));assert(!("notifications" in p.view));
 assert("audit" in before);assert.equal(p.synthetic_only,true);assert.equal(p.physical_advice_authorized,false);
});
for(const field of ["role","user","user_id","trainer_id","route","chat","health","photo_url","service_role"])
test("reject extraneous command data "+field,async()=>assert.rejects(()=>next(row(),{action:"confirm",data:{[field]:"forged"}}),/payload_invalid/));
for(const guard of ["current","serious","recurring","unclassified","self_reported","missing","technical","misunderstanding"])
test("physical proposal blocked under "+guard,async()=>assert.rejects(()=>next({...row(),guard},{action:"build",data:{intake:C.defaults}}),/safety/));
test("normal B adds complete candidate, not just facts",async()=>{
 const r=await next(row(),{action:"build",data:{intake:C.defaults}});
 assert.equal(r.status,"member_pending");for(const k of ["training","nutrition","recovery"])assert(r.candidate[k]);
 assert.equal(r.version,0);assert.equal(r.view.physical_advice_authorized,false);
});
test("RIR and RPE stay distinct and null load remains null",async()=>{
 const r=await next(row(),{action:"build",data:{intake:{...C.defaults,rir:false,rpe:true}}});
 const e=r.candidate.training.sessions[0].exercises[0];assert.equal(e.rir,null);assert.equal(e.rpe,7);assert.equal(e.load,null);
});
test("changing model source hash refuses replay",()=>assert.throws(()=>replay({...row(),basis:{model:"incorrect"}}),/source_invalid/));
test("no trainer operation on independent route",()=>assert.throws(()=>validate({action:"trainer_approve",data:{}},"B"),/route_action_denied/));
test("forged top-level command role refused",()=>assert.throws(()=>validate({action:"confirm",data:{},role:"trainer"},"B"),/payload_invalid/));
test("unvalidated exercise identity refused before storage",()=>assert.throws(()=>validate({action:"edit",data:{kind:"replace",session:0,index:0,id:"unknown"}},"B"),/payload_invalid/));
test("read-only W2 has actual configured weight step",()=>{
 const p=present({...row("A"),seed:"step_off_grid"});assert.equal(p.view.proposal.status,"blocked");
 assert(JSON.stringify(p.view).includes("weight_step_conflict"));
});
const url="https://mokxyyullfhkfalopbzd.supabase.co",endpoint=url+"/functions/v1/fmz6e9-synthetic";
test("handler refuses different project",()=>assert.throws(()=>createHandler({url:"https://other.invalid",key:"",proof:""}),/staging_target/));
for(const [name,headers,body,status] of [
 ["missing auth",{}, {op:"home"},401],
 ["forged route top-level",{Authorization:"Bearer fake"}, {op:"home",route:"B"},400],
 ["foreign origin",{Authorization:"Bearer fake",Origin:"https://evil.invalid"},{op:"home"},403],
 ["invalid workspace",{Authorization:"Bearer fake"},{op:"read",workspace:"other"},400]
])test(name+" rejected without outbound call",async()=>{
 let calls=0;const h=createHandler({url,key:"public",proof:"private",fetcher:()=>{calls++;throw Error("unexpected");}});
 const r=await h(new Request(endpoint,{method:"POST",headers,body:JSON.stringify(body)}));assert.equal(r.status,status);assert.equal(calls,0);
});
test("missing proof leaves endpoint disabled",async()=>{
 const h=createHandler({url,key:"public",proof:""}),r=await h(new Request(endpoint,{method:"POST"}));assert.equal(r.status,503);
});
test("invalid JWT rejected by Auth before RPC",async()=>{
 const calls=[];const h=createHandler({url,key:"public",proof:"private",fetcher:async u=>{calls.push(u);return new Response("{}",{status:401});}});
 const r=await h(new Request(endpoint,{method:"POST",headers:{Authorization:"Bearer fake"},body:'{"op":"home"}'}));
 assert.equal(r.status,401);assert.deepEqual(calls,[url+"/auth/v1/user"]);
});
const receipt=JSON.parse(fs.readFileSync(path.join(root,"docs/PHASE6E8_FREEZE_EVIDENCE.json")));
test("request body is bounded before outbound authentication",async()=>{
 let calls=0;const h=createHandler({url,key:"public",proof:"private",fetcher:()=>{calls++;throw Error("unexpected");}});
 const r=await h(new Request(endpoint,{method:"POST",headers:{Authorization:"Bearer fake"},body:"x".repeat(16385)}));
 assert.equal(r.status,413);assert.equal(calls,0);
});
for(const f of receipt.sources)test("frozen byte identity "+f.file,()=>assert.equal(crypto.createHash("sha256").update(fs.readFileSync(path.join(root,f.file))).digest("hex"),f.working_sha256));
test("entire change scope is only authorized new code and docs",()=>{
 const files=cp.execFileSync("git",["diff","--name-only",receipt.baseline],{cwd:root,encoding:"utf8"}).trim().split(/\r?\n/);
 files.push(...cp.execFileSync("git",["ls-files","--others","--exclude-standard"],{cwd:root,encoding:"utf8"}).trim().split(/\r?\n/));
 for(const f of files.filter(Boolean))assert(/^(docs\/|_offline\/phase6e9\/|coach-backend-demo\/|supabase\/migrations\/20260915072202_phase6e9_synthetic_authorization.sql$)/.test(f),f);
});
test("no old app bootstrap in backend demo; no private import or provider URL",()=>{
 const html=fs.readFileSync(path.join(root,"coach-backend-demo/index.html"),"utf8");
 assert(!html.includes('src="../app.js'));assert(html.includes("connect-src https://mokxyyullfhkfalopbzd.supabase.co"));
 for(const f of fs.readdirSync(path.join(root,"coach-backend-demo"))){
 const s=fs.readFileSync(path.join(root,"coach-backend-demo",f),"utf8");assert(!/_offline\/|api.openai|service_role|FMZ6E9_PROOF/.test(s),f);
 }
});
