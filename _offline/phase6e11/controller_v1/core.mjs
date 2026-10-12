export const PROJECT='mokxyyullfhkfalopbzd';
export const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const HASH=/^[0-9a-f]{64}$/;
export class Halt extends Error {
  constructor(phase,code){super(code);this.phase=phase;this.code=code;}
}
export const canonical=value=>{
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  if(value===undefined||typeof value==='number'&&!Number.isFinite(value))throw new Halt('validation','metadata_invalid');
  return JSON.stringify(value);
};
export async function sha(value){
  const data=new TextEncoder().encode(canonical(value));
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256',data))].map(x=>x.toString(16).padStart(2,'0')).join('');
}
export function safeFailure(error,phase){
  const code=error instanceof Halt&&/^[a-z][a-z0-9_]{1,63}$/.test(error.code)?error.code:'operation_failed';
  return {phase,code};
}
// Only typed technical metadata, never arbitrary API responses or error messages.
export function metadata(value){
  const keys=new Set(['version','rows','table','key_sha','value_sha','operation','before','after','count','sha256',
    'xid','backend','actor_sha','workspace_sha','request_sha','payload_sha','session_sha','source_sha',
    'status','phase','code','http_status','request_id','started_at','ended_at','query_count','temp_read','temp_written',
    'expected','actual','evidence_sha','contract_sha','protected_equal','pair_complete','present','revoked','expires_at',
    'kind','changes','user_sha','route','app_writes','auth_events','session_count','refresh_count','audit_count']);
  function check(x,key=''){
    if(x===null||typeof x==='boolean')return;
    if(typeof x==='number'&&Number.isSafeInteger(x)&&x>=0)return;
    if(typeof x==='string'){
      if(x.length>128||/[:/@\\\s]/.test(x)&&!/^\d{4}-\d\d-\d\dT[0-9:.+-]+Z?$/.test(x))throw new Halt('evidence','metadata_text_denied');
      if(/eyJ|sbp_|sb_secret_|Bearer|postgres:|password/i.test(x))throw new Halt('evidence','metadata_text_denied');
      if(key.endsWith('_sha')||key==='sha256')if(!HASH.test(x))throw new Halt('evidence','metadata_hash_invalid');
      return;
    }
    if(Array.isArray(x)&&x.length<=128){x.forEach(v=>check(v,key));return;}
    if(x&&typeof x==='object'&&Object.getPrototypeOf(x)===Object.prototype){
      for(const [k,v] of Object.entries(x)){if(!keys.has(k))throw new Halt('evidence','metadata_field_denied');check(v,k);}return;
    }
    throw new Halt('evidence','metadata_invalid');
  }
  check(value);
  if(new TextEncoder().encode(canonical(value)).length>65536)throw new Halt('evidence','metadata_budget');
  return structuredClone(value);
}
export function validateGrant(g,now=Date.now()){
  if(!g||g.project!==PROJECT||!UUID.test(g.id)||!/^[0-9a-f]{40}$/.test(g.sha)||!/^\d+$/.test(g.run)||!HASH.test(g.manifest_sha)
    ||!Number.isSafeInteger(g.starts)||!Number.isSafeInteger(g.expires)||g.starts>now||g.expires<=now||g.expires-g.starts>600000)
    throw new Halt('admission','grant_invalid');
  return g;
}
export class Controller {
  constructor({grant,store,now=Date.now,maxCommands=128}){
    validateGrant(grant,now());
    if(!Number.isSafeInteger(maxCommands)||maxCommands<1||maxCommands>128)throw new Halt('admission','budget_invalid');
    Object.assign(this,{grant:Object.freeze(structuredClone(grant)),store,now,maxCommands,commands:0,step:0,claimed:false,stopped:false,busy:false});
  }
  check(){if(this.stopped||this.now()>=this.grant.expires)throw new Halt('admission','controller_closed');}
  command(){this.check();if(++this.commands>this.maxCommands){this.stopped=true;throw new Halt('budget','command_budget');}}
  async claim(){this.check();if(this.claimed)throw new Halt('admission','run_replayed');await this.store.claim(this.grant);this.claimed=true;}
  async execute(contract,adapter){
    this.check();if(!this.claimed||this.busy)throw new Halt('admission','controller_busy_or_unclaimed');
    if(!UUID.test(contract?.actor)||!UUID.test(contract?.action_id)||!UUID.test(contract?.request_id)||
      contract.workspace!==null&&!UUID.test(contract.workspace)||contract.step!==this.step||!Array.isArray(contract.writes))
      throw new Halt('admission','contract_invalid');
    this.busy=true;let phase='before_saved';
    try {
      const before=metadata(await adapter.measure('before'));
      await this.store.before(this.grant.id,contract,before,await sha(contract));
      this.check();phase='action_started';await this.store.record(this.grant.id,this.step,phase,{contract_sha:await sha(contract)});
      this.check();
      const result=await adapter.act();
      phase='action_confirmed';await this.store.record(this.grant.id,this.step,phase,metadata(result));
      phase='after_saved';const after=metadata(await adapter.measure('after'));
      await this.store.record(this.grant.id,this.step,phase,after);
      phase='pair_validated';const verified=await adapter.validate(before,result,after);
      if(verified?.pair_complete!==true||verified?.protected_equal!==true)throw new Halt(phase,'pair_invalid');
      await this.store.record(this.grant.id,this.step,phase,metadata(verified));
      this.step++;return metadata(verified);
    } catch(error){
      this.stopped=true;
      try {await this.store.halt(this.grant.id,this.step,safeFailure(error,phase));} catch {}
      throw new Halt(phase,safeFailure(error,phase).code);
    } finally {this.busy=false;}
  }
}
export function createEndpoint({grant,verify,execute,now=Date.now}){
  return async req=>{
    const deny=(status,code)=>Response.json({status:'NO_GO',code},{status,headers:{'Cache-Control':'no-store'}});
    if(req.method!=='POST')return deny(405,'method_denied');
    if(req.headers.has('origin'))return deny(403,'browser_denied');
    try{
      validateGrant(grant,now());
      await verify(req.headers.get('authorization'),grant);
      const reader=req.body?.getReader();let n=0;const bytes=[];
      if(reader)for(;;){const v=await reader.read();if(v.done)break;n+=v.value.length;if(n>2){await reader.cancel();return deny(400,'payload_denied');}bytes.push(...v.value);}
      if(new TextDecoder().decode(new Uint8Array(bytes))!=='{}')return deny(400,'payload_denied');
      const result=metadata(await execute());
      return Response.json(result,{headers:{'Cache-Control':'no-store'}});
    }catch(error){return Response.json({status:'NO_GO',...safeFailure(error,'controller')},{status:403,headers:{'Cache-Control':'no-store'}});}
  };
}
