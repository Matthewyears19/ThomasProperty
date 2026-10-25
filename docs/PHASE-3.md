# Phase 3 — content and trust system

Update: the owner subsequently requested royalty-free illustrative photography and a Mould Removal service. Six locally hosted Pexels photographs now fill the hero, service cards/detail pages and introduction imagery. All remain labelled as stock; the genuine project/review arrays remain empty. The base build now has thirteen pages and six service categories. See `docs/ASSETS.md` for sources and licence details. The original preparation-only status below records the earlier handover.

## Status

The review/gallery/image systems and editable FAQs are implemented. The owner confirmed that genuine project photographs and permissioned reviews are not yet ready, so no projects, testimonials or ratings have been invented. Their JSON files remain empty and no empty Reviews or Our Work pages are generated. Their header/footer links and homepage sections stay hidden until approved content exists.

Phase 3 infrastructure is ready; publishing genuine trust content and replacing photography placeholders remain outstanding. The owner's report that Phase 2 account setup is complete is recorded without claiming a new end-to-end delivery test. This work does not read or change credentials, the existing Wrangler configuration, Cloudflare settings or production deployments.

## What was added

- `scripts/content.py`: validates content and permissions, renders review/project/image/FAQ patterns and rejects unsafe paths/URLs and broken content references.
- `data/faqs.json`: editable general FAQs and service-specific questions, with confirmed policies and cautious House MOT wording. `$phone`, `$email` and `$area` resolve from business configuration.
- `data/images.json`: image source/licence/permission register with alt text, actual dimensions and responsive variants.
- `data/content-settings.json`: optional approved hero/service image assignments.
- `data/reviews.json`: ready for genuine, permissioned testimonials. Cards support display name/initials, optional verified date, service and source; no ratings or review aggregates are generated.
- `data/projects.json`: ready for genuine work, service category, authorised general location, photographs and optional before/after pairs. Each approved project generates a detail page.
- `assets/js/gallery.js`: optional accessible category filtering. The controls appear only with at least six approved projects across at least two categories. Native buttons work with keyboard activation; selected state and result count are announced. Every project remains visible without JavaScript.
- Shared page navigation and homepage sections are generated conditionally. Up to three approved reviews/projects are featured; explicit `featured: true` items take priority, with the first three approved entries as the fallback.
- Header navigation collapses below 1100px to leave room for future Our Work/Reviews links without crowding.
- The generated `dist` directory is rebuilt from scratch after input validation, within a checked project-local path. Revoked content does not leave stale generated pages or assets behind. Only the logo, favicon and approved image files are copied; other draft photographs are not copied wholesale.

## Add content through Git

1. Prepare genuine content and get publication permission. Keep private consent records outside the public repository. Remove identifying details and photograph metadata that should not be published. Use general locations only when authorised.
2. Edit the JSON files below. Keep unfinished entries `approved: false`. The examples in this guide are deliberately incomplete instructions, not business claims or production content.
3. Supply optimised, appropriately licensed JPEG, PNG or WebP images under `assets/images/`. Prefer appropriately sized WebP/JPEG photographs and aim for a few hundred KB rather than multi-megabyte originals. Do not commit private originals, customer addresses or consent evidence. Repository visibility is separate from whether a file is copied to the website.
4. Set `permissionGranted: true` only after obtaining the relevant permission, fill every required field, then set `approved: true`. Image approvals are separate from project/review approvals. Build validation stops on incomplete approved entries.
5. Run the build and checks, inspect the pages and review the diff. If possible, inspect a Cloudflare preview before merging/pushing to the production branch. An existing Git-connected Pages project may deploy automatically on push.

### Image register: `data/images.json`

```json
[
  {
    "id": "replace-with-image-id",
    "approved": false,
    "permissionGranted": false,
    "kind": "project",
    "src": "/assets/images/replace-with-approved-photo.webp",
    "width": 0,
    "height": 0,
    "alt": "Replace with an accurate description of the photograph",
    "source": "Record who supplied the image or its licensed source",
    "licence": "Record the actual licence or permission basis",
    "credit": "Include any required public attribution",
    "variants": []
  }
]
```

Use `kind: "project"` only for genuine Thomas Property Services work. Use `stock` for licensed illustrative stock imagery, or `service` for other approved service imagery that is not being represented as a client project. Gallery projects only accept `project` photographs. Hero/service placements label stock as illustrative and not completed work.

Replace zero dimensions with the real pixel width and height. The build verifies JPEG/PNG/WebP headers and each registered responsive variant. A variant entry is `{"src":"/assets/images/another-size.webp","width":640}`; use the actual width and matching aspect ratio. Each width, including the default image, must be unique. Avoid spaces or URL controls in filenames. All image files must live within `assets/images/`.

