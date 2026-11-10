#!/usr/bin/env python3
"""Route between two named points on a map screen, as movement digits.

Written by the player of `minimaxflash-3` while playing (seed 313).

`tools/screen/map.py` can only route from the '@' on the screen.  But in the
town the '@' is wherever you happen to be standing, and a shop screen hides
the map entirely, so a route from one shop door to another has to be
computed from the last map screen, with the start given by hand.

    python3 runs/minimaxflash-3/tools/route.py <screen.txt> <start x,y> <goal x,y>
    python3 runs/minimaxflash-3/tools/route.py <screen.txt> --shop 5      # to a shop

It reuses the shared library's screen reader and the shared BFS, so the
digits it prints are the same ones `map.py --shops` prints.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools' / 'screen'))

from map import route as _route  # noqa: E402
from screen import STORES, load  # noqa: E402

# The shared map.py treats ':' (a pile of rubble) as walkable.  It is not:
# terrain.txt:257 gives RUBBLE the flags ROCK|NO_SCENT|NO_FLOW|INTERESTING|TORCH
# and no PASSABLE, so a route that crosses rubble stops on the first such tile
# with "There is a wall in the way!" (measured, ask 14).
WALKABLE = set('.') | set("'")


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip())
        return 1
    s = load(argv[0])
    if s.overlay:
        print(f'! {s.overlay}: the map is covered; nothing to route on.')
        return 1
    panel = s.panel
    start = tuple(int(v) for v in argv[1].split(','))
    if argv[2].startswith('--shop'):
        glyph = argv[2][6:].strip()
        if not glyph and len(argv) > 3:
            glyph = argv[3].strip()
        doors = s.find(glyph)
        if not doors:
            print(f'no store {glyph} on this screen')
            return 1
        goal = doors[0]
    else:
        goal = tuple(int(v) for v in argv[2].split(','))
    keys = _route(panel, start, goal, walkable=WALKABLE)
    print(f'from {start} to {goal}: {keys or "no route over drawn floor"}')
    if keys:
        print(f'({len(keys)} steps)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
