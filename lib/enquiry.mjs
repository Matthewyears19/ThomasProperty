import business from '../data/business.json' with {type: 'json'};
import {validateEnquiry} from './validation.mjs';
import {recordAcceptedEnquiry} from './analytics.mjs';

const DAY = 86400;
const REQUIRED = ['RESEND_API_KEY', 'ENQUIRY_FROM', 'TURNSTILE_SITE_KEY', 'TURNSTILE_SECRET_KEY', 'ALLOWED_ORIGINS', 'RATE_LIMIT_SALT'];
export function configurationReady(env) {
  return env.ENQUIRIES_ENABLED === 'true' && Boolean(env.ENQUIRY_DB) && REQUIRED.every(key => typeof env[key] === 'string' && env[key].trim());
}
export function jsonResponse(body, status = 200, headers = {}) {
  return Response.json(body, {status, headers: {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', ...headers}});
}
const fail = (message, status = 503, extra = {}) => jsonResponse({ok: false, message, ...extra}, status);
const success = email => jsonResponse({ok: true, acknowledgement: email, message: 'Thank you for your enquiry. Your message has been received. I aim to respond within 48 hours.'});
async function hash(text) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))), b => b.toString(16).padStart(2, '0')).join('');
}
export function buildEmails(data, from) {
  const text = [
    'New website enquiry — Thomas Property Services', '',
    `Name: ${data.name}`, `Email: ${data.email || 'Not supplied'}`, `Telephone: ${data.phone || 'Not supplied'}`,
    `Service: ${data.service}`, `Postcode: ${data.postcode || 'Not supplied'}`, `Timeframe: ${data.timeframe || 'Not supplied'}`,
    '', 'Enquiry or work details:', data.description, '', 'Additional details:', data.details || 'Not supplied'
  ].join('\n');
  // Plain text avoids HTML interpolation; user input never controls sender/recipient/subject.
  const emails = [{from, to: [business.email], subject: `Website enquiry: ${data.service}`, text}];
  if (data.email) emails[0].reply_to = data.email;
  if (data.email) emails.push({from, to: [data.email], reply_to: business.email,
    subject: 'Your enquiry — Thomas Property Services',
    text: `Thank you for your enquiry.\n\nWe have received your message and aim to respond within 48 hours.\n\nFor a more urgent enquiry, telephone ${business.phone}.\n\nThomas Property Services\n${business.email}\n${business.area}\n\nThis acknowledgement does not confirm a booking or acceptance of the work.`});
  return emails;
}

export async function limitedBody(request, maxBytes = 24000) {
  const reader = request.body?.getReader();
  if (!reader) throw new Error('empty-body');
  const chunks = [];
  let total = 0;
  for (;;) {
    const {done, value} = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maxBytes) { await reader.cancel(); throw new Error('body-limit'); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder().decode(bytes));
}

