-- LibraryConnect database schema (SQLite)
-- Safe to run more than once: tables are only created if missing.

CREATE TABLE IF NOT EXISTS patrons (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,          -- stored lowercase
    password_hash TEXT NOT NULL,                 -- never the real password
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS books (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patron_id    INTEGER NOT NULL,
    title        TEXT NOT NULL,
    library_name TEXT NOT NULL,
    due_date     TEXT NOT NULL,                  -- YYYY-MM-DD
    returned     INTEGER NOT NULL DEFAULT 0 CHECK (returned IN (0, 1)),
    returned_at  TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (patron_id) REFERENCES patrons (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_books_patron_due ON books (patron_id, due_date);
