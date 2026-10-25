-- Run privately in the Cloudflare D1 console. No public reporting endpoint.
-- The figures count events, not unique people, conversations or booked jobs.
SELECT day, event, SUM(count) AS total
FROM analytics_daily
GROUP BY day, event ORDER BY day DESC, event;

SELECT path, event, SUM(count) AS total
FROM analytics_daily
WHERE day >= date('now', '-30 days')
GROUP BY path, event ORDER BY event, total DESC;

-- Optional usage counts include opted-in visitors only. Accepted enquiry
-- counts are operational server totals; do not divide them to claim a precise
-- visitor conversion rate because the populations differ.
