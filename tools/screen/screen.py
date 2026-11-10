#!/usr/bin/env python3
"""Read one Angband screen dump: the panels, the sidebar, the status line.

Written for the shared library, 2026-11-10, out of what the runs measured
about the screen (`manuals/INSTRUCTIONS.md`, "Keys as the game receives them",
and `ACCUMULATED_KNOWLEDGE.md` section 3).

It parses only the text the game printed. It holds no opinion about how to
play, and it never decides anything: it turns 24 lines of text into the same
few things every tool here needs.

    from screen import load
    s = load('runs/mine/ask/screen-42.txt')
    s.message            # the top line: usually why your last key did nothing
    s.status             # the bottom line: LF, Light, Fed, conditions, terrain
    s.me                 # the '@' as (x, y) in map coordinates, or None
    s.at(3, 4)           # one tile
    s.find('>')          # every down staircase *drawn* on this screen
    s.sidebar['HP']      # ('25', '33')
    s.overlay            # a menu is covering the map, so coordinates are junk

Geometry, from `ui-term.h` and checked against real dumps: the screen is
80x24; row 0 is the message line, row 23 the status line, and the map panel is
rows 1-22 by columns 13-79, which is 66x22 tiles at 1:1. Map coordinates in
this library are panel-relative: x = column - 13, y = row - 1.

Two things the runs learned the hard way, which this module exposes rather
than hides:

- **a menu or a character sheet covers the map**, and a map read under one is
  nonsense. `overlay` says so, and every tool here refuses to route on it;
- **the tile under `@` is not drawn.** You cannot see the staircase you are
  standing on; only the status line names it. `s.terrain` is that field.
"""
import re
import sys

WIDTH, HEIGHT = 80, 24
MAP_COL, MAP_ROW = 13, 1
MAP_W, MAP_H = 66, 22

# What the frontend's own printers wrap a screen in, when a player pastes the
# output of `answer` or `wait` instead of the file itself.
HEADER = re.compile(r'^=== ASK \d+')
FOOTER = re.compile(r'^=== (answer|YOUR (NOTEBOOK|MEMORY))')
# A prompt that means the map is not what is on screen.
PROMPTS = ('Inven:', 'Equip:', 'Select Item', 'Command:', 'ESC)',
           'Which direction', 'Throw which item', 'you have nothing')

# The movement keys, as (dx, dy) with **y increasing downward**, which is how
# a screen is indexed and the opposite of how a map is usually imagined. The
# first tool adopted into this library had this table transposed, so every
# route it printed walked the wrong way; it is here once so that it is right
# once.
#
#   7 8 9      up is north, y - 1
#   4 . 6
#   1 2 3      down is south, y + 1
KEYPAD = {'1': (-1, 1), '2': (0, 1), '3': (1, 1),
          '4': (-1, 0), '5': (0, 0), '6': (1, 0),
          '7': (-1, -1), '8': (0, -1), '9': (1, -1)}
# The digit for a step, by the sign of (dx, dy).
STEP = {(dx, dy): key for key, (dx, dy) in KEYPAD.items()}

FLOOR = '.'
RUBBLE = ':'
WALLS = '#%'
DOORS = "+'"
STAIRS = '<>'
STORES = '12345678'


