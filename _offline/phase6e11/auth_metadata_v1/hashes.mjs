// v1 binds the existing canonical JSON hash to PostgreSQL's UTF-8 UUID key hash.
import {sha,UUID,Halt,metadata} from '../controller_v1/core.mjs';
export async function bindSession(auth,result){
 const id=auth.session();
 if(!UUID.test(id)||result.session_sha!==await sha(id))throw new Halt('evidence','session_hash_binding');
 const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(id)));
 return metadata({...result,key_sha:[...bytes].map(x=>x.toString(16).padStart(2,'0')).join(''),version:1});
}
