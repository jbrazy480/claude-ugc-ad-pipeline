#!/bin/bash
# Composite raw video + caption frames + motion-graphic overlays → final.mp4
#
# Reads cue points + speed from config.json. All MG types are overlaid in order.
# Captions are the LAST layer so they're never hidden by overlays (they're
# already gated by suppression windows in make_captions.py).
#
# Usage:  bash compose.sh [project-dir]   # defaults to current dir

set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
cd "$PROJECT_DIR"

if [[ ! -f config.json ]]; then
  echo "ERROR: config.json not found in $PROJECT_DIR"
  exit 1
fi

# ────────────────── read config via jq (or python fallback) ──────────────────
read_cfg() {
  python3 -c "import json,sys; d=json.load(open('config.json')); print(d$1)"
}

RAW_VIDEO=$(read_cfg "['raw_video']")
OUTPUT=$(read_cfg "['output']")
SPEED=$(read_cfg ".get('speed',1.0)")
TAIL=$(read_cfg ".get('tail_seconds',4.0)")
N_MG=$(read_cfg ".get('motion_graphics',[])" | python3 -c "import sys,ast; print(len(ast.literal_eval(sys.stdin.read())))")

# Detect raw duration
RAW_DUR=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$RAW_VIDEO")

# Compute output durations
SPED_DUR=$(echo "scale=3; $RAW_DUR / $SPEED" | bc)
TOTAL_DUR=$(echo "scale=3; $SPED_DUR + $TAIL" | bc)
FADE_OUT=$(echo "scale=3; $TOTAL_DUR - 0.5" | bc)

echo "── Composing at ${SPEED}× ──"
echo "  raw: ${RAW_VIDEO} (${RAW_DUR}s)"
echo "  output: ${OUTPUT} (${TOTAL_DUR}s)"
echo "  motion graphics: ${N_MG}"

# ────────────────── build ffmpeg input + filter args dynamically ──────────────────
INPUTS=( -i "$RAW_VIDEO" -framerate 30 -i "build/overlays/captions/%04d.png" )

# MG inputs in order
for ((i=0; i<N_MG; i++)); do
  MG_ID=$(read_cfg "['motion_graphics'][$i]['id']")
  INPUTS+=( -framerate 30 -i "build/overlays/${MG_ID}/%04d.png" )
done

# Build filter_complex
# [0]=raw, [1]=captions, [2..N+1]=MG slots
FILTER="[0:v]setpts=PTS/${SPEED},tpad=stop_mode=clone:stop_duration=${TAIL}[base];"
FILTER+="[0:a]atempo=${SPEED},apad=pad_dur=${TAIL},afade=t=out:st=${FADE_OUT}:d=0.5[a];"

PREV="base"
for ((i=0; i<N_MG; i++)); do
  IDX=$((i + 2))   # ffmpeg input index for this MG
  MG_T=$(read_cfg "['motion_graphics'][$i]['start_t']")
  MG_DUR=$(read_cfg "['motion_graphics'][$i]['duration']")

  # Cue in OUTPUT time = original / SPEED
  CUE=$(echo "scale=3; $MG_T / $SPEED" | bc)
  CUE_END=$(echo "scale=3; $CUE + $MG_DUR" | bc)

  FILTER+="[${IDX}:v]setpts=PTS-STARTPTS+${CUE}/TB[mg${i}];"
  FILTER+="[${PREV}][mg${i}]overlay=enable='between(t\\,${CUE}\\,${CUE_END})':x=0:y=0:eof_action=pass[v${i}];"
  PREV="v${i}"
done

# Final caption layer on top (already has built-in suppression windows)
FILTER+="[${PREV}][1:v]overlay=x=0:y=0:eof_action=pass:shortest=0[vfinal]"

# ────────────────── render ──────────────────
ffmpeg -y "${INPUTS[@]}" \
  -filter_complex "$FILTER" \
  -map "[vfinal]" -map "[a]" \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  -t "$TOTAL_DUR" \
  "$OUTPUT"

echo ""
echo "Done → $(pwd)/$OUTPUT"
ls -lah "$OUTPUT"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT"
