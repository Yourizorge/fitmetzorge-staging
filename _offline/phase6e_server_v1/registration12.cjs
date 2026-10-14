'use strict';
const F=require('../phase6e12/core.cjs');
const exact=(o,k)=>o&&JSON.stringify(Object.keys(o).sort())===JSON.stringify([...k].sort());
function initial(name='normal'){
 const fixture=F.fixture(name),c=F.create(fixture);
 return {slice:'registration12',synthetic_only:true,revision:0,consent:true,
  fixture,source:F.sourceHash(fixture),original:c.view().snapshot,records:[],events:[]};
}
function replay(s){
 if(s.slice!=='registration12'||s.synthetic_only!==true||F.sourceHash(s.fixture)!==s.source)throw Error('registration_source');
 const c=F.create(s.fixture);
 if(F.hash(c.view().snapshot)!==F.hash(s.original))throw Error('original_snapshot');
 for(const r of s.records){const v=c.register(r.input);if(!v.ok||F.hash(v.registration)!==r.hash)throw Error('registration_history');}
 return c;
}
function transition(s,request){
 if(!s.consent)throw Error('consent');
 if(!exact(request,['action','data'])||!['register12','revoke'].includes(request.action))throw Error('registration_action');
 const c=replay(s),next=structuredClone(s);
 if(request.action==='revoke'){
  if(!exact(request.data,[]))throw Error('payload');next.consent=false;
 }else{
  if(!exact(request.data,['input']))throw Error('payload');
  const result=c.register(request.data.input);
  if(!result.ok)throw Error(result.reason);
  next.records.push({input:structuredClone(request.data.input),hash:F.hash(result.registration)});
 }
 if(s.revision>=250)throw Error('synthetic_capacity');
 next.revision++;next.events.push({revision:next.revision,action:request.action,source:s.source});return next;
}
function view(s){const c=replay(s),v=c.view();return {slice:s.slice,revision:s.revision,consent:s.consent,
 source:s.source,snapshot:v.snapshot,registrations:v.records,draft:c.draft(),
 reflection:{kind:'historical_planned_vs_recorded_facts_only',snapshot:v.snapshot,
  registered:v.records.at(-1)||null,physical_advice_authorized:false},
 automatic_actions_allowed:false,full_day21:false};}
module.exports={initial,transition,view};
