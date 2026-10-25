# Phases 4 and 5 — SEO, measurement and release verification

## Status

Phase 4 source implementation is ready for configuration/review. Phase 5 local checks are implemented and have been run; production launch is **not complete**. No deployment, Git push, DNS, secrets, Cloudflare bindings or production settings were changed. The owner reported earlier integration setup complete, but live delivery and the currently deployed version have not been independently verified here.

Read-only live checks on 25 October 2026 against `https://thomaspropertyservices.uk/` confirm HTTP 200 over HTTPS, an existing CSP and the designed HTTP 404 for an unknown route. The live site still returns `X-Robots-Tag: noindex, nofollow`; `robots.txt` disallows all crawling and the sitemap is empty. Its public `/api/form-config` returns `{"enabled":false,"siteKey":null}`. The live enquiry form is therefore unavailable; this response alone cannot identify the missing/disabled setting. `/api/analytics-config` returns 404 because this new phase has not been deployed. No test enquiry, email or analytics event was submitted. Check the deployed runtime environment against the Phase 2 configuration list before live delivery testing. Do not mistake a reachable homepage for an operational enquiry system or an indexable release.

## SEO implementation

`scripts/seo.py` generates consistent canonical URLs, business/website/page structured data, service-specific entities and breadcrumb lists. Facts come from the supplied business/service data. No address, coordinates, qualifications, business age, prices, review rating or opening hours are invented. JSON-LD is escaped and authorised by exact CSP hashes. Social metadata includes the supplied business logo, dimensions, descriptive alt text, British locale and Twitter summary metadata. Page descriptions are limited to 160 characters.

The schema is descriptive structured data, not a promise of Google rich-result eligibility. A service-area business without a confirmed public address may not qualify for some Google LocalBusiness presentations; no fabricated address is supplied to satisfy a validator. FAQ/review rich-result claims are not made.

The default `TPS_BUILD_MODE=preview` keeps HTML robots tags, HTTP indexing directives and `robots.txt` non-indexable, with an empty sitemap. `TPS_BUILD_MODE=production` generates public robots directives and an XML sitemap containing only generated public routes, excluding API and 404 routes. It is blocked unless all checks in `data/release.json` are explicitly true. Those flags remain false. They record real review/testing/approval, not a way to bypass missing checks. Preview deployments must retain preview mode even after production is eventually approved.

No public gallery/review routes are added until genuine approved content exists. No thin town pages are generated. The canonical origin remains the confirmed business domain; configuring that URL in metadata does not configure DNS or deploy a site.

## Optional aggregate analytics

Cloudflare Web Analytics currently lacks custom events, so it cannot independently meet the required call-click and confirmed-enquiry measurement. This implementation instead uses a small first-party D1 aggregation layer, with no external analytics subscription or advertising SDK.

- `/api/analytics-config` exposes only an enabled boolean.
- `/api/metrics` accepts only allowlisted `page_view` and `call_intent` events, exact public paths and an explicit consent flag. It rejects query strings, arbitrary paths, additional properties and client-submitted quote conversions. Same-origin checks, body limits and temporary salted rate-limit buckets apply.
- Visitors choose optional usage statistics using the footer controls. No usage events are sent before opt-in. Declining or withdrawing stops them. Global Privacy Control and Do Not Track are respected. The preference is remembered locally for 180 days; it contains no visitor ID or enquiry details.
- Accepted enquiries are counted authoritatively on the server only after provider acceptance and the stored accepted state. A transactional marker prevents retries counting twice. A statistics outage never turns an accepted enquiry into a failure.
- D1 stores daily totals by event/path, not names, phone numbers, emails, enquiry descriptions, referrers or browsing profiles. IP-derived rate-limit buckets are salted and short lived, not stored in the daily statistics table. Aggregate totals become eligible for removal after 180 days and are cleaned up on later use; fixed physical deletion deadlines require scheduled cleanup. Provider logs/backups are separate.
- Page-view and call counts represent consenting visitors; accepted-enquiry totals are operational counts. Do not divide those differing populations to claim a precise conversion percentage. Call clicks express intent, not a completed conversation. There is no unique-visitor, advertising attribution or cross-device measurement.
- Reporting is via the authenticated Cloudflare D1 console using `docs/analytics-queries.sql`; no public dashboard or metrics-read endpoint is exposed.

To activate after privacy/configuration review: apply `migrations/0002_analytics.sql` **once** to the existing bound database, confirm the updated notice, then set `ANALYTICS_ENABLED=true` in the relevant Pages runtime environment and redeploy through the approved workflow. Leave it unset/false to disable all counting and hide the preference controls. Use separate preview resources for testing. The new migration adds a column as well as a table; do not repeatedly execute it blindly. Existing enquiry settings remain necessary and unchanged.

