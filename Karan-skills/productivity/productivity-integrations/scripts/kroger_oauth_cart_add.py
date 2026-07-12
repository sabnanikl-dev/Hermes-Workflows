#!/usr/bin/env python3
"""Kroger OAuth Authorization Code + cart-add smoke helper.

Usage:
  python3 scripts/kroger_oauth_cart_add.py \
    --creds /path/to/client_secret \
    --redirect-uri http://localhost:8000/callback \
    --item 0005100001251:1:PICKUP \
    --item 0000000004225:3:PICKUP

Credential file may contain:
  client_id: ...
  client_secret: ...

The script prints an authorization URL, starts a localhost callback server,
waits for the user to log in/consent in their browser, exchanges the code,
and PUTs the requested items to /v1/cart/add. It redacts tokens/secrets.
"""
import argparse
import base64
import gzip
import json
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def read_creds(path: Path):
    vals = {}
    for line in path.read_text().splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            vals[k.strip()] = v.strip()
    if not vals.get('client_id') or not vals.get('client_secret'):
        raise SystemExit(f'Missing client_id/client_secret in {path}')
    return vals['client_id'], vals['client_secret']


def request(method, url, headers=None, data=None):
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=data)
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            raw = resp.read()
            if resp.headers.get('Content-Encoding') == 'gzip':
                raw = gzip.decompress(raw)
            return resp.status, raw.decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        raw = e.read()
        if e.headers.get('Content-Encoding') == 'gzip':
            raw = gzip.decompress(raw)
        return e.code, raw.decode('utf-8', errors='replace')


def parse_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def parse_item(spec):
    parts = spec.split(':')
    if len(parts) != 3:
        raise argparse.ArgumentTypeError('items must be UPC:quantity:modality, e.g. 0005100001251:1:PICKUP')
    upc, qty, modality = parts
    modality = modality.upper()
    if modality not in {'PICKUP', 'DELIVERY', 'SHIP'}:
        raise argparse.ArgumentTypeError('modality must be PICKUP, DELIVERY, or SHIP')
    return {'upc': upc, 'quantity': int(qty), 'modality': modality}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--creds', required=True, type=Path)
    parser.add_argument('--base', default='https://api.kroger.com')
    parser.add_argument('--redirect-uri', default='http://localhost:8000/callback')
    parser.add_argument('--scope', default='cart.basic:write profile.compact')
    parser.add_argument('--timeout-seconds', type=int, default=900)
    parser.add_argument('--item', action='append', type=parse_item, required=True, help='UPC:quantity:modality')
    args = parser.parse_args()

    client_id, client_secret = read_creds(args.creds)
    oauth = args.base + '/v1/connect/oauth2'
    api = args.base + '/v1'
    state = secrets.token_urlsafe(24)
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if parsed.path != urllib.parse.urlparse(args.redirect_uri).path:
                self.send_response(404); self.end_headers(); return
            if qs.get('state', [''])[0] != state:
                result['error'] = 'state_mismatch'
            elif qs.get('error'):
                result['error'] = qs.get('error', ['unknown'])[0]
                result['error_description'] = qs.get('error_description', [''])[0]
            elif qs.get('code'):
                result['code'] = qs['code'][0]
            else:
                result['error'] = 'missing_code'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            ok = 'code' in result
            self.wfile.write((
                '<h2>Kroger OAuth ' + ('success' if ok else 'failed') + '</h2>'
                '<p>You can close this tab and return to Hermes.</p>'
            ).encode())

    params = urllib.parse.urlencode({
        'scope': args.scope,
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': args.redirect_uri,
        'state': state,
    })
    auth_url = oauth + '/authorize?' + params

    host = urllib.parse.urlparse(args.redirect_uri).hostname or 'localhost'
    port = urllib.parse.urlparse(args.redirect_uri).port or 80
    server = HTTPServer((host, port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print('client_id:', client_id)
    print('client_secret: [REDACTED]')
    print('redirect_uri:', args.redirect_uri)
    print('scope:', args.scope)
    print('items:', json.dumps(args.item))
    print('AUTH_URL:', auth_url, flush=True)
    print(f'Waiting up to {args.timeout_seconds}s for browser login...', flush=True)

    deadline = time.time() + args.timeout_seconds
    while time.time() < deadline and 'code' not in result and 'error' not in result:
        time.sleep(0.25)
    server.shutdown()

    if 'code' not in result:
        print('OAuth did not complete:', result)
        return 1

    auth = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'code': result['code'],
        'redirect_uri': args.redirect_uri,
    }).encode()
    status, body = request('POST', oauth + '/token', {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
    }, data)
    token = parse_json(body)
    print('token exchange status:', status)
    if not token or not token.get('access_token'):
        print('token response:', body[:1000])
        return 1
    print('access_token: [REDACTED]')

    payload = {'items': args.item}
    status, body = request('PUT', api + '/cart/add', {
        'Authorization': 'Bearer ' + token['access_token'],
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
    }, json.dumps(payload).encode())
    print('cart add status:', status)
    print('payload:', json.dumps(payload))
    if status == 204:
        print('SUCCESS: Kroger accepted cart mutation (204 No Content).')
        return 0
    print('cart response:', body[:1000])
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
