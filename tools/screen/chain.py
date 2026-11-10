#!/usr/bin/env python3
# Adopted into the shared library from `mmx-ran-1`'s own tools/chain.py,
# 2026-11-10. The run's copy stays in records/mmx-ran-1/tools/chain.py as it played it;
# this one may be corrected, and the correction belongs in this header.
"""Plan a digit-walk chain across the map panel, for mmx-ran-1 (Hobbit Ranger, seed 137).

Written by the player of `mmx-ran-1`, 2026-11-10, after measuring that the
game's own movement covers one to three tiles an ask on depth 1 of this seed:
`lxg` advanced one tile, the run command stops in an open room, and the aimed
walk gave a bogus one-tile path (find_path's unknown-destination fallback).
A digit string, on the other hand, runs through every turn until it meets a
wall - so the fastest ask is ONE long chain of direction keys planned over the
panel so that it does not meet a wall before its end.

The idea is the one minimaxflash-1.5 used in `records/minimaxflash-1.5/tools/g.py`;
this version reads the panel through the shared `tools/screen/screen.py`, which
pads the rows (a raw dump strips trailing blanks, and a short row reads as a
wall), and it requires the FIRST step to be known floor, because a chain whose
first step is a wall moves the character nowhere at all.

CORRECTION, 2026-11-10 (the player of mmx-ran-1, later the same day): the
paragraph above says the aimed walk "gave a bogus one-tile path". That was
wrong, and it was the reason this tool was written. The aimed walk
(`*` + `p` + digits + `g`) measures **9 to 23 actions in one ask** on depth 1
of seed 137, and it crosses unexplored ground. The chain this tool plans is
the slower instrument (1 to 9 actions an ask, and cut short by any
disturbance): use the aimed walk for movement and this tool only when a
specific tile is wanted. See `agents/minimax/COMMON.md`, the mmx-ran-1 section.

    python3 chain.py runs/mmx-ran-1/ask/screen-57.txt [max-keys]

It prints the chain and the screen coordinates it starts from.
"""
import sys
from collections import deque
from pathlib import Path

# The shared screen reader: a sibling of this file when the tool has been
# adopted into tools/screen/, and tools/screen/ when it still lives in the
# run's own tools/ directory.
_HERE = Path(__file__).resolve().parent
for _candidate in (_HERE, _HERE.parents[2] / 'tools' / 'screen'):
    if (_candidate / 'screen.py').exists():
        sys.path.insert(0, str(_candidate))
        break

from screen import load  # noqa: E402

# Movement keys, as (dx, dy) with y increasing downward, as the game has it.
DIRS = {'8': (0, -1), '2': (0, 1), '4': (-1, 0), '6': (1, 0),
        '7': (-1, -1), '9': (1, -1), '1': (-1, 1), '3': (1, 1)}

# What the chain may walk on, and what a step costs. A space is UNKNOWN
# ground: the chain may go there (that is where the new remembering happens)
# but it may be a wall, so it costs more than a known floor tile.
COST = {'.': 1.0, "'": 1.2, ' ': 1.6}
# A closed door: walking into it picks the lock, and a failed pick eats the
# rest of the key string, so it is expensive.
COST['+'] = 6.0
# Items on the floor are walkable, but a step onto one is a step that learns
# nothing, so they cost a little more than floor.
for _ch in '$!?_/\\|(){}"':
    COST[_ch] = 1.8

# Walls ('#'), mineral veins ('%' and '*'), rubble (':'), traps ('^') and every
# monster (a letter) are simply not in COST, so the search never enters them.


def main(argv):
    screen = argv[1]
    max_keys = int(argv[2]) if len(argv) > 2 else 24

    s = load(screen)
    if s.overlay:
        print('a menu is covering the map; this tool cannot read it')
        return 1
    if not s.me:
        print('no @ on this screen')
        return 1
    rows = [''.join(s.at(x, y) for x in range(66)) for y in range(22)]
    ax, ay = s.me

    def tile(x, y):
        if 0 <= y < 22 and 0 <= x < 66:
            return rows[y][x]
        return '#'

    # Best-first over the panel. What an ask can win is the tiles it turns
    # from dark into remembered, and those can only come from the DARK part of
    # the chain: a digit string stops at the first wall, so the chain has to
    # cross the known floor first and dash into the dark only at the end.
    # So the value of a cell is (the dark tiles at the END of the path to it,
    # -the cost of the path), and the best cell of all is the one whose chain
    # ends deepest in the dark.
    #
    # A diagonal step needs BOTH of its orthogonal neighbours to be passable
    # (the game will not let you walk past a wall corner), so the search
    # refuses a diagonal whose corners are not known floor. That rule is
    # worth more than the rest of this tool put together: a chain that plans
    # a diagonal into a wall corner stops there, and everything after it in
    # the chain is lost.
    def step_ok(x, y, key):
        dx, dy = DIRS[key]
        if dx and dy:
            for side in ((dx, 0), (0, dy)):
                t = tile(x + side[0], y + side[1])
                if t not in COST or t == ' ':
                    return False
        return True

    best = {(ax, ay): (0, 0.0, 0)}
    path_of = {(ax, ay): ''}
    pq = deque([(ax, ay)])
    while pq:
        x, y = pq.popleft()
        dark, cost, dep = best[(x, y)]
        if dep >= max_keys:
            continue
        for key, (dx, dy) in DIRS.items():
            nx, ny = x + dx, y + dy
            t = tile(nx, ny)
            if t not in COST:
                continue
            if dep == 0 and t == ' ':
                continue          # the first step must be known floor
            if not step_ok(x, y, key):
                continue          # a diagonal past a wall corner is refused
            ndark = dark + 1 if t == ' ' else 0
            ncost = cost + COST[t]
            ndep = dep + 1
            pos = (nx, ny)
            cur = best.get(pos)
            if cur is None or (ndark, -ncost) > (cur[0], -cur[1]):
                best[pos] = (ndark, ncost, ndep)
                path_of[pos] = path_of[(x, y)] + key
                pq.append(pos)

    ends = [p for p in best if best[p][0] > 0 and best[p][2] > 0]
    if not ends:
        print('no path into the dark from (%d,%d)' % (ax, ay))
        return 0
    ends.sort(key=lambda p: (-best[p][0], -best[p][2], best[p][1]))
    target = ends[0]
    chain = path_of[target]
    x, y = ax, ay
    for ch in chain:
        dx, dy = DIRS[ch]
        x, y = x + dx, y + dy
    print('from panel (%d,%d) to (%d,%d): %d keys, %d dark tiles at the end'
          % (ax, ay, x, y, len(chain), best[target][0]))
    print('keys: ' + chain)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
