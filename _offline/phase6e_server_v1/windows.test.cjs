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
 s=apply(s,W.example(s));a.equal(s.comparison.revision,2);a.deepEqual(s.comparisonHistory[0],old[0]);
 a.deepEqual(apply(s,W.example(s)),s);
});
test('health does not become clearance; withdrawn consent stops new comparisons',()=>{
 let s=D.initial('B');s=D.transition(s,{action:'health',data:{value:'current'}},'member');
 s=apply(s,W.example(s));a.equal(s.healthLatch,true);a.equal(s.review,null);a.equal(s.comparison.physical_advice_authorized,false);
 s=D.transition(s,{action:'revoke',data:{}},'member');a.throws(()=>apply(s,W.example(s)),/consent/);
});

const command=(s,action,data={})=>D.transition(s,{action,data},'member');
for(const action of ['intake','edit','revoke'])test(action+' removes current comparison facts while retaining their history',()=>{
 const initial=D.initial('B'),compared=apply(initial,W.example(initial));
 const history=structuredClone(compared.comparisonHistory),active=structuredClone(compared.active);
 const data=action==='intake'?{training:structuredClone(compared.pair.training.fixture.intake),
  nutrition:structuredClone(compared.pair.nutrition.fixture.intake)}:
  action==='edit'?{domain:'nutrition_portion',value:{meal:0,item:0,grams:225}}:{};
 const next=command(compared,action,data);
 a.equal(next.comparison,null);a.deepEqual(D.view(next).facts,[]);
 a.deepEqual(next.comparisonHistory,history);a.deepEqual(next.active,active);
 a.ok(next.notices.every(n=>n.status!=='current'));
 a.equal(compared.facts.length,4);a.deepEqual(compared.comparisonHistory,history);
 if(action==='revoke')a.throws(()=>apply(next,W.example(next)),/consent/);
 else{
  const fresh=apply(next,W.example(next));
  a.equal(fresh.facts.length,4);a.equal(fresh.comparisonHistory.length,2);
  a.deepEqual(fresh.comparisonHistory[0],history[0]);
 }
});

test('B comparison, confirmation, edit and separate application never reuse old facts or approval',()=>{
 let s=D.initial('B');s=apply(s,W.example(s));const history=structuredClone(s.comparisonHistory);
 s=command(command(s,'build'),'confirm');a.equal(s.review.member,true);
 s=command(s,'edit',{domain:'nutrition_portion',value:{meal:0,item:0,grams:225}});
 a.deepEqual(s.facts,[]);a.equal(s.review.member,false);a.equal(s.review.trainer,false);
 a.throws(()=>command(s,'apply'),/approvals/);a.equal(s.active.version,1);
 s=command(command(s,'confirm'),'apply');
 a.equal(s.active.version,2);a.equal(s.active.nutrition.meals[0].items[0].grams,225);
 a.deepEqual(s.facts,[]);a.deepEqual(s.comparisonHistory,history);
 a.equal(s.history[0].nutrition.meals[0].items[0].grams,200);
 a.equal(s.history.at(-1).approvals.trainer,null);
});

test('presentation preferences and rejected edits retain valid current facts',()=>{
 let s=D.initial('B');s=apply(s,W.example(s));const before=structuredClone(s);
 const next=command(s,'preferences',{language:'de',theme:'dark',units:'imperial'});
 a.deepEqual(next.comparison,s.comparison);a.deepEqual(next.facts,s.facts);
 a.throws(()=>command(s,'edit',{domain:'nutrition_portion',value:{meal:0,item:0,grams:9999}}));
 a.deepEqual(s,before);
});

for(const route of ['A','B'])test(route+' applying a rebuilt plan expires its prior comparison and allows a fresh one',()=>{
 let s=D.initial(route);
 if(route==='A'){
  const row=s.recovery.rows.at(-1);
  s=command(s,'recovery',{id:row.id,version:row.version,value:6});
 }
 const bundle=W.example(s);s=apply(s,bundle);
 const history=structuredClone(s.comparisonHistory),originalPlan=structuredClone(s.active);
 const notice=D.hash({window:s.comparison.bundleHash});
 s=command(s,'build');const pending=structuredClone(s);
 a.throws(()=>command(s,'apply'),/approvals/);a.deepEqual(s,pending);
 a.deepEqual(s.comparisonHistory,history);a.deepEqual(s.active,originalPlan);
 s=command(s,'confirm');
 if(route==='A'){
  a.throws(()=>command(s,'apply'),/approvals/);
  s=D.transition(s,{action:'approve',data:{}},'trainer');
 }
 const confirmed=structuredClone(s);s=command(s,'apply');
 a.equal(s.active.version,originalPlan.version+1);
 a.equal(s.comparison,null);a.deepEqual(D.view(s).facts,[]);
 a.deepEqual(s.comparisonHistory,history);a.deepEqual(confirmed.comparisonHistory,history);
 a.equal(s.notices.find(n=>n.id===notice).status,'superseded');
 a.deepEqual(s.history.at(-1).approvals,{member:true,trainer:route==='A'?true:null});
 a.throws(()=>apply(s,bundle),/comparison_binding/);
 const fresh=apply(s,W.example(s));
 a.equal(fresh.comparison.revision,history.at(-1).revision+1);
 a.equal(fresh.comparison.basis,W.basis(fresh));a.equal(fresh.facts.length,4);
 a.deepEqual(fresh.comparisonHistory.slice(0,-1),history);
 a.deepEqual(apply(fresh,W.example(fresh)),fresh);
});
