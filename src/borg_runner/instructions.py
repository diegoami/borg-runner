"""Check `manuals/INSTRUCTIONS.md` against the pinned game.

The page labels every factual line with a source. A label is a promise: this
module turns it into a check. It reads the page, finds the claims it can
check (a number that names a gamedata field, a citation that names a file, a
rule id, a quotation), looks each one up in `vendor/` at the pin, and says
what is wrong with a line number, the claimed value and the real one.

Two parts, by design:

* **extractors** read the page. Each one is a small grammar for one kind of
  sentence and says how many claims it must find (`minimum`), so a rewrite
  that stops a grammar from matching fails loudly instead of checking nothing;
* **checks** are inside the extractors: a claim is created with its real
  value already looked up, so a claim is a (line, what, claimed, real) row.

What it does not read is in `tests/test_instructions.py`'s docstring.
"""
import bisect
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from borg_runner import gamedata as gd
from borg_runner import pins

INSTRUCTIONS = pins.ROOT / 'manuals' / 'INSTRUCTIONS.md'

CONSUMABLE_TYPES = ('potion', 'scroll', 'food', 'flask')


@dataclass
class Claim:
    line: int
    kind: str
    what: str
    claimed: Any
    real: Any
    ok: bool
    span: tuple = (0, 0)
    verifiable: bool = True

    def message(self):
        if self.claimed is True:           # a yes/no claim: the page relies on it
            return (f'line {self.line}: {self.what}: the page relies on this, '
                    f'the pinned game says {self.real!r}')
        return (f'line {self.line}: {self.what}: page says {self.claimed!r}, '
                f'pinned game says {self.real!r}')


@dataclass
class Report:
    claims: list = field(default_factory=list)
    problems: list = field(default_factory=list)       # grammar and extractor trouble
    extractors: dict = field(default_factory=dict)     # name -> claims found

    @property
    def checked(self):
        return [c for c in self.claims if c.verifiable]

    @property
    def unverifiable(self):
        return [c for c in self.claims if not c.verifiable]

    @property
    def mismatches(self):
        return [c for c in self.checked if not c.ok]

    def by_kind(self):
        counts = {}
        for claim in self.checked:
            counts[claim.kind] = counts.get(claim.kind, 0) + 1
        return counts

    def failures(self):
        """Every reason the page does not match, as sentences."""
        return ([c.message() for c in self.mismatches] +
                [f'grammar: {p}' for p in self.problems])

    def summary(self):
        lines = [f'{len(self.checked)} claims checked '
                 f'({len(self.mismatches)} mismatched), '
                 f'{len(self.unverifiable)} found but not checkable, '
                 f'{len(self.problems)} grammar problems']
        for kind, count in sorted(self.by_kind().items()):
            lines.append(f'  {kind}: {count}')
        return '\n'.join(lines)


# -- reading the page --------------------------------------------------------

def plain(text):
    """Lower case, no accents, no markdown, one space: for comparing names."""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'[*`]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()


class Ctx:
    """The page, its line numbers and the claims found so far."""

    def __init__(self, text):
        self.text = text
        self.starts = [0] + [m.end() for m in re.finditer('\n', text)]
        self.report = Report()
        self.shortcuts = {}            # `object` -> its path, from the page's own header

    def line(self, pos):
        return bisect.bisect_right(self.starts, pos)

    def emit(self, kind, pos, what, claimed, real, ok=None, end=None,
             verifiable=True):
        ok = (claimed == real) if ok is None else ok
        self.report.claims.append(Claim(
            self.line(pos), kind, what, claimed, real, bool(ok),
            (pos, end if end is not None else pos), verifiable))
        return ok

    def problem(self, text, pos=None):
        where = f'line {self.line(pos)}: ' if pos is not None else ''
        self.report.problems.append(where + text)

    def search(self, pattern, flags=0, name=None, required=True):
        """First match of `pattern`; a missing required anchor is a problem."""
        found = re.search(pattern, self.text, flags)
        if not found and required:
            self.problem(f'the page no longer has {name or pattern!r}: the '
                         f'grammar must be updated with it')
        return found

    def finditer(self, pattern, flags=0):
        return list(re.finditer(pattern, self.text, flags))


EXTRACTORS = []


def extractor(name, minimum):
    def register(fn):
        EXTRACTORS.append((name, minimum, fn))
        return fn
    return register


# -- the game's tables, as the extractors need them --------------------------

def tval_names():
    """`SOFT_ARMOR` -> `soft armor`, from src/list-tvals.h."""
    text = gd.read_source('src/list-tvals.h') or ''
    return {code: name for code, name in re.findall(r'TV\((\w+), "([^"]+)"\)', text)}


def function_tvals(function):
    """The object types a `tval_*` function in src/obj-tval.c lists."""
    source = gd.read_source('src/obj-tval.c') or ''
    body = re.search(rf'{function}\([^)]*\)\s*\{{(.*?)\n\}}', source, re.S)
    if not body:
        return None
    names = tval_names()
    return {names[code] for code in re.findall(r'TV_(\w+)', body.group(1))
            if code in names}


def option_defaults():
    """`{option: default}` from src/list-options.h `OP(name, "desc", type, default)`."""
    text = gd.read_source('src/list-options.h') or ''
    return {name: default for name, default in
            re.findall(r'OP\((\w+),\s*"[^"]*",\s*\w+,\s*(\w+)\)', text)}


def constants():
    """`{'player:start-gold': 600, ...}` from constants.txt."""
    found = {}
    path = gd.GAMEDATA / 'constants.txt'
    for raw in path.read_text().splitlines():
        match = re.match(r'^(\w[\w-]*):([\w-]+):(-?\d+)\s*$', raw)
        if match:
            found[f'{match[1]}:{match[2]}'] = int(match[3])
    return found


def find_object(name, prefer=CONSUMABLE_TYPES, types=None):
    """The object kind a page name means, or None. Names repeat across types
    (a Cure Light Wounds potion and staff), so a type is preferred, not guessed."""
    matches = gd.find_objects(name, types)
    for wanted in prefer:
        for obj in matches:
            if obj.type == wanted:
                return obj
    return matches[0] if len(matches) == 1 else None


def alloc_min(obj):
    """The shallowest depth the object can be generated at (`alloc:`)."""
    alloc = obj.first('alloc')
    match = re.match(r'\d+:(\d+) to (\d+)', alloc or '')
    return int(match[1]) if match else None


def stores():
    """Every store: key, always and normal stock as (type, name)."""
    found = []
    for entry in gd.load('store.txt')[0]:
        always = [(v.split(':', 1) + [''])[:2] for v in entry.all('always')]
        normal = [(v.split(':', 1) + [''])[:2] for v in entry.all('normal')]
        found.append({'key': entry.value, 'always': always, 'normal': normal})
    return found


# -- extractors: numbers that name a gamedata field --------------------------

NAME_ALIASES = {'ration': 'Ration of Food'}


def split_pairs(body):
    """`Hobbit 7; Gnome, Kobold 8` style: [(names, number)], split on `;`."""
    out = []
    for group in body.split(';'):
        match = re.match(r'^\s*(.*?)\s+(\d+)\s*$', group)
        if match:
            out.append(([n.strip() for n in re.split(r'[,/]', match[1]) if n.strip()],
                        int(match[2]), match.start(2)))
    return out


