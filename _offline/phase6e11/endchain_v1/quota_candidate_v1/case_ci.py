"""Fixed matrix-entry contract. No stack may start before the actual joins close."""
import pathlib
from .compiler import CandidateStop
from .runtime_faults import CASES

CASE_NAMES = CASES
READY = False
_PREFIX = '_offline/phase6e11/endchain_v1/quota_candidate_v1/'
SOURCES = tuple(_PREFIX + name for name in (
    '__init__.py','compiler.py','candidate.sql.in','test_quota_candidate.py','README.md',
    'runtime_adapter.py','runtime_refs.json','runtime_node.mjs','runtime_parent_workflow.py',
    'runtime_auth.mjs','runtime_workflow.mjs','runtime_integral_workflow.mjs',
    'runtime_faults.py','runtime_dispatch.py','runtime_prefix.py','runtime_history.py',
    'runtime_recovery.py','test_runtime_recovery.py',
    'runtime_bootstrap_closeout.py','test_runtime_bootstrap_closeout.py',
    'runtime_case_entry.py','test_runtime_case_entry.py',
    'runtime_case_terminal.py','test_runtime_case_terminal.py',
    'runtime_catalog.py','test_runtime_catalog.py',
    'runtime_lifecycle.py','test_runtime_lifecycle.py',
    'runtime_registered_bootstrap.py',
    'runtime_registered_startup.py','runtime_registered_cleanup.py',
    'runtime_registered_costs.py','runtime_auth_failure_component.py',
    'runtime_auth_failure_witness.py','runtime_auth_failure_verify.py',
    'runtime_registered_fixture_closeout.py',
    'runtime_terminal.py','test_runtime_terminal.py',
    'runtime_terminal_bootstrap.py','test_runtime_terminal_bootstrap.py',
    'runtime_http.py','runtime_http.mjs','test_runtime_http.py','test_runtime_http.mjs',
    'runtime_exported_http.py','test_runtime_exported_http.py',
    'runtime_exported_terminal.py','test_runtime_exported_terminal.py','exported_worker.py',
    'runtime_worker_runner.py','runtime_worker_evidence.py','test_runtime_worker_evidence.py',
    'runtime_native_templates.py','runtime_native_templates.mjs','test_runtime_native_templates.py',
    'runtime_stream.py','test_runtime_stream.py',
    'test_runtime_adapter.py','test_runtime_node.mjs','test_runtime_faults.py',
    'test_runtime_dispatch.py','test_runtime_prefix.py','test_runtime_history.py',
    'case_ci.py','test_case_ci.py','RUNTIME.md')) + (
    '_offline/phase6e11/endchain_v1/admission_budget_current_release.py',
    '_offline/phase6e11/endchain_v1/admission_budget_root_runtime.py',
    '_offline/phase6e11/endchain_v1/admission_budget_root_replay.py',
    '_offline/phase6e11/endchain_v1/test_admission_budget_root_replay.py',
    '_offline/phase6e11/endchain_v1/admission_matrix_bootstrap.py',
    '_offline/phase6e11/endchain_v1/admission_budget_bootstrap_prefix.py',
    '_offline/phase6e11/endchain_v1/admission_budget_prefix_originals.py',
    '_offline/phase6e11/endchain_v1/test_admission_source_bytes.py',
    '_offline/phase6e11/endchain_v1/assembly_checks/byte_pairs_20261111.json',
    '_offline/phase6e11/endchain_v1/test_admission_budget_bootstrap_prefix.py',
    '_offline/phase6e11/endchain_v1/admission_case_archive.py',
    '_offline/phase6e11/endchain_v1/test_admission_case_archive.py',
    '_offline/phase6e11/endchain_v1/hosted_gate.py',
    '_offline/phase6e11/endchain_v1/admission_quota_readonly.py',
    '_offline/phase6e11/endchain_v1/admission_module_binding.py',
    '_offline/phase6e11/endchain_v1/auth_failure.py',
    '_offline/phase6e11/endchain_v1/auth_failure_tracked.py',
    '_offline/phase6e11/endchain_v1/auth_failure_transport.py',
    '_offline/phase6e11/endchain_v1/test_runtime_registered_bootstrap.py',
    '_offline/phase6e11/endchain_v1/test_runtime_registered_fixture_closeout.py',
    '_offline/phase6e11/controller_guard_v1/guard.py',
    '_offline/phase6e11/auth_metadata_v1/audit.py',
    '_offline/phase6e11/auth_metadata_v1/auth_contract.py',
    '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py',)

MISSING = ('complete_root_local_and_hosted_equivalent_bounds',
           'tracked_auth_context_startup_and_owned_cleanup',
           'actual_case_terminal_evidence_validator',
           'candidate_origin_execution_join')


def _case(case_name):
    if case_name not in CASE_NAMES:raise CandidateStop('case_name_denied')


def prepare_execution(gate, case_name):
    _case(case_name)
    from .runtime_case_entry import prepare_execution as prepare
    return prepare(gate, case_name)


def run(gate, migrations, case_name, *, bootstrap, prepared=None):
    _case(case_name)
    from .runtime_case_entry import run as execute
    return execute(gate,migrations,case_name,bootstrap=bootstrap,prepared=prepared)
