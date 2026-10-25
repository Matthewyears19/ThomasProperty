"""Export responsive WebP copies of the owner's supplied photographs.

Authoring helper only (requires Pillow); the website build has no Pillow dependency.
Originals and depicted work remain unchanged: orientation, proportional resize and
compression only. Metadata is not carried into the public derivatives.
"""
from pathlib import Path
from PIL import Image, ImageOps
import json

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = [
    ('real-blue-room', 'finished blue room.jpg', 'Blue-painted room with exposed timber ceiling beams and a white ceiling', 'My decorating work — blue room.', False),
    ('real-white-landing', 'finished white landing.png', 'White-painted landing with white door frames and a dark handrail', 'My decorating work — white landing and woodwork.', False),
    ('real-hallway-comparison', 'hallway before and after.png', 'Side-by-side hallway photographs labelled Before and After, showing preparation and a white-painted finish', 'Hallway preparation and decorating — before and after.', True),
    ('real-ceiling-comparison', 'mouldy ceiling before and after.png', 'Side-by-side landing photographs labelled Before and After, showing a marked ceiling and a white-painted ceiling', 'Landing ceiling — before and after.', True),
    ('real-sink-comparison', 'mould under kitchen sink before and after.png', 'Side-by-side under-sink photographs labelled Before and After, showing dark surface staining and the area with a white finish', 'Under-sink area — before and after.', True),
    ('real-neutral-room', 'Bright Neutral Room with Bay Window.png', 'Neutral-painted room with a bay window, white ceiling and timber-coloured skirting boards', 'My decorating work — neutral room with a bay window.', False),
]


def prepare():
    registry_path = ROOT / 'data/images.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    new_ids = {item[0] for item in PHOTOS}
    registry = [item for item in registry if item['id'] not in new_ids]
    for image_id, filename, alt, caption, comparison in PHOTOS:
        source_path = ROOT / 'website pics' / filename
        with Image.open(source_path) as original:
            source = ImageOps.exif_transpose(original).convert('RGB')
            widths = [640, 960, 1280] if comparison else [640, 960]
            exports = []
            for width in widths:
                if width > source.width:
                    continue
                height = round(source.height * width / source.width)
                resized = source.resize((width, height), Image.Resampling.LANCZOS)
                filename_out = f'{image_id}-{width}.webp'
                resized.save(ROOT / 'assets/images' / filename_out, 'WEBP', quality=82, method=6)
                exports.append({'src': '/assets/images/' + filename_out, 'width': width, 'height': height})
            if not exports:
                raise ValueError(f'Original photo too small: {filename}')
        primary = exports[-1]
        registry.append({
            'id': image_id, 'approved': True, 'permissionGranted': True, 'kind': 'project',
            'src': primary['src'], 'width': primary['width'], 'height': primary['height'],
            'alt': alt, 'caption': caption, 'presentation': 'comparison' if comparison else 'photo',
            'source': 'Owner-supplied: website pics/' + filename,
            'licence': 'Owner supplied and authorised website use in the chat on 25 October 2026.',
            'variants': [{'src': item['src'], 'width': item['width']} for item in exports[:-1]]
        })
    # Retain the stock records as drafts for future use, while publishing only
    # the two services with no matching genuine photographs.
    for item in registry:
        if item['id'].startswith('stock-'):
            item['approved'] = item['id'] in ('stock-jet-washing', 'stock-maintenance')
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    settings = {
        'heroImage': 'real-blue-room',
        'introImage': 'real-neutral-room',
        'serviceImages': {
            'painting-decorating': 'real-neutral-room',
            'gloss-work-wood-finishing': 'real-white-landing',
            'property-improvements': 'real-hallway-comparison',
            'jet-washing': 'stock-jet-washing',
            'house-mot': 'stock-maintenance',
            'mould-removal': 'real-ceiling-comparison'
        },
        'serviceGalleries': {'mould-removal': ['real-sink-comparison']}
    }
    (ROOT / 'data/content-settings.json').write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')
    print('Prepared six owner-supplied photographs; originals preserved.')


if __name__ == '__main__':
    prepare()
