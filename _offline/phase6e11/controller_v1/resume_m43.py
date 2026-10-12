"""New owner-authorized admission; old attempts and tested M43 remain immutable."""
import json
import pathlib
import sys
import uuid
import jit_diagnose as j
m=j.m


def perform(token,connect,folder,parent,capture=m.capture,cli=None):
    if cli is None:cli=lambda dry:m.prior.old.prior.cli_run(m.prior.old.CLI,connect,m.c.CA,token,dry)
    result={'status':'NO_GO','migration_applied':False,'phase':'before'}
    try:
        before=capture(connect,token,folder/'before',parent)
        if before['status']!='complete' or before['history_count']!=42:raise m.Stop('before_'+before.get('reason','history'))
        parent.event('before_saved',identity_sha256=m.digest(before))
        result['phase']='dry_run_before'
        dry=cli(True);m.save(folder/'cli-dryrun-before.json',dry)
        if dry['exit_code'] or dry.get('migration_files')!=[m.M43]:raise m.Stop('unexpected_pending_migrations')
        result['phase']='migration'
        parent.event('action_started',migration_sha256=m.c.sha(m.ROOT/'supabase/migrations'/m.M43))
        applied=cli(False);m.save(folder/'cli-apply.json',applied)
        result['migration_applied']=applied['exit_code']==0
        parent.event('action_confirmed',receipt_sha256=m.digest(applied))
        # Even a reported migration failure requires its direct after-measurement.
        result['phase']='after'
        after=capture(connect,token,folder/'after',parent,[x['name'] for x in before['tables']],before['bindings'])
        if after['status']!='complete':raise m.Stop('after_'+after.get('reason','incomplete'))
        parent.event('after_saved',identity_sha256=m.digest(after))
        if after['history_count']!=43 or applied['exit_code'] or applied.get('migration_files')!=[m.M43]:raise m.Stop('migration_identity')
        pair=m.compare(before,after);m.save(folder/'pair.json',pair)
        parent.event('pair_validated',receipt_sha256=m.digest(pair))
        load=m.prior.old.cli_load(before['cli_numeric'],after['cli_numeric']);m.save(folder/'cli-load.json',load)
        result['phase']='dry_run_after'
        dry=cli(True);m.save(folder/'cli-dryrun-after.json',dry)
        if dry['exit_code'] or dry.get('migration_files') or not dry.get('up_to_date'):raise m.Stop('dryrun_not_empty')
        parent.event('next_step_allowed')
        result.update(status='M43_PAIRED_PASS_CONTROLLER_PENDING',preservation=pair,dry_run_empty=True)
    except Exception as error:
        result['reason']=str(error) if isinstance(error,m.Stop) else type(error).__name__
    return result


def admission():
    tested=m.admitted()
    phase=m.ROOT/'supabase/.temp/phase6e11-jit-diagnose-43102a04057b4bffab2dcbf1cf93907e'
    ready=json.loads((phase/'enable-readiness.json').read_text())
    closed=json.loads((phase/'closed.json').read_text())
    if not all(ready.values()) or not closed['confirmed']:raise m.Stop('jit_phase_proof_missing')
    for n in ('06-enable-result.json','07-enable_applied-result.json','08-role_grant-result.json','09-mapping_confirm-result.json'):
        if json.loads((phase/n).read_text())['http_status']!=200:raise m.Stop('jit_phase_failed')
    local=pathlib.Path('C:/Users/Fitme/AppData/Local/Temp/fmz-fingerprint-offline-mh3klj58/metadata-result.json')
    if json.loads(local.read_text())['status']!='LOCAL_PG17_METADATA_PASS':raise m.Stop('metadata_local_required')
    return {**tested,'jit_phase_folder':phase.name,'jit_readiness_sha256':m.c.sha(phase/'enable-readiness.json'),
        'closed_sha256':m.c.sha(phase/'closed.json'),'local_metadata_sha256':m.c.sha(local),
        'historical_406':'not_reconstructable_without_original_response',
        'historical_show_failure':'retained; local terminal_row_count reproduced; proven SELECT adapter used'}


def main():
    allowed=admission()
    folder=m.ROOT/'supabase/.temp'/('phase6e11-controller-m43-resume-'+uuid.uuid4().hex);folder.mkdir()
    m.save(m.ROOT/'supabase/.temp/phase6e11-controller-m43-resume-20261012-once.json',{'folder':folder.name,'automatic_retry':False})
    m.save(folder/'contract.json',{**allowed,'maximum_commands':296,'per_cycle':128,'cycles':2,
        'cli_reserved_commands':40,'historical_commands_counted':21,'collectors':1,'retries':0,
        'auth_writes':0,'application_writes':0,'scope':'M43 only; not workflow canary',
        'sources':{n:m.c.sha(m.HERE/n) for n in ('resume_m43.py','jit_diagnose.py','install.py','transfer.py')}})
    journal=parent=None;started=False
    result={'status':'NO_GO','migration_applied':False,'phase':'admission','folder':folder.name}
    try:
        class Ledger(m.Ledger):MAX_QUERIES=296
        parent=Ledger(folder/'ledger')
        for _ in range(61):parent.reserve_query()
        token=m.p.jit.sb.credential()
        connect=json.loads((m.c.CONNECT/'connect.json').read_text());m.c.parameters(connect,token,m.c.CA)
        journal=j.Journal(token,folder);journal.inspect()
        started=True;result['phase']='lease';journal.grant()
        result.update(perform(token,connect,folder,parent))
    except j.Rejected as error:result.update(status='NO_GO',phase=error.phase,reason=error.code)
    except Exception as error:result.update(status='NO_GO',reason=str(error) if isinstance(error,m.Stop) else type(error).__name__)
    finally:
        if parent:
            result['commands_including_cli_reservations_and_historical']=parent.queries;parent.close()
        if started:
            try:journal.close();result['jit_revoked']=True
            except Exception as error:result.update(status='NO_GO',jit_revoked=False,close_error=type(error).__name__)
        if journal:journal.token=None
        token=None
        m.save(folder/'result.json',result)
    print(json.dumps(result))
    return 0 if result['status']=='M43_PAIRED_PASS_CONTROLLER_PENDING' else 2


if __name__=='__main__':sys.exit(main())
