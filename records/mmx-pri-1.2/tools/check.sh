#!/usr/bin/env bash
# Read the newest screen of a run: status, position, and every glyph it draws.
# Usage: bash runs/mmx-pri-1.2/tools/check.sh [ask-number]
set -euo pipefail
cd "$(dirname "$0")/../../.."
N="${1:-}"
if [ -z "$N" ]; then
  N=$(ls runs/mmx-pri-1.2/ask/screen-*.txt | sed 's/.*screen-//;s/.txt//' | sort -n | tail -1)
fi
echo "### screen-$N"
python3 tools/screen/screen.py "runs/mmx-pri-1.2/ask/screen-$N.txt"
echo "### glyphs"
python3 tools/screen/look.py "runs/mmx-pri-1.2/ask/screen-$N.txt"
