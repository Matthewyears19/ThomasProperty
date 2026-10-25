# Final handover and owner to-do list

## Completed in source

- Responsive website, six service pages, mobile navigation and contact controls.
- Locally hosted royalty-free illustrative photographs, with credits/licence records; no fabricated portfolio or reviews.
- General enquiry form on Contact, defaulting to General enquiry. The existing quote route also accepts general questions and service enquiries.
- Accessible description guidance asking for the area/postcode where work is to be completed. General questions do not require a location; the separate postcode field remains optional.
- First-person singular business copy: I, me and my across the site, service content, FAQs and enquiry email text. The business name, factual attributions and future customer quotations remain distinct. The father's experience remains clearly his, rather than the business's trading history.
- Enquiry validation, server-side spam protection, email acknowledgements, duplicate protection, failure/retry handling and optional aggregate analytics code.
- Permission-gated review/gallery systems, editable FAQs, technical SEO, structured data, social metadata, guarded production sitemap and release checks.
- Repeated automated validation: 19 Python tests and 34 JavaScript tests pass, plus navigation, page/asset/metadata/ARIA, static security/performance and HTTP checks. The general-enquiry path is tested without a postcode and verifies the business email receives the message context.

On 25 October 2026 the owner confirmed that live enquiries and email delivery work and were tested. `data/release.json` now records `liveEmailTestsPassed: true` on that basis. A separate read-only check confirmed the public form configuration returns `enabled: true`. No further test email was sent. This supersedes the earlier handover's disabled-form finding. The public robots file still blocks all crawling.

No production deployment, Git push, DNS change, credentials or live configuration changes were made by this work. The latest form and copy changes are local until deployed.

## Final actions for the owner

1. **Review the final wording and forms.** Check Contact and Enquiries/Free Quotations on your phone and desktop. Confirm the first-person voice and the advertised scope for House MOT, ongoing maintenance and Mould Removal. Edit or approve the remaining draft service wording.
2. **Finalise privacy and retention.** Set specific periods or documented criteria for unsuccessful enquiries and accepted-work/customer records, plus deletion/review arrangements. Check the privacy notice against the services actually used. No retention period has been invented or compliance certification claimed. Remove the draft notice only after the actual wording is complete and approved.
3. **Choose whether to use analytics.** It is optional. Leave `ANALYTICS_ENABLED` unset/false to keep it off. To enable it, apply `migrations/0002_analytics.sql` once, review the privacy wording and test opt-in/withdrawal before enabling the runtime setting. There is no separate paid analytics account. `quote_success` is the legacy technical counter name for accepted enquiries, now including general enquiries; it does not mean every message is a quote request or booking. View aggregates privately using `docs/analytics-queries.sql`.
4. **Deploy the reviewed update through your existing Cloudflare workflow.** Keep the existing working email/spam settings and secrets. Frontend and backend must be released together because the backend now accepts General enquiry. After deployment, make one short smoke check of the changed Contact/quote forms, selection defaults, location guidance, first-person emails and mobile controls. This checks the new release rather than repeating account setup.
5. **Approve the production release and enable search indexing.** The current public site still blocks crawling. Record actual privacy/service/preview review and explicit release approval in `data/release.json`; the email test flag is already recorded. Once all real checks/approval are complete, use `TPS_BUILD_MODE=production` for the production build and `preview` for previews. Check that the production robots file allows public pages and links the populated sitemap. Do not merely delete a robots tag from one page: the sitemap and HTTP indexing headers are generated together.
6. **Connect Google Search Console after the indexable release.** Verify the correct HTTPS domain and submit `https://thomaspropertyservices.uk/sitemap.xml`. Review indexing and contact consistency. Google Business Profile verification/updates remain an owner account task where applicable.
7. **Add genuine projects and reviews when available.** Optional for launch: they remain hidden until permissioned content exists. Supply genuine photographs, a short description/service category and approved review text/display names. Keep stock labelled as illustrative. Follow `docs/PHASE-3.md` for content formats.

## Verification and remaining limits

Run `python scripts/verify.py` to rebuild a safe preview and repeat all automated checks. Use `python scripts/serve.py` plus `python scripts/check_http.py` for local HTTP checks. The QA server deliberately disables live form/analytics integrations and sends no email.

`docs/lighthouse-results.json` contains measured local Lighthouse results with audit time/version and conditions. These are static lab audits with inactive Turnstile; they do not certify full WCAG conformance, real-device behaviour or field INP/Core Web Vitals. SEO scores are intentionally reduced while previews are blocked from indexing. Run the final performance/accessibility check on the deployed update with actual integrations active.

The revised Contact/general-enquiry page was inspected in the desktop browser: General enquiry is preselected, location guidance is associated with the description field, and the first-person wording is present. Its new mobile Lighthouse audit scores 100 for performance, accessibility and best practices, with 1.7-second LCP and zero layout shift. SEO remains 69 because the audited preview is deliberately blocked from indexing. The remaining recorded homepage/quote audits are from the preceding Phase 4 performance work and retain their individual timestamps.

The source work is ready for the final review/release steps. A public, indexable, fully approved production release is not claimed until the owner actions above are complete.
