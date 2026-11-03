"""Fresh-runner case entry; unavailable actual adapter stops before install."""
import argparse
import importlib
import json
import os
import pathlib
import re
import sys

from .bootstrap import SOURCES, bootstrap, require


def _adapter():
    return importlib.import_module('quota_candidate_v1.case_ci')


def _environment(env, adapter):
    require(env.get('GITHUB_ACTIONS') == 'true' and
            env.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging' and
            env.get('GITHUB_REF') == 'refs/heads/main' and
            env.get('GITHUB_RUN_ATTEMPT') == '1', 'case_entry_ci_scope')
    require(re.fullmatch('[a-f0-9]{40}', env.get('GITHUB_SHA', '')) and
            re.fullmatch('[1-9][0-9]{0,18}', env.get('GITHUB_RUN_ID', '')) and
            int(env['GITHUB_RUN_ID']) <= 9223372036854775807,
            'case_entry_source_run')
    require(bool(env.get('CANDIDATE_BLOB')) and
            re.fullmatch('[a-f0-9]{64}', env.get('CANDIDATE_SHA256', '')),
            'case_entry_candidate')
    names = getattr(adapter, 'CASE_NAMES', ())
    require(type(names) is tuple and len(names) == 15 and len(set(names)) == 15
            and 'normal' in names and all(isinstance(n, str) and
                re.fullmatch('[a-z][a-z0-9_]{0,63}', n) for n in names),
            'case_entry_names')
    name = env.get('CASE_NAME')
    require(name in names, 'case_entry_name')
    require(getattr(adapter, 'READY', False) is True and
            callable(getattr(adapter, 'run', None)), 'case_entry_adapter_not_ready')
    sources = getattr(adapter, 'SOURCES', ())
    require(type(sources) is tuple and bool(sources) and len(set(sources)) == len(sources)
            and '_offline/phase6e11/endchain_v1/quota_candidate_v1/case_ci.py' in sources
            and all(isinstance(p, str) and p.startswith('_offline/') and
                    '\\' not in p and '..' not in pathlib.PurePosixPath(p).parts
                    for p in sources), 'case_entry_adapter_sources')
    return name, set(sources) | set(SOURCES)


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    gate = None
    code = 1
    summary = {'status': 'ADAPTER_NOT_READY', 'full_chain_admission': False,
               'hosted_admitted': False}
    try:
        adapter = _adapter()
        name, sources = _environment(os.environ, adapter)
        import admission_ci
        admission_ci.EXTRA |= sources
        admission_ci.app.previous.prior.old.EXTRA |= sources
        gate = admission_ci.Gate()
        gate.result.update(case_name=name, phase='candidate', case_execution_started=False)
        migrations = gate.fetch()
        gate.bind_modules(sys.modules[__name__], adapter)
        import ci_source_binding
        gate.bind_modules(ci_source_binding)
        manifest = json.loads((gate.out / 'candidate.json').read_bytes())
        gate.save('case-entry-loaded-source.json', ci_source_binding.verify_all(
            pathlib.Path(os.environ['GITHUB_WORKSPACE']), gate.sources, manifest['sources']))
        gate.result['phase'] = 'case_stack_install'
        gate.install()
        gate.result['case_execution_started'] = True
        report = adapter.run(gate, migrations, name, bootstrap=bootstrap)
        require(isinstance(report, dict) and report.get('status') == 'CASE_PASS' and
                report.get('case_name') == name and
                report.get('source_commit') == os.environ['GITHUB_SHA'] and
                report.get('ci_run') == os.environ['GITHUB_RUN_ID'] and
                report.get('candidate_sha256') == os.environ['CANDIDATE_SHA256'],
                'case_entry_actual_report')
        gate.save('case-execution.json', report)
        summary = {'status': 'CASE_PASS', 'case_name': name,
                   'full_chain_admission': False, 'hosted_admitted': False}
        code = 0
    except Exception as error:
        summary.update(status='NO_GO' if gate is not None else 'ADAPTER_NOT_READY',
                       error_type=type(error).__name__)
    finally:
        if gate is not None:
            gate.result.update(summary)
            gate.result['matrix_aggregation_required'] = True
            try:
                gate.save('result.json', gate.result)
            except Exception as error:
                code = 1
                summary['status'] = 'NO_GO'
                summary.setdefault('error_type', type(error).__name__)
                summary['result_write_error_type'] = type(error).__name__
                gate.result.update(summary)
        print(json.dumps(summary, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
