#!/usr/bin/env python3
"""One line of state: where I am, what is next to me, and what the pack holds.

Written by the player of mmx-war-1 (seed 271, Half-Elf Warrior).

    python3 runs/mmx-war-1/tools/where.py runs/mmx-war-1/ask/screen-95.txt
"""
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                'tools', 'screen'))
from screen import load  # noqa: E402

# glyph -> what the game calls it, for the depth-1 monsters I want to kill
NAMES = {'k': 'small kobold (5 exp)', 'a': 'soldier ant (3 exp)',
         'm': 'grey mould (3 exp)', 'l': 'rock lizard (2 exp)',
         'w': 'white worm mass (2 exp)', 'i': 'icky thing',
         'C': 'canine or centipede', 'e': 'FLOATING EYE - never touch',
         ',': 'mushroom patch - confuses', 'p': 'person',
         'G': 'something G', 'o': 'something o'}
BAD = set('e,')
FLOOR = set(' .#:%*<>+=\'`~"!?,/0123456789abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ')


def latest():
    files = glob.glob('runs/mmx-war-1/ask/screen-*.txt')
    return sorted(files, key=lambda f: int(f.split('-')[-1].split('.')[0]))[-1]


def main(argv):
    f = argv[0] if argv else latest()
    s = load(f)
    me = s.me
    out = [f"{os.path.basename(f)} me={me} msg={s.message!r} "
           f"HP={s.sidebar.get('HP')} NXT={s.sidebar.get('NXT')} "
           f"AU={s.sidebar.get('AU')}"]
    if me:
        near = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                x, y = me[0] + dx, me[1] + dy
                if not (0 <= y < 22 and 0 <= x < 66):
                    continue
                ch = s.panel[y][x]
                if ch not in FLOOR:
                    where = f"{abs(dx)}E" if dx > 0 else (
                        f"{abs(dx)}W" if dx < 0 else '')
                    if dy:
                        where += f"{abs(dy)}S" if dy > 0 else f"{abs(dy)}N"
                    tag = NAMES.get(ch, '?')
                    mark = '!' if ch in BAD else ' '
                    near.append(f"{mark}{ch}@{where}({tag})")
        out.append('  near: ' + (', '.join(near) if near else 'none'))
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
