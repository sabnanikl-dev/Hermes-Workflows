# Binary Evidence Claim Depth and Container Grammar

Use this reference when a deterministic fixture or validator accepts screenshots, archives, media, signed envelopes, or another chunked/container format and the PR claims the evidence is “decoded,” “complete,” “valid,” or “integrity checked.”

## Separate the proof layers

A validator can prove one layer while silently failing the next:

1. **Recognition** — signature/magic and perhaps dimensions/header fields exist.
2. **Container integrity** — the entire stream is bounded, checksummed, ordered, and terminated correctly.
3. **Payload decoding** — decompression/decoding reaches EOF with no ignored, unconsumed, or trailing payload.
4. **Decoded semantics** — decoded data shape agrees with dimensions, row stride, filters, encoding, or manifest declarations.
5. **Evidence binding** — the file exists outside disposable state and is bound to the exact head/manifest/item the run claims.

Audit the strongest words across tests, comments, README, issue, PR body, and proof map. “Recognized image” does not imply “decodes”; “CRC checked” does not imply legal chunk grammar; “payload decompresses” does not imply valid row shape.

## Layered false-pass matrix

Every invalid case needs an honest control that reaches the same layer.

| Layer | Invalid probes | Honest controls |
|---|---|---|
| Signature/header | plain text with image suffix; truncated header; invalid dimensions/format | ordinary generated file |
| Bounds/checksum | over-declared/truncated chunk; bad CRC; bytes after terminator | intact bounded chunks |
| Decode completion | absent/corrupt/truncated compressed payload; trailing compressed bytes | one payload chunk; split consecutive payload chunks |
| Grammar/order | duplicate header; payload chunks separated by another chunk; unknown critical chunk; non-empty or non-final terminator | one header first; consecutive payload chunks; empty terminator last |
| Decoded shape | short/long rows; unsupported filter/encoding | exact row count/stride and supported values |
| Evidence binding | missing manifest/file; wrong head/dimensions; retained only in disposable checkout | complete head-bound manifest with retained files |

For a PNG-like generated fixture, the most useful controls are:

- honest `IHDR / IDAT / IEND`;
- consecutive split `IDAT / IDAT` to prove concatenation is intentional;
- duplicate `IHDR` former-red;
- `IDAT / ancillary / IDAT` former-red when the claimed/generated grammar requires consecutive payload chunks;
- unknown critical chunk former-red;
- corrupt and truncated payload former-red;
- exact scanline/filter control.

## Validate the lexical envelope before semantic classification

For formats whose identifier bytes encode properties (for example, critical versus ancillary bits in a chunk type), validate the identifier itself **before** interpreting those properties. A classifier such as “first byte is uppercase, therefore critical; otherwise ancillary” can let punctuation, digits, non-ASCII bytes, or an invalid reserved bit fall through as an allowed extension.

For each identifier/type field, probe:

- exact width and allowed byte/character set;
- reserved positions or property bits;
- unknown **valid** critical identifiers, which must fail closed;
- unknown **valid** ancillary identifiers, which should pass only in allowed positions;
- malformed critical-like and ancillary-like identifiers (punctuation, digits, non-ASCII, bad reserved bits);
- legal ancillary records before/after—but not inside—a consecutive payload run;
- bounds/checksum/decode precedence, using a checksum-valid and fully decodable payload so grammar is the only withdrawn property.

For a one-attempt bounded exception, run this lexical-envelope matrix before the builder exits. Otherwise an A-first class-wide review can correctly discover a same-class escape after the only authorized attempt has already been spent.

## Review sequence

1. Reproduce suspected false passes outside the builder’s fixtures using the exact public validator entry point.
2. Verify the committed honest control still passes.
3. Map each false pass to a specific public claim; do not block on abstract format purity the PR never promises.
4. After a fix, rerun the whole **claim class**—bounds, checksums, ordering, critical elements, decode completion, decoded shape, and binding—not only the cited bytes.
5. Keep one blocker ID for narrower manifestations of the same evidence-integrity gap; reviewers should independently reproduce and the auditor should deduplicate.
6. If the normal cycle cap is reached, complete the required current-head reviewer triad and escalate. Do not open an implicit extra cycle because the remaining repair looks tiny.

## Scope discipline

Do not demand a general-purpose binary/media parser when the fixture generates one deliberately narrow format. A proportionate repair usually enforces the exact generated grammar locally, uses existing standard-library primitives, and adds former-red tests. A dependency, production storage feature, browser service, or generalized artifact framework needs separate contract justification.

## Reporting language

Prefer precise status separation:

- “Committed evidence is honest; validator still has a grammar-order false pass.”
- “Recognition and decompression are proved; complete container validity is not.”
- “Green broad suite, but independent malformed-order probe still returns success.”
- “One deduplicated blocker remains in the same evidence-integrity class.”
