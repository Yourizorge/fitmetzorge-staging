"""Same private audit arm body, one atomic DO instead of four protocol commands."""
import importlib.util,pathlib
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('endchain_original_auth_audit',HERE.parent/'auth_metadata_v1/audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def render(run,ids,action,role,route):
    text=audit.arm(run,ids,action,role,route)
    prefix="BEGIN; SET LOCAL lock_timeout='1s';\nDO $arm$ BEGIN\n"
    suffix="END $arm$; COMMIT;"
    if not text.startswith(prefix) or not text.endswith(suffix):
        raise ValueError('original_arm_shape_changed')
    # DO runs in an implicit PostgreSQL transaction. All existing locks, actor,
    # lease and action-key checks remain byte-for-byte inside this body.
    body=text[len(prefix):-len(suffix)]
    return "DO $arm$ BEGIN\n PERFORM pg_catalog.set_config('lock_timeout','1s',true);\n"+body+"END $arm$;"
