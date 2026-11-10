#!/usr/bin/env python3
"""Compact reading of the newest screen: state, the map around @, and glyphs.

Usage: python3 runs/mmx-pri-1.2/tools/st.py [ask]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools' / 'screen'))
from screen import load  # noqa: E402

run = Path('runs/mmx-pri-1.2')
n = sys.argv[1] if len(sys.argv) > 1 else str(
    max(int(p.stem.split('-')[1]) for p in (run / 'ask').glob('screen-*.txt')))
s = load(run / 'ask' / f'screen-{n}.txt')
sb = s.sidebar
me = s.me
print(f"ask {n} | turn {s.turn if hasattr(s,'turn') else ''} | {s.status.strip()}")
print(f"HP {sb.get('HP')} SP {sb.get('SP')} AC {sb.get('Cur AC')} L{sb.get('LEVEL')} "
      f"NXT {sb.get('NXT')} AU {sb.get('AU')} | @ {me}")
if me:
    for y in range(0, 22):
        segs = []
        cur = None
        for x in range(0, 66):
            c = (s.at(x, y) or '?').replace(' ', '?')
            if c == '?':
                if cur:
                    segs.append(cur)
                    cur = None
                continue
            if cur and cur[0] == c and cur[2] == x - 1:
                cur = (c, cur[1], x)
            else:
                if cur:
                    segs.append(cur)
                cur = (c, x, x)
        if cur:
            segs.append(cur)
        if segs:
            print(f"y{y:2d} " + ' '.join(f"{a}-{b}{c}" for c, a, b in segs))
print('--- interesting')
for yy in range(22):
    for xx in range(66):
        c = s.at(xx, yy)
        if c and c not in '. #' and c != '@':
            d = (xx - me[0], yy - me[1]) if me else (0, 0)
            print(f"  {c!r} at ({xx},{yy}) ({d[0]:+d}E {d[1]:+d}S)")
