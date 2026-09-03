import assert from "node:assert/strict";
import test from "node:test";
import { createPhase6cHandler, createPhase6cMockReply, parsePhase6cChatRequest } from "./phase6c-handler.ts";

const input = {
  request_id:"10000000-0000-4000-8000-000000000001",attempt_id:"10000000-0000-4000-8000-000000000002",
  thread_id:"10000000-0000-4000-8000-000000000003",expected_revision:1,locale:"nl" as const,content:"Ik wil vandaag een haalbare stap zetten."
};

function invoke(body:unknown, options:{token?:string; fail?:boolean; begun?:Record<string,unknown>}={}) {
  const calls:{name:string;input:Record<string,unknown>}[]=[];
  const handler=createPhase6cHandler({
    async verifyBearer(token){return token==="member-token"?{id:"10000000-0000-4000-8000-000000000010"}:null;},
    async memberRpc(_token,name,args={}){calls.push({name,input:args});return {message_id:"10000000-0000-4000-8000-000000000011",revision:2};},
    async serviceRpc(name,args={}){calls.push({name,input:args});if(options.fail&&name.includes("complete"))throw new Error("mock_controlled_failure");return name.includes("begin")?(options.begun||{run_id:"10000000-0000-4000-8000-000000000012",status:"reserved"}):{status:"completed"};}
  });
  return {calls,response:handler(new Request("https://example.test/youri-ai/phase6c/chat",{method:"POST",headers:{Authorization:`Bearer ${options.token||"member-token"}`,Origin:"https://yourizorge.github.io","Content-Type":"application/json"},body:JSON.stringify(body)}))};
}

test("request is exact and bounded",()=>{
  assert.deepEqual(parsePhase6cChatRequest(input),input);
  assert.throws(()=>parsePhase6cChatRequest({...input,model:"gpt"}),/chat_request_invalid/);
  assert.throws(()=>parsePhase6cChatRequest({...input,content:"x".repeat(4001)}),/chat_content_invalid/);
});
test("normal mock is deterministic strict and has no actions",()=>{
  assert.deepEqual(createPhase6cMockReply(input.content,"nl"),createPhase6cMockReply(input.content,"nl"));
  assert.equal(createPhase6cMockReply(input.content,"nl").actions.length,0);
});
test("medical advice is safely refused",()=>{
  const reply=createPhase6cMockReply("Welke medicatie en dosering moet ik nemen?","nl");
  assert.match(reply.summary,/geen diagnose/);assert.equal(reply.actions.length,0);assert.equal(reply.safety.status,"clear");
});
test("serious signal hard stops",()=>{
  const reply=createPhase6cMockReply("Ik heb borstpijn en krijg geen adem.","nl");
  assert.equal(reply.safety.status,"hard_stop");assert.equal(reply.safety.automatic_execution_blocked,true);assert.equal(reply.actions.length,0);
});
test("authenticated request writes through RPC and completes zero-cost mock",async()=>{
  const {calls,response}=invoke(input);const result=await response;const body=await result.json();
  assert.equal(result.status,200);assert.equal(body.external_ai_calls,0);assert.equal(body.external_ai_cost_eur,0);
  assert.deepEqual(calls.map((item)=>item.name),["fmz_phase6c_submit_message","fmz_phase6c_service_begin_mock_run","fmz_phase6a_service_complete_run"]);
  assert.equal(Object.keys(calls[0].input).some((key)=>/provider|model|fixture/.test(key)),false);
});
test("completed attempt replays without another completion",async()=>{
  const {calls,response}=invoke(input,{begun:{run_id:"10000000-0000-4000-8000-000000000012",status:"completed"}});assert.equal((await response).status,200);
  assert.equal(calls.some((item)=>item.name.includes("complete_run")),false);
});
test("controlled failure is sanitized and reconciled",async()=>{
  const {calls,response}=invoke(input,{fail:true});const result=await response;assert.equal(result.status,422);assert.deepEqual(await result.json(),{error:"mock_controlled_failure"});
  assert.equal(calls.at(-1)?.name,"fmz_phase6a_service_fail_run");
});
test("auth and origin fail closed",async()=>{
  assert.equal(await (await invoke(input,{token:"bad"}).response).status,401);
  const handler=createPhase6cHandler({async verifyBearer(){return{id:"x"};},async memberRpc(){return{};},async serviceRpc(){return{};}});
  assert.equal((await handler(new Request("https://example.test/youri-ai/phase6c/chat",{method:"POST",headers:{Origin:"https://evil.example"},body:"{}"}))).status,403);
});
