import services from '../data/services.json' with {type: 'json'};
import projects from '../data/projects.json' with {type: 'json'};
import reviews from '../data/reviews.json' with {type: 'json'};

export const publicPaths = new Set(['/', '/services/', '/faqs/', '/contact/', '/request-quote/', '/privacy-policy/', ...services.map(service => `/services/${service.slug}/`)]);
if (reviews.some(review => review.approved === true && review.permissionGranted === true)) publicPaths.add('/reviews/');
const approvedProjects = projects.filter(project => project.approved === true && project.permissionGranted === true);
if (approvedProjects.length) publicPaths.add('/our-work/');
for (const project of approvedProjects) publicPaths.add(`/our-work/${project.slug}/`);

export function analyticsEnabled(env) {
  return env.ANALYTICS_ENABLED === 'true' && Boolean(env.ENQUIRY_DB && env.RATE_LIMIT_SALT && env.ALLOWED_ORIGINS);
}
export function metricStatement(db, day, path, event) {
  return db.prepare('INSERT INTO analytics_daily(day, path, event, count) VALUES (?, ?, ?, 1) ON CONFLICT(day, path, event) DO UPDATE SET count = count + 1').bind(day, path, event);
}

export async function recordAcceptedEnquiry(env, id, now) {
  if (!analyticsEnabled(env)) return;
  const db = env.ENQUIRY_DB;
  try {
    // D1 batches are transactional: count and marker commit together. Failures
    // must never change the outcome of an already accepted customer enquiry.
    await db.batch([
      db.prepare("INSERT INTO analytics_daily(day, path, event, count) SELECT strftime('%Y-%m-%d', updated_at, 'unixepoch'), '/request-quote/', 'quote_success', 1 FROM enquiry_requests WHERE id = ? AND state = 'accepted' AND analytics_counted = 0 ON CONFLICT(day, path, event) DO UPDATE SET count = count + 1").bind(id),
      db.prepare("UPDATE enquiry_requests SET analytics_counted = 1 WHERE id = ? AND state = 'accepted'").bind(id),
      db.prepare('DELETE FROM analytics_daily WHERE day < ?').bind(new Date((now - 180 * 86400) * 1000).toISOString().slice(0, 10))
    ]);
  } catch { console.error('aggregate_quote_metric_failed'); }
}
