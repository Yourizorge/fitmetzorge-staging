(function(root,factory){const api=factory();if(typeof module==="object")module.exports=api;else root.FMZ13Model=api;})(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const clone=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function create(input){
 const catalog=clone(input),requests=new Map();let state={revision:0,current:null,history:[],cards:[],audit:[],revoked:false,expired:false};
 const view=()=>clone(state),deny=reason=>({ok:false,reason,state:view()});
 function command(e,{failBeforeCommit=false}={}){
  if(!e||Object.keys(e).sort().join(",")!==["id","actor","type","source","expected_revision","source_hash"].sort().join(",")||
   typeof e.id!=="string"||!/^syn-command-[0-9]+$/.test(e.id)||e.actor!=="syn-owner")return deny("invalid_actor_or_envelope");
  if(requests.has(e.id)){const old=requests.get(e.id);return same(old.event,e)?{...clone(old.result),replayed:true}:deny("request_conflict");}
  if(e.expected_revision!==state.revision)return deny("stale_request");
  if(state.audit.length>=60)return deny("memory_capacity");
  const next=clone(state),active=catalog.versions.find(v=>v.key===state.current);
  if(e.type==="source_arrival"){
   if(state.revoked||state.expired)return deny("access_withdrawn");
   const v=catalog.versions.find(v=>v.key===e.source);
   if(!v||e.source_hash!==v.source_hash)return deny("payload_or_source_hash");
   if(active&&v.source_hash===active.source_hash){
    const result={ok:true,reason:"source_already_seen",state:view()};
    requests.set(e.id,{event:clone(e),result:clone(result)});return result;
   }
   if(v.revision!==state.history.length+1||v.previous_hash!==(active?.source_hash||null))return deny("source_lineage");
   for(const c of next.cards)if(c.state!=="superseded")c.state="superseded";
   next.current=v.key;next.history.push({key:v.key,revision:v.revision,source_hash:v.source_hash,previous_hash:v.previous_hash,restore_of:v.restore_of});
   if(v.result.status==="candidate_only")next.cards.push({key:v.key,source_hash:v.source_hash,state:"pending"});
  }else{
   if(!active||e.source!==active.key||e.source_hash!==active.source_hash)return deny("source_mismatch");
   if(["review","dismiss"].includes(e.type)){
    if(state.revoked||state.expired)return deny("access_withdrawn");
    const card=next.cards.find(c=>c.key===active.key);
    if(!card||card.state!=="pending")return deny("not_pending");
    card.state=e.type==="review"?"reviewed":"dismissed";
   }else if(e.type==="expire"||e.type==="revoke"){
    next[e.type==="expire"?"expired":"revoked"]=true;
    for(const c of next.cards)c.state="withdrawn";
   }else return deny("action_not_allowed");
  }
  next.revision++;next.audit.push({sequence:next.revision,event_id:e.id,type:e.type,source:e.source,source_hash:e.source_hash,
   synthetic_timestamp_ms:catalog.clock_ms+next.revision,actor:"syn-owner",plan_changed:false,physical_action:false});
  if(failBeforeCommit)return deny("simulated_before_commit_failure");
  state=next;const result={ok:true,reason:"committed_in_memory",state:view()};
  requests.set(e.id,{event:clone(e),result:clone(result)});return result;
 }
 const event=(type,source=state.current,id="syn-command-"+(state.revision+1))=>{
  const v=catalog.versions.find(v=>v.key===source);return {id,actor:"syn-owner",type,source,expected_revision:state.revision,source_hash:v?.source_hash||""};
 };
 return {view,event,command};
}
return {create};
});
