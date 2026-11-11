// Pure source-factory probes. The inspected modules have no filesystem/network APIs.
import vm from 'node:vm';
import {createHash,webcrypto} from 'node:crypto';
import {posix} from 'node:path';
import {TextEncoder,TextDecoder} from 'node:util';

const chunks=[];
let size=0;
for await(const part of process.stdin){size+=part.length;if(size>2000000)throw Error('template_input_bound');chunks.push(part);}
const input=JSON.parse(Buffer.concat(chunks));
if(input.format!=='quota-native-source-probe-v1')throw Error('template_input_format');
const prefix='_offline/phase6e11/';
const hash=value=>createHash('sha256').update(value).digest('hex');
const timers=new Set();
const context=vm.createContext({TextEncoder,TextDecoder,URL,crypto:webcrypto,
 setTimeout:(fn,ms)=>{const timer=setTimeout(fn,ms);timers.add(timer);return timer;},
 clearTimeout:timer=>{clearTimeout(timer);timers.delete(timer);},performance:{now:()=>0}});
const parseInContext=vm.runInContext('JSON.parse',context);
const intoContext=value=>parseInContext(JSON.stringify(value));
context.structuredClone=intoContext;
const modules=new Map(),used={},profiles=[];
const builtins={
 'node:crypto':{createHash},
 'node:path':{resolve:(...p)=>posix.resolve(...p),relative:posix.relative,
  isAbsolute:posix.isAbsolute,dirname:posix.dirname},
 'node:url':{fileURLToPath:value=>new URL(value).pathname},
 'node:fs':{
  readFileSync:()=>{throw Error('template_filesystem_denied');},
  realpathSync:()=>{throw Error('template_filesystem_denied');},
  lstatSync:()=>{throw Error('template_filesystem_denied');}}
};
function moduleFor(name){
 if(modules.has(name))return modules.get(name);
 let module;
 if(name in builtins){
  const values=builtins[name];
  module=new vm.SyntheticModule(Object.keys(values),function(){
   for(const [key,value] of Object.entries(values))this.setExport(key,value);
  },{context,identifier:name});
 }else{
  if(!name.startsWith(prefix)||name.includes('..')||!name.endsWith('.mjs'))throw Error('template_module_scope');
  const value=input.sources[name];
  if(!value||typeof value.source!=='string'||hash(value.source)!==value.sha256)throw Error('template_source_binding');
  used[name]=value.sha256;
  module=new vm.SourceTextModule(value.source,{context,identifier:name,
   initializeImportMeta:meta=>{meta.url='file:///'+name;},
   importModuleDynamically:()=>{throw Error('template_dynamic_import_denied');}});
 }
 modules.set(name,module);return module;
}
async function load(name){
 const module=moduleFor(name);
 if(module.status==='unlinked')await module.link((specifier,parent)=>{
  if(specifier.startsWith('node:'))return moduleFor(specifier);
  if(!specifier.startsWith('.'))throw Error('template_external_import_denied');
  return moduleFor(posix.normalize(posix.join(posix.dirname(parent.identifier),specifier)));
 });
 if(module.status==='linked')await module.evaluate({timeout:1000});
 return module.namespace;
}
const id=n=>'00000000-0000-4000-8000-'+String(n).padStart(12,'0');
function profile(name,source,symbol,conditions){
 const value={name,source,symbol,conditions,sites:[],execution_observed:false};
 profiles.push(value);return value;
}
try{
 const {BoundNativeStore,closeStatement}=await load(prefix+'endchain_v1/quota_candidate_v1/runtime_node.mjs');
 const {Store}=await load(prefix+'controller_v1/store.mjs');
 const quota={binding:{cap:2349}};
 let active;
 const store=new BoundNativeStore(async(sql,args)=>{
  active.sites.push({sql,args_count:args.length,channel:'outer',phase:active.name});
  return [{id:id(1),phase:'pair_validated',state:'closed'}];
 },quota);
 const source=prefix+'controller_v1/store.mjs';
 active=profile('claim',source,'Store.claim',{
  delegation:'BoundNativeStore.claim -> Store.claim',admission_not_exercised:true});
 await Store.prototype.claim.call(store,{id:id(1),run:'1',sha:'a'.repeat(40),manifest_sha:'b'.repeat(64),expires:1});
 active=profile('before_saved',source,'Store.before',{controller_pair_phase:'before_saved'});
 await store.before(id(1),{step:0,action_id:id(2),request_id:id(3),actor:id(4),workspace:null,
  kind:'auth',operation:'verify'},intoContext({count:0}),'a'.repeat(64));
 for(const phase of ['action_started','action_confirmed','after_saved','pair_validated']){
  active=profile(phase,source,'Store.record',{controller_pair_phase:phase});
  await store.record(id(1),0,phase,intoContext({pair_complete:true,protected_equal:true}));
 }
 active=profile('durable_stop',source,'Store.halt',{
  queryio:'outer direct; workflow transport may bind before dispatch',controller_catch:true});
 await store.halt(id(1),0,intoContext({phase:'call',code:'source_probe'}));
 for(const complete of [false,true]){
  active=profile('close_'+complete,prefix+'endchain_v1/quota_candidate_v1/runtime_node.mjs',
   'BoundNativeStore.close',{complete,admission_not_exercised:true});
  const command=closeStatement(id(1),complete,1);
  await store.one(command.sql,command.args);
 }
 const {createProtocolSessionTransport}=await load(prefix+'endchain_v1/session_transport.mjs');
 for(const operation of ['invoke','read'])for(const warmed of [false,true]){
  const rows=[];
  const sql={unsafe:async(text,args=[])=>{
   rows.push({sql:text,args_count:args.length,channel:'workflow',phase:rows.phase});
   return [{identity:true,safe:true,locks_allowed:true,value:{source_probe:true}}];
  },end:async()=>{}};
  const transport=createProtocolSessionTransport({sql,now:()=>0,
   onCommand:phase=>{rows.phase=phase;}});
  const request={input:operation==='read'?{op:'read',window:id(5),workspace:id(6)}:{op:'command'},
   claims:{sub:id(4)},proof:'source-probe-not-a-credential',requestId:id(3)};
  try{
   if(warmed){await transport[operation](request);rows.length=0;}
   await transport[operation](request);
   const probe=profile(operation+(warmed?'_warm':'_cold'),prefix+'endchain_v1/session_transport.mjs',
    'createProtocolSessionTransport.'+operation,{identity_attested_before:warmed,
     replies:'in_memory_shape_only',no_failure:true});
   probe.sites.push(...rows);
  }finally{await transport.close();}
 }
 process.stdout.write(JSON.stringify({format:'quota-native-source-probe-v1',source_hashes:used,
  profiles,sql_executed:0,network_calls:0,full_chain_admission:false}));
}finally{
 for(const timer of timers)clearTimeout(timer);
 timers.clear();
}
