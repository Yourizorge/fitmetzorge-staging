"""Real localhost framing/eleven-case engine; SQL, Docker and root are models."""
import copy
import json
import types
import unittest
import uuid
from unittest.mock import patch

import test_runtime_registered_context_join as join
from quota_candidate_v1 import runtime_auth_failure_component as job
from quota_candidate_v1 import runtime_registered_bootstrap as bootstrap
from quota_candidate_v1 import runtime_auth_failure_verify as verifier
import auth_failure as engine
import auth_failure_transport as transport


class DiagnosticLedger(join.FakeLedger):
    def defer(self, ticket, **kw):
        super().defer(ticket)
        self.events.append(('partial', ticket.command_id, kw))

    def deferred_group(self, group):
        return tuple(self.deferred)


class ComponentTests(unittest.TestCase):
    def failure_receipt(self, *, defer_failure, early_failure=False):
        fixture = join.JoinTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.binding['candidate_sha'] = 'b' * 64
        fixture.ledger = DiagnosticLedger(fixture.binding)
        fixture.ledger.__class__.__module__ = 'admission_budget_root_runtime'
        primary = RuntimeError('original root defer failure')
        report = {'status': 'LOCAL_AUTH_FAILURE_COMPONENT_PASS' if defer_failure else
                  'LOCAL_AUTH_FAILURE_COMPONENT_FAILED',
                  'cases': [{'case': name} for name in engine.CASES],
                  'safety_reconciliations': [], 'retained_claims': ['admin_unknown'],
                  'diagnostic_totals': {'native_sql_dispatched': 0,
                      'all_managed_observations_complete': True},
                  'reconciliation_diagnostic_totals': {'native_sql_dispatches': 0}}
        def failed_or_saved(gate, **kwargs):
            if early_failure:
                kwargs['read_witness'](str(uuid.uuid4()), 'before_dispatch', 'case', 'preflight',
                    {'users': [], 'session_ids': [], 'counts': dict.fromkeys(engine.SNAPSHOT_COUNTS, 0)})
                raise primary
            gate.save('auth-failure-component.json', report)
            return report
        original_init = join.startup.LocalServer.__init__
        def server_init(server, owner):
            original_init(server, owner)
            server.dsn = 'host=127.0.0.1 dbname=postgres'
            server.profile_receipt['evidence_refs'] = []
        def defer(*args, **kwargs):
            raise primary
        with patch.object(engine, 'run', side_effect=failed_or_saved), \
                patch.object(join.startup.LocalServer, '__init__', server_init):
            if defer_failure or early_failure:
                with patch.object(fixture.ledger, 'defer', side_effect=defer):
                    with self.assertRaises(RuntimeError) as caught:
                        job.run(fixture.gate, binding=fixture.binding,
                            stack={'status': 'CLEAN47_BOOTSTRAP_PASS'}, ledger=fixture.ledger)
                self.assertIs(caught.exception, primary)
            else:
                with self.assertRaisesRegex(ValueError, 'exact_eleven_cases_not_completed'):
                    job.run(fixture.gate, binding=fixture.binding,
                        stack={'status': 'CLEAN47_BOOTSTRAP_PASS'}, ledger=fixture.ledger)
        value = fixture.saved['auth-job-result.json']
        if early_failure:
            self.assertIsNone(value['component_status'])
            self.assertIsNone(value['retained_claims'])
            self.assertFalse(value['original_refs_complete'])
            self.assertTrue(any(r['path'].startswith('auth-failure-observer-private/')
                                for r in value['original_refs']))
            self.assertIsNotNone(value['original_archive_ref'])
            return
        self.assertEqual(value['component_status'], report['status'])
        self.assertEqual(value['retained_claims'], ['admin_unknown'])
        self.assertEqual(value['component_ref']['path'], 'auth-failure-component.json')
        self.assertTrue(value['original_refs'])
        self.assertEqual(fixture.requests, [])
        self.assertEqual(value['status'], 'AUTH_JOB_INCOMPLETE')

    def test_failed_component_preserves_published_originals(self):
        self.failure_receipt(defer_failure=False)

    def test_root_defer_failure_preserves_primary_and_component_originals(self):
        self.failure_receipt(defer_failure=True)

    def test_early_failure_still_packages_first_original_witness(self):
        self.failure_receipt(defer_failure=False, early_failure=True)

    def test_register_is_additional_eleven_not_fifteen_or_hosted(self):
        plan = job.command_register()
        self.assertEqual(tuple(plan['cases']), engine.CASES)
        self.assertEqual(len(plan['cases']), 11)
        self.assertEqual(plan['declared_local_capacity'], 5764)
        self.assertEqual(plan['native_sql_capacity'], 138)
        self.assertEqual(plan['http_capacity'], 45)
        self.assertFalse(plan['managed_costs_proven'])
        self.assertFalse(plan['planned_2349_run_changed'])
        self.assertEqual(plan['parent_bootstrap_http'], 0)

    def test_direct_execute_is_not_an_admission_capability(self):
        with self.assertRaisesRegex(ValueError, 'actual_context_caller'):
            job.execute(types.SimpleNamespace())

    def test_real_localhost_all_eleven_preserve_originals_and_retained_claims(self):
        fixture = join.JoinTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.binding['candidate_sha'] = 'b' * 64
        fixture.ledger = DiagnosticLedger(fixture.binding)
        fixture.ledger.__class__.__module__ = 'admission_budget_root_runtime'
        sessions = {}
        handler = fixture.server.RequestHandlerClass

        def respond(request, body):
            raw = json.dumps(body).encode()
            request.send_response(200)
            request.send_header('Content-Length', str(len(raw)))
            request.end_headers()
            request.wfile.write(raw)

        def post(request):
            raw = request.rfile.read(int(request.headers.get('Content-Length', '0')))
            data = json.loads(raw) if raw else {}
            fixture.requests.append((request.path, data))
            if request.path == '/admin/users':
                actor = str(uuid.uuid4())
                user = {'id': actor, 'email': data['email'],
                        'marker': data['app_metadata']['auth_failure_claim']}
                fixture.users[actor] = user
                respond(request, user)
            elif request.path == '/token?grant_type=password':
                actor = next(k for k, u in fixture.users.items() if u['email'] == data['email'])
                sessions[actor] = str(uuid.uuid4())
                respond(request, {'access_token': actor, 'user': fixture.users[actor]})
            elif request.path == '/logout?scope=global':
                actor = request.headers['Authorization'].removeprefix('Bearer ')
                sessions.pop(actor, None)
                respond(request, {})
            else:
                raise AssertionError('unregistered HTTP route')

        def delete(request):
            fixture.requests.append((request.path, None))
            actor = request.path.rsplit('/', 1)[-1]
            fixture.users.pop(actor, None)
            sessions.pop(actor, None)
            respond(request, {})

        class Backend:
            evidence_kind = 'SYNTHETIC_LOCALHOST_HTTP_SQL_MODEL_NOT_GOTRUE'
            def __init__(self, config):
                self.transport = transport.LocalTransport(config['auth_url'], config['admin_token'])
            def snapshot(self, email, marker, actor, session_ids):
                users = [copy.deepcopy(u) for u in fixture.users.values()
                         if u['email'] == email or u['marker'] == marker or u['id'] == actor]
                keys = [sessions[u['id']] for u in users if u['id'] in sessions]
                counts = dict.fromkeys(engine.SNAPSHOT_COUNTS, 0)
                counts['users'] = counts['identities'] = len(users)
                counts['sessions'] = counts['refresh_tokens'] = len(keys)
                return {'users': users, 'session_ids': keys, 'counts': counts}
            def stats(self):
                return {'reset': '2026-11-04T00:00:00+00:00', 'dealloc': 0, 'track_utility': 'on',
                    'statements': [{'queryid': '1', 'calls': len(fixture.requests),
                        'since': '2026-11-04T00:00:00+00:00', 'temp_written': 0, 'temp_read': 0,
                        'wal_bytes': '0', 'exec_ms': 0.0}]}
            def difference(self, before, after):
                return job.witness.managed_difference(before, after)
            def close(self): pass

        captured = []
        original_init = bootstrap.Context.__init__
        def capture(context, *args, **kwargs):
            original_init(context, *args, **kwargs)
            captured.append(context)
        original_server_init = join.startup.LocalServer.__init__
        def server_init(server, owner):
            original_server_init(server, owner)
            server.dsn = 'host=127.0.0.1 hostaddr=127.0.0.1 dbname=postgres'
            server.profile_receipt['evidence_refs'] = []
        with patch.object(handler, 'do_POST', post), patch.object(handler, 'do_DELETE', delete), \
                patch.object(engine, 'RealBackend', Backend), \
                patch.object(bootstrap.Context, '__init__', capture), \
                patch.object(join.startup.LocalServer, '__init__', server_init), \
                patch.object(bootstrap.Context, '_seed', side_effect=AssertionError('no fixture seed')), \
                patch.object(bootstrap.BootstrapRequests, 'create_all', side_effect=AssertionError('no parent create')):
            with self.assertRaisesRegex(ValueError, 'numeric_closure_missing'):
                job.run(fixture.gate, binding=fixture.binding,
                    stack={'status': 'CLEAN47_BOOTSTRAP_PASS'}, ledger=fixture.ledger)
            result = fixture.saved['auth-job-result.json']
        context, = captured
        self.assertEqual(result['component_status'], 'LOCAL_AUTH_FAILURE_COMPONENT_PASS')
        report = context._diagnostic_report
        self.assertEqual(tuple(r['case'] for r in report['cases']), engine.CASES)
        self.assertTrue(all(r['component_case_pass'] for r in report['cases']))
        self.assertEqual(len(fixture.requests), 28)
        self.assertEqual(report['diagnostic_totals']['native_sql_dispatched'], 95)
        self.assertEqual(report['reconciliation_diagnostic_totals']['native_sql_dispatches'], 6)
        self.assertEqual(result['retained_claims'],
                         ['admin_unknown', 'cleanup_interrupted', 'missing_mint_barrier'])
        self.assertEqual(len(fixture.users), 1)
        self.assertEqual(len(sessions), 1)
        self.assertIsNone(context.producer)
        self.assertIsNone(context.auth)
        self.assertIsNone(context.ids)
        self.assertFalse(hasattr(fixture.gate, 'auth_failure_context'))
        self.assertTrue(context._diagnostic_registry.valid_proof(context._diagnostic_seal))
        self.assertTrue(result['registered_requests_closed'])
        self.assertFalse(result['full_auth_cleanup_proven'])
        self.assertFalse(result['full_chain_admission'])
        self.assertFalse(result['numeric_lifetime_complete'])
        self.assertEqual(result['status'], 'AUTH_JOB_INCOMPLETE')
        self.assertEqual(result['coverage_verification'], 'PENDING_INDEPENDENT_ARCHIVE_VERIFIER')
        self.assertGreater(len(result['original_refs']), 100)
        self.assertEqual(len(context._diagnostic_witness.seen), 101)
        self.assertNotIn('PRIVATE_TEST_ADMIN', json.dumps(result))
        payloads = {p.name: p.read_bytes() for p in fixture.out.glob('*.json')}
        expected = job.archive.object_json(payloads['candidate.json'])
        expected['sha256'] = fixture.binding['candidate_sha']
        payloads['candidate.json'] = job.archive.encoded(expected)
        with self.assertRaisesRegex(ValueError, 'actual_backend_not_unit_model'):
            verifier.replay(payloads, binding=fixture.binding, expected_sources=expected['sources'])
        # Pure replay unit fixture, not new runtime evidence: preserve all actual
        # localhost records but model the backend-origin discriminator in memory.
        originals = job.archive.verify(payloads, result['original_archive_ref'], result['original_refs'])
        projected = copy.deepcopy(report)
        for row in projected['cases']:
            row['evidence_kind'] = 'REAL_LOCAL_PG17_GOTRUE'
            path = 'auth_failure_' + fixture.run_id + '/' + row['case'] + '/result.json'
            value = {k: v for k, v in row.items() if k != 'retained_journal'}
            raw = job.archive.encoded(value)
            originals[path] = raw
            row['retained_journal']['files']['result.json'] = {
                'sha256': job.archive.sha(raw), 'bytes': len(raw), 'content': value}
        remapped_claims = {}
        for row in projected['safety_reconciliations']:
            path = 'auth_failure_' + fixture.run_id + '/' + row['case'] + '/result.json'
            digest = job.archive.sha(originals[path])
            row['original_result_sha256'] = digest
            folder = path.removesuffix('/result.json') + '/safety-reconciliation/'
            for name in ('claim.json', 'result.json'):
                old_digest = job.archive.sha(originals[folder + name])
                value = job.archive.object_json(originals[folder + name])
                value['original_result_sha256'] = digest
                raw = job.archive.encoded(value)
                originals[folder + name] = raw
                row['retained_journal']['files'][name] = {
                    'sha256': job.archive.sha(raw), 'bytes': len(raw), 'content': value}
                if name == 'claim.json': remapped_claims[old_digest] = job.archive.sha(raw)
        for path, raw in list(originals.items()):
            if path.startswith('auth-failure-request-private/'):
                value = job.archive.object_json(raw)
                if value['kind'] == 'admitted':
                    claim_hash = value['reservation']['claim_sha256']
                    if claim_hash in remapped_claims:
                        value['reservation']['claim_sha256'] = remapped_claims[claim_hash]
                        originals[path] = job.archive.encoded(value)
        originals['auth-failure-component.json'] = job.archive.encoded(projected)
        result_copy = copy.deepcopy(result)
        result_copy['component_ref']['sha256'] = job.archive.sha(originals['auth-failure-component.json'])
        result_copy['component_ref']['bytes'] = len(originals['auth-failure-component.json'])
        modeled_payloads = {**payloads, 'auth-job-result.json': job.archive.encoded(result_copy)}
        with patch.object(verifier.archive, 'verify', return_value=originals):
            proof = verifier.replay(modeled_payloads, binding=fixture.binding, expected_sources=expected['sources'])
            self.assertEqual(proof['status'], 'AUTH_FAILURE_PROBE_SEMANTICS_VERIFIED')
            self.assertEqual(proof['native_sql_commands'], 101)
            self.assertEqual(proof['http_dispatches'], 28)
            self.assertFalse(proof['independent_root_terminal_verified'])
            self.assertFalse(proof['full_chain_admission'])
            bad = copy.deepcopy(projected)
            bad['cases'][0]['primary_failure'] = 'auth_failure_wrong_probe'
            changed = {**originals, 'auth-failure-component.json': job.archive.encoded(bad)}
            receipt = copy.deepcopy(result_copy)
            receipt['component_ref'].update(sha256=job.archive.sha(changed['auth-failure-component.json']),
                                           bytes=len(changed['auth-failure-component.json']))
            with patch.object(verifier.archive, 'verify', return_value=changed):
                with self.assertRaisesRegex(ValueError, 'requested_failure_observed'):
                    verifier.replay({**modeled_payloads, 'auth-job-result.json': job.archive.encoded(receipt)},
                        binding=fixture.binding, expected_sources=expected['sources'])
            for path, raw in originals.items():
                if path.startswith('auth-failure-observer-private/'):
                    row = job.archive.object_json(raw)
                    if row['case'] == 'create_lost_reply' and row['key'] == 'stats_before_create':
                        row['value']['statements'][0]['calls'] += 1
                        changed = {**originals, path: job.archive.encoded(row)}
                        break
            else: self.fail('missing counter fixture')
            with patch.object(verifier.archive, 'verify', return_value=changed):
                with self.assertRaisesRegex(ValueError, 'original_counter_difference'):
                    verifier.replay(modeled_payloads, binding=fixture.binding, expected_sources=expected['sources'])
        claim = next(r for r in result['original_refs'] if r['path'].endswith('/admin_unknown/claim.json'))
        with (fixture.out / claim['path']).open('ab') as stream: stream.write(b' ')
        with self.assertRaises(Exception): job.original_refs(context)

    def test_witness_snapshot_has_no_raw_identity_or_credentials(self):
        actor, session = str(uuid.uuid4()), str(uuid.uuid4())
        raw = {'users': [{'id': actor, 'email': 'synthetic@example.invalid', 'marker': 'claim'}],
               'session_ids': [session], 'counts': dict.fromkeys(engine.SNAPSHOT_COUNTS, 0)}
        raw['counts'].update(users=1, sessions=1)
        value = job.witness.snapshot(raw)
        encoded = json.dumps(value)
        for private in (actor, session, 'synthetic@example.invalid', 'claim'):
            self.assertNotIn('"' + private + '"', encoded)
        self.assertEqual(value['users'][0]['email_sha256'], engine.digest('synthetic@example.invalid'))
        self.assertEqual(raw['users'][0]['id'], actor)

    def test_stats_reject_unexpected_query_text_instead_of_exporting_it(self):
        value = {'reset': '2026-11-04T00:00:00Z', 'dealloc': 0, 'track_utility': 'on',
                 'statements': [], 'query': 'private text'}
        with self.assertRaisesRegex(ValueError, 'stats_shape'):
            job.witness.statistics(value)


if __name__ == '__main__':
    unittest.main()
