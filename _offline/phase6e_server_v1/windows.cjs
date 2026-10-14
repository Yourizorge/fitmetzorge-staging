'use strict';
const {METRICS,POLICY,hash}=require('../phase6e13/engine.cjs');
const DAY=86400000,fail=c=>{throw Error(c);},int=Number.isSafeInteger;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&JSON.stringify(Object.keys(v).sort())===JSON.stringify([...keys].sort());
const basis=s=>hash({pair:s.pair,recovery:s.recovery,records:s.records,health:s.healthLatch,plan:s.active.version});
function compare(s,b){
 if(!exact(b,['synthetic_only','source','subject','goal','planVersion','revision','issued','expires','end','policy','rows','manifest'])||b.synthetic_only!==true||b.source!==basis(s)||b.subject!==s.recovery.subject||b.goal!==s.pair.training.fixture.intake.goal||b.planVersion!==s.active.version||hash(b.policy)!==hash(POLICY)||!int(b.revision)||b.revision<1)fail('comparison_binding');
 if(![b.issued,b.expires,b.end].every(int)||b.issued>s.clock||b.expires<=s.clock||b.expires-b.issued>DAY||b.end%DAY||b.end>s.clock||s.clock-b.end>DAY)fail('comparison_expired');
 if(!Array.isArray(b.rows)||b.rows.length!==24||!Array.isArray(b.manifest)||b.manifest.length!==24)fail('comparison_incomplete');
 const seen=new Set(),slots=new Set(),manifest=new Map(),facts=[];
 for(const m of b.manifest){if(!exact(m,['id','version','sha'])||manifest.has(m.id)||!int(m.version)||m.version<1||!/^[a-f0-9]{64}$/.test(m.sha))fail('comparison_manifest');manifest.set(m.id,m);}
 for(const r of b.rows){
  if(!exact(r,['id','version','metric','day','value','unit','method','coverage','quality','subject','goal','planVersion'])||!/^syn-[a-z0-9-]+$/.test(r.id)||seen.has(r.id)||!int(r.version)||r.version<1||!Object.hasOwn(METRICS,r.metric)||r.subject!==b.subject||r.goal!==b.goal||r.planVersion!==b.planVersion||!int(r.day)||r.day%DAY||r.day<b.end-6*DAY||r.day>=b.end||slots.has(r.metric+':'+r.day))fail('comparison_row');
  const m=METRICS[r.metric],ref=manifest.get(r.id);
  if(!ref||ref.version!==r.version||ref.sha!==hash(r))fail('comparison_manifest');
  if(r.value===null||r.coverage!=='complete'||r.quality!=='confirmed')fail('comparison_incomplete');
  if(!int(r.value)||r.value<m.min||r.value>m.max||r.unit!==m.unit||r.method!==m.method)fail('comparison_incomparable');
  seen.add(r.id);slots.add(r.metric+':'+r.day);
 }
 for(const [metric,m] of Object.entries(METRICS)){
  const rows=b.rows.filter(r=>r.metric===metric).sort((a,b)=>a.day-b.day),divisor=m.aggregation==='sum'?1:3;
  if(rows.length!==6)fail('comparison_incomplete');
  const previous=rows.slice(0,3).reduce((n,r)=>n+r.value,0),current=rows.slice(3).reduce((n,r)=>n+r.value,0);
  facts.push({metric,unit:m.unit,previous:{sum:previous,divisor},current:{sum:current,divisor},delta:{numerator:current-previous,divisor},refs:rows.map(r=>({id:r.id,version:r.version}))});
 }
 return {bundleHash:hash(b),basis:b.source,revision:b.revision,facts,physical_advice_authorized:false,automatic_actions_allowed:false,sourceTruth:'synthetic_source_validation_not_live_authenticity'};
}
function example(s){
 const revision=s.comparison?.revision||(s.comparisonHistory?.at(-1)?.revision||0)+1;
 const end=Math.floor(s.clock/DAY)*DAY,b={synthetic_only:true,source:basis(s),subject:s.recovery.subject,goal:s.pair.training.fixture.intake.goal,planVersion:s.active.version,revision,issued:s.clock,expires:s.clock+DAY,end,policy:structuredClone(POLICY),rows:[],manifest:[]};
 const samples={sleep:[450,450,450,420,420,420],recovery:[8,8,8,6,6,6],nutrition:[2200,2200,2200,2100,2100,2100],training:[6,6,6,4,4,4]};
 for(const [metric,m] of Object.entries(METRICS))for(let d=0;d<6;d++)b.rows.push({id:'syn-window-'+metric+'-'+d,version:1,metric,day:end-(6-d)*DAY,value:samples[metric][d],unit:m.unit,method:m.method,coverage:'complete',quality:'confirmed',subject:b.subject,goal:b.goal,planVersion:b.planVersion});
 b.manifest=b.rows.map(r=>({id:r.id,version:r.version,sha:hash(r)}));return b;
}
module.exports={basis,compare,example};
