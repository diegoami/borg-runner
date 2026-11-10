#!/usr/bin/env python3
# Adopted into the shared library from `mmf-mage.3`'s own tools/panel.py,
# 2026-11-10. The run's copy stays in records/mmf-mage.3/tools/panel.py as it played it;
# this one may be corrected, and the correction belongs in this header.
"""Print the map panel, and the eight squares around `@`, with coordinates.

My own file, mmf-mage.3 (2026-11-10). I miscounted the printed map by one
column twice in this life (the shared tools/screen/map.py prints a ruler that
is offset from the content by one, and a printed row's leading spaces are
easy to miscount), and both mistakes cost a walk. So this prints the map
with a ruler whose marks are IN the row, and then prints the neighbourhood of
`@` tile by tile with the coordinates, which is what a route needs.

    python3 tools/panel.py runs/mmf-mage.3/ask/screen-154.txt
"""
import sys

sys.path.insert(0, '../../tools/screen')
from screen import load  # noqa: E402


def main(path):
    s = load(path)
    print('me', s.me, '|', s.status)
    print('msg:', repr(s.message))
    # ruler: every tenth column gets a digit, every fifth gets a mark
    ruler = ''.join('|' if x % 10 == 0 else ('+' if x % 5 == 0 else ' ')
                    for x in range(66))
    print('    ' + ruler)
    for y in range(22):
        row = ''.join(s.at(x, y) or ' ' for x in range(66))
        if row.strip():
            print('%3d %s' % (y, row))
    me = s.me
    if me:
        print()
        print('around @ (%d,%d):' % me)
        for dy in (-1, 0, 1):
            cells = []
            for dx in (-1, 0, 1):
                x, y = me[0] + dx, me[1] + dy
                c = s.at(x, y)
                cells.append('%s(%d,%d)' % (c if c else '?', x, y))
            print('  ' + '  '.join(cells))
    print()
    for g, items in sorted(s.glyphs().items()):
        for it in items:
            print('  glyph %r at %s  offset %s' % (g, it['at'], it['offset']))


if __name__ == '__main__':
    main(sys.argv[1])
