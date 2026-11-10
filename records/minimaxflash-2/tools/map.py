#!/usr/bin/env python3
"""Parse one Angband screen dump into the map panel, and route on it.

The tool reads ONLY the text the game printed. It does not reimplement the
game's pathfinding: it reports a *route* over tiles that are visibly floor,
as a string of the game's own movement digits, and lets the game walk it.

Usage:
    python3 map.py <screen.txt>              # print the map + notable glyphs
    python3 map.py <screen.txt> --to X,Y     # route from '@' to map coord X,Y
    python3 map.py <screen.txt> --shops      # route to each store door

Map coordinates: x = screen column - 13, y = screen row - 1 (the map panel of
Angband 4.2.6 is screen rows 1..22, columns 13..78, 66x22 tiles, 1:1).
"""
import sys
from collections import deque

COL0 = 13          # first column of the map panel
ROW0 = 1           # first row of the map panel
W, H = 66, 22      # panel size in tiles

# Digits on the numeric keypad, as the game receives them.
# Digit -> (dx, dy) in screen space: 2 is south, so dy grows downward.
DIR = {'1': (-1, 1), '2': (0, 1), '3': (1, 1),
       '4': (-1, 0), '5': (0, 0), '6': (1, 0),
       '7': (-1, -1), '8': (0, -1), '9': (1, -1)}

FLOOR = set('.')           # definitely walkable
MAYBE = set(':')           # rubble / rough floor: walkable, but slower
STAIR = set('><')          # down / up staircase tiles


def read_screen(path):
    with open(path) as fh:
        lines = fh.read().split('\n')
    # line 0 is the "=== ASK n ..." header, line 1 the message line;
    # the map panel is screen rows 1..22.
    return lines[2:2 + H]


def grid(lines):
    g = []
    for r in range(H):
        line = lines[r] if r < len(lines) else ''
        row = []
        for c in range(W):
            j = COL0 + c
            row.append(line[j] if j < len(line) else ' ')
        g.append(row)
    return g


def find(g, ch):
    return [(x, y) for y in range(H) for x in range(W) if g[y][x] == ch]


def route(g, start, goal):
    """BFS over floor tiles. Returns a list of keypad digits, or None."""
    if start is None:
        return None
    seen = {start}
    q = deque([(start, [])])
    while q:
        (x, y), path = q.popleft()
        if (x, y) == goal:
            return path
        for d, (dx, dy) in DIR.items():
            if d == '5':
                continue
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            if (nx, ny) in seen:
                continue
            cell = g[ny][nx]
            if cell not in FLOOR and cell not in MAYBE and cell not in STAIR:
                continue
            seen.add((nx, ny))
            q.append(((nx, ny), path + [d]))
    return None


def main():
    path = sys.argv[1]
    args = sys.argv[2:]
    lines = read_screen(path)
    g = grid(lines)

    print("     " + "".join(str((x // 10) % 10) if x % 10 == 0 else ' '
                            for x in range(W)))
    print("     " + "".join(str(x % 10) for x in range(W)))
    for y in range(H):
        print("%3d |%s|" % (y, "".join(g[y])))
    print("     " + "".join(str((x // 10) % 10) if x % 10 == 0 else ' '
                           for x in range(W)))
    print("     " + "".join(str(x % 10) for x in range(W)))

    me = find(g, '@')
    print("\n@ at map", me)
    if '--from' in args:
        i = args.index('--from')
        fx, fy = (int(v) for v in args[i + 1].split(','))
        me = [(fx, fy)]
        print("using start", me)
    for ch in '12345678<>':
        p = find(g, ch)
        if p:
            for (x, y) in p:
                d = (x - me[0][0], y - me[0][1]) if me else None
                print("glyph %s at map (%d,%d)  offset from @ = %s"
                      % (ch, x, y, d))

    if '--to' in args:
        i = args.index('--to')
        tx, ty = (int(v) for v in args[i + 1].split(','))
        p = route(g, me[0], (tx, ty))
        print("route to (%d,%d): %s" % (tx, ty, "".join(p) if p else "NONE"))

    if '--shops' in args:
        for ch in '12345678':
            p = find(g, ch)
            if not p:
                continue
            # the tile just left of the door, which is floor
            for tx, ty in [(p[0][0] - 1, p[0][1]), (p[0][0] + 1, p[0][1]),
                           (p[0][0], p[0][1] - 1), (p[0][0], p[0][1] + 1)]:
                r = route(g, me[0], (tx, ty))
                if r:
                    print("store %s door (%d,%d): walk %s then step onto it"
                          % (ch, p[0][0], p[0][1], "".join(r)))
                    break
            else:
                print("store %s: no route found" % ch)


if __name__ == '__main__':
    main()
