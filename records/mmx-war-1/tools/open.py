#!/usr/bin/env python3
"""Which way is open? A reading of the panel around the player.

Written by the player of `minimaxflash-3` while playing (seed 313).

The panel draws what the player has SEEN.  A tile the player has never
looked at is a blank (space); a wall that has been seen is '#'.  So a run
of blanks is a direction with ground nobody has mapped yet, and the game
will pathfind into it.  This prints, for each of the eight directions,
how many tiles of unseen ground lie that way, so an aim can be chosen
without spending an ask on a direction that ends at a wall.

    python3 runs/minimaxflash-3/tools/open.py runs/minimaxflash-3/ask/screen-99.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools' / 'screen'))

from screen import KEYPAD, load  # noqa: E402

# The keypad in the game: '1' is south-west, '8' is north, '7' is
# north-west (vendor/angband/src/cave.c:49).
NAME = {'1': 'SW', '2': 'S', '3': 'SE', '4': 'W', '5': '-', '6': 'E',
        '7': 'NW', '8': 'N', '9': 'NE'}


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
    print(f"@ at {me}, HP {s.sidebar.get('HP')}, gold {s.sidebar.get('AU')}")
    rows = []
    for key in sorted(KEYPAD):
        if key == '5':
            continue
        dx, dy = KEYPAD[key]
        x, y = me
        unseen = 0
        seen = 0
        blocked = None
        for step in range(1, 40):
            x += dx
            y += dy
            if not (0 <= x < len(panel[0]) and 0 <= y < len(panel)):
                blocked = 'edge'
                break
            tile = panel[y][x]
            if tile == ' ':
                unseen += 1
            elif tile in ".'":
                seen += 1
            else:
                blocked = tile
                break
        rows.append((unseen, key, NAME[key], seen, blocked))
    for unseen, key, name, seen, blocked in sorted(rows, reverse=True):
        print(f'  {key} {name:>2}: {unseen:>2} unseen, {seen:>2} seen, '
              f'ends at {blocked}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
