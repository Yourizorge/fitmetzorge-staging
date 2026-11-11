export const PHASES=new Set(['configuration_parser','dns_resolution','ip_family_support',
  'tcp_connection','tls_negotiation','tls_certificate_validation','session_pooler_route',
  'postgres_authentication','readonly_begin','readonly_identity','rollback','closed']);
const CODES=new Set(['ECONNREFUSED','ECONNRESET','ETIMEDOUT','ENETUNREACH','EHOSTUNREACH',
  'ENOTFOUND','EAI_AGAIN','EAFNOSUPPORT','CONNECT_TIMEOUT','CONNECTION_CLOSED',
  'CERT_HAS_EXPIRED','DEPTH_ZERO_SELF_SIGNED_CERT','UNABLE_TO_VERIFY_LEAF_SIGNATURE',
  'UNABLE_TO_GET_ISSUER_CERT_LOCALLY','ERR_TLS_CERT_ALTNAME_INVALID','CERT_AUTHORITY_INVALID',
  'DEADLINE','TLS_UNAVAILABLE','DRIVER_RECONNECT_BLOCKED','READONLY_UNCONFIRMED','IDENTITY_MISMATCH']);
export function safeCode(e) {
  if(CODES.has(e?.code))return e.code;
  if(/^[0-9A-Z]{5}$/.test(e?.code||''))return 'SQLSTATE_'+e.code;
  const names=new Set(['PermissionDenied','NotSupported','NetworkUnreachable','ConnectionRefused',
    'ConnectionReset','TimedOut','NotFound','InvalidData','BadResource']);
  return names.has(e?.name)?e.name:'UNCLASSIFIED_TRANSPORT_ERROR';
}
export function deadline(work,ms,cancel) {
  if(ms<1||ms>5000)throw Error('invalid_deadline');
  let timer;
  return Promise.race([Promise.resolve().then(work),new Promise((_,reject)=>{
    timer=setTimeout(()=>{try{cancel();}finally{reject(Object.assign(Error(),{code:'DEADLINE'}));}},ms);
  })]).finally(()=>clearTimeout(timer));
}
export function tracker(mode,clock=Date.now) {
  if(!['direct_ipv6','session_ipv4'].includes(mode))throw Error('mode_boundary');
  const start=clock(),events=[];
  let phase='configuration_parser',attempts=0;
  return {
    step(next){if(!PHASES.has(next))throw Error('phase_boundary');
      phase=next;events.push({phase,ms:Math.max(0,clock()-start)});},
    socket(){if(++attempts!==1)throw Object.assign(Error(),{code:'DRIVER_RECONNECT_BLOCKED'});},
    result(ok,error){return {mode,phase,ok,code:ok?null:safeCode(error),socket_attempts:attempts,events};},
    get phase(){return phase;}
  };
}
