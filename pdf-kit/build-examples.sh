#!/usr/bin/env bash
# Rebuild the template and both example documents, then render review images.
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py template.html
python3 build.py examples/redis-ticketing/redis-recap.html --footer "Redis for the ticket-booking round · SD-47 companion"
python3 build.py examples/url-shortener/url-shortener.html --footer "URL shortener · reference system design interview"
python3 check.py examples/url-shortener/url-shortener.pdf
python3 build.py examples/notification-platform/notification-platform.html --footer "Notification platform · reference system design interview"
