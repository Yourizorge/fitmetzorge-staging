"""Extract the CI routing methods only; never construct a live CI gate."""
import ast,hashlib,json,pathlib,types,unittest
from cli_envelope import local

HERE=pathlib.Path(__file__).resolve().parent

def receipt(slot):
    return local(dict(protocol_commands=2,complete=True,numeric_protocol_coverage=True,
                      observer_commands=[{'confirmed':True}]*8,dry_run=slot!='quota'),slot)

def routing_gate():
    tree=ast.parse((HERE/'ci.py').read_text())
    klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Gate')
    methods=[n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name in ('cli','reset_registered_cli')]
    body=ast.ClassDef(name='Gate',bases=[],keywords=[],body=methods,decorator_list=[])
    scope={'hashlib':hashlib,'json':json};exec(compile(ast.fix_missing_locations(ast.Module(body=[body],type_ignores=[])),'ci-routing-only','exec'),scope)
    gate=scope['Gate']();gate.result={'commit':'a'*40};gate.evidence_prefix='';gate.reset_registered_cli()
    gate.calls=[]
    def isolated(args,timeout):
        gate.calls.append((args,timeout))
        gate.cli_protocol.append(receipt(('quota','pre_auth','final')[len(gate.cli_protocol)]))
        return types.SimpleNamespace(stdout='up to date',stderr='')
    gate.isolated_cli=isolated
    return gate

class CiSequenceTests(unittest.TestCase):
    def test_stale_final_cannot_skip_new_pre_auth(self):
        gate=routing_gate();gate.final_dry_run=object();gate.cli_protocol=[receipt('quota')]
        gate.cli('db','push','--local','--dry-run','--skip-vault')
        self.assertEqual(len(gate.calls),1)
        self.assertEqual([r['slot'] for r in gate.cli_protocol],['quota','pre_auth'])
    def test_only_exact_same_completed_final_is_reused(self):
        gate=routing_gate();gate.cli_protocol=[receipt('quota'),receipt('pre_auth')]
        args=('db','push','--local','--dry-run','--skip-vault')
        result=gate.cli(*args)
        self.assertIs(gate.cli(*args),result)
        self.assertEqual(len(gate.calls),1)
        self.assertEqual(gate.calls[0][1],45)
        self.assertEqual(gate.final_dry_cache['key'][0],gate.result['commit'])
        gate.reset_registered_cli();gate.cli_protocol=[receipt('quota')]
        gate.cli(*args)
        self.assertEqual(len(gate.calls),2)
        self.assertEqual(gate.cli_protocol[-1]['slot'],'pre_auth')
    def test_namespace_change_never_reuses_prior_result(self):
        gate=routing_gate();gate.cli_protocol=[receipt('quota'),receipt('pre_auth')]
        args=('db','push','--local','--dry-run','--skip-vault')
        gate.cli(*args);gate.evidence_prefix='fault-before_call-'
        def denied(*args):raise ValueError('new_cli_required')
        gate.isolated_cli=denied
        with self.assertRaisesRegex(ValueError,'new_cli_required'):gate.cli(*args)
    def test_mutated_receipt_is_not_valid_cache(self):
        gate=routing_gate();gate.cli_protocol=[receipt('quota'),receipt('pre_auth')]
        args=('db','push','--local','--dry-run','--skip-vault')
        gate.cli(*args)
        gate.cli_protocol[-1]['protocol_commands']=3
        with self.assertRaisesRegex(RuntimeError,'cache_changed'):gate.cli(*args)
    def test_changed_commit_never_reuses_old_cache(self):
        gate=routing_gate();gate.cli_protocol=[receipt('quota'),receipt('pre_auth')]
        args=('db','push','--local','--dry-run','--skip-vault')
        gate.cli(*args);gate.result['commit']='b'*40
        def denied(*args):raise ValueError('new_cli_required')
        gate.isolated_cli=denied
        with self.assertRaisesRegex(ValueError,'new_cli_required'):gate.cli(*args)
    def test_invalid_source_cannot_reuse_cache_or_dispatch(self):
        for result in ({},{'head':'a'*40},{'commit':'a'*40,'head':'b'*40}):
            gate=routing_gate();gate.cli_protocol=[receipt('quota'),receipt('pre_auth')]
            args=('db','push','--local','--dry-run','--skip-vault')
            gate.cli(*args);gate.result=result
            with self.subTest(result=result),self.assertRaisesRegex(ValueError,'source_'):gate.cli(*args)
            self.assertEqual(len(gate.calls),1)
    def test_agreeing_head_alias_keeps_canonical_commit_cache(self):
        gate=routing_gate();gate.cli_protocol=[receipt('quota'),receipt('pre_auth')]
        args=('db','push','--local','--dry-run','--skip-vault')
        result=gate.cli(*args)
        gate.result['head']=gate.result['commit']
        self.assertIs(gate.cli(*args),result)
        self.assertEqual(len(gate.calls),1)
    def test_three_slots_and_final_post_source_checks_are_wired(self):
        tree=ast.parse((HERE/'ci.py').read_text())
        klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Gate')
        profile=next(n for n in klass.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cli_profile' for t in n.targets))
        self.assertEqual(ast.literal_eval(profile.value),'endchain')
        for name in ('fetch','advisors'):
            method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='verify_all' for n in ast.walk(method)),1)
        names=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NAMES' for t in n.targets))
        for name in ('test_final_gates.py','test_ci_cli_sequence.py'):self.assertIn(name,ast.literal_eval(names))

if __name__=='__main__':unittest.main()
