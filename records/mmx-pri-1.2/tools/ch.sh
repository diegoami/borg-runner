#!/usr/bin/env bash
# Compact state + what changed since the previous screen.
# Usage: bash runs/mmx-pri-1.2/tools/ch.sh [ask]
set -euo pipefail
cd "$(dirname "$0")/../../.."
RUN=runs/mmx-pri-1.2
N="${1:-}"
if [ -z "$N" ]; then
  N=$(ls $RUN/ask/screen-*.txt | sed 's/.*screen-//;s/.txt//' | sort -n | tail -1)
fi
P=$((N-1))
python3 tools/screen/screen.py "$RUN/ask/screen-$N.txt" | head -4
echo "--- changed since $P"
python3 tools/screen/diff.py "$RUN/ask/screen-$P.txt" "$RUN/ask/screen-$N.txt" 2>&1 | head -30
