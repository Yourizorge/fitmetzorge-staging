"""Private native sessions shared by disposable CI and the scoped staging run.

No connection string is serialized into the Node worker or any receipt. The
caller owns admission, command accounting, expiry and exact cleanup.
"""
import json,pathlib,re,subprocess

PROJECT='mokxyyullfhkfalopbzd'

class NativeRuntime:
    def __init__(self,parameters,auth_base,*,environment):
        import psycopg
        from psycopg.rows import dict_row
        p=dict(parameters)
        if environment not in ('disposable_ci','staging'):raise ValueError('native_environment')
        if p.get('sslmode')!='verify-full' or not pathlib.Path(p.get('sslrootcert','')).is_file():
            raise ValueError('native_tls_required')
        if str(p.get('connect_timeout'))!='5' or p.get('dbname')!='postgres':raise ValueError('native_connection_limits')
        expected='http://127.0.0.1:59999' if environment=='disposable_ci' else 'https://'+PROJECT+'.supabase.co/auth/v1'
        if auth_base!=expected:raise ValueError('native_auth_endpoint')
        if environment=='disposable_ci' and p.get('host')!='127.0.0.1':raise ValueError('native_loopback')
        if environment=='staging' and (p.get('user')!='postgres.'+PROJECT or str(p.get('port'))!='5432'
                or not re.fullmatch(r'aws-[0-9]+-[a-z0-9-]+\.pooler\.supabase\.com',p.get('host',''))
                or p.get('options')!='-c jit=true -c statement_timeout=5000 -c lock_timeout=1000'):
            raise ValueError('native_session_binding')
        self.__parameters=p
        self.__driver=psycopg
        self.__row_factory=dict_row
        self.environment=environment;self.auth_base=auth_base

    def __repr__(self):return '<NativeRuntime private parameters>'

    def connect(self):
        return self.__driver.connect(**self.__parameters,autocommit=True,prepare_threshold=None,row_factory=self.__row_factory)

    def clear(self):self.__parameters.clear()

    @classmethod
    def disposable(cls,gate):
        def private(args):
            p=subprocess.run(args,capture_output=True,text=True,timeout=10)
            if p.returncode:raise RuntimeError('ci_native_setup')
            return p.stdout.strip()
        password=private(['docker','exec',gate.container,'sh','-c','printf %s "$POSTGRES_PASSWORD"'])
        ports=private(['docker','port',gate.container,'5432/tcp']).splitlines()
        endpoints=[x for x in ports if re.fullmatch(r'(127\.0\.0\.1|0\.0\.0\.0):\d+',x)]
        if len(endpoints)!=1:raise RuntimeError('ci_loopback_binding')
        return cls({'host':'127.0.0.1','port':int(endpoints[0].split(':')[1]),'dbname':'postgres','user':'postgres',
            'password':password,'sslmode':'verify-full','sslrootcert':str(gate.work/'fmz-ci-ca.crt'),
            'connect_timeout':5,'options':'-c statement_timeout=5000 -c lock_timeout=1000'},
            'http://127.0.0.1:59999',environment='disposable_ci')

    @classmethod
    def staging(cls,connect,token,ca,parameter_validator):
        # The existing validator binds the exact dashboard Connect record and
        # CA. A caller-supplied hostname alone never authorizes a connection.
        parameters=parameter_validator(connect,token,ca)
        return cls(parameters,'https://'+PROJECT+'.supabase.co/auth/v1',environment='staging')

    def context(self,ids,aliases):
        return {'mode':'registered_synthetic','environment':self.environment,'authBase':self.auth_base,
            'registeredIds':ids,'identityBinding':{'project':PROJECT,'preexisting':True,
            'identities':{r:{'id':ids[r],'email':aliases[r],'registered':True} for r in ids}}}
