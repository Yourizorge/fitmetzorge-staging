"""Fresh isolated Python import from an assembled canonical-shaped source tree."""
import json
import os
import shutil
import subprocess
import sys
import unittest

import test_runtime_registered_bootstrap as base


class ImportTests(unittest.TestCase):
    def test_canonical_bundle_needs_no_agent_sibling_directories(self):
        path = base.CORE / "test_runtime_registered_bootstrap.py"
        shutil.copyfile(base.DELIVERY / path.name, path)
        paths = [str(base.CORE), *filter(None, os.environ.get("PYTHONPATH", "").split(os.pathsep))]
        code = ("import sys;sys.path[:0]=" + repr(paths) + ";"
                "import test_runtime_registered_bootstrap as m;"
                "assert not m.ISOLATED;"
                "from quota_candidate_v1 import runtime_registered_startup, runtime_registered_cleanup;"
                "from quota_candidate_v1 import runtime_auth_failure_component, runtime_auth_failure_verify;"
                "import admission_auth_runtime_profile, admission_budget_root_runtime;"
                "print('CANONICAL_IMPORT_OK')")
        environment = {**os.environ, "AUTH_CONTEXT_SOURCE_ROOT": str(base.ROOT)}
        result = subprocess.run([sys.executable, "-I", "-B", "-c", code],
            env=environment, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "CANONICAL_IMPORT_OK")


if __name__ == "__main__":
    unittest.main()
