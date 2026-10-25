-- No names, contact details, enquiry text or raw IP addresses are stored here.
CREATE TABLE IF NOT EXISTS enquiry_requests (
  id TEXT PRIMARY KEY,
  payload_hash TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('pending', 'retryable', 'accepted')),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS enquiry_created ON enquiry_requests(created_at);
CREATE TABLE IF NOT EXISTS enquiry_limits (
  bucket TEXT PRIMARY KEY,
  attempts INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