The public credit is displayed with service/detail imagery. If attribution is required, supply it in `credit`; `source` and `licence` are maintenance records, not substitutes for required public attribution. The operator is responsible for verifying rights; the software cannot verify a ticked permission flag against actual consent.

### Hero and service assignments: `data/content-settings.json`

```json
{
  "heroImage": null,
  "serviceImages": {}
}
```

Replace `null` with an approved image ID. To assign a service photograph, add an entry such as `"painting-decorating": "APPROVED-IMAGE-ID"` inside `serviceImages`, using a real existing image ID. The hero is eagerly loaded with high fetch priority; service/gallery images below the main heading are lazy-loaded. Images have responsive `srcset`/`sizes`, explicit dimensions and meaningful alt text. Without an assignment the labelled development placeholder remains.

### Reviews: `data/reviews.json`

```json
[
  {
    "id": "replace-with-review-id",
    "approved": false,
    "permissionGranted": false,
    "text": "Paste the exact approved genuine review here",
    "displayName": "Use the customer's approved display name or initials",
    "featured": false
  }
]
```

Optional fields: `date` (a verified `YYYY-MM-DD`, never a guessed/future date), `service` (an existing service slug) and `source` (`{"label":"Approved source label","url":"https://ACTUAL-SOURCE-URL"}`). A source URL is optional; if present, it must use HTTPS. Do not assume a publicly visible Facebook review grants permission to republish it. A review needs approval even if its source is public. Dates may be omitted. No stars or scores are invented.

### Projects: `data/projects.json`

```json
[
  {
    "id": "replace-with-project-id",
    "slug": "replace-with-project-route",
    "approved": false,
    "permissionGranted": false,
    "title": "Use a genuine project title",
    "category": "painting-decorating",
    "description": "Describe only work actually completed by the business",
    "images": [],
    "featured": false
  }
]
```

`images` must contain one or more approved genuine project-image IDs. The first image is the card cover. IDs/slugs must use unique lowercase words/numbers separated by hyphens. Categories are the five existing service slugs. The route becomes `/our-work/PROJECT-SLUG/`.

Optional `location` requires `locationApproved: true`; use a general authorised area, not an address. Optional `beforeAfter` is an object with `before` and `after` image IDs. Both must be distinct and included in `images`. The layout shows the two labelled images together; no slider or drag gesture is required. Other images appear in a responsive grid. Descriptions, names and labels are rendered as escaped text rather than interpreted HTML.

### FAQs: `data/faqs.json`

Each record contains `id`, `question`, `answer` and `services`. All appear on `/faqs/`; a question also appears on each service page named in `services`. Use an empty list for general questions. Keep materials, coverage, response times, guarantees and qualifications consistent with confirmed business policy. Existing House MOT draft labels remain until explicitly approved or edited.

## Validation

```powershell
python scripts/build.py
python scripts/check.py
python -m unittest discover -s tests -p test_content.py
node scripts/check-navigation.cjs
node --test tests/*.test.mjs
```

Fourteen Python tests cover permission gates, drafts, unsafe image paths, missing files, actual dimensions, responsive variants, location consent, before/after references, service assignments, review escaping/dates/URLs, FAQ substitutions and isolated build/unpublish behaviour. Synthetic fixtures are created only inside temporary test directories and are never written into the real site data. Two gallery interaction tests cover filtering and the no-filter case. Existing enquiry tests remain part of the regression suite.

The real build still generates twelve pages because reviews/projects are empty. Static checks adjust automatically when approved content adds pages. Checks verify local links/assets, metadata, field labels and ARIA targets. Populated gallery/review layouts still need visual review with actual approved content and real-device accessibility/performance checks. No live content or production configuration was changed.

Local validation on 25 October 2026: 14 Python content tests, 27 JavaScript tests and the navigation harness pass. The twelve-page real build passes structural/link checks. In the desktop browser the FAQ page rendered correctly, the House MOT answer opened by click and closed by keyboard, and the jet-washing page exposed its relevant service questions. Populated gallery/review routes and subsequent removal were checked in isolated builds using explicitly synthetic fixtures, not published data.

## Remaining inputs and later phases

- Genuine approved customer review text and display names/initials; dates/source only if verified.
- Genuine project details and optimised photographs, with permission to publish.
- Approved hero/service imagery and any required public credits/licence details.
- Optional confirmed base town/priority coverage areas; only Cheshire and surrounding areas are currently stated.
- Any final corrections/approval to the proposed House MOT/ongoing maintenance scope and privacy wording.

Phase 4 remains production SEO/structured data, sitemap and an approved privacy-conscious analytics integration. Development indexing blocks remain. Phase 5 remains measured audits, real-device and end-to-end email tests, preview approval and an expressly authorised production release.
