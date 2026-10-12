// One explicitly read-only READ COMMITTED cycle. Each SELECT gets a fresh
// snapshot; it is not a reused before-state or a repeatable-read fingerprint.
import {Halt,metadata} from '../controller_v1/core.mjs';
import {INSTANCE} from '../resume_v1/read_only.mjs';
export const GUARD=`select current_setting('transaction_read_only')='on' as readonly,
 current_setting('transaction_isolation')='read committed' as fresh,
 pg_backend_pid() as backend,current_database()='postgres' and current_user='postgres' and ssl as bound,
 encode(sha256(system_identifier::text::bytea),'hex') as instance
 from pg_control_system(),pg_stat_ssl where pid=pg_backend_pid()`;
export class ScopedCycle{
 constructor({query,close,queries,instance=INSTANCE}){
  if(typeof query!=='function'||typeof close!=='function'||!queries||Object.getPrototypeOf(queries)!==Object.prototype)
   throw new Halt('admission','scoped_configuration');
  this.query=query;this.close=close;this.queries=Object.freeze({...queries});
  this.instance=instance;this.backend=null;this.active=false;this.closed=false;this.busy=false;this.started=false;this.failure=null;
 }
 async begin(){
  if(this.started||this.closed)throw new Halt('admission','cycle_reuse');
  this.started=true;this.busy=true;
  try{
   await this.query('BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY');
   const rows=await this.query(GUARD),r=rows[0];
   if(rows.length!==1||r.readonly!==true||r.fresh!==true||r.bound!==true||
      r.instance!==this.instance||!Number.isSafeInteger(r.backend)||r.backend<1)throw new Halt('measurement','readonly_unconfirmed');
   this.backend=r.backend;this.active=true;
  }catch(error){
   this.failure=error instanceof Halt?error:new Halt('measurement','readonly_begin_unconfirmed');
   await this.end();throw this.failure;
  }
  finally{this.busy=false;}
 }
 async read(key,args=[]){
  if(!this.active||this.closed||this.busy||!Object.hasOwn(this.queries,key))throw new Halt('measurement','scoped_query_denied');
  this.busy=true;
  try{
   const body=this.queries[key];
   // Bodies are a source-bound server allowlist, never request-provided SQL.
   const rows=await this.query(`select current_setting('transaction_read_only')='on' as readonly,
    current_setting('transaction_isolation')='read committed' as fresh,pg_backend_pid() as backend,
    case when current_setting('transaction_read_only')='on'
      and pg_backend_pid()=$1::integer then (${body}) else null end as value`,[this.backend,...args]);
   const r=rows[0];
   if(rows.length!==1||r.backend!==this.backend||r.readonly!==true||r.fresh!==true)
    throw new Halt('measurement','scoped_connection_changed');
   return metadata(r.value);
  }catch(error){
   this.active=false;this.failure=error instanceof Halt?error:new Halt('measurement','scoped_read_unconfirmed');
   throw this.failure;
  }
  finally{this.busy=false;}
 }
 async end(){
  if(this.closed)return;
  this.closed=true;this.active=false;
  const failures=[];
  try{if(this.started)await this.query('ROLLBACK');}
  catch{failures.push({phase:'rollback',code:'rollback_unconfirmed'});}
  try{await this.close();}
  catch{failures.push({phase:'close',code:'connection_close_unconfirmed'});}
  if(failures.length){
   const first=failures.shift();
   if(this.failure)failures.unshift(first);
   else this.failure=new Halt(first.phase,first.code);
   this.failure.cleanupFailures=failures;throw this.failure;
  }
 }
}
