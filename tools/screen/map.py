#!/usr/bin/env python3
"""Print the map panel with rulers, and route over tiles that are drawn floor.

**Adopted into the shared library from `minimaxflash-2`'s own
`tools/map.py`, 2026-11-10.** The player wrote it while playing; it is kept
here so the next run does not write it again. Two changes were made in
adopting it:

- **its direction table was transposed**, so every route it printed walked
  the wrong way (`'4'` meant north instead of west, `'1'` north-west instead
  of south-west). The table now comes from `screen.KEYPAD`, where it is
  written once, with y increasing downward as a screen is indexed.
- it reads the screen through `screen.py`, so it handles a raw dump, a pasted
  `answer` output, and a menu drawn over the map (which it now refuses to
  route on, because those glyphs are the menu's text).

**Read this before using the route it prints.** A route here is a string of
movement digits, and a digit string *stops at the first wall and the rest is
dropped* - measured in two runs. The game's own walk covers 17 to 44 tiles in
one ask and pathfinds through ground you have not seen
(`tools/screen/aim.py`); this tool is for the short, local case where you can
see the whole way and want exact steps - stepping onto a store door, moving
two tiles to a corridor mouth, backing out of a room.

    python3 tools/screen/map.py screen.txt                # the panel + glyphs
    python3 tools/screen/map.py screen.txt --to 52,4      # route from @
    python3 tools/screen/map.py screen.txt --shops        # route to each store
"""
import sys
from collections import deque

from screen import FLOOR, MAP_H, MAP_W, RUBBLE, STEP, STORES, load

WALKABLE = set(FLOOR) | set(RUBBLE) | set("'")      # floor, rubble, open door


def route(panel, start, goal, walkable=WALKABLE):
    """Breadth-first over tiles drawn walkable. Movement digits, or None."""
    if start is None:
        return None
    seen, queue = {start}, deque([(start, '')])
    while queue:
        (x, y), keys = queue.popleft()
        if (x, y) == goal:
            return keys
        for (dx, dy), key in STEP.items():
            if key == '5':
                continue
            nx, ny = x + dx, y + dy
            if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
                continue
            if (nx, ny) in seen or (nx, ny) != goal and \
                    panel[ny][nx] not in walkable:
                continue
            seen.add((nx, ny))
            queue.append(((nx, ny), keys + key))
    return None


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 0
    s = load(argv[0])
    if s.overlay:
        print(f'! {s.overlay}: the map panel is covered, so there is nothing '
              f'here to route on. Escape first.')
        return 1
    panel, me = s.panel, s.me
    units = ''.join(str(x % 10) for x in range(MAP_W))
    tens = ''.join(str(x // 10 % 10) if x % 10 == 0 else ' '
                   for x in range(MAP_W))
    print(f'     {tens}\n     {units}')
    for y, row in enumerate(panel):
        print(f'{y:>4} |{row}|')
    print(f'     {units}')
    print(f'\n@ at {me}' if me else '\nno @ on this screen')

    for glyph in STORES:
        for (x, y) in s.find(glyph):
            away = (x - me[0], y - me[1]) if me else None
            print(f'store {glyph} at {x},{y}   offset from @ {away}')

    if '--to' in argv:
        x, y = (int(part) for part in argv[argv.index('--to') + 1].split(','))
        keys = route(panel, me, (x, y))
        print(f'route to {x},{y}: {keys or "none over tiles that are drawn"}')
        if keys and len(keys) > 8:
            print(f'({len(keys)} steps is long for a digit string: it stops at '
                  f'the first wall. Consider aim.py, which lets the game walk.)')
    if '--shops' in argv:
        if not me:
            print('no @, so no route')
            return 1
        for glyph in STORES:
            doors = s.find(glyph)
            if not doors:
                continue
            door = doors[0]
            keys = route(panel, me, door)
            print(f'store {glyph} at {door}: '
                  f'{keys or "no route over drawn floor"}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
