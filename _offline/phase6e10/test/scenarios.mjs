import assert from "node:assert/strict";
import crypto from "node:crypto";
const clone=x=>JSON.parse(JSON.stringify(x));
export async function runScenarios(api,report){
 const check=async(name,fn)=>{await fn();report.checks.push({name,pass:true});console.log("PASS",name);};
 const denied=(r,code)=>{
  assert([400,401,403,409].includes(r.status),"expected authorization/contract denial, not transport failure: "+r.status);
  if(code)assert.match(r.data.error||r.data.message||"",new RegExp(code));
 };
 const revisions=new Map();
 const request=async(who,b)=>{
  const r=await api.raw(who,b);assert.equal(r.status,200,JSON.stringify(r.data));
  if(r.data.windows)for(const w of r.data.windows)revisions.set(w.id,w.revision);
  if(typeof r.data.window==="string"&&Number.isInteger(r.data.revision))revisions.set(r.data.window,r.data.revision);
  if(r.data.window?.id)revisions.set(r.data.window.id,r.data.window.revision);
  return r.data;
 };
 const home=who=>request(who,{op:"home"});
 const read=(who,w,x)=>request(who,{op:"read",window:w,workspace:x});
 const body=async(who,w,action,data={},x=null)=>({op:"command",window:w,workspace:x,key:crypto.randomUUID(),expected:w?(revisions.get(w)??(await home(who)).windows.find(v=>v.id===w).revision):0,action,data});
 const command=async(who,w,action,data={},x=null)=>request(who,await body(who,w,action,data,x));
 async function prepare(unit="kg",future=false){
 const now=Date.now();const receipt=await command("trainer",null,"prepare",{scenario:unit,starts_at:new Date(now+(future?60000:0)).toISOString(),ends_at:new Date(now+3600000).toISOString()});
 (report.windows??=[]).push(receipt.window);return receipt;
 }
 const cleanup=async w=>{await command("trainer",w,"revoke");await command("trainer",w,"cleanup");};
 await check("anonymous and direct private-table access denied",async()=>{await api.anonymous();await api.direct();});
 await check("ordinary and unrelated trainer denied; no proof denied",async()=>{
 denied(await api.raw("plain",{op:"home"}),"synthetic_identity_required");denied(await api.raw("foreign",{op:"home"}),"synthetic_identity_required");denied(await api.raw("trainer",{op:"home"},false),"synthetic_disabled_or_proof_required");
 });
 let w=(await prepare()).window;
 await check("prepared window has no fixture read access",async()=>{
 const x=(await api.json("select jsonb_build_object('id',id) from fmz6e10_private.workspaces where window_id="+api.lit(w)+" and route='A'")).id;
 denied(await api.raw("member",{op:"read",window:w,workspace:x}));
 });
 const activation=await body("trainer",w,"activate");
 await check("activation exact retry is idempotent; fresh-key duplicate denied",async()=>{
 const first=await request("trainer",activation);const again=await request("trainer",activation);assert.equal(again.replay,true);assert.equal(first.revision,again.revision);
 denied(await api.raw("trainer",await body("trainer",w,"activate")));
 });
 const ha=await home("member"),hb=await home("b");
 await check("24-hour hard maximum and exact inclusive-start/exclusive-end boundary",async()=>{
  const now=Date.now();
  denied(await api.raw("trainer",await body("trainer",null,"prepare",{scenario:"kg",starts_at:new Date(now).toISOString(),ends_at:new Date(now+86400001).toISOString()})));
  const bounds=await api.json("select jsonb_build_array(fmz6e10_private.window_at(v,v.starts_at-interval '1 microsecond'),fmz6e10_private.window_at(v,v.starts_at),fmz6e10_private.window_at(v,v.ends_at-interval '1 microsecond'),fmz6e10_private.window_at(v,v.ends_at),fmz6e10_private.window_at(v,v.ends_at+interval '1 microsecond')) from fmz6e10_private.windows v where id="+api.lit(w));
  assert.deepEqual(bounds,[false,true,true,false,false]);
 });
 const x=ha.workspaces.find(x=>x.window===w).workspace,xb=hb.workspaces.find(x=>x.window===w).workspace;
 await check("Route A/B and operator data-plane isolation",async()=>{
 assert.equal((await read("member",w,x)).route,"A");assert.equal((await read("b",w,xb)).sources.length,0);
 denied(await api.raw("trainer",{op:"read",window:w,workspace:xb}));
 denied(await api.raw("b",{op:"read",window:w,workspace:x}));
 denied(await api.raw("b",await body("b",w,"propose",{},xb)));
 });
 const initial=await read("trainer",w,x),source=initial.source_template;
 const append=async b=>command("trainer",w,"source_append",{body:b,valid_from:initial.window.starts_at,valid_until:initial.window.ends_at},x);
 await check("member source write and client role spoof denied",async()=>{
 denied(await api.raw("member",await body("member",w,"source_append",{body:source,valid_from:initial.window.starts_at,valid_until:initial.window.ends_at},x)));
 denied(await api.raw("trainer",{op:"home",role:"operator"}));
 denied(await api.raw("member",await body("member",w,"prepare",{},null)));
 });
 await check("missing source never invents proposal",async()=>denied(await api.raw("member",await body("member",w,"propose",{},x))));
 await check("missing fields and null source values fail closed",async()=>{
  for(const mutate of [s=>delete s.rules[0].weight_step,s=>s.rules[0].weight_step=null,s=>s.rules[0].unit=null,s=>s.rules[0].selector.id=null,s=>s.note=null]){
   const s=clone(source);mutate(s);denied(await api.raw("trainer",await body("trainer",w,"source_append",{body:s,valid_from:initial.window.starts_at,valid_until:initial.window.ends_at},x)));
  }
 });
 await append(source);
 await check("source versions cannot be overwritten even by privileged maintenance",async()=>{
  await assert.rejects(()=>api.sql("update fmz6e10_private.source_versions set body=body where workspace_id="+api.lit(x)));
 });
 await check("all health/recovery guards and withdrawn consent block proposal without partial writes",async()=>{
  for(const guard of ["current","serious","recurring","unclassified","self_reported","missing"]){
   await api.sql("update fmz6e10_private.workspaces set guard="+api.lit(guard)+" where id="+api.lit(x));
   denied(await api.raw("member",await body("member",w,"propose",{},x)));
  }
  await api.sql("update fmz6e10_private.workspaces set guard='clear',consent=false where id="+api.lit(x));
  denied(await api.raw("trainer",await body("trainer",w,"propose",{},x)));
  await api.sql("update fmz6e10_private.workspaces set consent=true where id="+api.lit(x));
 });
 await check("removed A link and unexpected B trainer deny reads",async()=>{
  try{
   await api.sql("update public.profiles set trainer_id=null where id="+api.lit(api.ids.member));
   denied(await api.raw("member",{op:"read",window:w,workspace:x}));
   await api.sql("update public.profiles set trainer_id="+api.lit(api.ids.trainer)+" where id="+api.lit(api.ids.b));
   denied(await api.raw("b",{op:"read",window:w,workspace:xb}));
  }finally{
   await api.sql("update public.profiles set trainer_id="+api.lit(api.ids.trainer)+" where id="+api.lit(api.ids.member));
   await api.sql("update public.profiles set trainer_id=null where id="+api.lit(api.ids.b));
  }
 });
 await check("v1 source hash and immutable numeric decisions",async()=>{
 const r=await command("trainer",w,"propose",{},x);const view=await read("member",w,x),p=view.proposals.find(p=>p.id===r.proposal);
 assert.equal(p.source_version,1);assert.equal(p.source_hash,view.sources[0].hash);
 assert.deepEqual(p.reflection.rows.map(r=>r.kind),["reps","weight","hold"]);
 assert.equal(p.reflection.rows[0].next[0].reps,9);assert.equal(p.reflection.rows[1].next[0].load,42.5);
 });
 let p=(await read("member",w,x)).proposals.at(-1);
 const proposalData=()=>({proposal:p.id,proposal_version:p.version});
 await check("separate member approval then exact trainer approval required",async()=>{
 denied(await api.raw("member",await body("member",w,"member_accept",{proposal:p.id,proposal_version:null},x)));
 denied(await api.raw("member",await body("member",w,"member_accept",{proposal:p.id,proposal_version:String(p.version)},x)));
 denied(await api.raw("trainer",await body("trainer",w,"apply",proposalData(),x)));
 denied(await api.raw("member",await body("member",w,"trainer_approve",proposalData(),x)));
 await command("member",w,"member_accept",proposalData(),x);
 denied(await api.raw("trainer",await body("trainer",w,"apply",proposalData(),x)));
 });
 await check("source v2 after member acceptance leaves v1 immutable and blocks approval/apply",async()=>{
 const old=clone((await read("member",w,x)).proposals.at(-1));
 const v2=clone(source);v2.rules[0].reps_step=2;await append(v2);
 denied(await api.raw("trainer",await body("trainer",w,"trainer_approve",proposalData(),x)));
 const now=(await read("member",w,x)).proposals.find(q=>q.id===p.id);
 assert.equal(now.source_hash,old.source_hash);assert.deepEqual(now.target,old.target);assert(now.stale);
 });
 await command("trainer",w,"propose",{},x);p=(await read("member",w,x)).proposals.at(-1);
 await command("member",w,"member_accept",proposalData(),x);await command("trainer",w,"trainer_approve",proposalData(),x);
 await check("source change after trainer approval invalidates separate application",async()=>{
 await append(source);denied(await api.raw("trainer",await body("trainer",w,"apply",proposalData(),x)));
 });
 await command("trainer",w,"propose",{},x);p=(await read("member",w,x)).proposals.at(-1);
 await command("member",w,"member_accept",proposalData(),x);await command("trainer",w,"trainer_approve",proposalData(),x);
 await check("wrong proposal version and stale window revision denied",async()=>{
 denied(await api.raw("trainer",await body("trainer",w,"apply",{...proposalData(),proposal_version:999},x)));
 const stale=await body("trainer",w,"apply",proposalData(),x);stale.expected--;denied(await api.raw("trainer",stale));
 });
 await check("fault before receipt rolls back plan, approvals and audit",async()=>{
 const before=await read("trainer",w,x);
 await api.sql("create function fmz6e10_private.test_fault() returns trigger language plpgsql as $$begin raise exception 'synthetic_forced_fault';end$$;create trigger test_fault before insert on fmz6e10_private.requests for each row execute function fmz6e10_private.test_fault()");
 try{denied(await api.raw("trainer",await body("trainer",w,"apply",proposalData(),x)));}
 finally{await api.sql("drop trigger test_fault on fmz6e10_private.requests;drop function fmz6e10_private.test_fault()");}
 assert.deepEqual(await read("trainer",w,x),before);
 });
 const applyBody=await body("trainer",w,"apply",proposalData(),x);
 await check("concurrent apply commits once; same-key replay and changed-payload rejection",async()=>{
 const both=await api.concurrent("trainer",[applyBody,{...applyBody,key:crypto.randomUUID()}]);
 assert.equal(both.filter(r=>r.status===200).length,1);
 // Whichever unique key won, no fresh-key second application can change the version.
 assert.equal((await read("member",w,x)).active_version,2);
 denied(await api.raw("trainer",await body("trainer",w,"apply",proposalData(),x)));
 const winner=both[0].status===200?applyBody:null;
 if(winner){assert.equal((await request("trainer",winner)).replay,true);denied(await api.raw("trainer",{...winner,data:{...winner.data,proposal_version:999}}));}
 });
 await check("restore creates new version with original and current source references",async()=>{
 await command("member",w,"restore",{plan_version:1},x);p=(await read("member",w,x)).proposals.at(-1);
 assert.equal(p.restored_from.plan_version,1);assert.equal(p.restored_from.original_source_ref,null);
 await command("member",w,"member_accept",proposalData(),x);await command("trainer",w,"trainer_approve",proposalData(),x);await command("trainer",w,"apply",proposalData(),x);
 const v=await read("member",w,x);assert.equal(v.active_version,3);assert.equal(v.plans.length,3);
 assert.equal(v.plans[1].source_ref.version,3);assert.equal(v.plans[2].restored_from.plan_version,1);
 });
 await check("withdrawn source blocks new proposals",async()=>{
 await command("trainer",w,"source_withdraw",{source_version:3},x);denied(await api.raw("member",await body("member",w,"propose",{},x)));
 assert.equal((await read("member",w,x)).sources.at(-1).status,"withdrawn");
 });
 await check("withdrawn source before acceptance; expired source before review",async()=>{
  const currentSource=clone(source);currentSource.comparable_plan_versions=[1,3];
  await append(currentSource);
  const r=await command("member",w,"propose",{},x);
  assert.equal(r.status,"member_pending");
  await command("trainer",w,"source_withdraw",{source_version:4},x);
  denied(await api.raw("member",await body("member",w,"member_accept",{proposal:r.proposal,proposal_version:r.proposal_version},x)),"synthetic_source_unavailable");
  const end=new Date(Date.now()+20000).toISOString();
  await command("trainer",w,"source_append",{body:currentSource,valid_from:initial.window.starts_at,valid_until:end},x);
  const r2=await command("member",w,"propose",{},x);
  assert.equal(r2.status,"member_pending");
  await new Promise(resolve=>setTimeout(resolve,Math.max(0,new Date(end).getTime()-Date.now()+20)));
  denied(await api.raw("member",await body("member",w,"member_accept",{proposal:r2.proposal,proposal_version:r2.proposal_version},x)),"synthetic_source_unavailable");
 });
 await check("other window cannot reuse fixture ID and overlapping activation is denied",async()=>{
 const second=(await prepare()).window;
 denied(await api.raw("member",{op:"read",window:second,workspace:x}));
 denied(await api.raw("trainer",await body("trainer",second,"activate")));await cleanup(second);
 });
 await check("revocation immediately denies old authenticated read; cleanup retries safe",async()=>{
 await command("trainer",w,"revoke");denied(await api.raw("member",{op:"read",window:w,workspace:x}));
 const c=await body("trainer",w,"cleanup");await request("trainer",c);assert.equal((await request("trainer",c)).replay,true);
 await command("trainer",w,"cleanup");
 const totals=await api.json("select jsonb_build_object('fixtures',(select count(*) from fmz6e10_private.workspaces where window_id="+api.lit(w)+"),'sources',(select count(*) from fmz6e10_private.source_versions where workspace_id="+api.lit(x)+"))");
 assert.deepEqual(totals,{fixtures:0,sources:0});
 });
 await check("future start refused and expired window cannot reactivate",async()=>{
 const f=(await prepare("kg",true)).window;denied(await api.raw("trainer",await body("trainer",f,"activate")));
 await api.sql("update fmz6e10_private.windows set created_at=clock_timestamp()-interval '1 hour',starts_at=clock_timestamp()-interval '1 hour',ends_at=clock_timestamp() where id="+api.lit(f));
 denied(await api.raw("trainer",await body("trainer",f,"activate")));await cleanup(f);
 });
 for(const unit of ["kg","lb"]){
 const f=await api.fixture(unit);
 await check(unit+" exact-unit progression; original values retained",async()=>{
 const r=await api.calculate(f.source_template,f.plan,f.observations,1);assert(r.allowed);assert.equal(r.rows[1].next[0].load,unit==="kg"?42.5:105);
 });
 for(const [name,mutate,throws=false] of [
 ["W1 ambiguous exercise/type",f=>f.source_template.rules.push({...clone(f.source_template.rules[0]),id:"syn-extra-rule",selector:{kind:"type",id:"syn-lower"}})],
 ["W2 full step outside available weights",f=>f.source_template.rules[1].weight_step=unit==="kg"?3:7],
 ["missing rule",f=>f.source_template.rules.splice(0,1)],
 ["missing weight step",f=>delete f.source_template.rules[0].weight_step,true],
 ["mixed unit",f=>f.source_template.rules[0].unit=unit==="kg"?"lb":"kg"],
 ["RIR required but missing",f=>{f.source_template.rules[0].rir.required=true;f.observations[0].exercises[0].sets[0].rir=null;}],
 ["RPE zero is invalid, not missing",f=>f.observations[0].exercises[0].sets[0].rpe=0],
 ["partial set registration",f=>f.observations[0].exercises[0].sets.pop()],
 ["wrong set identity",f=>f.observations[0].exercises[0].sets[0].index=9],
 ["duplicate exercise observations",f=>f.observations[0].exercises.push(clone(f.observations[0].exercises[0]))],
 ["non-comparable source version",f=>f.observations[0].plan_version=999],
 ["missing historical goal",f=>f.observations[0].goal_ref="syn-other"],
 ["absent goal key",f=>delete f.observations[0].goal_ref],
 ["absent completed key",f=>delete f.observations[0].completed],
 ["absent observed unit",f=>delete f.observations[0].exercises[0].unit],
 ["absent observed set index",f=>delete f.observations[0].exercises[0].sets[0].index],
 ["duplicate session",f=>f.observations.push(clone(f.observations[0]))],
 ["exercise type mismatch",f=>f.plan.exercises[0].type="syn-push"]
 ]){
 await check(unit+" "+name,async()=>{
 const z=clone(f);mutate(z);
 if(throws){await assert.rejects(()=>api.calculate(z.source_template,z.plan,z.observations,1));}
 else{const r=await api.calculate(z.source_template,z.plan,z.observations,1);assert.equal(r.allowed,false);assert.equal(r.target,null);
 if(name.startsWith("W2")){assert.equal(r.rows[1].weight_step,unit==="kg"?3:7);assert.equal(r.rows[1].attempted_load,unit==="kg"?43:107);}}
 });
 }
 await check(unit+" RIR zero valid and optional RPE null preserved",async()=>{
 const z=clone(f);z.source_template.rules[0].rir={required:true,min:0,max:0};z.observations[0].exercises[0].sets[0].rpe=null;
 const r=await api.calculate(z.source_template,z.plan,z.observations,1);assert(r.allowed);assert.equal(r.rows[0].kind,"reps");
 });
 }
}
