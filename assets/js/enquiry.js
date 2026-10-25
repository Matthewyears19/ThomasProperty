import {validateEnquiry} from '/assets/js/validation.mjs';

const form = document.querySelector('#quote-form');
const fields = document.querySelector('#quote-fields');
const submit = document.querySelector('#quote-submit');
const status = document.querySelector('#form-status');
const summary = document.querySelector('#form-errors');
const retry = document.querySelector('#retry-setup');
const successPanel = document.querySelector('#quote-success');
let token = '', widget = null, pending = false, requestId = null, previousPayload = null;
let uncertain = false, conversionRecorded = false;

function showStatus(message) { status.textContent = message; }
function enableSubmit() { submit.disabled = pending || !token; }
function clearErrors() {
  summary.hidden = true;
  summary.replaceChildren();
  for (const field of form.querySelectorAll('[aria-invalid]')) field.removeAttribute('aria-invalid');
  for (const error of form.querySelectorAll('.field-error')) error.textContent = '';
}
function showErrors(errors) {
  clearErrors();
  const title = document.createElement('p');
  title.textContent = 'Please check the following:';
  const list = document.createElement('ul');
  for (const [name, message] of Object.entries(errors)) {
    const field = form.elements.namedItem(name);
    if (!field) continue;
    field.setAttribute('aria-invalid', 'true');
    const error = document.getElementById(`${name}-error`);
    if (error) {
      error.textContent = message;
      const described = new Set((field.getAttribute('aria-describedby') || '').split(' ').filter(Boolean));
      described.add(error.id);
      field.setAttribute('aria-describedby', [...described].join(' '));
    }
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = `#${name}`;
    link.textContent = message;
    link.addEventListener('click', event => {
      event.preventDefault();
      if (field.closest('details')) field.closest('details').open = true;
      field.focus();
    });
    item.append(link); list.append(item);
  }
  summary.append(title, list); summary.hidden = false; summary.focus();
}
function resetChallenge() {
  token = '';
  if (widget !== null && window.turnstile) window.turnstile.reset(widget);
  enableSubmit();
}
async function setup() {
  retry.hidden = true;
  fields.disabled = true;
  showStatus('Checking online enquiry availability…');
  try {
    const response = await fetch('/api/form-config', {cache: 'no-store', signal: AbortSignal.timeout(10000)});
    const config = await response.json();
    if (!response.ok || !config.enabled || !config.siteKey) throw new Error('unavailable');
    if (!window.turnstile) {
      await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
        script.async = true;
        const timer = window.setTimeout(() => { script.remove(); reject(new Error('timeout')); }, 15000);
        script.onload = () => { window.clearTimeout(timer); resolve(); };
        script.onerror = () => { window.clearTimeout(timer); script.remove(); reject(new Error('script')); };
        document.head.append(script);
      });
    }
    if (widget !== null) window.turnstile.remove(widget);
    widget = window.turnstile.render('#spam-check', {
      sitekey: config.siteKey, action: 'enquiry',
      callback(value) { token = value; enableSubmit(); showStatus('Ready to send. Quotations are free and no-obligation.'); },
      'expired-callback'() { token = ''; enableSubmit(); showStatus('The spam check expired. Please complete it again.'); },
      'error-callback'() { token = ''; enableSubmit(); retry.hidden = false; showStatus('Spam protection could not load. Retry, or call 07410 928465.'); }
    });
    fields.disabled = false;
    showStatus('Complete the spam check before sending your enquiry.');
  } catch {
    showStatus('Online enquiries are unavailable. Please call 07410 928465 or email thomaspropertyservicesuk@gmail.com.');
    retry.hidden = false;
  }
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (pending) return;
  const checked = validateEnquiry(Object.fromEntries(new FormData(form)));
  if (!checked.valid) { showErrors(checked.errors); return; }
  clearErrors();
  const fingerprint = JSON.stringify(checked.data);
  if (previousPayload && previousPayload !== fingerprint && uncertain) {
    showStatus('An earlier attempt could not be confirmed. Retry with the original details or telephone us before sending a changed enquiry.');
    return;
  }
  if (!token) { showStatus('Please complete the spam check.'); return; }
  if (!requestId || previousPayload !== fingerprint) requestId = crypto.randomUUID();
  previousPayload = fingerprint;
  const payload = {...checked.data, website: form.elements.website.value, requestId, turnstileToken: token};
  pending = true; enableSubmit(); fields.disabled = true;
  form.setAttribute('aria-busy', 'true'); submit.textContent = 'Sending…';
  showStatus('Sending your enquiry. Please keep this page open.');
  try {
    const response = await fetch('/api/enquiry', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload), signal: AbortSignal.timeout(35000)});
    const result = await response.json();
    if (!response.ok || result.ok !== true) {
      if (response.status >= 500 || response.status === 409) uncertain = true;
      if (result.errors) showErrors(result.errors);
      showStatus(result.message || 'Your enquiry could not be confirmed. Retry or telephone us.');
      return;
    }
    uncertain = false;
    form.hidden = true; successPanel.hidden = false;
    document.querySelector('#acknowledgement-status').textContent = result.acknowledgement ? 'An acknowledgement email has been requested. Please check your inbox and spam folder.' : 'We will use the telephone number you supplied to contact you. No email acknowledgement was requested.';
    showStatus(result.message);
    successPanel.focus();
    // A local hook for a later approved analytics adapter. No personal data.
    if (!conversionRecorded) {
      document.dispatchEvent(new CustomEvent('tps:quote-success', {detail: {event: 'quote_success'}}));
      conversionRecorded = true;
    }
  } catch {
    uncertain = true;
    showStatus('We could not confirm your enquiry. Your details are preserved on this page. Retry with the same details or call 07410 928465.');
  } finally {
    pending = false; fields.disabled = false;
    form.removeAttribute('aria-busy'); submit.textContent = 'Send enquiry';
    resetChallenge();
  }
});
retry.addEventListener('click', setup);
document.querySelector('#new-enquiry').addEventListener('click', () => {
  form.reset(); clearErrors(); requestId = null; previousPayload = null; uncertain = false; conversionRecorded = false;
  successPanel.hidden = true; form.hidden = false;
  showStatus('Complete the details and spam check to send another enquiry.');
  form.elements.name.focus();
});
setup();
