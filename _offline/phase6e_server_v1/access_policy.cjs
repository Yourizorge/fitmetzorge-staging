'use strict';
// Read-only policy preparation. No grants, trial creation, payments or real AI.
const DAY=86400000,rank={free:0,pro:1,ai:2};
function view(source,now){
 if(!source||source.synthetic_only!==true||source.verified!==true||!source.id||!Number.isSafeInteger(source.version)||source.version<1||!Number.isSafeInteger(now)||!Array.isArray(source.grants))throw Error('entitlement_source');
 let tier='free';const active=[];
 for(const grant of source.grants){
  if(!grant.id||!(grant.tier in rank)||!Number.isSafeInteger(grant.start)||!Number.isSafeInteger(grant.end)||grant.end<=grant.start||typeof grant.revoked!=='boolean')throw Error('entitlement_grant');
  if(grant.kind==='trial'&&(grant.tier!=='ai'||grant.end-grant.start!==30*DAY))throw Error('trial_policy');
  if(!grant.revoked&&grant.start<=now&&now<grant.end){active.push(grant.id);if(rank[grant.tier]>rank[tier])tier=grant.tier;}
 }
 if(new Set(source.grants.map(g=>g.id)).size!==source.grants.length||source.grants.filter(g=>g.kind==='trial').length>1)throw Error('entitlement_conflict');
 const notices=[];
 for(const grant of source.grants.filter(g=>g.kind==='trial'&&!g.revoked)){
  const offsets=[['seven_days',7*DAY],['one_day',DAY],['expired',0]];
  for(const [kind,offset] of offsets)if(now>=grant.end-offset)notices.push({key:grant.id+':'+kind,kind,at:grant.end-offset,source_version:source.version});
 }
 return {tier,active,notices,source_version:source.version,retained_history:true,automatic_renewal:false,
  final_day_delivery_rule:'unresolved_timezone_and_delivery_rule',
  trial_creation_allowed:false,external_ai_enabled:false,payment_action_allowed:false};
}
module.exports={view,DAY};
