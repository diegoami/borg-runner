"""The shared screen tools: what runs wrote, kept so the next run can use it.

A run may write code - a screen parser, a router, anything that reads the
screen - and one of the first did, a 143-line breadth-first search, and the
next run of the same character wrote the same thing again. That is the waste
this module exists to stop: a tool that was worth writing once is worth
keeping, and `tools/screen/` is where it is kept.

Two directories, with different jobs:

- `runs/<run>/tools/` is where a run writes. It is archived with the run
  (`records/<run>/tools/`), because a run played with a pathfinder it wrote is
  measuring its code as well as itself, and a reader has to be able to see it.
- `tools/screen/` is the **shared** library: tools any run may use, each one
  naming the run it came from. `adopt()` moves a run's tool there.

The rule that keeps the library honest is the same one the corpus taught:
**check the game first.** The game's own walk covers 17 to 44 tiles in one ask
and pathfinds through unseen ground; a tool that reimplements it costs a run
the chance to find that out. So the library's tools parse, describe and
convert - the one that routes says in its own header when not to use it.

A shared tool may not import this package: a player runs it as
`python3 tools/screen/look.py <screen>`, and a tool that needed the frontend
installed would be a tool that stops working in a bare checkout.
"""
import ast
import datetime
import re
import shutil
from pathlib import Path

from . import pins, run as run_module

SHARED = pins.ROOT / 'tools' / 'screen'
PROVENANCE = re.compile(r'(?:Adopted into the shared library from '
                        r'`(?P<run>[^`]+)`|Written for the shared library)',
                        re.MULTILINE)


def summary(path):
    """A tool's own first line, which is what it is for."""
    try:
        tree = ast.parse(Path(path).read_text())
    except SyntaxError as problem:
        return f'(does not parse: {problem})'
    doc = ast.get_docstring(tree) or ''
    return doc.strip().splitlines()[0] if doc else ''


def shared(where=None):
    """The library, as rows."""
    where = Path(where) if where else SHARED
    if not where.is_dir():
        return []
    found = []
    for path in sorted(where.glob('*.py')):
        text = path.read_text()
        says = PROVENANCE.search(text)
        found.append({
            'name': path.name,
            'path': path,
            'lines': len(text.splitlines()),
            'summary': summary(path),
            'from_run': says.group('run') if says and says.group('run') else None,
            'written_here': bool(says and not says.group('run')),
        })
    return found


def by_runs(where=None):
    """Tools runs wrote, which is what `adopt` draws from.

    Both the archive and the working directories, because the moment to adopt
    a tool is usually while the run that wrote it is still playing - and a run
    archives at the end, not when it writes the file.
    """
    places = ([Path(where)] if where
              else [run_module.RECORDS, pins.ROOT / 'runs'])
    found, seen = [], set()
    for place in places:
        if not place.is_dir():
            continue
        for directory in sorted(place.glob('*/tools')):
            for path in sorted(directory.rglob('*')):
                if not path.is_file():
                    continue
                run = directory.parent.name
                if (run, path.name) in seen:
                    continue
                seen.add((run, path.name))
                found.append({'run': run, 'path': path, 'name': path.name,
                              'archived': place == run_module.RECORDS,
                              'lines': len(path.read_text(errors='replace')
                                           .splitlines())})
    return sorted(found, key=lambda row: (row['run'], row['name']))


HEADER = """# Adopted into the shared library from `{run}`'s own tools/{name},
# {when}. The run's copy stays in records/{run}/tools/{name} as it played it;
# this one may be corrected, and the correction belongs in this header.
"""


def adopt(path, from_run, into=None, name=None):
    """Copy a run's tool into the shared library, saying where it came from.

    The run's own copy is left alone: it is part of that run's record, and a
    reader comparing the two sees what adopting changed.
    """
    path = Path(path)
    into = Path(into) if into else SHARED
    into.mkdir(parents=True, exist_ok=True)
    target = into / (name or path.name)
    text = path.read_text()
    note = HEADER.format(run=from_run, name=path.name,
                         when=datetime.date.today().isoformat())
    if text.startswith('#!'):
        first, rest = text.split('\n', 1)
        text = f'{first}\n{note}{rest}'
    else:
        text = note + text
    target.write_text(text)
    return target


def check(where=None):
    """What is wrong with the library. Empty means a player can rely on it.

    Three things, each of which has bitten: a tool that does not parse, a tool
    that does not say where it came from, and a tool that imports this package
    and so only works where the frontend is installed.
    """
    where = Path(where) if where else SHARED
    if not where.is_dir():
        return [f'{where} does not exist']
    problems = []
    for path in sorted(where.glob('*.py')):
        text = path.read_text()
        try:
            tree = ast.parse(text)
        except SyntaxError as problem:
            problems.append(f'{path.name}: does not parse ({problem})')
            continue
        if not ast.get_docstring(tree):
            problems.append(f'{path.name}: no docstring, so nothing says what '
                            f'it is for or how to run it')
        if not PROVENANCE.search(text):
            problems.append(
                f'{path.name}: does not say where it came from. A shared tool '
                f'says "Adopted into the shared library from `<run>`" or '
                f'"Written for the shared library"')
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or '']
            if any(name.split('.')[0] == 'borg_runner' for name in names):
                problems.append(f'{path.name}: imports borg_runner; a shared '
                                f'tool must run in a bare checkout')
    return problems
