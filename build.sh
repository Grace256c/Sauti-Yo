#!/usr/bin/env bash
set -euo pipefail

# Resolve paths from the repository root.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "===== INSTALL PYTHON DEPENDENCIES ====="
python -m pip install -r "$BACKEND_DIR/requirements.txt"

echo "===== INSTALL FRONTEND DEPENDENCIES ====="
cd "$FRONTEND_DIR"
npm ci

echo "===== BUILD REACT FRONTEND ====="
npm run build

echo "===== PREPARE DJANGO FRONTEND DIRECTORIES ====="
mkdir -p "$BACKEND_DIR/templates"
mkdir -p "$BACKEND_DIR/static/frontend"

# Remove assets from previous builds so old hashed files do not accumulate.
rm -rf "$BACKEND_DIR/static/frontend"
mkdir -p "$BACKEND_DIR/static/frontend"

echo "===== COPY REACT BUILD OUTPUT ====="
cp "$FRONTEND_DIR/dist/index.html" "$BACKEND_DIR/templates/index.html"

# Vite's assets and public files are served under /static/frontend/.
cp -a "$FRONTEND_DIR/dist/." "$BACKEND_DIR/static/frontend/"

# The HTML entry point is served by Django's template view, not as a static file.
rm -f "$BACKEND_DIR/static/frontend/index.html"

echo "===== COLLECT DJANGO STATIC FILES ====="
cd "$BACKEND_DIR"
python manage.py collectstatic --noinput

echo "===== BUILD COMPLETED ====="
