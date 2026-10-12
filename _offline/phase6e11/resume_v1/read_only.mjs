// A dedicated max:1 client avoids the pinned driver's first-reserve startup defect.
// The caller enforces one socket, TLS/CA/hostname, no retry and hard deadlines.
export const GUARD="select current_setting('transaction_read_only')='on' as readonly, pg_backend_pid() as backend";
export const IDENTITY="select current_database()='postgres' and current_user='postgres' as bound, pg_backend_pid() as backend, encode(sha256(system_identifier::text::bytea),'hex') as instance from pg_control_system()";
export const INSTANCE='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15';
const codes=new Set(['DEADLINE','CONNECTION_CLOSED','CONNECT_TIMEOUT','READONLY_UNCONFIRMED','IDENTITY_MISMATCH','BACKEND_CHANGED']);
function safe(e){return codes.has(e?.code)?e.code:'SANITIZED_QUERY_ERROR';}
function fail(code){throw Object.assign(Error(),{code});}
export async function readOnly(sql,deadline,{verifyInstance=true}={}){
  let phase='readonly_begin',commands=0,authenticated=false,readonly=false,bound=false,rollback=false;
  let error=null,rollbackError=null,backend=null;
  const query=(text,ms=2000)=>{commands++;return deadline(()=>sql.unsafe(text),ms);};
  try{
    await query('BEGIN TRANSACTION READ ONLY',5000);authenticated=true;
    phase='readonly_guard';const rows=await query(GUARD);
    if(rows.length!==1||rows[0].readonly!==true||!Number.isSafeInteger(rows[0].backend)||rows[0].backend<1)fail('READONLY_UNCONFIRMED');
    readonly=true;backend=rows[0].backend;
    if(verifyInstance){
      phase='readonly_identity';const identity=await query(IDENTITY);
      if(identity.length!==1||identity[0].bound!==true||identity[0].instance!==INSTANCE)fail('IDENTITY_MISMATCH');
      if(identity[0].backend!==backend)fail('BACKEND_CHANGED');
      bound=true;
    }
    phase='metadata_complete';
  }catch(e){error=safe(e);}
  finally{
    // Even an unconfirmed BEGIN can have reached the server. Reconnects must be
    // blocked by the caller; failed rollback is never promoted to success.
    try{await query('ROLLBACK');rollback=true;}catch(e){rollbackError=safe(e);}
  }
  return {status:phase==='metadata_complete'&&!error&&rollback?'READONLY_PASS':'NO_GO',
    phase,error,rollbackError,commands,authenticated,readonly,bound,rollback,
    backend_consistent:bound,instance_checked:verifyInstance};
}
