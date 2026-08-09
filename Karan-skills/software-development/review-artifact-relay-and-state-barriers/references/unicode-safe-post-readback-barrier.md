# Unicode-Safe GitHub Relay Readback Barrier

Use this after a reviewer artifact has been validated, sanitized into a distinct publication copy, and is ready for an external GitHub POST.

## Why this barrier exists

A compound shell command can successfully create a GitHub comment and then exit non-zero because a later local assertion, cleanup command, shell trap, or character/byte-length check failed. Retrying the whole command can publish a duplicate artifact.

Unicode makes naive diagnostics especially misleading: `len(text)` counts characters, while `stat`, file size, and SHA-256 operate on encoded bytes. Curly quotes, arrows, and other multibyte characters can make character counts differ from byte counts even when GitHub's body is exactly equal to the local file.

## Required sequence

1. **Pre-POST barrier**
   - Re-read PR `headRefOid`, state, draft state, and merge state.
   - Require the expected exact head and the intended open/draft/unmerged disposition.
   - Snapshot existing immutable comment/review IDs immediately before the POST.
   - Keep the raw child artifact local; pass only the parser-validated sanitized publication path to `--body-file`.

2. **Capture the POST identity**
   - Capture the URL or immutable ID returned by the POST command.
   - Persist it separately from later verification output.
   - Once a concrete URL/ID exists, treat the external side effect as potentially landed even if the compound command later exits non-zero.

3. **Read back by immutable ID**
   - Fetch that exact comment/review through the API.
   - Do not search by matching prose unless the transport truly returned no ID; if no ID was returned, require exactly one new matching ID since the immediate pre-POST snapshot.

4. **Compare exact publication bytes**
   - Read the local sanitized file as UTF-8 text and the API `body` as the decoded JSON string.
   - First require exact text equality with no asymmetric trimming.
   - Compute SHA-256 over `local_text.encode("utf-8")` and `api_body.encode("utf-8")`; require equal digests and byte counts.
   - If counts differ, print only lengths, digests, and the first differing character/byte position—not the full body, which may be the surface under secret review.
   - Never compare `len(str)` to filesystem byte size and call the difference corruption.

5. **Revalidate semantic identity**
   - Verify immutable ID, author, role, exact full head, status, blocker count, configured signature, and canonical parser/finding parity.
   - Re-read the live PR head after publication.

6. **Handle a non-zero compound exit safely**
   - If a URL/ID printed before failure, do **not** repost.
   - Run a fresh, read-only verifier against that ID.
   - Classify success from the independent readback, not from the original wrapper exit or its plausible-looking stdout.
   - Retry the POST only when direct inspection proves the expected artifact is absent.

## Minimal verifier shape

```python
local_text = publication_path.read_text(encoding="utf-8")
remote = github_comment_by_id(comment_id)
remote_text = remote["body"]

assert remote_text == local_text
assert sha256(remote_text.encode("utf-8")).digest() == sha256(
    local_text.encode("utf-8")
).digest()
assert len(remote_text.encode("utf-8")) == len(local_text.encode("utf-8"))
```

Then apply the repository's shipped artifact parser to `remote_text` and compare its claims/findings with the already parsed sanitized publication artifact.

## Failure reporting

Report the state precisely:

- **POST not attempted** — no external side effect.
- **POST identity returned; readback pending** — external state is ambiguous; no retry.
- **POST landed; local compound verifier failed** — rerun only the verifier.
- **Immutable-ID readback exact** — publication is verified even if the original compound shell returned non-zero later.
- **Immutable-ID readback differs** — stop; preserve local/remote digests and investigate without publishing a replacement.
