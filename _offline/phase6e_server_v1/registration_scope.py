"""Offline release12 boundary compiler. No credential, network or SQL access.

The release gate consumes actual proof references and a complete command register;
it cannot turn a local observation or the old 4135 estimate into authorization.
"""
import copy,datetime,hashlib,json,re,uuid

PROJECT='mokxyyullfhkfalopbzd'
ROLES={'a_member','a_trainer','b_member'}
REQUIRED_PHASES={'identity','migration','baseline','auth','fixtures','registration',
                 'correction','conflict','relogin','cleanup','final','closure'}
REQUIRED_CLOSURE={'rollback','disable_entry','revoke_test_sessions','audit_delete',
                  'protected_terminal','dry_run','jit_revoke'}

def fail(code):raise ValueError(code)
def uid(value):
    try:
        if str(uuid.UUID(value))!=value:fail('release_identity')
    except (ValueError,TypeError,AttributeError):fail('release_identity')
    return value

def sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def instant(value):
    try:
        date=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
        if date.utcoffset()!=datetime.timedelta(0):fail('release_utc_required')
        return date
    except (ValueError,TypeError,AttributeError):fail('release_utc_required')

def compile_scope(identities,workspaces,*,issued_at,expires_at,now,sources,register):
    if set(identities)!=ROLES or len(set(identities.values()))!=3:fail('release_registered_identities')
    for value in identities.values():uid(value)
    if set(workspaces)!={'A','B'} or len(set(workspaces.values()))!=2:fail('release_workspaces')
    for value in workspaces.values():uid(value)
    start,end,current=map(instant,(issued_at,expires_at,now))
    if not start<=current<end or not datetime.timedelta(0)<end-start<=datetime.timedelta(minutes=10):fail('release_expired')
    if not sources or any(not re.fullmatch(r'[0-9a-f]{64}',h) for h in sources.values()):fail('release_sources')
    if not REQUIRED_PHASES<=set(row.get('phase') for row in register):fail('release_incomplete_register')
    if len({row.get('id') for row in register})!=len(register):fail('release_duplicate_action')
    for row in register:
        if type(row.get('commands')) is not int or row['commands']<0 or row.get('retry') is not False:fail('release_cost_or_retry')
        if not re.fullmatch(r'[0-9a-f]{64}',row.get('template_sha256','')):fail('release_unbound_command')
        if row.get('mutation'):
            if not row.get('writeset') or row.get('pair')!=['before_saved','action_confirmed','after_saved','pair_validated']:
                fail('release_write_evidence')
        if not REQUIRED_CLOSURE<=set(row.get('safety',{})):fail('release_missing_closure')
        if any(type(v) is not int or v<0 for v in row['safety'].values()):fail('release_safety_cost')
    prefixes=[];used=0
    for row in register:
        used+=row['commands']
        prefixes.append({'after':row['id'],'used':used,'safety_reserve':sum(row['safety'].values()),
                         'required':used+sum(row['safety'].values())})
    return {'status':'OFFLINE_SCOPE_COMPILED_NOT_ADMITTED','project':PROJECT,'slice':'registration12',
        'issued_at':issued_at,'expires_at':expires_at,'identities':copy.deepcopy(identities),
        'bindings':{workspaces['A']:identities['a_member'],workspaces['B']:identities['b_member']},
        'trainer_write_access':False,'source_hashes':copy.deepcopy(sources),'register':copy.deepcopy(register),
        'prefixes':prefixes,'normal_commands':used,'required_maximum':max(x['required'] for x in prefixes),
        'register_sha256':sha(register),'source_bundle_sha256':sha(sources),
        'flags':{'registration12':False,'combined12_20':False,'day21':False,'real_member_ai':False},
        'rollback':'disable exact entry/subjects; preserve revisions and audit; no migration rewind',
        'hosted_authorized':False}

def admit(scope,proof,*,now,actual_sources,registered_identities):
    # These are private operator inputs, never browser claims or user metadata.
    if scope['project']!=PROJECT or scope['slice']!='registration12':fail('release_project')
    if scope['identities']!=registered_identities:fail('release_identity_changed')
    if not instant(scope['issued_at'])<=instant(now)<instant(scope['expires_at']):fail('release_expired')
    if scope['source_hashes']!=actual_sources or sha(actual_sources)!=scope['source_bundle_sha256']:fail('release_source_changed')
    if sha(scope['register'])!=scope['register_sha256']:fail('release_register_changed')
    for name in ('hosted11_complete','physical_owner_review','selected12_decision','transport_ci_complete',
                 'migration_identity','rights_safe','data_preserved','full_register_ci_complete'):
        if proof.get(name) is not True:fail('release_gate_'+name)
    if proof.get('source_bundle_sha256')!=scope['source_bundle_sha256'] or proof.get('register_sha256')!=scope['register_sha256']:
        fail('release_proof_binding')
    if type(proof.get('approved_sql_limit')) is not int or proof['approved_sql_limit']<scope['required_maximum']:
        fail('release_budget_not_authorized')
    return {'status':'PRIVATE_RELEASE_INPUTS_VALID','automatic_activation':False,
            'scope_sha256':sha(scope),'expires_at':scope['expires_at']}
