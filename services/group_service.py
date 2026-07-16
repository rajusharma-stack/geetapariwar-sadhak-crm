"""
Group / Level management service.

Each group has a name and role-holders (BC, GC, CT, TA)
stored as free-text names (optionally linked to user IDs).
"""

from dataclasses import dataclass
from typing import Optional
from database import get_connection
from services.backup_service import backup_to_drive


@dataclass
class GroupWithNames:
    id: int
    name: str
    level: str
    batch: str
    bc_name: str
    gc_name: str
    ct_name: str
    ta_name: str
    timing: str
    zoom_link: str


def get_all_groups() -> list[tuple[int, str, str, str]]:
    """Return list of (id, name, level, batch) for dropdowns."""
    conn = get_connection()
    rows = conn.execute("SELECT id, name, COALESCE(level, 'Level 1') AS level, COALESCE(batch, 'Regular') AS batch FROM groups ORDER BY name").fetchall()
    conn.close()
    return rows


def get_group_with_names(group_id: int) -> Optional[GroupWithNames]:
    """Return a group with role-holder names."""
    conn = get_connection()
    row = conn.execute("""
        SELECT g.id, g.name,
               COALESCE(g.level, 'Level 1') AS level,
               COALESCE(g.batch, 'Regular') AS batch,
               COALESCE(NULLIF(g.bc_name, ''), COALESCE(bc.full_name, '')) AS bc_name,
               COALESCE(NULLIF(g.gc_name, ''), COALESCE(gc.full_name, '')) AS gc_name,
               COALESCE(NULLIF(g.ct_name, ''), COALESCE(ct.full_name, '')) AS ct_name,
               COALESCE(NULLIF(g.ta_name, ''), COALESCE(ta.full_name, '')) AS ta_name,
               COALESCE(g.timing, '') AS timing,
               COALESCE(g.zoom_link, '') AS zoom_link
        FROM groups g
        LEFT JOIN users bc ON bc.id = g.bc_id
        LEFT JOIN users gc ON gc.id = g.gc_id
        LEFT JOIN users ct ON ct.id = g.ct_id
        LEFT JOIN users ta ON ta.id = g.ta_id
        WHERE g.id = ?
    """, (group_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return GroupWithNames(*row)


def save_group(group_id: Optional[int], name: str,
               bc_name: str, gc_name: str,
               ct_name: str, ta_name: str,
               timing: str = "", zoom_link: str = "",
               level: str = "Level 1", batch: str = "Regular") -> None:
    """Insert or update a group with role-holder names, timing, level, and batch.

    If a name matches an existing active user, the corresponding
    user ID is also stored for permission checks.
    """
    conn = get_connection()
    users = {r[0]: r[1] for r in conn.execute(
        "SELECT id, full_name FROM users WHERE active=1"
    ).fetchall()}
    name_to_id = {v: k for k, v in users.items()}

    bc_id = name_to_id.get(bc_name)
    gc_id = name_to_id.get(gc_name)
    ct_id = name_to_id.get(ct_name)
    ta_id = name_to_id.get(ta_name)

    if group_id:
        conn.execute(
            "UPDATE groups SET name=?, bc_id=?, gc_id=?, ct_id=?, ta_id=?, "
            "bc_name=?, gc_name=?, ct_name=?, ta_name=?, timing=?, zoom_link=?, "
            "level=?, batch=? WHERE id=?",
            (name, bc_id, gc_id, ct_id, ta_id,
             bc_name or None, gc_name or None, ct_name or None, ta_name or None,
             timing or None, zoom_link or None, level, batch, group_id),
        )
    else:
        conn.execute(
            "INSERT INTO groups (name, bc_id, gc_id, ct_id, ta_id, "
            "bc_name, gc_name, ct_name, ta_name, timing, zoom_link, "
            "level, batch) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, bc_id, gc_id, ct_id, ta_id,
             bc_name or None, gc_name or None, ct_name or None, ta_name or None,
             timing or None, zoom_link or None, level, batch),
        )
    conn.commit()
    conn.close()
    backup_to_drive()


def delete_group(group_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM groups WHERE id=?", (group_id,))
    conn.commit()
    conn.close()
    backup_to_drive()


def get_history(sadhak_id: int) -> list[tuple]:
    """Return history rows for a sadhak, newest first."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT h.id, COALESCE(h.group_name, '—') AS group_name,
               COALESCE(g.level, 'Level 1') AS level,
               COALESCE(g.batch, 'Regular') AS batch,
               COALESCE(h.bc_name, '—'), COALESCE(h.gc_name, '—'),
               COALESCE(h.ct_name, '—'), COALESCE(h.ta_name, '—'),
               COALESCE(u.full_name, '—') AS changed_by_name, h.changed_at
        FROM sadhak_history h
        LEFT JOIN groups g ON g.id = h.group_id
        LEFT JOIN users u ON u.id = h.changed_by
        WHERE h.sadhak_id = ?
        ORDER BY h.changed_at DESC
    """, (sadhak_id,)).fetchall()
    conn.close()
    return rows


def can_edit_sadhak(user_id: int, sadhak_id: int) -> bool:
    """Check if a user is allowed to edit a specific sadhak record.

    Admin can edit everything. Other users can only edit sadhaks in
    groups where they are assigned as BC, GC, CT, or TA.
    """
    conn = get_connection()
    # First check if user is Admin
    role = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if role and role[0] == "Admin":
        conn.close()
        return True
    # Check if user is a role-holder for the sadhak's group
    row = conn.execute("""
        SELECT 1 FROM sadhak s
        JOIN groups g ON g.id = s.group_id
        WHERE s.id = ? AND (g.bc_id = ? OR g.gc_id = ? OR g.ct_id = ? OR g.ta_id = ?)
    """, (sadhak_id, user_id, user_id, user_id, user_id)).fetchone()
    conn.close()
    return row is not None
