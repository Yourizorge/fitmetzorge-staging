import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {broker,makeApi,root,BASE,PUB} from '../test/live.mjs';
import * as audit from './followup-audit.mjs';

// One-shot owner-authorized closure; no account deletion or runtime/configuration change.
assert.equal(audit.enabled,true,'measured_closure_required');
const file=path.join(root,'supabase/.temp/phase6e10-owner-closure.json');
assert(!fs.existsSync(file),'closure_receipt_exists_inspect_do_not_overwrite');
const opening=JSON.parse(fs.readFileSync(path.join(root,'supabase/.temp/phase6e10-owner-window.json')));
assert.equal(opening.opened,true);
assert.match(opening.window,/^[a-f0-9-]{36}$/);
const out={pass:false,owner_physical_retest:'explicitly accepted in conversation',
 accounts_deleted:0,password_changes:0,emails:0,external_ai_calls:0,production_touched:false,
 checks:[],started_at:new Date().toISOString()};
const persist=()=>fs.writeFileSync(file,JSON.stringify(out,null,2)+'\n');
const b=broker();let api,started=false,finishing=false;
async function checkpoint(name){await audit.checkpoint(name,true);out.checks.push(name);persist();}
try{
 await audit.begin('owner-closure');started=true;persist();
 api=await makeApi(b);
 assert.deepEqual(Object.keys(api.ids).sort(),['b','member','trainer']);
 const read=async(role,p)=>{const r=await api.raw(role,p);assert.equal(r.status,200,'expected_success:'+p.op);return r.data;};
 const home=()=>read('trainer',{op:'home'});
 let h=await home(),w=h.windows.find(x=>x.id===opening.window);
 assert(w&&h.operator,'exact_owner_window_and_operator_required');
 assert(!h.windows.some(x=>x.id!==opening.window&&['active','prepared','expired','revoked'].includes(x.status)),'unexpected_unclosed_window');
 const W=api.lit(opening.window);
 const workspaces=await api.sql('select id,route,member_id,trainer_id from fmz6e10_private.workspaces where window_id='+W+' order by route');
 assert.equal(workspaces.length,2);
 for(const x of workspaces){
  assert.equal(x.member_id,api.ids[x.route==='A'?'member':'b']);
  assert.equal(x.trainer_id,x.route==='A'?api.ids.trainer:null);
 }
 const aggregate=await api.json(`select jsonb_build_object(
 'source_versions',(select coalesce(jsonb_agg(jsonb_build_object('version',version,'hash',hash) order by version),'[]') from fmz6e10_private.source_versions where workspace_id in(select id from fmz6e10_private.workspaces where window_id=${W})),
 'plan_versions',(select coalesce(jsonb_agg(jsonb_build_object('version',version,'hash',hash,'restored',restored_from is not null) order by version),'[]') from fmz6e10_private.plans where workspace_id in(select id from fmz6e10_private.workspaces where window_id=${W})),
 'proposal_states',(select coalesce(jsonb_agg(jsonb_build_object('version',version,'status',status,'source_version',source_version,'base_version',base_version,'separate_actors',member_actor is not null and trainer_actor is not null and member_actor<>trainer_actor) order by version),'[]') from fmz6e10_private.proposals where workspace_id in(select id from fmz6e10_private.workspaces where window_id=${W})),
 'audit_actions',(select coalesce(jsonb_agg(v),'[]') from(select i.role,a.action,count(*) count,min(a.at) first_at,max(a.at) last_at from fmz6e10_private.audit a join fmz6e10_private.identities i on i.user_id=a.actor where a.window_id=${W} group by i.role,a.action order by i.role,a.action)v))`);
 out.before={status:w.status,ends_at:w.ends_at,workspaces:2,...aggregate};persist();
 await api.anonymous();await checkpoint('exact_synthetic_ownership_and_preclosure_evidence');
 const command=async(action,key=crypto.randomUUID())=>{
  h=await home();w=h.windows.find(x=>x.id===opening.window);
  const p={op:'command',window:opening.window,workspace:null,key,expected:w.revision,action,data:{}};
  return {p,r:await read('trainer',p)};
 };
 if(!['revoked','cleaned'].includes(w.status))await command('revoke');
 h=await home();w=h.windows.find(x=>x.id===opening.window);assert.equal(w.status,'revoked');
 for(const role of ['member','trainer','b']){
  const x=workspaces.find(x=>x.route===(role==='b'?'B':'A'));
  const r=await api.raw(role,{op:'read',window:opening.window,workspace:x.id});
  assert.equal(r.status,403,'revoked_window_must_deny');
 }
 await checkpoint('revoked_window_denies_three_still_signed_sessions');
 const cleanup=await command('cleanup');
 h=await home();w=h.windows.find(x=>x.id===opening.window);
 assert.equal(w.status,'cleaned');assert.equal(w.cleanup.workspaces,2);assert.equal(w.cleanup.accounts_deleted,0);
 assert.equal((await api.sql('select id from fmz6e10_private.workspaces where window_id='+W)).length,0);
 assert.equal((await api.sql('select user_id from fmz6e10_private.participants where window_id='+W)).length,0);
 out.cleanup={...w.cleanup,status:w.status,closed_at:new Date().toISOString()};
 await checkpoint('exact_window_fixtures_removed_accounts_retained');
 const replay=await read('trainer',cleanup.p);assert.equal(replay.replay,true);
 for(const role of ['member','trainer','b']){
  const r=await read(role,{op:'home'});assert.equal(r.workspaces.length,0);
  if(role!=='trainer')assert.equal(r.windows.length,0);
 }
 await checkpoint('cleanup_replay_idempotent_no_participant_content');
 // Standard global logout is scoped by each proven synthetic user's own JWT.
 for(const role of ['member','trainer','b']){
  const event=audit.record(role,'logout','auth_logout_global');
  const r=await fetch(BASE+'/auth/v1/logout?scope=global',{method:'POST',headers:{apikey:PUB,Authorization:'Bearer '+api.sessions[role].access_token,'Content-Type':'application/json'},body:'{}',signal:AbortSignal.timeout(20000)});
  await r.text();audit.response(event,r.status);assert([200,204].includes(r.status),'synthetic_global_logout_failed');
 }
 const remaining=await api.json('select count(*) from auth.sessions where user_id in(select user_id from fmz6e10_private.identities)');
 assert.equal(remaining,0,'synthetic_sessions_remain');
 for(const role of ['member','trainer','b']){
  const r=await api.raw(role,{op:'home'});assert([401,403].includes(r.status),'signed_jwt_not_refused');
 }
 out.sessions_revoked=true;out.still_signed_jwts_refused=3;
 out.operator_configuration_retained=true;out.owner_window_access=false;
 await checkpoint('global_logout_three_identities_and_strict_session_denial');
 finishing=true;await audit.finish(true);
 out.pass=true;out.finished_at=new Date().toISOString();persist();
 console.log(JSON.stringify({pass:true,closed_at:out.cleanup.closed_at,workspaces_removed:2,accounts_retained:3,signed_jwts_refused:3,checks:out.checks.length,production_touched:false}));
}catch{
 out.pass=false;out.requires_inspection=true;persist();
 if(started&&!finishing){try{await audit.finish(false);}catch{}}
 console.error('owner_closure_incomplete_inspect_sanitized_receipts');process.exitCode=1;
}finally{b.assertQuiet();await b.close();}
