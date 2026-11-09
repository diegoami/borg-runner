#!/usr/bin/env bash
# Pinned clones and a tool check. Safe to rerun; clones into vendor/, which
# git ignores.
set -euo pipefail
cd "$(dirname "$0")/.."

for tool in git cmake gcc python3; do
    command -v "$tool" >/dev/null || echo "setup: MISSING $tool"
done

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
