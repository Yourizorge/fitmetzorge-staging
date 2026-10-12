"""Rerun unchanged product assertions with a correct local-only TLS fixture name."""
import os,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'request_v4'))
import request_local
# Only select the new local process entry; migrations/assertions stay immutable.
request_local.HERE=HERE
# Bound only this local psql harness; no session-wide setting on a hosted pooler.
os.environ['PGOPTIONS']='-c statement_timeout=5000 -c lock_timeout=1000'
if __name__=='__main__':
    if sys.argv[1]=='security':
        import security
        sys.exit(security.main())
    elif sys.argv[1]=='workflow':sys.exit(request_local.main())
    else:raise RuntimeError('local_mode')
