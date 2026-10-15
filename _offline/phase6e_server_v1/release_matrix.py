"""Eight actual loopback HTTP/Auth/PG selections, never a hosted admission."""
import collections, copy, http.cookiejar, json, threading, urllib.error, urllib.request, uuid
import server
from store import Store, SCHEMA, domain, digest, Denied
from registration_store import RegistrationStore
from release_selection import SLICES
from auth_protocol import STATS, difference


def seed(slice_id, route):
    if slice_id in ('registration12','workout12'):
        return domain('registration_initial',scenario='normal' if route=='A' else 'no_trainer')
    state=domain('initial',route=route)
    if slice_id=='review18':
        # Existing approved history is fixture input, not a browser approval bypass.
        row=state['recovery']['rows'][-1]
        state=domain('transition',state=state,request={'action':'recovery',
            'data':{'id':row['id'],'version':row['version'],'value':6}},role='member')
        for _ in range(2):
            for action,data,role in [('edit',{'domain':'time','value':'20:00'},'member'),
                                     ('confirm',{},'member')]+([('approve',{},'trainer')] if route=='A' else [])+[('apply',{},'member')]:
                state=domain('transition',state=state,request={'action':action,'data':data},role=role)
        state=domain('transition',state=state,request={'action':'restore','data':{'version':2}},role='member')
    return state


class Client:
    def __init__(self,url):
        self.url=url
        self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(self,path,data=None,csrf=None):
        headers={'Origin':self.url,'Content-Type':'application/json'}
        if csrf:headers['X-CSRF']=csrf
        request=urllib.request.Request(self.url+'/api/'+path,headers=headers,
            data=None if data is None else json.dumps(data).encode())
        try:response=self.opener.open(request,timeout=5)
        except urllib.error.HTTPError as error:response=error
        with response:return response.status,json.loads(response.read())
    def view(self):
        status,data=self.call('today')
        if status!=200:raise AssertionError('selected_view_'+str(status))
        return data['views'][0],data['csrf']
    def action(self,view,csrf,name,data=None,key=None,extra=None):
        request={'workspace':view['workspace'],'version':view['version'],
                 'request_id':key or str(uuid.uuid4()),'request':{'action':name,'data':data or {}}}
        if extra:request.update(extra)
        return self.call('action',request,csrf)


