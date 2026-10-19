CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message TEXT NOT NULL CHECK(length(trim(message)) BETWEEN 1 AND 2000),
  app_version TEXT NOT NULL CHECK(length(trim(app_version)) BETWEEN 1 AND 40),
  status TEXT NOT NULL DEFAULT 'Ontvangen',
  reactie TEXT,
  admin_note TEXT,
  resolved_in_version TEXT,
  resolved_at TEXT,
  status_changed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  rate_bucket TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS comments_created_at ON comments(created_at DESC);
CREATE TABLE IF NOT EXISTS site_visits (
  session_hash TEXT PRIMARY KEY,
  visitor_hash TEXT NOT NULL,
  visited_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS site_visits_visited_at ON site_visits(visited_at DESC);
