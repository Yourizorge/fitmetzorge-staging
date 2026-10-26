"""One-run budget checks, reusable on disposable PG17 and clean Supabase CI."""
import json
from closure import RUN_ID as RUN,PURPOSE,AUTHORIZATION,allowance
CAP=allowance(RUN,PURPOSE)
OTHER='69000000-0000-4000-8000-000000000001'
SCHEMA='fmz6e11_controller_private'
M44='20261012185121_phase6e11_single_endchain_budget.sql'

def insert(run=RUN,count=0,state='running'):
    return ("insert into "+SCHEMA+".runs(id,github_run,head_sha,manifest_sha,expires_at,command_count,state) "
      "values('"+run+"',123,'"+'a'*40+"','"+'b'*64+"',clock_timestamp()+interval '9 minutes',"+
      str(count)+",'"+state+"');")

def run(sql):
    checks=[]
    def case(name,body,denied=None):
        p=sql('begin;'+body+'rollback;')
        if denied is None:
            if p.returncode:raise RuntimeError('budget_database_'+name)
        elif not p.returncode or denied not in p.stderr:
            raise RuntimeError('budget_database_denial_'+name)
        checks.append({'name':name,'pass':True})
    for n in (0,128,129,CAP):case('exact_run_'+str(n),insert(count=n))
    for n in (-1,CAP+1):case('exact_limit_'+str(n),insert(count=n),'runs_command_count_check')
    case('ordinary_128',insert(OTHER,128))
    case('ordinary_129',insert(OTHER,129),'runs_command_count_check')
    for number,old in enumerate([AUTHORIZATION['previous_used_run']]+AUTHORIZATION['earlier_used_runs']):
        old_cap=2237 if old=='1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d' else 128
        case('old_used_run_no_new_allowance_'+str(number),insert(old,old_cap+1),'runs_command_count_check')
        prefix='recovery_run' if old==AUTHORIZATION['previous_used_run'] else 'single_endchain'
        case('old_used_run_retained_'+str(number),insert(old)+"delete from "+SCHEMA+".runs;",prefix+'_receipt_retained')
        denial=prefix+('_receipt_retained' if old==AUTHORIZATION['previous_used_run'] else '_identity_immutable')
        case('old_used_run_cannot_reopen_'+str(number),insert(old,state='stopped')+"update "+SCHEMA+".runs set state='running';",denial)
    for change in ("state='complete'",'command_count=1'):
        case('consumed_receipt_cannot_change_'+str(len(checks)),insert(AUTHORIZATION['previous_used_run'],state='stopped')+
             'update '+SCHEMA+'.runs set '+change+';','recovery_run_receipt_retained')
    for field,value in [('id',"'"+OTHER+"'"),('github_run','124'),('head_sha',"'"+'c'*40+"'"),
                        ('manifest_sha',"'"+'d'*64+"'"),('created_at',"created_at-interval '1 second'"),
                        ('expires_at',"expires_at+interval '1 second'")]:
        case('identity_'+field,insert()+"update "+SCHEMA+".runs set "+field+"="+value+";",
             'recovery_run_identity_immutable')
    case('count_decrease',insert(count=2)+"update "+SCHEMA+".runs set command_count=1;",
         'recovery_run_identity_immutable')
    for state in ('stopped','complete','closed'):
        case('no_restart_'+state,insert(state=state)+"update "+SCHEMA+".runs set state='running';",
             'recovery_run_identity_immutable')
    case('receipt_retained',insert()+"delete from "+SCHEMA+".runs;",'recovery_run_receipt_retained')
    case('ordinary_delete',insert(OTHER)+"delete from "+SCHEMA+".runs;")
    case('ordinary_to_exception',insert(OTHER)+"update "+SCHEMA+".runs set id='"+RUN+"';",
         'recovery_run_identity_immutable')
    case('safe_stop_and_close',insert()+"update "+SCHEMA+".runs set state='stopped',command_count=100;"
         "update "+SCHEMA+".runs set state='closed',command_count=110;")
    case('expiry_cap',insert().replace("interval '9 minutes'","interval '11 minutes'"),'violates check constraint')
    for role in ('anon','authenticated','service_role'):
        for op in ('select * from '+SCHEMA+'.runs','select '+SCHEMA+'.single_endchain_receipt()'):
            case('private_'+role+'_'+str(len(checks)),'set local role '+role+';'+op+';','permission denied')
    p=sql("select jsonb_build_object('functions',count(*),'safe',bool_and(not prosecdef and "
          "proconfig=array['search_path=pg_catalog, pg_temp'])) from pg_proc p join pg_namespace n "
          "on n.oid=p.pronamespace where n.nspname='"+SCHEMA+"';")
    if p.returncode or json.loads(p.stdout.strip())!={'functions':2,'safe':True}:
        raise RuntimeError('budget_function_acl')
    checks.append({'name':'invoker_fixed_path','pass':True})
    p=sql('select count(*) from '+SCHEMA+'.runs;')
    if p.returncode or p.stdout.strip()!='0':raise RuntimeError('local_budget_rows_remain')
    return {'status':'LOCAL_SINGLE_BUDGET_PASS','checks':len(checks),'cases':checks,
            'hosted_calls':0,'test_rows_remaining':0,'ordinary_cap':128,'single_run_cap':CAP}
