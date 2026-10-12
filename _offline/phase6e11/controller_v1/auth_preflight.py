"""Read-only synthetic identity, Auth policy and trigger admission; no Auth calls."""
import hashlib,json,pathlib,re,sys,uuid
import jit_diagnose as j
m=j.m


def identifiers():
    value=json.loads((m.ROOT/'supabase/.temp/phase6e9-owner-window.json').read_text())
    names={'memberA':'a_member','trainerA':'a_trainer','memberB':'b_member'}
    rows=value['accounts']
    if len(rows)!=3 or {r['name'] for r in rows}!=set(names):raise m.Stop('registered_identity_shape')
    ids={names[r['name']]:r['id'] for r in rows}
    if len(set(ids.values()))!=3 or any(str(uuid.UUID(v))!=v for v in ids.values()):raise m.Stop('registered_identity_shape')
    return ids


def settings(value):
    fields=['sessions_single_per_user','sessions_timebox','sessions_inactivity_timeout',
        'hook_custom_access_token_enabled','hook_before_user_created_enabled',
        'hook_password_verification_attempt_enabled','hook_mfa_verification_attempt_enabled',
        'refresh_token_rotation_enabled','security_refresh_token_reuse_interval',
        'mailer_autoconfirm','external_email_enabled','disable_signup']
    out={}
    for k in fields:
        v=value.get(k)
        if v is None or type(v) in (bool,int):out[k]=v
        elif isinstance(v,str) and re.fullmatch(r'[0-9]+(?:h|m|s)?',v):out[k]=v
        else:out[k]='unrecognized_format'
    return out


def query(ids):
    entries=','.join("('"+role+"','"+ids[role]+"'::uuid,'zorgeyouri+6e9-"+alias+"@gmail.com')"
        for role,alias in [('a_member','a-lid'),('a_trainer','a-trainer'),('b_member','b-lid')])
    return m.TAG+"""with expected(role,id,email) as (values """+entries+""")
select jsonb_build_object(
 'identities',(select jsonb_agg(jsonb_build_object('role',e.role,
 'id_matches',i.user_id=e.id,'registered_role_matches',i.role=e.role,'enabled',i.enabled,
 'auth_present',u.id is not null,'email_matches',u.email=e.email,'confirmed',u.email_confirmed_at is not null,
 'profile_matches',p.role=case when e.role='a_trainer' then 'trainer' else 'client' end and p.email=e.email,
 'trainer_matches',case when e.role='a_member' then p.trainer_id=(select id from expected where role='a_trainer') else p.trainer_id is null end,
 'operator_matches',case when e.role='a_trainer' then o.enabled else o.user_id is null end))
 from expected e left join fmz6e11_private.identities i on i.user_id=e.id
 left join auth.users u on u.id=e.id left join public.profiles p on p.id=e.id
 left join fmz6e11_private.operators o on o.user_id=e.id),
 'app_config',(select jsonb_build_object('enabled',enabled,'proof_present',proof_hash is not null) from fmz6e11_private.config where id),
 'bridge',(select jsonb_build_object('enabled',enabled,'unexpired',expires_at>clock_timestamp()) from fmz6e11_request_private.control where id),
 'windows',(select jsonb_build_object('total',count(*),'live',count(*) filter(where fmz6e11_private.live_window(w))) from fmz6e11_private.windows w),
 'incomplete_requests',(select count(*) from fmz6e11_request_private.receipts where state<>'pair_validated'),
 'triggers',(select coalesce(jsonb_agg(jsonb_build_object('name',t.tgname,'table',c.relname,'type',t.tgtype,
 'enabled',t.tgenabled,'function_schema',pn.nspname,'function_name',p.proname,
 'function_sha256',encode(sha256(convert_to(p.prosrc,'UTF8')),'hex'))),'[]')
 from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace
 join pg_proc p on p.oid=t.tgfoid join pg_namespace pn on pn.oid=p.pronamespace
 where n.nspname='auth' and not t.tgisinternal),
 'managed_audit_observers',(select count(*) from fmz6e11_audit_private.relations where table_name ~ '^(auth|storage|realtime)\\.'),
 'history_count',(select count(*) from supabase_migrations.schema_migrations)
)::text"""


