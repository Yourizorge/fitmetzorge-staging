"""Scoped temporary CLI credentials + pinned-CA session pooler; no secret persistence."""
import ctypes as C, datetime, hashlib, json, os, pathlib, re, sys, time, urllib.request
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from inventory import sb, NoRedirect
sys.path.insert(0,str(ROOT/"_offline/phase6e11/fingerprint_v1"))
from pq import LocalDB, BIN
from guard import Stop
PROJECT="mokxyyullfhkfalopbzd"
HOST="aws-0-eu-west-2.pooler.supabase.com"
CA_SHA="700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7"
def parameters(role,password,ca):
    if role != "cli_login_supabase_read_only_user":
        raise Stop("unexpected_managed_login_role")
    if not isinstance(password,str) or not password:raise Stop("temporary_credential_missing")
    if hashlib.sha256(ca.read_bytes()).hexdigest()!=CA_SHA:raise Stop("ca_changed")
    if any(k.startswith("PG") for k in os.environ):raise Stop("implicit_pg_environment")
    return {"host":HOST,"port":"5432","dbname":"postgres","user":role+"."+PROJECT,
      "password":password,"sslmode":"verify-full","sslrootcert":str(ca.resolve()),
      "connect_timeout":"5","application_name":"fmz6e11_temporary_readonly_v1",
      "options":"-c default_transaction_read_only=on -c statement_timeout=5000 -c lock_timeout=1000"}
def issue_readonly():
    req=urllib.request.Request("https://api.supabase.com/v1/projects/"+PROJECT+"/cli/login-role",
        method="POST",data=b'{"read_only":true}',headers={"Authorization":"Bearer "+sb.credential(),
        "Content-Type":"application/json","Accept":"application/json"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=20) as response:
            value=json.loads(response.read(16000))
    except Exception:raise Stop("temporary_login_request_failed") from None
    if not isinstance(value,dict) or set(value)!={"role","password","ttl_seconds"}:
        raise Stop("temporary_login_shape")
    if type(value["ttl_seconds"]) is not int or not 1<=value["ttl_seconds"]<=300:
        raise Stop("temporary_ttl_boundary")
    return value
class TemporaryReadOnly(LocalDB):
    def __init__(self,role,password,ca):
        params=parameters(role,password,ca)
        self.dll_directory=os.add_dll_directory(str(BIN)) if os.name=="nt" else None
        self.lib=C.CDLL(str(BIN/("libpq.dll" if os.name=="nt" else "libpq.so")))
        signatures={
          "PQconnectdbParams":(C.c_void_p,[C.POINTER(C.c_char_p),C.POINTER(C.c_char_p),C.c_int]),
          "PQstatus":(C.c_int,[C.c_void_p]),"PQsslInUse":(C.c_int,[C.c_void_p]),
          "PQfinish":(None,[C.c_void_p]),"PQsendQuery":(C.c_int,[C.c_void_p,C.c_char_p]),
          "PQsetSingleRowMode":(C.c_int,[C.c_void_p]),"PQconsumeInput":(C.c_int,[C.c_void_p]),
          "PQisBusy":(C.c_int,[C.c_void_p]),"PQgetResult":(C.c_void_p,[C.c_void_p]),
          "PQresultStatus":(C.c_int,[C.c_void_p]),"PQntuples":(C.c_int,[C.c_void_p]),
          "PQnfields":(C.c_int,[C.c_void_p]),"PQgetisnull":(C.c_int,[C.c_void_p,C.c_int,C.c_int]),
          "PQgetvalue":(C.c_char_p,[C.c_void_p,C.c_int,C.c_int]),"PQcmdTuples":(C.c_char_p,[C.c_void_p]),
          "PQclear":(None,[C.c_void_p]),"PQresultErrorField":(C.c_char_p,[C.c_void_p,C.c_int])}
        for name,(result,args) in signatures.items():
            fn=getattr(self.lib,name);fn.restype=result;fn.argtypes=args
        arr=C.c_char_p*(len(params)+1)
        self.conn=self.lib.PQconnectdbParams(arr(*[k.encode() for k in params],None),
            arr(*[v.encode() for v in params.values()],None),0)
        if not self.conn or self.lib.PQstatus(self.conn)!=0 or self.lib.PQsslInUse(self.conn)!=1:
            self.close();raise Stop("verified_temporary_connection_failed")
        self.client_tls_verified=True
        self.ledger=None;self.queries=0;self.bytes_received=0;self.terminal_count=None
META_SQL="""/* fmz6e11_temporary_connection_v1 */
select jsonb_build_object('database',current_database(),'current_user',current_user,
'session_user',session_user,'pg_version_num',current_setting('server_version_num'),
'read_only',current_setting('transaction_read_only'),'ssl',s.ssl,'tls_version',s.version,
'backend_pid',pg_backend_pid())::text from pg_stat_ssl s where s.pid=pg_backend_pid()"""
def check(folder):
    from ops import write
    result={"project":PROJECT,"status":"STARTED","phase":"temporary_credential",
            "at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "database_password_reset":False,"hosted_application_writes":0,"retries":0}
    if (folder/"temporary-connection.json").exists():raise Stop("no_automatic_retry")
    db=None
    try:
        value=issue_readonly()
        result.update(role=value["role"],ttl_seconds=value["ttl_seconds"])
        result["phase"]="verified_tls_connect"
        db=TemporaryReadOnly(value["role"],value["password"],folder/"prod-ca-2021.crt")
        del value
        result["phase"]="readonly_metadata"
        db.query("begin read only",timeout=8)
        started=time.monotonic();rows=db.query(META_SQL,timeout=8)
        result["elapsed_ms"]=(time.monotonic()-started)*1000
        if db.terminal_count!=1 or len(rows)!=1:raise Stop("metadata_terminal")
        meta=json.loads(rows[0][0])
        # pg_stat_ssl describes the upstream pooler/backend hop, not libpq's TLS peer.
        result.update(metadata=meta,client_tls_verified=db.client_tls_verified,
                      metadata_stream_terminal_count=db.terminal_count)
        if meta["database"]!="postgres" or meta["pg_version_num"]!="170006" or meta["read_only"]!="on" or not db.client_tls_verified:
            raise Stop("staging_metadata_mismatch")
        db.query("rollback",timeout=8)
        result.update(status="READ_ONLY_CONNECTION_PASS",metadata=meta,query_count=db.queries,
                      bytes_received=db.bytes_received)
    except Exception as e:
        result.update(status="NO_GO",error_type=type(e).__name__,
          stop_reason=str(e) if isinstance(e,Stop) and re.fullmatch(r"[a-zA-Z0-9_]+",str(e)) else "sanitized_error")
    finally:
        if db:db.close()
        write(folder/"temporary-connection.json",result)
    print(json.dumps(result))
    return result["status"]=="READ_ONLY_CONNECTION_PASS"
if __name__=="__main__":
    folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=(ROOT/"supabase/.temp").resolve():raise SystemExit("evidence_scope")
    sys.exit(0 if check(folder) else 2)
