"""Archive the one stopped run without altering or promoting its evidence."""
import hashlib,json,os,pathlib,re

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUN='32321f17-07f1-4f3d-aa4b-3218bc7368a4'
FILES=('preregistration.json','source-admission.json','inspection.json',
       'auth-policy.json','auth-version.json','integral-preflight.json',
       'integral-preservation-before-stop.json','registered-worker-stop-001.json',
       'registered-worker-terminal.json','result.json','closed.json',
       'enable-readiness.json','lease-confirmed.json')

def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    source=ROOT/'supabase/.temp'/('phase6e11-reserved-hosted-'+RUN)
    values={n:disk(source/n).read_bytes() for n in FILES}
    read=lambda n:json.loads(values[n])
    result=read('result.json');pre=read('integral-preflight.json');closed=read('closed.json')
    if result['status']!='NO_GO' or len(pre['migrations'])!=43 or closed['remaining_mappings']!=0 or not closed['confirmed']:
        raise ValueError('different_stop_requires_review')
    target=disk(HERE/'receipts'/('hosted-stop-'+RUN))
    for raw in values.values():
        if re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.',raw):
            raise ValueError('receipt_secret_pattern')
    target.mkdir(exist_ok=False)
    for name,raw in values.items():
        with (target/name).open('xb') as f:f.write(raw)
    manifest={'run_id':RUN,'status':'NO_GO','historical_evidence_unchanged':True,
        'source_head':read('preregistration.json')['head'],'ci_run':read('preregistration.json')['ci_run'],
        'files':{n:sha(v) for n,v in values.items()},
        'scope':'Stopped during initial read-only DECLARE attribution; no migration/Auth/workflow action reached',
        'complete_hosted_chain':False,'full_preservation_pair':False,'active_jit_mappings':0,
        'confirmed_preflight_commands':len(pre['commands']),
        'total_commands_durably_recorded':False,
        'estimated_protocol_from_confirmed_path':13,
        'estimate_is_not_a_complete_protocol_receipt':True,
        'own_and_background_io':'not attributable: utility before/after counters were not saved by this source',
        'hosted_attempt_consumed':True,'automatic_retry_allowed':False,'owner_window_open':False}
    with (target/'MANIFEST.json').open('x',encoding='utf8') as f:json.dump(manifest,f,indent=2,sort_keys=True)
    print(json.dumps({'path':str(target),'files':len(values),'status':'NO_GO','jit_mappings':0}))

if __name__=='__main__':main()
