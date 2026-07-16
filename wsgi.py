import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if "PYTHONANYWHERE_DOMAIN" in os.environ:
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("GEETAPARIWAR_DATA_DIR", str(data_dir))

from app import app as application
