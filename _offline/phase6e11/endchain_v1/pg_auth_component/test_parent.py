"""Lifecycle orchestration doubles; no live worker, PG or Auth proof."""
from contextlib import contextmanager
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import context as m
from . import parent


class ParentTests(unittest.TestCase):
    def test_database_stop_allowed_before_auth_creation_only(self):
        value=SimpleNamespace(body_started=False,body_terminal=False,server=None)
        self.assertTrue(parent.producers_terminal(value))
        value.server=SimpleNamespace(create_attempted=False,stopped=False)
        self.assertTrue(parent.producers_terminal(value))
        value.server.create_attempted=True
        self.assertFalse(parent.producers_terminal(value))
        value.server.stopped=True
        self.assertTrue(parent.producers_terminal(value))

    def test_unknown_worker_blocks_database_stop_even_if_auth_stopped(self):
        value=SimpleNamespace(body_started=True,body_terminal=False,
            server=SimpleNamespace(create_attempted=True,stopped=True))
        self.assertFalse(parent.producers_terminal(value))

    def make(self):
        events=[]; records={}
        value=object.__new__(m.Context)
        value.closed=False;value.unknown=[];value.body_started=True;value.body_terminal=True
        value.gate=SimpleNamespace();value.run_id='unit';value.ctx={}
        value.result={'status':'NO_GO','parent_subset_absent':False,'auth_process_stopped':False,
            'auth_container_absent':False,'post_stop_counters':False,'claims_released':False,'full_chain_admission':False}
        value.records=SimpleNamespace(save=lambda n,v:records.update({n:dict(v)}),seal=lambda:events.append('archive'))
        value.db=SimpleNamespace(closed=False)
        def close():value.db.closed=True;events.append('dbclose')
        value.db.close=close
        def cleanup(lease):events.append('cleanup');return {'known_parent_subset_absent':True}
        value.owners=SimpleNamespace(close=lambda:events.append('registryclose'),cleanup=cleanup,
            records=SimpleNamespace(seal=lambda:events.append('ownerarchive')))
        def stop():events.append('stop');value.server.stopped=True
        def remove():events.append('remove');value.server.removed=True
        value.server=SimpleNamespace(create_attempted=True,stopped=False,removed=False,stop=stop,remove=remove,
            records=SimpleNamespace(seal=lambda:events.append('containerarchive')),
            safety=SimpleNamespace(seal=lambda:events.append('safetyarchive')))
        value.counter=SimpleNamespace(finish=lambda:events.append('counter'))
        value.runtime=SimpleNamespace(clear=lambda:events.append('clear'))
        value.connect=lambda:SimpleNamespace(close=lambda:events.append('observerclose'))
        class lease:
            def __init__(self,*args):
                self.records=SimpleNamespace(seal=lambda:events.append('scopearchive'))
            def __enter__(self):events.append('locks');return self
            def __exit__(self,*args):events.append('unlock');return False
        p=patch.object(m.scope,'ScopeLease',side_effect=lease);p.start();self.addCleanup(p.stop)
        # Session is only a type wrapper here; execution is covered in other tests.
        import sys
        p=patch.dict(sys.modules,{'protocol':SimpleNamespace(Session=lambda *a:SimpleNamespace())})
        p.start();self.addCleanup(p.stop)
        return value,events,records

    def test_normal_registry_then_locks_then_cleanup_then_stop_then_counter(self):
        value,events,records=self.make();value.__exit__(None,None,None)
        self.assertLess(events.index('registryclose'),events.index('cleanup'))
        self.assertLess(events.index('cleanup'),events.index('stop'))
        self.assertLess(events.index('stop'),events.index('counter'))
        self.assertLess(events.index('counter'),events.index('remove'))
        self.assertEqual(value.result['status'],'LOCAL_PARENT_LIFECYCLE_CONFIRMED')
        self.assertFalse(value.result['claims_released'])

    def test_body_unknown_stops_server_but_never_cleans_accounts(self):
        value,events,records=self.make();value.body_terminal=False
        primary=TimeoutError('PRIVATE_REVIEW_SENTINEL')
        self.assertFalse(value.__exit__(type(primary),primary,None))
        self.assertNotIn('cleanup',events);self.assertIn('stop',events)
        self.assertIn('counter',events)
        self.assertEqual(value.result['status'],'NO_GO')
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',str(records))

    def test_partial_bootstrap_known_subset_can_close_without_fake_failure(self):
        value,events,records=self.make();value.body_started=False;value.body_terminal=False
        value.__exit__(None,None,None)
        self.assertIn('cleanup',events)

    def test_registry_unknown_prevents_scope_or_cleanup(self):
        value,events,records=self.make()
        value.owners.close=lambda:(_ for _ in ()).throw(ValueError('unknown'))
        with self.assertRaises(ValueError):value.__exit__(None,None,None)
        self.assertNotIn('locks',events);self.assertNotIn('cleanup',events)
        self.assertIn('stop',events)

    def test_stop_unconfirmed_no_counters(self):
        value,events,records=self.make()
        value.server.stop=lambda:(_ for _ in ()).throw(TimeoutError('unknown'))
        with self.assertRaises(TimeoutError):value.__exit__(None,None,None)
        self.assertNotIn('counter',events)
        self.assertFalse(value.result['post_stop_counters'])

    def test_original_error_survives_cleanup_stop_export_failure(self):
        value,events,records=self.make()
        value.owners.cleanup=lambda lease:(_ for _ in ()).throw(ValueError('secondary'))
        value.server.stop=lambda:(_ for _ in ()).throw(OSError('secondary'))
        value.records.save=lambda *args:(_ for _ in ()).throw(OSError('secondary'))
        primary=TimeoutError('original')
        self.assertFalse(value.__exit__(type(primary),primary,None))
        self.assertEqual(len(primary.__notes__),3)
        self.assertEqual(value.result['status'],'NO_GO')

    def test_reentry_does_not_repeat_delete_or_stop(self):
        value,events,_=self.make();value.__exit__(None,None,None)
        before=list(events);value.__exit__(None,None,None);self.assertEqual(events,before)

    def test_poststop_counter_failure_never_complete(self):
        value,events,_=self.make()
        value.counter.finish=lambda:(_ for _ in ()).throw(ValueError('counter_reset'))
        with self.assertRaises(ValueError):value.__exit__(None,None,None)
        self.assertEqual(value.result['status'],'NO_GO')

    def test_remove_failure_never_complete(self):
        value,events,_=self.make()
        value.server.remove=lambda:(_ for _ in ()).throw(TimeoutError('remove_unknown'))
        with self.assertRaises(TimeoutError):value.__exit__(None,None,None)
        self.assertEqual(value.result['status'],'NO_GO')
        self.assertFalse(value.result['auth_container_absent'])

    def test_failed_parent_cleanup_still_archives_original_scope(self):
        value,events,_=self.make()
        value.owners.cleanup=lambda lease:(_ for _ in ()).throw(ValueError('original'))
        with self.assertRaisesRegex(ValueError,'original'):value.__exit__(None,None,None)
        self.assertLess(events.index('unlock'),events.index('scopearchive'))
        self.assertIn('safetyarchive',events)

    def test_parent_registry_export_preserves_exact_original_bytes(self):
        import base64
        import tempfile
        from pathlib import Path
        value,_,saved=self.make()
        with tempfile.TemporaryDirectory() as temporary:
            value.gate.out=Path(temporary)
            folder=value.gate.out/'original-parent';folder.mkdir()
            original=b'{ "phase": "terminal", "known": false }\n'
            (folder/'original.json').write_bytes(original)
            record=SimpleNamespace(folder=folder,validate=lambda:{'original.json':original})
            value.ctx={'auth':SimpleNamespace(registry=SimpleNamespace(_recordsets=[record]))}
            value.records.source={'unit_only':True}
            value.tracked_originals()
            exported=saved['tracked-originals.json']['files']['original-parent/original.json']
            self.assertEqual(base64.b64decode(exported['base64']),original)
            self.assertEqual(exported['sha256'],m.lifecycle.durable.sha(original))
            self.assertTrue(saved['tracked-originals.json']['lossless'])

    def test_changed_parent_original_prevents_export_claim(self):
        value,_,saved=self.make()
        record=SimpleNamespace(folder=__import__('pathlib').Path(__file__).parent,
            validate=lambda:(_ for _ in ()).throw(ValueError('changed_original')))
        value.ctx={'auth':SimpleNamespace(registry=SimpleNamespace(_recordsets=[record]))}
        with self.assertRaisesRegex(ValueError,'changed_original'):value.tracked_originals()
        self.assertNotIn('tracked-originals.json',saved)


if __name__=='__main__':unittest.main()
