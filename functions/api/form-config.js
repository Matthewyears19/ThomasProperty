import {
  configurationReady,
  jsonResponse
} from '../../lib/enquiry.mjs';

export function onRequestGet({env}) {
  const required = [
    'RESEND_API_KEY',
    'ENQUIRY_FROM',
    'TURNSTILE_SITE_KEY',
    'TURNSTILE_SECRET_KEY',
    'ALLOWED_ORIGINS',
    'RATE_LIMIT_SALT'
  ];

  const missing = required.filter(
    name => typeof env[name] !== 'string' || !env[name].trim()
  );

  if (env.ENQUIRIES_ENABLED !== 'true') {
    missing.push('ENQUIRIES_ENABLED must equal true');
  }

  if (!env.ENQUIRY_DB) {
    missing.push('ENQUIRY_DB');
  }

  const enabled = configurationReady(env);

  return jsonResponse({
    enabled,
    siteKey: enabled ? env.TURNSTILE_SITE_KEY : null,
    missing
  }, 200);
}
