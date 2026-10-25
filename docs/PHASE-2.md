# Phase 2 — enquiry implementation and activation checklist

## Current status

Source implementation and local automated tests are complete. Phase 2 is **not yet accepted as operational**: Cloudflare bindings, Turnstile, a verified sending domain, provider credentials and real email tests remain necessary. Nothing has been pushed, deployed or changed in the existing Cloudflare account by this work.

Validation on 25 October 2026: all twelve generated pages pass structural checks; navigation tests and 25 server/frontend tests pass. The updated homepage colours were inspected in a desktop browser, and the real static preview displayed the unavailable-service notice with disabled inputs, retry button and telephone/email alternatives. Real Turnstile challenges, inbox delivery, a Cloudflare Functions deployment and mobile visual QA have not been exercised.

The supplied logo's sampled navy (`#012A58`) and gold (`#E0BD87`) now drive the website. The logo JPEG itself is unchanged. House MOT and ongoing maintenance copy is proposed content, visibly marked as a draft for business review, in `data/services.json` under `draftScope`.

## Your checklist

- Review the proposed House MOT and ongoing maintenance descriptions, especially the written summary, accessible areas, exclusions, scheduling and separately quoted follow-up work.
- Confirm your Cloudflare Pages project is connected to this repository. Set build command `python scripts/build.py`, output directory `dist`, and repository root as the project root. The `functions/` directory must remain at repository root, not inside `dist`. If you used dashboard drag-and-drop upload, that does not include Pages Functions: deploy the existing Direct Upload project using authorised Wrangler commands, or create a new Git-integrated project. A Direct Upload project cannot be switched to Git integration in place. Do not switch to GitHub Pages for this backend.
- Create a Resend account, add a sending domain/subdomain you control, and complete Resend's required DNS authentication. Use a verified sender such as `Thomas Property Services <quotes@YOUR-VERIFIED-DOMAIN>`; this is a placeholder, not a configured address. Customer enquiries still go to `thomaspropertyservicesuk@gmail.com`. A Gmail address cannot be used as your authenticated sending domain.
- Create a restricted Resend sending API key. Store it as the Cloudflare secret `RESEND_API_KEY`. Do not put it in this chat, Git or frontend files.
- Create a Cloudflare Turnstile widget. Add the exact Pages hostname and any later approved website hostname. Save its public site key as `TURNSTILE_SITE_KEY` and its secret as encrypted `TURNSTILE_SECRET_KEY`.
- Create a Cloudflare D1 database. In its console run the SQL from `migrations/0001_enquiries.sql`. Add a Pages D1 binding named **`ENQUIRY_DB`**, pointing to that database. It is a resource binding, not a string variable.
- Set `ENQUIRY_FROM` to your verified sender. Set `ALLOWED_ORIGINS` to the exact permitted origin(s), for example `https://YOUR-PROJECT.pages.dev`, with no path or trailing slash; separate multiple origins with commas. Do not allow every `pages.dev` site or wildcard origins. Add a random encrypted `RATE_LIMIT_SALT` secret of at least 32 random bytes.
- Choose and record retention periods/criteria for unsuccessful enquiries and accepted-work records, and confirm processor terms, relevant transfers and provider retention. Update `templates/privacy-content.html` accordingly. The business name/contact information is treated as confirmed; no compliance certification is claimed.
- Use separate preview/test secrets, widget hostnames and D1 database where practical. Leave `ENQUIRIES_ENABLED=false` until configuration and privacy information are ready; then set it to `true` for the intended test environment and redeploy through your chosen workflow.
- Test email-only, telephone-only and both-contact enquiries. Confirm the business notification reaches the Gmail inbox, customer acknowledgements arrive only when email was supplied, reply-to works and spam-folder behaviour is understood. Check actual delivery in the Resend dashboard; API acceptance is not proof of final inbox delivery.
- Test failed/expired spam checks, invalid fields, double-clicks, retries, provider failures and mobile keyboard use. Confirm errors retain typed content, success is never shown on failure, and retries do not create duplicate messages. Only then treat Phase 2 as complete and enable the intended environment.

Cloudflare variable/binding changes need a redeploy. Git-connected Pages projects may deploy automatically when you push; review before pushing to the production branch. This guide does not authorise production publication or live-domain changes.

## Configuration reference

