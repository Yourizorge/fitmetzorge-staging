import copy
import hashlib
import json
import os
import pathlib
import tempfile
import unittest

import cost_post_closure as c
import source_cost_probes as p

ROOT = os.environ.get('COST_SOURCE_ROOT')


class CurrentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ROOT:
            raise RuntimeError('COST_SOURCE_ROOT required; no fixture-only source fallback')
        cls.cp = c.Checkpoint(ROOT)
        cls.result = c.compile_checkpoint(ROOT)

    def test_all47_and_platform_first(self):
        report = self.result['coverage']
        self.assertEqual(len(report['rows']), 47)
        self.assertEqual({r['id'] for r in report['rows']}, set(self.cp.report['missing_costs']))
        self.assertTrue(report['rows'][0]['id'].startswith('case.platform.install:'))
        self.assertTrue(all(r['source_refs'] and r['reason'] for r in report['rows']))
        self.assertTrue(all(r['smallest_next_action'] and r['missing_evidence_source'] for r in report['rows']))
        self.assertEqual(len({r['smallest_next_action'] for r in report['rows']}), 47)

    def test_unknown_not_zero_and_no_admission(self):
        report = self.result['coverage']
        self.assertFalse(report['READY'])
        self.assertIsNone(report['minimal_cap'])
        self.assertIsNone(report['total_local_ci_upper_bound'])
        self.assertIsNone(report['total_hosted_equivalent_upper_bound'])
        self.assertEqual(report['closed_full_cost_posts'], 0)
        self.assertTrue(all(r['observed_commands'] is None for r in report['rows']))

    def test_no_arbitrary_cap_and_source_meter_blocker(self):
        report = self.result['coverage']
        self.assertEqual(report['hosted_limit'], 2349)
        core = report['retained_partial_core']
        self.assertEqual(core['normal_declared_capacity'], 2340)
        self.assertEqual(core['meter_required_limit'], 2352)
        self.assertEqual(core['first_denied']['required_limit'], 2350)

    def test_platform_all_outer_prefixes(self):
        plan = self.result['subprograms']['platform']
        self.assertEqual(len(plan['prefixes']), 37)
        self.assertEqual(len(plan['operations']), 36)
        for prefix in plan['prefixes']:
            self.assertEqual(prefix['retained_direct_sql_slots'] + prefix['unreached_direct_sql_slots'], 13)
            self.assertIsNone(prefix['failure_cleanup_upper_bound'])
        self.assertEqual(len(plan['unknown_atoms']), 8)
        self.assertEqual(plan['hosted_projection'], 'NOT_APPLICABLE')

    def test_platform_internal_stale_pins_are_not_silently_refreshed(self):
        gate = self.result['subprograms']['platform']['runtime_pin_gate']
        self.assertFalse(gate['runtime_source_program_accepts'])
        self.assertFalse(gate['unreviewed_repin_performed'])
        mismatches = {r['path'] for r in gate['rows'] if not r['matches_original_runtime_pin']}
        self.assertEqual(mismatches, {c.PREFIX+'admission_ci.py', c.PREFIX+'cli_predispatch/hook.cjs'})

    def test_actual_native_guard_precedes_action_and_denial_is_sticky(self):
        audit = self.result['subprograms']['conditional_native_contract']
        self.assertEqual(len(audit['guard_order_probes']), 4)
        for proof in audit['guard_order_probes']:
            self.assertEqual(proof['events'][:2], ['precharge', 'native_proof'])
            self.assertTrue(proof['primary_preserved'])
            if proof['guard_denied']:
                self.assertNotIn('action', proof['events'])
                self.assertIn('unknown', proof['events'])

    def test_native_source_proof_not_rejected_for_absent_measurement(self):
        audit = self.result['subprograms']['conditional_native_contract']
        self.assertTrue(audit['source_derivation_can_suffice_without_measurement'])
        for route in audit['routes']:
            self.assertFalse(route['measurement_required_for_source_bound'])
            self.assertEqual(route['conditional_driver_sql_bound'], 0)
            self.assertIsNone(route['accepted_current_cost_bound'])
            self.assertTrue(route['stronger_attestation_optional'])
            self.assertFalse(route['full_cost_post_closed'])
            self.assertTrue(route['root_effective_provenance_open'])
        self.assertEqual({r['operation'] for r in audit['routes'] if not r['guard_before_action']},
                         {'auth.scope', 'case.bootstrap.failure_closeout', 'case.quota_read'})
        self.assertEqual(audit['source_bound_contract_startup_upper_bound'], 3)
        self.assertFalse(audit['startup_bound_accepted'])
        self.assertEqual(audit['startup_conditional_source_bound'], 3)
        self.assertEqual(audit['positive_conditional_zero_routes'], 7)
        self.assertIsNone(audit['reported_linux_component_version'])

    def test_conditional_seven_routes_do_not_add_new_supply_chain_gates(self):
        routes = {r['operation']: r for r in self.result['subprograms']['conditional_native_contract']['routes']}
        positive = {name for name, r in routes.items() if r['conditional_source_bound'] == 0}
        self.assertEqual(positive, {'auth.observer_connect', 'auth.observer_reconnect', 'auth.observer_suspend',
            'auth.observer_close', 'auth.engine.close', 'auth.profile', 'auth.fixture_closeout'})
        for name in positive - {'auth.engine.close'}:
            self.assertFalse(routes[name]['route_binding_open'])
            self.assertEqual(routes[name]['missing_preconditions'], [])
        self.assertTrue(routes['auth.engine.close']['route_binding_open'])
        self.assertIn('opened backend', routes['auth.engine.close']['missing_preconditions'][0])
        self.assertTrue(routes['auth.engine.connect']['route_binding_open'])
        self.assertIn('config.dsn', routes['auth.engine.connect']['missing_preconditions'][0])
        for name in ('auth.scope', 'case.bootstrap.failure_closeout', 'case.quota_read'):
            self.assertTrue(routes[name]['route_binding_open'])
            self.assertIsNone(routes[name]['conditional_source_bound'])

    def test_source_seed_all_call_faults(self):
        seed = self.result['subprograms']['seed']
        self.assertEqual(seed['fault_prefix_count'], 37)
        self.assertEqual(seed['direct_sql_upper_bound'], 9)
        self.assertTrue(all(r['reserved'] <= 9 and r['primary_preserved'] for r in seed['fault_prefixes']))
        self.assertTrue(all(r['refund'] == 0 for r in seed['fault_prefixes']))

    def test_source_seed_unknown_commit_no_retry(self):
        faults = self.result['subprograms']['seed']['fault_prefixes']
        for row in faults:
            if row['failure'] in ('seed.commit', 'seed_confirmed'):
                self.assertEqual(row['reserved'], 9)
                self.assertFalse(any(r['id'] == 'seed.rollback' for r in row['commands']))
                self.assertFalse(row['numeric_terminal'])

    def test_source_seed_double_failure_preserved(self):
        faults = self.result['subprograms']['seed']['fault_prefixes']
        selected = [r for r in faults if r['rollback_failure'] and r['failure'] != 'seed.commit']
        self.assertEqual(len(selected), 16)
        self.assertTrue(all(r['primary_preserved'] and r['secondary_preserved'] for r in selected))

    def test_original_pre_dispatch_guards(self):
        guards = self.result['subprograms']['guards']
        self.assertEqual(guards['auth_profile']['explicit_sql_upper_bound'], 11)
        self.assertEqual(guards['fixture_closeout']['explicit_sql_upper_bound'], 37)
        self.assertEqual(guards['fixture_closeout']['normal_explicit'], 36)
        self.assertEqual(guards['fixture_closeout']['unknown_commit_physical_only_explicit'], 23)
        self.assertTrue(guards['auth_profile']['limit_plus_one_denied'])
        self.assertTrue(guards['fixture_closeout']['limit_plus_one_denied'])

    def test_all14_real_fault_selectors(self):
        cases = self.result['program']['cases']
        self.assertEqual(set(cases), {'normal', *self.cp.report['core_fault_cases'], *self.cp.report['bootstrap_fault_cases']})
        self.assertEqual(len(cases), 15)
        self.assertTrue(all(not r['bound_complete'] and r['refund'] == 0 for r in cases.values()))
        self.assertTrue(cases['timeout']['timeout_replaces_existing_dispatch'])
        self.assertEqual(cases['lost_response']['boundary']['edge'], 'after')
        self.assertEqual(cases['cleanup_failure']['boundary']['edge'], 'before')

    def test_every_fault_prefix_exact_retained_charges(self):
        events = self.cp.report['core_events']
        for name, case in self.result['program']['cases'].items():
            with self.subTest(case=name):
                prefix = events[:case['core_prefix_length']]
                groups = {e['charge_group']: e['cost'] for e in prefix if e['stage'] == 'precharge'}
                self.assertEqual(sum(groups.values()), case['core_declared_charged'])
                self.assertEqual(case['refund'], 0)
                self.assertEqual(self.result['program']['case_gates'][name]['decision'], 'DENY')
                self.assertEqual(self.result['program']['case_gates'][name]['core']['reason'], 'remaining_reserve_unknown')

    def test_all14_fault_truncations_are_not_fabricated_continuations(self):
        events = self.cp.report['core_events']
        for name, original in self.cp.report['core_fault_cases'].items():
            case = self.result['program']['cases'][name]
            index = case['core_prefix_length']
            with self.subTest(case=name):
                if 'before_event' in original:
                    self.assertEqual(events[index]['event_id'], original['before_event'])
                else:
                    self.assertEqual(events[index-1]['event_id'], original.get('after_event', original.get('case_event_id')))
                self.assertIsNone(case['total_local_ci_upper_bound'])
                self.assertFalse(case['admitted'])
        for name in self.cp.report['bootstrap_fault_cases']:
            self.assertEqual(self.result['program']['cases'][name]['core_prefix_length'], 0)

    def test_bootstrap_fault_cost_not_hidden_or_hosted_zero(self):
        cases = self.result['program']['cases']
        for name in ('pre_migration', 'post_migration'):
            self.assertEqual(cases[name]['closeout_direct_sql_reserved'], 4)
            self.assertEqual(cases[name]['closeout_docker_inventory_calls'], 1)
            self.assertIsNone(cases[name]['fresh_native_connection_upper_bound'])
            self.assertEqual(cases[name]['local_setup_hosted_projection'], 'NOT_APPLICABLE')

    def test_all_core_prefix_precharges_monotonic(self):
        prefixes = self.result['program']['prefixes']
        self.assertEqual(len(prefixes), len(self.cp.report['core_events']) + 1)
        self.assertEqual(prefixes[-1]['declared_charged'], 2340)
        self.assertEqual([p['declared_charged'] for p in prefixes], sorted(p['declared_charged'] for p in prefixes))

    def test_root_aliases_are_not_extra_charges(self):
        aliases = [r for r in self.result['coverage']['rows'] if r['id'].startswith('root:')]
        self.assertEqual(len(aliases), 13)
        self.assertTrue(all(r['alias_of'] and r['additive_charge'] is False for r in aliases))

    def test_recovery_retained_source_bound_not_added_twice(self):
        recovery = self.result['subprograms']['recovery']
        self.assertEqual(recovery['maxima']['explicit_sql_slots'], 8)
        self.assertEqual(recovery['maxima']['connection_open_attempts'], 1)
        self.assertEqual(recovery['maxima']['connection_close_attempts'], 5)
        self.assertFalse(recovery['additional_parent_charge'])
        self.assertIsNone(recovery['full_sql_upper_bound'])

    def test_current_recovery_original_functions_on_recorders(self):
        name = 'admission_budget_recovery_program.py'
        program_type = p.recovery_module(self.cp.source(name), self.cp.root/c.PREFIX/name)
        program = program_type(self.cp.root, self.cp.root/c.PREFIX/'quota_candidate_v1')
        for worker in ('absent', 'wait_unknown', 'kill_error'):
            trace = program.trace(worker=worker, watchdog='none' if worker == 'absent' else 'pending')
            self.assertLessEqual(trace['explicit_sql_slots'], 8)
            self.assertLessEqual(trace['connection_open_attempts'], 1)
            self.assertLessEqual(trace['connection_close_attempts'], 5)
            self.assertTrue(trace['original_failure_preserved'])
            self.assertFalse(trace['actual_execution_evidence'])

    def test_recovery_wait_and_save_failure_prefixes(self):
        name = 'admission_budget_recovery_program.py'
        program = p.recovery_module(self.cp.source(name), self.cp.root/c.PREFIX/name)(
            self.cp.root, self.cp.root/c.PREFIX/'quota_candidate_v1')
        normal = program.trace()
        targets = [i for i, r in enumerate(normal['events']) if r['kind'] in ('filesystem', 'process')]
        self.assertTrue(targets)
        for index in targets:
            for edge in ('before', 'after'):
                trace = program.trace(failure=index, edge=edge)
                self.assertTrue(trace['original_failure_preserved'])
                self.assertLessEqual(trace['explicit_sql_slots'], 8)

    def test_wal_not_admitted_by_five_commands(self):
        wal = self.result['coverage']['wal']
        self.assertEqual(wal['new_explicit_diagnostic_proposal'], 5)
        self.assertEqual(wal['statement_timeout_ms'], 5000)
        self.assertFalse(wal['new_probe_admitted'])
        self.assertFalse(wal['full_wal_coverage'])
        self.assertIsNone(wal['implicit_connection_bound'])

    def test_every_export_member_bounded_and_create_only(self):
        with tempfile.TemporaryDirectory(dir=c.HERE) as temporary:
            destination = pathlib.Path(temporary)/'fresh'
            receipt = c.export(ROOT, destination)
            for name, ref in receipt['files'].items():
                raw = (destination/(name+'.json')).read_bytes()
                self.assertLess(len(raw), 2_000_000)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), ref['sha256'])
            before = {p.name: p.read_bytes() for p in destination.iterdir()}
            with self.assertRaises(FileExistsError):
                c.export(ROOT, destination)
            self.assertEqual(before, {p.name: p.read_bytes() for p in destination.iterdir()})

    def test_changed_source_rejected(self):
        with tempfile.TemporaryDirectory(dir=c.HERE) as directory:
            path = pathlib.Path(directory)/'source.py'
            path.write_bytes(b'changed')
            isolated = object.__new__(c.Checkpoint)
            isolated.root = pathlib.Path(directory).resolve()
            with self.assertRaisesRegex(ValueError, 'source_changed'):
                isolated.read('source.py', '0'*64, 100)

    def test_source_path_escape_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source_path'):
            self.cp.read('../secret', '0'*64, 1)