@extractor('race hit dice', minimum=22)
def race_hit_dice(c):
    found = c.search(r'`race` hitdie:\s*(?P<body>[^.]*?)\.\s*Class die:\s*'
                     r'(?P<cls>[^(]*?)\(`class` hitdie\)', name='the race/class hit dice line')
    if not found:
        return
    races = {e.value.lower(): e for e in gd.load('p_race.txt')[0]}
    listed = set()
    for names, number, _ in split_pairs(found['body']):
        for name in names:
            entry = races.get(name.lower())
            real = int(entry.first('hitdie')) if entry else 'no such race in p_race.txt'
            c.emit('race hitdie', found.start('body'), f'{name} hit die', number, real)
            listed.add(name.lower())
    c.emit('race hitdie', found.start('body'), 'races listed (all of p_race.txt)',
           sorted(listed), sorted(races))
    classes = {e.value.lower(): e for e in gd.load('class.txt')[0]}
    listed = set()
    for piece in found['cls'].split(','):
        match = re.match(r'^\s*([\w/]+)\s+(\d+)\s*$', piece)
        if not match:
            c.problem(f'cannot read class die {piece!r}', found.start('cls'))
            continue
        for name in match[1].split('/'):
            entry = classes.get(name.lower())
            real = int(entry.first('hitdie')) if entry else 'no such class in class.txt'
            c.emit('class hitdie', found.start('cls'), f'{name} hit die',
                   int(match[2]), real)
            listed.add(name.lower())
    c.emit('class hitdie', found.start('cls'), 'classes listed (all of class.txt)',
           sorted(listed), sorted(classes))


@extractor('race experience', minimum=4)
def race_experience(c):
    found = c.search(r'mod = race exp, ([^)]*)\)', name='the race exp list')
    if not found:
        return
    races = {e.value.lower(): e for e in gd.load('p_race.txt')[0]}
    for piece in found[1].split(','):
        match = re.match(r'^\s*([\w-]+)\s+(\d+)\s*$', piece)
        entry = races.get(match[1].lower()) if match else None
        real = int(entry.first('exp')) if entry else 'no such race'
        c.emit('race exp', found.start(1), f'{match[1] if match else piece} exp',
               int(match[2]) if match else piece, real)
    first = c.search(r'Level 2 needs `(\d+) x XP-mod%`', name='the level-2 experience rule')
    if first:
        table = (gd.read_source('src/player.c') or '')
        match = re.search(r'player_exp\[PY_MAX_LEVEL\]\s*=\s*\{\s*(\d+),', table)
        c.emit('source', first.start(), 'level 2 base experience (player_exp[0])',
               int(first[1]), int(match[1]) if match else 'player_exp not found')


@extractor('shop prices', minimum=36)
def shop_prices(c):
    found = c.search(r'Prices\. FACT \([^)]*\):\s*(?P<body>.*?)\.\s+\*\*Gear',
                     re.S, 'the Prices line')
    if not found:
        return
    variable = function_tvals('tval_has_variable_power') or set()
    charged = function_tvals('tval_can_have_charges') or set()
    for piece in re.split(r',\s*', found['body'].replace('\n', ' ')):
        match = re.match(r'^(.*?)\s+(\d+)$', piece.strip())
        if not match:
            c.problem(f'cannot read price {piece!r}', found.start('body'))
            continue
        name = NAME_ALIASES.get(match[1].lower(), match[1])
        obj = find_object(name)
        real = int(obj.first('cost')) if obj else 'no such object'
        c.emit('object cost', found.start('body'), f'{name} cost:', int(match[2]), real)
        if obj:
            by_power = obj.type in variable or obj.type in charged
            c.emit('price semantics', found.start('body'),
                   f'{name} ({obj.type}) is priced by its `cost:` line (not by power or charges)',
                   True, not by_power)
    gear = c.search(r'\*\*Gear \(([^)]*)\) is priced by its power', name='the gear price rule')
    if gear:
        wanted = {'weapons': ['sword', 'polearm', 'hafted', 'bow', 'digger'],
                  'armour': ['boots', 'gloves', 'helm', 'crown', 'shield', 'cloak',
                             'soft armor', 'hard armor', 'dragon armor'],
                  'torches': ['light'], 'ammo': ['shot', 'arrow', 'bolt']}
        for word in re.split(r',\s*', gear[1]):
            for tval in wanted.get(word, ['?']):
                c.emit('price semantics', gear.start(), f'{word}: type {tval} is priced by power '
                       f'(tval_has_variable_power)', True, tval in variable)
        c.emit('source', gear.start(), 'src/obj-power.c defines object_value_real',
               True, 'object_value_real' in (gd.read_source('src/obj-power.c') or ''))


@extractor('price mentions', minimum=3)
def price_mentions(c):
    """`Phase Door (15 g)`, `Boldness 8 g`: a consumable followed by a price."""
    names = sorted({o.name for o in gd.objects() if o.type in CONSUMABLE_TYPES},
                   key=len, reverse=True)
    pattern = r'\b(' + '|'.join(re.escape(n) for n in names) + r')\s+\(?(\d+) g\b'
    for match in c.finditer(pattern):
        obj = find_object(match[1])
        c.emit('object cost', match.start(), f'{match[1]} cost: ({match[0]!r})',
               int(match[2]), int(obj.first('cost')), end=match.end())


def table_after(c, marker):
    """The first markdown table after `marker`: header cells and rows with positions."""
    start = c.text.find(marker)
    if start < 0:
        c.problem(f'the page no longer has {marker!r}')
        return None, []
    rows, header = [], None
    pos = c.text.find('\n|', start)
    while pos >= 0 and pos < len(c.text):
        end = c.text.find('\n', pos + 1)
        end = len(c.text) if end < 0 else end
        row = c.text[pos + 1:end]
        if not row.startswith('|'):
            break
        cells = [x.strip() for x in row.strip().strip('|').split('|')]
        if header is None:
            header = cells
        elif not all(re.fullmatch(r':?-+:?', x) for x in cells):
            rows.append((pos + 1, cells))
        pos = end
    return header, rows


def expand_names(cell):
    """`Potion of Speed / Heroism` -> [('potion','Speed'), ('potion','Heroism')]."""
    names, kind = [], None
    for part in cell.split(' / '):
        part = part.replace('**', '').strip()
        match = re.match(r'^(Potion|Scroll|Wand|Staff|Ring|Rod) of (.*)$', part)
        if match:
            kind, part = match[1].lower(), match[2]
        names.append((kind, part))
    return names


@extractor('keep table', minimum=48)
def keep_table(c):
    header, rows = table_after(c, '**Keep, in this order')
    if not header:
        return
    columns = {}
    for index, cell in enumerate(header):
        low = cell.lower().replace('`', '')
        if low.startswith('cost'):
            columns['cost'] = index
        elif low.startswith('level'):
            columns['level'] = index
        elif low.startswith('found'):
            columns['alloc'] = index
    for needed in ('cost', 'level', 'alloc'):
        if needed not in columns:
            c.problem(f'the Keep table has no {needed!r} column (header {header})')
    if len(columns) < 3:
        return
    for pos, cells in rows:
        names = expand_names(cells[0])
        for column, field_name in (('cost', 'cost:'), ('level', 'level:'),
                                   ('alloc', 'alloc: shallowest depth')):
            values = [v.strip() for v in cells[columns[column]].split(' / ')]
            if len(values) != len(names):
                c.problem(f'{cells[0]!r}: {len(names)} names but {len(values)} '
                          f'values in {column}', pos)
                continue
            for (kind, name), value in zip(names, values):
                obj = find_object(name, types=[kind] if kind else None) if kind else find_object(name)
                if obj is None:
                    c.emit('table', pos, f'{name}: no such object', value, 'absent')
                    continue
                real = {'cost': lambda: int(obj.first('cost')),
                        'level': lambda: int(obj.first('level')),
                        'alloc': lambda: alloc_min(obj)}[column]()
                c.emit(f'table {column}', pos, f'{obj.type} {obj.name} {field_name}',
                       int(value), real)


