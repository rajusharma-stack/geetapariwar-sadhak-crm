"""
Authentication service.

Handles password hashing (SHA-256), user lookup, and automatic seeding
of the default admin account when no users exist.
"""

import hashlib
from dataclasses import dataclass
from typing import Optional
from database import get_connection


@dataclass
class User:
    id: int
    full_name: str
    username: str
    role: str
    active: int


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed_admin() -> None:
    """Create the default admin account if no users exist."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO users (full_name, username, password_hash, role, active) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Administrator", "admin", _hash_password("admin123"), "Admin", 1),
        )
        conn.commit()
    conn.close()


def authenticate(username: str, password: str) -> Optional[User]:
    """Return the User if credentials are valid, otherwise None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, full_name, username, role, active FROM users "
        "WHERE username = ? AND password_hash = ? AND active = 1",
        (username.strip(), _hash_password(password)),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return User(id=row[0], full_name=row[1], username=row[2], role=row[3], active=row[4])
