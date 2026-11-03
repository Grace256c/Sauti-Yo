#!/usr/bin/env bash
set -euo pipefail

# Start Django using Render's assigned port.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR/backend"

PORT="${PORT:-10000}"

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
