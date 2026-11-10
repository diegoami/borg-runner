#!/usr/bin/env python3
"""Read an M (whole-level) screen: remembered coverage, stairs, the player."""
import sys
from pathlib import Path

run = Path('runs/mmx-pri-1.2')
n = sys.argv[1] if len(sys.argv) > 1 else str(
    max(int(p.stem.split('-')[1]) for p in (run / 'ask').glob('screen-*.txt')))
lines = (run / 'ask' / f'screen-{n}.txt').read_text().split('\n')
box = [l for l in lines if l.startswith('|')]
grid = [l[1:79] for l in box]
LEVEL_W, LEVEL_H, MW, MH = 198, 66, 78, 22
known = 0
marks = []
for mr in range(MH):
    row = grid[mr] if mr < len(grid) else ''
    for mc in range(MW):
        c = row[mc] if mc < len(row) else ' '
        if c in ' ':
            continue
        known += 1
        if c in '<>':
            marks.append((c, mc, mr))
me = None
for mr in range(MH):
    row = grid[mr] if mr < len(grid) else ''
    if '@' in row:
        me = (row.index('@'), mr)
print(f"ask {n}: remembered cells {known} of {MW*MH} boxes "
      f"= {100.0*known/(MW*MH):.1f}% of the map; level tiles ~{known*2.5}")
print("stairs on the M map:", marks)
print("player at M", me, "= level", (int(me[0]*LEVEL_W/MW), int(me[1]*LEVEL_H/MH)) if me else None)
