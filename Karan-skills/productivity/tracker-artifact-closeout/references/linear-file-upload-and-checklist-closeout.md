# Linear file upload and acceptance-checklist closeout

This reference captures the provider-specific details behind the tracker closeout workflow.

## Discover the live schema when needed

Linear's mutation schema includes:

- `fileUpload(filename, contentType, size, makePublic)` → `UploadPayload`;
- `attachmentCreate(input: AttachmentCreateInput!)` → `AttachmentPayload`;
- `issueUpdate(id, input)` for body/state closeout;
- `commentCreate(input)` for evidence notes.

Useful `UploadFile` fields are `uploadUrl`, `assetUrl`, and `headers { key value }`. Useful `AttachmentCreateInput` fields include `issueId`, `title`, `subtitle`, `url`, and `commentBody`.

The local `linear_api.py raw` helper may unwrap the GraphQL `data` object, while direct `curl` responses retain `.data`. Inspect one response before writing `jq` selectors; a wrong selector can exit nonzero after the mutation actually succeeded.

## 1. Request a signed upload slot

```graphql
mutation {
  fileUpload(
    filename: "artifact.png"
    contentType: "image/png"
    size: 123456
    makePublic: false
  ) {
    success
    uploadFile {
      uploadUrl
      assetUrl
      headers { key value }
    }
  }
}
```

Treat `uploadUrl` as a short-lived secret. Save the response to a temporary file without printing the URL. `assetUrl` is the durable URL used by Linear after upload.

## 2. PUT the exact bytes

```bash
args=( -H "Content-Type: $MIME" )
while IFS=$'\t' read -r key value; do
  args+=( -H "$key: $value" )
done < <(jq -r '.fileUpload.uploadFile.headers[] | [.key,.value] | @tsv' upload.json)

HTTP=$(curl -sS -o put-body -w '%{http_code}' \
  -X PUT "${args[@]}" \
  --data-binary @"$FILE" \
  "$UPLOAD_URL")
```

Accept HTTP 200, 201, or 204 as appropriate.

### `SignatureDoesNotMatch` diagnosis

`curl --data-binary` defaults to `application/x-www-form-urlencoded` unless a content type is supplied. Linear's signed Google Storage request may include `content-type` in `X-Goog-SignedHeaders`. If the PUT uses curl's default instead of the MIME type supplied to `fileUpload`, Google returns HTTP 403 `SignatureDoesNotMatch`.

The storage error's canonical request will show the mismatched content type. Request a **fresh** upload slot—signed URLs expire quickly—and retry with:

- explicit `Content-Type: image/png` (or the actual MIME type);
- every returned upload header; and
- the unchanged exact bytes/size.

Do not preserve the transient failure as “uploads are broken”; preserve the signed-header parity rule.

## 3. Create a durable attachment and inline image

```graphql
mutation($input: AttachmentCreateInput!) {
  attachmentCreate(input: $input) {
    success
    attachment {
      id
      title
      subtitle
      url
      issue { id identifier }
    }
  }
}
```

Variables:

```json
{
  "input": {
    "issueId": "ISSUE_UUID",
    "title": "One-page engineering blueprint",
    "subtitle": "Exact head abc1234 · reviewer findings and final proof",
    "url": "ASSET_URL",
    "commentBody": "## Blueprint\n\n![Blueprint](ASSET_URL)\n\nExact reviewed head: `FULL_SHA`\nSource: PR_URL"
  }
}
```

Use `makePublic: false` unless public access is explicitly needed. The formal attachment provides durable issue association; `commentBody` gives an inline visual activity entry.

Verify by attachment ID and comment ID. A successful PUT is not sufficient.

## 4. Complete checkboxes and state

Fetch the full issue description, locate the acceptance section, and stop at its next Markdown heading. Count the exact unchecked lines before mutation. Replace only those proven by evidence, append a completion section, and set the team-specific Done `stateId` in the same full-description update when every criterion is satisfied.

Linear can normalize checked Markdown from `- [x]` to `- [X]`. Readback should therefore count case-insensitively or explicitly accept both forms:

```python
checked = section.count("- [x] ") + section.count("- [X] ")
unchecked = section.count("- [ ] ")
assert checked == expected
assert unchecked == 0
```

Scope the count to the acceptance section. A lowercase-only regex can misleadingly report zero checked boxes after a successful mutation.

## 5. Final readback packet

Directly verify:

- issue state `{ name, type }` is Done/completed;
- expected checked count and zero unchecked criteria;
- completion section contains reviewed head and verified merge commit;
- attachment collection contains the captured attachment ID;
- inline blueprint comment contains the image Markdown and exact head;
- final closeout comment resolves directly by captured comment ID.
