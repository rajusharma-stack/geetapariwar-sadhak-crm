"""
Database initialisation and connection management.

Creates the SQLite database file inside the data/ directory and provides
a helper to obtain a database connection.
"""

import sqlite3
from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def initialize_database() -> None:
    """Create the database file and all required tables."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL CHECK (role IN ('Admin','BC','GC','CT','TA','Mentor')),
            active        INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL UNIQUE,
            bc_id     INTEGER REFERENCES users(id),
            gc_id     INTEGER REFERENCES users(id),
            ct_id     INTEGER REFERENCES users(id),
            ta_id     INTEGER REFERENCES users(id),
            bc_name   TEXT,
            gc_name   TEXT,
            ct_name   TEXT,
            ta_name   TEXT,
            timing    TEXT,
            zoom_link TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sadhak (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            phone       TEXT    NOT NULL UNIQUE,
            email       TEXT,
            prn         TEXT,
            group_id    INTEGER REFERENCES groups(id),
            bc_name     TEXT,
            gc_name     TEXT,
            ct_name     TEXT,
            ta_name     TEXT,
            created_by  INTEGER REFERENCES users(id),
            updated_by  INTEGER REFERENCES users(id),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sadhak_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sadhak_id   INTEGER NOT NULL REFERENCES sadhak(id) ON DELETE CASCADE,
            group_id    INTEGER REFERENCES groups(id),
            group_name  TEXT,
            bc_name     TEXT,
            gc_name     TEXT,
            ct_name     TEXT,
            ta_name     TEXT,
            changed_by  INTEGER REFERENCES users(id),
            changed_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    _migrate_columns(conn)
    conn.commit()
    conn.close()


def _migrate_columns(conn) -> None:
    """Add columns that may be missing on existing databases."""
    sadhak_cols = {row[1] for row in conn.execute("PRAGMA table_info(sadhak)").fetchall()}
    groups_cols = {row[1] for row in conn.execute("PRAGMA table_info(groups)").fetchall()}
    for col in ("bc_name", "gc_name", "ct_name", "ta_name"):
        if col not in groups_cols:
            try:
                conn.execute(f"ALTER TABLE groups ADD COLUMN {col} TEXT")
            except Exception:
                pass
    if "level" not in groups_cols:
        try:
            conn.execute("ALTER TABLE groups ADD COLUMN level TEXT DEFAULT 'Level 1'")
        except Exception:
            pass
    if "batch" not in groups_cols:
        try:
            conn.execute("ALTER TABLE groups ADD COLUMN batch TEXT DEFAULT 'Regular'")
        except Exception:
            pass
    if "timing" not in groups_cols:
        try:
            conn.execute("ALTER TABLE groups ADD COLUMN timing TEXT")
        except Exception:
            pass
    if "zoom_link" not in groups_cols:
        try:
            conn.execute("ALTER TABLE groups ADD COLUMN zoom_link TEXT")
        except Exception:
            pass
    for col in ("created_by", "updated_by", "group_id", "bc_name", "gc_name", "ct_name", "ta_name"):
        if col not in sadhak_cols:
            try:
                conn.execute(f"ALTER TABLE sadhak ADD COLUMN {col} TEXT")
            except Exception:
                pass

    # Ensure users CHECK constraint includes 'CT' (needed for existing databases)
    schema = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    if schema and "CT" not in schema[0]:
        try:
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("CREATE TABLE users_new ("
                         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                         "full_name TEXT NOT NULL,"
                         "username TEXT NOT NULL UNIQUE,"
                         "password_hash TEXT NOT NULL,"
                         "role TEXT NOT NULL CHECK (role IN ('Admin','BC','GC','CT','TA','Mentor')),"
                         "active INTEGER NOT NULL DEFAULT 1)")
            conn.execute("INSERT INTO users_new SELECT * FROM users")
            conn.execute("DROP TABLE users")
            conn.execute("ALTER TABLE users_new RENAME TO users")
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialised at {DATABASE_PATH}")
