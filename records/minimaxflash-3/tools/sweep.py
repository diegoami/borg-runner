#!/usr/bin/env python3
"""A sweep of every tile of drawn floor around the player, as key digits.

Written by the player of `minimaxflash-3` while playing (seed 313).

Exploring a level one aim at a time is slow: an aim into ground nobody has
looked at walks until it meets a wall, which is usually one tile away,
because most of a level is wall.  But the floor that HAS been drawn is
walkable and the game will follow a route over it, so one ask can cover
dozens of tiles - and a tile I have never stepped on may hold a gold pile
or a monster.

This walks a depth-first tour of every reachable tile of drawn floor in
the panel and prints it as the game's own movement digits (1=SW 2=S 3=SE
4=W 6=E 7=NW 8=N 9=NE; vendor/angband/src/cave.c:49).  One ask can carry
the whole string.

    python3 runs/minimaxflash-3/tools/sweep.py runs/minimaxflash-3/ask/screen-100.txt

Caveats, measured: a monster standing on a tile turns the step into an
attack and the player does not move, so a tour that runs into one comes
out of step with the map - the screen shows the fight and the next tour
starts from where the player actually is.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools' / 'screen'))

from screen import KEYPAD, load  # noqa: E402

WALKABLE = set(".'")
STEP = {k: v for k, v in KEYPAD.items() if k != '5'}


def digit(dx, dy):
    """The keypad digit for a step, or None if it is not one of the eight."""
    for key, (sx, sy) in STEP.items():
        if (sx, sy) == (dx, dy):
            return key
    return None


def tour(panel, start):
    """A depth-first walk over every reachable floor tile; returns digits."""
    height = len(panel)
    width = max(len(row) for row in panel)
    visited = {start}
    keys = []
    stack = [(start, iter(sorted(STEP.values())))]
    while stack:
        (x, y), steps = stack[-1]
        advanced = False
        for (dx, dy) in steps:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in visited or panel[ny][nx] not in WALKABLE:
                continue
            key = digit(dx, dy)
            visited.add((nx, ny))
            keys.append(key)
            stack.append(((nx, ny), iter(sorted(STEP.values()))))
            advanced = True
            break
        if not advanced:
            stack.pop()
    return keys


def main(argv):
    if len(argv) < 1:
        print(__doc__.strip())
        return 1
    s = load(argv[0])
    me = s.me
    if not me:
        print('no @ on this screen')
        return 1
    panel = s.panel
    steps = tour(panel, me)
    print(f'@ at {me}; a tour of the drawn floor is {len(steps)} steps')
    print(''.join(steps))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
