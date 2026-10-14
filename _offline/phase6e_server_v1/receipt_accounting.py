"""Account for the existing CLI meter's five admin SQL calls per invocation."""
import re

LABELS=('ci-meter-prefix','ci-meter-role-logging','ci-meter-reload','ci-meter-role-restore')

def meter_controls(manifest,read,invocations=2):
    evidence=[]
    for label in LABELS:
        names=sorted((n for n in manifest if re.fullmatch(r'\d+-'+label+r'\.json',n)),key=lambda n:int(n.split('-')[0]))
        if len(names)<invocations:raise ValueError('meter_control_missing')
        for name in names[:invocations]:
            if read(name)['exitcode']!=0:raise ValueError('meter_control_failed')
            evidence.append({'file':name,'sha256':manifest[name],'commands':1})
    for i in range(invocations):
        name='cli-log-location-'+str(i)+'.json'
        if name not in manifest or set(read(name))!={'collector','destination','directory','file'}:raise ValueError('meter_location_missing')
        evidence.append({'file':name,'sha256':manifest[name],'commands':1})
    return {'phase':'cli_meter_configuration_metadata_and_restore','commands':len(evidence),'evidence':evidence,
        'scope':'source-bound disposable-CI SQL; four psql controls and one metadata SELECT per CLI invocation'}
