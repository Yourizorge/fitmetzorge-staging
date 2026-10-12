"""All existing PG17 observer/concurrency tests with the compact arm renderer."""
import importlib.util,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
from auth_arm import render
spec=importlib.util.spec_from_file_location('endchain_metadata_local',HERE.parent/'auth_metadata_v1/local.py')
local=importlib.util.module_from_spec(spec);spec.loader.exec_module(local)
local.audit.arm=render
if __name__=='__main__':sys.exit(local.main())
