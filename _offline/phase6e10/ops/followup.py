"""Read-only owner match and aggregate-only preservation snapshots. No remote writes."""
import datetime
import hashlib
import json
import re
import sys
import urllib.error
import close6e9 as c
import investigate as historical

NINE=['entitlements','member_app_preferences','member_notifications','nutrition_preferences',
      'profiles','progress_preferences','user_onboarding','user_settings','workout_sessions']
PRESERVED=['supabase/.temp/phase6e10-before.json','supabase/.temp/phase6e10-data-differences.json',
           '_offline/phase6e10/ops/broker.py','_offline/phase6e10/ops/evidence.cjs',
           'docs/PHASE6E10_READONLY_INVESTIGATION.md','docs/PHASE6E10_READONLY_INVESTIGATION.json']
MUTABLE_PRIVATE={'windows','participants','workspaces','source_versions','source_heads','plans','proposals','audit','requests'}

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def preserved():
    return {f:hashlib.sha256((c.ROOT/f).read_bytes()).hexdigest() for f in PRESERVED}

def owner_match(email):
    if not isinstance(email,str) or '@' not in email: raise RuntimeError('owner_login_address_required')
    rows=historical.logs("""select timestamp,log_attributes['request.method'] method,
log_attributes['request.path'] path,log_attributes['response.status_code'] status,
log_attributes['request.sb.jwt.authorization.payload.subject'] subject,
log_attributes['request.sb.jwt.authorization.payload.session_id'] session,
log_attributes['request.sb.jwt.authorization.payload.role'] role,
log_attributes['request.sb.jwt.apikey.payload.role'] api_role,
log_attributes['request.sb.auth_user'] auth_user,
log_attributes['request.headers.user_agent'] agent,log_attributes['request.headers.referer'] referer
from logs where source='edge_logs' order by timestamp limit 500""")
    subjects={r['subject'] for r in rows if r['subject']}
    sessions={r['session'] for r in rows if r['session']}
    if len(rows)>=500 or len(subjects)!=1 or len(sessions)!=1: raise RuntimeError('ambiguous_log_identity')
    uid=next(iter(subjects)); sid=next(iter(sessions))
    account=c.query('select email from auth.users where id='+c.lit(uid))
    exact=len(account)==1 and account[0]['email'].casefold()==email.casefold()
    email=None;account=None
    if not exact: raise RuntimeError('owner_account_mismatch')
    session=c.query('select user_id,created_at,(user_agent like '+c.lit('%Mobile%')+') mobile from auth.sessions where id='+c.lit(sid))
    if len(session)!=1 or session[0]['user_id']!=uid or not session[0]['mobile']: raise RuntimeError('owner_session_mismatch')
    if c.query('select 1 from fmz6e10_private.identities where user_id='+c.lit(uid)): raise RuntimeError('owner_is_synthetic')
    authenticated=[r for r in rows if r['role']=='authenticated']
    historical_report=json.loads((c.ROOT/'docs/PHASE6E10_READONLY_INVESTIGATION.json').read_text())
    allowed=set(historical_report['post_or_mutation_paths'])|{'/auth/v1/token'}
    if any(r['role']=='service_role' or r['api_role']=='service_role' or '6e10' in r['path'] for r in rows): raise RuntimeError('unexpected_privileged_request')
    if any(r['auth_user'] and r['auth_user']!=uid for r in rows): raise RuntimeError('second_auth_user')
    if any('Mobile' not in r['agent'] or 'Safari/' not in r['agent'] or 'Chrome/' in r['agent'] or r['session']!=sid for r in authenticated): raise RuntimeError('browser_or_session_mismatch')
    if any(r['method'] in ['POST','PATCH','DELETE','PUT'] and r['path'] not in allowed for r in rows): raise RuntimeError('unexpected_mutating_path')
    if any(r['role'] not in ['', 'authenticated'] for r in rows): raise RuntimeError('unexpected_role')
    updates=[]
    for table in NINE:
        owner='id' if table=='profiles' else 'user_id'
        r=c.query('select '+c.lit(table)+' table_name,count(*) changed_rows,bool_and('+owner+'='+c.lit(uid)+') all_owner,min(updated_at) first_update,max(updated_at) last_update from public.'+table+' where updated_at>'+c.lit(historical.BASELINE)+' and '+owner+' not in(select user_id from fmz6e10_private.identities)')[0]
        if r['changed_rows']!=1 or r['all_owner'] is not True: raise RuntimeError('row_owner_mismatch')
        old=next(x for x in historical_report['updated_row_metadata'] if x['table_name']==table)
        if r['first_update']!=old['first_update'] or r['last_update']!=old['last_update']: raise RuntimeError('new_unexplained_owner_update')
        updates.append(r)
    audit=historical.logs("select log_attributes['auth_audit_event.action'] action,log_attributes['auth_audit_event.actor_id'] actor from logs where source='auth_audit_logs' limit 100")
    if len(audit)!=1 or audit[0]['actor']!=uid or audit[0]['action']!='login': raise RuntimeError('unexpected_auth_event')
    methods=historical.logs("select log_attributes['grant_type'] grant_type,log_attributes['status'] status from logs where source='auth_logs' and log_attributes['path']='/token' limit 30")
    if len(methods)!=1 or methods[0]['grant_type']!='password' or methods[0]['status']!='200': raise RuntimeError('unexpected_login_method')
    background=historical.logs("""select source,multiIf(positionCaseInsensitive(event_message,'checkpoint')>0,'checkpoint',positionCaseInsensitive(event_message,'cron job')>0,'cron_job',positionCaseInsensitive(event_message,'Warp server error: Thread killed by timeout manager')>0,'transport_timeout','unexpected') category,count() count from logs where source in ('postgres_logs','postgrest_logs') group by source,category""")
    if any(r['category']=='unexpected' for r in background): raise RuntimeError('unexpected_background_log')
    cron=c.query("select jobid,status,count(*) runs from cron.job_run_details where start_time>='2026-09-16T06:50:00Z' and start_time<'2026-09-16T07:00:00Z' group by jobid,status order by jobid")
    if len(cron)!=2 or any(r['jobid'] not in [1,7] or r['status']!='succeeded' or r['runs']!=10 for r in cron): raise RuntimeError('unexpected_cron_history')
    receipt=json.loads((c.ROOT/'supabase/.temp/phase6e9-owner-window.json').read_text())
    original=json.loads((c.ROOT/'supabase/.temp/phase6e10-before.json').read_text())
    old={r['name']:r for r in original['tables']}
    for d in json.loads((c.ROOT/'supabase/.temp/phase6e10-data-differences.json').read_text()): old[d['name']]=d['after']
    current=c.fingerprint(receipt)
    if {r['name']:r for r in current}!=old: raise RuntimeError('new_unexplained_fingerprint')
    out={'pass':True,'checked_at':now(),'owner_attestation':'Owner confirmed personal mobile Safari use and independently supplied the exact login address.',
         'owner_account_exact_match':exact,'unique_subjects':1,'unique_sessions':1,'session_created_at':session[0]['created_at'],
         'requests':len(rows),'authenticated_requests':len(authenticated),'second_identity':False,'service_role_requests':0,'phase6e10_requests':0,
         'all_nine_rows_same_owner':True,'updates':updates,'background':background,'cron':cron,
         'original_tables':68,'initial_unchanged':59,'initial_explained_differences':9,'new_unexplained_differences':0,
         'reconciled_fingerprints':current,'preserved_files':preserved(),'secrets_exported':False,
         'limitations':['Bounded recorded logs, not a universal proof against credential compromise.',
                       'Owner attestation plus exact account/session/row binding, not browser metadata alone.',
                       'Five transport-timeout records remain documented; they are not counted as authorization denials.']}
    dest=c.ROOT/'docs/PHASE6E10_OWNER_MATCH.json'
    with dest.open('x') as f: json.dump(out,f,indent=2);f.write('\n')
    return {k:out[k] for k in ['pass','owner_account_exact_match','unique_subjects','unique_sessions','all_nine_rows_same_owner','new_unexplained_differences']}

