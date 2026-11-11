import {createHandler} from '../edge/handler.mjs';

export const PROJECT = 'mokxyyullfhkfalopbzd';
export const BASE = 'https://' + PROJECT + '.supabase.co';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const EMAILS = new Set([
  'zorgeyouri+6e9-a-lid@gmail.com',
  'zorgeyouri+6e9-a-trainer@gmail.com',
  'zorgeyouri+6e9-b-lid@gmail.com',
]);
const COMMANDS = new Set(['source_append','source_withdraw','propose','restore',
  'member_accept','trainer_approve','apply','member_reject','trainer_reject',
  'trainer_block','b_build','b_edit','b_confirm','b_apply','b_reject','b_restore',
  'b_reopen','viewed','later']);
const failure = (message, status=403) => Object.assign(new Error(message), {safeStatus:status});
const json = (status, message) => Response.json({message}, {status});

function decode(part) {
  if (!/^[A-Za-z0-9_-]+$/.test(part)) throw failure('synthetic_session_required',401);
  const bytes=Uint8Array.from(atob(part.replaceAll('-','+').replaceAll('_','/')),x=>x.charCodeAt(0));
  return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}

export function verifiedClaims(authorization, user, now=Date.now()) {
  try {
    if (!/^Bearer [A-Za-z0-9_.-]{1,8192}$/.test(authorization||'')) throw Error();
    const parts=authorization.slice(7).split('.');
    if (parts.length!==3 || !parts.every(Boolean)) throw Error();
    const header=decode(parts[0]), claims=decode(parts[1]);
    if (!['HS256','ES256','RS256'].includes(header.alg) || header.typ && header.typ!=='JWT') throw Error();
    if (!user || !UUID.test(user.id||'') || claims.sub!==user.id || !EMAILS.has(user.email)) throw Error();
    if (claims.iss!==BASE+'/auth/v1' || claims.aud!=='authenticated' || claims.role!=='authenticated') throw Error();
    if (!Number.isSafeInteger(claims.exp) || claims.exp*1000<=now ||
        !UUID.test(claims.session_id||'') || claims.nbf!==undefined && (!Number.isSafeInteger(claims.nbf) || claims.nbf*1000>now)) throw Error();
    // getUser has already verified the token. Only these verified claims enter SQL.
    return Object.freeze({sub:claims.sub,session_id:claims.session_id,role:'authenticated',
      iss:claims.iss,aud:claims.aud,exp:claims.exp});
  } catch { throw failure('synthetic_session_required',401); }
}

export function createBridgeHandler({url,key,proof,transport,fetcher=fetch,now=Date.now}) {
  if (url!==BASE || typeof transport!=='function') throw Error('staging_transport_required');
  return async req => {
    if (req.headers.has('x-fmz6e11-proof')) return Response.json({error:'payload_invalid'},{status:400});
    let verified=null, boundAuthorization=null;
    const scopedFetch=async (target,options={}) => {
      if (target===BASE+'/auth/v1/user') {
        if (verified || boundAuthorization) return json(401,'synthetic_session_required');
        const response=await fetcher(target,options);
        if (response.ok) {
          try {
            const user=await response.clone().json();
            boundAuthorization=options.headers.Authorization;
            verified=verifiedClaims(boundAuthorization,user,now());
          } catch { return json(401,'synthetic_session_required'); }
        }
        return response;
      }
      if (target!==BASE+'/rest/v1/rpc/fmz6e11_call' || options.method!=='POST' ||
          !verified || options.headers.Authorization!==boundAuthorization)
        return json(403,'synthetic_session_required');
      let input,q;
      try {
        const payload=JSON.parse(options.body);
        if (Object.keys(payload).join()!=='p') throw Error();
        input=payload.p;q=input.op==='internal_b'?input.request:input;
      } catch { return json(400,'synthetic_payload_invalid'); }
      if (['home','read'].includes(q.op)) return fetcher(target,options);
      if (q.op!=='command' || !COMMANDS.has(q.action) || !UUID.test(q.key||'') ||
          !UUID.test(q.window||'') || !UUID.test(q.workspace||''))
        return json(403,'synthetic_audited_route_required');
      if (verified.exp*1000<=now()) return json(401,'synthetic_session_required');
      try {
        const value=await transport({input,claims:verified,proof,requestId:q.key});
        return Response.json(value);
      } catch (error) {
        // Never serialize driver error objects, SQL parameters or environment values.
        const code=/^synthetic_[a-z0-9_]{1,100}$/.test(error?.message||'')?error.message:'synthetic_bridge_unavailable';
        return json(error?.safeStatus===403?403:503,code);
      }
    };
    const response=await createHandler({url,key,proof,fetcher:scopedFetch})(req);
    if (proof && (await response.clone().text()).includes(proof))
      return Response.json({error:'database_temporarily_unavailable'},{status:503});
    return response;
  };
}
