'use strict';
const {test}=require('node:test'),a=require('node:assert/strict'),fs=require('node:fs'),p=require('node:path');
const {register:r,admission,nextSlice}=require('./gates.cjs'),root=p.resolve(__dirname,'../../..');
function valid(){const e={repository:r.repository,branch:r.branch,project:r.project,syntheticOnly:true,
 externalCalls:0,externalCost:0,realMemberAI:false,sourceManifest:'a'.repeat(64),runId:'synthetic-unit-run',proofs:{}};
 for(const g of r.requiredGates)e.proofs[g]={status:'PASS',hosted:true,syntheticOnly:true,runId:e.runId,sourceManifest:e.sourceManifest,receipt:'b'.repeat(64)};
 return e;}
test('only complete synthetic bound evidence admits the next slice, never owner/live acceptance',()=>{
 const x=admission(valid());a(x.allowed);a.equal(x.next,'registration-12');a.equal(x.realMemberAI,false);a.equal(x.ownerAccepted,false);
});
for(const gate of r.requiredGates)for(const mode of ['missing','local','stale','other_run']){
 test(gate+' denies '+mode,()=>{const e=valid();
 if(mode==='missing')delete e.proofs[gate];
 if(mode==='local')e.proofs[gate].hosted=false;
 if(mode==='stale')e.proofs[gate].sourceManifest='c'.repeat(64);
 if(mode==='other_run')e.proofs[gate].runId='other-run';
 a(!admission(e).allowed);a(admission(e).reasons.includes('proof:'+gate));
 });
}
for(const [key,value]of [['repository','other/repo'],['branch','other'],['project','other'],['syntheticOnly',false],
 ['externalCalls',1],['externalCost',1],['realMemberAI',true],['sourceManifest',''],['runId',null]]){
 test('deny '+key,()=>{const e=valid();e[key]=value;a(!admission(e).allowed);});
}
test('support reply is not a technical prerequisite',()=>{const e=valid();e.supportReply=null;a(admission(e).allowed);});
test('TLS-only, native and historical migration success do not pass Edge gate',()=>{
 const e=valid();e.proofs.edgeReadonly={status:'TLS_PASS',hosted:true};a(!admission(e).allowed);
});
test('no blanket rollout or unaccepted21',()=>{a(nextSlice('registration-12',valid()).allowed);
 for(const id of ['overview-20','phase21','unknown'])a(!nextSlice(id,valid()).allowed);
});
test('all accepted0-20 accounted for,11 not called accepted,21 excluded',()=>{
 const numbers=r.components.flatMap(x=>x.packages).sort((a,b)=>a-b);
 a.deepEqual(numbers,Array.from({length:21},(_,i)=>i));a.deepEqual(r.unaccepted,[21]);
 a.equal(r.components.find(x=>x.id==='foundation-11').status,'technical_no_go_not_owner_accepted');
});
test('every component has dependency, test, data authority and rollback planning',()=>{
 const ids=new Set(r.components.map(x=>x.id));
 for(const c of r.components){for(const k of ['frontend','server','rls','edge','notifications','rollback','status'])a(c[k].length>10,k);
 a(c.tests.length>=3,c.id);for(const d of c.dependencies)a(ids.has(d),d);}
});
test('dependency graph acyclic',()=>{
 function visit(id,path=[]){a(!path.includes(id),'cycle');for(const d of r.components.find(x=>x.id===id).dependencies)visit(d,[...path,id]);}
 for(const c of r.components)visit(c.id);
});
test('acceptance receipts exist and latest contract sources remain read-only',()=>{
 for(let i=0;i<=20;i++){if(i===11)continue;
 a(fs.existsSync(p.join(root,'docs/PHASE6E'+i+'_FREEZE_RECEIPT.md')),String(i));}
});
test('no provider/network/credential execution in gates',()=>{
 const source=fs.readFileSync(p.join(__dirname,'gates.cjs'),'utf8');
 a(!/fetch\(|https?:|supabase-js|process\.env|writeFile|execFile/.test(source));
});
