"""Standalone bootstrap smoke entry, not the fifteen-case orchestration."""
import argparse
import json


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    # No harness import on --help or ordinary package import.
    import admission_ci
    from .bootstrap import SOURCES, bootstrap
    admission_ci.EXTRA |= set(SOURCES)
    admission_ci.app.previous.prior.old.EXTRA |= set(SOURCES)
    gate = admission_ci.Gate()
    code = 1
    try:
        gate.result['phase'] = 'candidate'
        migrations = gate.fetch()
        gate.result['phase'] = 'case_stack_install'
        gate.install()
        bootstrap(gate, migrations)
        gate.result['status'] = 'BOOTSTRAP_ONLY_PASS'
        code = 0
    except Exception as error:
        gate.result['status'] = 'NO_GO'
        gate.result['error_type'] = type(error).__name__
    finally:
        gate.result.update(full_chain_admission=False, hosted_admitted=False,
                           case_execution_started=False, app_suite_repeated=False)
        try:
            gate.save('result.json', gate.result)
        except Exception as error:
            code = 1
            gate.result['status'] = 'NO_GO'
            gate.result.setdefault('error_type', type(error).__name__)
            gate.result['result_write_error_type'] = type(error).__name__
        print(json.dumps({key: gate.result[key] for key in (
            'status', 'full_chain_admission', 'hosted_admitted', 'case_execution_started',
            'error_type', 'result_write_error_type') if key in gate.result}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
