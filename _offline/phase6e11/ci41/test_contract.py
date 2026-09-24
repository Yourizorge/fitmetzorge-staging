import importlib.util, json, pathlib, tempfile, unittest
import fixture_compat
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("runner",HERE/"runner.py")
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
class Contract(unittest.TestCase):
    def test_advisor_wrapper_separates_unterminated_upstream_query(self):
        sql=runner.advisor_sql(b'select 1')
        self.assertTrue(sql.startswith('begin read only;'))
        self.assertTrue(sql.endswith('select 1;\nrollback;'))
    def test_advisor_wrapper_accepts_already_terminated_query(self):
        self.assertTrue(runner.advisor_sql(b'select 1;').endswith('select 1;;\nrollback;'))
    def test_6a_fixture_is_additive_and_retains_every_original_assertion(self):
        raw=(HERE.parents[2]/'supabase/tests'/fixture_compat.NAME).read_bytes()
        sql,changed=fixture_compat.adapt(fixture_compat.NAME,raw)
        self.assertTrue(changed)
        self.assertEqual(sql.replace(fixture_compat.ADDITION,'',1),raw.decode())
        self.assertIn("if sqlerrm <> 'ai_consent_or_access_changed' then raise",sql)
        self.assertIn("'private_chat','granted','phase6d-private-chat-v1'",sql)
    def test_changed_historical_fixture_is_not_silently_adapted(self):
        with self.assertRaisesRegex(RuntimeError,'historical_6a_fixture_source_changed'):
            fixture_compat.adapt(fixture_compat.NAME,b'select 1;')
    def test_other_fixtures_are_not_adapted(self):
        self.assertEqual(fixture_compat.adapt('other.sql',b'select 1;'),('select 1;',False))
    def test_allowed_sources(self):
        self.assertTrue(runner.allowed("supabase/migrations/"+runner.M41))
        self.assertTrue(runner.allowed("supabase/tests/20260901_example.sql"))
        self.assertTrue(runner.allowed("_offline/phase6e11/readiness_v1/txaudit/test_audit.py"))
    def test_no_other_sources(self):
        for name in ("../secret","supabase/.temp/before.json",".env","app.js",
                     "supabase/migrations/../../secret.sql","supabase/functions/real.ts"):
            self.assertFalse(runner.allowed(name),name)
    def test_redaction(self):
        text="eyJabc.def.ghi postgresql://name:private@host/db sb_secret_ABC123 ghp_secretvalue"
        out=runner.clean(text)
        for part in ("eyJabc","private@","sb_secret_ABC","ghp_secret"):
            self.assertNotIn(part,out)
    def test_scope_rejected_before_write(self):
        with patch.dict(runner.os.environ,{"GITHUB_REPOSITORY":"forbidden/repo"}):
            with self.assertRaisesRegex(RuntimeError,"repository_boundary"):runner.Gate()
    def test_branch_rejected_before_write(self):
        with patch.dict(runner.os.environ,{"GITHUB_REPOSITORY":"Yourizorge/fitmetzorge-staging","GITHUB_REF":"refs/heads/other"}):
            with self.assertRaisesRegex(RuntimeError,"branch_boundary"):runner.Gate()
    def test_exact_candidate_hash(self):
        root=HERE.parents[2]
        data=(root/"supabase/migrations"/runner.M41).read_bytes()
        self.assertEqual(runner.sha(data),runner.M41_SHA)
    def test_failure_stops_all_later_gates_and_saves_no_go(self):
        gate=object.__new__(runner.Gate);gate.result={"status":"NO_GO"}
        seen=[]
        gate.fetch=lambda:["candidate"]
        gate.install=lambda:None
        def fail(migrations):raise RuntimeError("migration_4_failed")
        gate.rebuild=fail
        gate.check_bridge=lambda:seen.append("unsafe_continue")
        gate.regressions=lambda:seen.append("unsafe_continue")
        gate.advisors=lambda:seen.append("unsafe_continue")
        gate.save=lambda name,value:seen.append((name,dict(value)))
        self.assertEqual(gate.run(),1)
        self.assertEqual(len(seen),1)
        self.assertEqual(seen[0][1]["status"],"NO_GO")
        self.assertEqual(seen[0][1]["error"],"migration_4_failed")
    def test_evidence_cannot_overwrite(self):
        gate=object.__new__(runner.Gate)
        with tempfile.TemporaryDirectory(prefix="fmz-ci41-contract-") as tmp:
            gate.out=pathlib.Path(tmp)
            gate.save("evidence.json",{"original":True})
            with self.assertRaises(FileExistsError):gate.save("evidence.json",{"original":False})
            self.assertEqual(json.loads((gate.out/"evidence.json").read_text()),{"original":True})
    def test_workflow_no_credentials_or_automatic_triggers(self):
        text=(HERE.parents[2]/".github/workflows/phase6e11-db41.yml").read_text()
        self.assertIn("workflow_dispatch:",text)
        self.assertIn("runs-on: ubuntu-24.04",text)
        self.assertIn("contents: read",text)
        self.assertIn("persist-credentials: false",text)
        for forbidden in ("secrets.","pull_request:","push:","schedule:","upload-artifact","cache@","self-hosted"):
            self.assertNotIn(forbidden,text)
if __name__=="__main__":unittest.main()
