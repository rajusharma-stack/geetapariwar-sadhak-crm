#!/bin/sh
# Railway injects $PORT — bind gunicorn to it, fallback to 3201
PORT="${PORT:-3201}"
gunicorn --bind "0.0.0.0:${PORT}" --workers 2 --timeout 120 wsgi:application
