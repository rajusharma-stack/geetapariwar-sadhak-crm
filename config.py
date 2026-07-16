"""
Application configuration.

Centralises paths, constants, and settings used across the project.
"""

import os
import sys
from pathlib import Path


def _get_base_dir() -> Path:
    """Return the writable data directory for the application."""
    if getattr(sys, "frozen", False):
        # PyInstaller: store data in %APPDATA% so it persists and is writable
        return Path(sys.executable).resolve().parent
    # Development / script mode
    return Path(__file__).resolve().parent


def _get_data_dir() -> Path:
    """Return the writable data directory.

    Override via GEETAPARIWAR_DATA_DIR env var (useful on PythonAnywhere).
    When installed (PyInstaller frozen), use %APPDATA% so the
    database is writable even when installed in Program Files.
    During development, use the project's data/ folder.
    """
    env_dir = os.environ.get("GEETAPARIWAR_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    if getattr(sys, "frozen", False):
        return Path.home() / "AppData" / "Local" / "GeetaPariwarSadhak"
    return Path(__file__).resolve().parent / "data"


def _detect_google_drive() -> Path | None:
    """Detect the user's local Google Drive folder."""
    home = Path.home()
    candidates = [
        home / "Google Drive",
        home / "My Drive",
        home / "Google Drive" / "My Drive",
        Path(os.environ.get("GOOGLE_DRIVE_PATH", "")),
    ]
    for p in candidates:
        if p and p.is_dir():
            return p
    return None


# Base directories
BASE_DIR = _get_base_dir()
DATA_DIR = _get_data_dir()
ASSETS_DIR = BASE_DIR / "assets"
BACKUPS_DIR = DATA_DIR / "backups"
EXPORTS_DIR = DATA_DIR / "exports"

# Database
DATABASE_PATH = DATA_DIR / "crm.db"

# Google Drive auto-backup (None if Google Drive not found)
GOOGLE_DRIVE_PATH = _detect_google_drive()
GOOGLE_DRIVE_BACKUP_PATH = (
    GOOGLE_DRIVE_PATH / "GeetaPariwarSadhak_Backup" / "crm.db"
    if GOOGLE_DRIVE_PATH
    else None
)

# Application metadata
APP_TITLE = "Geeta Pariwar Nepal Sadhak CRM"
APP_VERSION = "1.0.0"
