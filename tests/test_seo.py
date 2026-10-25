from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from seo import SEO


class SEOTest(unittest.TestCase):
    def setUp(self):
        self.business = json.loads((ROOT / 'data/business.json').read_text(encoding='utf-8'))
        self.services = json.loads((ROOT / 'data/services.json').read_text(encoding='utf-8'))

    def test_preview_is_safe_and_sitemap_empty(self):
        seo = SEO(ROOT, self.business, self.services, mode='preview')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            seo.structured_data('/', 'Home', 'Description')
            seo.write_files(out, ['/', '/services/', '/404.html'])
            self.assertIn('Disallow: /', (out / 'robots.txt').read_text())
            self.assertIn('X-Robots-Tag: noindex', (out / '_headers').read_text())
            self.assertIn('sha256-', (out / '_headers').read_text())
            self.assertEqual(len(ET.parse(out / 'sitemap.xml').getroot()), 0)

    def test_production_requires_all_release_checks(self):
        with self.assertRaisesRegex(ValueError, 'Production build blocked'):
            SEO(ROOT, self.business, self.services, mode='production')

    def test_approved_production_sitemap_excludes_404(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            flags = ['privacyNoticeApproved', 'serviceScopeApproved', 'liveEmailTestsPassed', 'previewReviewPassed', 'productionReleaseApproved']
            (root / 'data/release.json').write_text(json.dumps({flag: True for flag in flags}))
            seo = SEO(root, self.business, self.services, mode='production')
            seo.write_files(root, ['/', '/services/', '/404.html'])
            locations = [node.text for node in ET.parse(root / 'sitemap.xml').findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
            self.assertEqual(locations, [self.business['domain'] + '/', self.business['domain'] + '/services/'])
            self.assertIn('Sitemap:', (root / 'robots.txt').read_text())

    def test_schema_contains_only_confirmed_business_and_service_facts(self):
        seo = SEO(ROOT, self.business, self.services, mode='preview')
        graph = seo.graph('/services/mould-removal/', 'Mould Removal', 'Description')['@graph']
        service = next(node for node in graph if node['@type'] == 'Service')
        self.assertEqual(service['areaServed'], self.business['area'])
        business = graph[0]
        for key in ('address', 'geo', 'openingHours', 'aggregateRating', 'award', 'foundingDate'):
            self.assertNotIn(key, business)
        crumbs = next(node for node in graph if node['@type'] == 'BreadcrumbList')
        self.assertEqual([item['position'] for item in crumbs['itemListElement']], [1, 2, 3])

    def test_structured_data_cannot_close_its_script_element(self):
        seo = SEO(ROOT, self.business, self.services, mode='preview')
        script = seo.structured_data('/', '</script><script>alert(1)</script>', 'Test')
        self.assertEqual(script.count('</script>'), 1)
        self.assertIn('\\u003c', script)


if __name__ == '__main__':
    unittest.main()
