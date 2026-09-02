"""
Database connection plumbing.

This file knows how to open a connection and how to create the
schema. It does NOT know about conversations or messages as concepts
— that CRUD logic lives in models.py. Keeping the split means you can
read this file to understand "how do we talk to SQLite" and
models.py to understand "what data do we store", without one
tangled into the other.
"""

import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id         TEXT PRIMARY KEY,
    visitor_id    TEXT NOT NULL,
    title      TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('user', 'ai')),
    content         TEXT NOT NULL,
    attachment      TEXT,
    attachment_path TEXT,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        ON DELETE CASCADE
);
"""


@contextmanager
def get_db():
    """Yield a connection with row access by column name, foreign
    keys enforced, and auto-commit on clean exit."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(SCHEMA)