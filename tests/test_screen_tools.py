"""The shared screen tools, and the rule that keeps them usable.

They are plain scripts a player runs in a bare checkout, so these tests run
them the way a player does - by path, with a real screen dump from a real run
(`tests/screen-dungeon.txt`, `minimaxflash-1.3` ask 596: a confused druid in a
doorway on depth 1, with an up staircase, seven doors and no `>`).
"""
import subprocess
import sys
from pathlib import Path

import pytest

from borg_runner import pins, tools

SCREEN = Path(__file__).parent / 'screen-dungeon.txt'
LIBRARY = pins.ROOT / 'tools' / 'screen'


def run(tool, *args):
    """A tool exactly as a player runs it: python3 tools/screen/<tool>."""
    done = subprocess.run([sys.executable, str(LIBRARY / tool), *args],
                          capture_output=True, text=True, cwd=pins.ROOT)
    assert done.returncode in (0, 1), done.stderr
    return done.stdout


def test_the_library_is_sound():
    assert tools.check() == []


def test_every_tool_says_where_it_came_from():
    for row in tools.shared():
        assert row['from_run'] or row['written_here'], row['name']
        assert row['summary'], f'{row["name"]} does not say what it is for'


def test_the_reader_finds_the_player_the_sidebar_and_the_status_line():
    sys.path.insert(0, str(LIBRARY))
    try:
        import screen as screen_module
        s = screen_module.load(SCREEN)
    finally:
        sys.path.remove(str(LIBRARY))
    assert s.me == (40, 13)
    assert s.sidebar['HP'] == ('25', '33') and s.sidebar['LEVEL'] == '4'
    assert s.conditions == ['Confused'] and s.terrain == 'Broken door'
    assert s.level_feeling == ('1', '?')
    assert s.find('<') == [(45, 21)] and s.find('>') == []
    # The glyph under the player is never drawn, which is the whole reason the
    # status line has to be read.
    assert s.at(*s.me) == '@'


def test_the_keypad_table_is_not_transposed():
    """The adopted tool arrived with this wrong, and every route walked wrong."""
    sys.path.insert(0, str(LIBRARY))
    try:
        import screen as screen_module
    finally:
        sys.path.remove(str(LIBRARY))
    # y increases downward: 2 is south, 8 north, 4 west, 6 east, 1 south-west.
    assert screen_module.KEYPAD['2'] == (0, 1)
    assert screen_module.KEYPAD['8'] == (0, -1)
    assert screen_module.KEYPAD['4'] == (-1, 0)
    assert screen_module.KEYPAD['6'] == (1, 0)
    assert screen_module.KEYPAD['1'] == (-1, 1)
    assert screen_module.KEYPAD['9'] == (1, -1)


def test_look_lists_what_is_drawn_with_offsets_in_the_games_form():
    out = run('look.py', str(SCREEN))
    assert 'up staircase' in out and '8 S, 5 E' in out
    assert 'Broken door' in out and 'Confused' in out
    assert 'no down staircase is drawn here' in out


def test_aim_prints_keys_that_make_the_game_walk():
    out = run('aim.py', str(SCREEN), '--to', '45,21')
    assert 'answer: *' in out and out.strip().endswith(')')
    keys = [line for line in out.splitlines() if line.startswith('answer:')][0]
    assert keys.endswith('g'), 'the walk is what g does'
    # @ is at 40,13 and the target 5 east, 8 south: south-east then south.
    assert keys == 'answer: *33333222g'


def test_aim_refuses_a_glyph_that_is_not_on_the_screen():
    out = run('aim.py', str(SCREEN), '--to', '>')
    assert 'no' in out and 'drawn' in out


def test_aim_far_aims_past_the_panel():
    out = run('aim.py', str(SCREEN), '--far', '8')
    assert '*8' in out and out.count('8') > 10


