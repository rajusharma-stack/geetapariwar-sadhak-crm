#!/bin/sh
# Railway injects $PORT — bind gunicorn to it, fallback to 3201
# Single worker — SQLite cannot safely handle concurrent writers
PORT="${PORT:-3201}"
gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --timeout 120 wsgi:application
