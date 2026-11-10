#!/usr/bin/env bash
# Pinned clones and a tool check. Safe to rerun; clones into vendor/, which
# git ignores.
set -euo pipefail
cd "$(dirname "$0")/.."

for tool in git cmake gcc make python3; do
    command -v "$tool" >/dev/null || echo "setup: MISSING $tool"
done

# The game is built with our own file-driven frontend, which needs no display
# and no curses. X11 is compiled in for one thing only: `takeover`, which
# hands a replayed savefile to a person in a real terminal. A machine without
# the X11 headers - a cloud container, usually - builds everything else and
# replays recorded runs identically, with BORG_RUNNER_NO_X11=1.
x11_header=$(ls /usr/include/X11/Xlib.h 2>/dev/null || true)
if [ -z "$x11_header" ]; then
    if [ "${BORG_RUNNER_INSTALL:-}" = 1 ] && command -v apt-get >/dev/null; then
        echo "setup: installing libx11-dev"
        (sudo apt-get update -qq && sudo apt-get install -y -qq libx11-dev) \
            || echo "setup: could not install libx11-dev"
    fi
fi
if [ -z "$(ls /usr/include/X11/Xlib.h 2>/dev/null || true)" ]; then
    echo "setup: no libx11-dev. Play, replay and the tests work anyway:"
    echo "setup:   export BORG_RUNNER_NO_X11=1"
    echo "setup: only 'takeover' (handing a game to a person) needs X11."
fi

clone() {
    local name=$1 repository=$2 commit=$3
    local directory="vendor/$name"
    if [ ! -d "$directory/.git" ]; then
        git clone -q "https://github.com/$repository" "$directory"
    fi
    git -C "$directory" fetch -q origin "$commit" 2>/dev/null || git -C "$directory" fetch -q origin
    git -C "$directory" checkout -q "$commit"
    echo "setup: $name $(git -C "$directory" rev-parse --short=12 HEAD) ok"
}

mkdir -p vendor
python3 - <<'PY' | while read -r name repository commit; do clone "$name" "$repository" "$commit"; done
import json
for name, entry in json.load(open('pins.json'))['pins'].items():
    print(name, entry['repository'], entry['commit'])
PY
echo "setup: ready"