## Local verification

```powershell
python scripts/verify.py
python scripts/serve.py
# In another terminal:
python scripts/check_http.py
```

The verification command always builds preview output, validates generated routes/metadata/ARIA/assets, runs static accessibility/security/performance budgets, Python content/SEO tests, JavaScript enquiry/analytics/gallery tests and the navigation harness. The local QA server binds only to loopback, emits the generated security headers, returns the designed unknown-route page with HTTP 404 and keeps enquiry/analytics configuration disabled. It does not emulate real Cloudflare integration success.

Representative Lighthouse audits use official Lighthouse 13.5.0 with headless Microsoft Edge, default simulated mobile throttling (4x CPU, 150ms RTT, 1.6Mbps) and its desktop preset. The measured results and exact environment are saved in `docs/lighthouse-results.json`. Raw reports stay in ignored `reports/`. These are local lab results for a static preview with inactive Turnstile, not field Core Web Vitals or measured production delivery. Total Blocking Time is a lab metric and is not a verified INP measurement. SEO is intentionally penalised by preview indexing blocks; those blocks were not removed to raise the score.

| Local audit | Performance | Accessibility | Best practices | LCP | CLS |
| --- | --- | --- | --- | --- | --- |
| Homepage, mobile | 98 | 100 | 100 | 2.4s | 0 |
| Quote page, mobile | 99 | 100 | 100 | 1.8s | 0 |
| Homepage, desktop | 100 | 100 | 100 | 0.6s | 0 |

All three SEO scores are 69 because the audited preview is intentionally non-indexable. Nineteen Python tests and thirty-three JavaScript tests pass, along with navigation, generated-page and HTTP checks. Static compressed payload budgets are approximately 4.5KB CSS and 5.7KB total JavaScript; every public image is below 250KB. The audits also identify remaining image/cache delivery opportunities; repeat on Cloudflare with real compression/cache settings and enabled integrations before making production performance claims.

The initial mobile audit exposed a large menu-induced layout shift. A tiny CSP-hashed bootstrap now establishes the JavaScript navigation state before paint; mobile navigation starts collapsed while the no-JavaScript fallback remains accessible. WebP images reduced delivery cost. The quotation audit also caught an ARIA label on a generic spam-check container; it now has the correct group role, and the form has an accessible title. Static checks caught and corrected a heading-level skip on the Services index.

Automated accessibility scores do not certify full WCAG conformance. Live Turnstile behaviour, real mobile keyboards/assistive technology, tablet/browser coverage and the actual deployed site's headers/cache behaviour remain part of final acceptance.

## Before an approved production release

1. Supply the Cloudflare Pages preview URL and verify the intended source version is deployed there. Review the site on actual mobile/tablet/desktop devices, including keyboard and screen-reader checks.
2. Apply the new analytics migration only if choosing this optional measurement system. Verify footer opt-in/withdrawal, privacy signals, aggregate counts, server conversion deduplication and error behaviour in the preview environment. Confirm all claimed retention and processor details in the privacy notice.
3. Complete actual email-only/phone-only/both-contact tests, business inbox delivery, customer acknowledgement, reply-to, expired spam token, repeated click, retry and provider-failure tests. Check provider logs/delivery statuses without exposing personal data in Git. No real emails were sent by the local test suite.
4. Confirm House MOT/ongoing maintenance/Mould Removal scope and final legal/privacy wording. Record the confirmations in the appropriate content source; draft notices are still present. Keep stock images explicitly illustrative. Missing reviews/projects can stay unpublished.
5. Verify hosting HTTPS, the intended domain/redirects, secure runtime credentials, authenticated email sender and rate-limit/spam configuration. No DNS or provider changes are included in this work.
6. Complete `data/release.json` only against real evidence and explicit production approval. Set the intended production build environment to `TPS_BUILD_MODE=production`; keep previews on `preview`. Review the production build before release, and verify public robots/sitemap/canonicals afterward.
7. After the authorised launch, add the sitemap to Search Console, verify the site's indexing status and check Google Business Profile/contact consistency. These external account steps remain owner actions.

Rollback remains the previously approved Cloudflare deployment plus a source revert/rebuild. Disabling `ANALYTICS_ENABLED` stops collection without disabling enquiries. Never edit/delete customer messages to perform a website rollback.

## Reference sources checked

- [Cloudflare Web Analytics custom-event limitation](https://developers.cloudflare.com/web-analytics/faq/)
- [Schema.org Service](https://schema.org/Service)
- [Schema.org HomeAndConstructionBusiness](https://schema.org/HomeAndConstructionBusiness)
- [ICO storage/access exceptions](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/what-are-the-exceptions/) — optional browser measurement uses explicit opt-in here; no blanket exemption is assumed.
