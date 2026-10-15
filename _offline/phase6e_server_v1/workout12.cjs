'use strict';
const R=require('./registration12.cjs'),F=require('../phase6e12/core.cjs');
function session(s){return s.session12||{status:'ready',closures:[]};}
function transition(s,request){
 if(!s.consent)throw Error('consent');
 if(!request||Object.keys(request).sort().join(',')!=='action,data')throw Error('payload');
 const phase=session(s),next=structuredClone(s);
 if(request.action==='register12'){
  if(phase.status!=='started')throw Error('workout_not_started');
  const saved=R.transition(s,request);saved.session12={...structuredClone(phase),status:'started'};return saved;
 }
 if(request.action==='revoke')return R.transition(s,request);
 if(!request.data||Object.keys(request.data).length)throw Error('payload');
 const v=R.view(s);
 if(request.action==='start12'){
  if(phase.status==='started')throw Error('workout_already_started');
  next.session12={...structuredClone(phase),status:'started'};
 }else if(request.action==='finish12'){
  if(phase.status!=='started')throw Error('workout_not_started');
  const last=v.registrations.at(-1);
  if(!last||!last.sets.some(x=>x.completed))throw Error('missing');
  const hash=F.hash(last);
  if(phase.closures.some(c=>c.registration_hash===hash))throw Error('workout_already_finished');
  next.session12={status:'finished',closures:[...structuredClone(phase.closures),{
   source:s.source,snapshot_hash:F.hash(s.original),registration_hash:hash,registration_revision:last.revision,
   completed:last.sets.filter(x=>x.completed).length,total:last.sets.length,physical_advice_authorized:false}]};
 }else throw Error('registration_action');
 if(s.revision>=250)throw Error('synthetic_capacity');
 next.revision++;next.events.push({revision:next.revision,action:request.action,source:s.source});return next;
}
function view(s){return {...R.view(s),session12:structuredClone(session(s))};}
module.exports={transition,view};