@extractor('free objects', minimum=32)
def free_objects(c):
    found = c.search(r'cost 0 at `level:` (\d+)-(\d+) is (?P<body>.*?)\.\s+Once a kind',
                     re.S, 'the list of cost-0 objects')
    if not found:
        return
    low, high = int(found[1]), int(found[2])
    kinds = {'potion': 'potion', 'scroll': 'scroll', 'staff': 'staff', 'wand': 'wand'}
    listed = set()
    for group in re.sub(r'\s+', ' ', found['body']).split(';'):
        kind = None
        for piece in group.split(','):
            piece = piece.strip().replace('and ', '', 1) if piece.strip().startswith('and ') else piece.strip()
            match = re.match(r'^(Potion|Scroll|Staff|Wand) of (.*)$', piece)
            if match:
                kind, piece = match[1].lower(), match[2]
            obj = find_object(piece, types=[kinds[kind]] if kind else None)
            if obj is None:
                c.emit('cost 0', found.start('body'), f'{kind} {piece}: no such object',
                       'listed', 'absent')
                continue
            listed.add((obj.type, obj.name))
            c.emit('cost 0', found.start('body'), f'{obj.type} {obj.name} cost:',
                   0, int(obj.first('cost')))
            c.emit('cost 0', found.start('body'), f'{obj.type} {obj.name} level: within {low}-{high}',
                   True, low <= int(obj.first('level')) <= high)
    real = {(o.type, o.name) for o in gd.objects()
            if o.type in kinds and int(o.first('cost', '0')) == 0
            and low <= int(o.first('level', '0')) <= high}
    c.emit('cost 0', found.start('body'),
           f'objects with cost 0 and level {low}-{high} that the page does not list',
           [], sorted(real - listed))
    c.emit('cost 0', found.start('body'),
           'objects the page lists that are not in the cost-0 set', [], sorted(listed - real))


def stock_matches(token, item):
    """Does the page's `Torch` / `shot` mean store item (type, name)?"""
    token = token.strip().lower()
    kind, name = item[0].lower(), item[1].lower()
    return (token in (kind, name) or name.endswith(' ' + token)
            or name.startswith(token + ' '))


@extractor('store stock', minimum=36)
def store_stock(c):
    all_stores = {s['key']: s for s in stores()}

    def stock(key, which):
        return all_stores[key][which] if key in all_stores else []

    found = c.search(r'General: (?P<general>.*?)\.\s+Alchemist: (?P<alchemist>.*?); '
                     r'\*\*sometimes\*\* (?P<alchemist_normal>.*?)\.\s+Magic shop '
                     r'\*\*sometimes\*\*: (?P<magic>.*?) \(read the price\)\.\s+'
                     r'Bookseller: (?P<book>.*?)\.\s+Not sold anywhere in town: '
                     r'(?P<absent>.*?) \(c15 TOWN-02\)', re.S, 'the store stock line')
    if not found:
        return

    def tokens(text):
        out = []
        for piece in re.split(r',\s*', re.sub(r'\s+', ' ', text)):
            out.extend(p for part in piece.split('/') for p in [part.strip()] if p)
        return out

    for key, group, label in (('STORE_GENERAL', 'general', 'General'),
                              ('STORE_ALCHEMY', 'alchemist', 'Alchemist')):
        always = stock(key, 'always')
        said = tokens(found[group])
        for token in said:
            hit = [i for i in always if stock_matches(token, i)]
            c.emit('store always', found.start(group), f'{label} always has {token}',
                   True, bool(hit))
        for item in always:
            c.emit('store always', found.start(group),
                   f'{label}: store.txt always:{item[0]}:{item[1]} is on the page',
                   True, any(stock_matches(t, item) for t in said))
    normal = stock('STORE_ALCHEMY', 'normal')
    for token in tokens(found['alchemist_normal']):
        c.emit('store normal', found.start('alchemist_normal'),
               f'Alchemist sometimes has {token}', True,
               any(stock_matches(token, i) for i in normal))
    magic_normal = stock('STORE_MAGIC', 'normal')
    kind = None
    for piece in tokens(found['magic']):
        for part in re.split(r' and ', piece):
            match = re.match(r'^(wands|staves) of (.*)$', part)
            if match:
                kind, part = {'wands': 'wand', 'staves': 'staff'}[match[1]], match[2]
            c.emit('store normal', found.start('magic'), f'Magic shop sometimes has {kind} {part}',
                   True, (kind, part.lower()) in [(t, n.lower()) for t, n in magic_normal])
    books = {t for t, _ in stock('STORE_BOOK', 'always')}
    c.emit('store always', found.start('book'), 'Bookseller always has every book type',
           True, books == {'magic book', 'prayer book', 'nature book', 'shadow book'})
    everything = [i for s in all_stores.values() for i in s['always'] + s['normal']]
    for token in tokens(found['absent']):
        match = re.match(r'^(.*?)( scrolls| potions)?$', token)
        kind = {' scrolls': 'scroll', ' potions': 'potion'}.get(match[2] or '')
        hit = [i for i in everything
               if i[1].lower() == match[1].lower() and (kind is None or i[0] == kind)]
        c.emit('store absent', found.start('absent'), f'{token} is not in any store.txt list',
               [], hit)


SHOPS = {'General': ('STORE_GENERAL', 'General Store'),
         'Armoury': ('STORE_ARMOR', 'Armoury'),
         'Weaponsmith': ('STORE_WEAPON', 'Weapon Smiths'),
         'Bookseller': ('STORE_BOOK', 'Bookseller'),
         'Alchemist': ('STORE_ALCHEMY', 'Alchemy Shop'),
         'Magic shop': ('STORE_MAGIC', 'Magic Shop'),
         'Black market': ('STORE_BLACK', 'Black Market'),
         'Home': ('HOME', 'Home')}


@extractor('shop digits', minimum=16)
def shop_digits(c):
    found = c.search(r'\(`store` terrain order\): (?P<body>.*?)\. In a store', re.S,
                     'the shop digit list')
    if not found:
        return
    order = [e.value for e in gd.load('store.txt')[0]]
    terrain = {e.value.lower(): e for e in gd.load('terrain.txt')[0]}
    for match in re.finditer(r'\*\*(\d)\*\* ([A-Za-z ]+?)(?:,|$)', found['body']):
        digit, shop = int(match[1]), match[2].strip()
        if shop not in SHOPS:
            c.problem(f'unknown shop {shop!r}', found.start('body'))
            continue
        key, terrain_name = SHOPS[shop]
        position = order.index(key) + 1 if key in order else 'not in store.txt'
        c.emit('shop digit', found.start('body'), f'{shop} is number {digit} in store.txt order',
               digit, position)
        entry = terrain.get(terrain_name.lower())
        glyph = (entry.first('graphics') or '').split(':')[0] if entry else 'no such terrain'
        c.emit('shop digit', found.start('body'),
               f'{shop} is drawn as {digit} in terrain.txt ({terrain_name})', str(digit), glyph)


# -- section 9: the classes --------------------------------------------------

SPELL_ALIASES = {'Find Traps/Doors/Stairs': 'Find Traps, Doors & Stairs',
                 'Whirlwind': 'Whirlwind Attack'}


def class_spells(entry):
    """[(book, name, level, mana, fail)] of a class, in file order."""
    spells, book = [], None
    for key, value, _ in entry.fields:
        if key == 'book':
            book = value.split(':')[2].strip('[]')
        elif key == 'spell':
            parts = value.split(':')
            spells.append((book, parts[0], int(parts[1]), int(parts[2]), int(parts[3])))
    return spells


def sentence_end(text, start):
    """End of the sentence or clause that holds `start`: `. ` or `;` or the end."""
    match = re.compile(r'\.(?=\s|$)|;').search(text, start)
    return match.start() if match else len(text)


