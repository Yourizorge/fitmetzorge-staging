'use strict';
// Offline admission checks only. No network, credentials, SQL or mutation API.
const register=require('./register.json');
const SCOPE={repository:register.repository,branch:register.branch,project:register.project};
function admission(e){
 const reasons=[];
 for(const [key,value]of Object.entries(SCOPE))if(e?.[key]!==value)reasons.push('scope:'+key);
 if(e?.syntheticOnly!==true)reasons.push('synthetic_only');
 if(e?.externalCalls!==0||e?.externalCost!==0)reasons.push('cost_boundary');
 if(e?.realMemberAI!==false)reasons.push('real_member_ai');
 if(!/^[a-f0-9]{64}$/.test(e?.sourceManifest||''))reasons.push('source_manifest');
 if(!/^[a-z0-9-]{8,100}$/.test(e?.runId||''))reasons.push('run_binding');
 for(const gate of register.requiredGates){
   const p=e?.proofs?.[gate];
   if(!p||p.status!=='PASS'||p.hosted!==true||p.syntheticOnly!==true||p.runId!==e.runId||
      p.sourceManifest!==e.sourceManifest||!(/^[a-f0-9]{64}$/.test(p.receipt||'')))reasons.push('proof:'+gate);
 }
 return {allowed:reasons.length===0,reasons,next:reasons.length?null:register.next,
   automaticActionsAllowed:false,realMemberAI:false,ownerAccepted:false};
}
function nextSlice(id,e){
 const base=admission(e),component=register.components.find(x=>x.id===id);
 if(!component||id!==register.next)return {...base,allowed:false,next:null,reasons:[...base.reasons,'unreleased_slice']};
 return base;
}
module.exports={register,admission,nextSlice};
