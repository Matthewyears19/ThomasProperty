"""Dependency-free release checks and static performance budgets (not Lighthouse)."""
from pathlib import Path
from html.parser import HTMLParser
import gzip
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
info = json.loads((OUT / 'build-info.json').read_text(encoding='utf-8'))
failures = []


class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.scripts = []
        self.heading = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img':
            self.images.append(attrs)
        if tag == 'script' and attrs.get('src'):
            self.scripts.append(attrs)
        if re.fullmatch('h[1-6]', tag):
            level = int(tag[1])
            if level > self.heading + 1:
                failures.append(f'Skipped heading level: {level} after {self.heading}')
            self.heading = level


for path in OUT.rglob('*.html'):
    parser = Audit()
    source = path.read_text(encoding='utf-8')
    parser.feed(source)
    if len(gzip.compress(source.encode())) > 25000:
        failures.append(f'HTML exceeds 25KB compressed: {path.relative_to(OUT)}')
    if 'Skip to content' not in source or 'lang="en-GB"' not in source:
        failures.append(f'Missing skip link/language: {path.name}')
    for image in parser.images:
        if 'width' not in image or 'height' not in image or 'alt' not in image:
            failures.append('Image lacks dimensions/alt text')
    for script in parser.scripts:
        if not script.get('src', '').startswith('/assets/') or not ('defer' in script or script.get('type') == 'module'):
            failures.append('Unexpected blocking/external script')
for path in (OUT / 'assets/images').rglob('*'):
    if path.is_file() and path.stat().st_size > 250000:
        failures.append(f'Image exceeds 250KB: {path.name}')
css = (OUT / 'assets/css/site.css').read_bytes()
if len(gzip.compress(css)) > 12000:
    failures.append('CSS exceeds 12KB compressed')
javascript = sum(len(gzip.compress(p.read_bytes())) for p in (OUT / 'assets/js').glob('*') if p.is_file())
if javascript > 18000:
    failures.append('All JavaScript exceeds 18KB compressed')
headers = (OUT / '_headers').read_text()
for setting in ('Content-Security-Policy', 'X-Content-Type-Options', 'frame-ancestors', 'form-action'):
    if setting not in headers:
        failures.append(f'Missing security header: {setting}')
if "'unsafe-inline'" in headers or "'unsafe-eval'" in headers:
    failures.append('Unsafe CSP allowance')
for path in OUT.rglob('*'):
    if path.suffix in ('.html', '.js', '.mjs', '.json'):
        source = path.read_text(encoding='utf-8')
        if re.search(r'\bre_[A-Za-z0-9]{20,}\b', source):
            failures.append(f'Possible provider credential in public output: {path.name}')
if failures:
    raise SystemExit('\n'.join(failures))
print(f'PASS: static accessibility/security checks; CSS {len(gzip.compress(css))}B and JS {javascript}B compressed; images <=250KB; mode={info["mode"]}')
