# Thomas Property Services — website source

Phase 1 website foundation, Phase 2 enquiry code and Phase 3 content systems, built from the supplied development specification. HTML, CSS and vanilla JavaScript; no frontend framework or runtime npm packages. Python is used only to generate static pages. Cloudflare Pages Functions handle enquiries once the external services are configured.

**Content editing: [Phase 3 guide](docs/PHASE-3.md).** The owner reports Phase 2 account setup complete; this work does not independently claim an end-to-end live delivery test. Genuine photos and permissioned reviews are not yet supplied, so those pages and sections remain hidden. No deployment, push or account changes were made by this implementation. The [Phase 2 checklist](docs/PHASE-2.md) remains the technical integration reference.

## Build and check

Python 3.10+ is required to build. Node 24 is recommended for dependency-free tests, which use `node:sqlite`.

```powershell
python scripts/build.py
python scripts/check.py
python -m unittest discover -s tests -p test_content.py
node scripts/check-navigation.cjs
node --test tests/*.test.mjs
python -m http.server 8000 --directory dist --bind 127.0.0.1
```

Open http://127.0.0.1:8000/ . This static server previews pages, but cannot run Functions: online enquiries correctly remain unavailable. Stop with Ctrl+C. Rebuild and refresh after editing source. Root-relative links require HTTP serving, rather than opening HTML files directly. Full local Cloudflare runtime instructions are in the Phase 2 checklist.

## Source structure

- `data/business.json`: confirmed business details and supplied Facebook link.
- `data/faqs.json`: general and service-specific FAQ content.
- `data/images.json`, `data/content-settings.json`: approved imagery, source/licence records, responsive variants and hero/service placements.
- `data/reviews.json`, `data/projects.json`: permission-gated review and genuine project content.
- `scripts/content.py`: validation and reusable review/gallery/image/FAQ rendering.
- `data/services.json`: five services, plus clearly labelled draft House MOT/ongoing maintenance scope.
- `templates/page.html`: shared navigation, footer and mobile contact controls.
- `templates/quote-form.html`: accessible enquiry form and genuine response states.
- `templates/privacy-content.html`: privacy draft; retention periods/processor arrangements need confirmation.
- `scripts/build.py`: generates thirteen base HTML documents (including Mould Removal) plus approved review/gallery/project pages, assets, security headers and development SEO files in ignored `dist/`.
- `assets/css/site.css`: logo-sampled blue/gold design, responsive layouts and accessibility styles.
- `assets/js/site.js`: mobile navigation, service disclosure and quote preselection.
- `assets/js/gallery.js`: progressive category filtering when enough approved projects exist.
- `assets/js/enquiry.js`: validation, Turnstile setup, loading/error/success/retry states and non-persistent drafts.
- `lib/validation.mjs`: validation shared by browser/server; build copies it into public assets.
- `lib/enquiry.mjs`: secure enquiry handling and plain-text business/acknowledgement templates.
- `functions/api/enquiry.js` and `functions/api/form-config.js`: Cloudflare Pages endpoints.
- `migrations/0001_enquiries.sql`: D1 tables for rate limits and duplicate protection; no enquiry content in D1.
- `tests/`: API, SQLite, validation and frontend state tests with simulated external providers.
- `wrangler.example.jsonc`: optional local development template; not production configuration.
- `docs/ASSETS.md`: supplied logo/colour sampling and missing photography register.
- `docs/PHASE-1.md`: historical Phase 1 handover, superseded by Phase 2 where behaviour changed.

Generated pages cover `/`, `/services/`, all five service routes, `/contact/`, `/request-quote/`, `/faqs/`, `/privacy-policy/` and `404.html`. Shared editable content is generated at build time, with complete HTML available without client-side rendering. The form requires JavaScript for secure spam protection; telephone/email links remain available without it.

## Cloudflare Pages setup

For an existing Git-connected project: repository root is the project root, build command is `python scripts/build.py`, output is `dist`. Keep `functions/` at repository root so Cloudflare compiles it. Dashboard drag-and-drop uploads do not compile this Functions directory. Direct Upload projects can use Wrangler; migrating to Git integration requires a new Git-integrated project. See the Phase 2 guide before changing anything.

Configure the D1 binding, Turnstile and Resend values listed in `.env.example`; set secrets in Cloudflare, never in public assets, Git, chat or command arguments. The form fails closed when required settings are missing or `ENQUIRIES_ENABLED` is not `true`. Preview environments should use separate settings and test resources. Changes to bindings or secrets need a redeploy.

A custom 404 document is supplied. Python's preview server returns its own generic page for unknown routes; inspect `/404.html` to review the designed layout.

Development output remains non-indexable: HTML robots tags, `robots.txt` and Cloudflare response headers block indexing; the sitemap is valid but empty. Canonicals use the confirmed future business domain without configuring it. Public sitemap/structured data and an analytics provider remain later-phase work. Only local, non-personal conversion hooks are present. Missing photography and privacy/service scope review notices remain visible.

## Updating content

Change business information in `data/business.json`, service descriptions in `data/services.json` and page copy in `scripts/build.py` or templates; rebuild and test. Actual logo colours now drive CSS and theme metadata; see the asset register. The original logo remains unchanged.

Add approved optimised photographs under `assets/images/` and register them in `data/images.json`, including actual dimensions, alt text, source/licence and permission details. Assign hero/service image IDs in `data/content-settings.json`. Approved placements automatically replace placeholders and use responsive sources, eager hero loading and lazy below-the-fold images. Licensed stock receives an illustrative-image label and cannot be used as a project photograph.

Reviews and project JSON files are intentionally empty. Approved, permissioned entries now automatically generate their pages, navigation and homepage sections. Before adding reviews, obtain permission and verified text, display name/initials, optional date, service and source. Before adding projects, obtain authorised titles, categories, descriptions and genuine photographs, with general locations only where separately authorised. Keep unfinished entries `approved: false`; private consent evidence belongs outside Git. The [Phase 3 guide](docs/PHASE-3.md) contains full formats. Never invent content or add fictional examples to the live data files. Rebuilding removes stale pages/assets when approval is withdrawn; review before pushing to an automatically deployed branch.

## Publication and rollback

Review and test before pushing: Git-connected Cloudflare projects may automatically deploy the configured production branch. No production release or domain/DNS change is authorised by this repository. Keep development indexing blocks until an approved launch review, and remove placeholders only after supplying verified replacements.

To undo a release, restore the previously approved deployment in Cloudflare, then revert the responsible source commit and rebuild. Avoid retrying uncertain enquiries with changed content; telephone follow-up prevents duplicate email requests. Account credentials should remain in hosting settings and ignored local `.dev.vars` files, with separate preview/production resources as appropriate.
