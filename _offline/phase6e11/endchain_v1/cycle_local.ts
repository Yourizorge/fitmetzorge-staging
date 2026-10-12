import postgres from 'https://deno.land/x/postgresjs@v3.4.7/mod.js';
import {ScopedCycle} from './scoped_cycle.mjs';
const [caPath,portText]=Deno.args,port=Number(portText);
if(!Number.isInteger(port)||port<56110||port>=56140)throw Error('local_only');
const ca=await Deno.readTextFile(caPath);
const options={host:'127.0.0.1',port,database:'postgres',username:'postgres',password:'',
 ssl:{caCerts:[ca],hostname:'127.0.0.1'},max:1,max_pipeline:1,fetch_types:false,prepare:false,
 connect_timeout:5,idle_timeout:0,max_lifetime:0,debug:false,
 connection:{application_name:'fmz6e11-endchain-local-cycle',statement_timeout:2000,lock_timeout:1000},
 onnotice:()=>{}};
const read=postgres(options),write=postgres(options);
let commands=0,cycle:ScopedCycle|undefined;
const query=(q:string,args:any[]=[])=>{commands++;return read.unsafe(q,args);};
try{
 const instance=await write.unsafe("select encode(sha256(system_identifier::text::bytea),'hex') instance from pg_control_system()");
 await write.unsafe('create table public.fmz_local_cycle(id integer primary key,n integer)');
 cycle=new ScopedCycle({query,close:()=>read.end({timeout:2}),instance:instance[0].instance,
  queries:{row:"select jsonb_build_object('count',count(*),'version',coalesce(max(n),0)) from public.fmz_local_cycle"}});
 await cycle.begin();
 const snapshots=[await cycle.read('row')];
 await write.unsafe('insert into public.fmz_local_cycle values(1,1)');snapshots.push(await cycle.read('row'));
 await write.unsafe('update public.fmz_local_cycle set n=2 where id=1');snapshots.push(await cycle.read('row'));
 await write.unsafe('delete from public.fmz_local_cycle where id=1');snapshots.push(await cycle.read('row'));
 const expected=[{count:0,version:0},{count:1,version:1},{count:1,version:2},{count:0,version:0}];
 if(JSON.stringify(snapshots)!==JSON.stringify(expected))throw Error('stale_snapshot');
 let denied=false;
 try{await read.unsafe('insert into public.fmz_local_cycle values(2,2)');}
 catch(e){denied=(e as {code?:string}).code==='25006';}
 if(!denied)throw Error('readonly_write_not_denied');
 await cycle.end();
 console.log(JSON.stringify({status:'LOCAL_NATIVE_FRESH_CYCLE_PASS',snapshots,commands,
  same_backend:true,explicit_readonly:true,forbidden_write_denied:denied,hosted_calls:0}));
}catch(e){
 console.log(JSON.stringify({status:'NO_GO',code:(e as {code?:string}).code||'local_cycle_failed'}));
 Deno.exitCode=2;
}finally{
 try{if(cycle)await cycle.end();else await read.end({timeout:2});}
 finally{await write.end({timeout:2});}
}
