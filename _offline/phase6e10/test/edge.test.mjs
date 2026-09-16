import test from "node:test";
import assert from "node:assert/strict";
import {createHandler} from "../edge/handler.mjs";
const url="https://mokxyyullfhkfalopbzd.supabase.co",id="61000000-0000-4000-8000-000000000001";
const req=(body={op:"home"},headers={})=>new Request(url,{method:"POST",headers:{Authorization:"Bearer synthetic.token.only","Content-Type":"application/json",...headers},body:JSON.stringify(body)});
test("wrong project rejected",()=>assert.throws(()=>createHandler({url:"https://example.invalid"})));
test("missing proof, wrong origin and unauthenticated requests denied",async()=>{
 const h=createHandler({url,key:"public",proof:"only-local",fetcher:()=>{throw Error("must not call");}});
 assert.equal((await h(new Request(url,{method:"POST"}))).status,401);
 assert.equal((await h(req({}, {Origin:"https://example.invalid"}))).status,403);
 assert.equal((await createHandler({url,key:"public"})(req())).status,503);
});
test("strict payload shape and size",async()=>{
 const h=createHandler({url,key:"public",proof:"only-local",fetcher:()=>{throw Error("must not call");}});
 assert.equal((await h(req({op:"home",role:"trainer"}))).status,400);
 assert.equal((await h(req({op:"home",x:"a".repeat(33000)}))).status,413);
});
test("user token forwarded, no service authority; only fixed RPC",async()=>{
 let n=0;
 const h=createHandler({url,key:"public",proof:"only-local",fetcher:async(u,o)=>{
  assert.equal(o.headers.Authorization,"Bearer synthetic.token.only");
  if(n++===0){assert.equal(u,url+"/auth/v1/user");return Response.json({id});}
  assert.equal(u,url+"/rest/v1/rpc/fmz6e10_call");assert.equal(o.headers["x-fmz6e10-proof"],"only-local");
  assert.deepEqual(JSON.parse(o.body),{p:{op:"home"}});return Response.json({role:"a_member"});
 }});
 const r=await h(req());assert.equal(r.status,200);assert.deepEqual(await r.json(),{role:"a_member"});assert.equal(n,2);
});
test("SQL detail and secrets never echoed; stale code remains actionable",async()=>{
 for(const [message,expected,status] of [["SQL contains private values","synthetic_database_temporarily_unavailable",503],["synthetic_source_or_plan_stale","synthetic_source_or_plan_stale",409]]){
  let n=0;const h=createHandler({url,key:"public",proof:"only-local",fetcher:async()=>n++?Response.json({message,details:"private",hint:"secret"},{status:400}):Response.json({id})});
  const r=await h(req());assert.equal(r.status,status);assert.deepEqual(await r.json(),{error:expected});
 }
});
test("network errors give technical feedback, not health warning",async()=>{
 const h=createHandler({url,key:"public",proof:"only-local",fetcher:()=>{throw Error("private");}});
 const r=await h(req());assert.equal(r.status,503);assert.deepEqual(await r.json(),{error:"synthetic_auth_temporarily_unavailable"});
});
test("Auth outage is never reported as an authentication denial",async()=>{
 const h=createHandler({url,key:"public",proof:"only-local",fetcher:async()=>Response.json({}, {status:503})});
 const r=await h(req());assert.equal(r.status,503);assert.deepEqual(await r.json(),{error:"synthetic_auth_temporarily_unavailable"});
});
test("malformed JSON and SQL constraints are input errors, not technical successes",async()=>{
 let n=0;const h=createHandler({url,key:"public",proof:"only-local",fetcher:async()=>n++?Response.json({code:"23514",message:"private constraint detail"},{status:400}):Response.json({id})});
 const bad=await h(new Request(url,{method:"POST",headers:{Authorization:"Bearer synthetic.token.only"},body:"{"}));
 assert.equal(bad.status,400);assert.equal(n,0);
 const r=await h(req());assert.equal(r.status,400);assert.deepEqual(await r.json(),{error:"payload_invalid"});
});
