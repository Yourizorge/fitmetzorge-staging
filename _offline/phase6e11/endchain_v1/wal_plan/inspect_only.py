"""Read trusted checkout query sources and parse them offline; never connect."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest
from plan_only import prepare,sha

HERE=Path(__file__).resolve().parent
cli=argparse.ArgumentParser();cli.add_argument('--source-root',type=Path,required=True)
cli.add_argument('--receipt', choices=('r2',), required=True)
args=cli.parse_args();root=args.source_root.resolve(strict=True)
base=root/'_offline/phase6e11/endchain_v1'
sys.path.insert(0,str(base))
import lifecycle_gates as gates
if Path(gates.__file__).resolve()!=base/'lifecycle_gates.py':raise ValueError('source_origin')
sources={}
for module in list(sys.modules.values()):
    file=getattr(module,'__file__',None)
    if file and Path(file).is_file() and Path(file).resolve().is_relative_to(root):
        path=Path(file).resolve();sources[path.relative_to(root).as_posix()]=sha(path.read_bytes())
queries={name:prepare(getattr(gates,name),sha(getattr(gates,name).encode())) for name in ('ACCESS','CATALOG')}
suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_plan_only.py')
count=suite.countTestCases();stream=io.StringIO();start=time.monotonic()
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
for name,digest in sources.items():
    if sha((root/name).read_bytes())!=digest:raise ValueError('source_changed_during_read')
raw=stream.getvalue().encode()
with (HERE/('tests-'+args.receipt+'.txt')).open('xb') as output:output.write(raw)
report={'scope':'offline syntax and sanitized projection; not a runtime probe',
    'sources':sources,'queries':queries,'selected':count,'run':result.testsRun,
    'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
    'seconds':time.monotonic()-start,'log_sha256':sha(raw),
    'passed':result.wasSuccessful() and count==result.testsRun and not result.skipped,
    'proposed_explicit_sql_commands':5,'proposed_statement_timeout_ms':5000,
    'connection_implicit_sql_bound':None,'actual_sql_commands':0,'actual_pg':False,
    'fixture_equivalence_proven':False,'hosted_calls':0,'full_chain_admission':False}
with (HERE/('feasibility-'+args.receipt+'.json')).open('x') as output:json.dump(report,output,indent=2)
print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
