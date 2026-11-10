#!/usr/bin/env python3
"""Where the level is still dark, and the keys to send the game at it.

Written for the shared library, 2026-11-10, against the hardest thing in the
corpus: a level is 198x66, the view is 66x22, there is **exactly one** down
staircase and it is placed uniformly at random (`gen-cave.c:1583`,
`gen-util.c:620`). No heuristic finds it. Only coverage does, and coverage is
bookkeeping across hundreds of screens that a player cannot keep in its head.

Two ways in, and the first is much the better:

**1. The whole-level view, which costs one ask.** Press `M`, save the screen,
and pass it here. `M` draws the *remembered* level scaled into a box - the
corpus found that out the hard way, and it is exactly what coverage planning
needs: everything seen, in one picture.

    python3 tools/screen/explore.py m-screen.txt

It reports the staircases and stores remembered, how much of the level is
still blank, which direction holds most of the blank, and the keys to send.
Because the box is scaled about 3:1, a position in it is worth about three
level tiles, so it gives a **direction and a distance**, not a tile - and
when a `>` is remembered it tells you to stop reading maps and use `l>g`,
which is the game walking to it in one ask.

**2. The ordinary screens of a run**, which cost nothing because you already
have them. The panel scrolls, and fitting two panels together is guesswork
that invented duplicate corridors when this tool tried it - so it does not
guess: it accumulates only while the view is **stable**, says when the view
moved, and reports the current stretch.

    python3 tools/screen/explore.py runs/mine/ask --last 30

What it never does is route. `find_path` crosses ground you have never seen
and one ask covers 17 to 44 tiles; nothing written here beats that. The answer
is always an aim in the game's own keys.
"""
import sys
from collections import Counter
from pathlib import Path

from aim import keys_to
from screen import MAP_H, MAP_W, STEP, load

LEVEL_W, LEVEL_H = 198, 66
STATIC = set('#%.+\':<>')
WALKABLE = set(".:'")
STORES = '12345678'
HEADINGS = {(0, -1): 'north', (1, -1): 'north-east', (1, 0): 'east',
            (1, 1): 'south-east', (0, 1): 'south', (-1, 1): 'south-west',
            (-1, 0): 'west', (-1, -1): 'north-west'}


# -- 1. the whole-level view -------------------------------------------------

def framed(rows):
    """The inside of the `M` view's box, or None if this is not one."""
    if not rows or not rows[0].startswith('+--'):
        return None
    bottom = next((index for index in range(len(rows) - 1, 0, -1)
                   if rows[index].startswith('+--')), None)
    if bottom is None:
        return None
    inside = []
    for row in rows[1:bottom]:
        inside.append(row[1:len(rows[0]) - 1] if row.startswith('|') else '')
    return inside


def whole_level(inside):
    wide, high = max(len(row) for row in inside), len(inside)
    scale = (LEVEL_W / wide, LEVEL_H / high)
    seen = {(x, y): glyph for y, row in enumerate(inside)
            for x, glyph in enumerate(row)
            if glyph not in ' ' and glyph != '|'}
    me = next((at for at, glyph in seen.items() if glyph == '@'), None)
    print(f'the remembered level, {wide}x{high} in the box and about '
          f'{scale[0]:.0f}x{scale[1]:.0f} level tiles per box tile')
    drawn = sum(1 for glyph in seen.values() if glyph in STATIC)
    print(f'{drawn} of {wide * high} box tiles have terrain in them: '
          f'{100.0 * drawn / (wide * high):.0f}% of the level is remembered at '
          f'all, and the rest is dark')
    if not me:
        print('! no `@` in the box, so no direction from here')
        return 0
    print(f'@ in the box at {me}')
    for glyph, what in (('>', 'DOWN staircase'), ('<', 'up staircase')):
        for at, found in sorted(seen.items()):
            if found != glyph:
                continue
            dx, dy = at[0] - me[0], at[1] - me[1]
            steps = (round(dx * scale[0]), round(dy * scale[1]))
            print(f'{what} in the box at {at}: about {abs(steps[0])} '
                  f'{"E" if steps[0] > 0 else "W"} and {abs(steps[1])} '
                  f'{"S" if steps[1] > 0 else "N"} in level tiles')
    stores = {glyph: at for at, glyph in seen.items() if glyph in STORES}
    if stores:
        print('stores remembered: ' + ', '.join(
            f'{glyph} at {at}' for glyph, at in sorted(stores.items())))
    if any(glyph == '>' for glyph in seen.values()):
        print('\nThe game remembers that staircase too, so stop measuring: '
              '`l>g` walks to it in one ask, then `> ` takes it (the trailing '
              'space clears the -more-).')
        return 0
    # Where is the dark? Count blank box tiles by direction from `@`.
    dark = Counter()
    for y in range(high):
        for x in range(wide):
            if (x, y) in seen:
                continue
            dark[(1 if x > me[0] else -1 if x < me[0] else 0,
                  1 if y > me[1] else -1 if y < me[1] else 0)] += 1
    if not dark:
        print('\nnothing in the box is blank: the level is remembered and has '
              'no `>` in it. Reroll - `< ` then `> ` - which is two asks '
              'against a level that cannot pay.')
        return 0
    heading, blank = dark.most_common(1)[0]
    name = HEADINGS.get(heading, 'here')
    far = round(min(LEVEL_W, LEVEL_H) * 0.7)
    print(f'\nno `>` is remembered. Most of the dark is {name} '
          f'({blank} box tiles of {sum(dark.values())}).')
    print(f'answer: *{keys_to(heading[0] * far, heading[1] * far)}g')
    print(f'(the cursor is clamped to the level, so an over-long aim is safe, '
          f'and `find_path` crosses ground you have never seen. Send it alone '
          f'in the ask.)')
    return 0


