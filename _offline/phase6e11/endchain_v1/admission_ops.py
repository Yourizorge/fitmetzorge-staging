"""Reuse source-only application packaging for the disposable admission workflow."""
import importlib.util
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import admission_ci

spec = importlib.util.spec_from_file_location('admission_application_ops',
    HERE.parents[1]/'phase6e_server_v1/ops.py')
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)
ops.ci = admission_ci.app
ops.WORKFLOW = 'phase6e-admission-local-ci.yml'


def dispatch_preflight(folder):
    folder = pathlib.Path(folder).resolve()
    if folder.parent != ops.ROOT/'supabase/.temp' or not folder.name.startswith('phase6e-server-ci-'):
        raise ValueError('admission_dispatch_scope')
    head = ops.g.git('rev-parse', 'HEAD')
    before = json.loads(ops.disk(folder/'before.json').read_bytes())
    if (ops.g.git('branch', '--show-current') != 'main' or before.get('head') != head
            or ops.g.git('ls-remote', 'origin', 'refs/heads/main').split()[0] != head):
        raise ValueError('admission_dispatch_source_changed')
    blob = json.loads(ops.disk(folder/'blob.json').read_bytes())
    if hashlib.sha256(ops.disk(folder/'candidate.json').read_bytes()).hexdigest() != blob.get('sha256'):
        raise ValueError('admission_dispatch_candidate_changed')
    if (folder/'dispatch.json').exists():
        raise ValueError('admission_dispatch_consumed')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'dispatch':
        dispatch_preflight(sys.argv[2])
    ops.main()
