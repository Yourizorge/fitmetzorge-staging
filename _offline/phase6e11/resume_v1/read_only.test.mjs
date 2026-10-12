import {test} from 'node:test';
import a from 'node:assert/strict';
import {readOnly,GUARD,IDENTITY,INSTANCE} from './read_only.mjs';
function fixture({failure,guard,identity,rollbackFailure}={}){
  const calls=[];
  const sql={reserve(){throw Error('reserve_forbidden');},async unsafe(q){
    calls.push(q);
    if(failure===q||q==='ROLLBACK'&&rollbackFailure)throw Object.assign(Error('postgres://private:secret@invalid'),{code:'DEADLINE'});
    if(q===GUARD)return guard??[{readonly:true,backend:17}];
    if(q===IDENTITY)return identity??[{bound:true,backend:17,instance:INSTANCE}];
    return [];
  }};
  return {calls,sql};
}
const deadline=f=>f();
test('explicit first BEGIN, no reserve/catalog fetch/commit; one backend; rollback',async()=>{
  const x=fixture(),r=await readOnly(x.sql,deadline);
  a.equal(r.status,'READONLY_PASS');a.deepEqual(x.calls,['BEGIN TRANSACTION READ ONLY',GUARD,IDENTITY,'ROLLBACK']);
  a.equal(r.commands,4);a.equal(r.backend_consistent,true);
});
for(const [name,q]of [['begin','BEGIN TRANSACTION READ ONLY'],['guard',GUARD],['identity',IDENTITY]]){
  test(name+' failure retains phase and attempts rollback without later queries',async()=>{
    const x=fixture({failure:q}),r=await readOnly(x.sql,deadline);
    a.equal(r.status,'NO_GO');a.equal(r.phase,'readonly_'+name);a.equal(r.error,'DEADLINE');
    a.equal(x.calls.at(-1),'ROLLBACK');a.equal(r.rollback,true);
    a(!JSON.stringify(r).includes('secret'));
    if(q!==IDENTITY)a(!x.calls.includes(IDENTITY));
  });
}
for(const [name,guard]of [['off',[{readonly:false,backend:17}]],['missing',[]],['duplicate',[{readonly:true,backend:17},{readonly:true,backend:17}]],['bad pid',[{readonly:true,backend:null}]]]){
 test('reject '+name+' guard',async()=>{const x=fixture({guard}),r=await readOnly(x.sql,deadline);
   a.equal(r.error,'READONLY_UNCONFIRMED');a(!x.calls.includes(IDENTITY));a(r.rollback);});
}
for(const [name,identity,code]of [['wrong instance',[{bound:true,backend:17,instance:'wrong'}],'IDENTITY_MISMATCH'],
 ['wrong role',[{bound:false,backend:17,instance:INSTANCE}],'IDENTITY_MISMATCH'],
 ['reconnected',[{bound:true,backend:18,instance:INSTANCE}],'BACKEND_CHANGED'],
 ['missing',[],'IDENTITY_MISMATCH']]){
 test(name+' blocks identity',async()=>{const r=await readOnly(fixture({identity}).sql,deadline);a.equal(r.error,code);a(r.rollback);});
}
test('rollback failure cannot pass and retains original error',async()=>{
 const r=await readOnly(fixture({failure:IDENTITY,rollbackFailure:true}).sql,deadline);
 a.equal(r.status,'NO_GO');a.equal(r.phase,'readonly_identity');a.equal(r.error,'DEADLINE');a.equal(r.rollbackError,'DEADLINE');
});
test('unknown error redacted, never raw code/URL/message',async()=>{
 const r=await readOnly({unsafe(){throw Object.assign(Error('token secret'),{code:'private-value'});}},deadline);
 a.equal(r.error,'SANITIZED_QUERY_ERROR');a.equal(r.rollbackError,'SANITIZED_QUERY_ERROR');
 a(!JSON.stringify(r).includes('private-value'));
});
test('connect and query deadlines separate and bounded',async()=>{
 const limits=[];await readOnly(fixture().sql,(f,ms)=>{limits.push(ms);return f();});
 a.deepEqual(limits,[5000,2000,2000,2000]);
});
test('local-only guard mode is explicitly not project binding',async()=>{
 const r=await readOnly(fixture().sql,deadline,{verifyInstance:false});
 a.equal(r.commands,3);a.equal(r.instance_checked,false);a.equal(r.bound,false);
});
