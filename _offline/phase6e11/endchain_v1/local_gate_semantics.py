"""Fast PG17 semantic check of new catalog SQL; disposable synthetic DB only."""
import json,sys,uuid
from local_composition import n,r,HERE
import lifecycle_gates as gates

def main():
    folder=r.ROOT/'supabase/.temp'/('phase6e11-gate-semantics-'+uuid.uuid4().hex);folder.mkdir()
    try:
        r.ServerBoundary.setUpClass();r.enable_local_tls=n.local_ca_and_leaf;w=n.NativeRequests(folder)
        for name in ['20261012104331_phase6e11_controller_evidence.sql','20261012185121_phase6e11_single_endchain_budget.sql']:
            w.sql((r.ROOT/'supabase/migrations'/name).read_text())
        catalog=w.rows(gates.CATALOG.replace('$1',"'{}'"))[0]['value']
        access=w.rows(gates.ACCESS.replace('$1',"'{}'"))[0]
        result={'status':'LOCAL_PG17_GATE_SEMANTICS_PASS','catalog_sections':list(catalog),
            'function_count':len(catalog['functions']),'private_functions_safe':access['private_functions_safe'],
            'absence':'Requires actual GoTrue tables; tested in clean Docker CI, not this narrow semantic check.',
            'hosted_calls':0,'local_only':True}
        if not access['private_functions_safe']:raise RuntimeError('local_private_function_boundary')
        r.save(folder/'result.json',result);print(json.dumps(result));return 0
    finally:
        if getattr(r.ServerBoundary,'cluster',None):r.ServerBoundary.tearDownClass()

if __name__=='__main__':sys.exit(main())
