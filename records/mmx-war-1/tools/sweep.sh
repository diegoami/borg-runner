#!/bin/sh
# One sweep: plan a beam-search digit chain over the latest screen and send it.
#
# Written by the player of mmx-war-1 (seed 271, Half-Elf Warrior).
#
# It does three things the manual warns about doing by hand:
#   - it works out the ask number from the latest screen file, so the run
#     never sends a key to a question that does not exist;
#   - it starts the key string with a space when the previous screen ended in
#     a -more- or was the M map, because both swallow the first key;
#   - it sends the chain as ONE ask, because a digit string runs through
#     every turn until it meets a wall.
#
# Usage:  sh runs/mmx-war-1/tools/sweep.sh ["reason text"] [max-steps]
set -e
cd /home/diego/projects/borg-runner/../mmx-war-1 2>/dev/null || cd "$(dirname "$0")/../../.."
ALL=$(ls -1 runs/mmx-war-1/ask/screen-*.txt | sort -V)
S=$(echo "$ALL" | tail -1)
N=$(basename "$S" .txt | sed 's/screen-//')
# The M map screen has no map panel to plan on, but pressing M does not change
# the game state, so the chain planned on the screen before it is still good.
if grep -q "Hit any key to continue" "$S"; then
  S=$(echo "$ALL" | grep -v "$(basename "$S")" | tail -1)
fi
MAX=${2:-40}
KEYS=$(python3 runs/mmx-war-1/tools/beam.py "$S" "$MAX" | sed -n 's/^keys: //p')
case "$KEYS" in
  "") echo "no chain for $S"; exit 1;;
esac
# A -more- or the M map swallows the first key of the next string.
LEAD=""
if grep -q -- "-more-" "$S" || grep -q "Hit any key to continue" "$S"; then
  LEAD=" "
fi
echo "ask $N  lead='$LEAD'  keys=$KEYS"
.venv/bin/python -m borg_runner answer "$N" "$LEAD$KEYS" --run runs/mmx-war-1 \
  --reason "${1:-beam chain into the dark: the chain maximises the unknown squares it turns into remembered ones}"
