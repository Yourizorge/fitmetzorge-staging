"""Real GoTrue + verified local TLS. Ephemeral credentials never enter artifacts."""
import base64,contextlib,hashlib,hmac,json,os,re,secrets,subprocess,time,urllib.request,uuid
import psycopg
from psycopg.rows import dict_row
from psycopg.conninfo import make_conninfo
from store import LocalAuth,Denied
from protocol import Session

IMAGE='supabase/gotrue:v2.197.0'
NAME='fmz-integration-auth-ci'

@contextlib.contextmanager
def environment(gate):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':raise RuntimeError('ci_only')
    def private(args,**kw):
        p=subprocess.run(args,capture_output=True,text=True,timeout=30,**kw)
        if p.returncode:raise RuntimeError('local_auth_container')
        return p.stdout.strip()
    password=private(['docker','exec',gate.container,'sh','-c','printf %s "$POSTGRES_PASSWORD"'])
    network=private(['docker','inspect','--format','{{range $key, $value := .NetworkSettings.Networks}}{{$key}}{{end}}',gate.container])
    ports=private(['docker','port',gate.container,'5432/tcp']).splitlines()
    endpoints=[p for p in ports if re.fullmatch(r'(127\.0\.0\.1|0\.0\.0\.0):\d+',p)]
    if len(endpoints)!=1 or not re.fullmatch(r'[A-Za-z0-9_-]+',network):raise RuntimeError('ci_endpoint')
    dsn=make_conninfo(host='127.0.0.1',port=int(endpoints[0].split(':')[1]),dbname='postgres',user='postgres',
        password=password,sslmode='verify-full',sslrootcert=str(gate.work/'fmz-ci-ca.crt'))
    secret=secrets.token_hex(32)
    def jwt(role):
        def b64(x):return base64.urlsafe_b64encode(json.dumps(x,separators=(',',':')).encode()).decode().rstrip('=')
        raw=b64({'alg':'HS256','typ':'JWT'})+'.'+b64({'role':role,'iss':'supabase','exp':int(time.time())+900})
        return raw+'.'+base64.urlsafe_b64encode(hmac.new(secret.encode(),raw.encode(),hashlib.sha256).digest()).decode().rstrip('=')
    env={**os.environ,'GOTRUE_DB_DATABASE_URL':'postgres://supabase_auth_admin:'+password+'@'+gate.container+':5432/postgres','GOTRUE_JWT_SECRET':secret}
    gate.command('integration-auth-image',['docker','pull',IMAGE],timeout=180)
    digests=json.loads(private(['docker','image','inspect','--format','{{json .RepoDigests}}',IMAGE]))
    args=['docker','run','-d','--name',NAME,'--network',network,'-p','127.0.0.1:59999:9999','-e','GOTRUE_DB_DATABASE_URL','-e','GOTRUE_JWT_SECRET']
    config={'GOTRUE_API_HOST':'0.0.0.0','GOTRUE_API_PORT':'9999','GOTRUE_DB_DRIVER':'postgres',
        'API_EXTERNAL_URL':'http://127.0.0.1:59999','GOTRUE_SITE_URL':'http://127.0.0.1:59999',
        'GOTRUE_JWT_ISSUER':'http://127.0.0.1:59999','GOTRUE_JWT_ADMIN_ROLES':'service_role',
        'GOTRUE_JWT_AUD':'authenticated','GOTRUE_JWT_DEFAULT_GROUP_NAME':'authenticated','GOTRUE_JWT_EXP':'3600',
        'GOTRUE_EXTERNAL_EMAIL_ENABLED':'true','GOTRUE_MAILER_AUTOCONFIRM':'true','GOTRUE_DISABLE_SIGNUP':'true',
        'GOTRUE_SECURITY_REFRESH_TOKEN_ROTATION_ENABLED':'true','GOTRUE_LOG_LEVEL':'panic'}
    for k,v in config.items():args+=['-e',k+'='+v]
    args.append(IMAGE);started=False
    try:
        private(args,env=env);started=True;env.clear();password=None
        healthy=False
        for _ in range(10):
            try:
                with urllib.request.urlopen('http://127.0.0.1:59999/health',timeout=2) as r:healthy=r.status==200
                if healthy:break
            except OSError:pass
            time.sleep(1)
        if not healthy:raise RuntimeError('local_auth_health')
        auth=LocalAuth('http://127.0.0.1:59999');tokens={};claims={};accounts={};admin_token=jwt('service_role')
        with psycopg.connect(dsn,autocommit=True,prepare_threshold=None,row_factory=dict_row) as connection:
            events=[];admin=Session(connection,events.append,'fixture_admin')
            from auth_protocol import STATS,difference
            before=admin.execute('select '+STATS+' value').fetchone()['value']
            measured_roles=('postgres','fmz6e_integration_server')
            app_before={role:admin.execute('select '+STATS.replace("rolname='supabase_auth_admin'","rolname='"+role+"'")+' value').fetchone()['value'] for role in measured_roles}
            for role in ('a','trainer','b','owner','outsider'):
                email='fmz-'+uuid.uuid4().hex+'@example.invalid';pw=secrets.token_urlsafe(32)
                user=auth.call('/admin/users',admin_token,{'email':email,'password':pw,'email_confirm':True})
                issued=auth.call('/token?grant_type=password',data={'email':email,'password':pw})
                tokens[role]=issued['access_token'];claims[role]=auth.verify(tokens[role]);accounts[role]={'email':email,'password':pw}
                if claims[role]['sub']!=user['id']:raise RuntimeError('local_auth_subject')
            ctx={'dsn':dsn,'auth':auth,'tokens':tokens,'claims':claims,'admin':admin,'accounts':accounts,'image':IMAGE,'digests':digests}
            try:yield ctx
            finally:
                after=admin.execute('select '+STATS+' value').fetchone()['value']
                load=difference(before,after)
                app_after={role:admin.execute('select '+STATS.replace("rolname='supabase_auth_admin'","rolname='"+role+"'")+' value').fetchone()['value'] for role in measured_roles}
                app_load={role:difference(app_before[role],app_after[role]) for role in measured_roles}
                for value in app_load.values():value['scope']='isolated local CI role; no hosted attribution'
                gate.save('integration-application-io.json',{'before':app_before,'after':app_after,'deltas':app_load,'query_text_read':False})
                complete=[e for e in events if e['phase']=='completed']
                gate.save('integration-native-admin-protocol.json',{'commands':len(complete),
                    'failed_commands':sum(not e['confirmed'] for e in complete),
                    'scope':'disposable fixture/admin, including explicit BEGIN/COMMIT/ROLLBACK; no row values',
                    'templates':sorted({e['template_sha256'] for e in complete})})
                gate.save('integration-managed-auth-protocol.json',load)
    finally:
        env.clear()
        if started:private(['docker','rm','-f',NAME])

def auth_checks(ctx):
    auth=ctx['auth'];roles=ctx['accounts'];old=ctx['tokens']['a'];subject=ctx['claims']['a']['sub'];checks=[]
    second=auth.call('/token?grant_type=password',data=roles['a'])['access_token']
    if auth.verify(second)['sub']!=subject:raise RuntimeError('relogin_subject')
    checks.append('real_password_relogin_same_subject')
    # /logout may have an empty body. Read no payload and retain no token.
    req=urllib.request.Request(auth.url+'/logout?scope=global',headers={'Authorization':'Bearer '+second},data=b'')
    with urllib.request.urlopen(req,timeout=5) as response:
        if response.status!=204:raise RuntimeError('logout_status')
    row=ctx['admin'].execute('select count(*) n from auth.sessions where user_id=%s',[subject]).fetchone()
    if row['n']!=0:raise RuntimeError('logout_sessions')
    checks.append('global_logout_deletes_sessions')
    for token in (old,second):
        try:auth.verify(token)
        except Denied:checks.append('revoked_token_denied')
        else:raise RuntimeError('revoked_token_accepted')
    return {'checks':checks,'auth_image':ctx['image'],'image_digests':ctx['digests'],'secrets_exported':False}