| Setting | Type | Purpose |
| --- | --- | --- |
| `ENQUIRIES_ENABLED` | Variable | Literal `true` enables the form only when all other settings exist. |
| `RESEND_API_KEY` | Encrypted secret | Server-only sending credential. |
| `ENQUIRY_FROM` | Variable | Sender address authenticated with Resend. |
| `TURNSTILE_SITE_KEY` | Variable | Public widget key, returned by `/api/form-config`. |
| `TURNSTILE_SECRET_KEY` | Encrypted secret | Server-side token verification. |
| `ALLOWED_ORIGINS` | Variable | Exact comma-separated approved origins. |
| `RATE_LIMIT_SALT` | Encrypted secret | Salts IP/request fingerprints; keep stable across normal retries. |
| `ENQUIRY_DB` | D1 binding | Atomic attempt counters and duplicate-prevention metadata. |

Changing the sender or salt while an enquiry is retrying can invalidate its stored fingerprint; ask the customer to telephone rather than forcing a duplicate. No personal enquiry content is stored in D1, but pseudonymous metadata still deserves appropriate retention and access controls.

## Local checks

Python 3.10+ builds the site. Node 22.13+ (Node 24 recommended) runs the tests using the bundled `node:sqlite`, with no npm packages required.

```powershell
python scripts/build.py
python scripts/check.py
node scripts/check-navigation.cjs
node --test tests/*.test.mjs
```

The tests execute real SQLite statements against an in-memory adapter for D1 and use simulated Turnstile/email responses. They cover validation, same-origin policy, configuration failures, body limits, spam errors, rate limits, concurrent duplicates, retry windows, plain-text email templates and frontend loading/error/success state. They send no email and do not establish real Cloudflare/provider compatibility or deliverability.

For a static visual preview, `python -m http.server 8000 --directory dist --bind 127.0.0.1` works; online submission correctly stays unavailable because that server cannot run Functions.

For a full local Cloudflare runtime, install/use the official Wrangler CLI and copy `wrangler.example.jsonc` to ignored `wrangler.local.jsonc`. The all-zero database ID is explicitly a local placeholder. Create ignored `.dev.vars` from `.env.example` and populate local/test settings, including `ALLOWED_ORIGINS=http://localhost:8788`. Use an actual test widget configured for localhost; the handler requires a matching Turnstile hostname and action. Never use a real sending key for automated tests.

```powershell
npx wrangler d1 execute local-enquiries --local --config wrangler.local.jsonc --file migrations/0001_enquiries.sql
npx wrangler pages dev dist --config wrangler.local.jsonc
```

These commands operate locally by default; no deploy or remote migration command is included. A Cloudflare preview with real bindings remains the decisive integration test.

## Behaviour and operational limits

- Browser and server share validation; full name, known service, description and email-or-phone are required. Fields are bounded, error summaries are keyboard reachable and optional details stay optional.
- Spam protection is verified server-side, including action and exact hostname. A honeypot adds a secondary check. The application allows five submission attempts per connecting IP per ten-minute fixed window; this is a baseline, not comprehensive DDoS protection.
- Requests use an in-memory browser UUID plus atomic D1 state and Resend idempotency keys. A pending request has a 60-second lease. An uncertain attempt may retry with identical content for less than 23 hours, within Resend's documented 24-hour key window. Changed uncertain enquiries and older attempts require telephone follow-up rather than automatic resending. Reloading the page loses the in-memory draft/key; do not reload an uncertain submission before retrying.
- Business notification and optional acknowledgement are sent as one batch. Success requires a valid provider response for every requested email and recorded accepted state. The API confirms provider acceptance, not ultimate inbox placement. Provider failures are logged only as a generic event, without personal details or token dumps.
- Only anti-abuse metadata enters D1. Attempts become eligible for removal within 20 minutes and request records after seven days; cleanup runs on subsequent endpoint calls. If fixed physical deletion deadlines are required, configure scheduled cleanup separately and account for provider backups/logs.
- No enquiry details enter browser persistent storage, repository files or analytics. Typed details stay in the current page after a recoverable error. Local `tps:quote-success` and `tps:call-intent` events prepare for a later approved analytics adapter; no analytics provider is active.
- Cloudflare `_headers` permits only the required Turnstile script/frame/connect origins in addition to this site. API responses set their own no-store headers because static `_headers` rules do not apply to Functions responses. Development indexing blocks and labelled missing imagery remain until a later approved launch review.

## References

- [Cloudflare Pages bindings and secrets](https://developers.cloudflare.com/pages/functions/bindings/)
- [Cloudflare Turnstile server validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/)
- [Resend batch email API](https://resend.com/docs/api-reference/emails/send-batch-emails)
- [Resend idempotency window](https://resend.com/docs/dashboard/emails/idempotency-keys)
- [ICO retention guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/)
