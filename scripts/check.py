"""Check generated routes, metadata, assets, labels and development safeguards."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
import json
from content import Content

ROOT = Path(__file__).resolve().parents[1] / 'dist'
SOURCE = ROOT.parent
content = Content(SOURCE, json.loads((SOURCE / 'data/services.json').read_text(encoding='utf-8')), json.loads((SOURCE / 'data/business.json').read_text(encoding='utf-8')))
build_info = json.loads((ROOT / 'build-info.json').read_text(encoding='utf-8'))

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.tags = []
        self.ids = []
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if 'id' in attrs:
            self.ids.append(attrs['id'])

pages = [Page(p) for p in ROOT.rglob('*.html')]
expected = 7 + len(content.services) + bool(content.reviews) + bool(content.projects) + len(content.projects)
assert len(pages) == expected, f'Expected {expected} pages from approved content'
titles = set()
descriptions = set()
for p in pages:
    source = p.path.read_text(encoding='utf-8')
    assert source.count('<h1>') == 1, p.path
    title = source.split('<title>')[1].split('</title>')[0]
    assert title not in titles, f'Duplicate title: {p.path}'
    titles.add(title)
    description = next(a['content'] for t,a in p.tags if t == 'meta' and a.get('name') == 'description')
    assert description not in descriptions, f'Duplicate description: {p.path}'
    descriptions.add(description)
    assert len(p.ids) == len(set(p.ids)), f'Duplicate ID: {p.path}'
    assert any(t == 'link' and a.get('rel') == 'canonical' for t,a in p.tags)
    assert ('noindex, nofollow' in source) == (not build_info['indexable'] or p.path.name == '404.html')
    schemas = __import__('re').findall(r'<script type="application/ld\+json">(.*?)</script>', source)
    if p.path.name != '404.html':
        assert len(schemas) == 1, 'Exactly one structured-data graph expected'
        graph = json.loads(schemas[0])
        assert graph['@context'] == 'https://schema.org'
        assert not any(key in schemas[0] for key in ('aggregateRating', 'openingHours', 'geo"', 'address"'))
    if p.path.parent.name in ('request-quote', 'contact'):
        assert 'action="/api/enquiry"' in source
        assert 'id="quote-fields" disabled' in source, 'Fail closed until configuration loads'
        assert 'src="/assets/js/enquiry.js"' in source
        assert 'value="General enquiry"' in source
        assert 'aria-describedby="description-hint"' in source
        assert 'area or postcode where the work is to be completed' in source
        assert source.count('<form ') == 1
        if p.path.parent.name == 'contact':
            assert 'value="General enquiry" selected' in source
    for t,a in p.tags:
        if t == 'img':
            assert all(k in a for k in ('alt', 'width', 'height'))
        if t in ('input', 'select', 'textarea'):
            assert any(tag == 'label' and attr.get('for') == a.get('id') for tag,attr in p.tags)
        for key in ('href', 'src'):
            link = a.get(key, '')
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = ROOT / unquote(parts.path.lstrip('/'))
            if parts.path.endswith('/'):
                target /= 'index.html'
            assert target.is_file(), f'Broken {key}: {link} in {p.path}'
        for key in ('aria-controls', 'aria-describedby'):
            for id_ in a.get(key, '').split():
                assert id_ in p.ids, f'Missing ARIA target: {id_}'
    assert 'https://www.facebook.com/ThomasPropertyServices' in source
    assert 'tel:+447410928465' in source
    assert 'mailto:thomaspropertyservicesuk@gmail.com' in source
sitemap = ET.parse(ROOT / 'sitemap.xml')
locations = [node.text for node in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
if build_info['indexable']:
    assert len(locations) == len(pages) - 1
    assert all('/404.html' not in location and '/api/' not in location for location in locations)
else:
    assert not locations
    assert 'Disallow: /' in (ROOT / 'robots.txt').read_text()
assert (ROOT / 'our-work/index.html').is_file() == bool(content.projects)
assert (ROOT / 'reviews/index.html').is_file() == bool(content.reviews)
print(f'PASS: {len(pages)} pages; unique metadata; internal links/assets; labels/ARIA; development safeguards.')
