#!/bin/bash
# Transcribe a video file to word-level timestamps using Hyperframes' built-in Whisper.
# No API key needed — runs locally on CPU/GPU.
#
# Usage: bash transcribe.sh <video.mp4> [output.json]

set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo "Usage: bash transcribe.sh <video.mp4> [output.json]"
  exit 1
fi

VIDEO="$1"
OUT="${2:-transcript.json}"

if ! command -v npx >/dev/null; then
  echo "ERROR: npx not found. Install Node.js (≥20) first."
  exit 1
fi

echo "Transcribing $VIDEO via hyperframes (local Whisper, no API key needed)..."
npx -y hyperframes transcribe "$VIDEO" --model small.en --json -o "$OUT"

echo ""
echo "Done → $OUT"
WORDS=$(python3 -c "import json; print(len(json.load(open('$OUT'))))")
echo "Word count: $WORDS"
