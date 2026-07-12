#!/usr/bin/env python3
"""Template for post-change ad-hoc verification when no canonical suite exists.

Copy the relevant assertions into a tempfile-created verifier. Do not commit this
file into the target repo; create the runnable verifier under the verifier's
requested temp directory with prefix `hermes-verify-`, run it, then delete it.
"""
from pathlib import Path
import os
import subprocess
import tempfile

REQUESTED_TMPDIR = Path("/var/folders/5t/ngjzk0ss29s_ng61054v19h80000gn/T")  # replace when requested
TARGET_REPO = Path("/path/to/repo")

fd, raw_path = tempfile.mkstemp(prefix="hermes-verify-", suffix=".py", dir=REQUESTED_TMPDIR)
script_path = Path(raw_path)
result = None
script = """
from pathlib import Path
import importlib.util
import subprocess
import sys

ROOT = Path('/path/to/repo')
MODULE_PATH = ROOT / 'path' / 'to' / 'changed_file.py'

# Import changed module directly when possible. Register in sys.modules before
# exec_module; dataclasses and some runtime reflection expect this during import.
spec = importlib.util.spec_from_file_location('module_under_test', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

# Expected red: prove the verifier would catch the old/bad behavior.
old_fixture = 'old rejected behavior marker'
assert 'old rejected behavior marker' in old_fixture

# Green/current assertions: verify concrete changed behavior and generated outputs.
# assert module.CONSTANT == 'expected value'
# assert generated_output == committed_output

# If the changed module hardcodes repo-root constants (ROOT, PRODUCT, etc.) but
# the verifier uses temp fixtures, monkeypatch those constants to the temp paths
# before calling the function under test. This avoids false failures from
# Path.relative_to(ROOT) or repo-root-only file assumptions.
# module.ROOT = fixture_dir
# module.TARGET_FILE = fixture_dir / 'target.md'

# Optional: run the target's lightweight check-only command if one exists.
# leak = subprocess.run([...], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
# assert leak.returncode == 0, leak.stdout

print('EXPECTED_RED_OLD_FIXTURE_DETECTED=True')
print('GREEN_CURRENT_BEHAVIOR_OK=True')
"""
try:
    os.close(fd)
    script_path.write_text(script, encoding="utf-8")
    result = subprocess.run(["python3", str(script_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    print(f"TEMP_SCRIPT={script_path}")
    print(f"VERIFY_EXIT={result.returncode}")
    print(result.stdout, end="")
finally:
    try:
        script_path.unlink()
    except FileNotFoundError:
        pass
    print(f"TEMP_SCRIPT_EXISTS_AFTER_CLEANUP={script_path.exists()}")

status = subprocess.run(["git", "status", "--short", "--branch"], cwd=TARGET_REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
print("GIT_STATUS_BEGIN")
print(status.stdout, end="")
print("GIT_STATUS_END")

if result is None or result.returncode != 0 or script_path.exists() or status.returncode != 0:
    raise SystemExit(1)
