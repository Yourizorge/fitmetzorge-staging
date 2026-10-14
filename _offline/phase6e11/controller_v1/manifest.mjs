import {Controller,Halt,UUID,sha,canonical} from './core.mjs';
import {ENDCHAIN_RUN_ID,PURPOSE,limitFor} from '../endchain_v1/budget.mjs';
const AUTH=new Set(['issue','verify','get_user','refresh','logout','revoked_denial']);
const BY_ROLE={
 a_member:new Set(['propose','restore','member_accept','member_reject','viewed','later']),
 a_trainer:new Set(['source_append','source_withdraw','trainer_approve','trainer_reject','trainer_block','apply','revoke','cleanup_batch']),
 b_member:new Set(['b_build','b_edit','b_confirm','b_apply','b_restore','b_reopen','b_reject','viewed','later'])};
const fail=code=>{throw new Halt('manifest',code);};
function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}

export function validateManifest(value){
 const m=structuredClone(value);
 const full=m?.version===2&&m.run_id===ENDCHAIN_RUN_ID&&m.budget_ref===PURPOSE;
 if(!m||(!full&&m.version!==1)||!Array.isArray(m.identities)||m.identities.length!==3||!Array.isArray(m.workspaces)||m.workspaces.length!==2||
    !Array.isArray(m.actions)||m.actions.length<1||m.actions.length>(full?128:64)||!Number.isSafeInteger(m.max_commands)||m.max_commands<1||m.max_commands>limitFor({id:m.run_id,budget_ref:m.budget_ref}))fail('manifest_shape');
 const identities=new Map();
 for(const identity of m.identities){
  if(!identity||!UUID.test(identity.id)||!Object.hasOwn(BY_ROLE,identity.role)||identities.has(identity.role))fail('identity_allowlist');
  identities.set(identity.role,identity);
 }
 if(new Set(m.identities.map(x=>x.id)).size!==3)fail('identity_collision');
 if(identities.get('a_member').trainer_id!==identities.get('a_trainer').id||identities.get('a_trainer').trainer_id!==null||identities.get('b_member').trainer_id!==null)fail('trainer_relation');
 const workspaces=new Map();
 for(const w of m.workspaces){
  if(!w||!UUID.test(w.id)||!UUID.test(w.window)||!['A','B'].includes(w.route)||workspaces.has(w.route))fail('workspace_allowlist');
  if(w.member!==identities.get(w.route==='A'?'a_member':'b_member').id||w.trainer!==(w.route==='A'?identities.get('a_trainer').id:null))fail('workspace_relation');
  workspaces.set(w.route,w);
 }
 if(m.workspaces[0].id===m.workspaces[1].id||m.workspaces[0].window!==m.workspaces[1].window)fail('workspace_collision');
 const actions=new Set(),requests=new Set();
 for(const [index,c] of m.actions.entries()){
  const actor=m.identities.find(x=>x.id===c?.actor);
  if(!actor||c.step!==index||!UUID.test(c.action_id)||!UUID.test(c.request_id)||actions.has(c.action_id)||requests.has(c.request_id)||!Array.isArray(c.writes))fail('action_allowlist');
  actions.add(c.action_id);requests.add(c.request_id);
  if(c.kind==='auth'){
   if(!AUTH.has(c.operation)||c.workspace!==null||c.writes.length!==0)fail('auth_scope');
  }else if(c.kind==='workflow'){
   const w=m.workspaces.find(x=>x.id===c.workspace);
   const operatorCleanup=full&&c.operation==='cleanup_batch'&&actor.role==='a_trainer'&&
    m.cleanup?.operator_id===actor.id&&m.cleanup?.requires_revoked_window===true&&
    c.writes.length>0&&c.writes.length<=8&&c.writes.every(x=>x.operation==='DELETE');
   if(full&&c.operation==='cleanup_batch'&&!operatorCleanup)fail('cleanup_scope');
   if(!w||!BY_ROLE[actor.role].has(c.operation)||
      !operatorCleanup&&(actor.role==='b_member')!==(w.route==='B'))fail('workflow_scope');
   for(const write of c.writes){
    if(!write||!/^fmz6e11_private\.[a-z_]+$/.test(write.table)||!['INSERT','UPDATE','DELETE'].includes(write.operation)||
       !Array.isArray(write.key)||!write.key.length||write.key.some(k=>typeof k!=='string'&&!Number.isSafeInteger(k)))fail('write_scope');
   }
  }else fail('action_kind');
 }
 return freeze(m);
}

// Only a server-compiled manifest may supply identities/actions. HTTP has no
// actor, role, SQL, action index or payload parameters.
export async function boundController({manifest,grant,store,now=Date.now}){
 const fixed=validateManifest(manifest);
 if(fixed.version===2&&(grant.id!==fixed.run_id||grant.budget_ref!==fixed.budget_ref||limitFor(grant)!==limitFor({id:fixed.run_id,budget_ref:fixed.budget_ref})))fail('manifest_run_binding');
 if(await sha(fixed)!==grant.manifest_sha)fail('manifest_hash');
 const controller=new Controller({grant,store,now,maxCommands:fixed.max_commands});
 const execute=controller.execute.bind(controller);
 controller.execute=async(contract,adapter)=>{
  if(!fixed.actions[controller.step]||canonical(contract)!==canonical(fixed.actions[controller.step]))fail('contract_not_registered');
  return execute(fixed.actions[controller.step],adapter);
 };
 return {controller,manifest:fixed};
}
