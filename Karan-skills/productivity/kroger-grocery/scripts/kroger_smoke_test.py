#!/usr/bin/env python3
"""Kroger public API smoke test: token + locations + products.

Reads credentials from /Users/creator/projects/grocery-shopper/client_secret by default.
Never prints client_secret or tokens.
"""
import argparse, base64, gzip, json, urllib.parse, urllib.request, urllib.error
from pathlib import Path


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--creds', default='/Users/creator/projects/grocery-shopper/client_secret')
    ap.add_argument('--env', choices=['production', 'certification'], default='production')
    ap.add_argument('--zip', default='45202')
    ap.add_argument('--term', default='milk')
    args = ap.parse_args()

    base = 'https://api.kroger.com' if args.env == 'production' else 'https://api-ce.kroger.com'
    client_id, client_secret = read_creds(args.creds)
    auth = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    data = urllib.parse.urlencode({'grant_type': 'client_credentials', 'scope': 'product.compact'}).encode()
    status, body = request('POST', base + '/v1/connect/oauth2/token', {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
    }, data)
    tok = as_json(body) or {}
    print('client_id:', client_id)
    print('token status:', status)
    if not tok.get('access_token'):
        print('error:', tok.get('error'))
        print('error_description:', tok.get('error_description'))
        raise SystemExit(1)
    print('access_token: [REDACTED]')

    headers = {'Authorization': f"Bearer {tok['access_token']}", 'Accept': 'application/json', 'Accept-Encoding': 'gzip'}
    loc_url = base + '/v1/locations?' + urllib.parse.urlencode({'filter.zipCode.near': args.zip, 'filter.limit': '1'})
    status, body = request('GET', loc_url, headers)
    loc = as_json(body) or {}
    print('locations status:', status)
    location_id = None
    if loc.get('data'):
        first = loc['data'][0]
        location_id = first.get('locationId')
        print('location:', location_id, first.get('name'))

    params = {'filter.term': args.term, 'filter.limit': '3'}
    if location_id: params['filter.locationId'] = location_id
    prod_url = base + '/v1/products?' + urllib.parse.urlencode(params)
    status, body = request('GET', prod_url, headers)
    products = as_json(body) or {}
    print('products status:', status)
    for p in products.get('data', [])[:3]:
        item = (p.get('items') or [{}])[0]
        print('-', p.get('description'), '| upc=' + str(p.get('upc')), '| stock=' + str((item.get('inventory') or {}).get('stockLevel')), '| curbside=' + str((item.get('fulfillment') or {}).get('curbside')))

if __name__ == '__main__':
    main()
