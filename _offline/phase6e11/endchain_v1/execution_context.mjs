// Trusted private IPC configuration. No browser-selected authority or endpoint.
import {EMAILS} from '../controller_v1/auth.mjs';
import {UUID} from '../controller_v1/core.mjs';

export const AUTH_ORIGIN='https://mokxyyullfhkfalopbzd.supabase.co';
const LOCAL='http://127.0.0.1:59999';
const OPERATIONS=new Set(['/admin/generate_link','/verify','/user','/token','/logout']);

export function executionContext(config,fetcher=fetch){
 const local=config.environment==='disposable_ci';
 if(config.mode!=='registered_synthetic'||(!local&&config.environment!=='staging'))throw Error('execution_environment');
 const expected=local?LOCAL:AUTH_ORIGIN+'/auth/v1';
 if(config.authBase!==expected)throw Error('execution_endpoint');
 const ids=config.registeredIds||config.ids;
 if(!ids||Object.keys(ids).sort().join()!==Object.keys(EMAILS).sort().join()||
    Object.values(ids).some(x=>!UUID.test(x))||new Set(Object.values(ids)).size!==3)throw Error('execution_identities');
 const binding=config.identityBinding;
 if(!binding||binding.project!=='mokxyyullfhkfalopbzd'||binding.preexisting!==true||
    Object.keys(EMAILS).some(role=>binding.identities?.[role]?.id!==ids[role]||
     binding.identities[role].email!==EMAILS[role]||binding.identities[role].registered!==true))throw Error('execution_identity_binding');
 const network=async(url,options={})=>{
  const target=new URL(url);
  if(target.origin!==AUTH_ORIGIN||target.username||target.password||target.hash||
     !target.pathname.startsWith('/auth/v1/'))throw Error('auth_network_scope');
  const path=target.pathname.slice('/auth/v1'.length);
  if(!OPERATIONS.has(path))throw Error('auth_route_not_allowed');
  if(path==='/token'&&target.search!=='?grant_type=refresh_token')throw Error('auth_token_flow');
  if(path!=='/token'&&target.search&&!(path==='/logout'&&target.search==='?scope=local'))throw Error('auth_query_scope');
  return fetcher(expected+path+target.search,{...options,redirect:'error',signal:AbortSignal.timeout(5000)});
 };
 return Object.freeze({ids:Object.freeze({...ids}),local,fetcher:network,authBase:expected});
}
