import assert from 'node:assert/strict';
import {execFileSync,spawnSync} from 'node:child_process';
import {Store} from './store.mjs';
import {sha,Controller,Halt,PROJECT} from './core.mjs';
if(!/^561[123]\d$/.test(process.env.FMZ_LOCAL_PORT||''))throw Error('local_port_required');
const args=['-X','-q','-h','127.0.0.1','-p',process.env.FMZ_LOCAL_PORT,'-U','postgres','-d','postgres','-v','ON_ERROR_STOP=1','-At'];
const quote=x=>x===null?'null':typeof x==='number'?String(x):"'"+String(x).replaceAll("'","''")+"'";
const raw=sql=>execFileSync(process.env.FMZ_LOCAL_PSQL,args,{input:sql,encoding:'utf8',windowsHide:true});
const query=async(sql,params=[])=>{
  // Disposable local fixtures only. PREPARE/EXECUTE preserves driver SQL typing.
  const script='prepare test_statement as '+sql+';execute test_statement('+params.map(quote).join(',')+');';
  const result=raw(script).trim();return result?[{value:result}]:[];
};
const store=new Store(query),id=n=>'65100000-0000-4000-8000-'+String(n).padStart(12,'0');
const now=Date.now(),g={id:id(1),run:'10001',sha:'a'.repeat(40),manifest_sha:'b'.repeat(64),expires:now+300000};
const c={step:0,actor:id(2),action_id:id(3),request_id:id(4),workspace:null,kind:'auth',operation:'verify',writes:[]};
const checks=[];
async function good(name,fn){await fn();checks.push(name);}
async function denied(name,fn){await assert.rejects(fn);checks.push(name);}
await good('empty by default',async()=>assert.equal(raw('select count(*) from fmz6e11_controller_private.runs;').trim(),'0'));
await good('one shot claim',()=>store.claim(g));
await denied('empty run cannot claim complete',()=>store.close(g.id,true,1));
await denied('same run rejected after process restart',()=>new Store(query).claim(g));
await denied('different concurrent run rejected',()=>store.claim({...g,id:id(9),run:'10002'}));
await denied('skipped step rejected',()=>store.before(g.id,{...c,step:1},{count:0},'b'.repeat(64)));
await good('committed before',()=>store.before(g.id,c,{count:0},'b'.repeat(64)));
await denied('pending pair cannot claim complete',()=>store.close(g.id,true,5));
await denied('pair before action rejected',()=>store.record(g.id,0,'pair_validated',{pair_complete:true}));
for(const p of ['action_started','action_confirmed','after_saved','pair_validated'])
 await good('phase '+p,()=>store.record(g.id,0,p,{count:0}));
await denied('duplicate seal rejected',()=>store.record(g.id,0,'pair_validated',{count:0}));
await good('independent connection sees durable pair',async()=>{
 assert.equal(raw('select next_step from fmz6e11_controller_private.runs;').trim(),'1');
 assert.equal(raw('select count(*) from fmz6e11_controller_private.evidence;').trim(),'5');
});
await good('new step after pair',()=>store.before(g.id,{...c,step:1,action_id:id(5),request_id:id(6)},{count:0},'c'.repeat(64)));
await good('expiry fixture only',async()=>raw("update fmz6e11_controller_private.runs set created_at=now()-interval '2 minutes',expires_at=now()-interval '1 minute';"));
await denied('expiry blocks action start',()=>store.record(g.id,1,'action_started',{count:0}));
await good('halt survives expiry',()=>store.halt(g.id,1,{phase:'action_started',code:'expired'}));
await denied('stopped run cannot claim complete',()=>store.close(g.id,true,20));
await denied('command limit cannot be hidden on close',()=>store.close(g.id,false,129));
await denied('stopped run cannot continue',()=>store.before(g.id,{...c,step:1},{count:0},'c'.repeat(64)));
await good('close without wiping proof',()=>store.close(g.id,false,20));
await good('evidence retained after close',async()=>assert.equal(raw('select count(*) from fmz6e11_controller_private.evidence;').trim(),'7'));
const forensicGrant={...g,id:id(20),run:'10003',project:PROJECT,starts:Date.now(),expires:Date.now()+300000};
const controller=new Controller({grant:forensicGrant,store});
const forensicContract={...c,action_id:id(21),request_id:id(22)};
raw('create table public.synthetic_lost_response(id integer primary key);');
await good('forensic run claimed',()=>controller.claim());
await good('unconfirmed mutation remains stopped with durable after-state',async()=>{
 await assert.rejects(controller.execute(forensicContract,{
  measure:async()=>({count:Number(raw('select count(*) from public.synthetic_lost_response;').trim())}),
  act:async()=>{raw('insert into public.synthetic_lost_response values(1);');throw new Halt('transport','connection_deadline');},
  validate:async()=>assert.fail('unknown action cannot validate')
 }),/connection_deadline/);
 const evidence=JSON.parse(raw(`select metadata from fmz6e11_controller_private.evidence where run_id='${forensicGrant.id}' and phase='stopped';`));
 assert.equal(evidence.before.count,0);assert.equal(evidence.after.count,1);assert.equal(evidence.pair_complete,false);
 assert.equal(evidence.actual.phase,'transport');assert.equal(evidence.actual.code,'connection_deadline');
 assert.equal(raw(`select next_step from fmz6e11_controller_private.runs where id='${forensicGrant.id}';`).trim(),'0');
});
await denied('forensic stop does not permit cleanup or another step',()=>controller.execute({...forensicContract,step:1},{}));
await denied('forensic evidence cannot be marked complete',()=>store.close(forensicGrant.id,true,30));
await good('forensic close preserves unknown-outcome proof',()=>store.close(forensicGrant.id,false,30));
for(const role of ['anon','authenticated','service_role'])for(const table of ['runs','steps','evidence'])for(const operation of ['select','insert','update','delete']){
 const cmd={select:'select * from '+table,insert:'insert into '+table+' default values',update:'update '+table+' set '+(table==='runs'?'next_step=next_step':table==='steps'?'step=step':'phase=phase'),delete:'delete from '+table}[operation];
 const p=spawnSync(process.env.FMZ_LOCAL_PSQL,args,{input:`begin;set local role ${role};set search_path=fmz6e11_controller_private;${cmd};rollback;`,encoding:'utf8',windowsHide:true});
 assert.notEqual(p.status,0);assert.ok(/permission denied|does not exist/.test(p.stderr));checks.push(role+' '+operation+' '+table);
}
assert.equal(raw("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='fmz6e11_controller_private';").trim(),'0');checks.push('no added RPC or definer');
assert.equal(raw("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='fmz6e11_controller_private' and c.relkind='r' and c.relrowsecurity;").trim(),'3');checks.push('three tables RLS enabled');
console.log(JSON.stringify({status:'LOCAL_PG17_STORE_PASS',checks:checks.length,names:checks,store_sha:await sha(checks)}));