export async function handleEnquiry({request, env}, dependencies = {}) {
  const send = dependencies.fetch || fetch;
  const now = Math.floor((dependencies.now ? dependencies.now() : Date.now()) / 1000);
  if (request.method !== 'POST') return fail('Use the quotation form to send an enquiry.', 405, {code: 'method'});
  if (!configurationReady(env)) return fail('Online enquiries are unavailable. Please call 07410 928465 or email me.', 503);
  const origin = request.headers.get('Origin');
  const allowed = env.ALLOWED_ORIGINS.split(',').map(value => value.trim()).filter(Boolean);
  if (!origin || origin !== new URL(request.url).origin || !allowed.includes(origin)) return fail('This website is not enabled for online enquiries.', 403);
  if (!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json')) return fail('Send the enquiry using the website form.', 415);
  let input;
  try { input = await limitedBody(request); }
  catch { return fail('The enquiry could not be read or is too large. Please shorten it and try again.', 400); }
  if (!input || Array.isArray(input) || typeof input !== 'object') return fail('Invalid enquiry.', 400);
  const checked = validateEnquiry(input);
  if (!checked.valid) return fail('Please check the highlighted fields.', 400, {errors: checked.errors});
  if (input.website) return fail('The spam check could not be completed. Please call or email me.', 400);
  if (typeof input.requestId !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(input.requestId)) return fail('Refresh the page before sending your enquiry.', 400);
  const id = input.requestId;
  const data = checked.data;
  // Include exact email content in the fingerprint so changed sender settings cannot
  // silently reuse an old provider idempotency key with a different request body.
  const emails = buildEmails(data, env.ENQUIRY_FROM);
  const payloadHash = await hash(env.RATE_LIMIT_SALT + JSON.stringify({data, emails}));
  const db = env.ENQUIRY_DB;
  let claimed = false;
  try {
    // Opportunistic cleanup; only pseudonymous anti-abuse metadata is stored.
    await db.batch([
      db.prepare('DELETE FROM enquiry_limits WHERE expires_at < ?').bind(now),
      db.prepare('DELETE FROM enquiry_requests WHERE created_at < ?').bind(now - 7 * DAY)
    ]);
    const ip = request.headers.get('CF-Connecting-IP') || 'local';
    const bucket = await hash(`${env.RATE_LIMIT_SALT}|${Math.floor(now / 600)}|${ip}`);
    const rate = await db.prepare('INSERT INTO enquiry_limits (bucket, attempts, expires_at) VALUES (?, 1, ?) ON CONFLICT(bucket) DO UPDATE SET attempts = attempts + 1 RETURNING attempts').bind(bucket, now + 1200).first();
    if (!rate || rate.attempts > 5) return jsonResponse({ok: false, message: 'Too many attempts. Please wait ten minutes or telephone me.'}, 429, {'Retry-After': '600'});
    let existing = await db.prepare('SELECT * FROM enquiry_requests WHERE id = ?').bind(id).first();
    if (existing) {
      if (existing.payload_hash !== payloadHash) return fail('This enquiry was changed after an earlier attempt. Please telephone me to avoid a duplicate.', 409, {code: 'changed'});
      if (existing.state === 'accepted') {
        await recordAcceptedEnquiry(env, id, now);
        return success(Boolean(data.email));
      }
      if (now - existing.created_at >= 23 * 3600) return fail('This earlier attempt needs checking. Please telephone me before sending it again.', 409, {code: 'expired'});
      if (existing.state === 'pending' && now - existing.updated_at < 60) return fail('Your enquiry is still being processed. Wait a minute and retry with the same details.', 409, {code: 'pending'});
    }
    if (typeof input.turnstileToken !== 'string' || !input.turnstileToken || input.turnstileToken.length > 2048) return fail('Please complete the spam check and try again.', 400, {code: 'spam'});
    const verification = await send('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, signal: AbortSignal.timeout(12000),
      body: JSON.stringify({secret: env.TURNSTILE_SECRET_KEY, response: input.turnstileToken, remoteip: ip === 'local' ? undefined : ip})
    });
    const result = await verification.json();
    if (!verification.ok || result.success !== true || result.action !== 'enquiry' || result.hostname !== new URL(origin).hostname) return fail('The spam check expired or could not be verified. Please try again.', 400, {code: 'spam'});
    if (!existing) {
      const inserted = await db.prepare("INSERT OR IGNORE INTO enquiry_requests (id, payload_hash, state, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?)").bind(id, payloadHash, now, now).run();
      claimed = inserted.meta.changes === 1;
    } else {
      const updated = await db.prepare("UPDATE enquiry_requests SET state = 'pending', updated_at = ? WHERE id = ? AND payload_hash = ? AND state != 'accepted' AND (state = 'retryable' OR updated_at <= ?)").bind(now, id, payloadHash, now - 60).run();
      claimed = updated.meta.changes === 1;
    }
    if (!claimed) return fail('Another attempt is being processed. Wait a minute and retry with the same details.', 409, {code: 'pending'});
    const response = await send('https://api.resend.com/emails/batch', {
      method: 'POST', signal: AbortSignal.timeout(15000),
      headers: {Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json', 'Idempotency-Key': `enquiry/${id}`},
      body: JSON.stringify(emails)
    });
    const delivered = await response.json();
    if (!response.ok || !Array.isArray(delivered.data) || delivered.data.length !== emails.length || !delivered.data.every(email => typeof email.id === 'string' && email.id)) throw new Error('provider-rejected');
    await db.prepare("UPDATE enquiry_requests SET state = 'accepted', updated_at = ? WHERE id = ?").bind(now, id).run();
    await recordAcceptedEnquiry(env, id, now);
    return success(Boolean(data.email));
  } catch {
    // Do not log request bodies, addresses, tokens or provider response text.
    console.error('enquiry_processing_failed');
    if (claimed) {
      try { await db.prepare("UPDATE enquiry_requests SET state = 'retryable', updated_at = ? WHERE id = ? AND state = 'pending'").bind(now, id).run(); }
      catch { /* A stale pending lease may be reclaimed safely with the same key. */ }
    }
    return fail('I could not confirm your enquiry. Your details are still on this page. Retry with the same details, or call 07410 928465.');
  }
}
