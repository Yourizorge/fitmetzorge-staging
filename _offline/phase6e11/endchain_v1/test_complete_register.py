import unittest
from complete_register import safety_path,reserve_prefixes,Escrow,classify,RUN_ID,PURPOSE

class RegisterTests(unittest.TestCase):
    def test_every_prefix_keeps_remaining_cleanup(self):
        rows=[{'sql':1,'phase':'setup','state_after':{'guard':True,'observer':True,'controls':True,'claimed':True}}]
        rows += [{'sql':1,'phase':'route_a'} for _ in range(600)]
        rows += [{'sql':1,'phase':'cleanup'} for _ in range(338)]
        rows += [{'sql':1,'phase':'final'} for _ in range(100)]
        prefixes=reserve_prefixes(rows)
        self.assertEqual(len(prefixes),len(rows)+1)
        for i,p in enumerate(prefixes):
            expected=sum(r['sql'] for r in rows[i:] if r['phase'] in ('cleanup','final','closure'))
            self.assertGreaterEqual(p['reserve'],expected)
            self.assertGreaterEqual(p['reserve'],sum(x['sql'] for x in p['path']))
    def test_safety_has_no_retry_or_fixture_deletion(self):
        path=safety_path(True,True,True,True)
        self.assertEqual(sum(x['sql'] for x in path),29)
        self.assertFalse(any(x['retry'] for x in path))
        self.assertFalse(any('fixture' in x['action'] for x in path))
        self.assertEqual(sum(x['sql'] for x in safety_path()),9)
    def test_missing_unknown_phase_is_not_zero_cost(self):
        with self.assertRaises(ValueError):classify({'phase':'unknown'},[])
    def test_cleanup_includes_its_evidence_io_and_auth(self):
        for phase in ('controller_evidence','measurement','io_sample','call'):
            self.assertEqual(classify({'phase':phase,'action':{'kind':'workflow','step':45}},[]),'cleanup')
        self.assertEqual(classify({'phase':'evidence_query','action':{'kind':'auth','operation':'logout'}},[]),'cleanup')
    def test_managed_or_extra_queries_cannot_hide_overrun(self):
        with self.assertRaises(ValueError):Escrow({'run_id':RUN_ID,'purpose':PURPOSE,'complete_register':True,'fits':True,'worst_including_safety':2227})
        with self.assertRaises(ValueError):Escrow({'complete_register':False,'fits':True,'worst_including_safety':1})
    def test_active_guard_extends_reserve(self):
        before=reserve_prefixes([{'phase':'guard','sql':1,'state_after':{'guard':True}}])
        self.assertEqual(before[1]['emergency_sql']-before[0]['emergency_sql'],7)
    def test_every_prefix_blocks_when_cleanup_cannot_fit(self):
        rows=[{'sql':1,'phase':'cleanup'} for _ in range(2221)]
        register={'run_id':RUN_ID,'purpose':PURPOSE,'complete_register':True,'fits':True,'worst_including_safety':2226,'rows':rows,'prefixes':reserve_prefixes(rows)}
        executor=Escrow(register)
        for _ in range(2217):executor.charge()
        with self.assertRaises(ValueError):executor.charge()

if __name__=='__main__':unittest.main()
