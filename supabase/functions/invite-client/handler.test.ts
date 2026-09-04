import { test } from "node:test";
import assert from "node:assert/strict";
import { handleInvite } from "./handler.ts";
function harness(mode="new") {
 const calls:any[]=[];
 const user={auth:{getUser:async()=>({data:{user:{id:"synthetic-trainer"}}})},
 rpc:async(name:string,args:unknown)=>{calls.push({name,args});return mode==="denied"?{error:{code:"42501"}}:{data:{token:"a".repeat(64),invitation_id:"synthetic-invite",email:"target@example.invalid",name:"Target"}};}};
 const admin={auth:{admin:{inviteUserByEmail:async(email:string,args:unknown)=>{calls.push({name:"mail",email,args});return mode==="existing"?{error:{code:"email_exists"}}:mode==="failed"?{error:{code:"smtp_failure"}}:{data:{user:{id:"unused"}}};}},
 resetPasswordForEmail:async(email:string,args:unknown)=>{calls.push({name:"recovery",email,args});return{};}}};
 return {clients:{user,admin},calls};
}
const request=(body:object={},headers:Record<string,string>={},method="POST")=>new Request("https://mokxyyullfhkfalopbzd.supabase.co/functions/v1/invite-client",
 {method,headers:{Authorization:"Bearer synthetic-test",Origin:"https://yourizorge.github.io","Content-Type":"application/json",...headers},...(method==="POST"?{body:JSON.stringify(body)}:{})});
test("no authorization denies before RPC",async()=>{const h=harness();assert.equal((await handleInvite(request({},{Authorization:""}),h.clients)).status,401);assert.equal(h.calls.length,0);});
test("untrusted origin denied",async()=>{const h=harness();assert.equal((await handleInvite(request({},{Origin:"https://untrusted.invalid"}),h.clients)).status,403);});
test("preflight restricted",async()=>{const h=harness();const r=await handleInvite(request({},{},"OPTIONS"),h.clients);assert.equal(r.status,204);assert.equal(r.headers.get("Access-Control-Allow-Origin"),"https://yourizorge.github.io");});
test("invalid auth rejected",async()=>{const h=harness();h.clients.user.auth.getUser=async()=>({data:{user:null}}) as any;assert.equal((await handleInvite(request({clientId:"slot"}),h.clients)).status,401);});
test("member denied by authoritative issue RPC",async()=>{const h=harness("denied");assert.equal((await handleInvite(request({clientId:"slot"}),h.clients)).status,403);assert.equal(h.calls.length,1);});
test("only stored slot identity reaches Auth invitation",async()=>{const h=harness();const r=await handleInvite(request({clientId:"slot",email:"attacker@example.invalid",name:"spoof",trainerId:"other",redirectTo:"https://untrusted.invalid"}),h.clients);
 assert.equal(r.status,200);assert.deepEqual(h.calls[0],{name:"fmz_phase6d0_issue_client_invite",args:{p_client_id:"slot"}});
 assert.equal(h.calls[1].email,"target@example.invalid");assert.deepEqual(h.calls[1].args.data,{name:"Target"});
 assert.equal(new URL(h.calls[1].args.redirectTo).origin,"https://yourizorge.github.io");
 assert.ok(!JSON.stringify(await r.json()).includes("a".repeat(64)));});
test("existing Auth user recovery does not relink profile",async()=>{const h=harness("existing");assert.equal((await handleInvite(request({clientId:"slot"}),h.clients)).status,200);assert.equal(h.calls[2].name,"recovery");assert.equal(h.calls.length,3);});
test("delivery failure revokes issued token",async()=>{const h=harness("failed");assert.equal((await handleInvite(request({clientId:"slot"}),h.clients)).status,400);assert.equal(h.calls.at(-1)?.name,"fmz_phase6d0_revoke_client_invite");});
test("malformed payload never issues token",async()=>{const h=harness();assert.equal((await handleInvite(request({email:"unused@example.invalid"}),h.clients)).status,400);assert.equal(h.calls.length,0);});
test("other methods refused",async()=>{const h=harness();assert.equal((await handleInvite(request({},{},"GET"),h.clients)).status,405);});
