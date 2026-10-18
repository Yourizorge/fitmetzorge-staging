import copy,pathlib,unittest
import history_pin as h

class HistoryTests(unittest.TestCase):
    def test_both_independent_pins_and_sources(self):
        for env,key in [('staging','staging'),('disposable_ci','disposable')]:
            rows=h.load()['history'][key]
            self.assertEqual(h.validate(rows,env)['prior_migrations'],44)
            self.assertFalse(h.validate(rows+[{'version':'candidate'}],env)['cross_environment_equivalence_claimed'])
    def test_wrong_environment_cannot_normalize_history(self):
        with self.assertRaisesRegex(ValueError,'historical_migration_drift'):
            h.validate(h.load()['history']['staging'],'disposable_ci')
        with self.assertRaisesRegex(ValueError,'environment_unbound'):
            h.validate(h.load()['history']['staging'],'browser')
    def test_every_old_sql_hash_name_and_version_fail_closed(self):
        for index in range(44):
            for field in ('version','name','sql_sha'):
                rows=copy.deepcopy(h.load()['history']['staging']);rows[index][field]='changed'
                with self.assertRaisesRegex(ValueError,'historical_migration_drift'):h.validate(rows,'staging')

if __name__=='__main__':unittest.main()