def test_map_prints_the_panel_and_refuses_an_overlay(tmp_path):
    out = run('map.py', str(SCREEN))
    assert '@ at (40, 13)' in out
    covered = tmp_path / 'menu.txt'
    covered.write_text('Select Item: (Inven: a-f, / for Equip, ESC)\n'
                       + '\n' * 23)
    out = run('map.py', str(covered))
    assert 'covered' in out, 'a menu over the map must not be routed on'


def test_diff_says_when_nothing_changed(tmp_path):
    same = tmp_path / 'same.txt'
    same.write_text(SCREEN.read_text())
    out = run('diff.py', str(SCREEN), str(same))
    assert 'nothing changed at all' in out


def test_diff_finds_what_moved(tmp_path):
    rows = SCREEN.read_text().split('\n')
    moved = tmp_path / 'moved.txt'
    moved.write_text('\n'.join(row.replace('@', 'X') for row in rows))
    out = run('diff.py', str(SCREEN), str(moved))
    assert 'tiles differ' in out


LEVEL_MAP = Path(__file__).parent / 'screen-level-map.txt'


def test_explore_reads_the_whole_level_view_and_finds_the_staircase():
    """`M` is one ask and draws the remembered level; this is the town's."""
    out = run('explore.py', str(LEVEL_MAP))
    assert 'DOWN staircase in the box' in out
    assert '`l>g` walks to it in one ask' in out, \
        'with a staircase remembered, the game walks there; no tool should'
    assert 'stores remembered: 1 at' in out
    assert '3x3 level tiles per box tile' in out, 'the box is scaled'


def test_explore_on_ordinary_screens_says_where_the_dark_is():
    out = run('explore.py', str(SCREEN))
    assert 'border the dark' in out
    answer = [line for line in out.splitlines() if line.startswith('answer:')]
    assert answer and answer[0].endswith('g'), 'the aim is the game walking'
    assert 'press `M`' in out, 'the better route is the whole-level view'


def test_explore_does_not_stitch_a_scrolled_view(tmp_path):
    """It tried, and two stretches of corridor produced duplicate rooms."""
    rows = SCREEN.read_text().split('\n')
    shifted = tmp_path / 'scrolled.txt'
    shifted.write_text('\n'.join(
        row[:13] + row[13:][30:] + ' ' * 30 if len(row) > 43 else row
        for row in rows))
    out = run('explore.py', str(SCREEN), str(shifted))
    assert 'the view moved 1 times' in out


def test_adopting_a_runs_tool_records_where_it_came_from(tmp_path):
    written = tmp_path / 'mine.py'
    written.write_text('#!/usr/bin/env python3\n"""Mine."""\nprint(1)\n')
    into = tmp_path / 'library'
    target = tools.adopt(written, 'some-run', into=into)
    text = target.read_text()
    assert text.startswith('#!/usr/bin/env python3\n# Adopted into the shared '
                           'library from `some-run`')
    assert 'print(1)' in text
    # And the run's own copy is untouched: it is part of that run's record.
    assert written.read_text().startswith('#!/usr/bin/env python3\n"""Mine."""')
    assert tools.check(into) == []


def test_a_shared_tool_may_not_need_the_frontend(tmp_path):
    (tmp_path / 'bad.py').write_text(
        '"""Written for the shared library."""\nfrom borg_runner import run\n')
    assert any('bare checkout' in problem for problem in tools.check(tmp_path))


def test_a_tool_that_says_nothing_about_itself_is_a_problem(tmp_path):
    (tmp_path / 'quiet.py').write_text('print(1)\n')
    problems = tools.check(tmp_path)
    assert any('no docstring' in p for p in problems)
    assert any('where it came from' in p for p in problems)


PROMPTS = ('PLAYGAME.txt', 'CONTINUEGAME.txt')


@pytest.mark.parametrize('name', PROMPTS)
def test_both_prompts_point_at_the_library_and_at_adopting(name):
    prose = ' '.join((pins.ROOT / name).read_text().split())
    assert 'borg_runner tools' in prose
    assert 'tools/screen' in prose
    assert 'tools --adopt' in prose
