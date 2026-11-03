"""Same-source application plus fresh-runner cases; never a hosted entry."""
import importlib
import json
import os
import pathlib

import admission_ci
from admission_budget import CASES
from case_stack_v1 import SOURCES as STACK_SOURCES

NAMES = ('application', 'normal', *CASES)
WORKFLOW = 'phase6e-admission-matrix-local-ci.yml'
SELF_SOURCES = ('_offline/phase6e11/endchain_v1/admission_matrix_ci.py',
    '_offline/phase6e11/endchain_v1/admission_matrix_ops.py',
    '_offline/phase6e11/endchain_v1/test_admission_matrix.py',
    '.github/workflows/' + WORKFLOW)


def source_contract():
    adapter = importlib.import_module('quota_candidate_v1.case_ci')
    if (getattr(adapter, 'READY', False) is not True
            or getattr(adapter, 'CASE_NAMES', None) != NAMES[1:]
            or not callable(getattr(adapter, 'run', None))):
        raise ValueError('matrix_actual_adapter_not_ready')
    sources = getattr(adapter, 'SOURCES', ())
    if (type(sources) is not tuple or not sources or len(set(sources)) != len(sources)
            or '_offline/phase6e11/endchain_v1/quota_candidate_v1/case_ci.py' not in sources
            or any(not isinstance(p, str) or not p.startswith('_offline/')
                   or '\\' in p or '..' in pathlib.PurePosixPath(p).parts for p in sources)):
        raise ValueError('matrix_adapter_source_inventory')
    extra = set(sources) | set(STACK_SOURCES) | set(SELF_SOURCES)
    admission_ci.EXTRA |= extra
    admission_ci.app.previous.prior.old.EXTRA |= extra
    return extra


def main():
    try:
        source_contract()
        name = os.environ.get('CASE_NAME')
        if name not in NAMES:
            raise ValueError('matrix_case_name')
        if name == 'application':
            return admission_ci.Gate().run()
        from case_stack_v1.ci import main as case_main
        return case_main([])
    except Exception as error:
        # No free exception text, paths, connection fields or caller data.
        result = {'status': 'ADAPTER_NOT_READY', 'error_class': type(error).__name__,
                  'hosted_admitted': False, 'full_chain_admission': False}
        try:
            root = pathlib.Path(os.environ['RUNNER_TEMP'])/'fmz-db41-evidence'
            root.mkdir(exist_ok=True)
            with (root/'matrix-preflight-stop.json').open('x') as stream:
                json.dump(result, stream, sort_keys=True)
        except Exception as storage_error:
            result['receipt_error_class'] = type(storage_error).__name__
        print(json.dumps(result, sort_keys=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
