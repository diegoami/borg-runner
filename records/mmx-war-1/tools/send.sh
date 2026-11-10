#!/bin/sh
# Send one key string to the pending question of the run.
#
# Written by the player of mmx-war-1 (seed 271, Half-Elf Warrior).
# The ask number is worked out from the latest screen file, so the run never
# sends a key to a question that does not exist.
#
# Usage:  sh runs/mmx-war-1/tools/send.sh '<keys>' ["reason"]
set -e
cd /home/diego/projects/borg-runner/../mmx-war-1 2>/dev/null || cd "$(dirname "$0")/../../.."
S=$(ls -1 runs/mmx-war-1/ask/screen-*.txt | sort -V | tail -1)
N=$(basename "$S" .txt | sed 's/screen-//')
KEYS="$1"
# A -more- or the M map swallows the first key of the next string.
case "$KEYS" in
  " "*) ;;
  *)
    if grep -q -- "-more-" "$S" || grep -q "Hit any key to continue" "$S"; then
      KEYS=" $KEYS"
    fi
    ;;
esac
echo "ask $N  keys='$KEYS'"
.venv/bin/python -m borg_runner answer "$N" "$KEYS" --run runs/mmx-war-1 \
  --reason "${2:-sent by the run's own send.sh}"
