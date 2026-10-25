import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {handleEnquiry, buildEmails, configurationReady} from '../lib/enquiry.mjs';
import {validateEnquiry} from '../lib/validation.mjs';
import {onRequestGet} from '../functions/api/form-config.js';

function database() {
  const sqlite = new DatabaseSync(':memory:');
  sqlite.exec(readFileSync(new URL('../migrations/0001_enquiries.sql', import.meta.url), 'utf8'));
  return {sqlite, prepare(sql) {
    return {bind(...args) {
      return {async first() { return sqlite.prepare(sql).get(...args) || null; }, async run() {
        const result = sqlite.prepare(sql).run(...args);
        return {meta: {changes: Number(result.changes)}};
      }};
    }};
  }, async batch(statements) { return Promise.all(statements.map(s => s.run())); }};
}
const fixture = () => ({name: 'Test Enquirer', email: 'test@example.com', phone: '', service: 'Painting and Decorating', description: 'Test only: refresh a room.', postcode: '', timeframe: '', details: '', website: '', requestId: crypto.randomUUID(), turnstileToken: 'test-token'});
const environment = () => ({ENQUIRIES_ENABLED: 'true', ENQUIRY_DB: database(), RESEND_API_KEY: 'test-only', ENQUIRY_FROM: 'Thomas Property Services <quotes@example.com>', TURNSTILE_SITE_KEY: 'test-site-key', TURNSTILE_SECRET_KEY: 'test-secret', ALLOWED_ORIGINS: 'https://example.com', RATE_LIMIT_SALT: 'test-salt-not-a-production-secret'});
function request(data = fixture(), {method = 'POST', origin = 'https://example.com', headers = {}} = {}) {
  return new Request('https://example.com/api/enquiry', {method, headers: {Origin: origin, 'Content-Type': 'application/json', 'CF-Connecting-IP': '192.0.2.1', ...headers}, ...(method !== 'GET' ? {body: JSON.stringify(data)} : {})});
}
function provider({reject = false, malformed = false, hostname = 'example.com', action = 'enquiry', spam = true, networkError = false} = {}) {
  const calls = [];
  return {calls, async fetch(url, options) {
    calls.push({url, options});
    if (url.includes('siteverify')) return Response.json({success: spam, hostname, action});
    if (networkError) throw new Error('test-network-failure');
    const sent = JSON.parse(options.body);
    return Response.json(reject ? {message: 'test rejection'} : {data: malformed ? [] : sent.map((_, index) => ({id: `test-${index}`}))}, {status: reject ? 500 : 200});
  }};
}
async function run(env, data, mock, opts = {}, now) {
  const response = await handleEnquiry({env, request: request(data, opts)}, {fetch: mock.fetch, ...(now ? {now: () => now} : {})});
  return {status: response.status, body: await response.json(), response};
}

