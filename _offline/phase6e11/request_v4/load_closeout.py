"""Reconcile an aggregate interval with immutable, individually bounded FETCH proof."""
import hashlib,importlib.util,json,math,pathlib,sys,uuid
spec=importlib.util.spec_from_file_location('request_v4_install',pathlib.Path(__file__).with_name('install.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
from guard import Stop,save

RUN=i.ROOT/'supabase/.temp/phase6e11-m42-be9a04735a66446b82d7503cd0d03831'

def reconcile(before,after,profiles,binding):
    if before['stats_info']!=after['stats_info'] or (before['role_oid'],before['dbid'])!=(after['role_oid'],after['dbid']):
        raise Stop('statistics_reset_or_identity')
    out=[];found=False
    for row in after['statements']:
        previous=i.d.base.one(before,row['queryid'])
        calls=row['calls']-(previous['calls'] if previous else 0)
        if calls<0:raise Stop('counter_regression')
        if not calls:continue
        delta=i.d.base.profile(before,after,row['queryid'],expected_calls=calls)['delta']
        if delta['temp_blks_read'] or delta['temp_blks_written']:raise Stop('query_spill')
        if row['queryid']==binding['queryid']:
            found=True
            if len(profiles)!=calls:raise Stop('missing_or_extra_fetch_profile')
            for profile,frame in profiles:
                if (profile['queryid']!=row['queryid'] or frame['queryid']!=row['queryid']
                    or frame['sql_sha256']!=binding['sql_sha256'] or not profile['acceptable']
                    or profile['delta']['calls']!=1 or profile['delta']['total_exec_time']>2500
                    or profile['delta']['temp_blks_read'] or profile['delta']['temp_blks_written']):
                    raise Stop('fetch_profile_binding_or_load')
            for metric in delta:
                total=sum(p['delta'][metric] for p,f in profiles)
                if not math.isclose(total,delta[metric],rel_tol=1e-10,abs_tol=1e-6):
                    raise Stop('fetch_interval_not_fully_accounted')
            out.append({'queryid':row['queryid'],'calls':calls,'total_ms':delta['total_exec_time'],
                'per_call_max_ms':max(p['delta']['total_exec_time'] for p,f in profiles),
                'proof':'each_call_independently_measured','temp_written':0})
        else:
            if delta['total_exec_time']>5000:raise Stop('unaccounted_aggregate_time')
            out.append({'queryid':row['queryid'],'calls':calls,'total_ms':delta['total_exec_time'],
                'proof':'aggregate_bounds_every_call','temp_written':0})
    if not found:raise Stop('fetch_not_observed')
    return out

def verify():
    read=lambda p:json.loads(p.read_text())
    original=read(RUN/'result.json');before=read(RUN/'before/identity.json');after=read(RUN/'after/identity.json')
    if original.get('reason')!='cli_own_spill_or_statement_time' or not original['jit_revoked']:
        raise Stop('historical_result_changed')
    if before['status']!='complete' or after['status']!='complete' or not before['rollback']['confirmed'] or not after['rollback']['confirmed']:
        raise Stop('measurement_incomplete')
    pair=i.compare(before,after)
    if json.loads(json.dumps(pair))!=read(RUN/'pair.json'):raise Stop('preservation_pair_changed')
    profiles=[(read(p),read(p.with_name(p.name.replace('-profile','-frame'))))
              for p in sorted((RUN/'before').glob('fetch_*-profile.json'))]
    result=reconcile(before['cli_numeric'],after['cli_numeric'],profiles,before['bindings']['fetch'])
    files=[RUN/'result.json',RUN/'pair.json',RUN/'before/identity.json',RUN/'after/identity.json']
    files+=sorted((RUN/'before').glob('fetch_*-profile.json'))+sorted((RUN/'before').glob('fetch_*-frame.json'))
    return {'status':'SAVED_INTERVAL_LOAD_PASS','historical_status_unchanged':'NO_GO',
        'cause':'14 individually bounded FETCH calls were mistaken for one slow CLI statement',
        'profiles':result,'protected_pair':pair,'historical_run':RUN.name,
        'sources':{str(f.relative_to(i.ROOT)):i.c.sha(f) for f in files},
        'validator_sha256':i.c.sha(pathlib.Path(__file__)),'hosted_queries':0,'reapplied_migration':False}

if __name__=='__main__':
    result=verify();folder=i.ROOT/'supabase/.temp'/('phase6e11-m42-load-closeout-'+uuid.uuid4().hex);folder.mkdir()
    save(folder/'result.json',result)
    print(json.dumps({'folder':str(folder),'status':result['status'],'queries':0,
        'fetch':next(x for x in result['profiles'] if x['proof']=='each_call_independently_measured')}))
