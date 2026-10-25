import {analyticsEnabled, metricStatement, publicPaths} from '../../lib/analytics.mjs';
import {jsonResponse, limitedBody} from '../../lib/enquiry.mjs';

export async function onRequest({request, env}) {
  if (request.method !== 'POST') return jsonResponse({ok: false}, 405, {Allow: 'POST'});
  if (!analyticsEnabled(env)) return jsonResponse({ok: false}, 503);
  const origin = request.headers.get('Origin');
  if (!origin || origin !== new URL(request.url).origin || !env.ALLOWED_ORIGINS.split(',').map(value => value.trim()).includes(origin)) return jsonResponse({ok: false}, 403);
  if (!request.headers.get('Content-Type')?.startsWith('application/json')) return jsonResponse({ok: false}, 415);
  let data;
  try { data = await limitedBody(request, 256); } catch { return jsonResponse({ok: false}, 400); }
  if (!data || Object.keys(data).some(key => !['event', 'path', 'consent'].includes(key)) || data.consent !== true || !['page_view', 'call_intent'].includes(data.event) || !publicPaths.has(data.path)) return jsonResponse({ok: false}, 400);
  const now = Math.floor(Date.now() / 1000);
  const day = new Date(now * 1000).toISOString().slice(0, 10);
  const ip = request.headers.get('CF-Connecting-IP') || 'local';
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${env.RATE_LIMIT_SALT}|metrics|${Math.floor(now / 600)}|${ip}`));
  const bucket = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
  const db = env.ENQUIRY_DB;
  try {
    const rate = await db.prepare('INSERT INTO enquiry_limits (bucket, attempts, expires_at) VALUES (?, 1, ?) ON CONFLICT(bucket) DO UPDATE SET attempts = attempts + 1 RETURNING attempts').bind(bucket, now + 1200).first();
    if (!rate || rate.attempts > 120) return jsonResponse({ok: false}, 429);
    await db.batch([
      metricStatement(db, day, data.path, data.event),
      db.prepare('DELETE FROM enquiry_limits WHERE expires_at < ?').bind(now),
      db.prepare('DELETE FROM analytics_daily WHERE day < ?').bind(new Date((now - 180 * 86400) * 1000).toISOString().slice(0, 10))
    ]);
    return jsonResponse({ok: true});
  } catch {
    console.error('aggregate_usage_metric_failed');
    return jsonResponse({ok: false}, 503);
  }
}
