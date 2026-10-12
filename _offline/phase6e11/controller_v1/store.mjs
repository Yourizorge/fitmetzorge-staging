import {Halt,metadata,sha} from './core.mjs';
const S='fmz6e11_controller_private';
const TAG='/* fmz6e11:controller_v1:evidence */ ';
const previous={action_started:'before_saved',action_confirmed:'action_started',after_saved:'action_confirmed',pair_validated:'after_saved'};
export class Store {
  constructor(query){this.query=query;}
  async one(sql,args){const rows=await this.query(TAG+sql,args);if(rows.length!==1)throw new Halt('evidence','store_guard');return rows[0];}
  async claim(g){
    return this.one(`insert into ${S}.runs(id,github_run,head_sha,manifest_sha,expires_at)
      values($1::uuid,$2::bigint,$3,$4,to_timestamp($5::double precision/1000)) returning id`,
      [g.id,g.run,g.sha,g.manifest_sha,g.expires]);
  }
  async before(run,c,before,hash){
    const value=metadata(before);
    return this.one(`with r as (select id from ${S}.runs where id=$1::uuid and state='running'
      and expires_at>clock_timestamp() and next_step=$2 for update), s as (
      insert into ${S}.steps(run_id,step,action_id,request_id,actor,workspace,kind,operation,contract_sha)
      select r.id,$2,$3::uuid,$4::uuid,$5::uuid,$6::uuid,$7,$8,$9 from r returning run_id,step)
      insert into ${S}.evidence(run_id,step,phase,metadata,sha256)
      select run_id,step,'before_saved',$10::jsonb,$11 from s returning phase`,
      [run,c.step,c.action_id,c.request_id,c.actor,c.workspace,c.kind,c.operation,hash,JSON.stringify(value),await sha(value)]);
  }
  async record(run,step,phase,data){
    if(!previous[phase])throw new Halt('evidence','phase_invalid');
    const value=metadata(data);
    return this.one(`with r as (select id from ${S}.runs where id=$1::uuid and state='running'
      and next_step=$2 and ($3<>'action_started' or expires_at>clock_timestamp()) for update), s as (
      update ${S}.steps set state=$3 from r where run_id=r.id and step=$2 and state=$4 returning run_id,step), e as (
      insert into ${S}.evidence(run_id,step,phase,metadata,sha256)
      select run_id,step,$3,$5::jsonb,$6 from s returning run_id,phase), n as (
      update ${S}.runs set next_step=next_step+1 where id in(select run_id from e where phase='pair_validated'))
      select phase from e`,[run,step,phase,previous[phase],JSON.stringify(value),await sha(value)]);
  }
  async halt(run,step,reason){
    const value=metadata(reason);
    return this.one(`with r as (update ${S}.runs set state='stopped' where id=$1::uuid and state='running' returning id),
      s as (update ${S}.steps set state='stopped' from r where run_id=r.id and step=$2 returning run_id,step),
      e as (insert into ${S}.evidence(run_id,step,phase,metadata,sha256)
      select run_id,step,'stopped',$3::jsonb,$4 from s returning phase) select id from r`,
      [run,step,JSON.stringify(value),await sha(value)]);
  }
  async close(run,complete,count){
    if(typeof complete!=='boolean'||!Number.isSafeInteger(count)||count<0||count>128)throw new Halt('evidence','close_budget');
    return this.one(`update ${S}.runs set state=$2,command_count=$3,closed_at=clock_timestamp()
      where id=$1::uuid and state in ('running','stopped') and ($2<>'complete' or
        (state='running' and next_step>0 and next_step=(select count(*) from ${S}.steps where run_id=$1::uuid)
         and not exists(select 1 from ${S}.steps where run_id=$1::uuid and state<>'pair_validated')))
      returning state`,[run,complete?'complete':'closed',count]);
  }
}
