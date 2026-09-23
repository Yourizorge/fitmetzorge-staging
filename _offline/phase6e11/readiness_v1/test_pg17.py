"""Additional PG17 tests; all data is synthetic and every cluster is retained/stopped."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'fingerprint_v1'))
from local_cluster import Cluster
from fingerprint import configure, ROW_HASH
from guard import Stop

class PG17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster=Cluster()
        cls.db=cls.cluster.start()
        cls.version=cls.db.query("select current_setting('server_version_num')")[0][0]
        if cls.version!='170006':
            cls.db.close();cls.cluster.stop()
            raise Stop('exact_PG17_6_required')
    @classmethod
    def tearDownClass(cls):
        cls.db.close();cls.cluster.stop()

    def one(self):
        return self.db.query("select "+ROW_HASH+" from (select 1.2345678901234567::float8 f, '2026-03-29 01:30:00+00'::timestamptz stamp) t")[0][0]

    def test_observed_staging_float_setting_is_not_silently_equated(self):
        configure(self.db)
        self.db.query("select set_config('extra_float_digits','0',true)")
        old=self.one()
        self.db.query("select set_config('extra_float_digits','3',true)")
        new=self.one()
        self.db.query('commit')
        self.assertNotEqual(old,new)

    def test_ambient_staging_settings_are_pinned(self):
        outputs=[]
        for zone,style,float_digits in [('UTC','ISO, MDY','0'),('Europe/Amsterdam','German, DMY','2')]:
            self.db.query("select set_config('TimeZone','"+zone+"',false),set_config('DateStyle','"+style+"',false),set_config('extra_float_digits','"+float_digits+"',false)")
            configure(self.db);outputs.append(self.one());self.db.query('commit')
        self.assertEqual(outputs[0],outputs[1])

if __name__=='__main__':unittest.main()
