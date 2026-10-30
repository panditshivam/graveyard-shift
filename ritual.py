"""Execute only our fixed authored regression fixture, in fresh temporary copies."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from fixture import BUG, PATCH, TEST

def replay():
    results = []
    for label, source in [('before', BUG), ('after', PATCH)]:
        with tempfile.TemporaryDirectory(prefix='graveyard-test-') as folder:
            path = Path(folder)
            (path/'retry.py').write_text(source)
            (path/'test_retry.py').write_text(TEST)
            start = time.monotonic()
            proc = subprocess.run([sys.executable, '-I', '-S', '-c',
                "import sys;sys.path.insert(0,'.');import unittest;unittest.main(module='test_retry',verbosity=2)"],
                cwd=folder, env={'PATH':os.defpath, 'PYTHONHASHSEED':'0'},
                capture_output=True, text=True, timeout=10)
            results.append({'stage':label, 'returncode':proc.returncode,
                'seconds':round(time.monotonic()-start,3),
                'output':(proc.stdout+proc.stderr)[-8000:],
                'source_sha256':hashlib.sha256(source.encode()).hexdigest()})
    verified = results[0]['returncode']==1 and 'FAILED (failures=1, errors=1)' in results[0]['output'] and results[1]['returncode']==0 and 'Ran 3 tests' in results[1]['output']
    return {'verified':verified, 'results':results, 'tests':3,
            'boundary':'Only authored fixed Python code; no visitor code or shell input. Isolated temporary directories and stripped environment; not an OS security sandbox.'}
