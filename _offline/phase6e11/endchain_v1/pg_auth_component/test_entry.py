"""Pure entry scope/inventory checks; no platform or network dispatch."""
from pathlib import Path
import unittest
from unittest.mock import patch
from . import entry as m, inventory, prepare
from .test_resume import ResumeTests

ENV={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging',
     'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'123','GITHUB_REF':'refs/heads/main',
     'GITHUB_RUN_ATTEMPT':'1','CANDIDATE_BLOB':'b'*40,'CANDIDATE_SHA256':'c'*64,
     'GITHUB_WORKSPACE':'/checkout','RUNNER_TEMP':'/temp','PATH':'/usr/bin:/bin','HOME':'/home/runner'}


class EntryTests(unittest.TestCase):
    def admit(self, env):
        with patch.object(m.sys,'platform','linux'),patch.object(m.sys,'version_info',(3,12)):
            return m.environment(env)

    def test_exact_local_ci(self):self.admit(ENV)

    def test_hosted_repository_denied(self):
        with self.assertRaises(ValueError):self.admit({**ENV,'GITHUB_REPOSITORY':'other/repo'})

    def test_second_attempt_denied(self):
        with self.assertRaises(ValueError):self.admit({**ENV,'GITHUB_RUN_ATTEMPT':'2'})

    def test_nonlinux_denied(self):
        with patch.object(m.sys,'platform','win32'):
            with self.assertRaises(ValueError):m.environment(ENV)

    def test_missing_source_sha_denied(self):
        with self.assertRaises(ValueError):self.admit({**ENV,'GITHUB_SHA':''})

    def test_fresh_child_environment_no_secrets(self):
        result=m.resumed_environment({**ENV,'GH_READ_TOKEN':'PRIVATE_REVIEW_SENTINEL',
                                     'PGPASSWORD':'PRIVATE_REVIEW_SENTINEL','PYTHONPATH':'/untrusted'})
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',str(result))
        self.assertNotIn('PYTHONPATH',result)

    def test_every_owned_source_exists(self):
        root=Path(__file__).resolve().parents[4]
        for name in inventory.OWN:self.assertTrue((root/name).is_file(),name)

    def test_lifecycle_all_producers_in_explicit_inventory(self):
        for name in ('context','lifecycle','scope','subset','parent','worker','pg_worker'):
            self.assertIn(inventory.PREFIX+'pg_auth_component/'+name+'.py',inventory.OWN)

    def test_workflow_separate_not_endchain(self):
        root=Path(__file__).resolve().parents[4]
        raw=(root/inventory.WORKFLOW).read_text()
        self.assertIn('pg_auth_component/entry.py',raw)
        self.assertNotIn('supabase link',raw)
        self.assertNotIn('workflow_run:',raw)

    def test_prepare_overlay_only_explicit_owned_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            checkout=Path(folder)/'checkout';overlay=Path(folder)/'overlay'
            checkout.mkdir();overlay.mkdir()
            name=inventory.PREFIX+'pg_auth_component/entry.py'
            for root in (checkout,overlay):
                (root/name).parent.mkdir(parents=True)
                (root/name).write_bytes(b'unit source')
                (root/'external.py').write_bytes(b'unit external')
            self.assertEqual(prepare.source_path(checkout,overlay,name),overlay/name)
            self.assertEqual(prepare.source_path(checkout,overlay,'external.py'),checkout/'external.py')
            with self.assertRaises(ValueError):prepare.source_path(checkout,overlay,'../external.py')

    def test_pinned_driver_and_both_launches_use_exact_private_venv(self):
        root=Path(__file__).resolve().parents[4]
        raw=(root/inventory.WORKFLOW).read_text()
        python='"$RUNNER_TEMP/fmz-pg-auth-component-venv/bin/python"'
        self.assertIn('python3 -m venv "$RUNNER_TEMP/fmz-pg-auth-component-venv"',raw)
        self.assertIn(python+' -I -m pip install',raw)
        self.assertIn(python+' -B -m unittest',raw)
        self.assertIn(python+' -B _offline/phase6e11/endchain_v1/pg_auth_component/entry.py',raw)
        self.assertIn('psycopg[binary]==3.2.10',raw);self.assertIn('pglast==7.20',raw)
        self.assertNotIn('python3 -m pip install',raw)
        self.assertNotIn('--break-system-packages',raw)
        self.assertIn('os.execve(sys.executable, [sys.executable',Path(m.__file__).read_text())
        from . import worker
        self.assertIn('sys.executable',Path(worker.__file__).read_text())


if __name__=='__main__':unittest.main()
