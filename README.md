# Thomas Property Services — Phase 1

Responsive static website foundation built from the supplied Website Development Specification v1.0. No frontend framework, npm packages, third-party fonts or runtime dependencies. No deployment or DNS changes have been made.

## Run locally

Requires Python 3.10+; Node is optional for the navigation checks.

```powershell
python scripts/build.py
python scripts/check.py
node --check assets/js/site.js
node scripts/check-navigation.cjs
python -m http.server 8000 --directory dist --bind 127.0.0.1
```

Open http://127.0.0.1:8000/ . Stop the server with Ctrl+C. Rebuild after editing source files; refresh the browser. Root-relative links require HTTP serving, rather than opening HTML files directly.

## Structure and implemented pages

- `data/business.json`: confirmed business name, contact details, coverage, supplied Facebook link and logo path.
- `data/services.json`: five services, descriptions, scope, customer benefits and quotation selections.
- `templates/page.html`: shared semantic header, service submenu, footer and mobile contact controls.
- `scripts/build.py`: small standard-library static generator. Outputs twelve complete HTML documents to ignored `dist/`, including `/`, `/services/`, all five requested service routes, `/contact/`, `/request-quote/`, `/faqs/`, `/privacy-policy/` and `404.html`.
- `assets/css/site.css`: provisional colour tokens, system typography, responsive layouts, focus styles and reduced-motion support.
- `assets/js/site.js`: accessible collapsible navigation, Escape/focus handling and service selection from quotation links. Content and contact links are available without JavaScript.
- `assets/images/logo.jpg`: unaltered copy of the supplied logo, displayed through a compact crop that keeps its lettering visible. The original remains at repository root.
- `data/reviews.json` and `data/projects.json`: empty reserved content files for Phase 3; no gallery or testimonial rendering is claimed in Phase 1.
- `scripts/check.py`, `scripts/check-navigation.cjs`: repeatable structural and interaction checks.
- `docs/PHASE-1.md`: assumptions, validation and next steps.

Generated HTML is intentionally not maintained in Git. This avoids repeating editable contact information and shared components across twelve files. Python is a build tool only: the output is ordinary HTML/CSS/JavaScript. No JavaScript rendering is needed for page content or SEO metadata.

## Editing content and assets

Update contact details in `data/business.json`, service copy in `data/services.json`, and page-specific copy in `scripts/build.py`; rebuild. Keep claims consistent with the specification. Add approved, optimised photographs under `assets/images/`, replace the placeholder markup in the generator and include image alt text, explicit dimensions and responsive sources. Lazy-load below-the-fold images; do not lazy-load the future hero image. Record permission/licence information in `docs/ASSETS.md`.

Before adding reviews, obtain publication permission and retain verified text, customer display name/initials, optional verified date, service, source and permission record. Before adding projects, obtain authorised title, category, optional general location, description and image permissions. Leave the JSON files empty until verified content is available. A gallery/review renderer and navigation links will be added in Phase 3; adding JSON alone does not publish content. Do not add fictional examples to the live content files.

## Phase boundaries

The quotation page is an explicitly labelled input layout with no submission mechanism. It transmits and stores nothing; call/email links work now. Phase 2 will implement client/server validation, Turnstile verification, rate limiting, idempotent email handling, optional acknowledgements and genuine server-confirmed feedback. Do not advertise online submission as operational yet.

The provisional palette follows the requested navy/white/gold tokens. Logo colours remain unmodified; final colour sampling and approval are outstanding. The imagery placeholders are intentional. Reviews and Our Work are omitted from navigation until genuine content is approved. The basic FAQ page uses confirmed specification answers. The privacy page is a development draft and requires operator review.

## Preview and future hosting

All output is development-only: HTML robots metadata, `robots.txt` and Cloudflare `_headers` block indexing; the sitemap is valid but empty because no pages are currently indexable. Canonical and Open Graph URLs use the confirmed future domain; this does not configure the domain. Public sitemap population, structured data and analytics remain Phase 4 work.

For a future explicitly authorised Cloudflare Pages preview, use `python scripts/build.py` as the build command and `dist` as the output directory, with Python available in the build image. A top-level `404.html` is supplied for correct Cloudflare unknown-route handling. Python's simple local server returns its own generic 404 for unknown routes; view `/404.html` to review the custom layout.

Do not connect the production domain, change DNS or publish without explicit approval. Before launch, remove all placeholders only after replacing them with verified content, finalise privacy information and production robots directives, and run the launch checks. Keep preview environments non-indexable. Reverting source to a reviewed Git commit and rebuilding provides the local rollback path; once hosting exists, restore the previous approved deployment in its dashboard. Secrets belong in hosting environment settings, never source or public files. `.env.example` records the Phase 1 absence of integrations.