def snapshot():
    match=json.loads((c.ROOT/'docs/PHASE6E10_OWNER_MATCH.json').read_text())
    if not match['pass'] or preserved()!=match['preserved_files']: raise RuntimeError('preserved_evidence_changed')
    ids=c.query('select user_id,role from fmz6e10_private.identities order by role')
    if len(ids)!=3: raise RuntimeError('identity_registry_changed')
    id_sql=','.join(c.lit(r['user_id']) for r in ids)
    inventory=c.query("select schemaname,tablename from pg_tables where schemaname not in ('pg_catalog','information_schema') order by schemaname,tablename")
    columns=c.query("select table_schema,table_name,column_name from information_schema.columns where table_schema='auth'")
    parts=[]
    for t in inventory:
        schema,table=t['schemaname'],t['tablename'];name=schema+'.'+table
        if not re.fullmatch(r'[a-zA-Z0-9_.]+',name): raise RuntimeError('unexpected_identifier')
        qname='"'+schema+'"."'+table+'"'
        keep='true'
        if name=='public.profiles': keep='id not in('+id_sql+')'
        if schema=='fmz6e10_private' and table in MUTABLE_PRIVATE: keep='false'
        if name=='cron.job_run_details': keep='false'
        if schema=='auth':
            cs={r['column_name'] for r in columns if r['table_name']==table}
            if table=='users': keep='id not in('+id_sql+')'
            elif 'user_id' in cs: keep='user_id is null or user_id::text not in('+id_sql+')'
            elif table=='mfa_amr_claims': keep='session_id not in(select id from auth.sessions where user_id in('+id_sql+'))'
        digest="encode(sha256(convert_to(coalesce(string_agg(h,',' order by h){filter},''),'UTF8')),'hex')"
        parts.append('select '+c.lit(name)+' name,count(*)::int rows,'+digest.format(filter='')+' sha256,count(*) filter(where keep)::int protected_rows,'+digest.format(filter=' filter(where keep)')+' protected_sha256 from(select encode(sha256(convert_to(to_jsonb(t)::text,\'UTF8\')),\'hex\') h,('+keep+') keep from '+qname+' t) q')
    measured=now()
    tables=c.query(' union all '.join(parts))
    audit=c.query("select a.id,coalesce(i.role,'UNKNOWN') actor,a.action,a.at from fmz6e10_private.audit a left join fmz6e10_private.identities i on i.user_id=a.actor order by a.id")
    if any(r['actor']=='UNKNOWN' for r in audit): raise RuntimeError('unknown_audit_actor')
    cron=c.query("select jobid,status,count(*) rows,max(start_time) latest_start from cron.job_run_details group by jobid,status order by jobid,status")
    state=c.query("select (select count(*) from fmz6e10_private.windows where status='active' and ends_at>clock_timestamp()) active_windows,(select count(*) from fmz6e10_private.workspaces) workspaces,(select count(*) from auth.users where email like '6e10-%@example.invalid') temporary_controls")
    return {'at':measured,'tables':tables,'nine':[r for r in tables if r['name'] in ['public.'+t for t in NINE]],
            'audit':audit,'cron':cron,'state':state,'preserved_files':preserved()}

for line in sys.stdin:
    try:
        d=json.loads(line)
        if d['op']=='owner_match': result=owner_match(d.get('email'))
        elif d['op']=='snapshot': result=snapshot()
        else: raise RuntimeError('unknown_readonly_operation')
        print(json.dumps({'ok':True,'result':result}),flush=True)
    except Exception as e:
        error=str(e) if isinstance(e,RuntimeError) else 'readonly_followup_'+type(e).__name__
        if isinstance(e,urllib.error.HTTPError): error+='_'+str(e.code)
        print(json.dumps({'ok':False,'error':error}),flush=True)