class LedgerTests(unittest.TestCase):
    def test_unknown_reserve_denies_even_with_zero_charge(self):
        self.assertEqual(c.reserve_gate(0, None)['decision'], 'DENY')
        self.assertIsNone(c.reserve_gate(0, None)['required'])

    def test_numeric_reserve_never_grants_runtime_admission(self):
        self.assertEqual(c.reserve_gate(2338, 11)['decision'], 'ARITHMETIC_ONLY')
        self.assertEqual(c.reserve_gate(2338, 12)['decision'], 'DENY')
        with self.assertRaises(ValueError):
            c.reserve_gate(0, True)
        with self.assertRaises(ValueError):
            c.reserve_gate(0, 0, limit=2352)

    def ledger(self):
        return c.PrefixLedger([
            dict(event_id='reserve', charge_group='one', stage='precharge', cost=8, outcomes=['confirmed', 'rejected']),
            dict(event_id='dispatch', charge_group='one', stage='dispatch', cost=0, outcomes=['confirmed', 'lost_response']),
            dict(event_id='terminal', charge_group='one', stage='validation', cost=0, outcomes=['confirmed'])])

    def test_uncertain_dispatch_remains_consumed(self):
        ledger = self.ledger()
        ledger.advance('reserve')
        ledger.advance('dispatch', outcome='lost_response')
        receipt = ledger.advance('terminal')
        self.assertEqual(receipt['declared_charged'], 8)
        self.assertEqual(receipt['unknown_events'], ['dispatch'])
        self.assertIsNone(receipt['actual_sql_commands'])
        self.assertFalse(receipt['admitted'])

    def test_event_skip_and_replay_denied(self):
        ledger = self.ledger()
        with self.assertRaisesRegex(ValueError, 'event_order'):
            ledger.advance('dispatch')
        ledger.advance('reserve')
        with self.assertRaisesRegex(ValueError, 'event_order'):
            ledger.advance('reserve')

    def test_unknown_outcome_denied(self):
        with self.assertRaisesRegex(ValueError, 'event_outcome'):
            self.ledger().advance('reserve', outcome='PASS')

    def test_duplicate_charge_group_denied(self):
        ledger = self.ledger()
        ledger.events = [ledger.events[0], dict(ledger.events[0], event_id='again')]
        ledger.advance('reserve')
        with self.assertRaisesRegex(ValueError, 'charge_group_replay'):
            ledger.advance('again')


if __name__ == '__main__':
    unittest.main(verbosity=2)
