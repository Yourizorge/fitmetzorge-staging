"""CI-only OIDC caller: no Supabase secret; one invocation, no raw error logging."""
import json,os,sys,time,urllib.request,urllib.error
URL='https://mokxyyullfhkfalopbzd.supabase.co/functions/v1/fmz-phase6e11-proof'
AUD='fmz6e11-mokxyyullfhkfalopbzd-proof'
def main():
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging' or os.environ.get('GITHUB_REF')!='refs/heads/main':raise RuntimeError('scope')
    # One bounded deployment handoff, not a retry/polling loop.
    time.sleep(120)
    request=urllib.request.Request(os.environ['ACTIONS_ID_TOKEN_REQUEST_URL']+'&audience='+AUD,
      headers={'Authorization':'Bearer '+os.environ['ACTIONS_ID_TOKEN_REQUEST_TOKEN']})
    with urllib.request.urlopen(request,timeout=10) as r:token=json.load(r)['value']
    request=urllib.request.Request(URL,data=b'{}',method='POST',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=45) as r:raw=r.read(20000)
    except urllib.error.HTTPError as e:raw=e.read(20000)
    value=json.loads(raw)
    allowed={'status','bound','readonly','migrations','synthetic_identities','bridge_enabled','proof_present','auth_admin_present','application_writes','auth_calls','secrets_returned','error','sqlstate'}
    if not isinstance(value,dict) or set(value)-allowed or token in raw.decode():raise RuntimeError('response_boundary')
    print(json.dumps(value));return value.get('status')=='EDGE_READONLY_CONNECTION_PASS'
if __name__=='__main__':
    try:sys.exit(0 if main() else 2)
    except Exception as e:print(json.dumps({'status':'NO_GO','error_type':type(e).__name__}));sys.exit(2)
