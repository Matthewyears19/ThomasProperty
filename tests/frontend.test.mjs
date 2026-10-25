import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {validateEnquiry} from '../lib/validation.mjs';

function frontend({enabled = true, reply = {ok: true, acknowledgement: true, message: 'Accepted'}, reject = false} = {}) {
  const nodes = new Map(), events = [], requests = [], fieldsByName = {};
  class Element {
    constructor(id) { this.id = id; this.hidden = false; this.disabled = false; this.value = ''; this.textContent = ''; this.attrs = {}; this.listeners = {}; this.children = []; }
    addEventListener(name, fn) { this.listeners[name] = fn; }
    setAttribute(name, value) { this.attrs[name] = value; }
    getAttribute(name) { return this.attrs[name] || null; }
    removeAttribute(name) { delete this.attrs[name]; }
    append(...items) { this.children.push(...items); }
    replaceChildren() { this.children = []; }
    focus() { document.activeElement = this; }
    closest() { return null; }
    querySelectorAll(selector) { return selector === '.field-error' ? [...nodes.values()].filter(n => n.id.endsWith('-error')) : []; }
    reset() { for (const field of Object.values(fieldsByName)) field.value = ''; }
  }
  const initial = {name: 'Test Enquirer', email: 'test@example.com', phone: '', service: 'Painting and Decorating', description: 'Test enquiry', postcode: '', timeframe: '', details: '', website: ''};
  for (const [name, value] of Object.entries(initial)) {
    const field = new Element(name); field.value = value; fieldsByName[name] = field; nodes.set(name, field); nodes.set(`${name}-error`, new Element(`${name}-error`));
  }
  const form = new Element('quote-form');
  form.elements = {...fieldsByName, namedItem(name) { return fieldsByName[name]; }};
  nodes.set('quote-form', form);
  const document = {
    querySelector(selector) {
      const id = selector.replace('#', '');
      if (!nodes.has(id)) nodes.set(id, new Element(id));
      return nodes.get(id);
    },
    getElementById(id) { return nodes.get(id); },
    createElement(tag) { return new Element(tag); },
    dispatchEvent(event) { events.push(event); }
  };
  const turnstile = {render(_container, config) { this.config = config; return 'widget'; }, reset() {}, remove() {}};
  const window = {turnstile};
  let release;
  const blocked = new Promise(resolve => {release = resolve;});
  let hold = false;
  async function fetch(url, options) {
    if (url === '/api/form-config') return Response.json({enabled, siteKey: enabled ? 'test-key' : null});
    requests.push(JSON.parse(options.body));
    if (hold) await blocked;
    if (reject) throw new Error('test-network');
    return Response.json(reply, {status: reply.ok ? 200 : 503});
  }
  const source = readFileSync(new URL('../assets/js/enquiry.js', import.meta.url), 'utf8').replace(/^import .*?;\s*/, '');
  vm.runInNewContext(source, {document, window, fetch, validateEnquiry, AbortSignal, crypto,
    FormData: class {constructor() {return Object.entries(fieldsByName).map(([name, field]) => [name, field.value]);}},
    CustomEvent: class {constructor(type, options) {this.type = type; this.detail = options.detail;}}
  });
  return {nodes, form, events, requests, turnstile, document, async settle() { await new Promise(resolve => setImmediate(resolve)); },
    solve() {turnstile.config.callback('test-token');}, hold() {hold = true;}, release,
    submit() {return form.listeners.submit({preventDefault() {}});}};
}

test('frontend fails closed while unavailable and does not load/execute spam challenge', async () => {
  const page = frontend({enabled: false}); await page.settle();
  assert.equal(page.nodes.get('quote-fields').disabled, true);
  assert.match(page.nodes.get('form-status').textContent, /unavailable/);
  assert.equal(page.turnstile.config, undefined);
  assert.equal(page.requests.length, 0);
});
test('frontend validates, links errors and focuses error summary without sending', async () => {
  const page = frontend(); await page.settle(); page.solve();
  page.nodes.get('name').value = '';
  await page.submit();
  assert.equal(page.requests.length, 0);
  assert.equal(page.nodes.get('name').attrs['aria-invalid'], 'true');
  assert.equal(page.document.activeElement.id, 'form-errors');
  assert.equal(page.nodes.get('form-errors').hidden, false);
});
test('frontend locks duplicate clicks, shows success only after response and emits no personal event data', async () => {
  const page = frontend(); await page.settle(); page.solve(); page.hold();
  const first = page.submit();
  await page.submit();
  assert.equal(page.requests.length, 1);
  assert.equal(page.nodes.get('quote-fields').disabled, true);
  assert.equal(page.form.hidden, false);
  page.release(); await first;
  assert.equal(page.form.hidden, true);
  assert.equal(page.nodes.get('quote-success').hidden, false);
  assert.equal(page.document.activeElement.id, 'quote-success');
  assert.equal(page.events[0].type, 'tps:quote-success');
  assert.equal(JSON.stringify(page.events).includes('example.com'), false);
});
test('frontend preserves fields and reuses request key after recoverable failure', async () => {
  const page = frontend({reply: {ok: false, message: 'Please retry'}}); await page.settle(); page.solve();
  await page.submit();
  assert.equal(page.form.hidden, false);
  assert.equal(page.nodes.get('description').value, 'Test enquiry');
  assert.equal(page.nodes.get('quote-fields').disabled, false);
  assert.equal(page.events.length, 0);
  page.solve(); await page.submit();
  assert.equal(page.requests[0].requestId, page.requests[1].requestId);
});
test('frontend protects uncertain network failures from changed duplicate enquiries', async () => {
  const page = frontend({reject: true}); await page.settle(); page.solve();
  await page.submit();
  page.nodes.get('description').value = 'Changed work'; page.solve();
  await page.submit();
  assert.equal(page.requests.length, 1);
  assert.match(page.nodes.get('form-status').textContent, /original details/);
});
test('phone-only success does not promise an email acknowledgement', async () => {
  const page = frontend({reply: {ok: true, acknowledgement: false, message: 'Accepted'}}); await page.settle();
  page.nodes.get('email').value = ''; page.nodes.get('phone').value = '07410 928465'; page.solve();
  await page.submit();
  assert.match(page.nodes.get('acknowledgement-status').textContent, /No email acknowledgement/);
});