# -- 2. the ordinary screens of a run ----------------------------------------

def same_view(previous, panel):
    """Whether these two panels are the same window on the level.

    Only the stable case is trusted. Fitting a scrolled panel onto its
    predecessor was tried and it duplicated corridors: two stretches of a
    level look alike, and a wrong fit is worse than no fit.
    """
    same = compared = 0
    for before, after in zip(previous, panel):
        for a, b in zip(before, after):
            if a in STATIC and b in STATIC:
                compared += 1
                same += a == b
    return compared >= 80 and same / compared >= 0.97


def stretch(paths):
    seen, me, moves, menus, depths = {}, None, 0, 0, Counter()
    previous = None
    for path in paths:
        s = load(path)
        if s.overlay:
            menus += 1
            continue
        if s.depth_line:
            depths[s.depth_line] += 1
        if previous is not None and not same_view(previous, s.panel):
            moves += 1
            seen, previous = {}, None        # the window moved: start again
        for y, row in enumerate(s.panel):
            for x, glyph in enumerate(row):
                if glyph in STATIC:
                    seen[(x, y)] = glyph
        if s.me:
            me = s.me
        previous = s.panel
    return seen, me, moves, menus, depths


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 0
    paths, last = [], None
    for index, argument in enumerate(argv):
        if argument == '--last':
            last = int(argv[index + 1])
        elif argument.startswith('--') or (index and argv[index - 1] == '--last'):
            continue
        elif Path(argument).is_dir():
            paths += sorted(Path(argument).glob('screen-*.txt'),
                            key=lambda p: int(p.stem.split('-')[1]))
        else:
            paths.append(Path(argument))
    if not paths:
        print('no screens found')
        return 1

    inside = framed(Path(paths[0]).read_text().split('\n'))
    if inside is not None:
        return whole_level(inside)

    if last:
        paths = paths[-last:]
    seen, me, moves, menus, depths = stretch(paths)
    print(f'{len(paths)} screens: {menus} menus skipped, the view moved '
          f'{moves} times')
    if len(depths) > 1:
        print(f'! more than one depth here {dict(depths)}, and a level is '
              f'regenerated when you leave it, so these are different levels')
    print(f'the current stretch holds {len(seen)} tiles of the 66x22 view. '
          f'For the whole level in one ask, press `M` and pass that screen '
          f'here instead.')
    if '>' in seen.values():
        print('a `>` is in view: `l>g` then `> `.')
        return 0
    if not me:
        print('no `@` on the last screen, so no aim')
        return 0
    frontier = [(x, y) for (x, y), glyph in seen.items() if glyph in WALKABLE
                and any((x + dx, y + dy) not in seen
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    if not frontier:
        print('nothing you can see borders the dark inside this view; press '
              '`M` for the level, or reroll with `< ` then `> `.')
        return 0
    dark = Counter()
    for x, y in frontier:
        dark[(1 if x > me[0] else -1 if x < me[0] else 0,
              1 if y > me[1] else -1 if y < me[1] else 0)] += 1
    heading = dark.most_common(1)[0][0]
    far = round(min(LEVEL_W, LEVEL_H) * 0.7)
    print(f'{len(frontier)} tiles in view border the dark, most of it '
          f'{HEADINGS.get(heading, "here")}')
    print(f'answer: *{keys_to(heading[0] * far, heading[1] * far)}g')
    print('(alone in the ask; aim long, because a short aim lands in a wall '
          'and does nothing at all)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