def validate(value,config):
    rows=value.get('identities',[])
    if len(rows)!=3 or {r.get('role') for r in rows}!={'a_member','a_trainer','b_member'}:raise m.Stop('identity_count')
    for row in value['identities']:
        if any(row.get(k) is not True for k in ('id_matches','registered_role_matches','enabled','auth_present','email_matches','confirmed','profile_matches','trainer_matches','operator_matches')):
            raise m.Stop('registered_synthetic_identity_unavailable')
    if value['history_count']!=43 or value['incomplete_requests'] or value['managed_audit_observers']:raise m.Stop('server_admission_state')
    if value['windows']['live']:raise m.Stop('existing_live_window')
    if config.get('sessions_single_per_user') is not False:raise m.Stop('existing_sessions_not_protected_by_policy')
    if any(v is not False for k,v in config.items() if k.startswith('hook_')):raise m.Stop('unreviewed_auth_hook')
    return True


def main():
    ids=identifiers();folder=m.ROOT/'supabase/.temp'/('phase6e11-controller-auth-readonly-'+uuid.uuid4().hex);folder.mkdir()
    m.save(m.ROOT/'supabase/.temp/phase6e11-controller-auth-preflight-20261012-once.json',{'folder':folder.name})
    sql=query(ids)
    m.save(folder/'contract.json',{'database_writes':0,'auth_calls':0,'maximum_commands':4,
        'maximum_connections':1,'retries':0,'sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),
        'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()})
    journal=db=tx=ledger=None;started=False
    result={'status':'NO_GO','folder':folder.name,'phase':'preflight','auth_calls':0,'database_writes':0}
    try:
        token=m.p.jit.sb.credential();journal=j.Journal(token,folder);result['phase']='management_inspection';journal.inspect()
        result['phase']='auth_policy'
        config=settings(journal.request('auth_policy',j.BASE+'/config/auth'))
        m.save(folder/'auth-settings.json',config)
        result['phase']='jit_lease';started=True;journal.grant()
        result['phase']='database_connection'
        db=m.c.Connection(json.loads((m.c.CONNECT/'connect.json').read_text()),token,m.c.CA)
        ledger=m.Ledger(folder/'ledger');s=m.stream.t.old.s
        tx=s.Transaction(db,folder,ledger)
        result['phase']='explicit_readonly'
        tx.command(s.BEGIN,'begin');tx.transaction=s.identity(tx.command(s.CHECK,'read_only_check'))
        m.save(folder/'transaction-confirmed.json',tx.transaction)
        result['phase']='synthetic_auth_inventory'
        value=json.loads(tx.command(sql,'synthetic_auth_inventory')[0][0]);m.save(folder/'inventory.json',value)
        result['phase']='admission_validation'
        validate(value,config)
        result['status']='SYNTHETIC_AUTH_READONLY_PREFLIGHT_PASS'
    except j.Rejected as error:result.update(phase=error.phase,reason=error.code)
    except Exception as error:result['reason']=str(error) if isinstance(error,m.Stop) else type(error).__name__
    finally:
        if tx:
            result['rollback']=tx.rollback()['confirmed']
            if not result['rollback']:result['status']='NO_GO'
        if db:result['commands']=db.queries;db.close()
        if ledger:ledger.close()
        if started:
            try:journal.close();result['jit_revoked']=True
            except Exception:result.update(status='NO_GO',jit_revoked=False)
        if journal:journal.token=None
        token=None;m.save(folder/'result.json',result)
    print(json.dumps(result));return 0 if result['status']=='SYNTHETIC_AUTH_READONLY_PREFLIGHT_PASS' else 2


if __name__=='__main__':sys.exit(main())
