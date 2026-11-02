// Private IPC: existing controller/store and B computation, never network/Auth.
import readline from 'node:readline';
import {Controller, Halt, sha} from '../controller_v1/core.mjs';
import {NativeStore} from './native_store.mjs';
import {next, validate, C} from '../edge/core.mjs';

const lines = readline.createInterface({input:process.stdin, terminal:false})[Symbol.asyncIterator]();
const read = async()=>JSON.parse((await lines.next()).value);
const send = value=>process.stdout.write(JSON.stringify(value)+'\n');
const p = await read();
let messages=0;
const query = async(sql,args=[])=>{
  if(++messages>200)throw new Halt('component','message_bound');
  send({op:'sql',sql,args});
  const reply=await read();
  if(reply.error)throw new Halt('component','injected_boundary_failure');
  return reply.rows;
};
try{
  if(p.op==='compute_b'){
    const command={action:p.action,data:p.action==='build'?{intake:C.defaults}:p.data};
    validate(command,'B');
    const result=await next(p.row,command);
    send({op:'complete',value:{event:result.event,status:result.status,version:result.version,
      content:result.content,candidate_hash:result.candidate_hash,
      row_revision:p.row.revision,source_hash:p.row.basis.model}});
  }else if(p.op==='controller'||p.op==='closure'){
    const store=new NativeStore(query);
    const now=Date.now();
    const grant={project:'mokxyyullfhkfalopbzd',id:p.run,run:p.github_run,
      sha:p.source_commit,manifest_sha:await sha(p.contract),starts:now,expires:now+120000};
    const controller=new Controller({grant,store,maxCommands:128});
    await controller.claim();
    if(p.op==='closure'){
      await store.close(p.run,false,p.count);
    }else{
      await controller.execute(p.contract,{
        measure:async()=>({rows:(await query('select count(*)::integer n from fmz6e11_controller_private.steps where run_id=$1::uuid',[p.run]))[0].n}),
        act:async()=>({rows:(await query('select count(*)::integer n from fmz6e11_controller_private.steps where run_id=$1::uuid',[p.run]))[0].n}),
        // This driver always injects at action_started, so this is unreachable.
        validate:async()=>{throw new Halt('component','unexpected_complete_pair');},
      });
    }
    send({op:'complete',value:{completed:true}});
  }else throw new Halt('component','operation_denied');
}catch(error){
  send({op:'complete',failed:true,code:error instanceof Halt?error.code:'component_worker_failed'});
}finally{
  process.stdin.destroy();
}
