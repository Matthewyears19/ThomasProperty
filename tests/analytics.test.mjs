import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {onRequest} from '../functions/api/metrics.js';
import {recordAcceptedEnquiry} from '../lib/analytics.mjs';

function environment() {
  const sqlite = new DatabaseSync(':memory:');
  for (const name of ['0001_enquiries.sql', '0002_analytics.sql']) sqlite.exec(readFileSync(new URL('../migrations/' + name, import.meta.url), 'utf8'));
  const db = {sqlite, prepare(sql) {return {bind(...args) {return {async first() {return sqlite.prepare(sql).get(...args);}, async run() {return {meta: {changes: Number(sqlite.prepare(sql).run(...args).changes)}};}};}};},
    async batch(statements) {sqlite.exec('BEGIN'); try {const results = []; for (const statement of statements) results.push(await statement.run()); sqlite.exec('COMMIT'); return results;} catch (error) {sqlite.exec('ROLLBACK'); throw error;}}};
  return {ANALYTICS_ENABLED: 'true', ENQUIRY_DB: db, RATE_LIMIT_SALT: 'synthetic-test-secret-not-production', ALLOWED_ORIGINS: 'https://example.com'};
}
function request(data, origin = 'https://example.com') {
  return new Request('https://example.com/api/metrics', {method: 'POST', headers: {Origin: origin, 'Content-Type': 'application/json', 'CF-Connecting-IP': '192.0.2.2'}, body: JSON.stringify(data)});
}

test('metrics endpoint is disabled by default and requires same-origin consented allowlisted events', async () => {
  const env = environment();
  assert.equal((await onRequest({env: {...env, ANALYTICS_ENABLED: 'false'}, request: request({event: 'page_view', path: '/', consent: true})})).status, 503);
  for (const body of [{event: 'quote_success', path: '/', consent: true}, {event: 'page_view', path: '/?email=private', consent: true}, {event: 'page_view', path: '/', consent: false}, {event: 'page_view', path: '/', consent: true, email: 'test@example.com'}]) {
    assert.equal((await onRequest({env, request: request(body)})).status, 400);
  }
  assert.equal((await onRequest({env, request: request({event: 'page_view', path: '/', consent: true}, 'https://other.example')})).status, 403);
  assert.equal(env.ENQUIRY_DB.sqlite.prepare('SELECT count(*) AS total FROM analytics_daily').get().total, 0);
});
test('accepted usage events produce daily aggregate counters only', async () => {
  const env = environment();
  for (let n = 0; n < 2; n++) assert.equal((await onRequest({env, request: request({event: 'call_intent', path: '/services/mould-removal/', consent: true})})).status, 200);
  const rows = env.ENQUIRY_DB.sqlite.prepare('SELECT * FROM analytics_daily').all();
  assert.equal(rows.length, 1); assert.equal(rows[0].count, 2);
  assert.deepEqual(Object.keys(rows[0]).sort(), ['count', 'day', 'event', 'path']);
});
test('accepted enquiries are counted once and only after accepted state', async () => {
  const env = environment(), db = env.ENQUIRY_DB.sqlite, now = Math.floor(Date.now() / 1000);
  db.prepare("INSERT INTO enquiry_requests VALUES ('test-request', 'test-hash', 'pending', ?, ?, 0)").run(now, now);
  await recordAcceptedEnquiry(env, 'test-request', now);
  assert.equal(db.prepare('SELECT count(*) AS total FROM analytics_daily').get().total, 0);
  db.prepare("UPDATE enquiry_requests SET state = 'accepted'").run();
  await recordAcceptedEnquiry(env, 'test-request', now);
  await recordAcceptedEnquiry(env, 'test-request', now + 86400);
  assert.equal(db.prepare('SELECT count FROM analytics_daily').get().count, 1);
  assert.equal(db.prepare('SELECT day FROM analytics_daily').get().day, new Date(now * 1000).toISOString().slice(0, 10));
});
test('aggregate-count failure does not fail an already accepted enquiry', async () => {
  const env = environment();
  env.ENQUIRY_DB.batch = async () => {throw new Error('test-only');};
  await assert.doesNotReject(recordAcceptedEnquiry(env, 'test-request', Math.floor(Date.now() / 1000)));
});
async function browserAnalytics({privacy = false, choice = null, active = true} = {}) {
  const calls = [], saved = [];
  const elements = Object.fromEntries(['analytics-preferences', 'analytics-allow', 'analytics-decline', 'analytics-choice'].map(id => [id, {hidden: true, listeners: {}, addEventListener(event, fn) {this.listeners[event] = fn;}}]));
  const document = {listeners: {}, querySelector(selector) {return elements[selector.slice(1)];}, addEventListener(name, fn) {this.listeners[name] = fn;}};
  const source = readFileSync(new URL('../assets/js/analytics.js', import.meta.url), 'utf8');
  vm.runInNewContext(source, {document, navigator: {globalPrivacyControl: privacy}, location: {pathname: '/contact/', search: '?private=data'}, AbortSignal, localStorage: {getItem() {return choice;}, setItem(key, value) {saved.push({key, value});}}, async fetch(url, options) {if (url.endsWith('analytics-config')) return Response.json({enabled: active}); calls.push({url, options}); return Response.json({ok: true});}});
  await new Promise(resolve => setImmediate(resolve));
  return {calls, saved, elements, document};
}
test('browser sends nothing until opt-in, omits query strings and stops on withdrawal', async () => {
  const browser = await browserAnalytics();
  assert.equal(browser.calls.length, 0);
  browser.elements['analytics-allow'].listeners.click();
  assert.equal(browser.calls.length, 1);
  assert.equal(browser.calls[0].options.body.includes('private'), false);
  browser.document.listeners['tps:call-intent']();
  assert.equal(browser.calls.length, 2);
  browser.elements['analytics-decline'].listeners.click();
  browser.document.listeners['tps:call-intent']();
  assert.equal(browser.calls.length, 2);
});
test('browser honours privacy signals, expired choices and disabled configuration', async () => {
  const consent = JSON.stringify({allowed: true, expires: Date.now() + 10000});
  const browser = await browserAnalytics({privacy: true, choice: consent});
  assert.equal(browser.calls.length, 0);
  assert.equal(browser.elements['analytics-allow'].disabled, true);
  const expired = await browserAnalytics({choice: JSON.stringify({allowed: true, expires: 0})});
  assert.equal(expired.calls.length, 0);
  const disabled = await browserAnalytics({active: false});
  assert.equal(disabled.elements['analytics-preferences'].hidden, true);
});
