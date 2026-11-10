#!/usr/bin/env python3
"""Plan a long digit-walk chain from the current panel, for minimaxflash-1.5.

A digit string runs through every turn as long as nothing blocks it, so the
best ask is one long chain through floor that ends in the DARK (an unexplored
square), because the sweep's whole job is to convert dark into remembered.
This does a bounded best-first search over the panel, treats a blank square
as passable but unknown, avoids magma (2d8) and treats a closed door as a
place where a failed pick eats the rest of the key string, and prints the
chain.

Usage:  python3 g.py <screen-file> [max-steps]
"""
import sys
from collections import deque

path = sys.argv[1]
MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 24

lines = open(path).read().split('\n')
rows = []
for li in range(1, 23):
    rows.append(lines[li][14:80] if len(lines[li]) >= 14 else '')

at = None
for r, row in enumerate(rows):
    if '@' in row:
        at = (row.index('@'), r)
        break
if at is None:
    print('no @')
    sys.exit(1)
ax, ay = at

DIRS = {8: (0, -1), 2: (0, 1), 4: (-1, 0), 6: (1, 0)}
COST = {' ': 1.0, '.': 1.0, "'": 1.0, '+': 3.0, '%': 8.0}


def tile(x, y):
    if 0 <= y < 22 and 0 <= x < len(rows[y]):
        return rows[y][x]
    return '#'


# state: (x, y) -> (unknown_count, cost, depth, parent_key)
best = {(ax, ay): (0, 0.0, 0, None)}
path_of = {(ax, ay): ''}
pq = deque([(ax, ay)])
while pq:
    x, y = pq.popleft()
    un, c, dep, _ = best[(x, y)]
    if dep >= MAX:
        continue
    for d, (dx, dy) in DIRS.items():
        nx, ny = x + dx, y + dy
        t = tile(nx, ny)
        if t not in COST:
            continue
        ncost = COST[t]
        if ncost == 8.0 and dep > 3:
            continue          # magma: only near the start
        nun = un + (1 if t == ' ' else 0)
        ndep = dep + 1
        key = (nx, ny)
        cur = best.get(key)
        if cur is None or (nun, -ncost) > (cur[0], -cur[1]):
            best[key] = (nun, ncost, ndep, key)
            path_of[key] = path_of[(x, y)] + str(d)
            pq.append(key)

ends = [k for k in best if best[k][0] > 0 and best[k][2] > 0]
if not ends:
    print('no path into the dark')
    sys.exit(0)
ends.sort(key=lambda k: (-best[k][0], best[k][2], best[k][1]))
target = ends[0]
chain = path_of[target]
x, y = ax, ay
for ch in chain:
    dx, dy = DIRS[int(ch)]
    x, y = x + dx, y + dy
print('from panel (%d,%d) to (%d,%d); %d steps; %d unknown squares reached'
      % (ax, ay, x, y, len(chain), best[target][0]))
print('keys: ' + chain)
