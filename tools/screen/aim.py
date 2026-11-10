#!/usr/bin/env python3
"""Turn a place on the screen into the keys that make the *game* walk there.

Written for the shared library, 2026-11-10, from the one technique the corpus
measured as fast (`ACCUMULATED_KNOWLEDGE.md` section 2, `minimaxflash-1.3`).

The game has a pathfinder and you do not have to write one. In targeting mode
the digit keys move the **cursor**, not the player, one tile each, clamped
only to the level's own bounds - so the cursor can be aimed at ground you have
never seen - and `g` then walks the shortest path there, through unknown
grids if it must (`find_path`, `player-path.c:1069`). Measured: 170 to 440
game turns and 17 to 44 tiles **in one ask**, against ten or twenty turns for
`lxg`.

    python3 tools/screen/aim.py screen.txt --to 52,4      # map coordinates
    python3 tools/screen/aim.py screen.txt --to '>'       # the glyph, if drawn
    python3 tools/screen/aim.py screen.txt --far 8        # 40 tiles north

It prints the key string and nothing else happens: you send it, the game
walks. Three rules, each of which cost a run asks:

- **send it alone in its ask.** `g` leaves targeting mode and the next key
  cancels the walk, so two aims in one answer are one walk and some noise;
- **aim long.** 30 to 70 tiles. Aim short and the destination lands inside a
  wall, and then nothing happens at all - no movement, no message;
- **`x` is the slow version.** `*xg` snaps the cursor to the nearest
  unexplored tile, which is usually next to you.
"""
import sys

from screen import KEYPAD, MAP_H, MAP_W, load

LEVEL_W, LEVEL_H = 198, 66          # constants.txt: the level, not the panel


def keys_to(dx, dy):
    """The digit string that moves the cursor dx east and dy south."""
    out = []
    while dx or dy:
        step_x = (1 if dx > 0 else -1) if dx else 0
        step_y = (1 if dy > 0 else -1) if dy else 0
        for key, (kx, ky) in KEYPAD.items():
            if (kx, ky) == (step_x, step_y):
                out.append(key)
                break
        dx -= step_x
        dy -= step_y
    return ''.join(out)


def aim(dx, dy, mode='*'):
    """The whole answer: into targeting mode, move the cursor, walk."""
    return f'{mode}{keys_to(dx, dy)}g'


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 0
    s = load(argv[0])
    if s.overlay:
        print(f'! {s.overlay}: escape the menu first; this screen has no map.')
        return 1
    me = s.me
    if not me:
        print('! no `@` on this screen, so there is nothing to aim from.')
        return 1
    if '--to' in argv:
        target = argv[argv.index('--to') + 1]
        if ',' in target:
            x, y = (int(part) for part in target.split(','))
        else:
            drawn = s.find(target)
            if not drawn:
                print(f'! no {target!r} is drawn on this screen. The game can '
                      f'only walk to what it knows: explore first.')
                return 1
            x, y = min(drawn, key=lambda t: max(abs(t[0] - me[0]),
                                                abs(t[1] - me[1])))
        dx, dy = x - me[0], y - me[1]
        tiles = max(abs(dx), abs(dy))
        print(f'target {x},{y}  = {tiles} tiles from @ at {me[0]},{me[1]}')
        print(f'answer: {aim(dx, dy)}')
        if tiles < 10:
            print(f'(only {tiles} tiles: short aims land in walls and do '
                  f'nothing at all. For a step or two, send the digits '
                  f'themselves: {keys_to(dx, dy)})')
        if target == '>':
            print("(a known staircase has its own two keys: `l>g`, then `> ` "
                  "to take it - the trailing space clears the -more-)")
        return 0
    if '--far' in argv:
        key = argv[argv.index('--far') + 1]
        if key not in KEYPAD or key == '5':
            print(f'! --far takes a direction digit, not {key!r}')
            return 1
        dx, dy = KEYPAD[key]
        # As far as the panel allows, which is the most the screen can justify.
        reach = MAP_W - 1 if dx else MAP_H - 1
        print(f'answer: {aim(dx * reach, dy * reach)}')
        print(f'(the cursor is clamped to the level, {LEVEL_W}x{LEVEL_H}, not '
              f'to the panel, so a longer aim is legal - and a level is about '
              f'three screens each way)')
        return 0
    print('say where: --to X,Y, --to <glyph>, or --far <digit>')
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
