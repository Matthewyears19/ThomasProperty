# Phase 1 handover

## Implemented

Twelve static documents with a responsive homepage, shared sticky header and footer, five individual service pages, service index, contact and quotation layouts, confirmed-answer FAQs, a clearly marked privacy draft and a custom 404. The provisional navy, warm gold, white and soft white palette uses CSS custom properties. System serif/sans typography avoids external font requests.

Navigation is a disclosure pattern, not an ARIA application menu: native links and buttons use normal Tab order. Menu opening focuses the first link; Escape closes the service disclosure first, then the mobile menu, returning focus to its trigger. Outside click/focus closes disclosures. Breakpoint changes reset expanded state. No modal focus trap is used because the menu remains part of the document flow. Navigation links remain accessible without JavaScript.

Mobile contact controls respect safe-area insets and reserve page space. They hide while a form field has focus, so they do not cover keyboard/input content. Quote links preselect known services, including separate one-off House MOT and ongoing maintenance options. The input layout has no form submission mechanism, no browser storage and no network integration.

## Assumptions

- Existing `logo.jpg` is the supplied business logo. Its file remains unchanged.
- Provisional colours are retained as requested; final matching awaits approval.
- Only Cheshire and surrounding areas are advertised; no base town, radius or address is invented.
- Materials and timings depend on the quotation. No guarantee, qualification, price or specialist service is added.
- The father's experience is clearly distinguished from the recently established business.
- Approved photography is unavailable. Labelled placeholders replace it for development.
- The supplied Facebook URL is used as a normal link; no embedded tracking is loaded.
- Gallery and reviews are omitted until approved content exists, as permitted by the specification. Reserved content files are empty.
- The current output is a local development build and is deliberately non-indexable.

## Validation

See the repeatable commands in README. Automated checks cover generated routes, unique metadata, one H1 per page, all local links/assets, field labels, ARIA references, image dimensions, contact links and development safeguards. A Node harness exercises desktop/mobile disclosure transitions, Escape focus handling, outside dismissal and breakpoint resets. It supplements rather than replaces a real mobile browser check.

Validation performed on 25 October 2026: all twelve generated documents passed the structural/link/metadata checks and returned HTTP 200 locally. JavaScript syntax and the desktop/mobile navigation harness passed. The rendered desktop homepage was visually inspected; the services disclosure opened and closed, and the quotation page correctly preselected One-off House MOT from its URL. The disabled submission control and development notice were verified in the browser accessibility tree.

Real-device mobile/tablet visual QA, browser/screen-reader coverage, colour contrast audit and Lighthouse/Core Web Vitals measurements remain outstanding for later testing. WCAG conformance and the performance targets are not asserted from source checks. Phase 1 implementation is complete for development review; production acceptance criteria, including real email delivery, remain later-phase work.

## Before Phase 2

1. Review the Phase 1 layout, wording and brand direction on desktop, tablet and mobile; approve photography and final colours when available.
2. Confirm legal business identity, privacy contact, retention approach and actual processor arrangements.
3. Confirm form UX and the service enquiry options, especially House MOT scope and recurring maintenance terms.
4. Select/configure the email provider, authenticated sending domain, spam protection and a non-production test environment. Store credentials only in server-side secrets.
5. Implement a secure endpoint with client/server validation, email-or-phone requirement, length checks, rate limiting, Turnstile verification, duplicate protection and error handling that preserves entered data.
6. Implement actual business email delivery, acknowledgements only when email is supplied, and confirmed-server-success feedback. Test delivery, retry and failure paths before enabling submission.

Subsequent phases: permissioned testimonials, genuine project gallery and approved imagery (Phase 3); structured data, production SEO/sitemap and privacy-conscious analytics (Phase 4); measured accessibility/performance, cross-device/email verification and approved launch (Phase 5). No domain, DNS, production or provider account configuration has been performed.
