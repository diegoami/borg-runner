"""The handover is for the next session, so it must not go stale silently.

`docs/HANDOVER.md` is the first thing a fresh session reads after AGENTS.md.
What can be checked mechanically is checked here: that it is linked from the
two entry points, that every repository path it names exists, and that every
`borg_runner` command it tells the next session to run is a real command. What
cannot be checked is whether what it says is still true - that is the job of
whoever finishes the work it describes.
"""
import re
import subprocess
import sys

from borg_runner import pins

HANDOVER = pins.ROOT / 'docs' / 'HANDOVER.md'
# Paths that are made, not committed: the clones, the build, the run directories.
MADE_LATER = ('vendor/', 'build/', 'runs/', 'records/<run>', 'knowledge/<run>',
              'agents/<family>', '<CLASS>', '_2')
# The pinned game's own data files, which live in the git-ignored clone.
GAME_DATA = ('class.txt', 'monster.txt', 'p_race.txt', 'object.txt', 'store.txt',
             'trap.txt', 'constants.txt', 'dungeon_profile.txt')


def text():
    return HANDOVER.read_text()


def test_the_handover_exists_and_is_not_a_stub():
    assert HANDOVER.is_file(), 'docs/HANDOVER.md is how a fresh session starts'
    assert len(text().splitlines()) > 60, 'a handover that fits on a screen is a note'


def test_both_entry_points_link_to_it():
    for name in ('AGENTS.md', 'README.md'):
        assert 'docs/HANDOVER.md' in (pins.ROOT / name).read_text(), \
            f'{name} does not point at the handover'


def test_every_repository_path_it_names_exists():
    missing = []
    for token in set(re.findall(r'`([\w./-]+\.(?:md|txt|py|json|yaml|c|html))`', text())):
        if token in GAME_DATA or any(part in token for part in MADE_LATER):
            continue
        if not (pins.ROOT / token).exists():
            missing.append(token)
    assert not missing, f'the handover names paths that do not exist: {missing}'


def test_every_command_it_shows_is_a_real_command():
    shown = set(re.findall(r'borg_runner (\w[\w-]*)', text()))
    listed = subprocess.run([sys.executable, '-m', 'borg_runner', '--help'],
                            capture_output=True, text=True, cwd=pins.ROOT)
    available = set(re.findall(r'[\w-]+', listed.stdout.split('{', 1)[-1].split('}', 1)[0]))
    unknown = {name for name in shown if name not in available}
    assert not unknown, f'the handover names commands that do not exist: {unknown}'
