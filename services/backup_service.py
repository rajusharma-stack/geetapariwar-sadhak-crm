"""
Auto-backup to Google Drive.

Copies the SQLite database to the user's Google Drive folder
after every write operation so data is synced to the cloud.
"""

import shutil
import threading
from pathlib import Path
from config import DATABASE_PATH, GOOGLE_DRIVE_BACKUP_PATH


def backup_to_drive() -> None:
    """Copy the database to Google Drive in a background thread."""
    if GOOGLE_DRIVE_BACKUP_PATH is None:
        return
    threading.Thread(target=_do_copy, daemon=True).start()


def _do_copy() -> None:
    try:
        GOOGLE_DRIVE_BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(DATABASE_PATH), str(GOOGLE_DRIVE_BACKUP_PATH))
    except Exception:
        pass
