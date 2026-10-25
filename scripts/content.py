"""Validated, permission-gated Phase 3 content. Uses only Python's standard library."""
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import struct
from string import Template


def text(value):
    return escape(str(value), quote=True)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(item, key):
    value = item.get(key)
    require(isinstance(value, str) and bool(value.strip()), f'{item.get("id", "content")}: {key} must be non-empty text')
    return value.strip()


def image_dimensions(path):
    """Read common image headers so incorrect dimensions cannot cause layout shifts."""
    raw = path.read_bytes()
    if raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw) >= 24:
        return struct.unpack('>II', raw[16:24])
    if raw.startswith(b'\xff\xd8'):
        position = 2
        while position + 4 <= len(raw):
            if raw[position] != 255:
                position += 1
                continue
            marker = raw[position + 1]
            position += 2
            if marker in (0, 255, 216, 217) or 208 <= marker <= 215:
                continue
            length = int.from_bytes(raw[position:position + 2], 'big')
            if marker in (192, 193, 194, 195, 197, 198, 199, 201, 202, 203, 205, 206, 207):
                height, width = struct.unpack('>HH', raw[position + 3:position + 7])
                return width, height
            require(length >= 2, f'Invalid JPEG: {path.name}')
            position += length
    if raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
        mode = raw[12:16]
        if mode == b'VP8X' and len(raw) >= 30:
            return int.from_bytes(raw[24:27], 'little') + 1, int.from_bytes(raw[27:30], 'little') + 1
        if mode == b'VP8 ' and raw[23:26] == b'\x9d\x01\x2a':
            width, height = struct.unpack('<HH', raw[26:30])
            return width & 16383, height & 16383
        if mode == b'VP8L' and len(raw) >= 25 and raw[20] == 47:
            bits = int.from_bytes(raw[21:25], 'little')
            return (bits & 16383) + 1, ((bits >> 14) & 16383) + 1
    raise ValueError(f'Unsupported or malformed image: {path.name}; use JPEG, PNG or WebP')


