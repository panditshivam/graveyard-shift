"""Create the small, original demonstration history. Not real maintainer history."""
import os
from pathlib import Path
import subprocess

OLD = '''def legacy_retry(operation, attempts=3):
    """Try an operation, including its final permitted attempt."""
    for attempt in range(attempts):
        try:
            return operation()
        except ValueError:
            if attempt == attempts - 1:
                raise


def read_config(values):
    return {key.lower(): value for key, value in values.items()}
'''
BUG = '''def run_with_retry(operation, attempts=3):
    """Replacement implementation from the authored demo rewrite."""
    for attempt in range(attempts - 1):
        try:
            return operation()
        except ValueError:
            pass
    raise ValueError("retry budget exhausted")


def load_settings(values):
    return {key.lower(): value for key, value in values.items()}
'''
PATCH = '''def run_with_retry(operation, attempts=3):
    """Preserve the old implementation's final-attempt fix."""
    for attempt in range(attempts):
        try:
            return operation()
        except ValueError:
            if attempt == attempts - 1:
                raise


def load_settings(values):
    return {key.lower(): value for key, value in values.items()}
'''
TEST = '''import unittest
from retry import run_with_retry

class RetryContract(unittest.TestCase):
    def test_success_on_last_attempt(self):
        calls = []
        def operation():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "returned on attempt 3"
        self.assertEqual(run_with_retry(operation, 3), "returned on attempt 3")
        self.assertEqual(len(calls), 3)

    def test_success_on_first_attempt(self):
        self.assertEqual(run_with_retry(lambda: "first", 3), "first")

    def test_failure_uses_all_attempts(self):
        calls = []
        def operation():
            calls.append(1)
            raise ValueError("still failing")
        with self.assertRaises(ValueError):
            run_with_retry(operation, 3)
        self.assertEqual(len(calls), 3)

if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True,
                                   stderr=subprocess.PIPE, timeout=15).strip()

def make_fixture(repo):
    repo = Path(repo)
    if (repo / '.git').exists():
        return repo
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, 'init', '-b', 'main')
    git(repo, 'config', 'user.name', 'Graveyard Shift demo')
    git(repo, 'config', 'user.email', 'demo@example.invalid')
    versions = [
        ('Add retry helper and configuration reader', OLD.replace('range(attempts)', 'range(attempts - 1)')),
        ('Fix: include the final permitted retry attempt', OLD),
        ('Rename configuration reader without changing its body', OLD.replace('read_config', 'load_settings')),
        ('Rewrite retry API; retire legacy_retry', BUG),
    ]
    for index, (message, source) in enumerate(versions):
        (repo / 'retry.py').write_text(source)
        git(repo, 'add', 'retry.py')
        # Fixed timestamps make the authored fixture reproducible, not historical evidence.
        env = {**os.environ, 'GIT_AUTHOR_DATE': f'2026-10-27T12:0{index}:00+00:00',
               'GIT_COMMITTER_DATE': f'2026-10-27T12:0{index}:00+00:00'}
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', message], env=env,
                       check=True, capture_output=True, timeout=15)
    return repo
