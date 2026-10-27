CREATE TABLE IF NOT EXISTS captures (
  id      TEXT PRIMARY KEY,
  inbox   TEXT NOT NULL,      -- SHA-256 of the user's capture key
  body    TEXT NOT NULL,
  source  TEXT NOT NULL DEFAULT 'siri',
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS captures_inbox ON captures (inbox, created);
