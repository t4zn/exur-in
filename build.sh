#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Step 1: Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "==> Step 2: Checking frontend assets in out/..."
if command -v pnpm &> /dev/null; then
  echo "Found pnpm. Building static Next.js frontend..."
  pnpm install
  pnpm build
elif command -v npm &> /dev/null; then
  echo "Found npm. Building static Next.js frontend..."
  npm install
  npm run build
elif [ -d "out" ] && [ -f "out/index.html" ]; then
  echo "Pre-compiled out/ directory exists. Ready to serve!"
else
  echo "WARNING: Neither Node/pnpm found nor pre-compiled out/ directory found."
fi

echo "==> Build complete! Python FastAPI server is ready to launch."
