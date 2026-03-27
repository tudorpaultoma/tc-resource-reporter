#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Cleaning previous build..."
rm -rf package tc-resource-reporter.zip
mkdir package

echo "==> Installing dependencies..."
pip3 install -t package -r requirements.txt --no-cache-dir

echo "==> Cleaning up..."
find package -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find package -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find package -type f -name "*.pyc" -delete 2>/dev/null || true
rm -rf package/bin 2>/dev/null || true

echo "==> Building zip..."
cd package && zip -r9 ../tc-resource-reporter.zip . -x ".DS_Store" && cd ..
zip -r9 tc-resource-reporter.zip index.py template.py publisher.py services/ policies/ \
  -x "services/__pycache__/*" "*/.DS_Store"

echo "==> Done!"
ls -lh tc-resource-reporter.zip
