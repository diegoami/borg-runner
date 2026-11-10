#!/usr/bin/env bash
# Send one answer and print only the screen - the notebook echo is skipped.
# Usage: bash runs/mmx-pri-1.2/tools/play.sh <ask> <keys> <reason> [note]
set -euo pipefail
cd "$(dirname "$0")/../../.."
RUN=runs/mmx-pri-1.2
NOTE="${4:-}"
if [ -n "$NOTE" ]; then
  OUT=$(.venv/bin/python -m borg_runner answer "$1" "$2" --run "$RUN" --reason "$3" --note "$NOTE" 2>&1)
else
  OUT=$(.venv/bin/python -m borg_runner answer "$1" "$2" --run "$RUN" --reason "$3" 2>&1)
fi
printf '%s\n' "$OUT" | awk '
  /^=== ASK / {p=1}
  p && /^=== YOUR NOTEBOOK/ {p=0}
  p {print}
  /^=== answer:/ {print}
'
