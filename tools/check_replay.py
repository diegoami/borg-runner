"""Compare the screens a replay produced with the ones the archived page holds.

The archive keeps the record, the decisions and the keys, but not the
screens: `replay` reproduces them from the seed and the keys (D6). So the
screens a replay produces are the evidence that the page being rebuilt is the
page that was archived - and the archived page still holds the screens it
was built from, in its own frames.

    python tools/check_replay.py [run ...]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from borg_runner import replay as replay_module      # noqa: E402

RECORDS = Path('records')
RUNS = Path('runs')
# The build id is in the title bar of the splash and of the help screen,
# and it names the commit this repository was at when the binary was built.
# A page built then and a replay built now differ there and nowhere else -
# unless the build id is pinned, which this repository's pin does not
# achieve on Unix, where the game overwrites it with `git describe`.
BUILD = re.compile(r'-g[0-9a-f]{7,}(?:-dirty)?|borg-runner-[0-9a-f]+')


def frames_of(page):
    """The frames a page holds.

    The frames are one line of JSON, and the reasons in them are a model's
    words - so the brackets are counted outside the strings, not inside.
    """
    for line in page.read_text().splitlines():
        stripped = line.strip()
        if not stripped.startswith('var frames = '):
            continue
        raw = stripped[len('var frames = '):]
        depth, end, in_string, escaped = 0, 0, False, False
        for index, char in enumerate(raw):
            if in_string:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        return json.loads(raw[:end])
    return []


def archived_screens(name):
    """The screens the archived page holds, ask by ask."""
    return {frame['ask']: frame['screen']
            for frame in frames_of(RECORDS / name / 'report.html')}


def comparable(screen):
    """The screen as two builds of the same game would write it.

    The clock of the tombstone is not game state and can never replay, and
    the build id names the commit the binary was built from.
    """
    return BUILD.sub('the build', replay_module.comparable(screen))


def check(name):
    """What the replay and the archived page disagree about."""
    was = archived_screens(name)
    live = RUNS / name
    if not was:
        return [f'{name}: the archived page holds no frames']
    if not (live / 'ask').is_dir():
        return [f'{name}: no replay to compare with']
    problems = []
    for ask, screen in was.items():
        replayed = live / 'ask' / f'screen-{ask}.txt'
        if not replayed.exists():
            problems.append(f'{name}: the replay has no screen for ask {ask}')
            continue
        now = replayed.read_text()
        if comparable(now) != comparable(screen):
            problems.append(f'{name}: ask {ask} differs from the archived page')
    return problems


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    names = argv or sorted(path.parent.name
                           for path in RECORDS.glob('*/record.json'))
    problems = []
    for name in names:
        problems += check(name)
    for problem in problems:
        print(problem)
    print(f'{len(names)} runs checked, {len(problems)} differences')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
