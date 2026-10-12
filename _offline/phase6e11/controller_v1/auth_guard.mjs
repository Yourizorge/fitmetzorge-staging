import {Halt,UUID} from './core.mjs';
import {assertIdentity,EMAILS} from './auth.mjs';
export const LOCK_IDENTITY=`/* fmz6e11:controller_v1:identity_lock */
select u.id::text,u.email,i.role registered_role,p.role profile_role,p.trainer_id::text,
i.enabled,exists(select 1 from fmz6e11_private.operators o where o.user_id=u.id and o.enabled) operator,
exists(select 1 from pg_index ix join pg_attribute a on a.attrelid=ix.indrelid
 where ix.indrelid='auth.users'::regclass and a.attname='email' and a.attnum=any(ix.indkey)
 and ix.indisunique and ix.indisvalid and ix.indimmediate and ix.indpred is null and ix.indexprs is null) alias_key_locked
from auth.users u join public.profiles p on p.id=u.id
join fmz6e11_private.identities i on i.user_id=u.id
where u.id=$1::uuid and u.email=$2 and p.email=$2
for share of i,p for key share of u`;

// One dedicated server connection; callers cannot inject SQL or identities.
// The Auth service uses a separate transaction. This rollback releases locks;
// it cannot undo an Auth side effect or substitute for its after-measurement.
export function existingIdentityGuard({query,check}){
 if(typeof query!=='function'||typeof check!=='function')throw new Halt('configuration','identity_guard_absent');
 let busy=false;
 return async(expected,action)=>{
  check();
  if(busy||!UUID.test(expected?.id)||!Object.hasOwn(EMAILS,expected?.role)||typeof action!=='function')
   throw new Halt('auth_guard','identity_guard_scope');
  busy=true;let began=false;
  try{
   await query('BEGIN');began=true;
   await query("SET LOCAL lock_timeout='1s'");
   await query("SET LOCAL statement_timeout='2s'");
   const rows=await query(LOCK_IDENTITY,[expected.id,EMAILS[expected.role]]);
   if(rows.length!==1)throw new Halt('auth_guard','identity_not_allowlisted');
   assertIdentity(rows[0],expected);
   // A partial unique email index does not participate in KEY SHARE protection.
   // No assumption that aliases remain unchanged may grant hosted authority.
   if(rows[0].alias_key_locked!==true)throw new Halt('auth_guard','alias_stability_unproven');
   check();
   return await action();
  }finally{
   try{if(began)await query('ROLLBACK');}
   catch{throw new Halt('auth_guard','identity_unlock_unconfirmed');}
   finally{busy=false;}
  }
 };
}
