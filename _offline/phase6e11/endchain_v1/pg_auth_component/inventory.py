"""Complete existing Gate closure plus explicit component additions; no dispatch."""
import pathlib

PREFIX = '_offline/phase6e11/endchain_v1/'
WORKFLOW = '.github/workflows/phase6e-pg-auth-component.yml'
OWN = tuple(PREFIX + 'pg_auth_component/' + name for name in (
    '__init__.py', 'runner.py', 'test_runner.py', 'worker.py', 'pg_worker.py',
    'test_worker.py', 'parent.py', 'entry.py', 'inventory.py', 'prepare.py',
    'lifecycle.py','scope.py','subset.py','context.py','test_lifecycle.py',
    'test_scope.py','test_subset.py','test_parent.py','test_entry.py'))


def additions():
    from . import runner, worker
    from case_stack_v1 import SOURCES
    dependencies = ('admission_auth_runtime_profile.py','fixture_cleanup_runtime.py',
        'quota_candidate_v1/runtime_registered_startup.py',
        'fixture_producer_scope.py','native_runtime.py','auth_failure_tracked.py',
        'admission_journal.py','test_admission_auth_runtime_profile.py','test_fixture_producer_scope.py',
        'fixture_cleanup_runtime_test.py','test_fixture_parent_closure.py')
    return (set(OWN) | set(runner.SOURCES) | set(worker.SOURCES) | set(SOURCES)
            | {PREFIX+n for n in dependencies} | {WORKFLOW})


def register(admission):
    names = additions()
    admission.EXTRA |= names
    admission.app.previous.prior.old.EXTRA |= names
    return names


def paths(admission, root):
    register(admission)
    result = set(admission.app.previous.prior.old.old.EXTRAS) | set(admission.app.previous.prior.old.EXTRA)
    root = pathlib.Path(root)
    result |= {path.relative_to(root).as_posix() for path in (root/'supabase/migrations').glob('*.sql')}
    result |= {path.relative_to(root).as_posix() for path in (root/'supabase/tests').glob('*.sql')}
    return sorted(result)
