import {Halt,UUID} from '../controller_v1/core.mjs';
import {assertIdentity,EMAILS} from '../controller_v1/auth.mjs';
import {LOCK_IDENTITY} from '../controller_v1/auth_guard.mjs';

const HASH=/^[0-9a-f]{64}$/;
export function guardedIssuance({receipt,query,check,now=Date.now}){
 if(!receipt||!UUID.test(receipt.run)||receipt.schema!=='fmz6e11_guard_'+receipt.run.replaceAll('-','')||
    !HASH.test(receipt.function_sha)||!Number.isFinite(Date.parse(receipt.expires_at))||typeof query!=='function'||typeof check!=='function')
  throw new Halt('auth_guard','guard_receipt_invalid');
 const fixed=Object.freeze(structuredClone(receipt));
 const expectedNames=['_d','_i','_u'].map(x=>fixed.schema+x);
 if(JSON.stringify(Object.keys(fixed.trigger_shas||{}).sort())!==JSON.stringify(expectedNames)||Object.values(fixed.trigger_shas).some(x=>!HASH.test(x)))
  throw new Halt('auth_guard','guard_receipt_invalid');
 let busy=false,closed=false;
 const enough=()=>{
  check();
  if(closed||Date.parse(fixed.expires_at)-now()<=60000)throw new Halt('auth_guard','guard_expired_or_closing');
 };
 const attestation=`/* fmz6e11:controller_guard_v1:attest */
select encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex') function_sha,
 ((obj_description(p.oid,'pg_proc')::jsonb->>'expires_at')::timestamptz>clock_timestamp()+interval '60 seconds') unexpired,
 p.prosecdef definer,p.proconfig search_path, p.proacl::text acl,
 (select jsonb_object_agg(t.tgname,encode(sha256(convert_to(pg_get_triggerdef(t.oid),'UTF8')),'hex'))
 from pg_trigger t where t.tgfoid=p.oid and t.tgrelid='auth.users'::regclass and t.tgenabled='O') trigger_shas
from pg_proc p where p.oid=to_regprocedure($1)`;
 const issue=async(expected,action)=>{
  enough();
  if(busy||!UUID.test(expected?.id)||!Object.hasOwn(EMAILS,expected?.role)||typeof action!=='function')throw new Halt('auth_guard','guard_action_invalid');
  busy=true;let began=false;
  try{
   await query('BEGIN');began=true;
   await query("SET LOCAL lock_timeout='1s'");
   await query("SET LOCAL statement_timeout='2s'");
   const identity=await query(LOCK_IDENTITY,[expected.id,EMAILS[expected.role]]);
   if(identity.length!==1)throw new Halt('auth_guard','identity_not_allowlisted');
   assertIdentity(identity[0],expected);
   const rows=await query(attestation,[fixed.schema+'.identity_guard()']);
   const value=rows[0];
   if(rows.length!==1||value.function_sha!==fixed.function_sha||value.unexpired!==true||value.definer!==false||
      value.acl!=='{postgres=X/postgres}'||JSON.stringify(value.search_path)!==JSON.stringify(['search_path=pg_catalog, pg_temp'])||
      Object.keys(value.trigger_shas||{}).length!==3||expectedNames.some(n=>value.trigger_shas[n]!==fixed.trigger_shas[n]))
    throw new Halt('auth_guard','guard_attestation_failed');
   enough();const result=await action();enough();return result;
  }catch(error){closed=true;throw error;}
  finally{
   try{if(began)await query('ROLLBACK');}
   catch{closed=true;throw new Halt('auth_guard','identity_unlock_unconfirmed');}
   finally{busy=false;}
  }
 };
 issue.close=()=>{closed=true;};
 return issue;
}

// Removal is a distinct safety capability, not Controller.execute/fixture cleanup.
export async function withSafetyRemoval({run,closeIssuance,remove,verifyRemoved}){
 let result,error;
 try{result=await run();}catch(e){error=e;}
 finally{
  closeIssuance();
  try{await remove();if(await verifyRemoved()!==true)throw new Error();}
  catch{throw new Halt('guard_removal','guard_removal_unconfirmed');}
 }
 if(error)throw error;
 return result;
}
