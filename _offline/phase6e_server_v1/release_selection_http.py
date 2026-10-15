"""Actual loopback HTTP/Auth/PG slice boundary; never uses hosted endpoints."""
import http.cookiejar,json,threading,urllib.error,urllib.request,uuid
import server

def run(store,workspaces,accounts):
    app=server.Application(store,[workspaces['A'],workspaces['B']],enabled=True,release_slice='preferences')
    httpd=server.serve(app,0);thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
    url='http://127.0.0.1:'+str(httpd.server_port);checks=[]
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(path,data=None,csrf=None):
        headers={'Origin':url,'Content-Type':'application/json'}
        if csrf:headers['X-CSRF']=csrf
        request=urllib.request.Request(url+'/api/'+path,headers=headers,data=None if data is None else json.dumps(data).encode())
        try:response=client.open(request,timeout=5)
        except urllib.error.HTTPError as error:response=error
        with response:return response.status,json.loads(response.read())
    def ok(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    def today():
        status,value=call('today');ok('verified_read',status==200);return value
    def action(view,csrf,name,data=None,key=None,version=None,extra=None):
        payload={'workspace':view['workspace'],'request_id':key or str(uuid.uuid4()),
            'version':view['version'] if version is None else version,'request':{'action':name,'data':data or {}}}
        if extra:payload.update(extra)
        return call('action',payload,csrf)
    try:
        ok('anonymous_denied',call('today')[0]==403)
        ok('real_login',call('login',accounts['b'])[0]==200)
        initial=today();v=initial['views'][0];csrf=initial['csrf'];original=v['state']['preferences']
        ok('exact_member_workspace',v['workspace']==workspaces['B'] and v['role']=='member')
        for name in ('build','apply','approve','record','finish_day'):
            status,value=action(v,csrf,name)
            ok('neighbor_denied_'+name,status==403 and value['code']=='release_slice_denied')
        wrong={**v,'workspace':workspaces['A']}
        ok('other_actor_denied',action(wrong,csrf,'preferences',original)[0]==403)
        ok('browser_cannot_select_slice',action(v,csrf,'preferences',original,extra={'release_slice':'review18'})[0]==403)
        ok('denials_preserve_version',today()['views'][0]['version']==v['version'])
        key=str(uuid.uuid4());changed={**original,'language':'de'}
        ok('selected_preference_saved',action(v,csrf,'preferences',changed,key)[0]==200)
        saved=today()['views'][0]
        ok('durable_exact_preference',saved['state']['preferences']==changed and saved['version']==v['version']+1)
        ok('replay_same_request',action(v,csrf,'preferences',changed,key)[0]==200)
        ok('replay_no_new_version',today()['views'][0]['version']==saved['version'])
        ok('stale_version_denied',action(v,csrf,'preferences',original)[0]==403)
        ok('original_plan_untouched',saved['state']['active']==v['state']['active'])
        ok('explicit_original_preferences',action(saved,csrf,'preferences',original)[0]==200)
        ok('logout',call('logout',{},csrf)[0]==200)
        ok('trainer_login',call('login',accounts['trainer'])[0]==200)
        trainer=today();t=trainer['views'][0]
        ok('trainer_cannot_write_preferences',action(t,trainer['csrf'],'preferences',original)[0]==403)
        ok('trainer_logout',call('logout',{},trainer['csrf'])[0]==200)
        return {'status':'PASS','checks':len(checks),'cases':checks,'actual_local_auth':True,
            'selected_slice':'preferences','hosted_admission':False,'hosted_calls':0}
    finally:httpd.shutdown();httpd.server_close();thread.join(timeout=5)
