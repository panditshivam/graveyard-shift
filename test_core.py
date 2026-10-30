import tempfile
from pathlib import Path
import unittest
from fixture import make_fixture
from history import mine, symbols
from ritual import replay

class CoreTests(unittest.TestCase):
    def test_authored_history_and_rename(self):
        with tempfile.TemporaryDirectory() as folder:
            result=mine(make_fixture(Path(folder)/'repo'))
        self.assertEqual(result['commits'],4)
        ghosts={g['name']:g for g in result['ghosts']}
        self.assertEqual(set(ghosts),{'legacy_retry','read_config'})
        self.assertEqual(ghosts['read_config']['descendant']['name'],'load_settings')
        self.assertIsNone(ghosts['legacy_retry']['descendant'])
        self.assertIn('range(attempts)',ghosts['legacy_retry']['source'])
    def test_body_match_ignores_name_but_not_changed_logic(self):
        a=next(iter(symbols('def a(x):\n return x+1\n','x.py','a').values()))
        b=next(iter(symbols('def b(x):\n return x+1\n','y.py','b').values()))
        c=next(iter(symbols('def b(x):\n return x+2\n','y.py','c').values()))
        self.assertEqual(a['fingerprint'],b['fingerprint']);self.assertNotEqual(a['fingerprint'],c['fingerprint'])
    def test_regression_fails_then_fixed_passes(self):
        result=replay();self.assertTrue(result['verified']);self.assertEqual([x['returncode'] for x in result['results']],[1,0])

if __name__=='__main__':unittest.main(verbosity=2)
