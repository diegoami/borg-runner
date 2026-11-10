#!/usr/bin/env python3
"""What is on this screen, and where it is relative to you.

Written for the shared library, 2026-11-10.

One ask of the game's own `[` lists the monsters it can see; this lists
*everything the screen has drawn* - stairs, doors, store entrances, items,
monsters, rubble - with map coordinates and the offset from `@` in the
game's own form (south and east positive), and costs no ask at all, because
it reads a screen you already have.

    python3 tools/screen/look.py runs/mine/ask/screen-42.txt
    python3 tools/screen/look.py screen.txt --map        # with coordinate rulers
    python3 tools/screen/look.py screen.txt --glyph '>'  # just this one

It cannot tell you what it cannot see. Two limits the runs paid for:

- **the tile under `@` is not drawn**, so the staircase you are standing on
  is invisible here and named only on the status line (which this prints);
- **a letter is a monster whose name is not on the screen.** `[` names them,
  and looking with `l` at a specific tile names one. Guessing from the letter
  is how a run walked into a floating eye.
"""
import sys

from screen import DOORS, FLOOR, RUBBLE, STAIRS, STORES, load

NAMED = {'<': 'up staircase', '>': 'DOWN STAIRCASE', '+': 'closed door',
         "'": 'open or broken door', ':': 'rubble', '*': 'mineral vein or item',
         '$': 'gold', ';': 'glyph or trap', '^': 'visible trap',
         ',': 'item or a mushroom patch - look before you step'}
KINDS = (('stairs', STAIRS), ('doors', DOORS), ('store entrances', STORES),
         ('rubble', RUBBLE))


def describe(glyph):
    if glyph in NAMED:
        return NAMED[glyph]
    if glyph.isalpha():
        return 'a monster (its letter is not its name: use `[` or look at it)'
    return 'an item or a feature'


def offset(where):
    dx, dy = where
    parts = []
    if dy:
        parts.append(f'{abs(dy)} {"S" if dy > 0 else "N"}')
    if dx:
        parts.append(f'{abs(dx)} {"E" if dx > 0 else "W"}')
    return ', '.join(parts) or 'here'


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 0
    s = load(argv[0])
    wanted = argv[argv.index('--glyph') + 1] if '--glyph' in argv else None
    if s.overlay:
        print(f'! {s.overlay}: the map panel is covered, so every coordinate '
              f'below is that menu\'s text, not the dungeon. Escape first.')
        return 1
    print(f'message : {s.message or "(none)"}')
    print(f'standing on: {s.terrain}   {s.depth_line}   '
          f'conditions: {", ".join(s.conditions) or "none"}')
    me = s.me
    print(f'@       : {me}' if me else '@       : not on this screen')
    if '--map' in argv:
        ruler = ''.join(str(x // 10 % 10) if x % 10 == 0 else ' '
                        for x in range(len(s.panel[0])))
        units = ''.join(str(x % 10) for x in range(len(s.panel[0])))
        print(f'      {ruler}\n      {units}')
        for y, row in enumerate(s.panel):
            print(f'{y:>5} |{row}|')
        print(f'      {units}')
    found = s.glyphs()
    if wanted:
        found = {wanted: found.get(wanted, [])}
    if not found:
        print('nothing but floor, wall and dark on this screen')
        return 0
    print('\nwhat is drawn, nearest first:')
    flat = [(glyph, tile) for glyph, tiles in found.items() for tile in tiles]

    def how_far(entry):
        away = entry[1]['offset']
        return max(abs(away[0]), abs(away[1])) if away else 0

    for glyph, tile in sorted(flat, key=how_far):
        at, away = tile['at'], tile['offset']
        print(f"  {glyph}  at {at[0]:>2},{at[1]:<2}  "
              f"{offset(away) if away else '':<12}  {describe(glyph)}")
    for name, glyphs in KINDS:
        seen = sum(len(found.get(g, [])) for g in glyphs)
        if seen:
            print(f'{name}: {seen}')
    if not found.get('>'):
        print('no down staircase is drawn here. The game can only walk you to '
              'one it already knows (`l>g`), so it has to be seen first - and '
              'the one under your feet is never drawn.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
