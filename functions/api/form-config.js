import {configurationReady, jsonResponse} from '../../lib/enquiry.mjs';

export function onRequestGet({env}) {
  const enabled = configurationReady(env);
  return jsonResponse({enabled, siteKey: enabled ? env.TURNSTILE_SITE_KEY : null}, 200);
}
