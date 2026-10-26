import {bindSession} from '../auth_metadata_v1/hashes.mjs';
import {metadata} from '../controller_v1/core.mjs';

// This is a failure suffix, not another Controller execution or Auth retry.
export async function safetyAuthlogout({send,receipt,auths}) {
 const start=await send({op:'safetyAuthlogout',stage:'start',receipt});
 for(const role of start.roles){
  try{
   await send({op:'safetyAuthlogout',stage:'before',role});
   const result=await bindSession(auths[role],metadata(await auths[role].logout()));
   await send({op:'safetyAuthlogout',stage:'after',role,result});
  }catch{
   // A timeout can be a committed logout. Never repeat HTTP or invent its result.
   break;
  }
 }
 return send({op:'safetyAuthlogout',stage:'finish'});
}
