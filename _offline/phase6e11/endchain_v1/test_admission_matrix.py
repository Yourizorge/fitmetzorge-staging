"""Matrix source/ZIP controls only; fake archives are not CI admission."""
import base64
import contextlib
import copy
import hashlib
import io
import json
import pathlib
import types
import unittest
import uuid
import zipfile
from unittest.mock import patch

import admission_matrix_ci as ci
import admission_matrix_ops as ops

HEAD, CANDIDATE, RUN = 'a'*40, 'b'*64, '12345'
SOURCES = {'_offline/test.py': hashlib.sha256(b'synthetic source').hexdigest()}


def encoded(value): return json.dumps(value, sort_keys=True).encode()


def fixture(name='normal', *, change=None):
    result = {'commit': HEAD, 'run_id': RUN, 'candidate_sha256': CANDIDATE,
              'case_name': name, 'status': 'CASE_PASS', 'hosted_admitted': False,
              'full_chain_admission': False}
    case = {'source_commit': HEAD, 'ci_run': RUN, 'candidate_sha256': CANDIDATE,
            'case_name': name, 'status': 'CASE_PASS'}
    files = {'result.json': encoded(result), 'candidate.json': encoded({'sha256': CANDIDATE, 'sources': SOURCES}),
             'case-execution.json': encoded(case)}
    if change: change(files)
    files['artifact-manifest.json'] = encoded({n: hashlib.sha256(v).hexdigest() for n,v in files.items()})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for n, value in files.items(): archive.writestr(n, value)
    return stream.getvalue()


