#!/usr/bin/env python3
"""What changed between two screens - and whether anything did at all.

Written for the shared library, 2026-11-10.

The commonest silent failure in this game is a key that does nothing: a
digit string stopped by a wall, an aim that landed inside rock, a command
swallowed by a `-more-` or by look mode. The tell is always the same - the
screen is identical and the turn counter has not moved - and it is easy to
miss when reading two 80x24 dumps by eye.

    python3 tools/screen/diff.py screen-41.txt screen-42.txt
    python3 tools/screen/diff.py screen-41.txt screen-42.txt --tiles

It compares the message line, the sidebar, the status line and the map, and
says plainly when nothing at all changed. The game turn is not on the screen:
it is in `ask/question-<n>.txt`, and this prints it when the files are beside
each other.
"""
import re
import sys
from pathlib import Path

from screen import load


def turn_of(path):
    """The game turn, from the question file beside the screen, if it is there."""
    found = re.match(r'screen-(\d+)\.txt$', Path(path).name)
    if not found:
        return None
    question = Path(path).with_name(f'question-{found.group(1)}.txt')
    if not question.exists():
        return None
    for line in question.read_text().splitlines():
        if line.startswith('turn '):
            return int(line.split()[1])
    return None


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 0
    before, after = load(argv[0]), load(argv[1])
    turns = (turn_of(argv[0]), turn_of(argv[1]))
    changed = False

    if before.message != after.message:
        changed = True
        print(f'message: {before.message!r}\n      -> {after.message!r}')
    if before.status != after.status:
        changed = True
        print(f'status : {before.status.strip()!r}\n      -> '
              f'{after.status.strip()!r}')
    was, now = before.sidebar, after.sidebar
    for field in sorted(set(was) | set(now)):
        if was.get(field) != now.get(field):
            changed = True
            print(f'{field:<8}: {was.get(field)} -> {now.get(field)}')
    if before.me != after.me:
        changed = True
        print(f'@       : {before.me} -> {after.me}')

    tiles = [(x, y, before.at(x, y), after.at(x, y))
             for y in range(len(after.panel))
             for x in range(len(after.panel[0]))
             if before.at(x, y) != after.at(x, y)]
    if tiles:
        changed = True
        print(f'map     : {len(tiles)} tiles differ')
        if '--tiles' in argv:
            for x, y, old, new in tiles:
                print(f'   {x:>2},{y:<2}  {old!r} -> {new!r}')
    if all(turns):
        print(f'turn    : {turns[0]} -> {turns[1]} '
              f'({turns[1] - turns[0]:+d})')
        if turns[0] == turns[1]:
            print('the turn did not move: the game took no time, so the keys '
                  'did nothing the game recognised. Read the message line.')
    if not changed:
        print('nothing changed at all. Whatever you sent was refused, '
              'swallowed by a -more-, eaten by look mode, or stopped by a '
              'wall. Read the message line before sending it again.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
