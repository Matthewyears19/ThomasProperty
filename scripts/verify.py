"""One-command preview verification. No deployments or real email calls."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
environment = {**os.environ, 'TPS_BUILD_MODE': 'preview'}
commands = [
    [sys.executable, 'scripts/build.py'],
    [sys.executable, 'scripts/check.py'],
    [sys.executable, 'scripts/audit.py'],
    [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'],
    ['node', 'scripts/check-navigation.cjs'],
    ['node', '--test', *[str(path.relative_to(ROOT)) for path in sorted((ROOT / 'tests').glob('*.test.mjs'))]],
]
for command in commands:
    print('Checking: ' + ' '.join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
print('All local preview checks passed. Live integrations and release approval are separate.')
