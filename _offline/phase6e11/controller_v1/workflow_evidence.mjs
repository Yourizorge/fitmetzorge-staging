import {Halt,UUID,canonical,sha} from './core.mjs';
const H=/^[0-9a-f]{64}$/;
const TABLES=new Set(['windows','participants','workspaces','source_versions','source_heads','plans','proposals','audit','requests','b_states','b_versions','inbox_state','events'].map(n=>'fmz6e11_private.'+n));
const failure=code=>{throw new Halt('pair_validated',code);};
const same=(a,b)=>canonical(a)===canonical(b);
const multiset=rows=>rows.map(canonical).sort();
function entry(x){
 if(!x||!same(Object.keys(x).sort(),['new','old','op','table'])||!TABLES.has(x.table)||!['INSERT','UPDATE','DELETE'].includes(x.op))failure('write_shape');
 if(x.op==='INSERT'?(x.old!==null||!H.test(x.new)):x.op==='DELETE'?(!H.test(x.old)||x.new!==null):(!H.test(x.old)||!H.test(x.new)))failure('write_key');
 return x;
}

// The expected multiset is registered from the locked pre-state, never inferred
// from these observed writes. Evidence is accepted only for that exact request.
export async function validateWorkflow(contract,before,receipt,writes,after){
 if(!contract||!UUID.test(contract.request_id)||!UUID.test(contract.actor)||!UUID.test(contract.session_id)||
    !UUID.test(contract.workspace)||!UUID.test(contract.window)||!UUID.test(contract.key)||!H.test(contract.payload_sha)||
    !Array.isArray(contract.expected)||contract.expected.length>64)failure('contract_shape');
 contract.expected.forEach(entry);
 const bindings={request_id:contract.request_id,actor:contract.actor,session_id:contract.session_id,
  workspace_id:contract.workspace,window_id:contract.window,idempotency_key:contract.key,
  payload_sha:contract.payload_sha,route:contract.route,action:contract.operation,selected_branch:contract.outcome};
 for(const [key,value] of Object.entries(bindings))if(receipt?.[key]!==value)failure('receipt_binding');
 if(receipt.state!=='pair_validated'||!UUID.test(receipt.action_id)||!UUID.test(receipt.run_id)||
    !/^\d+$/.test(String(receipt.xid))||!Number.isSafeInteger(receipt.backend)||receipt.backend<1)failure('receipt_incomplete');
 if(!same(receipt.versions_before,contract.versions_before)||!same(receipt.versions_after,contract.versions_after)||
    !same(before.versions,contract.versions_before)||!same(after.versions,contract.versions_after))failure('version_binding');
 if(!H.test(before.sha256)||!H.test(after.sha256)||receipt.before_sha!==before.sha256||receipt.after_sha!==after.sha256)failure('snapshot_binding');
 if(!before.observers_complete||!after.observers_complete||!H.test(before.observer_sha)||before.observer_sha!==after.observer_sha)failure('observer_coverage');
 if(!same(before.protected_rows,after.protected_rows))failure('protected_row_drift');
 if(!Array.isArray(writes)||writes.length>64)failure('write_count');
 const ordinals=new Set();
 const actual=writes.map(w=>{
  if(w.action_id!==receipt.action_id||w.run_id!==receipt.run_id||String(w.xid)!==String(receipt.xid)||w.backend!==receipt.backend||
     w.actor!==contract.actor||w.workspace!==contract.workspace)failure('transaction_binding');
  if(!Number.isSafeInteger(w.ordinal)||w.ordinal<1||ordinals.has(w.ordinal))failure('duplicate_audit_ordinal');
  ordinals.add(w.ordinal);
  return entry({table:w.table_name,op:w.operation,old:w.old_key_sha,new:w.new_key_sha});
 });
 if(!same(multiset(contract.expected),multiset(actual)))failure('write_multiset');
 if(actual.some(w=>w.op==='DELETE'&&!w.old))failure('delete_tombstone_missing');
 return {pair_complete:true,protected_equal:true,evidence_sha:await sha({contract,before,receipt,writes,after}),
  actor_sha:await sha(contract.actor),workspace_sha:await sha(contract.workspace),session_sha:await sha(contract.session_id),
  request_id:contract.request_id,xid:String(receipt.xid),count:actual.length,
  changes:['INSERT','UPDATE','DELETE'].map(operation=>({operation,count:actual.filter(w=>w.op===operation).length}))};
}
