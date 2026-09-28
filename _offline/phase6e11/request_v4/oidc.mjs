// Temporary CI control plane only. This never supplies application actor claims.
export const ISSUER='https://token.actions.githubusercontent.com';
export const AUDIENCE='fmz6e11-mokxyyullfhkfalopbzd-proof';
const bytes=s=>Uint8Array.from(atob(s.replaceAll('-','+').replaceAll('_','/')),c=>c.charCodeAt(0));
const decode=s=>JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes(s)));
export async function verifyCI(header,expected,{fetcher=fetch,now=Date.now}={}) {
  try {
    if(!/^Bearer [A-Za-z0-9_.-]{1,12000}$/.test(header||''))throw Error();
    const parts=header.slice(7).split('.');if(parts.length!==3)throw Error();
    const h=decode(parts[0]),p=decode(parts[1]);
    if(h.alg!=='RS256'||typeof h.kid!=='string'||h.jku||h.x5u)throw Error();
    const t=now()/1000;
    if(p.iss!==ISSUER||p.aud!==AUDIENCE||p.sub!=='repo:Yourizorge@292557331/fitmetzorge-staging@1330119916:ref:refs/heads/main'
      ||p.repository_id!=='1330119916'||p.repository_owner_id!=='292557331'
      ||p.repository!=='Yourizorge/fitmetzorge-staging'||p.ref!=='refs/heads/main'
      ||p.event_name!=='workflow_dispatch'||p.sha!==expected.sha||String(p.run_id)!==expected.run
      ||p.run_attempt!=='1'||p.workflow_ref!=='Yourizorge/fitmetzorge-staging/.github/workflows/phase6e11-proof.yml@refs/heads/main'
      ||!Number.isSafeInteger(p.exp)||!Number.isSafeInteger(p.iat)||!Number.isSafeInteger(p.nbf)
      ||p.exp<=t||p.nbf>t||p.iat>t||p.exp-p.iat>600||t>=expected.expires)throw Error();
    const response=await fetcher(ISSUER+'/.well-known/jwks',{signal:AbortSignal.timeout(5000),redirect:'error'});
    if(!response.ok)throw Error();
    const body=await response.text();if(body.length>100000)throw Error();
    const keys=JSON.parse(body).keys.filter(k=>k.kid===h.kid&&k.kty==='RSA'&&k.use==='sig');
    if(keys.length!==1)throw Error();
    const key=await crypto.subtle.importKey('jwk',keys[0],{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['verify']);
    if(!await crypto.subtle.verify('RSASSA-PKCS1-v1_5',key,bytes(parts[2]),new TextEncoder().encode(parts[0]+'.'+parts[1])))throw Error();
    return {run:p.run_id,sha:p.sha,verified:true};
  } catch {throw Error('ci_authorization_denied');}
}
