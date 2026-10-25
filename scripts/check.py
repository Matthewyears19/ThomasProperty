"""Check generated routes, metadata, assets, labels and development safeguards."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'dist'

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
assert len(pages) == 12, 'Expected twelve pages'
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
    assert 'noindex, nofollow' in source
    if p.path.parent.name == 'request-quote':
        assert 'action="/api/enquiry"' in source
        assert 'id="quote-fields" disabled' in source, 'Fail closed until configuration loads'
        assert 'src="/assets/js/enquiry.js"' in source
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
ET.parse(ROOT / 'sitemap.xml')
assert 'Disallow: /' in (ROOT / 'robots.txt').read_text()
assert not (ROOT / 'our-work').exists()
assert not (ROOT / 'reviews').exists()
print(f'PASS: {len(pages)} pages; unique metadata; internal links/assets; labels/ARIA; development safeguards.')
