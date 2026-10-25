"""Technical SEO generation; preview builds are non-indexable by default."""
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element, SubElement, tostring
from hashlib import sha256
import base64
import json
import os


class SEO:
    def __init__(self, root, business, services, mode=None):
        self.business = business
        self.services = services
        self.mode = mode or os.environ.get('TPS_BUILD_MODE', 'preview')
        if self.mode not in ('preview', 'production'):
            raise ValueError('TPS_BUILD_MODE must be preview or production')
        self.indexable = self.mode == 'production'
        self.origin = business['domain'].rstrip('/')
        parsed = urlsplit(self.origin)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError('Business domain must be an HTTPS origin without a path')
        if self.indexable:
            approval = json.loads((root / 'data/release.json').read_text(encoding='utf-8'))
            flags = ['privacyNoticeApproved', 'serviceScopeApproved', 'liveEmailTestsPassed', 'previewReviewPassed', 'productionReleaseApproved']
            if not all(approval.get(flag) is True for flag in flags):
                raise ValueError('Production build blocked: complete and record the release checklist in data/release.json first')
        self.hashes = set()

    def graph(self, route, title, description):
        business_id = self.origin + '/#business'
        website_id = self.origin + '/#website'
        url = self.origin + route
        owner = {'@type': 'HomeAndConstructionBusiness', '@id': business_id, 'name': self.business['name'], 'url': self.origin + '/', 'telephone': self.business['phoneHref'].removeprefix('tel:'), 'email': self.business['email'], 'areaServed': self.business['area'], 'logo': self.origin + self.business['logo']}
        if self.business.get('facebook'):
            owner['sameAs'] = [self.business['facebook']]
        website = {'@type': 'WebSite', '@id': website_id, 'url': self.origin + '/', 'name': self.business['name'], 'publisher': {'@id': business_id}, 'inLanguage': 'en-GB'}
        webpage = {'@type': 'ContactPage' if route == '/contact/' else 'WebPage', '@id': url + '#webpage', 'url': url, 'name': title, 'description': description, 'isPartOf': {'@id': website_id}, 'about': {'@id': business_id}, 'inLanguage': 'en-GB'}
        graph = [owner, website, webpage]
        for service in self.services:
            if route == '/services/' + service['slug'] + '/':
                graph.append({'@type': 'Service', '@id': url + '#service', 'name': service['name'], 'serviceType': service['name'], 'description': service['intro'], 'url': url, 'provider': {'@id': business_id}, 'areaServed': self.business['area']})
                webpage['mainEntity'] = {'@id': url + '#service'}
        if route not in ('/', '/404.html'):
            crumbs = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': self.origin + '/'}]
            if route.startswith('/services/') and route != '/services/':
                crumbs.append({'@type': 'ListItem', 'position': 2, 'name': 'Services', 'item': self.origin + '/services/'})
            if route.startswith('/our-work/') and route != '/our-work/':
                crumbs.append({'@type': 'ListItem', 'position': 2, 'name': 'Our Work', 'item': self.origin + '/our-work/'})
            crumbs.append({'@type': 'ListItem', 'position': len(crumbs) + 1, 'name': title, 'item': url})
            graph.append({'@type': 'BreadcrumbList', '@id': url + '#breadcrumbs', 'itemListElement': crumbs})
            webpage['breadcrumb'] = {'@id': url + '#breadcrumbs'}
        return {'@context': 'https://schema.org', '@graph': graph}

    def structured_data(self, route, title, description):
        if route == '/404.html':
            return ''
        raw = json.dumps(self.graph(route, title, description), ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        self.hashes.add("'sha256-" + base64.b64encode(sha256(raw.encode()).digest()).decode() + "'")
        return '<script type="application/ld+json">' + raw + '</script>'

    def navigation_bootstrap(self):
        raw = "document.documentElement.classList.add('js');"
        self.hashes.add("'sha256-" + base64.b64encode(sha256(raw.encode()).digest()).decode() + "'")
        return '<script>' + raw + '</script>'

    def write_files(self, out, routes):
        namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        sitemap = Element('urlset', xmlns=namespace)
        if self.indexable:
            for route in routes:
                if route != '/404.html':
                    node = SubElement(sitemap, 'url')
                    SubElement(node, 'loc').text = self.origin + route
        (out / 'sitemap.xml').write_bytes(tostring(sitemap, encoding='utf-8', xml_declaration=True))
        robots = f'User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {self.origin}/sitemap.xml\n' if self.indexable else 'User-agent: *\nDisallow: /\n'
        (out / 'robots.txt').write_text(robots, encoding='utf-8')
        directives = '' if self.indexable else '  X-Robots-Tag: noindex, nofollow\n'
        csp = "default-src 'self'; script-src 'self' https://challenges.cloudflare.com " + ' '.join(sorted(self.hashes)) + "; connect-src 'self' https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; style-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        (out / '_headers').write_text('/*\n' + directives + "  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  Content-Security-Policy: " + csp + '\n\n/404.html\n  X-Robots-Tag: noindex, nofollow\n\n/assets/*\n  Cache-Control: public, max-age=86400\n', encoding='utf-8')
        (out / 'build-info.json').write_text(json.dumps({'mode': self.mode, 'indexable': self.indexable, 'routes': routes}, indent=2) + '\n', encoding='utf-8')
