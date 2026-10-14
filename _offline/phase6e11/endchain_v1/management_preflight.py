"""Bounded GET-only staging management inspection; zero SQL or JIT mutations."""
import importlib.util,json,pathlib,re,sys,time,urllib.error,urllib.request,uuid

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'controller_v1'))
import jit_diagnose as j

def main():
    folder=j.ROOT/'supabase/.temp'/('phase6e11-endchain-management-'+uuid.uuid4().hex);folder.mkdir()
    result={'status':'NO_GO','sql_commands':0,'jit_requests':0,'auth_mutations':0,'automatic_retries':0}
    token=journal=None
    try:
        token=j.jit.sb.credential();journal=j.Journal(token,folder)
        result.update(inspection=journal.inspect())
        config=journal.request('auth_policy',j.BASE+'/config/auth')
        import auth_preflight
        result['auth_policy']=auth_preflight.settings(config)
        public=(j.ROOT/'config.js').read_text()
        key=re.search(r'SUPABASE_ANON_KEY:\s*"(sb_publishable_[A-Za-z0-9_-]+)"',public)
        if not key or 'https://mokxyyullfhkfalopbzd.supabase.co' not in public:raise ValueError('public_project_binding')
        req=urllib.request.Request('https://mokxyyullfhkfalopbzd.supabase.co/auth/v1/health',method='GET',
            headers={'apikey':key[1]})
        started=time.monotonic()
        with urllib.request.build_opener(j.jit.NoRedirect()).open(req,timeout=5) as response:
            raw=response.read(4097)
            if len(raw)>4096:raise ValueError('auth_health_response_budget')
            value=json.loads(raw)
            version=value.get('version')
            if not isinstance(version,str) or not re.fullmatch(r'v?\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.]+)?',version):
                raise ValueError('auth_health_version_unavailable')
            result['auth_health']={'version':version,'http_status':response.status,
                'duration_ms':round((time.monotonic()-started)*1000)}
        pinned=re.search(r"IMAGE='supabase/gotrue:(v[0-9.]+)'",(HERE.parent/'controller_guard_v1/auth_service.py').read_text())
        if not pinned:raise ValueError('auth_ci_pin_missing')
        result['auth_ci_pin']=pinned[1]
        result['auth_version_matches_ci']=version==pinned[1]
        result['status']='READ_ONLY_MANAGEMENT_COMPLETE'
    except j.Rejected as error:
        result.update(phase=error.phase,code=error.code)
    except urllib.error.HTTPError as error:
        result.update(phase='auth_health_metadata',http_status=error.code)
    except Exception as error:
        result.update(phase='credential_or_health_metadata',error_class=type(error).__name__)
    finally:
        if journal:journal.token=None
        token=None
        j.m.save(folder/'result.json',result)
    print(json.dumps({**result,'evidence':str(folder)}))
    return 0 if result['status']=='READ_ONLY_MANAGEMENT_COMPLETE' else 2

if __name__=='__main__':sys.exit(main())
