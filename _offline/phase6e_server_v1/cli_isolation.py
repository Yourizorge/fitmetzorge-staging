"""Quiesce only disposable-CI cron jobs around measured CLI invocations."""
import json,os,sys

SETTING="select current_setting('cron.launch_active_jobs') setting"
ACTIVE="select count(*) n from pg_stat_activity where application_name='pg_cron' and state='active'"

def measured(gate,args,timeout,meter):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':raise RuntimeError('ci_only')
    trace=[];original=None;changed=False;restored=False;index=len(getattr(gate,'cli_protocol',[]))
    def sql(text,rows=False):
        item={'statement':text,'confirmed':False};trace.append(item)
        result=gate.rows(text) if rows else gate.sql(text)
        item['confirmed']=True
        return result
    try:
        original=sql(SETTING,True)[0]['setting']
        if original not in ('on','off'):raise RuntimeError('cron_setting')
        if original=='on':
            changed=True
            sql("alter system set cron.launch_active_jobs='off'")
            sql('select pg_reload_conf()')
        if sql(SETTING,True)!=[{'setting':'off'}] or sql(ACTIVE,True)!=[{'n':0}]:raise RuntimeError('ci_not_quiet')
        result=meter(gate,args,timeout)
        receipt=gate.cli_protocol[-1]
        if not receipt['complete'] or not receipt['numeric_protocol_coverage']:raise RuntimeError('cli_incomplete_evidence')
        return result
    finally:
        primary=sys.exception()
        try:
            if changed:
                sql("alter system set cron.launch_active_jobs='on'")
                sql('select pg_reload_conf()')
            if original is not None:
                restored=sql(SETTING,True)==[{'setting':original}]
                if not restored:raise RuntimeError('cron_restore')
        except Exception as error:
            if primary is None:raise
            primary.add_note('secondary_cron_restore:'+type(error).__name__)
        finally:
            gate.save('cli-isolation-'+str(index)+'.json',{'scope':'disposable CI only; no hosted config changes',
                'original':original,'restored':restored,'commands':len(trace),'protocol':trace,
                'primary_error_class':type(primary).__name__ if primary else None})