test('validation accepts phone-only and email-only enquiries', () => {
  assert.equal(validateEnquiry(fixture()).valid, true);
  const phone = {...fixture(), email: '', phone: '07410 928465'};
  assert.equal(validateEnquiry(phone).valid, true);
  assert.equal(validateEnquiry({...fixture(), service: 'Mould Removal'}).valid, true);
});
test('validation rejects missing contact, invalid contacts, services, controls and excessive lengths', () => {
  for (const change of [{name: ''}, {email: '', phone: ''}, {email: 'invalid'}, {phone: '123'}, {service: 'Roofing'}, {description: ''}, {name: 'x'.repeat(101)}, {details: 'x'.repeat(3001)}, {email: 'a@example.com\nBcc: x@example.com'}, {description: '\u0000'}]) {
    assert.equal(validateEnquiry({...fixture(), ...change}).valid, false, JSON.stringify(change));
  }
  assert.equal(validateEnquiry({...fixture(), name: []}).valid, false);
});
test('configuration fails closed and public config never exposes secrets', async () => {
  const env = environment();
  assert.equal(configurationReady(env), true);
  for (const key of ['ENQUIRY_DB', 'RESEND_API_KEY', 'ENQUIRY_FROM', 'TURNSTILE_SITE_KEY', 'TURNSTILE_SECRET_KEY', 'ALLOWED_ORIGINS', 'RATE_LIMIT_SALT']) {
    assert.equal(configurationReady({...env, [key]: ''}), false, key);
  }
  const publicConfig = await onRequestGet({env}).json();
  assert.deepEqual(publicConfig, {enabled: true, siteKey: 'test-site-key'});
  const result = await run({...env, ENQUIRIES_ENABLED: 'false'}, fixture(), provider());
  assert.equal(result.status, 503);
  assert.equal(result.body.ok, false);
});
test('POST JSON and exact allowed same-origin are required', async () => {
  for (const [opts, expected] of [[{method: 'GET'}, 405], [{origin: 'https://evil.example'}, 403], [{origin: ''}, 403], [{headers: {'Content-Type': 'text/plain'}}, 415]]) {
    const mock = provider();
    const result = await run(environment(), fixture(), mock, opts);
    assert.equal(result.status, expected);
    assert.equal(mock.calls.length, 0);
  }
});
test('malformed and oversized bodies do not send mail', async () => {
  for (const body of ['{bad', 'x'.repeat(24001), '[]', 'null']) {
    const mock = provider();
    const response = await handleEnquiry({env: environment(), request: new Request('https://example.com/api/enquiry', {method: 'POST', headers: {Origin: 'https://example.com', 'Content-Type': 'application/json'}, body})}, {fetch: mock.fetch});
    assert.equal(response.status, 400);
    assert.equal(mock.calls.length, 0);
  }
});
test('honeypot, invalid ID and field errors do not send mail', async () => {
  for (const change of [{website: 'spam'}, {requestId: 'bad'}, {email: 'bad'}, {turnstileToken: ''}]) {
    const mock = provider();
    const result = await run(environment(), {...fixture(), ...change}, mock);
    assert.equal(result.status, 400);
    assert.equal(mock.calls.length, 0);
  }
});
test('Turnstile success, hostname and action are verified server-side', async () => {
  for (const change of [{spam: false}, {hostname: 'other.example'}, {action: 'other'}]) {
    const mock = provider(change);
    const result = await run(environment(), fixture(), mock);
    assert.equal(result.status, 400);
    assert.equal(mock.calls.length, 1);
  }
});
test('email enquiry is accepted only after provider accepts both emails', async () => {
  const env = environment(), mock = provider(), data = fixture();
  const result = await run(env, data, mock);
  assert.equal(result.status, 200);
  assert.equal(result.body.ok, true);
  assert.equal(result.body.acknowledgement, true);
  const send = mock.calls.find(c => c.url.includes('resend'));
  const emails = JSON.parse(send.options.body);
  assert.equal(emails.length, 2);
  assert.deepEqual(emails[0].to, ['thomaspropertyservicesuk@gmail.com']);
  assert.deepEqual(emails[1].to, ['test@example.com']);
  assert.equal(emails[0].reply_to, data.email);
  assert.equal(send.options.headers['Idempotency-Key'], `enquiry/${data.requestId}`);
  const stored = env.ENQUIRY_DB.sqlite.prepare('SELECT * FROM enquiry_requests').all();
  assert.equal(stored[0].state, 'accepted');
  assert.equal(JSON.stringify(stored).includes('Test Enquirer'), false);
  assert.equal(JSON.stringify(stored).includes('test@example.com'), false);
});
test('phone-only enquiry sends no acknowledgement email', async () => {
  const mock = provider();
  const result = await run(environment(), {...fixture(), email: '', phone: '07410 928465'}, mock);
  assert.equal(result.body.acknowledgement, false);
  assert.equal(JSON.parse(mock.calls[1].options.body).length, 1);
});
test('general questions are accepted without a property postcode and retain message context in email', async () => {
  const mock = provider();
  const result = await run(environment(), {...fixture(), service: 'General enquiry', description: 'Could you tell me more about the services you offer?', postcode: ''}, mock);
  assert.equal(result.status, 200);
  assert.equal(result.body.ok, true);
  const email = JSON.parse(mock.calls[1].options.body)[0];
  assert.match(email.subject, /General enquiry/);
  assert.match(email.text, /Enquiry or work details:/);
  assert.match(email.text, /Could you tell me more/);
});
test('successful retries return success without another provider or Turnstile call', async () => {
  const env = environment(), data = fixture(), mock = provider();
  await run(env, data, mock);
  const retry = await run(env, {...data, turnstileToken: ''}, mock);
  assert.equal(retry.body.ok, true);
  assert.equal(mock.calls.length, 2);
});
test('changed payload cannot reuse an earlier request ID', async () => {
  const env = environment(), data = fixture(), mock = provider();
  await run(env, data, mock);
  const result = await run(env, {...data, description: 'Changed work'}, mock);
  assert.equal(result.status, 409);
  assert.equal(result.body.code, 'changed');
  assert.equal(mock.calls.length, 2);
});
test('rate limiter is atomic in SQLite and blocks sixth attempt', async () => {
  const env = environment(), mock = provider({spam: false});
  for (let n = 0; n < 5; n++) assert.equal((await run(env, fixture(), mock)).status, 400);
  const result = await run(env, fixture(), mock);
  assert.equal(result.status, 429);
  assert.equal(result.response.headers.get('Retry-After'), '600');
  assert.equal(mock.calls.length, 5);
  assert.equal(JSON.stringify(env.ENQUIRY_DB.sqlite.prepare('SELECT * FROM enquiry_limits').all()).includes('192.0.2.1'), false);
});
test('provider rejection, malformed response and network failure never report success', async () => {
  for (const change of [{reject: true}, {malformed: true}, {networkError: true}]) {
    const env = environment(), mock = provider(change);
    const result = await run(env, fixture(), mock);
    assert.equal(result.status, 503);
    assert.equal(result.body.ok, false);
    assert.equal(env.ENQUIRY_DB.sqlite.prepare('SELECT state FROM enquiry_requests').get().state, 'retryable');
  }
});
test('recoverable failures retry with identical provider key and body', async () => {
  const env = environment(), data = fixture(), failed = provider({reject: true}), recovery = provider();
  await run(env, data, failed);
  const result = await run(env, {...data, turnstileToken: 'fresh-token'}, recovery);
  assert.equal(result.body.ok, true);
  assert.equal(failed.calls[1].options.headers['Idempotency-Key'], recovery.calls[1].options.headers['Idempotency-Key']);
  assert.equal(failed.calls[1].options.body, recovery.calls[1].options.body);
});
test('concurrent duplicate submissions result in one provider request', async () => {
  const env = environment(), data = fixture(), mock = provider();
  const results = await Promise.all([run(env, data, mock), run(env, data, mock)]);
  assert.equal(results.filter(r => r.body.ok).length >= 1, true);
  assert.equal(mock.calls.filter(c => c.url.includes('resend')).length, 1);
});
test('expired uncertain attempts are not resent outside provider idempotency window', async () => {
  const env = environment(), data = fixture(), failed = provider({reject: true});
  const start = Date.now();
  await run(env, data, failed, {}, start);
  const recovery = provider();
  const result = await run(env, data, recovery, {}, start + 23 * 3600 * 1000);
  assert.equal(result.status, 409);
  assert.equal(result.body.code, 'expired');
  assert.equal(recovery.calls.length, 0);
});
test('a recent pending lease blocks retries and a stale one can be recovered', async () => {
  const env = environment(), data = fixture(), failed = provider({reject: true});
  const start = Date.now();
  await run(env, data, failed, {}, start);
  env.ENQUIRY_DB.sqlite.prepare("UPDATE enquiry_requests SET state = 'pending'").run();
  const mock = provider();
  const pending = await run(env, data, mock, {}, start + 30000);
  assert.equal(pending.body.code, 'pending');
  assert.equal(mock.calls.length, 0);
  const recovered = await run(env, data, mock, {}, start + 61000);
  assert.equal(recovered.body.ok, true);
  assert.equal(mock.calls.filter(c => c.url.includes('resend')).length, 1);
});
test('database outage prevents sending and never produces false success', async () => {
  const env = environment(); env.ENQUIRY_DB.batch = async () => {throw new Error('test-db-down');};
  const mock = provider();
  const result = await run(env, fixture(), mock);
  assert.equal(result.status, 503);
  assert.equal(mock.calls.length, 0);
});
test('email templates use plain text, fixed recipients and acknowledgement without reflected enquiry content', () => {
  const data = validateEnquiry({...fixture(), description: '<script>alert(1)</script>'}).data;
  const emails = buildEmails(data, 'quotes@example.com');
  assert.equal('html' in emails[0], false);
  assert.equal(emails[1].text.includes(data.description), false);
  assert.equal(emails[1].text.includes('confirm a booking'), true);
});
