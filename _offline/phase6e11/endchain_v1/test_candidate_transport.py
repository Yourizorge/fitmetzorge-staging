"""Exercise the pinned fetch parser without networking or database imports."""
import ast,base64,hashlib,io,json,pathlib,unittest

SOURCE=pathlib.Path(__file__).resolve().parent.parent/'controller_v1/ci.py'
tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
nodes=[node for node in tree.body if
       isinstance(node,ast.FunctionDef) and node.name=='read_candidate' or
       isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('CANDIDATE_') for t in node.targets)]
scope={'base64':base64,'hashlib':hashlib,'json':json}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),scope)
read_candidate=scope['read_candidate']

class CandidateTransport(unittest.TestCase):
    def envelope(self,data,**changes):
        obj={'encoding':'base64','size':len(data),'content':base64.encodebytes(data).decode('ascii')}
        obj.update(changes)
        return io.BytesIO(json.dumps(obj).encode())
    def test_full_app_sized_blob_exceeds_old_limit_without_truncation(self):
        data=b'x'*8_200_000
        response=self.envelope(data)
        self.assertGreater(len(response.getvalue()),8_000_000)
        self.assertEqual(read_candidate(response,hashlib.sha256(data).hexdigest()),data)
    def test_envelope_oversize_is_bounded(self):
        response=io.BytesIO(b'x'*(scope['CANDIDATE_ENVELOPE_LIMIT']+2))
        with self.assertRaisesRegex(RuntimeError,'candidate_envelope_limit'):read_candidate(response,'0'*64)
        self.assertEqual(response.tell(),scope['CANDIDATE_ENVELOPE_LIMIT']+1)
    def test_truncated_response_never_reaches_source_unpack(self):
        data=b'candidate'
        response=io.BytesIO(self.envelope(data).getvalue()[:-2])
        with self.assertRaisesRegex(RuntimeError,'candidate_envelope_invalid'):read_candidate(response,'0'*64)
    def test_format_size_and_digest_are_independent(self):
        for changes,error in [({'encoding':'raw'},'encoding'),({'size':True},'payload_limit'),
          ({'size':scope['CANDIDATE_PAYLOAD_LIMIT']+1},'payload_limit'),
          ({'size':2},'payload_length'),({'content':'!'},'base64_invalid'),({},'digest')]:
            with self.subTest(error=error),self.assertRaisesRegex(RuntimeError,'candidate_'+error):
                read_candidate(self.envelope(b'x',**changes),'0'*64)
    def test_harness_pin_matches_current_parser(self):
        from ci_source_binding import HARNESS
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
                         HARNESS['_offline/phase6e11/controller_v1/ci.py'])

if __name__=='__main__':unittest.main()