def run(ctx,save):
    admin=ctx['admin'];claims=ctx['claims'];rows=[];admin_events=[]
    original=admin.observer
    def observe(event):
        admin_events.append(event)
        if original:original(event)
    admin.observer=observe
    def bind(role):
        admin.execute("select set_config('fmz6e.verified_session',%s,false),set_config('request.jwt.claims',%s,false),set_config('fmz6e.request_id',%s,false)",
            [claims[role]['session_id'],json.dumps(claims[role]),str(uuid.uuid4())])
    try:
        admin.operation='release_matrix_subject_setup'
        for value in claims.values():
            admin.execute('insert into '+SCHEMA+'.subjects values(%s,true,true,now()+interval \'20 minutes\')',[value['sub']])
        for spec in SLICES:
            slice_id=spec['id'];checks=[];events=[];owned=[];before_admin=len(admin_events)
            admin.operation=slice_id+'_auth_observer'
            auth_before=admin.execute('select '+STATS+' value').fetchone()['value']
            def ok(name,value):
                if not value:raise AssertionError(slice_id+':'+name)
                checks.append(name)
            for route in ('A','B'):
                member=route.lower();workspace=str(uuid.uuid4());owned.append(workspace)
                admin.operation=slice_id+'_fixture';bind(member)
                state=seed(slice_id,route);raw=json.dumps(state,separators=(',',':'))
                admin.execute('insert into '+SCHEMA+'.workspaces(id,fixture_run,member_id,trainer_id,owner_id,route,expires_at,state_text,state_sha,version) values(%s,%s,%s,%s,%s,%s,now()+interval \'15 minutes\',%s,%s,%s)',
                    [workspace,str(uuid.uuid4()),claims[member]['sub'],claims['trainer']['sub'] if route=='A' else None,
                     claims[member]['sub'],route,raw,digest(raw),state['revision']])
                admin.execute('insert into '+SCHEMA+'.revisions(workspace_id,version,state_text,state_sha) values(%s,%s,%s,%s)',
                    [workspace,state['revision'],raw,digest(raw)])
                historical=slice_id in ('registration12','workout12')
                if historical:
                    store=RegistrationStore(ctx['dsn'],ctx['auth'],{workspace:claims[member]['sub']},enabled=True,
                                            journey=slice_id=='workout12',observer=events.append)
                else:store=Store(ctx['dsn'],ctx['auth'],enabled=True,observer=events.append)
                try:server.Application(store,[workspace],release_slice=slice_id)
                except Denied:ok(route+'_default_off',True)
                else:raise AssertionError('default_off')
                app=server.Application(store,[workspace],enabled=True,release_slice=slice_id)
                http=server.serve(app,0);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
                client=Client('http://127.0.0.1:'+str(http.server_port))
                try:
                    ok(route+'_anonymous_denied',client.call('today')[0]==403)
                    ok(route+'_real_login',client.call('login',ctx['accounts'][member])[0]==200)
                    view,csrf=client.view();initial=copy.deepcopy(view)
                    for action in ('record','finish_day','finish_workout'):
                        ok(route+'_21_off_'+action,client.action(view,csrf,action)[0]==403)
                    neighbor='preferences' if slice_id!='preferences' else 'compare_window'
                    ok(route+'_neighbor_denied',client.action(view,csrf,neighbor)[0]==403)
                    ok(route+'_browser_selector_denied',client.action(view,csrf,neighbor,extra={'release_slice':'preferences'})[0]==403)
                    ok(route+'_denial_no_version_change',client.view()[0]['version']==view['version'])
                    def act(name,data=None,key=None):
                        v,c=client.view();status,result=client.action(v,c,name,data,key)
                        ok(route+'_action_'+name,status==200)
                        return v,result
                    if route=='A' and slice_id in ('intake15','plans16_17'):
                        action='build' if slice_id=='intake15' else 'edit'
                        ok('A_frozen_scope_denied',client.action(view,csrf,action)[0]==403)
                    else:
                        if historical:
                            if slice_id=='workout12':
                                ok(route+'_start_required',client.action(view,csrf,'register12',{'input':view['state']['draft']})[0]==403)
                                act('start12')
                            draft=client.view()[0]['state']['draft'];draft['sets'][0]['rir']=0;draft['sets'][0]['rpe']=None
                            key=str(uuid.uuid4());before,receipt=act('register12',{'input':draft},key)
                            ok(route+'_same_request_replay',client.action(before,csrf,'register12',{'input':draft},key)[1].get('idempotent') is True)
                            ok(route+'_stale_denied',client.action(before,csrf,'register12',{'input':draft})[0]==403)
                            changed=client.view()[0]['state']['draft'];changed['sets'][0]['reps']=3
                            act('register12',{'input':changed})
                            current=client.view()[0]['state']
                            ok(route+'_two_registration_versions',len(current['registrations'])==2)
                            ok(route+'_null_zero',current['registrations'][0]['sets'][0]['rir']==0 and current['registrations'][0]['sets'][0]['rpe'] is None)
                            ok(route+'_snapshot_unchanged',current['snapshot']==initial['state']['snapshot'])
                            if slice_id=='workout12':
                                act('finish12');current=client.view()[0]
                                ok(route+'_explicit_finish',current['state']['session12']['status']=='finished')
                                ok(route+'_no_double_finish',client.action(current,csrf,'finish12')[0]==403)
                        elif slice_id=='signals13_14':
                            bundle=view['state']['comparisonExample'];act('compare_window',{'bundle':bundle})
                            saved=client.view()[0];act('compare_window',{'bundle':bundle})
                            ok(route+'_dedup',client.view()[0]['version']==saved['version'])
                            bad=copy.deepcopy(bundle);bad['rows'].pop()
                            ok(route+'_missing_window_denied',client.action(saved,csrf,'compare_window',{'bundle':bad})[0]==403)
                        elif slice_id=='intake15':
                            pair=view['state']['pair'];act('intake',{'training':pair['training']['fixture']['intake'],'nutrition':pair['nutrition']['fixture']['intake']})
                            act('build');current=client.view()[0]
                            ok('B_proposal_not_applied',current['state']['review'] is not None and current['state']['active']['version']==1)
                            ok('B_apply_other_slice_denied',client.action(current,csrf,'apply')[0]==403)
                        elif slice_id=='plans16_17':
                            act('edit',{'domain':'nutrition_portion','value':{'meal':0,'item':0,'grams':225}})
                            current=client.view()[0]
                            ok('B_edit_not_applied',current['state']['active']==initial['state']['active'] and current['state']['review'] is not None)
                            ok('B_time_edit_other_slice_denied',client.action(current,csrf,'edit',{'domain':'time','value':'20:00'})[0]==403)
                        elif slice_id=='review18':
                            def approve_apply():
                                current,c=client.view();ok(route+'_separate_confirmation',client.action(current,c,'apply')[0]==403)
                                act('confirm')
                                if route=='A':
                                    current,c=client.view();ok('A_trainer_required',client.action(current,c,'apply')[0]==403)
                                    trainer=Client(client.url);ok('A_trainer_login',trainer.call('login',ctx['accounts']['trainer'])[0]==200)
                                    tv,tc=trainer.view();ok('A_minimal_trainer_view','recovery' not in tv['state'] and 'pair' not in tv['state'])
                                    ok('A_approve',trainer.action(tv,tc,'approve')[0]==200);ok('A_trainer_logout',trainer.call('logout',{},tc)[0]==200)
                                key=str(uuid.uuid4());previous,result=act('apply',key=key)
                                ok(route+'_double_apply_one_version',client.action(previous,c,'apply',key=key)[1].get('idempotent') is True)
                            approve_apply();act('restore',{'version':3});approve_apply()
                            ok(route+'_restore_new_version',client.view()[0]['state']['active']['version']==5)
                            ok(route+'_previous_versions_preserved',len(client.view()[0]['state']['history'])==5)
                        elif slice_id=='recovery19_today20':
                            row=view['state']['recovery']['rows'][-1]
                            act('recovery',{'id':row['id'],'version':row['version'],'value':6})
                            current=client.view()[0];ok(route+'_source_bound_notice',len(current['notices'])>0)
                            pending=next(x for x in current['notices'] if x['status']=='pending')
                            act('notice_seen',{'id':pending['id']})
                            ok(route+'_notice_saved',any(x['status']=='seen' for x in client.view()[0]['notices']))
                        else:
                            act('preferences',{**view['state']['preferences'],'language':'de','theme':'dark','units':'imperial'})
                            ok(route+'_original_units_preserved',client.view()[0]['state']['active']==view['state']['active'])
                        saved=client.view()[0]
                        ok(route+'_logout',client.call('logout',{},csrf)[0]==200)
                        ok(route+'_no_session_access',client.call('today')[0]==403)
                        ok(route+'_relogin',client.call('login',ctx['accounts'][member])[0]==200)
                        fresh,csrf=client.view();ok(route+'_durable_relogin',fresh==saved)
                        act('revoke');current=client.view()[0]
                        action='register12' if historical else 'preferences' if slice_id=='preferences' else 'confirm' if slice_id=='review18' else spec['actions']['member'][0]
                        ok(route+'_revoked_denied',client.action(current,csrf,action)[0]==403)
                    ok(route+'_logout_final',client.call('logout',{},csrf)[0]==200)
                finally:http.shutdown();http.server_close();thread.join(timeout=5)
            admin.operation=slice_id+'_cleanup';bind('a');request=str(uuid.uuid4())
            admin.execute("select set_config('fmz6e.request_id',%s,false)",[request]);counts={}
            with admin.transaction():
                for table in ('outbox','requests','revisions','workspaces'):
                    key='id' if table=='workspaces' else 'workspace_id'
                    counts[SCHEMA+'.'+table]=len(admin.execute('delete from '+SCHEMA+'.'+table+' where '+key+'=any(%s::uuid[]) returning '+key,[owned]).fetchall())
            deletes=admin.execute('select table_name,operation,key_sha,xid from '+SCHEMA+'.audit where request_id=%s order by id',[request]).fetchall()
            ok('all_exact_deletes_visible',dict(collections.Counter(x['table_name'] for x in deletes))=={k:v for k,v in counts.items() if v} and all(x['operation']=='DELETE' and len(x['key_sha'])==64 for x in deletes) and len({x['xid'] for x in deletes})==1)
            ok('selected_fixtures_gone',admin.execute('select count(*) n from '+SCHEMA+'.workspaces where id=any(%s::uuid[])',[owned]).fetchone()['n']==0)
            auth_after=admin.execute('select '+STATS+' value').fetchone()['value']
            completed=[e for e in events if e['phase']=='completed'];native_admin=[e for e in admin_events[before_admin:] if e['phase']=='completed']
            receipt={'slice':slice_id,'status':'PASS_LOCAL_HTTP_AUTH_PG','checks':len(checks),'cases':checks,
                'native_runtime_commands':len(completed),'native_admin_commands':len(native_admin),'managed_auth':difference(auth_before,auth_after),
                'runtime_register':completed,'admin_register':native_admin,'delete_counts':counts,'delete_evidence':deletes,
                'migration_installation':'shared independently measured M45/M46; not repeated eight times',
                'hosted_admission':False,'owner_accepted':False,'full_day21':False}
            save('release-matrix-'+slice_id+'.json',receipt);rows.append({k:v for k,v in receipt.items() if k not in ('runtime_register','admin_register','delete_evidence','cases')})
        admin.operation='release_matrix_subject_cleanup';admin.execute('delete from '+SCHEMA+'.subjects where user_id=any(%s::uuid[])',[[c['sub'] for c in claims.values()]])
        result={'status':'EIGHT_SELECTED_LOCAL_PASS','slices':rows,'checks':sum(x['checks'] for x in rows),
                'hosted':False,'physical_owner_test':False,'shared_admin_register':[x for x in admin_events if x['phase']=='completed']}
        save('release-matrix.json',result);return result
    finally:admin.observer=original
