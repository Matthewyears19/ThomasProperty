"""Synthetic fixtures exist only in temporary test directories, never site content."""
from pathlib import Path
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from content import Content


def png(width=4, height=3):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress((b'\x00' + b'\x80\x80\x80' * width) * height)) + chunk(b'IEND', b'')


class ContentTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        (self.root / 'assets/images').mkdir(parents=True)
        for name in ('reviews', 'projects', 'images', 'faqs'):
            self.write(name, [])
        self.write('content-settings', {'heroImage': None, 'serviceImages': {}})
        self.services = [{'slug': 'test-service', 'name': 'Test service'}, {'slug': 'other-service', 'name': 'Other service'}]

    def write(self, name, data):
        (self.root / f'data/{name}.json').write_text(json.dumps(data), encoding='utf-8')

    def load(self):
        return Content(self.root, self.services, {'phone': 'test telephone'})

    def image(self, id='test-photo', kind='project'):
        (self.root / f'assets/images/{id}.png').write_bytes(png())
        return {'id': id, 'approved': True, 'permissionGranted': True, 'kind': kind, 'src': f'/assets/images/{id}.png', 'width': 4, 'height': 3, 'alt': 'Synthetic test image', 'source': 'Test fixture only', 'licence': 'Test fixture only'}

    def review(self):
        return {'id': 'test-review', 'approved': True, 'permissionGranted': True, 'text': 'SYNTHETIC TEST ONLY <script>', 'displayName': 'Test <name>', 'service': 'test-service', 'featured': True}

    def project(self, id='test-project', category='test-service'):
        return {'id': id, 'slug': id, 'approved': True, 'permissionGranted': True, 'title': 'SYNTHETIC TEST ONLY', 'description': 'Temporary fixture, never real work.', 'category': category, 'images': ['test-photo']}

    def test_empty_content_produces_no_trust_content(self):
        result = self.load()
        self.assertEqual(result.projects, [])
        self.assertEqual(result.reviews, [])
        self.assertFalse(result.filter_enabled)

    def test_drafts_are_excluded_even_with_unfinished_fields(self):
        self.write('reviews', [{'id': 'draft', 'approved': False}])
        self.write('projects', [{'id': 'draft'}])
        self.write('images', [{'id': 'draft', 'approved': False, 'src': '/missing.png'}])
        self.assertEqual(self.load().reviews, [])
        self.assertEqual(self.load().public_images, set())

    def test_permission_required_for_each_approved_content_type(self):
        for name, entry in [('images', self.image()), ('reviews', self.review()), ('projects', self.project())]:
            with self.subTest(name=name):
                entry['permissionGranted'] = False
                self.write(name, [entry])
                with self.assertRaisesRegex(ValueError, 'permission required'):
                    self.load()
                self.write(name, [])

    def test_duplicate_ids_are_rejected(self):
        entry = self.review()
        self.write('reviews', [entry, entry])
        with self.assertRaisesRegex(ValueError, 'unique'):
            self.load()

    def test_reviews_escape_text_and_reject_unsafe_urls_dates_and_categories(self):
        review = self.review()
        self.write('reviews', [review])
        html = self.load().review_cards([review])
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)
        self.assertNotIn('rating', html)
        for patch in [{'source': {'label': 'Bad', 'url': 'javascript:alert(1)'}}, {'date': '2999-01-01'}, {'date': '2025-13-99'}, {'service': 'unconfirmed-service'}]:
            self.write('reviews', [{**review, **patch}])
            with self.assertRaises(ValueError):
                self.load()

    def test_project_images_must_be_genuine_and_location_permission_is_separate(self):
        image = self.image(kind='stock')
        self.write('images', [image]); self.write('projects', [self.project()])
        with self.assertRaisesRegex(ValueError, 'stock is not accepted'):
            self.load()
        image['kind'] = 'project'; self.write('images', [image])
        self.write('projects', [{**self.project(), 'location': 'Test location'}])
        with self.assertRaisesRegex(ValueError, 'location requires'):
            self.load()
        self.write('projects', [{**self.project(), 'location': 'Test location', 'locationApproved': True}])
        self.assertIn('Test location', self.load().project_cards(self.load().projects))

    def test_invalid_paths_missing_files_and_wrong_dimensions_are_rejected(self):
        image = self.image()
        for patch in [{'src': '/assets/images/../../data/reviews.json'}, {'src': 'https://example.com/a.png'}, {'src': '/assets/images/missing.png'}, {'width': 100}, {'src': '/assets/images/test photo.png'}]:
            self.write('images', [{**image, **patch}])
            with self.assertRaises(ValueError):
                self.load()

    def test_responsive_images_have_verified_sizes_alt_and_loading_policy(self):
        image = self.image()
        (self.root / 'assets/images/variant.png').write_bytes(png(8, 6))
        image['variants'] = [{'src': '/assets/images/variant.png', 'width': 8}]
        self.write('images', [image])
        content = self.load()
        html = content.picture('test-photo')
        self.assertIn('width="4" height="3"', html)
        self.assertIn('8w', html)
        self.assertIn('loading="lazy"', html)
        self.assertIn('fetchpriority="high"', content.picture('test-photo', hero=True))
        self.assertEqual(len(content.public_images), 2)

    def test_stock_service_figure_is_clearly_labelled(self):
        self.write('images', [self.image(kind='stock')])
        self.assertIn('not a completed Thomas Property Services project', self.load().service_figure('test-photo'))

    def test_before_after_pairs_must_be_distinct_project_photos(self):
        self.write('images', [self.image()])
        self.write('projects', [{**self.project(), 'beforeAfter': {'before': 'test-photo', 'after': 'test-photo'}}])
        with self.assertRaisesRegex(ValueError, 'distinct'):
            self.load()

    def test_filters_require_six_real_projects_and_multiple_categories(self):
        self.write('images', [self.image()])
        projects = [self.project(f'test-{n}', 'test-service' if n % 2 else 'other-service') for n in range(6)]
        self.write('projects', projects[:5]); self.assertFalse(self.load().filter_enabled)
        self.write('projects', projects); self.assertTrue(self.load().filter_enabled)
        self.assertIn('hidden', self.load().filters())

    def test_faqs_are_escaped_and_contact_details_are_centralised(self):
        self.write('faqs', [{'id': 'question', 'question': 'Test <question>', 'answer': 'Call $phone', 'services': ['test-service']}])
        content = self.load()
        html = content.faq_list(content.faqs)
        self.assertIn('Test &lt;question&gt;', html)
        self.assertIn('Call test telephone', html)

    def test_only_approved_images_can_be_assigned_to_service_pages(self):
        self.write('content-settings', {'heroImage': 'unknown', 'serviceImages': {}})
        with self.assertRaisesRegex(ValueError, 'approved'):
            self.load()

    def test_genuine_comparisons_are_labelled_and_extra_service_images_are_validated(self):
        image = {**self.image(), 'presentation': 'comparison', 'caption': 'Test before and after.'}
        self.write('images', [image])
        self.write('content-settings', {'heroImage': None, 'introImage': 'test-photo', 'serviceImages': {}, 'serviceGalleries': {'test-service': ['test-photo']}})
        content = self.load()
        html = content.service_figure('test-photo')
        self.assertIn('service-figure comparison', html)
        self.assertIn('View larger before-and-after image', html)
        self.assertNotIn('stock', html)
        self.assertEqual(content.placements['intro'], 'test-photo')
        self.write('content-settings', {'heroImage': None, 'serviceImages': {}, 'serviceGalleries': {'test-service': ['missing']}})
        with self.assertRaisesRegex(ValueError, 'approved'):
            self.load()

    def test_build_adds_then_removes_approved_pages_nav_and_assets(self):
        # Isolated checkout. No test content is written to the real data/assets.
        for folder in ('scripts', 'templates', 'assets', 'lib', 'data'):
            shutil.copytree(ROOT / folder, self.root / folder, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
        self.services = json.loads((self.root / 'data/services.json').read_text(encoding='utf-8'))
        photo = self.image()
        self.write('images', [photo])
        review = {**self.review(), 'service': self.services[0]['slug']}
        project = {**self.project(), 'category': self.services[0]['slug']}
        self.write('reviews', [review]); self.write('projects', [project])
        self.write('content-settings', {'heroImage': 'test-photo', 'serviceImages': {}})
        def build():
            return subprocess.run([sys.executable, str(self.root / 'scripts/build.py')], cwd=self.root, check=True, capture_output=True, text=True)
        build()
        home = (self.root / 'dist/index.html').read_text(encoding='utf-8')
        self.assertIn('href="/reviews/"', home)
        self.assertIn('href="/our-work/"', home)
        self.assertIn('loading="eager"', home)
        self.assertTrue((self.root / 'dist/our-work/test-project/index.html').is_file())
        check = subprocess.run([sys.executable, str(self.root / 'scripts/check.py')], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.write('reviews', []); self.write('projects', []); self.write('images', [])
        self.write('content-settings', {'heroImage': None, 'serviceImages': {}})
        build()
        home = (self.root / 'dist/index.html').read_text(encoding='utf-8')
        self.assertNotIn('href="/reviews/"', home)
        self.assertNotIn('SYNTHETIC TEST ONLY', home)
        self.assertFalse((self.root / 'dist/our-work').exists())
        self.assertFalse((self.root / 'dist/reviews').exists())
        self.assertFalse((self.root / 'dist/assets/images/test-photo.png').exists())


if __name__ == '__main__':
    unittest.main()
