#!/bin/bash
# Build script for FastWorker Management GUI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installing dependencies..."
npm install

echo "Building Vue.js app..."
npm run build

echo "Copying favicon..."
cp public/favicon.svg ../static/ 2>/dev/null || true

echo "Build complete! Static files are in ../static/"
