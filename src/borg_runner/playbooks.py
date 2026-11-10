"""What one model family has learned, kept for its own next session.

`manuals/INSTRUCTIONS.md` is the repository's memory: the manuals distilled,
with what runs measured folded in as OBSERVED lines and the evidence behind
them in `knowledge/LEARNED.md`. Nothing in it belongs to anybody. A playbook is
the other thing - one family's own account of playing this game, written for
the next session of the same model: what it measured, what it got wrong, and
the judgement it would apply again. The two are not interchangeable. A line in
INSTRUCTIONS has to hold for any player; a line in a playbook may be "this is
how I keep losing track of my inventory", which is true of one player and
useless as a general claim.

    agents/<family>/COMMON.md     what any run of that family should know
    agents/<family>/<CLASS>.md    the part that is only true of one class

`<family>` names a model family, not a provider and not a version - `minimax`,
not `minimax/MiniMax-M2.7` - because the point is continuity between sessions
of the same model, which a version bump does not break. `<CLASS>` is one of the
game's own classes, spelled in capitals: `DRUID.md`, `WARRIOR.md`. A class file
is written only once there is enough to say; a family with one life of one
character has a COMMON.md and nothing else.

Who writes which: **a family writes its own and only its own.** Reading another
family's playbook is allowed and worth saying in the first note - knowledge is
not private here - but editing it would put words in another player's mouth,
and the file says in its own first lines whose experience it is.
"""
import re
from pathlib import Path

from . import pins

AGENTS = pins.ROOT / 'agents'
COMMON = 'COMMON.md'


def slug(name):
    """A family name as a directory name: `MiniMax` and `minimax` are one."""
    return re.sub(r'[^a-z0-9._-]+', '-', str(name).strip().lower()).strip('-')


def directory(family, where=None):
    return (Path(where) if where else AGENTS) / slug(family)


def classes():
    """The game's own class names, or None when the clone is not there.

    Taken from `class.txt` rather than listed here: a list of the nine classes
    written into this file is a second source of truth that nothing checks.
    """
    try:
        from . import gamedata
        return [entry.value for entry in gamedata.load('class.txt')[0]]
    except Exception:
        return None


def class_file(character_class):
    return f'{slug(character_class).upper().replace("-", "_")}.md'


def paths(family, character_class=None, where=None):
    """The files this run should read, in the order it should read them."""
    home = directory(family, where)
    wanted = [(home / COMMON, 'everything this family has learned')]
    if character_class:
        wanted.append((home / class_file(character_class),
                       f'the part that is only true of a {character_class}'))
    return [{'path': path, 'exists': path.exists(), 'what': what,
             'lines': (len(path.read_text().splitlines()) if path.exists() else 0)}
            for path, what in wanted]


def files(family, where=None):
    home = directory(family, where)
    return sorted(home.glob('*.md')) if home.is_dir() else []


def families(where=None):
    """Every family with a playbook, and what it keeps."""
    home = Path(where) if where else AGENTS
    found = []
    for directory_path in sorted(p for p in home.glob('*') if p.is_dir()):
        kept = sorted(directory_path.glob('*.md'))
        found.append({
            'family': directory_path.name,
            'common': (directory_path / COMMON).exists(),
            'classes': [p.stem.title() for p in kept if p.name != COMMON],
            'lines': sum(len(p.read_text().splitlines()) for p in kept),
        })
    return found


def touched_since(family, when, where=None):
    """Whether this family's playbook was written to after a moment.

    How `archive` tells a run that consolidated from one that only read. It is
    a file time, so it answers "was this file written during the run", not
    "was anything worth keeping added" - which no tool can answer.
    """
    return [path.name for path in files(family, where)
            if path.stat().st_mtime > when]


SKELETON = """# COMMON - what {family} has learned about playing Angband

*Written by the player of `{run}`. This file is for the next session of
{family}, not a general manual: `manuals/INSTRUCTIONS.md` and
`knowledge/LEARNED.md` are that. What belongs here is what is **mine** - what I
measured, what I got wrong, and the judgement I would apply again. Where it
contradicts the manual, it is because I measured it, and it says so.*

*Name the runs every claim came from. A playbook nobody can trace back to a
game is a style guide.*

---

## What I would tell myself before the first keypress

## What cost me the most asks

## What I got wrong

## What I would try next
"""


def start(family, run='this run', where=None):
    """Create a family's COMMON.md if it has none, and return the path."""
    home = directory(family, where)
    home.mkdir(parents=True, exist_ok=True)
    page = home / COMMON
    if not page.exists():
        page.write_text(SKELETON.format(family=slug(family), run=run))
    return page


def check(where=None, known_runs=None):
    """What is wrong with the playbooks, as a list of complaints.

    The layout is checkable and the content is not, so this checks the layout
    and one thing about the content: that a playbook names a run it came from.
    A page that cites no game cannot be weighed against the record, and this
    repository's whole claim is that everything in it can be.
    """
    home = Path(where) if where else AGENTS
    if not home.is_dir():
        return []
    complaints = []
    valid = classes()
    allowed = {class_file(name) for name in valid} if valid else None
    runs = known_runs
    if runs is None:
        from . import run as run_module
        runs = sorted(p.parent.name for p in run_module.RECORDS.glob('*/record.json'))
    for directory_path in sorted(p for p in home.glob('*') if p.is_dir()):
        family = directory_path.name
        kept = sorted(directory_path.glob('*.md'))
        if not (directory_path / COMMON).exists():
            complaints.append(f'agents/{family}/ has no {COMMON}: a family keeps '
                              f'its general notes there and a class file beside it')
        for page in kept:
            if page.name != COMMON and allowed is not None and page.name not in allowed:
                complaints.append(
                    f'agents/{family}/{page.name} is named after no class the game '
                    f'has; a class file is <CLASS>.md, e.g. {class_file("Druid")}')
            text = page.read_text()
            if not text.strip():
                complaints.append(f'agents/{family}/{page.name} is empty')
                continue
            if runs and not any(name in text for name in runs):
                complaints.append(
                    f'agents/{family}/{page.name} names no run it came from: '
                    f'a playbook that cites no game cannot be checked against '
                    f'the record')
        for stray in sorted(p for p in directory_path.glob('*') if p.is_file()
                            and p.suffix != '.md'):
            complaints.append(f'agents/{family}/{stray.name} is not a .md page; '
                              f'a playbook is prose, and tools belong with their run')
    return complaints
