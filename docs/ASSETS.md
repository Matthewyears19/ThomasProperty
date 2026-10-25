# Asset register

## Owner-supplied photographs — current placements

Six real photographs were supplied in `website pics/` and explicitly authorised for website use by the owner. Original files remain unchanged. `scripts/prepare_photos.py` exports proportional 640px/960px WebP copies, applies orientation metadata and leaves metadata out of public derivatives. It does not retouch, generate or alter the depicted work. Pillow is needed only to rerun that authoring helper; the normal website build still uses the Python standard library only.

| Original | Placement |
| --- | --- |
| `finished blue room.jpg` | Homepage hero |
| `Bright Neutral Room with Bay Window.png` | Painting/decorating card and detail, homepage introduction |
| `finished white landing.png` | Gloss/woodwork card and detail |
| `hallway before and after.png` | Property improvements card and detail |
| `mouldy ceiling before and after.png` | Mould removal card and detail |
| `mould under kitchen sink before and after.png` | Additional before/after image on the mould removal page |

Comparison composites keep both sides and the original Before/After labels visible, with an option to view a larger image. Captions describe what is visible, without dates, locations, treatment methods or permanent-removal guarantees. They are labelled as my work rather than stock. No standalone project stories or client details were invented.

Jet washing and House MOT retain clearly labelled stock photographs because no supplied photograph establishes those services. Replaced stock entries remain in the register as unapproved drafts and are not copied into the public build. See `data/content-settings.json` for current assignments; `introImage` controls the homepage introduction and `serviceGalleries` adds supplementary service images.

## Royalty-free illustrative photographs — 25 October 2026

The owner requested stock placeholders. The following photographs are downloaded locally in 640px and 1200px JPEG sizes, with responsive sources and visible stock labels. All six were visually inspected. They are illustrative only and must not be used as a completed-work portfolio. The [Pexels License](https://www.pexels.com/license/) permits free commercial website use; no attribution is required, but photographer credits are included. These are royalty-free under that licence, not claimed to be public domain. No recurring external image requests are needed.

| Local filename prefix | Photographer | Original source |
| --- | --- | --- |
| `stock-painting-` | Stephanie Ho | https://www.pexels.com/photo/person-holding-paint-roller-while-painting-the-wall-994164/ |
| `stock-woodwork-` | Max Vakhtbovych | https://www.pexels.com/photo/a-wooden-door-near-the-mirror-8135108/ |
| `stock-improvements-` | Anastasia Shuraeva | https://www.pexels.com/photo/overhead-shot-of-home-improvement-materials-5481512/ |
| `stock-jet-washing-` | Caitlin Whealy | https://www.pexels.com/photo/back-view-of-a-person-pressure-washing-a-house-5652626/ |
| `stock-maintenance-` | La Miko | https://www.pexels.com/photo/tools-on-the-floor-3615716/ |
| `stock-mould-removal-` | Kaboompics | https://www.pexels.com/photo/person-in-glove-wiping-surface-of-sink-in-modern-bathroom-4239113/ |

The mould-removal image illustrates general bathroom cleaning, not a real mould treatment, result or health claim. Details, dimensions and licence records are in `data/images.json`. Replace stock with authorised genuine work photographs when available; keep project permissions separate.

## Earlier asset history

Phase 4 performance update: active stock files now use Pexels-provided 640px and 960px WebP versions at quality 75, with the same source/licence and no change in depicted content. The original JPEG downloads are retained as source assets but are not copied into the generated website. This reduced the measured mobile transfer cost. No additional image provider or tracking was introduced.

| Asset | Source | Status |
| --- | --- | --- |
| `assets/images/logo.jpg` | User-supplied repository `logo.jpg` | Used as supplied, with CSS cropping for the header. Confirm production rights and request a transparent/vector variant if available. |
| `assets/images/favicon.svg` | Simple locally authored letter T | Provisional, pending final brand approval. |
| Service/hero photography | Not supplied | Explicit HTML/CSS development placeholders, not stock images or completed-work claims. |

No remote imagery, third-party fonts or generated project photographs are used.

Phase 2 colour update: sampled the supplied JPEG using System.Drawing. The most frequent blue pixel is `#012A58`; `#E0BD87` is a representative sampled gold from the lettering (JPEG shades vary). These now drive the CSS tokens, favicon and theme colour. The original logo remains unchanged. White and off-white content surfaces remain neutral; the secondary navy is a derived supporting shade.

Phase 3 adds `data/images.json` as the structured register for approved photography and responsive variants. It remains empty because no photographs are supplied. `data/content-settings.json` controls hero/service placement. Unapproved photo files are not copied into generated output. This register does not replace actual licence/consent checks; keep private supporting records outside the repository. See `docs/PHASE-3.md` for formats.