class ArchiveTests(unittest.TestCase):
    def verify(self, raw, name='normal'):
        return ops.verify_archive(raw, name=name, head=HEAD, candidate=CANDIDATE, run=RUN,
                                  expected_sources=SOURCES)

    def test_prepared_candidate_bytes_bind_exact_source_map(self):
        raw = encoded({'format': 1, 'files': {'_offline/test.py': base64.b64encode(b'synthetic source').decode()}})
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(ops.prepared_sources(raw, digest), SOURCES)
        with self.assertRaisesRegex(ValueError, 'prepared_candidate_digest'):
            ops.prepared_sources(raw+b' ', digest)

    def test_missing_wrong_or_invented_source_map_is_rejected(self):
        for sources in (None, 17, {'../not_candidate.py': '0'*64},
                        {'_offline/test.py': '0'*64}, {'_offline/invented.py': '0'*64}):
            with self.subTest(sources=sources):
                def change(files):
                    files['candidate.json'] = encoded({'sha256': CANDIDATE, 'sources': sources})
                with self.assertRaisesRegex(ValueError, 'source_'):
                    self.verify(fixture(change=change))

    def test_exact_binding_and_raw_manifest_retained(self):
        raw = fixture(); result = self.verify(raw)
        self.assertEqual(result['archive_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertIn('artifact-manifest.json', result['payloads'])

    def test_other_commit_run_and_candidate_rejected_even_if_zip_resealed(self):
        for key, value in (('commit','c'*40), ('run_id','54321'), ('candidate_sha256','c'*64)):
            with self.subTest(key=key):
                def change(files):
                    data=json.loads(files['result.json']);data[key]=value;files['result.json']=encoded(data)
                with self.assertRaisesRegex(ValueError,'result_binding'): self.verify(fixture(change=change))

    def test_case_receipt_cannot_belong_to_another_runner(self):
        def change(files):
            data=json.loads(files['case-execution.json']);data['case_name']='route_a'
            files['case-execution.json']=encoded(data)
        with self.assertRaisesRegex(ValueError,'case_receipt_binding'): self.verify(fixture(change=change))

    def test_full_or_hosted_admission_is_never_accepted_from_worker(self):
        for key in ('hosted_admitted','full_chain_admission'):
            def change(files):
                data=json.loads(files['result.json']);data[key]=True;files['result.json']=encoded(data)
            with self.assertRaisesRegex(ValueError,'unreviewed_admission'): self.verify(fixture(change=change))

    def test_path_escape_and_case_alias_are_rejected(self):
        for name in ('../escape.json','folder/file.json','RESULT.JSON'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.verify(fixture(change=lambda f:f.update({name:b'{}'})))

    def test_member_size_is_bounded_before_reading(self):
        with self.assertRaisesRegex(ValueError,'size_or_link'):
            self.verify(fixture(change=lambda f:f.update({'large.txt':b'x'*(ops.MAX_MEMBER+1)})))

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate_json_key'):
            self.verify(fixture(change=lambda f:f.update({'result.json':b'{"status":0,"status":1}'})))

    def test_changed_member_fails_its_manifest(self):
        raw=fixture()
        with zipfile.ZipFile(io.BytesIO(raw)) as original:
            files={n:original.read(n) for n in original.namelist()}
        files['result.json']=b'{}'
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as out:
            for name,value in files.items():out.writestr(name,value)
        with self.assertRaisesRegex(ValueError,'member_digest'):self.verify(stream.getvalue())

    def test_incomplete_case_preserved_but_never_passes(self):
        def change(files):
            files.pop('case-execution.json')
            value=json.loads(files['result.json']);value['status']='NO_GO';files['result.json']=encoded(value)
        result=self.verify(fixture(change=change))
        self.assertIsNone(result['case']);self.assertEqual(result['result']['status'],'NO_GO')


class AggregateTests(unittest.TestCase):
    def setUp(self):
        self.values={}
        for i,name in enumerate(ci.NAMES):
            self.values[name]={'source_manifest_sha256':'a'*64,'archive_sha256':str(i).zfill(64),
                'manifest_sha256':'b'*64,'files':3,
                'result':{'status':'PASS' if name=='application' else 'CASE_PASS'},
                'case':{'status':'CASE_PASS','isolation':{'pg_system_identifier':str(i+1),
                    'database_oid':5,'pg_container':str(i).zfill(64),'auth_container':str(100+i).zfill(64),
                    'run_id':str(uuid.UUID(int=i+1)),'db_target_sha256':'d'*64,'auth_target_sha256':'d'*64,
                    'reused':False,'auth_database_bound':True}}}

    def test_complete_matrix_is_still_not_hosted_authority(self):
        result=ops.aggregate(self.values, run_conclusion='success')
        self.assertEqual(result['status'],'LOCAL_MATRIX_VERIFIED_PENDING_REVIEW')
        self.assertFalse(result['hosted_admitted']);self.assertFalse(result['owner_window_allowed'])

    def test_missing_case_is_not_optional(self):
        self.values.pop('closure_failure')
        with self.assertRaisesRegex(ValueError,'incomplete_case_set'):ops.aggregate(self.values, run_conclusion='success')

    def test_case_source_mismatch_is_not_averaged(self):
        self.values['normal']['source_manifest_sha256']='c'*64
        with self.assertRaisesRegex(ValueError,'different_source_manifests'):ops.aggregate(self.values, run_conclusion='success')

    def test_database_or_container_reuse_rejected(self):
        for field in ('pg_system_identifier','pg_container','auth_container','run_id'):
            value=copy.deepcopy(self.values)
            value['route_a']['case']['isolation'][field]=value['normal']['case']['isolation'][field]
            with self.assertRaisesRegex(ValueError,'database_reuse'):ops.aggregate(value, run_conclusion='success')

    def test_auth_must_target_same_database(self):
        self.values['normal']['case']['isolation']['auth_target_sha256']='e'*64
        with self.assertRaisesRegex(ValueError,'auth_database_isolation'):ops.aggregate(self.values, run_conclusion='success')

    def test_reused_cluster_with_another_database_oid_is_rejected(self):
        self.values['route_a']['case']['isolation']['pg_system_identifier'] = self.values['normal']['case']['isolation']['pg_system_identifier']
        self.values['route_a']['case']['isolation']['database_oid'] = 6
        with self.assertRaisesRegex(ValueError, 'database_reuse'): ops.aggregate(self.values, run_conclusion='success')

    def test_missing_isolation_and_actual_failure_remain_no_go(self):
        self.values['route_a']['case'].pop('isolation')
        self.values['route_b']['result']['status']='NO_GO'
        result=ops.aggregate(self.values, run_conclusion='success')
        self.assertEqual(result['status'],'NO_GO');self.assertEqual(len(result['blockers']),2)

    def test_app_blocker_not_promoted_by_successful_cases(self):
        self.values['application']['result']['status']='NO_GO'
        self.assertEqual(ops.aggregate(self.values, run_conclusion='success')['status'],'NO_GO')

    def test_persisted_pass_receipts_cannot_override_failed_process(self):
        for conclusion in ('failure', 'cancelled', 'timed_out', None):
            result = ops.aggregate(self.values, run_conclusion=conclusion)
            self.assertEqual(result['status'], 'NO_GO')
            self.assertIn('ci_execution_not_successful', result['blockers'])
            self.assertEqual(result['cases']['normal']['status'], 'CASE_PASS')

    def test_collector_uses_github_run_conclusion_not_receipt_flag(self):
        import inspect
        self.assertIn("aggregate(verified, run_conclusion=metadata.get('conclusion'))",
                      inspect.getsource(ops.collect))


class EntryTests(unittest.TestCase):
    def test_storage_failure_never_leaks_primary_exception_context(self):
        for method in ('mkdir', 'open'):
            output = io.StringIO()
            with patch.object(ci, 'source_contract', side_effect=ValueError('PRIVATE_SENTINEL')), \
                    patch.dict(ci.os.environ, {'RUNNER_TEMP': '/synthetic'}), \
                    patch.object(pathlib.Path, 'mkdir'), \
                    patch.object(pathlib.Path, method, side_effect=OSError('PRIVATE_STORAGE')), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(ci.main(), 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result['error_class'], 'ValueError')
            self.assertEqual(result['receipt_error_class'], 'OSError')
            self.assertNotIn('PRIVATE', output.getvalue())

    def test_unready_adapter_blocks_before_preparation(self):
        with patch.object(ci.importlib,'import_module',return_value=types.SimpleNamespace(READY=False)):
            with self.assertRaisesRegex(ValueError,'not_ready'):ci.source_contract()

    def test_source_inventory_requires_real_adapter_and_all_cases(self):
        adapter=types.SimpleNamespace(READY=True,CASE_NAMES=ci.NAMES[1:],run=lambda:None,
            SOURCES=('_offline/phase6e11/endchain_v1/quota_candidate_v1/case_ci.py',))
        with patch.object(ci.importlib,'import_module',return_value=adapter):
            source=ci.source_contract()
        self.assertTrue(set(ci.SELF_SOURCES)<=source)
        self.assertTrue(set(ci.STACK_SOURCES)<=source)

    def test_exact_serial_matrix_without_secrets_retries_or_paid_runner(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        text=(root/'.github/workflows'/ci.WORKFLOW).read_text()
        for item in ('max-parallel: 1','fail-fast: false','github.run_attempt == 1',
                     'runs-on: ubuntu-24.04','timeout-minutes: 25','contents: read','persist-credentials: false'):
            self.assertIn(item,text)
        for item in ('secrets.','id-token: write','supabase db push','continue-on-error: true','self-hosted'):
            self.assertNotIn(item,text)
        self.assertIn('case: ['+', '.join(ci.NAMES)+']',text)


if __name__ == '__main__':unittest.main()
