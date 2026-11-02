"""Offline ZIP binding checks; synthetic fixtures are never a real CI PASS."""
import builtins,copy,hashlib,io,json,os,pathlib,runpy,stat,tempfile,types,unittest,warnings,zipfile
from unittest.mock import Mock,patch
import closure_ops as c

def raw(value):return json.dumps(value,sort_keys=True).encode()
def digest(value):return hashlib.sha256(value).hexdigest()

class Tests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        self.root=pathlib.Path(folder.name)

    def values(self):
        chain={'status':'CLEAN_CI_PASS','full_chain_admission':True,'commit':'a'*40,'run_id':'42'}
        app={'status':'CLEAN_CI_PASS','migrations_applied':47,'dry_run':'EMPTY',
            'member_data_used':False,'external_ai_calls':0,'hosted_requests':0,
            'commit':'a'*40,'run_id':'42'}
        return chain,app,{'shared':'b'*64},{'shared':'b'*64}

    def fixture(self,kind):
        folder=self.root/kind;folder.mkdir()
        sources={}
        for name in sorted(c.APP_PROOF_SOURCES|{'shared.py'}):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b'# synthetic fixture, not executed\n');sources[name]=digest(path.read_bytes())
        payloads={name:raw({'unit_fixture':True}) for name in (c.APP_PROOFS if kind=='app' else c.CHAIN_PROOFS)}
        payloads['candidate.json']=raw({'sources':sources})
        payloads['result.json']=raw(self.values()[1 if kind=='app' else 0])
        if kind=='app':
            payloads['123-release-security.json']=raw({'exitcode':0,'phase':'regressions','stderr':'unit fixture'})
            payloads['release-train.json']=raw({'format':'fmz-release-train-v1',
                'status':'LOCAL_SOURCE_BOUND_MANIFEST_NOT_RELEASED'})
        else:
            payloads['complete-command-register.json']=raw({'unit_fixture':True,'total':2349})
        self.package(folder,kind,payloads)
        return folder,payloads,sources

    def package(self,folder,kind,payloads,manifest=None,entries=None,embedded_manifest=None):
        manifest=manifest if manifest is not None else {name:digest(data) for name,data in payloads.items()}
        manifest_raw=raw(manifest) if embedded_manifest is None else embedded_manifest
        entries=list(payloads.items()) if entries is None else entries
        buffer=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(buffer,'w') as archive:
                for name,data in entries:archive.writestr(name,data)
                archive.writestr('artifact-manifest.json',manifest_raw)
        for name,data in payloads.items():c.disk(folder/name).write_bytes(data)
        c.disk(folder/'artifact-manifest.json').write_bytes(manifest_raw)
        c.disk(folder/'evidence.zip').write_bytes(buffer.getvalue())
        self.collection(folder,kind)

    def collection(self,folder,kind):
        c.disk(folder/'collection.json').write_bytes(raw({'head':'a'*40,'run':42,
            'archive_sha256':digest(c.disk(folder/'evidence.zip').read_bytes()),
            'verified':kind=='app','all_file_hashes_valid':kind=='chain'}))

    def fake_admission(self,folder,**kwargs):
        read=lambda name:json.loads(c.disk(folder/name).read_bytes())
        return {'head':'a'*40,'ci_run':'42','sources':read('candidate.json')['sources'],
            'archive_sha256':read('collection.json')['archive_sha256'],
            'register':read('complete-command-register.json')}

    def test_requires_both_real_gate_results(self):
        result=c.compare_results(*self.values())
        self.assertFalse(result['hosted_admitted']);self.assertFalse(result['package21_released'])
        self.assertFalse(result['owner_accepted'])

    def test_incomplete_gate_never_composes(self):
        for side,key,value in ((0,'full_chain_admission',False),(0,'status','NO_GO'),
                (1,'status','NO_GO'),(1,'migrations_applied',45),(1,'dry_run','PENDING'),
                (1,'member_data_used',True),(1,'external_ai_calls',1),(1,'hosted_requests',1)):
            args=list(self.values());args[side][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.compare_results(*args)

    def test_independent_runs_or_sources_not_one_admission(self):
        for key,value in (('commit','c'*40),('run_id','43')):
            args=list(self.values());args[1][key]=value
            with self.assertRaises(ValueError):c.compare_results(*args)
        args=list(self.values());args[3]['shared']='c'*64
        with self.assertRaises(ValueError):c.compare_results(*args)

    def test_candidate_change_stale_source_and_consumed_intent(self):
        folders=[]
        for name in ('chain','app'):
            folder=self.root/name;folder.mkdir();folders.append(folder)
            data=b'{"files":{}}';(folder/'candidate.json').write_bytes(data)
            (folder/'before.json').write_bytes(raw({'head':'a'*40}))
            (folder/'blob.json').write_bytes(raw({'blob':'b'*40,'sha256':digest(data)}))
        self.assertEqual(len(c.inputs_for(*folders,'a'*40)),4)
        with self.assertRaises(ValueError):c.inputs_for(*folders,'c'*40)
        (folders[0]/'candidate.json').write_bytes(b'changed')
        with self.assertRaises(ValueError):c.inputs_for(*folders,'a'*40)
        (folders[0]/'candidate.json').write_bytes(b'{"files":{}}')
        (folders[1]/'dispatch.json').write_bytes(b'{}')
        with self.assertRaises(ValueError):c.inputs_for(*folders,'a'*40)

    def test_workflow_requires_both_real_existing_entries_and_no_hosted(self):
        root=pathlib.Path(os.environ.get('CLOSURE_REVIEW_ROOT',pathlib.Path(__file__).resolve().parents[3]))
        text=(root/'.github/workflows/phase6e-closure-ci.yml').read_text()
        for path in ('phase6e11-endchain-ci.yml','phase6e-server-local-ci.yml'):
            self.assertIn('uses: ./.github/workflows/'+path,text)
        self.assertIn('needs: [endchain, application]',text)
        self.assertIn("github.run_attempt == 1",text)
        for forbidden in ('secrets: inherit','hosted_gate.py','supabase db push','id-token: write'):
            self.assertNotIn(forbidden,text)

    def test_candidate_import_does_not_load_checkout_ops_ci_or_hosted(self):
        original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name.split('.')[0] in ('ops','ci','hosted_gate'):
                raise AssertionError('checkout-only import forbidden')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=guarded):
            loaded=runpy.run_path(str(pathlib.Path(c.__file__)),run_name='candidate_closure_import')
        self.assertTrue(callable(loaded['verify_app']));self.assertTrue(callable(loaded['validate_bundle']))

    def test_real_small_app_zip_is_verified_without_extraction(self):
        folder,payloads,sources=self.fixture('app')
        before=set(folder.iterdir())
        result,actual=c.verify_app(folder,self.root)
        self.assertEqual(result,self.values()[1]);self.assertEqual(actual,sources)
        self.assertEqual(set(folder.iterdir()),before)

    def test_validate_binds_both_zips_before_offline_legacy_admission(self):
        chain,_,_=self.fixture('chain');app,_,_=self.fixture('app')
        gate=Mock(side_effect=self.fake_admission)
        with patch.dict('sys.modules',{'hosted_gate':types.SimpleNamespace(admission=gate)}):
            value=c.validate_bundle(chain,app,self.root)
        gate.assert_called_once_with(chain,root=self.root)
        self.assertFalse(value['hosted_admitted'])
        self.assertEqual(value['endchain_archive_sha256'],self.fake_admission(chain)['archive_sha256'])
        self.assertEqual(value['application_archive_sha256'],json.loads((app/'collection.json').read_bytes())['archive_sha256'])

    def test_unbound_chain_receipt_is_rejected_before_legacy_admission(self):
        chain,payloads,_=self.fixture('chain');app,_,_=self.fixture('app')
        original_manifest=(chain/'artifact-manifest.json').read_bytes()
        for name in c.CHAIN_PROOFS:
            with self.subTest(name=name):
                (chain/name).write_bytes(raw({'forged':True}))
                manifest=json.loads(original_manifest);manifest[name]=digest((chain/name).read_bytes())
                (chain/'artifact-manifest.json').write_bytes(raw(manifest))
                gate=Mock(side_effect=AssertionError('must not reach admission'))
                with patch.dict('sys.modules',{'hosted_gate':types.SimpleNamespace(admission=gate)}):
                    with self.assertRaisesRegex(ValueError,'manifest_changed'):
                        c.validate_bundle(chain,app,self.root)
                gate.assert_not_called()
                (chain/name).write_bytes(payloads[name])
                (chain/'artifact-manifest.json').write_bytes(original_manifest)

    def test_each_used_chain_receipt_must_be_in_zip_not_only_on_disk(self):
        folder,payloads,_=self.fixture('chain')
        for name in c.CHAIN_PROOFS:
            with self.subTest(name=name):
                reduced={k:v for k,v in payloads.items() if k!=name}
                self.package(folder,'chain',reduced)
                self.assertTrue((folder/name).exists())
                with self.assertRaisesRegex(ValueError,'proof_missing'):c.verify_archive(folder,'chain')

    def test_disk_receipt_and_rehashed_disk_manifest_cannot_replace_zip_evidence(self):
        folder,payloads,_=self.fixture('app')
        names=list(c.APP_PROOFS)+['123-release-security.json']
        for name in names:
            with self.subTest(name=name):
                self.package(folder,'app',payloads)
                (folder/name).write_bytes(raw({'forged':True}))
                with self.assertRaisesRegex(ValueError,'evidence_changed'):c.verify_app(folder,self.root)
                manifest=json.loads((folder/'artifact-manifest.json').read_bytes())
                manifest[name]=digest((folder/name).read_bytes())
                (folder/'artifact-manifest.json').write_bytes(raw(manifest))
                with self.assertRaisesRegex(ValueError,'manifest_changed'):c.verify_app(folder,self.root)

    def test_all_manifest_receipts_are_bound_even_when_not_explicitly_consumed(self):
        folder,payloads,_=self.fixture('app');payloads['extra-proof.txt']=b'proof'
        self.package(folder,'app',payloads);(folder/'extra-proof.txt').write_bytes(b'forged')
        with self.assertRaisesRegex(ValueError,'evidence_changed'):c.verify_app(folder,self.root)

    def test_zip_payload_tampering_rejected_even_if_outer_archive_digest_updated(self):
        folder,payloads,_=self.fixture('app')
        manifest={n:digest(data) for n,data in payloads.items()}
        changed={**payloads,'result.json':raw({'forged':True})}
        self.package(folder,'app',changed,manifest=manifest)
        with self.assertRaisesRegex(ValueError,'entry_changed'):c.verify_app(folder,self.root)

    def test_invalid_zip_with_matching_outer_digest_is_rejected(self):
        folder,_,_=self.fixture('app')
        (folder/'evidence.zip').write_bytes(b'not a ZIP');self.collection(folder,'app')
        with self.assertRaisesRegex(ValueError,'archive_invalid'):c.verify_app(folder,self.root)

    def test_zip_missing_embedded_manifest_is_rejected(self):
        folder,payloads,_=self.fixture('app')
        with zipfile.ZipFile(folder/'evidence.zip','w') as archive:
            for name,data in payloads.items():archive.writestr(name,data)
        self.collection(folder,'app')
        with self.assertRaisesRegex(ValueError,'archive_invalid'):c.verify_app(folder,self.root)

    def test_duplicate_case_alias_traversal_and_extra_zip_entries_rejected(self):
        folder,payloads,_=self.fixture('app')
        for name in ('result.json','RESULT.json','../escape.json','unlisted.json','nested/file.json'):
            with self.subTest(name=name):
                entries=list(payloads.items())+[(name,b'{}')]
                self.package(folder,'app',payloads,entries=entries)
                with self.assertRaisesRegex(ValueError,'archive_paths|manifest_set'):c.verify_app(folder,self.root)

    def test_zip_entry_missing_from_real_zip_rejected_even_if_disk_exists(self):
        folder,payloads,_=self.fixture('app')
        entries=[(n,data) for n,data in payloads.items() if n!='result.json']
        self.package(folder,'app',payloads,entries=entries)
        with self.assertRaisesRegex(ValueError,'manifest_set'):c.verify_app(folder,self.root)

    def test_duplicate_json_manifest_keys_and_invalid_digest_are_rejected(self):
        folder,payloads,_=self.fixture('app')
        self.package(folder,'app',payloads,embedded_manifest=b'{"result.json":"a","result.json":"b"}')
        with self.assertRaisesRegex(ValueError,'duplicate_json_key'):c.verify_app(folder,self.root)
        manifest={n:digest(data) for n,data in payloads.items()};manifest['result.json']='not-sha256'
        self.package(folder,'app',payloads,manifest=manifest)
        with self.assertRaisesRegex(ValueError,'manifest_digest'):c.verify_app(folder,self.root)

    def test_required_app_proofs_cannot_be_left_on_disk_unlisted(self):
        folder,payloads,_=self.fixture('app')
        for name in c.APP_PROOFS|{'123-release-security.json'}:
            with self.subTest(name=name):
                reduced={k:v for k,v in payloads.items() if k!=name}
                self.package(folder,'app',reduced)
                self.assertTrue((folder/name).exists())
                with self.assertRaisesRegex(ValueError,'proof_missing'):c.verify_app(folder,self.root)

    def test_security_receipt_must_be_unique_and_successful(self):
        folder,payloads,_=self.fixture('app')
        for code in (1,False,None,'0'):
            with self.subTest(code=code):
                changed={**payloads,'123-release-security.json':raw({'exitcode':code})}
                self.package(folder,'app',changed)
                with self.assertRaisesRegex(ValueError,'security_failed'):c.verify_app(folder,self.root)
        self.package(folder,'app',{**payloads,'124-release-security.json':raw({'exitcode':0})})
        with self.assertRaisesRegex(ValueError,'ambiguous'):c.verify_app(folder,self.root)

    def test_security_and_train_sources_must_be_in_source_bound_candidate(self):
        folder,payloads,sources=self.fixture('app')
        for name in c.APP_PROOF_SOURCES:
            candidate={'sources':{n:h for n,h in sources.items() if n!=name}}
            self.package(folder,'app',{**payloads,'candidate.json':raw(candidate)})
            with self.assertRaisesRegex(ValueError,'proof_source_missing'):c.verify_app(folder,self.root)

    def test_source_and_collection_tampering_rejected(self):
        folder,_,_=self.fixture('app')
        (self.root/'shared.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'source_changed'):c.verify_app(folder,self.root)
        (self.root/'shared.py').write_bytes(b'# synthetic fixture, not executed\n')
        original=(folder/'collection.json').read_bytes()
        for key,value in (('head','b'*40),('run',43),('verified',False),('archive_sha256','0'*64)):
            collection=json.loads(original);collection[key]=value
            (folder/'collection.json').write_bytes(raw(collection))
            with self.assertRaisesRegex(ValueError,'archive_binding|archive_changed'):c.verify_app(folder,self.root)

    def test_missing_disk_receipt_or_archive_is_rejected(self):
        folder,payloads,_=self.fixture('app')
        for name in ('result.json','artifact-manifest.json','evidence.zip','collection.json'):
            with self.subTest(name=name):
                self.package(folder,'app',payloads);(folder/name).unlink()
                with self.assertRaisesRegex(ValueError,'evidence_missing'):c.verify_app(folder,self.root)

    def test_zip_sizes_and_symlink_entries_rejected_without_extracting(self):
        folder,payloads,_=self.fixture('app')
        huge={**payloads,'oversized.txt':b'x'*2000001}
        self.package(folder,'app',huge)
        with self.assertRaisesRegex(ValueError,'archive_size'):c.verify_app(folder,self.root)
        link=zipfile.ZipInfo('linked.txt');link.create_system=3;link.external_attr=(stat.S_IFLNK|0o777)<<16
        self.package(folder,'app',payloads,entries=list(payloads.items())+[(link,b'target')])
        with self.assertRaisesRegex(ValueError,'archive_paths'):c.verify_app(folder,self.root)

    def test_legacy_admission_return_must_match_verified_chain(self):
        chain,_,_=self.fixture('chain');app,_,_=self.fixture('app')
        admitted=self.fake_admission(chain)
        for key,value in (('archive_sha256','0'*64),('head','b'*40),('ci_run','43'),
                          ('sources',{}),('register',{})):
            gate=Mock(return_value={**admitted,key:value})
            with patch.dict('sys.modules',{'hosted_gate':types.SimpleNamespace(admission=gate)}):
                with self.assertRaisesRegex(ValueError,'admission_binding'):c.validate_bundle(chain,app,self.root)

if __name__=='__main__':unittest.main()
