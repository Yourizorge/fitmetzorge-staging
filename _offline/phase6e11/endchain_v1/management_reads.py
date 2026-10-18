"""Two bounded private reads, sharing the existing Management request budget."""
import json,time,urllib.error,urllib.request

PROJECT='mokxyyullfhkfalopbzd'

def read(journal,kind,save,anon=None):
    if kind not in ('api_keys','auth_health'):raise ValueError('private_read_scope')
    if journal.calls>=24 or time.monotonic()>=journal.deadline:raise ValueError('private_read_budget')
    if kind=='api_keys':
        url='https://api.supabase.com/v1/projects/'+PROJECT+'/api-keys?reveal=true'
        headers={'Authorization':'Bearer '+journal.token,'Accept':'application/json'};limit=100000
    else:
        if not isinstance(anon,str) or not anon:raise ValueError('private_health_key_missing')
        url='https://'+PROJECT+'.supabase.co/auth/v1/health';headers={'apikey':anon};limit=4096
    journal.calls+=1
    label='private-read-%02d-%s'%(journal.calls,kind)
    record={'ordinal':journal.calls,'category':kind,'method':'GET','at_ms':int(time.time()*1000),
            'automatic_retry':False,'response_exported':False}
    save(label+'-started.json',record.copy());started=time.monotonic()
    try:
        with journal.opener.open(urllib.request.Request(url,headers=headers),timeout=5) as response:
            record['http_status']=response.status
            raw=response.read(limit+1)
        if len(raw)>limit:raise ValueError('private_read_response_budget')
        value=json.loads(raw);raw=None
        return value
    except urllib.error.HTTPError as error:
        record.update(http_status=error.code,error_class='HTTPError')
        raise ValueError('private_read_http_failed') from None
    except Exception as error:
        record['error_class']=type(error).__name__
        raise ValueError('private_read_transport_or_format') from None
    finally:
        record['duration_ms']=round((time.monotonic()-started)*1000)
        save(label+'-result.json',record)
