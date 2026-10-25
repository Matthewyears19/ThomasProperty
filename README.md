# Thomas Property Services — website source

Phase 1 website foundation and Phase 2 enquiry code, built from the supplied development specification. HTML, CSS and vanilla JavaScript; no frontend framework or runtime npm packages. Python is used only to generate static pages. Cloudflare Pages Functions handle enquiries once the external services are configured.

**Start with [the Phase 2 checklist](docs/PHASE-2.md).** Local tests pass; real Cloudflare binding, spam protection and email-delivery tests remain outstanding. No deployment, push or account changes were made by this implementation.

## Build and check

Python 3.10+ is required to build. Node 24 is recommended for dependency-free tests, which use `node:sqlite`.

```powershell
python scripts/build.py
python scripts/check.py
node scripts/check-navigation.cjs
node --test tests/*.test.mjs
python -m http.server 8000 --directory dist --bind 127.0.0.1
```

Open http://127.0.0.1:8000/ . This static server previews pages, but cannot run Functions: online enquiries correctly remain unavailable. Stop with Ctrl+C. Rebuild and refresh after editing source. Root-relative links require HTTP serving, rather than opening HTML files directly. Full local Cloudflare runtime instructions are in the Phase 2 checklist.

## Source structure

- `data/business.json`: confirmed business details and supplied Facebook link.
- `data/services.json`: five services, plus clearly labelled draft House MOT/ongoing maintenance scope.
- `templates/page.html`: shared navigation, footer and mobile contact controls.
- `templates/quote-form.html`: accessible enquiry form and genuine response states.
- `templates/privacy-content.html`: privacy draft; retention periods/processor arrangements need confirmation.
- `scripts/build.py`: generates twelve HTML documents, assets, security headers and development SEO files in ignored `dist/`.
- `assets/css/site.css`: logo-sampled blue/gold design, responsive layouts and accessibility styles.
- `assets/js/site.js`: mobile navigation, service disclosure and quote preselection.
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

Add approved optimised photographs under `assets/images/`, replace placeholder markup, and record source/licence/permission details. Include alt text, explicit image dimensions and responsive sources. Lazy-load below-the-fold images; do not lazy-load the future hero. Do not present stock images as completed work.

Reviews and project JSON files are intentionally empty. Before adding reviews, obtain permission and verified text, display name/initials, optional date, service and source. Before adding projects, obtain authorised titles, categories, descriptions and photographs, with general locations only where authorised. Phase 3 must add rendering/navigation; inserting JSON alone does not publish content. Never invent content or add fictional examples to these files.

## Publication and rollback

Review and test before pushing: Git-connected Cloudflare projects may automatically deploy the configured production branch. No production release or domain/DNS change is authorised by this repository. Keep development indexing blocks until an approved launch review, and remove placeholders only after supplying verified replacements.

To undo a release, restore the previously approved deployment in Cloudflare, then revert the responsible source commit and rebuild. Avoid retrying uncertain enquiries with changed content; telephone follow-up prevents duplicate email requests. Account credentials should remain in hosting settings and ignored local `.dev.vars` files, with separate preview/production resources as appropriate.
