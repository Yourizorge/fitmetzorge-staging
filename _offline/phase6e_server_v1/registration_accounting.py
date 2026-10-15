"""Executed local release12 transport register, never hosted budget permission."""
import collections,hashlib,json

def build(read,names):
    prefix='registration12-transport-'
    admin=read(prefix+'integration-native-admin-protocol.json')
    managed=read(prefix+'integration-managed-auth-protocol.json')
    if admin['synthetic_roles']!=['a','trainer','b']:raise ValueError('release_three_identities')
    rows=[]
    def add(phase,event):
        if event.get('confirmed') is not True:raise ValueError('release_incomplete_command')
        rows.append({'id':len(rows)+1,'phase':phase,'commands':1,'template_sha256':event['template_sha256'],
                     'call_id':event['call_id'],'ordinal':event['ordinal'],'duration_ms':event['duration_ms']})
    for event in admin['register']:add(event['operation'],event)
    for role in ('a','b'):
        proof=read(prefix+'database-'+role+'.json')
        if proof['route']!=role.upper() or proof['transport']!='private_candidate_actual_local_GoTrue_and_verified_TLS':raise ValueError('release_transport_missing')
        if len(proof['register'])!=proof['commands']:raise ValueError('release_register_count')
        for event in proof['register']:add(event['operation']+'_'+role,event)
    native=len(rows)
    for query in managed['statements']:
        if query['temp_written'] or query['calls']<0:raise ValueError('release_auth_load')
        rows.append({'id':len(rows)+1,'phase':'managed_auth','commands':query['calls'],
                     'queryid':query['queryid'],'exec_ms':query['exec_ms'],'temp_written':query['temp_written']})
    if sum(r['commands'] for r in rows if r['phase']=='managed_auth')!=managed['commands']:raise ValueError('release_auth_count')
    pairs=[]
    for name in sorted(names):
        if not name.startswith(prefix+'pair-') or not name.endswith('-validated.json'):continue
        pair=read(name);start=name[:-len('-validated.json')]
        before,after=read(start+'-before.json'),read(start+'-after.json')
        if not pair['complete'] or before['binding']!=after['binding'] or before['binding']!=pair['binding']:raise ValueError('release_pair_binding')
        if pair['expected_count']!=len(pair['writes']):raise ValueError('release_pair_write_count')
        pairs.append({'file':name,'binding':pair['binding'],'expected_writes':pair['expected_count'],
                      'actual_writes':len(pair['writes']),'error_class':pair['error_class']})
    if not pairs or not any(p['expected_writes']==0 for p in pairs) or not any(p['expected_writes']==3 for p in pairs):raise ValueError('release_pair_coverage')
    phases=collections.Counter()
    for row in rows:phases[row['phase']]+=row['commands']
    # Observed successful suffix, not a claim about future hosted guard costs.
    cleanup=sum(n for phase,n in phases.items() if phase.startswith('registration12_cleanup_'))
    closure=phases['numeric_final_observers']+phases['revocation_session_check']
    return {'status':'LOCAL_TRANSPORT_LIFECYCLE_MEASURED','rows':rows,'phase_commands':dict(phases),
            'native_commands':native,'managed_auth_commands':managed['commands'],
            'observed_commands':sum(r['commands'] for r in rows),'cleanup_sql_observed':cleanup,
            'closing_sql_observed':closure,'pairs':pairs,'pair_count':len(pairs),
            'register_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'hosted_authorized':False,'hosted_maximum':None,
            'remaining_hosted_binding':['accepted11 outcome and physical review','exact registered hosted identities and new workspaces',
              'temporary guard/Auth issuance lifecycle from accepted11','selected migration and complete hosted register admission'],
            'no_old_budget_imported':True,'rollback':'disable selected entry; revoke exact sessions; retain historical revisions/audit'}
