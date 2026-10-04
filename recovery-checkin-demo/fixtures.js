(function(r){"use strict";const D=typeof module==='object'?require('./data.js'):r.FMZ19Data,copy=x=>JSON.parse(JSON.stringify(x));
function base(route='B'){
 const plan=copy(D.plans[route]),rows=copy(D.rows).map(x=>({...x,plan:plan.id,planVersion:plan.version}));rows.at(-1).value=null;
 return {synthetic_only:true,route,subject:'syn19-member',clock:D.clock,plan,rows,reportedRecovery:'low',consent:true,health:'none',
 rule:{id:'syn19-'+route+'-checkin',version:1,origin:D.options[1].source,option:'daily',optionVersion:1,allowedRestore:['after_workout','daily'],plan:plan.id,planVersion:plan.version,status:'active',at:D.clock-1000,expires:D.clock+D.DAY,trainer:route==='A'?{id:'syn19-trainer',relationshipVersion:1,status:'active'}:null},
 sources:{version:1,issued:D.clock,expires:D.clock+D.DAY},agenda:{version:1,plan:plan.id,planVersion:plan.version,nextTraining:{id:'syn19-next-training',date:'2026-10-05',day:'mon',at:'18:00',origin:'explicit synthetic member appointment'},checkin:{id:'syn19-checkin-1',date:'2026-09-30',at:'19:00',origin:'explicit synthetic after-workout occurrence'},allowedTimes:['08:00','20:00']},
 cadence:{version:1,option:'after_workout',at:'19:00'}};}
const cases={};for(const id of ['arrival','trainer','duplicate','correction','unchanged','missing','incomparable','rule','no_trainer','health','consent','expired','complete','edit','atomic','restore'])cases[id]=base(['trainer','no_trainer'].includes(id)?'A':'B');
cases.missing.rows[0].value=null;cases.incomparable.rows[0].unit='hours';cases.rule.rule=null;cases.no_trainer.rule.trainer=null;cases.health.health='current';cases.expired.sources.expires=D.clock;
for(const x of cases.unchanged.rows)x.value=x.metric==='sleep'?450:8;
const api={base,cases,copy};if(typeof module==='object')module.exports=api;else r.FMZ19Fixtures=api;})(globalThis);
