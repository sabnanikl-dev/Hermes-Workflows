"""LinkedIn image-post publish/verify via the treg CLI proxy.

Copy into the post's project folder, set the constants, and run with the treg
CLI's interpreter (the uv-tool python named in `treg`'s shebang); system
pythons lack treg/httpx. Actions: upload | publish | verify.

A JSON state file guards every mutation: upload refuses if an image_urn
exists, publish refuses if create_attempted is set, and approved-file hashes
are re-checked before create. Reconcile state instead of blindly retrying.
"""
import argparse, datetime, hashlib, json, os, re, time
from pathlib import Path
from urllib.parse import quote, urlparse
import httpx
from treg.cli import _client, _load_config

ROOT = Path(__file__).parent
STATE = ROOT / '<post>-publication.json'          # e.g. linkedin-post-05-publication.json
CAPTION = ROOT / '<post>-caption-v<final>.txt'    # exact approved caption
IMAGE = ROOT / '<post>-image-v<final>.png'         # exact approved PNG
AUTHOR = 'urn:li:person:<sub>'                     # sub from GET v2/userinfo
APPROVAL = '<one-line quote of the explicit Telegram approval>'
HEADERS = {'LinkedIn-Version': '<current supported YYYYMM>', 'X-Restli-Protocol-Version': '2.0.0'}

def save(s):
    s['updated_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    STATE.write_text(json.dumps(s, indent=2) + '\n')

def req(c, method, path, body=None, params=None):
    r = c.request(method, '/call/linkedin/' + path.lstrip('/'), headers=HEADERS, json=body, params=params)
    if r.status_code >= 400:
        raise RuntimeError(f'API {r.status_code}: {r.text[:1800]}')
    return r

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('action', choices=['upload', 'publish', 'verify']); a = ap.parse_args()
    os.environ.pop('TREG_TOKEN', None)  # use the CLI's saved credential
    s = json.loads(STATE.read_text()) if STATE.exists() else {}
    text = CAPTION.read_text(); data = IMAGE.read_bytes()
    assert len(text) <= 3000 and data.startswith(b'\x89PNG\r\n\x1a\n')
    hashes = {'caption_sha256': hashlib.sha256(text.encode()).hexdigest(),
              'image_sha256': hashlib.sha256(data).hexdigest()}
    with _client(_load_config()) as c:
        who = req(c, 'GET', 'v2/userinfo').json()
        assert 'urn:li:person:' + who['sub'] == AUTHOR, 'Connected member is not the approved author'
        if a.action == 'upload':
            assert not s.get('image_urn'), 'Upload exists: reconcile instead'
            v = req(c, 'POST', 'rest/images', {'initializeUploadRequest': {'owner': AUTHOR}},
                   params={'action': 'initializeUpload'}).json()['value']
            s.update(hashes); s.update({'author': AUTHOR, 'image_urn': v['image'], 'caption_characters': len(text),
                                        'visibility': 'PUBLIC', 'approval': APPROVAL, 'caption_file': CAPTION.name,
                                        'image_file': IMAGE.name, 'provider': 'linkedin via treg team-owned proxy',
                                        'catalog_cost_usd': 0})
            save(s)
            u = urlparse(v['uploadUrl'])
            assert u.scheme == 'https' and (u.hostname.endswith('.linkedin.com') or u.hostname.endswith('.licdn.com'))
            r = httpx.put(v['uploadUrl'], content=data, headers={'Content-Type': 'image/png'}, timeout=120)
            s['upload_http_status'] = r.status_code; save(s)
            assert r.status_code < 300, f'Upload failed {r.status_code}'
            for _ in range(12):
                r = c.get('/call/linkedin/rest/images/' + quote(v['image'], safe=''), headers=HEADERS)
                s['image_readback_http_status'] = r.status_code
                if r.status_code == 403:
                    s['image_status'] = 'UPLOADED_READ_FORBIDDEN'; save(s); break
                r.raise_for_status(); im = r.json(); s['image_status'] = im.get('status'); save(s)
                if im.get('status') == 'AVAILABLE':
                    assert im.get('owner') == AUTHOR
                    s['image_readback'] = {k: im.get(k) for k in ['id', 'owner', 'status']}; save(s); break
                assert im.get('status') != 'PROCESSING_FAILED'; time.sleep(2)
            print(json.dumps({k: s.get(k) for k in ['image_urn', 'upload_http_status', 'image_status', 'image_readback_http_status']}))
        elif a.action == 'publish':
            assert s.get('image_status') in ['AVAILABLE', 'UPLOADED_READ_FORBIDDEN']
            assert not s.get('create_attempted'), 'Create attempted: reconcile, never blindly retry'
            assert all(s.get(k) == v for k, v in hashes.items()), 'Approved files changed'
            commentary = re.sub(r'([\\()\[\]{}<>@|~])', r'\\\1', text)
            payload = {'author': AUTHOR, 'commentary': commentary, 'visibility': 'PUBLIC',
                       'distribution': {'feedDistribution': 'MAIN_FEED', 'targetEntities': [], 'thirdPartyDistributionChannels': []},
                       'content': {'media': {'id': s['image_urn']}}, 'lifecycleState': 'PUBLISHED',
                       'isReshareDisabledByAuthor': False}
            s['create_attempted'] = True; save(s)  # marker BEFORE sending
            r = c.post('/call/linkedin/rest/posts', headers=HEADERS, json=payload)
            s['create_http_status'] = r.status_code; s['create_response_body'] = r.text[:3000]
            s['create_response_headers'] = {k: v for k, v in r.headers.items() if k.lower() in ['x-restli-id', 'location']}
            urn = r.headers.get('x-restli-id')  # 201 has an empty body; URN is here
            if not urn and r.content:
                try: urn = r.json().get('id')
                except ValueError: pass
            s['post_urn'] = urn
            if urn: s['post_url'] = 'https://www.linkedin.com/feed/update/' + urn + '/'
            save(s)
            print(json.dumps({k: s.get(k) for k in ['create_http_status', 'post_urn', 'post_url']}))
            assert r.status_code == 201 and urn, 'Reconcile creation; do not retry'
        else:
            assert s.get('post_urn')
            r = c.get('/call/linkedin/rest/posts/' + quote(s['post_urn'], safe=''), headers=HEADERS,
                      params={'viewContext': 'AUTHOR'})
            s['post_readback_http_status'] = r.status_code; save(s)
            if r.status_code == 403:
                # read-permission limit, NOT a failed publish — verify the public URL in a browser instead
                print(json.dumps({'status': 403, 'next': 'Verify exact public URL in browser; do not republish', 'url': s['post_url']})); return
            r.raise_for_status(); p = r.json()
            assert p['author'] == AUTHOR and p['visibility'] == 'PUBLIC' and p['lifecycleState'] == 'PUBLISHED'
            assert p['content']['media']['id'] == s['image_urn']
            assert re.sub(r'\\([\\()\[\]{}<>@|~])', r'\1', p['commentary']) == text
            s['verified_api'] = True; save(s)
            print(json.dumps({'verified_api': True, 'url': s['post_url']}))

if __name__ == '__main__':
    main()
