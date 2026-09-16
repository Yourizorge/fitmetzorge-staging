import fs from 'node:fs';
import path from 'node:path';
import cp from 'node:child_process';
import readline from 'node:readline';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
export const enabled=process.env.FMZ6E10_FOLLOWUP==='1';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const roles={member:'a_member',trainer:'a_trainer',b:'b_member'};
let pipe,queue=[],state,baseline,before,start=0,file,tokens=[];
const compact=s=>s.tables.map(r=>[r.name,r.protected_rows,r.protected_sha256]);
const protectedEqual=(a,b)=>assert.deepEqual(compact(a),compact(b),'NO_GO: existing protected data changed');
function provider(){
 if(pipe)return;
 pipe=cp.spawn('C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',['-B',path.join(root,'_offline/phase6e10/ops/followup.py')],{cwd:root,windowsHide:true,stdio:['pipe','pipe','pipe']});
 readline.createInterface({input:pipe.stdout}).on('line',line=>{const q=queue.shift();if(!q)return;try{const r=JSON.parse(line);r.ok?q.resolve(r.result):q.reject(Error(r.error));}catch{q.reject(Error('audit_protocol_error'));}});
 pipe.stderr.on('data',()=>{while(queue.length)queue.shift().reject(Error('audit_provider_error'));});
 pipe.on('exit',()=>{while(queue.length)queue.shift().reject(Error('audit_provider_exited'));});
}
const rpc=d=>{provider();return new Promise((resolve,reject)=>{queue.push({resolve,reject});pipe.stdin.write(JSON.stringify(d)+'\n');});};
const persist=()=>fs.writeFileSync(file,JSON.stringify(state,null,2)+'\n');
async function measure(){const s=await rpc({op:'snapshot'});if(baseline)protectedEqual(baseline,s);return s;}
export async function begin(label){
 if(!enabled)return;
 assert(/^[a-z0-9-]+$/.test(label));
 file=path.join(root,'supabase/.temp/phase6e10-followup-'+label+'.json');
 if(fs.existsSync(file))throw Error('audit_receipt_exists_do_not_overwrite');
 const match=JSON.parse(fs.readFileSync(path.join(root,'docs/PHASE6E10_OWNER_MATCH.json')));
 assert.equal(match.pass,true);
 state={label,started_at:new Date().toISOString(),owner_match:true,events:[],tests:[],snapshots:[],pass:false};
 persist();
 baseline=before=await measure();
 for(const prior of match.reconciled_fingerprints){const r=baseline.tables.find(x=>x.name===prior.name);assert(r);assert.equal(r.protected_rows,prior.rows,prior.name);assert.equal(r.protected_sha256,prior.sha256,prior.name);}
 state.snapshots.push(before);persist();
}
export function record(actor,action,transport,extra={}){
 if(!enabled)return null;
 assert(state,'audit must begin before any test operation');
 assert(roles[actor]||actor==='test_operator'||actor==='anonymous','unknown audit actor');
 const event={at:new Date().toISOString(),actor:roles[actor]||actor,action,transport,...extra};state.events.push(event);persist();return event;
}
export function brokerBefore(d){
 if(!enabled)return null;
 if(d.op==='session')return record(d.role,'synthetic_auth_session','standard_auth_no_email');
 if(d.op==='identities')return null;
 if(d.op==='query'){
  const sql=d.sql.trim();if(/^select\s/i.test(sql))return null;
  if(/^update public\.profiles set trainer_id=(null|'[a-f0-9-]+') where id='[a-f0-9-]+'$/i.test(sql))return record('test_operator','fixture_trainer_link','management_sql',{target:'a_member_only'});
  if(/^update fmz6e10_private\.workspaces set consent=(false|true)(,guard='(self_reported|clear)')? where id='[a-f0-9-]+'$/i.test(sql))return record('test_operator','fixture_consent_or_guard','management_sql',{target:'synthetic_A_workspace'});
 }
 throw Error('unregistered_broker_operation');
}
export function brokerAfter(d,r,event){
 if(!enabled||!event)return;
 if(d.op==='session'){const payload=JSON.parse(Buffer.from(r.access_token.split('.')[1],'base64url').toString());tokens.push({actor:d.role,token:r.access_token,session:payload.session_id});}
 event.completed=true;persist();
}
export function request(actor,p,transport='edge'){
 if(!enabled||p?.op!=='command')return null;
 assert(['prepare','activate','revoke','cleanup','source_append','source_withdraw','propose','restore','member_accept','member_reject','trainer_approve','trainer_reject','trainer_block','apply'].includes(p.action),'unregistered command');
 return record(actor,p.action,transport,{expected_revision:p.expected});
}
export function response(event,status){if(enabled&&event){event.http_status=status;persist();}}
export async function checkpoint(name,value=true){
 if(!enabled){assert(value,name);return;}
 const after=await measure();
 const events=state.events.slice(start);
 const previousIds=new Set(before.audit.map(x=>x.id));
 const added=after.audit.filter(x=>!previousIds.has(x.id));
 for(const row of added)assert(events.some(e=>e.actor===row.actor&&e.action===row.action),'unattributed server audit action');
 const changed=after.tables.filter((r,i)=>r.sha256!==before.tables[i].sha256||r.rows!==before.tables[i].rows).map(r=>r.name);
 for(const name of changed){
  if(name.startsWith('fmz6e10_private.'))assert(events.some(e=>e.transport==='edge'||e.transport==='browser_edge'||e.action==='fixture_consent_or_guard'),name);
  else if(name==='public.profiles')assert(events.some(e=>e.action==='fixture_trainer_link'),name);
  else if(name.startsWith('auth.'))assert(events.some(e=>e.action==='synthetic_auth_session'||e.action==='logout'||e.action==='cleanup_test_session'),name);
  else if(name==='cron.job_run_details')assert(after.cron.every(r=>[1,2,7].includes(r.jobid)&&['running','succeeded'].includes(r.status)),name);
  else assert.fail('unexplained write: '+name);
 }
 const beforeIndex=state.snapshots.indexOf(before);state.snapshots.push(after);
 state.tests.push({name,pass:Boolean(value),before:beforeIndex,after:state.snapshots.length-1,events_from:start,events_to:state.events.length,changed_tables:changed,server_actions:added,existing_protected_unchanged:true,nine_unchanged:true});
 start=state.events.length;persist();assert(value,name);
 // A shared boundary is both the preceding after and the next before measurement.
 before=after;persist();
}
export async function cleanupSessions(){
 if(!enabled)return;
 for(const s of tokens){
  const e=record(s.actor,'cleanup_test_session','auth_logout_local');
  const r=await fetch('https://mokxyyullfhkfalopbzd.supabase.co/auth/v1/logout?scope=local',{method:'POST',headers:{apikey:'sb_publishable_6OiMLMl946arkI71-ylqkQ_EQWL6kKT',Authorization:'Bearer '+s.token,'Content-Type':'application/json'},body:'{}',signal:AbortSignal.timeout(20000)});
  await r.text();assert([200,204,401,403].includes(r.status));response(e,r.status);
 }
 tokens=[];
}
export async function finish(success){
 if(!enabled)return;
 try{await checkpoint('final_cleanup_and_preservation',success);state.pass=Boolean(success);state.finished_at=new Date().toISOString();persist();}
 finally{if(pipe)await new Promise(resolve=>{pipe.once('exit',resolve);pipe.stdin.end();});}
}
