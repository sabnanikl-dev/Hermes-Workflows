#!/usr/bin/env python3
"""Kroger OAuth authorization-code add-to-cart helper.

Starts a local callback server, prints an authorize URL for the user to open,
then exchanges the code and calls PUT /v1/cart/add.

Never prints client_secret, access_token, refresh_token, or auth code.
"""
import argparse, base64, gzip, json, secrets, threading, time, urllib.parse, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

RESULT = {}


def read_creds(path):
    vals = {}
    for line in Path(path).read_text().splitlines():
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
            if resp.headers.get('Content-Encoding') == 'gzip': raw = gzip.decompress(raw)
            return resp.status, raw.decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        raw = e.read()
        if e.headers.get('Content-Encoding') == 'gzip': raw = gzip.decompress(raw)
        return e.code, raw.decode('utf-8', errors='replace')


def as_json(body):
    try: return json.loads(body)
    except Exception: return None


def make_handler(expected_state):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if parsed.path != '/callback':
                self.send_response(404); self.end_headers(); return
            if qs.get('error'):
                RESULT['error'] = qs.get('error', ['unknown'])[0]
                RESULT['error_description'] = qs.get('error_description', [''])[0]
                msg = 'OAuth failed/denied. Return to Hermes.'
            elif qs.get('code'):
                RESULT['code'] = qs['code'][0]
                if qs.get('state', [''])[0] != expected_state:
                    RESULT['state_warning'] = 'state_mismatch'
                msg = 'Kroger OAuth success. You can close this tab and return to Hermes.'
            else:
                RESULT['error'] = 'missing_code'
                msg = 'OAuth callback missing code. Return to Hermes.'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'<html><body><h2>{msg}</h2></body></html>'.encode())
    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--creds', default='/Users/creator/projects/grocery-shopper/client_secret')
    ap.add_argument('--redirect-uri', default='http://localhost:8000/callback')
    ap.add_argument('--scope', default='cart.basic:write profile.compact')
    ap.add_argument('--timeout-seconds', type=int, default=900)
    ap.add_argument('--item', action='append', required=True, help='UPC:quantity:modality, e.g. 0005100001251:1:PICKUP')
    args = ap.parse_args()

    base = 'https://api.kroger.com'
    oauth = base + '/v1/connect/oauth2'
    api = base + '/v1'
    client_id, client_secret = read_creds(args.creds)
    state = secrets.token_urlsafe(24)

    items = []
    for raw in args.item:
        upc, qty, modality = raw.split(':', 2)
        items.append({'upc': upc, 'quantity': int(qty), 'modality': modality})

    params = urllib.parse.urlencode({
        'scope': args.scope,
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': args.redirect_uri,
        'state': state,
    })
    auth_url = oauth + '/authorize?' + params
    print('client_id:', client_id)
    print('client_secret: [REDACTED]')
    print('items:', json.dumps(items))
    print('AUTH_URL:', auth_url, flush=True)

    httpd = HTTPServer(('localhost', urllib.parse.urlparse(args.redirect_uri).port or 8000), make_handler(state))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True); thread.start()
    deadline = time.time() + args.timeout_seconds
    while time.time() < deadline and 'code' not in RESULT and 'error' not in RESULT:
        time.sleep(0.25)
    httpd.shutdown()

    if 'code' not in RESULT:
        print('OAuth did not complete:', RESULT)
        raise SystemExit(1)
    if RESULT.get('state_warning'):
        print('Warning:', RESULT['state_warning'])

    auth = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    data = urllib.parse.urlencode({'grant_type': 'authorization_code', 'code': RESULT['code'], 'redirect_uri': args.redirect_uri}).encode()
    status, body = request('POST', oauth + '/token', {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
    }, data)
    tok = as_json(body) or {}
    print('token exchange status:', status)
    if not tok.get('access_token'):
        print('error:', tok.get('error'))
        print('error_description:', tok.get('error_description'))
        raise SystemExit(1)
    print('access_token: [REDACTED]')

    status, body = request('PUT', api + '/cart/add', {
        'Authorization': f"Bearer {tok['access_token']}",
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
    }, json.dumps({'items': items}).encode())
    print('cart add status:', status)
    if status != 204:
        print('response:', body[:1000])
        raise SystemExit(1)
    print('SUCCESS: Kroger returned 204 No Content.')

if __name__ == '__main__':
    main()
