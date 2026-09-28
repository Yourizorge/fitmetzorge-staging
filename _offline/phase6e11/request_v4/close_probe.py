"""Delete only this task's exact temporary diagnostic function, preserving receipts."""
import datetime,json,pathlib,sys,urllib.request,urllib.error,uuid
import install as i
from guard import Stop,save
SLUG='fmz-phase6e11-proof'
ID='144aba78-4fc4-46ad-8213-2141ffac82d1'

def main():
    folder=i.ROOT/'supabase/.temp'/('phase6e11-request-probe-close-'+uuid.uuid4().hex);folder.mkdir()
    token=i.p.jit.sb.credential();i.p.jit.owner_id(token)
    url='https://api.supabase.com/v1/projects/mokxyyullfhkfalopbzd/functions/'+SLUG
    def call(method):
        req=urllib.request.Request(url,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/json'})
        try:
            with urllib.request.build_opener(i.p.jit.NoRedirect()).open(req,timeout=20) as r:
                raw=r.read(200000)
                return r.status,json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code==404:return 404,None
            raise Stop('control_http_'+str(e.code)) from None
    result={'status':'NO_GO','folder':str(folder),'database_connections':0,'auth_calls':0}
    try:
        status,meta=call('GET')
        if status!=200 or meta['id']!=ID or meta['slug']!=SLUG or meta['version']!=2 or meta['created_at']!=1790601056985:
            raise Stop('own_temporary_function_identity')
        save(folder/'before.json',meta)
        status,_=call('DELETE')
        if status not in (200,204):raise Stop('delete_unconfirmed')
        status,_=call('GET')
        if status!=404:raise Stop('temporary_function_still_present')
        root='/v1/projects/mokxyyullfhkfalopbzd'
        jit=i.p.jit.api(token,root+'/jit-access').get('state')
        mappings=i.p.jit.api(token,root+'/database/jit/list').get('items')
        if jit!='disabled' or mappings!=[]:raise Stop('jit_not_closed')
        result.update(status='TEMPORARY_EDGE_REMOVED',http_after=404,jit='disabled',jit_mappings=0,
          closed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    except Exception as e:result['reason']=str(e) if isinstance(e,Stop) else type(e).__name__
    finally:token=None;save(folder/'result.json',result)
    print(json.dumps(result));return result['status']=='TEMPORARY_EDGE_REMOVED'
if __name__=='__main__':sys.exit(0 if main() else 2)
