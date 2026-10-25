-- Aggregate totals only: no visitor IDs, enquiry content or raw IP addresses.
CREATE TABLE IF NOT EXISTS analytics_daily (
  day TEXT NOT NULL,
  path TEXT NOT NULL,
  event TEXT NOT NULL CHECK(event IN ('page_view', 'call_intent', 'quote_success')),
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(day, path, event)
);
ALTER TABLE enquiry_requests ADD COLUMN analytics_counted INTEGER NOT NULL DEFAULT 0;
