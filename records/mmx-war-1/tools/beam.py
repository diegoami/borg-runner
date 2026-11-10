#!/usr/bin/env python3
"""Plan a long digit-walk chain from the current panel.

Copied from the family's own `runs/minimaxflash-1.5/g.py` (seed 23 druid) by the
player of mmx-war-1, with the panel offset corrected from [14:80] to
[13:79] so that the known/unknown boundary is right.

A digit string runs through every turn as long as nothing blocks it, so the
best ask is one long chain through floor that ends as deep in the DARK (an
unexplored square) as possible, because the sweep's whole job is to convert
dark into remembered.  This is a beam search over the panel: a blank square is
passable but unknown, magma costs 2d8 so it is avoided, a closed door is a
place where a failed pick cancels the rest of the key string, any letter is a
monster and is never walked into, and a square already walked in this chain is
charged extra so the search does not oscillate.

Usage:  python3 g.py <screen-file> [max-steps]
"""
import sys

path = sys.argv[1]
MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 24
BEAM = 500

lines = open(path).read().split('\n')
# The map panel starts at screen column 13 and row 1 (tools/screen/screen.py
# MAP_COL/MAP_ROW, and the game's own SCREEN_WID = 80-13-1 = 66).  The
# original minimaxflash-1.5 copy sliced [14:80], which is one column off;
# it did not matter there because the chain is relative to '@', but the
# unknown/known boundary does matter, so this copy uses the right offset.
rows = []
for li in range(1, 23):
    # ljust(66) matters: the screen dump strips trailing whitespace, so a map
    # row that is entirely blank (all unknown) comes back as a short line and
    # every tile on it would read as a wall.  Found at ask 34.
    rows.append((lines[li][13:79] if len(lines[li]) >= 13 else '').ljust(66))

at = None
for r, row in enumerate(rows):
    if '@' in row:
        at = (row.index('@'), r)
        break
if at is None:
    print('no @')
    sys.exit(1)
ax, ay = at

DIRS = ((8, 0, -1), (2, 0, 1), (4, -1, 0), (6, 1, 0))
COST = {' ': 1.0, '.': 1.0, "'": 1.0, '+': 4.0, '%': 12.0}
for _c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
    COST[_c] = None


def tile(x, y):
    if 0 <= y < 22 and 0 <= x < len(rows[y]):
        return rows[y][x]
    return '#'


def bit(x, y):
    return 1 << (y * 66 + x)


# beam state: (x, y, unknown_mask, visited_mask, dist, cost, chain)
beam = [(ax, ay, 0, bit(ax, ay), 0, 0.0, '')]
best = None


def score(s):
    unk = bin(s[2]).count('1')
    revisits = s[4] - bin(s[3]).count('1')
    # maximise unknown squares remembered, then end in the dark, then
    # progress without revisiting
    return (-unk, -(s[4] - 3 * revisits), s[5])


for depth in range(MAX):
    nxt = []
    for (x, y, mask, vis, dist, cost, chain) in beam:
        for (d, dx, dy) in DIRS:
            nx, ny = x + dx, y + dy
            t = tile(nx, ny)
            if t not in COST or COST[t] is None:
                continue
            # The first steps must be KNOWN floor: an unknown square may be a
            # wall, and a chain that starts on one moves the character nowhere
            # at all (measured: sixteen asks of nothing).
            if depth < 1 and t not in ".'+":
                continue
            c = COST[t]
            if t == '%' and depth > 2:
                continue
            nb = bit(nx, ny)
            revisit = 1 if nb & vis else 0
            nm = mask | (nb if t == ' ' else 0)
            nxt.append((nx, ny, nm, vis | nb, dist + 1, cost + c + 3 * revisit,
                        chain + str(d)))
    if not nxt:
        break
    nxt.sort(key=score)
    beam = nxt[:BEAM]
    if best is None or score(beam[0]) < score(best):
        best = beam[0]

if best is None:
    print('no path')
    sys.exit(0)
x, y, mask, vis, dist, cost, chain = best
print('from panel (%d,%d) to (%d,%d); %d steps; %d unknown squares memorised'
      % (ax, ay, x, y, dist, bin(mask).count('1')))
print('keys: ' + chain)
near = []
for dy in range(-4, 5):
    for dx in range(-4, 5):
        if dx == 0 and dy == 0:
            continue
        t = tile(ax + dx, ay + dy)
        if t.isalpha():
            where = ('%dE' % dx if dx > 0 else '%dW' % -dx)
            if dy:
                where += ('%dS' % dy if dy > 0 else '%dN' % -dy)
            near.append('%s at %s' % (t, where))
print('near: ' + (', '.join(near) if near else 'none'))
