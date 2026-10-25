"""Check the running local QA preview: python scripts/serve.py."""
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
import json

ROOT = Path(__file__).resolve().parents[1]
info = json.loads((ROOT / 'dist/build-info.json').read_text())
base = 'http://127.0.0.1:8000'
for route in info['routes']:
    with urlopen(base + route) as response:
        assert response.status == 200
        assert response.headers.get('Content-Security-Policy')
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
try:
    urlopen(base + '/this-page-does-not-exist/')
    raise AssertionError('Unknown route should return HTTP 404')
except HTTPError as error:
    assert error.code == 404
    assert 'This page could not be found.' in error.read().decode()
for route in ['/api/form-config', '/api/analytics-config']:
    with urlopen(base + route) as response:
        assert json.load(response)['enabled'] is False
print(f'PASS: {len(info["routes"])} local pages, headers, designed HTTP 404 and disabled local integrations')
