"""Default-off loopback app entry. GoTrue tokens remain in server memory only."""
import http.cookies,http.server,json,mimetypes,pathlib,secrets,threading,time,traceback,uuid
from store import Denied,identifier
HERE=pathlib.Path(__file__).resolve().parent

class Application:
    def __init__(self,store,workspaces,enabled=False):
        if enabled is not True:raise Denied('feature_disabled')
        self.store=store;self.workspaces=frozenset(identifier(x) for x in workspaces)
        self.sessions={};self.lock=threading.Lock()
    def session(self,cookie):
        jar=http.cookies.SimpleCookie()
        try:jar.load(cookie or '');sid=jar['fmz_local'].value
        except (KeyError,http.cookies.CookieError):raise Denied('login_required') from None
        with self.lock:
            session=self.sessions.get(sid)
            if not session or session['expires']<=time.time():
                self.sessions.pop(sid,None);raise Denied('login_required')
            return sid,dict(session)

def serve(app,port=8766):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,value,cookie=None,mime='application/json'):
            raw=json.dumps(value).encode() if mime=='application/json' else value
            self.send_response(status);self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'")
            self.send_header('Referrer-Policy','no-referrer')
            if cookie:self.send_header('Set-Cookie',cookie)
            self.end_headers();self.wfile.write(raw)
        def valid_host(self):
            if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port):raise Denied('host')
        def failed(self,error):
            frames=[{'file':pathlib.Path(f.filename).name,'line':f.lineno}
                    for f in traceback.extract_tb(error.__traceback__)
                    if pathlib.Path(f.filename).parent==HERE]
            self.send(503,{'code':'server_unavailable','class':type(error).__name__,
                           'sqlstate':getattr(error,'sqlstate',None),'frames':frames})
        def do_GET(self):
            try:
                self.valid_host()
                static={'/':'ui.html','/ui.js':'ui.js','/ui.css':'ui.css','/panels.js':'panels.js'}
                if self.path=='/brand.png':
                    return self.send(200,(HERE.parents[1]/'assets/fit-met-zorge-logo-cropped.png').read_bytes(),mime='image/png')
                if self.path in static:
                    path=HERE/static[self.path]
                    return self.send(200,path.read_bytes(),mime=mimetypes.guess_type(str(path))[0] or 'text/plain')
                _,session=app.session(self.headers.get('Cookie'))
                if self.path!='/api/today':raise Denied('route')
                views=[]
                for workspace in sorted(app.workspaces):
                    try:views.append(app.store.read(workspace,session['token']))
                    except Denied as e:
                        if str(e)!='workspace_denied':raise
                if not views:raise Denied('workspace_denied')
                self.send(200,{'views':views,'csrf':session['csrf']})
            except Denied as e:self.send(403,{'code':str(e)})
            except Exception as e:
                self.failed(e)
        def do_POST(self):
            try:
                self.valid_host()
                if self.headers.get('Origin')!='http://127.0.0.1:'+str(self.server.server_port):raise Denied('origin')
                if self.headers.get('Content-Type')!='application/json':raise Denied('content_type')
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=131072:raise Denied('request_size')
                data=json.loads(self.rfile.read(size))
                if self.path=='/api/login':
                    if set(data)!= {'email','password'}:raise Denied('payload')
                    token=app.store.auth.call('/token?grant_type=password',data=data)['access_token']
                    app.store.auth.verify(token)
                    if not any(allowed(workspace,token) for workspace in app.workspaces):raise Denied('workspace_denied')
                    sid=secrets.token_urlsafe(32)
                    with app.lock:
                        app.sessions={k:v for k,v in app.sessions.items() if v['expires']>time.time()}
                        if len(app.sessions)>=20:raise Denied('local_capacity')
                        app.sessions[sid]={'token':token,'csrf':secrets.token_urlsafe(32),'expires':time.time()+900}
                    return self.send(200,{'ok':True},cookie='fmz_local='+sid+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=900')
                sid,session=app.session(self.headers.get('Cookie'))
                if not secrets.compare_digest(self.headers.get('X-CSRF',''),session['csrf']):raise Denied('csrf')
                if self.path=='/api/logout':
                    app.store.auth.call('/logout?scope=local',session['token'],{},method='POST')
                    with app.lock:app.sessions.pop(sid,None)
                    return self.send(200,{'ok':True},cookie='fmz_local=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/')
                if self.path!='/api/action' or set(data)!= {'workspace','request_id','version','request'}:raise Denied('route')
                if data['workspace'] not in app.workspaces:raise Denied('workspace_denied')
                result=app.store.execute(data['workspace'],session['token'],data['request_id'],data['version'],data['request'])
                self.send(200,result)
            except Denied as e:self.send(403,{'code':str(e)})
            except (ValueError,KeyError,TypeError):self.send(400,{'code':'payload'})
            except Exception as e:
                self.failed(e)
    def allowed(workspace,token):
        try:app.store.read(workspace,token);return True
        except Denied:return False
    server=http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True
    return server

if __name__=='__main__':
    import os,sys
    try:
        integration=os.environ.get('FMZ_LOCAL_INTEGRATION_ENABLED')=='1'
        registration=os.environ.get('FMZ_LOCAL_REGISTRATION12_ENABLED')=='1'
        if integration==registration:raise Denied('feature_disabled')
        from store import Store,LocalAuth
        path=pathlib.Path(os.environ['FMZ_LOCAL_INTEGRATION_CONFIG']).resolve()
        # Only a private local operator supplies this configuration. Never serve it.
        config=json.loads(path.read_text())
        if registration:
            from registration_store import RegistrationStore
            if set(config)!= {'dsn','auth_url','bindings'}:raise Denied('configuration')
            store=RegistrationStore(config['dsn'],LocalAuth(config['auth_url']),config['bindings'],enabled=True)
            workspaces=list(config['bindings'])
        else:
            if set(config) not in ({'dsn','auth_url','workspaces'},{'dsn','auth_url','workspaces','registration_bindings'}):raise Denied('configuration')
            store=Store(config['dsn'],LocalAuth(config['auth_url']),enabled=True,
                        full_day21=os.environ.get('FMZ_LOCAL_FULL_DAY21_ENABLED')=='1')
            workspaces=config['workspaces']
            if 'registration_bindings' in config:
                from composed_store import ComposedStore
                from registration_store import RegistrationStore
                registration_store=RegistrationStore(config['dsn'],store.auth,config['registration_bindings'],enabled=True)
                store=ComposedStore(store,workspaces,registration_store)
                workspaces=list(workspaces)+list(registration_store.bindings)
        app=Application(store,workspaces,enabled=True)
        http=serve(app)
        print('LOCAL SYNTHETIC ONLY: http://127.0.0.1:8766',flush=True)
        try:http.serve_forever()
        finally:http.server_close()
    except (Denied,KeyError,ValueError,OSError):
        print('Local integration unavailable; check the private local configuration.',file=sys.stderr)
        sys.exit(2)