def claim_spells(c, cls, entry, body, offset):
    spells = class_spells(entry)
    names = {name.lower(): name for _, name, *_ in spells}
    names.update({alias.lower(): real for alias, real in SPELL_ALIASES.items()
                  if real.lower() in names})
    if not names:
        return
    pattern = r'(?<![\w\[])(' + '|'.join(
        re.escape(n) for n in sorted(names, key=len, reverse=True)) + r')(?![\w\]])'
    mentions = list(re.finditer(pattern, body, re.I))
    own = []
    for index, mention in enumerate(mentions):
        stop = sentence_end(body, mention.end())
        if index + 1 < len(mentions):
            stop = min(stop, mentions[index + 1].start())
        own.append(body[mention.end():stop])
    for index, mention in enumerate(mentions):
        scope = own[index]
        # "A and B CL3": the level after B is A's too (nothing else is shared)
        shared = scope
        if re.fullmatch(r'\s*and\s*', scope) and index + 1 < len(mentions):
            shared = own[index + 1]
        # "CL1 spells: A, B (2 sp)" and "CL1: A only": a head names the level
        before = body[:mention.start()]
        heads = list(re.finditer(r'\bCL(\d+)(?: spells?)?:', before))
        head = (int(heads[-1][1]) if heads and
                not re.search(r'\.\s', before[heads[-1].end():]) else None)
        real_name = names[mention[1].lower()]
        real = next((s for s in spells if s[1] == real_name), None)
        level = re.search(r'\bCL ?(\d+)', shared)
        mana = re.search(r'(\d+) sp\b', scope)
        fail = re.search(r'(\d+)% base failure', scope)
        pos = offset + mention.start()
        if level:
            c.emit('spell level', pos, f'{cls} {real_name} level', int(level[1]), real[2])
        elif head is not None and not re.search(r'CL ?\d', scope):
            c.emit('spell level', pos, f'{cls} {real_name} level (under "CL{head}:")',
                   head, real[2])
        if mana:
            c.emit('spell mana', pos, f'{cls} {real_name} mana', int(mana[1]), real[3])
        if fail:
            c.emit('spell fail', pos, f'{cls} {real_name} base failure %', int(fail[1]), real[4])


def kit_items(text):
    """`Dagger, **2 Cure Serious Wounds**, 15-20 Arrows, [Lesser Charms]` as
    [(name, low, high, dice)] with the page's generic words mapped to object names."""
    generic = {'food': 'Ration of Food', 'torch': 'Wooden Torch', 'torches': 'Wooden Torch',
               'arrows': 'Arrow'}
    items = []
    for piece in text.split(','):
        dice = re.search(r'\((\d+d\d+)\)', piece)
        piece = re.sub(r'\(.*?\)', '', piece).replace('*', '').strip()
        piece = re.sub(r'\s+scroll$', '', piece)
        match = re.match(r'^(?:(\d+)(?:-(\d+))?\s+)?(.*)$', piece)
        low = int(match[1]) if match[1] else None
        high = int(match[2]) if match[2] else low
        name = match[3].strip().strip('[]')
        items.append((generic.get(name.lower(), name), low, high, dice[1] if dice else None))
    return items


@extractor('class paragraphs', minimum=105)
def class_paragraphs(c):
    headings = {}
    chapter = gd.read_chapter(14) or ''
    for number, title in re.findall(r'^## (\d+)\. (\w+)\s*$', chapter, re.M):
        headings[title] = int(number)
    classes = {e.value: e for e in gd.load('class.txt')[0]}
    seen = []
    for match in c.finditer(r'^\*\*(\w+)\*\* \((?:c14 )?s(\d+)\):(.*)$', re.M):
        cls, section, body = match[1], int(match[2]), match[3]
        offset = match.start(3)
        seen.append(cls)
        entry = classes.get(cls)
        if entry is None:
            c.emit('class', match.start(), f'{cls} is a class in class.txt', True, False)
            continue
        c.emit('class section', match.start(), f'{cls} is c14 section {section}',
               section, headings.get(cls, 'no such heading in c14'))
        for found in re.finditer(r'HP = race die: \*\*(\d+)\*\* for a Human', body):
            human = next(e for e in gd.load('p_race.txt')[0] if e.value == 'Human')
            c.emit('class hitdie', offset + found.start(), f'{cls} level-1 HP for a Human',
                   int(found[1]), int(human.first('hitdie')) + int(entry.first('hitdie')))
        for found in re.finditer(r'hit die (\d+)', body):
            c.emit('class hitdie', offset + found.start(), f'{cls} hit die',
                   int(found[1]), int(entry.first('hitdie')))
        for found in re.finditer(r'(?:up to )?(\d+) blows', body):
            c.emit('class blows', offset + found.start(), f'{cls} max blows',
                   int(found[1]), int(entry.first('max-attacks')))
        for found in re.finditer(r'(\d+) lb armour', body):
            magic = entry.first('magic')
            real = int(magic.split(':')[1]) // 10 if magic else 'no spells, no allowance'
            c.emit('class armour', offset + found.start(), f'{cls} armour weight allowance (lb)',
                   int(found[1]), real)
        for found in re.finditer(r'first spell at \*\*CL(\d+)\*\*', body):
            magic = entry.first('magic')
            c.emit('class first spell', offset + found.start(), f'{cls} first spell level',
                   int(found[1]), int(magic.split(':')[0]) if magic else 'no spells')
        for found in re.finditer(r'best (throwing|shooting) skill \((\d+)\)', body):
            skill = 'skill-throw' if found[1] == 'throwing' else 'skill-shoot'
            value = lambda e: int(e.first(skill).split(':')[0])
            c.emit('class skill', offset + found.start(), f'{cls} {skill} base',
                   int(found[2]), value(entry))
            c.emit('class skill', offset + found.start(),
                   f'{cls} has the best {skill} of all classes', True,
                   value(entry) == max(value(e) for e in classes.values()))
        kit = re.search(r'Kit: ([^.;]*)', body)
        if kit:
            equip = []
            for line in entry.all('equip'):
                parts = line.split(':')
                equip.append((parts[1].strip('[]').lower(), int(parts[2]), int(parts[3])))
            for name, low, high, dice in kit_items(kit[1]):
                have = [e for e in equip if e[0] == name.lower()]
                pos = offset + kit.start(1)
                if not have:
                    c.emit('class kit', pos, f'{cls} starts with {name}', True, False)
                    continue
                c.emit('class kit', pos, f'{cls} starts with {name}', True, True)
                if low is not None:
                    c.emit('class kit', pos, f'{cls} starts with {name}: quantity',
                           (low, high), (have[0][1], have[0][2]))
                if dice:
                    obj = find_object(name, prefer=('sword', 'hafted', 'polearm'))
                    c.emit('class kit', pos, f'{cls} kit {name} damage dice',
                           dice, obj.first('attack').split(':')[0] if obj else 'no such object')
        for found in re.finditer(r'; no torch', body):
            c.emit('class kit', offset + found.start(), f'{cls} starts without a torch', True,
                   not any(e.split(':')[1] == 'Wooden Torch' for e in entry.all('equip')))
        flags = {f.strip() for v in entry.all('player-flags') for f in v.split('|')}
        for found in re.finditer(r'fear-proof only from CL(\d+)', body):
            c.emit('class flags', offset + found.start(), f'{cls} flag BRAVERY_{found[1]}',
                   True, f'BRAVERY_{found[1]}' in flags)
        for found in re.finditer(r'no spells', body):
            c.emit('class flags', offset + found.start(), f'{cls} has no magic: line',
                   True, not entry.has('magic'))
        for found in re.finditer(r'random spell learning', body):
            c.emit('class flags', offset + found.start(),
                   f'{cls} lacks CHOOSE_SPELLS (random spell learning)', True,
                   'CHOOSE_SPELLS' not in flags)
        for phrase, flag in (('sees without light', 'UNLIGHT'), ('extra shots', 'FAST_SHOT'),
                             ('earned by fighting', 'COMBAT_REGEN'),
                             ('steals from an adjacent monster', 'STEAL')):
            for found in re.finditer(phrase, body):
                c.emit('class flags', offset + found.start(), f'{cls} flag {flag} ({phrase})',
                       True, flag in flags)
        for found in re.finditer(r'needs CL(\d+) and \[([^\]]+)\]', body):
            tail = re.match(r' \(kind cost (\d+)', body[found.end():])
            spell = [s for s in class_spells(entry) if s[2] == int(found[1])
                     and s[0] == found[2]]
            c.emit('spell book', offset + found.start(),
                   f'{cls} has a level-{found[1]} spell in [{found[2]}]', True, bool(spell))
            if tail:
                cost = None
                lines = entry.fields
                for index, (key, value, _) in enumerate(lines):
                    if key == 'book' and value.split(':')[2].strip('[]') == found[2]:
                        for key2, value2, _ in lines[index + 1:]:
                            if key2 == 'book-properties':
                                cost = int(value2.split(':')[0])
                                break
                            if key2 == 'book':
                                break
                c.emit('book cost', offset + found.end(), f'[{found[2]}] kind cost',
                       int(tail[1]), cost)
        claim_spells(c, cls, entry, body, offset)
    c.emit('class', 0, 'every class has a paragraph', sorted(classes), sorted(seen))
    found = c.search(r'\*\*Priests and Paladins\*\* are given a random one, others choose',
                     name='who chooses spells')
    if found:
        random_ = sorted(name for name, e in classes.items() if e.has('magic') and not any(
            'CHOOSE_SPELLS' in v for v in e.all('player-flags')))
        c.emit('class flags', found.start(), 'classes that do not choose their spells '
               '(no CHOOSE_SPELLS)', ['Paladin', 'Priest'], random_)