class Screen:
    def __init__(self, rows):
        self.rows = [row.ljust(WIDTH)[:WIDTH] for row in rows]
        while len(self.rows) < HEIGHT:
            self.rows.append(' ' * WIDTH)

    # -- the three lines that are not the map ------------------------------
    @property
    def message(self):
        return self.rows[0].rstrip()

    @property
    def status(self):
        return self.rows[HEIGHT - 1].rstrip()

    @property
    def terrain(self):
        """The last field of the status line: what you are standing on."""
        found = re.search(r'Fed\s+\d+\s*%\s*(?P<what>.*)$', self.status)
        return found.group('what').strip() if found else None

    @property
    def conditions(self):
        """Confused, Afraid, Blind, Poisoned, Slow ... from the status line."""
        known = ('Blind', 'Confused', 'Afraid', 'Poisoned', 'Stun', 'Slow',
                 'Fast', 'Paralyzed!', 'Study', 'Recall', 'Descent', 'Hungry',
                 'Weak', 'Faint', 'Full')
        return [name for name in known if name in self.status]

    @property
    def level_feeling(self):
        """`LF:n-m` as a pair of strings; `?` until you have walked enough."""
        found = re.search(r'LF:(?P<danger>[\d?]+)-(?P<loot>[\d?]+)', self.status)
        return (found.group('danger'), found.group('loot')) if found else None

    @property
    def depth_line(self):
        """The sidebar's own depth, e.g. `50' (L1)` or `Town`."""
        return self.rows[HEIGHT - 2][:MAP_COL].strip() or None

    # -- the sidebar -------------------------------------------------------
    @property
    def sidebar(self):
        """The left thirteen columns, as the fields the game prints there."""
        found = {}
        for row in self.rows[1:HEIGHT - 1]:
            text = row[:MAP_COL].strip()
            pair = re.match(r'^(?P<name>[A-Za-z][A-Za-z ]*?):?\s+'
                            r'(?P<value>-?\d+)\s*/?\s*(?P<of>-?\d+)?$', text)
            if pair:
                name = pair.group('name').strip()
                found[name] = ((pair.group('value'), pair.group('of'))
                               if pair.group('of') else pair.group('value'))
            elif text and ':' not in text and ' ' not in text:
                found.setdefault('lines', []).append(text)
        return found

    # -- the map -----------------------------------------------------------
    @property
    def overlay(self):
        """Whether something is drawn over the map panel.

        A menu, an inventory, a character sheet or an item prompt: the glyphs
        in the panel are then that menu's text, and any coordinate read off
        them is meaningless.
        """
        if any(hint in self.message for hint in PROMPTS):
            return self.message.strip()
        # A character sheet fills the sidebar columns with prose instead of
        # the handful of numeric fields.
        if 'Self  RB  CB  EB' in ''.join(self.rows[:4]):
            return 'character sheet'
        return None

    @property
    def panel(self):
        """The map as 22 strings of 66 characters, panel-relative."""
        return [row[MAP_COL:MAP_COL + MAP_W] for row in
                self.rows[MAP_ROW:MAP_ROW + MAP_H]]

    def at(self, x, y):
        if not (0 <= x < MAP_W and 0 <= y < MAP_H):
            return None
        return self.panel[y][x]

    def find(self, glyph):
        """Every tile drawn with this glyph, as (x, y) map coordinates."""
        return [(x, y) for y, row in enumerate(self.panel)
                for x, cell in enumerate(row) if cell == glyph]

    @property
    def me(self):
        found = self.find('@')
        return found[0] if found else None

    def glyphs(self, skip=' .#%'):
        """Everything drawn that is not floor, wall or nothing.

        Grouped by glyph, each with its tiles and the offset from `@`, which
        is the form the game's own `[` list and look descriptions use: south
        and east are positive.
        """
        me = self.me
        found = {}
        for y, row in enumerate(self.panel):
            for x, cell in enumerate(row):
                if cell in skip or cell == '@':
                    continue
                offset = (x - me[0], y - me[1]) if me else None
                found.setdefault(cell, []).append({'at': (x, y),
                                                   'offset': offset})
        return found


def load(where):
    """A Screen from a file path, an open file, or the text itself."""
    if hasattr(where, 'read'):
        text = where.read()
    elif '\n' in str(where):
        text = str(where)
    else:
        with open(where) as handle:
            text = handle.read()
    rows = []
    for line in text.split('\n'):
        if HEADER.match(line):            # the printers' own wrapper
            rows = []
            continue
        if FOOTER.match(line):
            break
        rows.append(line.rstrip('\n'))
    # A pasted screen may carry a trailing blank line or two.
    while rows and not rows[-1].strip() and len(rows) > HEIGHT:
        rows.pop()
    return Screen(rows)


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 0
    s = load(argv[0])
    print(f'message : {s.message or "(none)"}')
    print(f'status  : {s.status}')
    print(f'depth   : {s.depth_line}   terrain: {s.terrain}')
    print(f'feeling : {s.level_feeling}   conditions: '
          f'{", ".join(s.conditions) or "none"}')
    print(f'sidebar : {s.sidebar}')
    print(f'@       : {s.me}')
    if s.overlay:
        print(f'overlay : {s.overlay} - the map is covered, coordinates are junk')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
