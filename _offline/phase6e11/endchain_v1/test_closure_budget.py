"""Role C offline regressions. Passing tests do not admit a hosted run."""
import json
import unittest

import closure_budget as audit
from complete_register import safety_path
from runtime_budget import BudgetStop


class AccountingTests(unittest.TestCase):
    def event(self, **changes):
        return dict(event_id='native_1', phase='baseline', kind='native',
                    reserved_commands=1, observed_commands=1, confirmed=True, **changes)

    def test_protocol_auth_cli_are_disjoint(self):
        events = [self.event(), {'event_id': 'auth_1', 'phase': 'auth',
            'kind': 'managed_auth', 'reserved_commands': 11,
            'observed_commands': 11, 'confirmed': True},
            {'event_id': 'cli_quota', 'phase': 'migration', 'kind': 'cli',
             'reserved_commands': 64, 'observed_commands': 14, 'confirmed': True}]
        result = audit.account(events)
        self.assertEqual(result['reserved_commands'], 76)
        self.assertEqual(result['confirmed_observed_by_kind'],
                         {'native': 1, 'managed_auth': 11, 'cli': 14})
        self.assertFalse(result['hosted_admitted'])

    def test_duplicate_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_event'):
            audit.account([self.event(), self.event()])

    def test_unknown_outcome_keeps_whole_reservation(self):
        event = self.event()
        event.update(kind='managed_auth', phase='auth', reserved_commands=27,
                     observed_commands=None, confirmed=False)
        result = audit.account([event])
        self.assertEqual(result['reserved_commands'], 27)
        self.assertEqual(result['confirmed_observed_by_kind'], {})
        self.assertFalse(result['all_emitted_counts_known'])

    def test_unknown_cli_is_never_an_observed_count(self):
        event = self.event()
        event.update(kind='cli', phase='migration', reserved_commands=64,
                     observed_commands=None, confirmed=False)
        result = audit.account([event])
        self.assertEqual(result['reservations_by_kind'], {'cli': 64})
        self.assertEqual(result['confirmed_observed_by_kind'], {})

    def test_bad_or_missing_attribution_fails_closed(self):
        changes = [{'event_id': ''}, {'phase': 'unregistered'}, {'kind': 'HTTP'},
                   {'confirmed': True, 'observed_commands': None},
                   {'reserved_commands': True}, {'observed_commands': -1},
                   {'observed_commands': 2}, {'confirmed': None}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                event = self.event()
                event.update(change)
                audit.account([event])

    def test_over_ceiling_fails_closed(self):
        event = self.event()
        event.update(reserved_commands=2350, observed_commands=2350)
        with self.assertRaisesRegex(ValueError, 'authorized_ceiling'):
            audit.account([event])

    def test_bootstrap_is_separate_and_still_requires_unique_evidence(self):
        event = self.event()
        event['phase'] = 'ci_bootstrap'
        self.assertEqual(audit.account([event])['reserved_commands'], 0)
        with self.assertRaises(ValueError):
            audit.account([event, event])


class CapacityTests(unittest.TestCase):
    def test_initial_reserve_and_unchanged_limits(self):
        m = audit.meter()
        self.assertEqual(m._reserve(m.phases, m.state), 731)
        self.assertEqual(sum(m.limits.values()), 2338)
        self.assertEqual(m.limit, 2349)

    def test_all_required_failure_categories_are_explicit(self):
        self.assertEqual(set(audit.CASES), {'normal', 'pre_migration', 'post_migration',
            'auth', 'controller', 'route_a', 'route_b', 'restore', 'lost_response',
            'duplicate', 'timeout', 'partial_cleanup'})

    def test_normal_capacity_is_not_emitted_sql(self):
        result = audit.capacity_probe('normal')
        self.assertEqual(result['reserved_used'], 2338)
        self.assertEqual(result['emitted_sql'], 0)
        self.assertFalse(result['hosted_admitted'])

    def test_every_failure_category_stops_new_work_and_keeps_suffix_budget(self):
        for case in audit.CASES[1:]:
            with self.subTest(case=case):
                result = audit.capacity_probe(case)
                self.assertTrue(result['dependent_action_denied'])
                self.assertLessEqual(result['safety_reserved'], result['reserve_at_stop'])
                self.assertLessEqual(result['reserved_used'], 2349)
                self.assertEqual(result['emitted_sql'], 0)
                self.assertFalse(result['database_cleanup_proven'])

    def test_terminal_claimed_suffix_reaches_2349_without_raising_it(self):
        m = audit.meter()
        for phase, cost in m.limits.items():
            ticket = m.charge(phase, cost, action=phase, mutation=True,
                              state_after={'claimed': True})
            m.confirm(ticket)
        m.stop('terminal_failure')
        for row in safety_path(**m.state):
            ticket = m.safety(row['action'], row['sql'], kind=row['kind'])
            m.confirm_safety(ticket)
        self.assertEqual(m.used, 2349)
        with self.assertRaises(BudgetStop):
            m.safety('rollback_writer', 1)

    def test_lost_multi_statement_response_is_unconfirmed_capacity(self):
        c = audit.MeteredComposition()
        c.before_sql('guard_install', 'BEGIN; SELECT 1; COMMIT')
        c.abort('lost_response')
        self.assertEqual(c.meter.used, 3)
        self.assertEqual(len(c.commands), 3)
        self.assertTrue(all(not row['confirmed'] for row in c.commands))
        self.assertFalse(c.meter.receipt()['complete'])

    def test_timeout_does_not_extend_ordinary_or_safety_window(self):
        now = [0]
        m = audit.RuntimeBudget(audit.capacity(), run_id=audit.RUN_ID,
                                purpose=audit.PURPOSE, clock=lambda: now[0])
        now[0] = 540
        with self.assertRaisesRegex(BudgetStop, 'ordinary_deadline'):
            m.charge('auth', 1, action='late')
        ticket = m.safety('rollback_writer', 1)
        m.confirm_safety(ticket)
        now[0] = 600
        with self.assertRaisesRegex(BudgetStop, 'safety_deadline'):
            m.safety('rollback_reader', 1)

    def test_partial_cleanup_cannot_replay_removal(self):
        c = audit.MeteredComposition()
        c.meter.state['guard'] = True
        c.abort('partial_cleanup')
        c.safety_label = 'guard_exact_remove'
        text = 'BEGIN; SELECT 1; SELECT 2; SELECT 3; COMMIT'
        c.before_sql('remove', text)
        self.assertEqual(c.meter.used, 5)
        with self.assertRaisesRegex(ValueError, 'removal_replay'):
            c.before_sql('remove', text)
        self.assertTrue(c.meter.state['guard'])
        self.assertFalse(c.meter.receipt()['complete'])


class ExecutorAuditTests(unittest.TestCase):
    def test_failure_runner_anchor_survives_signature_and_loop_changes(self):
        source='def run(gate, *, selection=None, diagnostic_only=False):\n    return None\n'
        with audit.patch.object(audit.pathlib.Path,'read_text',return_value=source):
            location=audit.anchor('integral_failures.py','function:run')
        self.assertEqual(location['line'],1)
        self.assertEqual(len(location['sha256']),64)

    def test_actual_executor_attributes_each_protocol_statement(self):
        for case in ('controller', 'route_a', 'route_b', 'restore', 'partial_cleanup'):
            with self.subTest(case=case):
                result = audit.protocol_probe(case)
                phase = 'cleanup' if case == 'partial_cleanup' else case
                self.assertEqual(result['phase_bookings'], {phase: 3})
                self.assertEqual(result['booked_protocol_statements'], 3)

    def test_worker_precharge_is_capacity_not_emission(self):
        result = audit.workflow_precharge_probe()
        self.assertEqual(result['precharged_managed_capacity'], 360)
        self.assertEqual(result['precharged_cleanup_auth'], 130)
        self.assertEqual(result['unconfirmed_managed_tickets'], 72)
        self.assertEqual(result['reserved_cleanup_before'], 731)
        self.assertEqual(result['reserved_cleanup_after'], 601)
        self.assertEqual(result['emitted_sql'], 0)

    def test_parent_timeout_joins_before_auth_then_removes_owned_objects_without_auth_zero(self):
        result = audit.worker_abort_probe()
        self.assertEqual(result['events'], ['kill', 'joined', 'parent_auth', 'remove_owned_objects'])
        self.assertTrue(result['auth_maybe_live'])
        self.assertEqual(result['parent_auth_suffix_calls'], 1)
        self.assertTrue(result['parent_received_terminated'])
        self.assertTrue(result['owned_objects_removed'])
        self.assertFalse(result['worker_complete'])

    def test_first_control_response_loss_restores_current_source(self):
        result = audit.control_loss_probe(1)
        self.assertEqual(result['calls'].count('safety_control_restore'),2)
        self.assertFalse(result['config_still_enabled'])
        self.assertFalse(result['request_still_enabled'])

    def test_second_control_response_loss_restores_known_expiry(self):
        result = audit.control_loss_probe(2)
        self.assertIn('safety_control_restore', result['calls'])
        self.assertFalse(result['config_still_enabled'])
        self.assertFalse(result['request_still_enabled'])

    def test_repeated_labels_create_distinct_charges_not_reusable_confirmations(self):
        m = audit.meter()
        tickets=[]
        for _ in range(2):
            ticket = m.charge('route_a', 1, action='same_request')
            tickets.append(ticket)
            m.confirm(ticket)
        self.assertNotEqual(*tickets)
        with self.assertRaises(audit.BudgetStop):m.confirm(tickets[0])
        self.assertEqual(m.used, 2)
        self.assertEqual([r['action'] for r in m.events], ['same_request'] * 2)

    def test_preflight_failure_dispatches_are_precharged(self):
        result = audit.preflight_failure_probe()
        self.assertEqual(result['memory_driver_dispatches'], 3)
        self.assertEqual(result['runtime_booked'], 3)
        self.assertEqual(result['phase_bookings'], {'preflight': 2})
        self.assertEqual(result['safety_bookings'], {'rollback_reader': 1})
        self.assertFalse(result['receipt_complete'])
        self.assertTrue(result['connection_closed'])
        self.assertTrue(result['receipt_saved'])

    def test_preflight_rollback_error_still_closes_and_saves_receipt(self):
        result = audit.preflight_failure_probe(True)
        self.assertEqual(result['memory_driver_dispatches'], 3)
        self.assertEqual(result['runtime_booked'], 3)
        self.assertTrue(result['connection_closed'])
        self.assertTrue(result['receipt_saved'])
        self.assertFalse(result['receipt_complete'])

    def test_unknown_protocol_phase_is_not_silently_free(self):
        c = audit.MeteredComposition()
        with self.assertRaisesRegex(ValueError, 'unclassified'):
            c.before_sql('unregistered_protocol', 'SELECT 1')
        self.assertEqual(c.meter.used, 0)

    def test_historical_stop_is_not_full_chain_evidence(self):
        result = audit.historical_stop()
        self.assertEqual(result['trace_entries'], 52)
        self.assertEqual(result['classified_trace'], {'ci_bootstrap': 16, 'baseline': 36})
        self.assertEqual(result['runtime_booked'], 40)
        self.assertFalse(result['full_chain_complete'])

    def test_report_is_source_bound_and_never_admits(self):
        report = audit.report()
        self.assertFalse(report['hosted_admitted'])
        self.assertFalse(report['limits']['worst_case_full_executor_proven'])
        self.assertEqual(len(report['failure_matrix']), 12)
        self.assertEqual(len(report['current_findings']), 10)
        self.assertEqual({r['id'] for r in report['blocking_findings']},{'C03','C04','C05','C06','C07','C09'})
        statuses={r['id']:r['status'] for r in report['current_findings']}
        for ident in ('C01','C02','C10'):self.assertEqual(statuses[ident],'locally_corrected')
        self.assertEqual(statuses['C08'],'not_demonstrated_bug')
        self.assertEqual(report['historical_observations']['sha256'],
            'cd2e7697026612700636d4d2adbd96702409cd29f17972fcba65c198ad4d503a')
        for item in report['current_findings']:
            self.assertGreater(item['source']['line'], 0)
            self.assertEqual(len(item['source']['sha256']), 64)
        self.assertEqual(report['accounting']['auth_matrix_expected_capacity'], 234)
        self.assertEqual(report['accounting']['cli_unknown_reserved_capacity'], 120)
        json.dumps(report)


if __name__ == '__main__':
    unittest.main()