class Content:
    def __init__(self, root, services, business=None):
        self.root = Path(root).resolve()
        self.services = {service['slug']: service for service in services}
        self.images = {}
        self.public_images = set()
        for image in self.records('images'):
            if image.get('approved') is not True:
                continue
            require(image.get('permissionGranted') is True, f'{image["id"]}: image publication permission required')
            require(image.get('kind') in ('project', 'service', 'stock'), f'{image["id"]}: invalid image kind')
            for key in ('alt', 'source', 'licence'):
                nonempty(image, key)
            require(image.get('presentation', 'photo') in ('photo', 'comparison'), 'Unknown image presentation')
            if 'caption' in image:
                nonempty(image, 'caption')
            require(type(image.get('width')) is int and type(image.get('height')) is int and image['width'] > 0 and image['height'] > 0, 'Positive integer image dimensions required')
            path = self.image_path(image.get('src'))
            require(image_dimensions(path) == (image['width'], image['height']), f'{image["id"]}: dimensions do not match the file')
            self.public_images.add(path)
            variants = image.get('variants', [])
            require(isinstance(variants, list), 'Image variants must be a list')
            widths = {image['width']}
            for variant in variants:
                require(isinstance(variant, dict), 'Image variant must be an object')
                require(type(variant.get('width')) is int and variant['width'] > 0 and variant['width'] not in widths, 'Variant widths must be positive and unique, including the default image')
                candidate = self.image_path(variant.get('src'))
                width, height = image_dimensions(candidate)
                require(width == variant['width'], f'{image["id"]}: variant width does not match the file')
                require(abs(width / height - image['width'] / image['height']) < .02, 'Responsive variants must keep the same aspect ratio')
                widths.add(width)
                self.public_images.add(candidate)
            self.images[image['id']] = image

        self.reviews = []
        for review in self.records('reviews'):
            if review.get('approved') is not True:
                continue
            require(review.get('permissionGranted') is True, f'{review["id"]}: review publication permission required')
            for key in ('text', 'displayName'):
                nonempty(review, key)
            require(review.get('service') in (None, '', *self.services), 'Unknown review service')
            if review.get('date'):
                require(isinstance(review['date'], str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', review['date'])), 'Review date must use YYYY-MM-DD')
                require(date.fromisoformat(review['date']) <= date.today(), 'Review date cannot be in the future')
            if review.get('source'):
                require(isinstance(review['source'], dict), 'Review source must be an object')
                nonempty(review['source'], 'label')
                if review['source'].get('url'):
                    parsed = urlsplit(review['source']['url'])
                    require(parsed.scheme == 'https' and bool(parsed.netloc) and not parsed.username and not parsed.password, 'Review source URL must be a public HTTPS URL')
            self.reviews.append(review)

        self.projects = []
        slugs = set()
        for project in self.records('projects'):
            if project.get('approved') is not True:
                continue
            require(project.get('permissionGranted') is True, f'{project["id"]}: project publication permission required')
            for key in ('title', 'description', 'slug'):
                nonempty(project, key)
            require(bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', project['slug'])) and project['slug'] not in slugs, 'Project slug must be unique and use lowercase words/hyphens')
            slugs.add(project['slug'])
            require(project.get('category') in self.services, 'Unknown project category')
            if project.get('location'):
                nonempty(project, 'location')
                require(project.get('locationApproved') is True, 'Project location requires explicit publication approval')
            require(isinstance(project.get('images'), list) and bool(project['images']), 'Published projects require genuine photographs')
            require(all(isinstance(item, str) for item in project['images']) and len(project['images']) == len(set(project['images'])), 'Project image IDs must be unique strings')
            for image_id in project['images']:
                require(image_id in self.images and self.images[image_id]['kind'] == 'project', 'Project photographs must be approved genuine project images; stock is not accepted')
            if project.get('beforeAfter'):
                pair = project['beforeAfter']
                require(isinstance(pair, dict) and pair.get('before') != pair.get('after') and pair.get('before') in project['images'] and pair.get('after') in project['images'], 'Before/after images must be distinct project photographs')
            self.projects.append(project)

        self.faqs = self.records('faqs')
        for faq in self.faqs:
            for key in ('question', 'answer'):
                nonempty(faq, key)
            try:
                faq['answer'] = Template(faq['answer']).substitute(business or {})
            except (KeyError, ValueError) as error:
                raise ValueError(f'{faq["id"]}: invalid FAQ business-data placeholder') from error
            require(isinstance(faq.get('services'), list) and all(slug in self.services for slug in faq['services']), 'FAQ services must name existing services')
        self.settings = json.loads((self.root / 'data/content-settings.json').read_text(encoding='utf-8-sig'))
        require(isinstance(self.settings, dict) and isinstance(self.settings.get('serviceImages'), dict), 'Content settings require a serviceImages object')
        self.placements = {}
        if self.settings.get('heroImage'):
            self.placements['hero'] = self.settings['heroImage']
        if self.settings.get('introImage'):
            self.placements['intro'] = self.settings['introImage']
        for slug, image_id in self.settings['serviceImages'].items():
            require(slug in self.services, f'Unknown service image placement: {slug}')
            self.placements[slug] = image_id
        require(all(isinstance(image_id, str) and image_id in self.images for image_id in self.placements.values()), 'Image placements must reference approved, permissioned images')
        self.service_galleries = self.settings.get('serviceGalleries', {})
        require(isinstance(self.service_galleries, dict), 'serviceGalleries must be an object')
        for slug, image_ids in self.service_galleries.items():
            require(slug in self.services and isinstance(image_ids, list), 'Service galleries must use existing service slugs and image lists')
            require(all(isinstance(image_id, str) and image_id in self.images for image_id in image_ids), 'Service galleries must reference approved images')
            require(len(image_ids) == len(set(image_ids)), 'Service gallery images must be unique')

    def records(self, name):
        items = json.loads((self.root / 'data' / f'{name}.json').read_text(encoding='utf-8-sig'))
        require(isinstance(items, list), f'{name}.json must contain a list')
        ids = set()
        for item in items:
            require(isinstance(item, dict), f'{name}.json entries must be objects')
            item_id = nonempty(item, 'id')
            require(bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', item_id)) and item_id not in ids, f'{name}.json IDs must be unique lowercase words/hyphens')
            ids.add(item_id)
        return items

    def image_path(self, src):
        require(isinstance(src, str) and src.startswith('/assets/images/'), 'Images must use local /assets/images/ paths')
        require(not any(character in src for character in ('?', '#', '\\', '"', "'", '<', '>', ' ')), 'Use simple image filenames without URL controls or spaces')
        path = (self.root / src.lstrip('/')).resolve()
        require(path.is_relative_to(self.root / 'assets/images') and path.is_file(), f'Image path is missing or outside assets/images: {src}')
        require(path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'), 'Use JPEG, PNG or WebP photographs')
        return path

    def picture(self, image_id, *, hero=False, sizes='(max-width: 640px) 100vw, 50vw'):
        image = self.images[image_id]
        candidates = [(image['width'], image['src'])] + [(v['width'], v['src']) for v in image.get('variants', [])]
        srcset = ', '.join(f'{text(src)} {width}w' for width, src in sorted(candidates))
        loading = 'loading="eager" fetchpriority="high"' if hero else 'loading="lazy"'
        return f'<img src="{text(image["src"])}" srcset="{srcset}" sizes="{text(sizes)}" width="{image["width"]}" height="{image["height"]}" alt="{text(image["alt"])}" decoding="async" {loading}>'

    def service_figure(self, image_id, *, hero=False):
        image = self.images[image_id]
        label = 'Illustrative service photograph — not a completed Thomas Property Services project.' if image['kind'] == 'stock' else ('My work — photograph supplied by Thomas Property Services.' if image['kind'] == 'project' else 'Service photograph — not presented as a completed customer project.')
        if image.get('caption'):
            label = image['caption'] + (' ' + label if image['kind'] == 'stock' else '')
        attribution = f' {image["credit"]}' if image.get('credit') else ''
        classes = 'service-figure comparison' if image.get('presentation') == 'comparison' else 'service-figure'
        larger = f'<a class="comparison-link" href="{text(image["src"])}">View larger before-and-after image</a>' if image.get('presentation') == 'comparison' else ''
        return f'<figure class="{classes}">' + self.picture(image_id, hero=hero) + f'<figcaption>{text(label + attribution)}{larger}</figcaption></figure>'

    def review_cards(self, reviews):
        cards = []
        for review in reviews:
            context = self.services[review['service']]['name'] if review.get('service') else ''
            verified_date = ''
            if review.get('date'):
                value = date.fromisoformat(review['date'])
                verified_date = f'<time datetime="{text(review["date"])}">{value.day} {value.strftime("%B %Y")}</time>'
            source = review.get('source', {})
            source_markup = ''
            if source:
                source_markup = f'<a href="{text(source["url"])}">{text(source["label"])}</a>' if source.get('url') else text(source['label'])
            details = ' · '.join(value for value in (text(context), verified_date, source_markup) if value)
            cards.append(f'<figure class="review-card"><blockquote><p>{text(review["text"])}</p></blockquote><figcaption><strong>{text(review["displayName"])}</strong><span>{details}</span></figcaption></figure>')
        return '<div class="review-grid">' + ''.join(cards) + '</div>'

    def project_cards(self, projects, heading=2):
        cards = []
        for project in projects:
            link = f'/our-work/{project["slug"]}/'
            location = f'<p class="project-location">{text(project["location"])}</p>' if project.get('location') else ''
            cards.append(f'<article class="project-card" data-category="{text(project["category"])}">' + self.picture(project['images'][0], sizes='(max-width: 640px) 100vw, (max-width: 900px) 50vw, 33vw') + f'<div class="project-copy"><span class="eyebrow">{text(self.services[project["category"]]["name"])}</span><h{heading}><a href="{link}">{text(project["title"])}</a></h{heading}>{location}<p>{text(project["description"])}</p><a class="text-link" href="{link}">View project <span aria-hidden="true">↗</span></a></div></article>')
        return '<div class="project-grid" id="project-list">' + ''.join(cards) + '</div>'

    def faq_list(self, faqs):
        return '<div class="faq-list">' + ''.join(f'<details><summary>{text(faq["question"])}</summary><p>{text(faq["answer"])}</p></details>' for faq in faqs) + '</div>'

    @property
    def filter_enabled(self):
        return len(self.projects) >= 6 and len({p['category'] for p in self.projects}) >= 2

    def filters(self):
        if not self.filter_enabled:
            return ''
        categories = {project['category'] for project in self.projects}
        buttons = '<button type="button" data-filter="all" aria-pressed="true">All projects</button>'
        buttons += ''.join(f'<button type="button" data-filter="{text(slug)}" aria-pressed="false">{text(service["name"])}</button>' for slug, service in self.services.items() if slug in categories)
        return '<div class="project-filters" role="group" aria-label="Filter projects by service" hidden>' + buttons + '</div><p id="project-count" role="status" aria-live="polite"></p>'
