#!/bin/bash
# Setup script for the Cloud Routine environment.
# Result is cached after first run (per the Anthropic env caching).
set -euo pipefail

echo "[setup] installing Python deps"
pip install --quiet --upgrade Pillow requests

echo "[setup] verifying ffmpeg"
if ! command -v ffmpeg &> /dev/null; then
  echo "[setup] installing ffmpeg"
  apt-get update -qq && apt-get install -y -qq ffmpeg fontconfig
fi
ffmpeg -version | head -1

echo "[setup] verifying Impact font (needed for thumbnail generation)"
# Cloud env likely doesn't have it. We embed a copy or download once.
if [ ! -f /usr/share/fonts/truetype/impact.ttf ]; then
  echo "[setup] Impact.ttf not found — downloading from public mirror"
  mkdir -p /usr/share/fonts/truetype
  # Use a CDN-hosted Impact font (must be in allowed domains)
  curl -sL -o /usr/share/fonts/truetype/impact.ttf \
    "https://raw.githubusercontent.com/follox42/voidline-remotion-preview/main/public/fonts/impact.ttf" \
    || echo "[setup] could not fetch impact.ttf — thumbnail gen will fall back"
  fc-cache -fv > /dev/null 2>&1 || true
fi

echo "[setup] ensuring stats_log.csv exists"
mkdir -p shorts
[ -f shorts/stats_log.csv ] || echo "ts,asset,yt_id,kind,views,likes" > shorts/stats_log.csv

echo "[setup] done"
