"""Disposable PG17 storage/RLS tests. Auth is explicitly a local test double here."""
import datetime,ipaddress,json,os,pathlib,sys,time,uuid
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'supabase/.temp/phase6e-server-deps'))
sys.path.insert(0,str(ROOT/'_offline/phase6e11/fingerprint_v1'))
from local_cluster import Cluster
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import psycopg
from psycopg.rows import dict_row
from psycopg.conninfo import make_conninfo
from database_tests import run
from store import Denied


def tls(cluster,db):
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'FMZ local integration CA')])
    now=datetime.datetime.now(datetime.timezone.utc)
    cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1))
        .not_valid_after(now+datetime.timedelta(hours=2))
        .add_extension(x509.BasicConstraints(ca=True,path_length=None),critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1')),
                                                   x509.DNSName('localhost')]),critical=False)
        .sign(key,hashes.SHA256()))
    ca=cluster.path/'local-integration.crt';private=cluster.path/'local-integration.key'
    ca.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    for field,value in [('ssl_cert_file',ca.as_posix()),('ssl_key_file',private.as_posix()),('ssl','on')]:
        db.query("alter system set "+field+"='"+value.replace("'","''")+"'")
    db.query('select pg_reload_conf()')
    return ca


def main():
    cluster=Cluster();native=None;result={'status':'NO_GO','hosted_calls':0}
    try:
        native=cluster.start();ca=tls(cluster,native)
        dsn=make_conninfo(host='127.0.0.1',port=cluster.port,user='postgres',dbname='postgres',
                         sslmode='verify-full',sslrootcert=str(ca))
        with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
            db.execute('create role anon;create role authenticated;create role service_role;create schema auth;'
                       'create table auth.users(id uuid primary key);'
                       'create table auth.sessions(id uuid primary key,user_id uuid,not_after timestamptz)')
            if os.environ.get('FMZ_TEST_AUTH_RLS')=='1':db.execute('alter table auth.sessions enable row level security')
            migration=next((HERE/'supabase/migrations').glob('*.sql'))
            db.execute(migration.read_text())
            claims={role:{'sub':str(uuid.uuid4()),'session_id':str(uuid.uuid4())}
                    for role in ('a','trainer','b','owner','outsider')}
            for c in claims.values():
                db.execute('insert into auth.users values(%s)',[c['sub']])
                db.execute('insert into auth.sessions values(%s,%s,now()+interval \'20 minutes\')',[c['session_id'],c['sub']])
            class LocalDouble:
                def verify(self,token):
                    if token not in claims:raise Denied('auth_denied')
                    return claims[token]
            result=run(dsn,LocalDouble(),{r:r for r in claims},claims,db,'test_double_not_Auth_proof')
    except Exception as e:
        result.update(error_type=type(e).__name__,code=getattr(e,'sqlstate',None))
        if isinstance(e,(AssertionError,Denied)):result['error']=str(e)
    finally:
        if native:native.close()
        cluster.stop()
        path=cluster.path/'integration-result.json'
        with path.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({**result,'evidence':str(path)}))
    return 0 if result['status']=='LOCAL_DATABASE_PASS' else 2


if __name__=='__main__':sys.exit(main())
