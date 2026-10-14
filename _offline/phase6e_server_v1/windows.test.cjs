'use strict';
const test=require('node:test'),a=require('node:assert/strict'),D=require('./domain.cjs'),W=require('./windows.cjs');
const apply=(s,b)=>D.transition(s,{action:'compare_window',data:{bundle:b}},'member');
test('complete existing 3+3-day policy gives traceable facts, not a physical proposal',()=>{
 const s=D.initial('B'),b=W.example(s),v=apply(s,b);a.equal(v.comparison.facts.length,4);a.equal(v.review,null);
 a.deepEqual(v.comparison.facts.find(x=>x.metric==='training').delta,{numerator:-6,divisor:1});
 a.deepEqual(apply(v,b),v);a.equal(v.active.version,1);a.equal(v.comparisonHistory.length,1);
});
test('missing, partial, duplicate, conflicting and expired windows deny conclusions',()=>{
 for(const change of [b=>b.rows.pop(),b=>b.rows[0].value=null,b=>b.rows[0].coverage='partial',b=>b.rows[0].planVersion++,b=>b.rows[1]=b.rows[0],b=>b.expires=b.issued,b=>b.source='0'.repeat(64)]){
  const s=D.initial('B'),b=W.example(s);change(b);a.throws(()=>apply(s,b),/comparison_/);a.equal(s.revision,0);
 }
});
test('source correction invalidates comparison and approvals without removing history',()=>{
 let s=D.initial('B');s=apply(s,W.example(s));const old=structuredClone(s.comparisonHistory),r=s.recovery.rows.at(-1);
 s=D.transition(s,{action:'recovery',data:{id:r.id,version:r.version,value:6}},'member');
 a.equal(s.comparison,null);a.deepEqual(s.comparisonHistory,old);a.equal(s.review?.member,false);
});
test('health does not become clearance; withdrawn consent stops new comparisons',()=>{
 let s=D.initial('B');s=D.transition(s,{action:'health',data:{value:'current'}},'member');
 s=apply(s,W.example(s));a.equal(s.healthLatch,true);a.equal(s.review,null);a.equal(s.comparison.physical_advice_authorized,false);
 s=D.transition(s,{action:'revoke',data:{}},'member');a.throws(()=>apply(s,W.example(s)),/consent/);
});
