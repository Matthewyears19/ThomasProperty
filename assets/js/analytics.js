'use strict';

// Optional first-party aggregate measurement, disabled until configured and opted in.
(async () => {
  const panel = document.querySelector('#analytics-preferences');
  if (!panel) return;
  let enabled = false, optedIn = false, pageCounted = false;
  const key = 'tps-usage-choice-v1';
  const age = 180 * 86400 * 1000;
  const status = document.querySelector('#analytics-choice');
  const privacySignal = navigator.globalPrivacyControl === true || navigator.doNotTrack === '1';
  function send(event) {
    if (!enabled || !optedIn || privacySignal) return;
    // Never transmit search strings, fragments, referrers, service selections or form fields.
    fetch('/api/metrics', {method: 'POST', keepalive: true, headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event, path: location.pathname, consent: true})}).catch(() => {});
  }
  function setChoice(allow, remember = true) {
    optedIn = allow && !privacySignal;
    status.textContent = optedIn ? 'Optional usage statistics are on. You can turn them off here at any time.' : 'Optional usage statistics are off.';
    if (remember) {
      try { localStorage.setItem(key, JSON.stringify({allowed: optedIn, expires: Date.now() + age})); } catch { /* Choice still works for this page. */ }
    }
    if (optedIn && !pageCounted) { pageCounted = true; send('page_view'); }
  }
  try {
    const response = await fetch('/api/analytics-config', {cache: 'no-store', signal: AbortSignal.timeout(5000)});
    const config = await response.json();
    if (!response.ok || config.enabled !== true) return;
    enabled = true;
    panel.hidden = false;
    document.querySelector('#analytics-allow').disabled = privacySignal;
    document.querySelector('#analytics-allow').addEventListener('click', () => setChoice(true));
    document.querySelector('#analytics-decline').addEventListener('click', () => setChoice(false));
    let choice;
    try { choice = JSON.parse(localStorage.getItem(key)); } catch { /* Default remains off. */ }
    setChoice(choice?.allowed === true && typeof choice.expires === 'number' && choice.expires > Date.now(), false);
    if (privacySignal) status.textContent = 'Optional usage statistics are off because your browser requests privacy protection.';
    document.addEventListener('tps:call-intent', () => send('call_intent'));
  } catch { /* Analytics must never block navigation or enquiries. */ }
})();
