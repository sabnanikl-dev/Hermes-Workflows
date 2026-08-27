# Safe Multiline Tracker Mutations

Use this pattern for full Markdown issue-body updates and comments when content includes backticks, dollar signs, quotes, or multiple lines.

## Never interpolate the body into a shell string

Unsafe:

```python
terminal(f"python helper.py update --description {json.dumps(body)}")
```

Even JSON-looking quoting can become unsafe once interpreted by a shell. Markdown backticks may execute command substitution, and a helper can still report success after receiving corrupted text.

## Preferred transport order

1. Provider API/tool with structured variables.
2. A local wrapper using `subprocess.run([...])` with an argument vector and `shell=False`.
3. A provider helper that natively accepts `--body-file` or stdin without shell interpolation.

Example:

```python
from pathlib import Path
import subprocess
import sys

body = Path("/tmp/issue-body.md").read_text()
result = subprocess.run(
    [
        sys.executable,
        "/path/to/linear_api.py",
        "update-issue",
        "ENG-42",
        "--description",
        body,
    ],
    text=True,
    capture_output=True,
    check=False,
)
raise SystemExit(result.returncode)
```

For comments, pass the file contents as one positional argv element in the same way.

## Pre-mutation packet

Before writing, save or retain:

- exact live description/body;
- current workflow state;
- current comment count;
- intended full replacement body;
- SHA-256 of the intended body;
- unique amendment heading/marker expected exactly once.

## Repair after a suspicious write

If stderr shows shell commands, missing paths, or interpreted Markdown—even with exit `0`:

1. reject the result as evidence;
2. refetch live state before retrying;
3. rebuild the intended full body from the verified pre-mutation snapshot, not from the possibly corrupted live body;
4. run one argument-safe full-body update;
5. refetch and verify normalized semantics;
6. verify the unique amendment heading appears exactly once;
7. verify state and unrelated historical sections remained unchanged.

## Readback contract

Trackers may normalize Markdown (`-` to `*`, links, checked-box case, trailing newline). Do not demand byte equality unless the provider promises it. Verify:

- state name/type unchanged or intentionally changed;
- unique amendment heading count;
- exact IDs, event names, hashes, URLs, and authority clauses;
- historical tail/head sections preserved;
- expected checked/unchecked counts in the scoped section;
- no telltale missing inline-code tokens;
- created comments directly by returned ID when available.

A successful helper response or HTTP 200 is not mutation proof.
