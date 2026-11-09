"""The pinned game's data files, parsed for real.

`lib/gamedata/*.txt` is a sequence of entries. An entry starts at a line whose
key is the file's entry key (`name:` for most files, `store:` for store.txt)
and runs to the next one; every other line is `key:value`, and a key may
repeat (`effect:`, `blow:`, `spell:`). Comments and blank lines are skipped.

This reads the files and nothing else: it knows no claim, no page and no pin
beyond where the clone is.
"""
import functools
import re
import subprocess
from pathlib import Path

from borg_runner import pins

ANGBAND = pins.clone('angband')
STRATEGY = pins.clone('strategy-manual')
GAMEDATA = ANGBAND / 'lib' / 'gamedata'

ENTRY_KEY = {'store.txt': 'store'}


class Entry:
    """One entry: `name`, the file it came from and its fields in order."""

    def __init__(self, file, key, value, line):
        self.file = file
        self.key = key
        self.value = value
        self.line = line
        self.fields = []            # (key, value, line number), in file order

    def all(self, key):
        return [value for k, value, _ in self.fields if k == key]

    def first(self, key, default=None):
        for k, value, _ in self.fields:
            if k == key:
                return value
        return default

    def has(self, key):
        return any(k == key for k, _, _ in self.fields)

    def flags(self):
        found = set()
        for value in self.all('flags'):
            found.update(part.strip() for part in value.split('|'))
        return found

    def __repr__(self):
        return f'<{self.file} {self.key}:{self.value} line {self.line}>'


def parse(path, entry_key=None):
    """The entries of one gamedata file, and the set of keys it uses."""
    path = Path(path)
    entry_key = entry_key or ENTRY_KEY.get(path.name, 'name')
    entries, keys, current = [], set(), None
    for number, raw in enumerate(path.read_text(errors='replace').splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        key, _, value = raw.partition(':')
        keys.add(key)
        if key == entry_key:
            current = Entry(path.name, key, value, number)
            entries.append(current)
        elif current is not None:
            current.fields.append((key, value, number))
    return entries, keys


_cache = {}


def load(file):
    """`(entries, keys)` of `lib/gamedata/<file>`, parsed once."""
    if file not in _cache:
        _cache[file] = parse(GAMEDATA / file)
    return _cache[file]


def object_name(raw):
    """`& Flask~ of oil` -> `Flask of oil`: object.txt marks articles and plurals."""
    return re.sub(r'\s+', ' ', raw.replace('&', '').replace('~', '')).strip()


def objects():
    """Every object kind, with `.name` (marks removed) and `.type`."""
    entries, _ = load('object.txt')
    for entry in entries:
        entry.name = object_name(entry.value)
        entry.type = entry.first('type')
    return entries


def find_objects(name, types=None):
    wanted = name.lower()
    return [o for o in objects()
            if o.name.lower() == wanted and (types is None or o.type in types)]


def by_name(file):
    """Entries of `file` keyed by lower-cased name (the first one wins)."""
    table = {}
    for entry in load(file)[0]:
        table.setdefault(entry.value.split(':')[0].lower(), entry)
    return table


def dice_max(text):
    """`2d8` -> 16; `1d4` -> 4. None when it is not plain dice."""
    match = re.fullmatch(r'(\d+)d(\d+)', text.strip())
    return int(match[1]) * int(match[2]) if match else None


# -- source and the strategy manual ---------------------------------------

def read_source(relative):
    """`src/x.c` (or `docs/x.rst`) under the game clone; None if absent."""
    path = ANGBAND / relative
    return path.read_text(errors='replace') if path.is_file() else None


@functools.lru_cache(maxsize=None)
def strategy_chapter_files():
    """`{chapter number: file name}` of the strategy manual at its pin."""
    commit = pins.commit('strategy-manual')
    listing = subprocess.run(
        ['git', '-C', str(STRATEGY), 'ls-tree', '--name-only', commit,
         'docs/c-manual/'], capture_output=True, text=True, check=True).stdout
    chapters = {}
    for line in listing.split():
        name = line.rsplit('/', 1)[-1]
        match = re.match(r'(\d\d)-.*\.md$', name)
        if match:
            chapters[int(match[1])] = name
    return chapters


@functools.lru_cache(maxsize=None)
def read_chapter(number):
    """Chapter `number` as it is at the pinned commit (not the working tree)."""
    files = strategy_chapter_files()
    if number not in files:
        return None
    commit = pins.commit('strategy-manual')
    return subprocess.run(
        ['git', '-C', str(STRATEGY), 'cat-file', '-p',
         f'{commit}:docs/c-manual/{files[number]}'],
        capture_output=True, text=True, check=True).stdout


def clones_at_their_pins():
    """Problems with the clones, as strings; empty when both are at the pin."""
    problems = []
    for name, path in (('angband', ANGBAND), ('strategy-manual', STRATEGY)):
        if not (path / '.git').exists():
            problems.append(f'vendor/{name} is not cloned (scripts/setup.sh)')
            continue
        head = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()
        if head != pins.commit(name):
            problems.append(f'vendor/{name} is at {head[:12]}, pins.json says '
                            f'{pins.commit(name)[:12]}')
    return problems
