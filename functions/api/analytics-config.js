import {analyticsEnabled} from '../../lib/analytics.mjs';
import {jsonResponse} from '../../lib/enquiry.mjs';

export function onRequestGet({env}) {
  return jsonResponse({enabled: analyticsEnabled(env)});
}
