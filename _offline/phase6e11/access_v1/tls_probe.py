"""One bounded pre-authentication TLS probe. No password, token or SQL is sent."""
import argparse, datetime, hashlib, json, pathlib, socket, ssl, struct, sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"_offline/phase6e11/ci41"))
import ops
PROJECT="mokxyyullfhkfalopbzd"
CA_SHA="700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7"
HOSTS={"direct":"db."+PROJECT+".supabase.co","session_pooler":"aws-0-eu-west-2.pooler.supabase.com"}
def probe(kind, ca):
    if kind not in HOSTS or hashlib.sha256(ca.read_bytes()).hexdigest()!=CA_SHA:
        raise RuntimeError("binding_failed")
    context=ssl.create_default_context(cafile=str(ca))
    context.check_hostname=True
    context.verify_mode=ssl.CERT_REQUIRED
    context.minimum_version=ssl.TLSVersion.TLSv1_2
    result={"project":PROJECT,"host_type":kind,"host":HOSTS[kind],"port":5432,
        "at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"ca_sha256":CA_SHA,
        "sslmode_equivalent":"verify-full","password_sent":False,"sql_queries":0}
    raw=None
    try:
        raw=socket.create_connection((HOSTS[kind],5432),timeout=5)
        raw.settimeout(5)
        raw.sendall(struct.pack("!II",8,80877103))
        if raw.recv(1)!=b"S":raise RuntimeError("postgres_ssl_refused")
        with context.wrap_socket(raw,server_hostname=HOSTS[kind]) as secured:
            result.update(status="TLS_PASS",hostname_verified=True,chain_verified=True,
                tls_version=secured.version(),
                peer_sha256=hashlib.sha256(secured.getpeercert(binary_form=True)).hexdigest())
        raw=None
    except ssl.SSLCertVerificationError as e:
        result.update(status="CERTIFICATE_NO_GO",verify_code=e.verify_code)
    except (TimeoutError,ConnectionError,socket.gaierror,OSError) as e:
        result.update(status="NETWORK_UNAVAILABLE",error_type=type(e).__name__,errno=e.errno)
    except Exception as e:
        result.update(status="TLS_NO_GO",error_type=type(e).__name__)
    finally:
        if raw is not None:raw.close()
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("kind",choices=HOSTS);p.add_argument("folder")
    a=p.parse_args();folder=pathlib.Path(a.folder).resolve()
    if folder.parent!=(ROOT/"supabase/.temp").resolve():raise SystemExit("evidence_scope")
    output=folder/("tls-"+a.kind+".json")
    if output.exists():raise SystemExit("no_automatic_retry")
    result=probe(a.kind,folder/"prod-ca-2021.crt")
    ops.write(output,result)
    print(json.dumps(result))
    sys.exit(0 if result["status"]=="TLS_PASS" else 2)