@extractor('armour allowance list', minimum=8)
def armour_list(c):
    found = c.search(r'\(((?:Mage|Priest)[^;]*?); c14 0\.2\)', name='the armour weight list')
    if not found:
        return
    classes = {e.value: e for e in gd.load('class.txt')[0]}
    for piece in found[1].split(','):
        match = re.match(r'^\s*([\w/]+) (\d+)(?: lb)?\s*$', piece)
        if not match:
            c.problem(f'cannot read {piece!r}', found.start(1))
            continue
        for name in match[1].split('/'):
            full = {'Necro': 'Necromancer'}.get(name, name)
            entry = classes.get(full)
            magic = entry.first('magic') if entry else None
            c.emit('class armour', found.start(1), f'{full} armour weight allowance (lb)',
                   int(match[2]), int(magic.split(':')[1]) // 10 if magic else 'no such class')


# -- monsters, traps, effects --------------------------------------------------

MONSTER_SHORT = {'smeagol': 'smeagol', 'bullroarer': 'bullroarer the hobbit',
                 'fang': "fang, farmer maggot's dog", 'grip': "grip, farmer maggot's dog"}
KEYWORDS = {'never moves': ('flag', 'NEVER_MOVE'), 'invisible': ('flag', 'INVISIBLE'),
            'paralyses': ('text', 'PARALYZE'), 'confuses': ('text', 'CONFUSE'),
            'terrifies': ('text', 'TERRIFY'), 'drains mana': ('text', 'DRAIN_MANA'),
            'poison touch': ('text', 'POISON'), 'steals gold': ('text', 'EAT_GOLD')}


def monster_table():
    table = {}
    for entry in gd.load('monster.txt')[0]:
        table.setdefault(plain(entry.value), entry)
    return table


def find_monster(token, table):
    token = plain(token)
    token = MONSTER_SHORT.get(token, token)
    for candidate in (token, token.rstrip('s'), token.replace('ies', 'y')):
        if candidate in table:
            return table[candidate]
    return None


def blow_dice(entry):
    out = []
    for blow in entry.all('blow'):
        parts = blow.split(':')
        out.append(parts[2] if len(parts) > 2 else None)
    return out


@extractor('monsters', minimum=50)
def monsters(c):
    start = c.search(r'Early dangers, `monster`', name='the early dangers list')
    stop = c.search(r'- \*\*POLICY\*\* c15 FIGHT-02', name='the list end')
    if not start or not stop:
        return
    block_start, block_end = start.end(), stop.start()
    table = monster_table()
    names = sorted(list(table) + list(MONSTER_SHORT) + [n + 's' for n in table],
                   key=len, reverse=True)
    name_re = re.compile(r'(?<![\w])(' + '|'.join(re.escape(n) for n in names) + r')(?![\w])', re.I)
    block = c.text[block_start:block_end]
    for segment in re.finditer(r'[^;\n]+', block):
        text = segment.group(0)
        base = block_start + segment.start()
        mentions = [m for m in name_re.finditer(plain_keep(text))]
        groups, current = [], []
        for index, m in enumerate(mentions):
            nxt = mentions[index + 1].start() if index + 1 < len(mentions) else len(text)
            scope = text[m.end():nxt]
            current.append(m)
            if re.fullmatch(r'[\s*]*and[\s*]*', scope) and index + 1 < len(mentions):
                continue                           # "Fang and Grip": share the next scope
            groups.append((current, scope))
            current = []
        for members, scope in groups:
            for m in members:
                entry = find_monster(m[1], table)
                label = m[1]
                pos = base + m.start()
                if entry is None:
                    c.emit('monster name', pos, f'{label} is a monster in monster.txt',
                           True, False)
                    continue
                claim_monster(c, entry, label, scope, pos)


def plain_keep(text):
    """Lower-cased and accent-free but the same length, so offsets still line up."""
    out = []
    for ch in text:
        folded = ''.join(x for x in unicodedata.normalize('NFKD', ch)
                         if not unicodedata.combining(x))
        out.append(folded.lower() if len(folded) == 1 else ch.lower())
    return ''.join(out)


def claim_monster(c, entry, label, scope, pos):
    depth = re.search(r'\bDL ?(\d+)', scope)
    if depth:
        c.emit('monster depth', pos, f'{label} depth:', int(depth[1]), int(entry.first('depth')))
    hp = re.search(r'(\d+) hp', scope)
    if hp:
        c.emit('monster hp', pos, f'{label} hit-points:', int(hp[1]), int(entry.first('hit-points')))
    speed = re.search(r'\+(\d+)(?: speed)?\b', scope)
    if speed:
        c.emit('monster speed', pos, f'{label} speed: (+{speed[1]})', int(speed[1]),
               int(entry.first('speed')) - 110)
    exp = re.search(r'(\d+) exp x level (\d+)', scope)
    if exp:
        c.emit('monster exp', pos, f'{label} experience:', int(exp[1]),
               int(entry.first('experience')))
        c.emit('monster depth', pos, f'{label} depth: (as level)', int(exp[2]),
               int(entry.first('depth')))
    scope_blows = re.sub(r'swarm\*\* of \d+d\d+', '', scope)
    dice = re.search(r'(?:(\d+) x )?(\d+d\d+)', scope_blows)
    real_blows = blow_dice(entry)
    if dice:
        count = int(dice[1]) if dice[1] else None
        have = real_blows.count(dice[2])
        c.emit('monster blow', pos, f'{label} blow dice {dice[2]}' +
               (f' x{count}' if count else ''), (count or 1, dice[2]),
               (have if count else min(have, 1), dice[2]))
    swarm = re.search(r'swarm\*\* of (\d+d\d+)', scope)
    if swarm:
        friends = (entry.first('friends') or '').split(':')
        c.emit('monster group', pos, f'{label} friends: dice', swarm[1],
               friends[1] if len(friends) > 1 else 'no friends: line')
    upto = re.search(r'up to (\d+)(?: per turn)?', scope)
    if upto and real_blows:
        top = sum(gd.dice_max(d) or 0 for d in real_blows)
        factor = 1 + (int(entry.first('speed')) - 110) // 10
        c.emit('monster damage', pos, f'{label} worst melee per player turn', int(upto[1]),
               top * factor)
    for word, (where, needle) in KEYWORDS.items():
        if word in scope.lower():
            if where == 'flag':
                real = needle in entry.flags()
            else:
                real = any(needle in value for _, value, _ in entry.fields)
            c.emit('monster trait', pos, f'{label} {word} ({needle})', True, real)


@extractor('trap door', minimum=6)
def trap_door(c):
    found = c.search(r'`trap` gives it (\d+d\d+) damage \((\d+)-(\d+)', name='the trap door damage')
    traps = {e.value.split(':')[0].lower(): e for e in gd.load('trap.txt')[0]}
    entry = traps.get('trap door')
    if found:
        dice = (entry.first('dice') if entry else None)
        c.emit('trap', found.start(), 'trap door dice', found[1], dice)
        c.emit('trap', found.start(), 'trap door minimum damage', int(found[2]),
               int(dice.split('d')[0]) if dice else None)
        c.emit('trap', found.start(), 'trap door maximum damage', int(found[3]),
               gd.dice_max(dice) if dice else None)
    down = c.search(r'drops you one level \*\*on no staircase\*\*', name='the trap door drop')
    if down:
        c.emit('trap', down.start(), 'trap door drops you a level (flag DOWN)', True,
               bool(entry and 'DOWN' in entry.flags()))
    races = [int(e.first('hitdie')) for e in gd.load('p_race.txt')[0]]
    classes = {e.value: int(e.first('hitdie')) for e in gd.load('class.txt')[0]}
    for hp in c.finditer(r'level-1 (\w+) has (\d+)-(\d+) hit\s+points'):
        real = (min(races) + classes.get(hp[1], 0), max(races) + classes.get(hp[1], 0))
        c.emit('trap', hp.start(), f'level-1 {hp[1]} hit points: race die + class die',
               (int(hp[2]), int(hp[3])), real)


@extractor('effects', minimum=34)
def effects(c):
    constants_ = constants()
    handler = gd.read_source('src/effect-handler-general.c') or ''
    # Flask of oil damage
    found = c.search(r'1d4 x3 \(throwing weight multiplier\) x3 \(EXPLODE\) = '
                     r'\*\*(\d+) to (\d+) per hit, about (\d+)\*\*', name='the flask damage line')
    if found:
        flask = find_object('Flask of oil')
        dice = flask.first('attack').split(':')[0]
        n, sides = (int(x) for x in dice.split('d'))
        weight = int(flask.first('weight'))
        multiplier = (2 + weight // 12) * (3 if 'EXPLODE' in flask.flags() else 1)
        c.emit('effect', found.start(), 'flask of oil attack: 1d4', '1d4', dice)
        c.emit('effect', found.start(), 'flask of oil damage low', int(found[1]), n * multiplier)
        c.emit('effect', found.start(), 'flask of oil damage high', int(found[2]),
               n * sides * multiplier)
        average = n * (sides + 1) / 2 * multiplier
        c.emit('effect', found.start(), f'flask of oil average damage ({average})',
               int(found[3]), int(found[3]), ok=int(found[3]) in (int(average), round(average)))
    found = c.search(r'Daggers and Spears are `THROWING` too \(x(\d+) and x(\d+) on dice\)',
                     name='the dagger and spear multipliers')
    if found:
        for name, said in (('Dagger', found[1]), ('Spear', found[2])):
            obj = find_object(name, types=['sword', 'polearm'])
            c.emit('effect', found.start(), f'{name} is THROWING', True, 'THROWING' in obj.flags())
            c.emit('effect', found.start(), f'{name} throw multiplier (2 + weight/12)', int(said),
                   2 + int(obj.first('weight')) // 12)
    # Phase Door, Cure Light Wounds
    found = c.search(r'Phase Door \((\d+) g\): teleports about (\d+) squares', name='Phase Door')
    if found:
        door = find_object('Phase Door')
        c.emit('effect', found.start(), 'Phase Door distance (dice:)', int(found[2]),
               int(door.first('dice')))
    found = c.search(r'Cure Light Wounds: heals (\d+), cures blindness, cuts (\d+) and confusion '
                     r'(\d+) turns', name='Cure Light Wounds')
    if found:
        potion = find_object('Cure Light Wounds')
        fields = [(k, v) for k, v, _ in potion.fields]
        def dice_after(effect):
            for i, (k, v) in enumerate(fields):
                if k == 'effect' and v == effect:
                    return int(fields[i + 1][1]) if fields[i + 1][0] == 'dice' else None
        c.emit('effect', found.start(), 'CLW heals', int(found[1]), dice_after('HEAL_HP'))
        c.emit('effect', found.start(), 'CLW cuts', int(found[2]), dice_after('TIMED_DEC:CUT'))
        c.emit('effect', found.start(), 'CLW confusion', int(found[3]),
               dice_after('TIMED_DEC:CONFUSED'))
        c.emit('effect', found.start(), 'CLW cures blindness', True,
               ('effect', 'CURE:BLIND') in fields)
    # Magic Mapping
    scroll = find_object('Magic Mapping', types=['scroll'])
    said = c.finditer(r'within (\d+) rows and (\d+) columns of you')
    if not said:
        c.problem('the page no longer says how far Magic Mapping maps')
    for found in said:
        c.emit('effect', found.start(), 'Magic Mapping effect-yx (rows, columns each side)',
               (int(found[1]), int(found[2])),
               tuple(int(x) for x in scroll.first('effect-yx').split(':')))
    c.emit('source', said[0].start() if said else 0,
           'MAP_AREA reads effect-yx as a distance each side of you', True,
           'y1 = centre.y - dist_y' in handler and 'x2 = centre.x + dist_x' in handler)
    found = c.search(r'Find Traps/Doors/Stairs 1 sp \(detects within (\d+) rows and (\d+) columns\)',
                     name='the Mage detection area')
    if found:
        mage = next(e for e in gd.load('class.txt')[0] if e.value == 'Mage')
        index = next(i for i, (k, v, _) in enumerate(mage.fields)
                     if k == 'spell' and v.startswith('Find Traps'))
        yx = [v for k, v, _ in mage.fields[index:index + 8] if k == 'effect-yx']
        c.emit('effect', found.start(), 'Find Traps, Doors & Stairs effect-yx',
               f'{found[1]}:{found[2]}', yx[0] if yx else None)
    # source facts
    recall = [m for m in c.finditer(r'\b(\d+)-(\d+) turns')
              if 'Recall' in c.text[c.starts[c.line(m.start()) - 1]:c.starts[c.line(m.start())]]]
    if not recall:
        c.problem('the page no longer gives the Word of Recall delay')
    match = re.search(r'word_recall = randint0\((\d+)\) \+ (\d+);', handler)
    real = (int(match[2]), int(match[2]) + int(match[1]) - 1) if match else None
    for word in recall:
        c.emit('source', word.start(), 'Word of Recall delay (src/effect-handler-general.c)',
               (int(word[1]), int(word[2])), real)
    match = re.search(r'deep_descent = (\d+) \+ randint1\((\d+)\);', handler)
    deeps = c.finditer(r'\b(\d+)\+(\d+)d(\d+) turns')
    if not deeps:
        c.problem('the page no longer gives the Deep Descent delay')
    for deep in deeps:
        c.emit('source', deep.start(), 'Deep Descent delay, base + dice (src/effect-handler-general.c: '
               'base + randint1(sides))', (int(deep[1]), int(deep[2]), int(deep[3])),
               (int(match[1]), 1, int(match[2])) if match else None)
    levels = c.search(r'\*\*(\d+) levels below your deepest level reached\*\*', name='Deep Descent depth')
    if levels:
        has = '(4 / z_info->stair_skip) + 1' in handler and 'player->max_depth' in handler
        skip = constants_.get('world:stair-skip')
        c.emit('source', levels.start(), 'Deep Descent target below max_depth',
               int(levels[1]), 4 // skip + 1 if has and skip else None)
    for found in c.finditer(r'Magic Mapping \([^)]*found from DL(\d+)\)'):
        c.emit('effect', found.start(), 'Magic Mapping found from (alloc: minimum)',
               int(found[1]), alloc_min(scroll))
    for found in c.finditer(r'Deep Descent\*\* \(`object`: found from DL(\d+)'):
        c.emit('effect', found.start(), 'Deep Descent found from (alloc: minimum)',
               int(found[1]), alloc_min(find_object('Deep Descent', types=['scroll'])))
    for found in c.finditer(r'Range up to (\d+) squares'):
        match = re.search(r'range = MIN\(\(\(str \+ 20\) \* 10\) / weight, (\d+)\);',
                          gd.read_source('src/player-attack.c') or '')
        c.emit('source', found.start(), 'throwing range cap (src/player-attack.c)',
               int(found[1]), int(match[1]) if match else None)
    for found in c.finditer(r'\+(\d+) speed (?:is double your moves|monster acts twice)'):
        c.emit('docs', found.start(), f'docs/attack.rst: (+{found[1]}) is exactly double normal speed',
               True, f'(+{found[1]}) is exactly double normal speed' in
               (gd.read_source('docs/attack.rst') or ''))
    torch = c.search(r'General Store lists (\d+) turns', name='the torch fuel')
    if torch:
        c.emit('constants', torch.start(), 'obj-make:fuel-torch', int(torch[1]),
               constants_.get('obj-make:fuel-torch'))
    gold = c.search(r'Gold = (\d+) \+ unspent point-buy', name='the starting gold')
    if gold:
        c.emit('constants', gold.start(), 'player:start-gold', int(gold[1]),
               constants_.get('player:start-gold'))
    pack = c.search(r'Pack holds (\d+) kinds \(`command`\)', name='the pack size')
    if pack:
        text = re.sub(r'\s+', ' ', gd.read_source('docs/command.rst') or '')
        c.emit('docs', pack.start(), 'docs/command.rst: pack size',
               True, f'up to {pack[1]} different items' in text)
    found = c.search(r'pays experience \(the last field of a `class` `spell:` line\)',
                     name='the first-cast experience field')
    if found:
        header = (gd.GAMEDATA / 'class.txt').read_text()
        c.emit('docs', found.start(), 'class.txt: spell:name:level:mana:fail:exp (exp is last)',
               True, '# spell:name:level:mana:fail:exp' in header)
        spell = next(e for e in gd.load('class.txt')[0] if e.has('spell'))
        fields = spell.all('spell')[0].split(':')
        c.emit('docs', found.start(), 'a class.txt spell line has the six fields the header names',
               6, len(fields) + 1)
    formula = c.search(r'`hitdie = r_mhp \+ c_mhp`', name='the hit point formula')
    if formula:
        birth = gd.read_source('src/player-birth.c') or ''
        c.emit('source', formula.start(), 'src/player-birth.c: hitdie = r_mhp + c_mhp', True,
               bool(re.search(r'hitdie\s*=\s*p->race->r_mhp\s*\+\s*p->class->c_mhp', birth)))
    defaults = option_defaults()
    for pattern, option, wanted in ((r'start kit \*\*on\*\*', 'birth_start_kit', 'true'),
                                    (r'selling \*\*off\*\*', 'birth_no_selling', 'true'),
                                    (r'connected stairs \*\*on\*\*', 'birth_connect_stairs', 'true')):
        found = c.search(pattern, name=pattern)
        if found:
            c.emit('option', found.start(), f'{option} default (src/list-options.h)', wanted,
                   defaults.get(option))
    found = c.search(r'`birth_no_selling` is on', name='no selling is on')
    if found:
        c.emit('option', found.start(), 'birth_no_selling default (src/list-options.h)', 'true',
               defaults.get('birth_no_selling'))
    found = c.search(r'`10 - feeling`', name='the level feeling reversal')
    if found:
        display = gd.read_source('src/ui-display.c') or ''
        c.emit('source', found.start(), 'src/ui-display.c prints 10 - mon_feeling', True,
               bool(re.search(r'\(\s*10-mon_feeling\s*\)', display)))
        generate = gd.read_source('src/generate.c') or ''
        c.emit('source', found.start(), 'src/generate.c calc_mon_feeling: 1 is the worst (x > 7000)',
               True, bool(re.search(r'if \(x > 7000\) return 1;', generate)))


# What the strategy manual is quoted as saying: (page anchor, chapter or None=any, needle).
def manual_says(c):
    rules = [
        (r'reserve \(max\(20, 10% of max HP\)', 15, r'`K_HP_RESERVE` \| max\(20, 10% max hp\)'),
        (r'rest only when no awake monster can reach you in about (\d+) turns', 15,
         r'`K_REST_SAFE_TURNS` \| {0} \|'),
        (r'within about (\d+) steps', 15, r'`K_STAIR_REST_DIST` \| {0} \|'),
        (r'DL5 needs Word of Recall, 3\+ cure potions and a ranged attack', 15,
         r'\| 5 \| Word of Recall, 3\+ cure potions, ranged attack \|'),
        (r'DL15 needs 100 max HP and about 10 Phase Door', 15,
         r'\| 15 \| 100 max hp, Phase ×10 \|'),
        (r'`K_LF_LEAVE = (\d+)`', 15, r'`K_LF_LEAVE` \| {0} \|'),
        (r'Word of Recall \(\d+-\d+ turns delay\)', 15, r'recall 15-34 world ticks'),
        (r'`monster exp x monster level / your level`', 15, r'`mexp × mlevel / plevel`'),
        (r'Buy: oil (\d+)-(\d+)', None,
         r'(?i)(flasks? of oil[^\n]*\b{0}[-–]{1}\b|\b{0}[-–]{1}\s+flasks?)'),
        (r'10-20 of them', None, r'(?i)flasks? of oil[^\n]*\b10[-–]20|10[-–]20[^\n]*flasks?'),
        (r'strategy manual says 10-20 before the first descent', None,
         r'(?i)flasks? of oil[^\n]*\b10[-–]20|10[-–]20[^\n]*flasks?'),
        (r'paralyse you and drain CON \(c14 0\.2\)', 14, r'50% chance of CON damage'),
    ]
    chapters = {n: gd.read_chapter(n) or '' for n in gd.strategy_chapter_files()}
    for anchor, chapter, needle in rules:
        found = c.search(anchor, name=anchor)
        if not found:
            continue
        needle = needle.format(*[g for g in found.groups()]) if found.groups() else needle
        texts = [chapters[chapter]] if chapter else list(chapters.values())
        where = f'chapter {chapter}' if chapter else 'any chapter'
        c.emit('manual says', found.start(), f'{where} contains {needle!r}', True,
               any(re.search(needle, t) for t in texts), end=found.end())


extractor('strategy manual quotations', minimum=12)(manual_says)


# Numbers the data files cannot give. Each must carry a label on the page, so
# a reader knows it is not a fact: the check is that the label is still there.
UNVERIFIABLE = [
    (r'arrows \(priced by power, believed about \d+ g each: (UNTESTED)[^)]*\)',
     'ammo is priced by object_value_real from computed power and store markup; '
     'not derivable from object.txt'),
]


@extractor('labelled unverifiable numbers', minimum=1)
def unverifiable(c):
    for pattern, reason in UNVERIFIABLE:
        found = c.search(pattern, name=pattern)
        if found:
            c.emit('unverifiable', found.start(), reason, 'UNTESTED', found.group(1),
                   verifiable=False, end=found.end())


# -- citations ------------------------------------------------------------

def line_text(c, number):
    """Line `number` (1-based) of the page."""
    end = c.starts[number] if number < len(c.starts) else len(c.text)
    return c.text[c.starts[number - 1]:end]


@extractor('citation shortcuts', minimum=14)
def citation_shortcuts(c):
    """The header's `object`/`store`/... = file conventions: every file named exists."""
    found = c.search(r'^Sources, so any line can be checked\..*$', re.M, 'the sources header')
    if not found:
        return
    header = found.group(0)
    for names, target in re.findall(r'((?:`\w+`/?)+) = `([^`]+)`', header):
        for name in re.findall(r'`(\w+)`', names):
            path = target.replace('<name>', name)
            c.shortcuts[name] = path
            c.emit('citation', found.start(), f'`{name}` = {path} exists', True,
                   (pins.ROOT / path).is_file())
    for chapter in re.findall(r'`c(\d+)`', header):
        c.emit('citation', found.start(), f'chapter c{chapter} exists in the strategy manual',
               True, int(chapter) in gd.strategy_chapter_files())
    c.emit('citation', found.start(), 'the header defines the gamedata and docs shortcuts',
           True, {'object', 'store', 'class', 'race', 'monster', 'trap',
                  'command', 'playing', 'attack', 'birth'} <= set(c.shortcuts))


def rst_titles(text):
    """Section titles of an .rst file: a line followed by a line of ====, ---- ..."""
    titles = set()
    lines = text.splitlines()
    for index in range(len(lines) - 1):
        under = lines[index + 1]
        if (lines[index].strip() and re.fullmatch(r'([=~^"\-#*+])\1{2,}', under)
                and len(under) >= len(lines[index].rstrip()) - 1):
            titles.add(plain(lines[index]))
    return titles


def line_files(c, pos):
    """The gamedata files the page cites on the line holding `pos`, or on the
    lines either side of it when that line cites none (the page wraps)."""
    number = c.line(pos)
    for lines in ([number], [number - 1, number + 1]):
        files = []
        for n in lines:
            if not 1 <= n <= len(c.starts):
                continue
            for token in re.findall(r'`([^`\n]+)`', line_text(c, n)):
                path = c.shortcuts.get(token, '')
                name = (path.rsplit('/', 1)[-1] if path.startswith('vendor/angband/lib/gamedata/')
                        else token if re.fullmatch(r'[\w-]+\.txt', token) else None)
                if name and (gd.GAMEDATA / name).is_file() and name not in files:
                    files.append(name)
        if files:
            return files
    return []


@extractor('source and field citations', minimum=32)
def source_citations(c):
    """Every backticked token that names something in the pinned tree must exist."""
    keys = {path.name: gd.load(path.name)[1] for path in gd.GAMEDATA.glob('*.txt')}
    every_key = set().union(*keys.values())
    options = option_defaults()
    chapter15 = gd.read_chapter(15) or ''
    vocabulary = ''.join(p.read_text(errors='replace') for p in gd.GAMEDATA.glob('*.txt')) + \
        ''.join(p.read_text(errors='replace') for p in (gd.ANGBAND / 'src').glob('list-*.h'))
    for tick in c.finditer(r'`([^`\n]+)`'):
        token, pos = tick[1], tick.start(1)
        found = re.match(r'^(?:vendor/angband/)?(src/[\w-]+\.[ch])(?::|\s|$)\s*(.*)$', token)
        if found and found[1] != 'src/x.c':                 # `src/x.c` is the header's example
            source = gd.read_source(found[1])
            c.emit('citation', pos, f'{found[1]} exists at the pin', True, source is not None)
            words = re.findall(r'[A-Za-z_][A-Za-z_0-9]+', found[2])
            for word in words:
                if source is not None and ('_' in word or len(words) == 1):
                    c.emit('citation', pos, f'{found[1]} contains {word!r}', True, word in source)
        elif re.fullmatch(r'[\w-]+\.txt', token):
            c.emit('citation', pos, f'{token} exists in lib/gamedata', True,
                   (gd.GAMEDATA / token).is_file())
        elif re.fullmatch(r'(?:knowledge|docs|records)/[\w./-]+', token):
            c.emit('citation', pos, f'{token} exists in this repository', True,
                   (pins.ROOT / token).exists())
        elif re.fullmatch(r'[a-z]+(?:_[a-z]+)+', token):
            c.emit('citation', pos, f'option {token} exists in src/list-options.h', True,
                   token in options)
        elif re.fullmatch(r'[A-Z][A-Z_]{3,}', token):
            c.emit('citation', pos, f'flag {token} exists in the game data or chapter 15', True,
                   token in vocabulary or token in chapter15)
        else:
            # field references: `cost:`, `cost:0`, `effect-yx`, a bare `hitdie`
            ref = re.fullmatch(r'([a-z][a-z-]*):\S*', token)
            bare = re.fullmatch(r'[a-z][a-z-]*', token)
            if ref or (bare and token in every_key and token not in c.shortcuts):
                key = ref[1] if ref else token
                files = line_files(c, pos)
                valid = [f for f in files if key in keys[f]] if files else \
                    [f for f, k in keys.items() if key in k]
                c.emit('citation', pos,
                       f'field `{key}` exists in {", ".join(files) or "any gamedata file"}',
                       True, bool(valid))


@extractor('chapter references', minimum=23)
def chapter_references(c):
    """`c4 4.11`, `ESC-04`, `c15 ESC`: the section or rule must exist at the pin."""
    chapters = {n: gd.read_chapter(n) or '' for n in gd.strategy_chapter_files()}
    fifteen = chapters.get(15, '')
    for m in c.finditer(r'\bc(\d+) (\d+\.\d+)\b'):
        chapter, section = int(m[1]), m[2]
        has = bool(re.search(rf'^#{{2,4}} {re.escape(section)}[ .]',
                             chapters.get(chapter, ''), re.M))
        c.emit('citation', m.start(), f'c{chapter} has a section {section}', True, has,
               end=m.end())
    for m in c.finditer(r'\b([A-Z]{3,6})-(\d\d)((?:/\d\d)*)\b'):
        for rule in [f'{m[1]}-{m[2]}'] + [f'{m[1]}-{n}' for n in m[3].split('/') if n]:
            c.emit('citation', m.start(), f'rule {rule} exists in chapter 15', True,
                   bool(re.search(rf'\b{rule}\b', fifteen)), end=m.end())
    for m in c.finditer(r'\bc15 ([A-Z]{2,6})\b(?!-)'):
        c.emit('citation', m.start(), f'rule family {m[1]} exists in chapter 15', True,
               bool(re.search(rf'\b{m[1]}-\d\d\b', fifteen)), end=m.end())


@extractor('quotations and document sections', minimum=9)
def quotations(c):
    """A phrase in double quotes is quoted from a source cited on its line."""
    sources = {}

    def source_text(token):
        if token not in sources:
            text = None
            if token in c.shortcuts:
                path = pins.ROOT / c.shortcuts[token]
                text = path.read_text(errors='replace') if path.is_file() else None
            elif re.fullmatch(r'c\d+', token):
                text = gd.read_chapter(int(token[1:]))
            elif re.fullmatch(r'(?:vendor/angband/)?src/[\w-]+\.[ch]', token):
                text = gd.read_source(token.replace('vendor/angband/', ''))
            sources[token] = text
        return sources[token]

    for m in c.finditer(r'"([^"\n]{8,})"'):
        text = line_text(c, c.line(m.start()))
        tokens = [t.split()[0] for t in re.findall(r'`([^`\n]+)`', text) if t.split()]
        tokens += [f'c{n}' for n in re.findall(r'\bc(\d+)\b', text)]
        names = [t for t in dict.fromkeys(tokens) if source_text(t)]
        if not names:
            continue                      # no source on the line: not a source quotation
        pieces = [plain(p) for p in re.split(r'\s*\.\.\.\s*', m[1])]
        found_in = []
        for name in names:
            haystack = plain(source_text(name))
            position = 0
            for piece in pieces:
                at = haystack.find(piece, position)
                if at < 0:
                    break
                position = at + len(piece)
            else:
                found_in.append(name)
        c.emit('quotation', m.start(), f'"{m[1]}" appears in a source cited on the line '
               f'({", ".join(names)})', True, bool(found_in), end=m.end())
    for m in c.finditer(r'`(playing|attack|command|birth)`,\s+([A-Z][A-Za-z ]+?)'
                        r'(?=[,:)]|\s+which)'):
        titles = rst_titles(source_text(m[1]) or '')
        for part in re.split(r' and ', m[2]):
            c.emit('document section', m.start(), f'{m[1]}.rst has a section titled {part!r}',
                   True, plain(part) in titles, end=m.end())


# -- running everything --------------------------------------------------------

def check(text=None, path=INSTRUCTIONS):
    """Read the page and check every claim the grammars find."""
    text = path.read_text() if text is None else text
    ctx = Ctx(text)
    # citation shortcuts first: later extractors use them
    ordered = sorted(EXTRACTORS, key=lambda e: e[0] != 'citation shortcuts')
    for name, minimum, fn in ordered:
        before = len(ctx.report.claims)
        try:
            fn(ctx)
        except Exception as error:       # a broken grammar must not read as a pass
            ctx.problem(f'extractor {name!r} crashed: {type(error).__name__}: {error}')
        found = len(ctx.report.claims) - before
        ctx.report.extractors[name] = found
        if found < minimum:
            ctx.problem(f'extractor {name!r} found {found} claims, expected at least {minimum}: '
                        f'the page changed or the grammar has to follow it')
    return ctx.report
