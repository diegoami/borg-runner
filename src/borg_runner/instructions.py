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

Volume two (`manuals/INSTRUCTIONS_2.md`, depth 5 to 20) is read the same way with
`check(volume=2)`. It borrows volume one's shorthand header, reuses the generic
extractors (citations, chapter references, quotations) and `claim_monster` and
`claim_spells`, and adds grammars for what only it says: counts over the whole
monster list (every breather, summoner and unique in range must be in its table),
arithmetic from the game's own formulas (breath damage and falloff, teleport
distance, energy, hit points at a level, gold per pile) and what the strategy
manual says against what the data says. Each claim can name the page's numbers it
settles (`covers`), so `number_coverage` can say how many of the page's numbers
nothing checks.
"""
import bisect
import functools
import json
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from borg_runner import gamedata as gd
from borg_runner import pins

INSTRUCTIONS = pins.ROOT / 'manuals' / 'INSTRUCTIONS.md'
INSTRUCTIONS_2 = pins.ROOT / 'manuals' / 'INSTRUCTIONS_2.md'

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
    covers: tuple = ()          # spans of the page's numbers this claim settles

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

@functools.lru_cache(maxsize=512)
def plain(text):
    """Lower case, no accents, no markdown, one space: for comparing names."""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'[*`]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()


class Ctx:
    """The page, its line numbers and the claims found so far."""

    def __init__(self, text, volume=1):
        self.text = text
        self.volume = volume
        self.starts = [0] + [m.end() for m in re.finditer('\n', text)]
        self.report = Report()
        self.shortcuts = {}            # `object` -> its path, from the page's own header

    def line(self, pos):
        return bisect.bisect_right(self.starts, pos)

    def emit(self, kind, pos, what, claimed, real, ok=None, end=None,
             verifiable=True, covers=()):
        ok = (claimed == real) if ok is None else ok
        self.report.claims.append(Claim(
            self.line(pos), kind, what, claimed, real, bool(ok),
            (pos, end if end is not None else pos), verifiable, tuple(covers)))
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


def extractor(name, minimum, volumes=(1,)):
    """Register a grammar. `minimum` is how many claims it must find, one number
    for every volume it reads or {volume: number}."""
    def register(fn):
        EXTRACTORS.append((name, minimum, fn, tuple(volumes)))
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


WORD_NUMBERS = {'two': 2, 'three': 3, 'six': 6, 'twelve': 12, 'twenty': 20,
                'forty': 40}


def player_exp_table():
    """`player_exp[]` from src/player.c: the cumulative experience for CL2, CL3, ..."""
    text = gd.read_source('src/player.c') or ''
    body = re.search(r'player_exp\[PY_MAX_LEVEL\]\s*=\s*\{(.*?)\}', text, re.S)
    return [int(n) for n in re.findall(r'\d+', body[1])] if body else []


def monster_entry(name):
    """A monster.txt entry by its name, or None."""
    for entry in gd.load('monster.txt')[0]:
        if entry.value.lower() == name.lower():
            return entry
    return None


def spell_entries(class_name):
    """{spell: {'level':, 'mana':, 'fail':, 'exp':, 'dice':, 'expr':}} for a class."""
    entry = next((e for e in gd.load('class.txt')[0]
                  if e.value.lower() == class_name.lower()), None)
    spells, current = {}, None
    for key, value, *_ in (entry.fields if entry else []):
        if key == 'spell':
            parts = value.split(':')
            current = parts[0]
            spells[current] = {'level': int(parts[1]), 'mana': int(parts[2]),
                               'fail': int(parts[3]), 'exp': int(parts[4]),
                               'dice': None, 'expr': None}
        elif current and key in ('dice', 'expr'):
            spells[current][key] = spells[current][key] or value
    return spells


def missile_dice(spells, level):
    """Magic Missile's dice at character `level`, from `dice:` and `expr:`."""
    dice, expr = spells['Magic Missile']['dice'], spells['Magic Missile']['expr']
    match = re.fullmatch(r'\$(\w)d(\d+)', dice or '')
    operation = re.fullmatch(r'(\w):PLAYER_LEVEL:(.+)', expr or '')
    if not (match and operation and match[1] == operation[1]):
        return None
    count = level
    for token in operation[2].split():                 # `- 1 / 5 + 3`, left to right
        if re.fullmatch(r'[-+*/]', token):
            op = token
        else:
            value = int(token)
            count = {'-': count - value, '+': count + value,
                     '*': count * value, '/': count // value}[op]
    return f'{count}d{match[2]}'


def monster_rounds(limit=2):
    """[(worst round, name)] for every monster at `limit` depth or shallower."""
    rows = []
    for entry in gd.load('monster.txt')[0]:
        depth = entry.first('depth')
        if depth is None or int(depth) > limit:
            continue
        total = 0
        for blow in entry.all('blow'):
            parts = blow.split(':')
            dice = re.fullmatch(r'(\d+)d(\d+)', parts[2].strip()) if len(parts) > 2 else None
            total += int(dice[1]) * int(dice[2]) if dice else 0
        rows.append((total, entry.value))
    return sorted(rows, reverse=True)


def died_records():
    """{run: record} for every archived run that died."""
    found = {}
    for path in sorted((pins.ROOT / 'records').glob('*/record.json')):
        try:
            record = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if record.get('died'):
            found[path.parent.name] = record
    return found


@extractor('thin characters', minimum=20)
def thin_characters(c):
    """What a character with eight hit points is up against, and what killed
    the three that died. The page's gate on descending."""
    races = {e.value.lower(): e for e in gd.load('p_race.txt')[0]}
    classes = {e.value.lower(): e for e in gd.load('class.txt')[0]}

    def at_level_one(race, character_class):
        return (int(races[race].first('hitdie')) +
                int(classes[character_class].first('hitdie')))

    found = c.search(r'\*\*(\d+)\*\* for a Gnome\s*\nMage, \*\*(\d+)\*\* for a Human Mage, '
                     r'\*\*(\d+)\*\* for a High-Elf Druid', name='the thin hit points')
    if found:
        for group, (race, kind) in enumerate([('gnome', 'mage'), ('human', 'mage'),
                                              ('high-elf', 'druid')], start=1):
            c.emit('thin', found.start(group), f'{race} {kind} hit points at CL1',
                   int(found[group]), at_level_one(race, kind))
    found = c.search(r'Each level adds a\s*\nroll of `randint1\(hit die\)`, 1 to (\d+) for that '
                     r'Gnome mage \(FACT,\s*\n`src/player-birth\.c roll_hp\(\)`\), so \*\*about '
                     r'(\d+) hit points at CL4 and (\d+) at\s*\nCL5\*\* on average, and as few as '
                     r'(\d+) at CL5', name='the hit-point roll')
    if found:
        die = at_level_one('gnome', 'mage')
        source = gd.read_source('src/player-birth.c') or ''
        c.emit('thin', found.start(), 'a level adds randint1(hitdie)', True,
               'randint1(player->hitdie)' in source)
        c.emit('thin', found.start(1), 'the gnome mage hit die', int(found[1]), die)
        for group, level in ((2, 4), (3, 5)):
            average = die + (level - 1) * (die + 1) / 2
            c.emit('thin', found.start(group), f'average hit points at CL{level}',
                   int(found[group]), round(average),
                   ok=abs(int(found[group]) - average) <= 1)
        c.emit('thin', found.start(4), 'the worst roll at CL5',
               int(found[4]), die + 4)
    rounds = monster_rounds()
    found = c.search(r'is a \*\*soldier\*\*, 2 x 1d7 =\s*\n\s*\*\*(\d+) damage\*\*', name='the worst round')
    if found:
        c.emit('thin', found.start(1), 'the worst round at depth 2 or shallower',
               int(found[1]), rounds[0][0])
        c.emit('thin', found.start(1), 'and it is the soldier that does it',
               'soldier', rounds[0][1])
    found = c.search(r'\*\*(\d+) of the (\d+) monsters at depth 2 or shallower can take 8\s*\n'
                     r'\s*hit points in one round, and (\d+) of them can take 10\*\*',
                     name='how many can kill eight hit points')
    if found:
        c.emit('thin', found.start(2), 'monsters at depth 2 or shallower',
               int(found[2]), len(rounds))
        c.emit('thin', found.start(1), 'how many can take 8 hit points in a round',
               int(found[1]), sum(1 for total, _ in rounds if total >= 8))
        c.emit('thin', found.start(3), 'how many can take 10',
               int(found[3]), sum(1 for total, _ in rounds if total >= 10))
    found = c.search(r'a \*\*cave spider\*\* comes in a group of \*\*(\d+d\d+)\*\* of them, each '
                     r'(\d+d\d+), at speed\s*\n\s*(\d+)', name='the cave spider group')
    if found:
        spider = next((e for e in gd.load('monster.txt')[0] if e.value == 'cave spider'), None)
        friends = (spider.all('friends') + spider.all('friends-base')) if spider else []
        c.emit('thin', found.start(1), 'cave spider group size',
               found[1], friends[0].split(':')[1] if friends else 'no friends line')
        c.emit('thin', found.start(2), 'cave spider blow',
               found[2], spider.all('blow')[0].split(':')[2] if spider else None)
        c.emit('thin', found.start(3), 'cave spider speed',
               int(found[3]), int(spider.first('speed')) if spider else None)
    found = c.search(r'A battle-scarred veteran hits for (\d+d\d+) = (\d+) and\s*\n'
                     r'\s*a mean-looking mercenary for (\d+d\d+) = (\d+), both at depth (\d+)',
                     name='what the town hits for')
    if found:
        for dice_group, total_group, name in ((1, 2, 'battle-scarred veteran'),
                                              (3, 4, 'mean-looking mercenary')):
            entry = next((e for e in gd.load('monster.txt')[0] if e.value == name), None)
            blow = entry.all('blow')[0].split(':')[2] if entry else None
            c.emit('thin', found.start(dice_group), f'{name} blow', found[dice_group], blow)
            dice = re.fullmatch(r'(\d+)d(\d+)', found[dice_group])
            c.emit('thin', found.start(total_group), f'{name} worst blow',
                   int(found[total_group]), int(dice[1]) * int(dice[2]) if dice else None)
            c.emit('thin', found.start(5), f'{name} depth',
                   int(found[5]), int(entry.first('depth')) if entry else None)
    deaths = died_records()
    for pattern, run, fields in (
            (r'the dog took the last point \(qwen-flash-1#\d+\)', 'qwen-flash-1',
             {'killed_by': 'a scruffy little dog', 'death_depth': 0, 'character_level': 1}),
            (r'kobold walked up during them.*?\(sonnet-3#\d+\)', 'sonnet-3',
             {'killed_by': 'a small kobold', 'death_depth': 1, 'character_level': 1}),
            (r'the whole game and did not read until it was at 2 \(minimaxflash-2\.2#\d+\)',
             'minimaxflash-2.2',
             {'killed_by': 'a metallic green centipede', 'death_depth': 2,
              'character_level': 2})):
        found = c.search(pattern, re.S, name=f"the death of {run}")
        if not found:
            continue
        record = deaths.get(run, {})
        for field, claimed in fields.items():
            c.emit('death', found.start(), f'{run} {field.replace("_", " ")}',
                   claimed, record.get(field, f'no record for {run}'))
    found = c.search(r'CL1 Druid was clawed from (\d+) to 1', name="the druid's hit points")
    if found:
        c.emit('death', found.start(1), 'qwen-flash-1 max hit points',
               int(found[1]), (deaths.get('qwen-flash-1', {}).get('hp') or {}).get('max'))
    found = c.search(r'a (\d+)-hit-point Mage, blind', name="the mage's hit points")
    if found:
        c.emit('death', found.start(1), 'sonnet-3 max hit points',
               int(found[1]), (deaths.get('sonnet-3', {}).get('hp') or {}).get('max'))
    found = c.search(r'a CL2 Mage stood at 4 of (\d+) hit points', name='the gnome mage at four')
    if found:
        c.emit('death', found.start(1), 'minimaxflash-2.2 max hit points',
               int(found[1]), (deaths.get('minimaxflash-2.2', {}).get('hp') or {}).get('max'))


@extractor('staircases per level', minimum=8)
def staircases_per_level(c):
    """How many staircases a level is built with, and where they can sit.
    Section 8's answer to the sweep: there are three or four, in dead ends."""
    found = c.search(r'both ask for \*\*(\d+) or (\d+) down staircases and (\d+) or '
                     r'(\d+) up\*\*', name='the staircase counts')
    cave = gd.read_source('src/gen-cave.c') or ''
    if found and cave:
        for name in ('classic_gen', 'modified_gen'):
            body = re.search(rf'chunk \*{name}\(.*?\n\}}', cave, re.S)
            call = re.search(r'handle_level_stairs\([^;]*?rand_range\((\d+), (\d+)\),\s*'
                             r'rand_range\((\d+), (\d+)\)', body[0] if body else '', re.S)
            real = tuple(int(call[n]) for n in (1, 2, 3, 4)) if call else 'no such call'
            c.emit('staircases', found.start(1), f'{name} staircase counts (down, up)',
                   tuple(int(found[n]) for n in (1, 2, 3, 4)), real)
    profiles = {}
    for entry in gd.load('dungeon_profile.txt')[0]:
        profiles[entry.value.lower()] = {'alloc': int(entry.first('alloc') or 0),
                                         'min': int(entry.first('min-level') or 0)}
    found = c.search(r'`dungeon_profile\.txt`: modified (\d+), classic (\d+), cavern '
                     r'and the rest deeper or special', name='the profile weights')
    if found:
        for group, name in ((1, 'modified'), (2, 'classic')):
            c.emit('staircases', found.start(group), f'{name} profile alloc',
                   int(found[group]), profiles.get(name, {}).get('alloc'))
        deeper = {name for name, row in profiles.items()
                  if row['alloc'] > 0 and row['min'] > 1}
        c.emit('staircases', found.start(), 'every other profile with an alloc is '
               'deeper than depth 1', True,
               bool(deeper) and all(profiles[n]['min'] > 1 for n in deeper))
    found = c.search(r'at least `min\(width, height\) / 4` = (\d+) squares apart',
                     name='the minimum separation')
    if found:
        size = constants()
        height = size.get('world:dungeon-hgt')
        width = size.get('world:dungeon-wid')
        real = min(height, width) // 4 if height and width else 'no world size'
        c.emit('staircases', found.start(1), 'minimum separation of staircases',
               int(found[1]), real)
        c.emit('staircases', found.start(), 'the separation is a quarter of the '
               'smaller dimension', True,
               'MIN(c->width, c->height) / 4' in (cave or ''))
    found = c.search(r'square with \*\*(\w+) adjacent walls\*\* - three of its four '
                     r'orthogonal neighbours, diagonals not counted',
                     name='the three-wall rule')
    if found:
        util = gd.read_source('src/gen-util.c') or ''
        body = re.search(r'void alloc_stairs\(.*?\n\}', util, re.S)
        text = body[0] if body else ''
        c.emit('staircases', found.start(1), 'walls adjacent to a staircase',
               WORD_NUMBERS.get(found[1].lower(), found[1]),
               int(match[1]) if (match := re.search(r'\twalls = (\d+);', text)) else 'not found')
        # The diagonal count belongs to the player-placement fallback, not
        # here: the page said otherwise until this check said so.
        c.emit('staircases', found.start(), 'the walls are counted orthogonally '
               'only, and the count is relaxed when nothing is free', True,
               'square_num_walls_adjacent' in text
               and 'square_num_walls_diagonal' not in text
               and '--walls;' in text)


@extractor('experience ladder', minimum=24)
def experience_ladder(c):
    """What a character level costs, what a kill pays, and what pays nothing.
    Section 1's arithmetic, which "Depth is not the objective" leans on."""
    table = player_exp_table()
    found = c.search(r'cumulative and before that modifier[^:]*:\s*(?P<body>CL2 [^.]*)\.',
                     name='the experience ladder')
    if found and table:
        for match in re.finditer(r'CL(\d+) (\d+)', found['body']):
            level = int(match[1])
            real = table[level - 2] if 2 <= level <= len(table) + 1 else 'off the table'
            c.emit('experience', found.start('body') + match.start(2),
                   f'experience for CL{level}', int(match[2]), real)
    races = {e.value.lower(): int(e.first('exp')) for e in gd.load('p_race.txt')[0]}
    found = c.search(r'CL5 is therefore (\d+) experience for a Human, (\d+) for a '
                     r'Gnome or a Half-Troll, (\d+) for a High-Elf',
                     name='what CL5 costs each race')
    if found and table:
        for group, race in ((1, 'human'), (2, 'gnome'), (2, 'half-troll'), (3, 'high-elf')):
            c.emit('experience', found.start(group), f'CL5 experience for a {race}',
                   int(found[group]), table[3] * races[race] // 100)
    found = c.search(r'A small kobold \(`monster` experience (\d+), depth (\d+)\) pays '
                     r'(\d+) at CL1 but ([\d.]+) at CL4, so climbing CL1 to CL5 on '
                     r'depth-1 kobolds is about (\d+) kills, then (\d+), then (\d+), '
                     r'then (\d+): \*\*(\w+) kills, half of them',
                     name='the kill arithmetic')
    if found and table:
        kobold = monster_entry('small kobold')
        mexp = int(kobold.first('experience')) if kobold else 0
        depth = int(kobold.first('depth')) if kobold else 0
        c.emit('monster experience', found.start(1), 'small kobold experience',
               int(found[1]), mexp)
        c.emit('monster depth', found.start(2), 'small kobold depth', int(found[2]), depth)
        c.emit('experience', found.start(3), 'a small kobold at CL1 pays',
               int(found[3]), mexp * depth)
        c.emit('experience', found.start(4), 'a small kobold at CL4 pays',
               float(found[4]), mexp * depth / 4)
        counts = [int(found[n]) for n in (5, 6, 7, 8)]
        for index, claimed in enumerate(counts):
            level = index + 1
            needed = table[level - 1] - (table[level - 2] if level > 1 else 0)
            c.emit('experience', found.start(5 + index),
                   f'small kobolds to go from CL{level} to CL{level + 1}',
                   claimed, round(needed / (mexp * depth / level)))
        c.emit('experience', found.start(9), 'kobolds for the whole of CL1 to CL5',
               WORD_NUMBERS.get(found[9].lower(), found[9]), sum(counts))
        c.emit('experience', found.start(9), 'half of them is the last level',
               counts[-1] * 2, sum(counts))
    found = c.search(r'a soldier \(`monster` experience (\d+), depth (\d+)\) pays (\d+) at CL1',
                     name='what a soldier pays')
    if found:
        soldier = monster_entry('soldier')
        mexp = int(soldier.first('experience')) if soldier else 0
        depth = int(soldier.first('depth')) if soldier else 0
        c.emit('monster experience', found.start(1), 'soldier experience', int(found[1]), mexp)
        c.emit('monster depth', found.start(2), 'soldier depth', int(found[2]), depth)
        c.emit('experience', found.start(3), 'a soldier at CL1 pays', int(found[3]), mexp * depth)
    spells = spell_entries('Mage')
    found = c.search(r"A mage's five CL1 and CL2 spells pay (\d+), (\d+), (\d+), (\d+) and "
                     r"(\d+), so studying them and casting each once is (\d+) experience",
                     name='what a first cast pays')
    if found and spells:
        early = [(name, s) for name, s in spells.items() if s['level'] <= 2]
        for index, (name, spell) in enumerate(early[:5]):
            c.emit('spell experience', found.start(index + 1),
                   f'Mage {name} first-cast experience', int(found[index + 1]), spell['exp'])
        c.emit('spell experience', found.start(6), 'the five first casts together',
               int(found[6]), sum(s['exp'] for _, s in early[:5]))
        c.emit('spell experience', found.start(6), 'the mage has five spells at CL1-CL2',
               5, len(early))
    found = c.search(r'Magic Missile 1 sp \(dice `(\$\w+d\d+)` with the count '
                     r'`\(CL-1\)/5\+3`, so \*\*(\d+d\d+), (\d+) to (\d+) damage\*\*, '
                     r'all the way from CL1 to CL5 and (\d+d\d+) at CL6',
                     name="Magic Missile's dice")
    if found and spells.get('Magic Missile'):
        c.emit('spell damage', found.start(1), 'Magic Missile dice expression',
               found[1], spells['Magic Missile']['dice'])
        for group, level in ((2, 1), (5, 6)):
            c.emit('spell damage', found.start(group), f'Magic Missile dice at CL{level}',
                   found[group], missile_dice(spells, level))
        at_one = missile_dice(spells, 1) or '0d0'
        count, sides = (int(n) for n in at_one.split('d'))
        c.emit('spell damage', found.start(3), 'Magic Missile lowest damage at CL1',
               int(found[3]), count)
        c.emit('spell damage', found.start(4), 'Magic Missile highest damage at CL1',
               int(found[4]), count * sides)
    found = c.search(r'studying costs one action and nothing else - no mana, no experience, '
                     r'no gold \(`src/cmd-obj\.c do_cmd_study_spell\(\)`\)',
                     name='what studying costs')
    if found:
        source = gd.read_source('src/cmd-obj.c') or ''
        body = re.search(r'void do_cmd_study_spell\(struct command \*cmd\)\s*\{(.*?)\n\}',
                         source, re.S)
        text = body[1] if body else ''
        c.emit('source', found.start(), 'studying spends one move and nothing else',
               True, bool(body) and 'energy_use = z_info->move_energy' in text
               and not re.search(r'csp|exp_gain|au\b', text))


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
        match = re.match(r'^(Potion|Scroll|Wand|Staff|Ring|Rod|Amulet) of (.*)$', part)
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
        scope_at = offset + mention.end()
        # "A and B CL3": the level after B is A's too (nothing else is shared)
        shared, shared_at = scope, scope_at
        if re.fullmatch(r'\s*and\s*', scope) and index + 1 < len(mentions):
            shared, shared_at = own[index + 1], offset + mentions[index + 1].end()
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
            c.emit('spell level', pos, f'{cls} {real_name} level', int(level[1]), real[2],
                   covers=[(shared_at + level.start(1), shared_at + level.end(1))])
        elif head is not None and not re.search(r'CL ?\d', scope):
            c.emit('spell level', pos, f'{cls} {real_name} level (under "CL{head}:")',
                   head, real[2])
        if mana:
            c.emit('spell mana', pos, f'{cls} {real_name} mana', int(mana[1]), real[3],
                   covers=[(scope_at + mana.start(1), scope_at + mana.end(1))])
        if fail:
            c.emit('spell fail', pos, f'{cls} {real_name} base failure %', int(fail[1]), real[4],
                   covers=[(scope_at + fail.start(1), scope_at + fail.end(1))])


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


def worst_round(entry):
    """Every blow at its maximum: the most one monster turn of melee can do."""
    return sum(gd.dice_max(d) if d else 0 for d in blow_dice(entry))


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


def monster_flags(entry):
    """The monster's flags with its base's (`monster_base.txt`): ghosts are
    INVISIBLE and PASS_WALL there, not in the monster's own entry."""
    flags = set(entry.flags())
    for base in gd.load('monster_base.txt')[0]:
        if base.value == entry.first('base'):
            flags |= base.flags()
    return flags


def claim_monster(c, entry, label, scope, pos, base=None):
    """Claims in `scope`, the text after a monster's name. `base`, when given, is
    the page offset of `scope`, and lets each claim say which numbers it settles."""
    def at(found, group=0):
        if base is None or found is None:
            return ()
        return ((base + found.start(group), base + found.end(group)),)

    depth = re.search(r'\bDL ?(\d+)', scope)
    if depth:
        c.emit('monster depth', pos, f'{label} depth:', int(depth[1]), int(entry.first('depth')),
               covers=at(depth, 1))
    hp = re.search(r'(\d+) hp', scope)
    if hp:
        c.emit('monster hp', pos, f'{label} hit-points:', int(hp[1]), int(entry.first('hit-points')),
               covers=at(hp, 1))
    speed = re.search(r'\+(\d+)(?: speed)?\b', scope)
    if speed:
        c.emit('monster speed', pos, f'{label} speed: (+{speed[1]})', int(speed[1]),
               int(entry.first('speed')) - 110, covers=at(speed, 1))
    exp = re.search(r'(\d+) exp x level (\d+)', scope)
    if exp:
        c.emit('monster exp', pos, f'{label} experience:', int(exp[1]),
               int(entry.first('experience')), covers=at(exp, 1))
        c.emit('monster depth', pos, f'{label} depth: (as level)', int(exp[2]),
               int(entry.first('depth')), covers=at(exp, 2))
    scope_blows = re.sub(r'(?:swarm\*\* of|pack of up to) \d+d\d+', '', scope)
    dice = re.search(r'(?:(\d+) x )?(\d+d\d+)', scope_blows)
    real_blows = blow_dice(entry)
    if dice:
        count = int(dice[1]) if dice[1] else None
        have = real_blows.count(dice[2])
        c.emit('monster blow', pos, f'{label} blow dice {dice[2]}' +
               (f' x{count}' if count else ''), (count or 1, dice[2]),
               (have if count else min(have, 1), dice[2]),
               covers=at(re.search(re.escape(dice[0]), scope)))
    swarm = re.search(r'swarm\*\* of (\d+d\d+)', scope)
    if swarm:
        friends = (entry.first('friends') or '').split(':')
        c.emit('monster group', pos, f'{label} friends: dice', swarm[1],
               friends[1] if len(friends) > 1 else 'no friends: line')
    pack = re.search(r'pack of up to (\d+d\d+) more', scope)
    if pack:
        same = [v.split(':') for v in entry.all('friends') if v.split(':')[2].lower() == 'same']
        c.emit('monster group', pos, f'{label} friends: its own kind, dice', pack[1],
               same[0][1] if same else 'no friends: line', covers=at(pack, 1))
    upto = re.search(r'up to (\d+)( per its turn)?', scope)
    if upto and real_blows:
        top = worst_round(entry)
        factor = 1 if upto[2] else 1 + (int(entry.first('speed')) - 110) // 10
        c.emit('monster damage', pos, f'{label} worst melee per ' +
               ('monster' if upto[2] else 'player') + ' turn', int(upto[1]), top * factor,
               covers=at(upto, 1))
    freq = re.search(r'\b1 in (\d+)\b', scope)
    if freq:
        real = {int(entry.first(k)) for k in ('spell-freq', 'innate-freq') if entry.first(k)}
        c.emit('monster freq', pos, f'{label} casts 1 in N turns (spell-freq or innate-freq)',
               int(freq[1]), int(freq[1]) if int(freq[1]) in real else sorted(real) or 'no freq line',
               covers=at(freq))
    flags = monster_flags(entry)
    for word, (where, needle) in KEYWORDS.items():
        if word in scope.lower():
            if where == 'flag':
                real = needle in flags
            else:
                real = any(needle in value for _, value, _ in entry.fields)
            c.emit('monster trait', pos, f'{label} {word} ({needle})', True, real)
    for word, flag in VOLUME_TWO_FLAGS.items():
        if word in scope.lower():
            c.emit('monster trait', pos, f'{label} {word} ({flag})', True, flag in flags)
    if base is not None:
        have = set()
        for key, value, _ in entry.fields:
            if key in ('spells', 'blow', 'flags'):
                have.update(re.findall(r'[A-Z][A-Z_0-9]+', value))
        for token in re.findall(r'\b([A-Z]{2,}(?:_[A-Z0-9]+)+|[A-Z]{3,})\b', scope):
            c.emit('monster trait', pos, f'{label} has {token} (spell, blow or flag)', True,
                   token in have or token in flags)


VOLUME_TWO_FLAGS = {'passes walls': 'PASS_WALL', 'breeds': 'MULTIPLY'}


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


@extractor('citation shortcuts', minimum={1: 14, 2: 11}, volumes=(1, 2))
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


@extractor('source and field citations', minimum={1: 32, 2: 65}, volumes=(1, 2))
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
        elif re.fullmatch(r'[a-z]+(?:_[a-z]+)+', token) and token not in c.shortcuts:
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


@extractor('chapter references', minimum={1: 23, 2: 22}, volumes=(1, 2))
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


@extractor('quotations and document sections', minimum={1: 9, 2: 4}, volumes=(1, 2))
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
               f'({", ".join(names)})', True, bool(found_in), end=m.end(), covers=[m.span(1)])
    for m in c.finditer(r'`(playing|attack|command|birth)`,\s+([A-Z][A-Za-z ]+?)'
                        r'(?=[,:)]|\s+which)'):
        titles = rst_titles(source_text(m[1]) or '')
        for part in re.split(r' and ', m[2]):
            c.emit('document section', m.start(), f'{m[1]}.rst has a section titled {part!r}',
                   True, plain(part) in titles, end=m.end())


# =============================================================================
# Volume two: depth 5 to 20 (`manuals/INSTRUCTIONS_2.md`)
#
# The same method: the page makes a claim and names where it comes from, the
# grammar finds the claim and looks it up. What is new is what volume two says
# that volume one does not: counts over the whole monster list (every breather,
# every summoner, every unique in range), arithmetic over the game's own
# formulas (breath damage, teleport distance, hit points at a level) and what
# the strategy manual says against what the data says. `covers` lets a claim
# say which numbers on the page it settles, so `number_coverage` can say how
# many of the page's numbers nothing checks.
# =============================================================================

def real_monsters():
    """Every monster kind but the `<player>` placeholder, which is not a monster."""
    return [e for e in gd.load('monster.txt')[0] if e.value != '<player>']


def depth_of(entry):
    return int(entry.first('depth', '0'))


def spell_names(entry):
    names = []
    for value in entry.all('spells'):
        names += [part.strip() for part in value.split('|')]
    return names


def spell_table():
    return {e.value: e for e in gd.load('monster_spell.txt')[0]}


@functools.lru_cache(maxsize=1)
def projection_entries():
    """`projection.txt` with each `code:` given to the `name:` that FOLLOWS it
    (the file writes `code:` first, so the generic parser files it under the
    entry before)."""
    entries, code, current = [], None, None
    for number, raw in enumerate((gd.GAMEDATA / 'projection.txt').read_text().splitlines(), 1):
        if raw.startswith('code:'):
            code = raw[5:].strip()
        elif raw.startswith('name:'):
            current = gd.Entry('projection.txt', 'name', raw[5:], number)
            current.fields.append(('code', code, number))
            entries.append(current)
        elif current is not None and raw.strip() and not raw.startswith('#'):
            key, _, value = raw.partition(':')
            current.fields.append((key, value, number))
    return entries


def projection_by_code():
    return {e.first('code'): e for e in projection_entries()}


def projection_by_name():
    return {e.value.lower(): e for e in projection_entries()}


def breath_codes(entry):
    """The projection codes (`FIRE`, `ELEC`...) of the entry's breath spells."""
    spells = spell_table()
    codes = []
    for name in spell_names(entry):
        if name.startswith('BR_') and name in spells:
            codes.append(next(v for k, v, _ in spells[name].fields if k == 'effect').split(':')[1])
    return codes


def in_range(entry, low=5, high=20):
    return low <= depth_of(entry) <= high


def monster_table_two():
    """`monster_table` plus the short names the page uses for uniques
    (`Wormtongue` for `Wormtongue, Agent of Saruman`)."""
    table = monster_table()
    for key in list(table):
        if ',' in key:
            table.setdefault(key.split(',')[0], table[key])
    for short, full in MONSTER_SHORT.items():
        if full in table:
            table.setdefault(short, table[full])
    return table


def name_regex(table):
    names = sorted(table, key=len, reverse=True)
    return re.compile(r'(?<![\w])(' + '|'.join(re.escape(n) for n in names) + r')(?![\w])')


def table_cells(c, marker):
    """The first markdown table after `marker`: (header, rows), each a list of
    (text, start, end) cells with positions in the page."""
    start = c.text.find(marker)
    if start < 0:
        c.problem(f'the page no longer has {marker!r}')
        return [], []
    rows, pos = [], c.text.find('\n|', start)
    while pos >= 0:
        end = c.text.find('\n', pos + 1)
        end = len(c.text) if end < 0 else end
        line = c.text[pos + 1:end]
        if not line.startswith('|'):
            break
        offset, cells = pos + 2, []
        for part in line.split('|')[1:-1]:
            lead = len(part) - len(part.lstrip())
            text = part.strip()
            cells.append((text, offset + lead, offset + lead + len(text)))
            offset += len(part) + 1
        rows.append(cells)
        pos = end
    if not rows:
        return [], []
    body = [r for r in rows[1:] if not all(re.fullmatch(r':?-+:?', t) for t, _, _ in r)]
    return rows[0], body


def numbers_in(cell):
    """Spans of the numbers inside a cell (text, start, end)."""
    text, start, _ = cell
    return [(start + m.start(), start + m.end()) for m in re.finditer(r'\d+(?:\.\d+)?', text)]


def find_row_monster(c, cell, table):
    entry = find_monster(cell[0], table)
    if entry is None:
        c.emit('monster name', cell[1], f'{cell[0]} is a monster in monster.txt', True, False)
    return entry


@extractor('depth bands', minimum=17, volumes=(2,))
def depth_bands(c):
    header, rows = table_cells(c, 'kinds per depth band')
    bands = []
    for text, _, _ in header[1:]:
        match = re.fullmatch(r'(\d+)-(\d+)', text)
        bands.append((int(match[1]), int(match[2])) if match else None)
    monsters = real_monsters()
    for row in rows:
        label = row[0][0]
        for cell, band in zip(row[1:], bands):
            inside = [m for m in monsters if band[0] <= depth_of(m) <= band[1]]
            real = {'kinds': len(inside),
                    'breathe': sum(any(s.startswith('BR_') for s in spell_names(m)) for m in inside),
                    'summon': sum(any(s.startswith('S_') for s in spell_names(m)) for m in inside)
                    }.get(label, 'no such row')
            c.emit('depth band', cell[1], f'monsters of depth {band[0]}-{band[1]}: {label}',
                   int(cell[0]), real, covers=numbers_in(cell))
    spells = spell_table()
    breaths = [n for n in spells if n.startswith('BR_')]
    found = c.search(r'`hit:100`', name='the breath always hits claim')
    c.emit('breath', found.start() if found else 0, 'every BR_ spell has hit:100 (no armour roll)', True,
           all(spells[n].first('hit') == '100' for n in breaths), covers=[found.span()] if found else ())
    found = c.search(r'no `message-save` line on any `BR_` spell', name='breath has no saving throw')
    c.emit('breath', found.start() if found else 0, 'no BR_ spell has a message-save line (no saving throw)',
           True, not any(spells[n].has('message-save') for n in breaths))


def squash(text):
    """Chapter text for comparing: no markdown, `x` for the multiplication sign."""
    return re.sub(r'\s+', ' ', plain(text).replace('×', 'x').replace('−', '-'))


def chapter15_depth_gates():
    """`{depth: (required, [(anchor name, depth)])}` from DEPTH-02's table."""
    fifteen = gd.read_chapter(15) or ''
    block = fifteen[fifteen.find('DEPTH-02'):fifteen.find('DEPTH-03')]
    gates = {}
    for m in re.finditer(r'^>?\s*\| (\d+) \| (.*?) \| (.*?) \|\s*$', block, re.M):
        anchors = [(plain(a[0]), int(a[1])) for a in re.findall(r'([^,()]+?) \(D(\d+)', m[3])]
        gates[int(m[1])] = (squash(m[2]), anchors)
    return gates


@extractor('kit gates', minimum=21, volumes=(2,))
def kit_gates(c):
    _, rows = table_cells(c, "Rows in this volume's range")
    gates, table = chapter15_depth_gates(), monster_table_two()
    for row in rows:
        depth_cell, need_cell, anchor_cell = row[:3]
        depth = int(depth_cell[0])
        said, anchors = gates.get(depth, (None, []))
        c.emit('gate', depth_cell[1], f'c15 DEPTH-02 has a row for depth {depth}', True,
               said is not None, covers=numbers_in(depth_cell))
        c.emit('gate', need_cell[1], f'depth {depth} gate requirement is c15 DEPTH-02\'s',
               squash(need_cell[0]), said, covers=numbers_in(need_cell))
        mine = [(plain(a[0]), int(a[1])) for a in re.findall(r'([^,()]+?) \(DL(\d+)\)', anchor_cell[0])]
        c.emit('gate', anchor_cell[1], f'depth {depth} anchor monsters (name, depth) are c15 DEPTH-02\'s',
               mine, anchors)
        for name, said_depth in anchors:
            entry = find_monster(name, table)
            c.emit('gate', anchor_cell[1], f'c15 DEPTH-02 anchor {name}: depth', said_depth,
                   depth_of(entry) if entry else 'no such monster')
    carry = c.search(r'carry (\d+)\+ and leave rather than trade', name='the cure potions to carry')
    if carry:
        c.emit('gate', carry.start(), 'cure potions to carry is the c15 DEPTH-02 DL5 figure', int(carry[1]),
               int(re.search(r'(\d+)\+ cure potions', gates[5][0])[1]), covers=[carry.span(1)])
    found = c.search(r'Cure Light Wounds heals (\d+) \(`object`\), under his (\d+)',
                     name='the Cure Light Wounds against Bullroarer line')
    if found:
        potion = find_object('Cure Light Wounds', types=['potion'])
        c.emit('gate', found.start(), 'Cure Light Wounds heals', int(found[1]),
               int(potion.first('dice')) if potion.first('dice') else None, covers=[found.span(1)])
        bull = find_monster('Bullroarer', table)
        top = worst_round(bull) * (1 + (int(bull.first('speed')) - 110) // 10)
        c.emit('gate', found.start(), 'Bullroarer worst melee per player turn', int(found[2]), top,
               covers=[found.span(2)])


    m = c.search(r'the chapter\'s "\+(\d+)" for him is \+(\d+) in `monster`', name='the Bullroarer speed disagreement')
    if m:
        bull = find_monster('Bullroarer', table)
        fifteen = gd.read_chapter(15) or ''
        c.emit('manual says', m.start(), 'c15 DEPTH-02 gives Bullroarer this speed', int(m[1]),
               int(re.search(r'Bullroarer \(D5, \+(\d+)\)', fifteen)[1]), covers=[m.span(1)])
        c.emit('gate', m.start(), 'Bullroarer speed in monster.txt', int(m[2]),
               int(bull.first('speed')) - 110, covers=[m.span(2)])
    m = c.search(r'The next gate, DL(\d+), wants (?P<need>.*?) \(c15 DEPTH-02\)', name='the DL25 gate')
    if m:
        said = squash(m['need']).replace(' and ', '; ')
        c.emit('gate', m.start(), 'depth 25 gate requirement is c15 DEPTH-02\'s', said,
               gates.get(int(m[1]), ('no such gate',))[0], covers=[m.span(1), m.span('need')])


@extractor('monster mentions', minimum=42, volumes=(2,))
def monster_mentions(c):
    """`**name** (DL5, +10, 60 hp, ...)`: every figure in the parentheses is looked up."""
    table = monster_table_two()
    for m in c.finditer(r'\*\*([^*]+?)\*\* \((DL\d+[^)]*)\)'):
        for name in [n.strip() for n in re.split(r' and |, ', m[1])]:
            entry = find_monster(name, table)
            if entry is None:
                c.emit('monster name', m.start(), f'{name} is a monster in monster.txt', True, False)
                continue
            claim_monster(c, entry, name, m[2], m.start(), base=m.start(2))


@extractor('monster depths in lists', minimum=24, volumes=(2,))
def monster_depth_lists(c):
    """`Orfax and tengu (DL10), quasit (DL16)`: each name's depth."""
    table = monster_table_two()
    names = '|'.join(re.escape(n) for n in sorted(table, key=len, reverse=True))
    text = plain_keep(c.text)
    chain = re.compile(rf'(?<![\w])((?:{names})(?:(?:, and |, | and )(?:{names}))*) \(dl(\d+)\)')
    inner = name_regex(table)
    for m in chain.finditer(text):
        for name in inner.finditer(m[1]):
            entry = find_monster(name[1], table)
            c.emit('monster depth', m.start(), f'{name[1]} depth (in a list)', int(m[2]),
                   depth_of(entry), covers=[m.span(2)])


def monster_vocabulary():
    """Every spell, blow effect and flag a monster entry can carry."""
    words = set()
    for entry in gd.load('monster.txt')[0] + gd.load('monster_base.txt')[0]:
        for key, value, _ in entry.fields:
            if key in ('spells', 'blow', 'flags'):
                words.update(re.findall(r'[A-Z][A-Z_0-9]+', value))
    return words


@extractor('monster lists under a spell or blow', minimum=13, volumes=(2,))
def monster_token_lists(c):
    """`TELE_TO casters pull you back: Orfax and tengu`: every name after the colon
    has that spell, blow or flag."""
    table = monster_table_two()
    inner = name_regex(table)
    vocabulary = monster_vocabulary()
    for word in c.finditer(r'\b([A-Z][A-Z_0-9]{2,})\b'):
        token = word[1]
        if token not in vocabulary:
            continue
        m = re.match(r'[^:.\n]{0,70}: ([^.\n]+)', c.text[word.end():])
        if not m:
            continue
        for name in inner.finditer(plain_keep(m[1])):
            entry = find_monster(name[1], table)
            have = set()
            for key, value, _ in entry.fields:
                if key in ('spells', 'blow', 'flags'):
                    have.update(re.findall(r'[A-Z][A-Z_0-9]+', value))
            c.emit('monster trait', word.start(), f'{name[1]} has {token}', True,
                   token in have or token in monster_flags(entry))


def spell_max_damage(spell, power):
    """The most a monster spell does at spell power `power`: the first damaging
    effect's dice, with `expr:` variables worked out left to right."""
    fields, damaging = spell.fields, ('DAMAGE', 'BOLT', 'BALL', 'BOLT_OR_BEAM', 'ARC', 'STRIKE')
    for index, (key, value, _) in enumerate(fields):
        if key != 'effect' or value.split(':')[0] not in damaging:
            continue
        dice, values = None, {}
        for key2, value2, _ in fields[index + 1:]:
            if key2 == 'effect':
                break
            if key2 == 'dice':
                dice = value2
            elif key2 == 'expr':
                var, base_name, ops = value2.split(':', 2)
                number = power if base_name == 'SPELL_POWER' else 0
                tokens = ops.split()
                for op, operand in zip(tokens[0::2], tokens[1::2]):
                    operand = int(operand)
                    number = {'/': lambda a, b: a // b, '*': lambda a, b: a * b,
                              '+': lambda a, b: a + b, '-': lambda a, b: a - b}[op](number, operand)
                values[var] = number
        if dice is None:
            return None
        for var, number in values.items():
            dice = dice.replace(f'${var}', str(number))
        match = re.fullmatch(r'(?:(\d+)\+)?(\d+)d(\d+)', dice)
        if not match:
            return None
        return int(match[1] or 0) + int(match[2]) * int(match[3])
    return None


@extractor('monster spell damage', minimum=11, volumes=(2,))
def monster_spell_damage(c):
    found = c.search(r'Worst spells at the native depth: (?P<body>[^.]*?)\. ', re.S, 'the worst spells list')
    if not found:
        return
    table, spells = monster_table_two(), spell_table()
    body, offset = found['body'], found.start('body')
    position = 0
    for group in body.split('; '):
        start = offset + body.index(group, position)
        position = body.index(group, position) + len(group)
        name = re.match(r'^(.*?) (?:[A-Z]{2}_[A-Z]+|WOUND) up to', group)
        entry = find_monster(name[1], table) if name else None
        if entry is None:
            c.problem(f'cannot read a monster in {group!r}', start)
            continue
        power = int(entry.first('spell-power') or entry.first('depth'))
        for m in re.finditer(r'\b([A-Z]{2}_[A-Z]+|WOUND) up to (\d+)', group):
            real = spell_max_damage(spells[m[1]], power) if m[1] in spells else None
            c.emit('spell damage', start + m.start(), f'{name[1]} {m[1]} at spell power {power}: '
                   f'maximum damage', int(m[2]), real, covers=[(start + m.start(2), start + m.end(2))])
        stated = re.search(r'\(power (\d+)\)', group)
        if stated:
            c.emit('spell damage', start, f'{name[1]} spell power', int(stated[1]), power,
                   covers=[(start + stated.start(1), start + stated.end(1))])
    formula = c.search(r'`BO_FIRE` is `\$B\+(\d+d\d+)` with B = power / (\d+)', name='the BO_FIRE formula')
    if formula:
        fire = spells['BO_FIRE']
        dice = [v for k, v, _ in fire.fields if k == 'dice'][0]
        expr = [v for k, v, _ in fire.fields if k == 'expr'][0]
        c.emit('spell damage', formula.start(), 'BO_FIRE dice', f'$B+{formula[1]}', dice,
               covers=[formula.span(1), formula.span(2)])
        c.emit('spell damage', formula.start(), 'BO_FIRE B = power / N', f'B:SPELL_POWER:/ {formula[2]}', expr)
    reserve = c.search(r'(\d+) \+ the (\d+)-point reserve \(c15 `K_HP_RESERVE`, max\(20, 10%\)\) = (\d+), so (\d+) is the '
                       r'round number above', name='the druid bolt plus reserve sum')
    if reserve:
        druid = table[plain('druid')]
        bolt = spell_max_damage(spells['BO_FIRE'], int(druid.first('depth')))
        c.emit('spell damage', reserve.start(), 'druid BO_FIRE plus reserve is the sum', int(reserve[3]),
               bolt + int(reserve[2]), covers=[reserve.span(1), reserve.span(2), reserve.span(3)])
        c.emit('spell damage', reserve.start(), 'the druid bolt in the sum', int(reserve[1]), bolt)
        gate = chapter15_depth_gates()[15][0]
        c.emit('gate', reserve.start(), 'the round number is the c15 DEPTH-02 hit points for DL15',
               int(reserve[4]), int(re.match(r'(\d+) max hp', gate)[1]), covers=[reserve.span(4)])
        c.emit('gate', reserve.start(), 'the round number is above the bolt plus the reserve', True,
               int(reserve[4]) > int(reserve[3]))


STORE_NAMES = {'Alchemist': 'STORE_ALCHEMY', 'Magic shop': 'STORE_MAGIC', 'General Store': 'STORE_GENERAL',
               'Bookseller': 'STORE_BOOK'}


def object_table_two(c, marker, label):
    """A table of objects: `cost:`, `level:`, found from (the `alloc:` minimum), where
    it is sold (`Alchemist, sometimes`, `no store`) and, if there is a column for it,
    how far it teleports."""
    header, rows = table_cells(c, marker)
    column = {}
    for index, (text, _, _) in enumerate(header):
        low = text.lower().replace('`', '')
        for word in ('cost', 'level', 'found', 'where', 'distance'):
            if low.startswith(word):
                column[word] = index
    for needed in ('cost', 'level', 'found', 'where'):
        if needed not in column:
            c.problem(f'the {label} table has no {needed!r} column')
            return
    all_stores = {s['key']: s for s in stores()}
    for row in rows:
        names = expand_names(row[0][0])
        for word, field_name in (('cost', 'cost:'), ('level', 'level:'), ('found', 'alloc: shallowest depth')):
            cell = row[column[word]]
            values = [v.strip() for v in cell[0].split(' / ')]
            if len(values) != len(names):
                c.problem(f'{row[0][0]!r}: {len(names)} names but {len(values)} values in {word}', cell[1])
                continue
            for (kind, name), value in zip(names, values):
                obj = find_object(name, types=[kind] if kind else None)
                if obj is None:
                    c.emit('table', cell[1], f'{name}: no such object', value, 'absent')
                    continue
                real = {'cost': lambda: int(obj.first('cost')), 'level': lambda: int(obj.first('level')),
                        'found': lambda: alloc_min(obj)}[word]()
                c.emit(f'{label} {word}', cell[1], f'{obj.type} {obj.name} {field_name}', int(value), real,
                       covers=numbers_in(cell))
        where = row[column['where']]
        for kind, name in names:
            obj = find_object(name, types=[kind] if kind else None)
            if obj is None:
                continue
            sells = []
            for store_key, entry in all_stores.items():
                for how in ('always', 'normal'):
                    if any(t == obj.type and n.lower() == obj.name.lower() for t, n in entry[how]):
                        sells.append((store_key, how))
            said = re.match(r'^(Alchemist|Magic shop|General Store|Bookseller), (always|sometimes)$', where[0])
            if said:
                want = (STORE_NAMES[said[1]], 'always' if said[2] == 'always' else 'normal')
                c.emit(f'{label} where', where[1], f'{obj.name} is sold by {said[1]} ({said[2]}) in store.txt',
                       True, want in sells)
            elif where[0] == 'no store':
                c.emit(f'{label} where', where[1], f'{obj.name} is in no store.txt list', [], sells)
            else:
                c.problem(f'cannot read where {where[0]!r}', where[1])
        if 'distance' in column:
            cell = row[column['distance']]
            obj = find_object(names[0][1], types=[names[0][0]] if names[0][0] else None)
            dice = obj.first('dice') if obj else None
            if re.fullmatch(r'\d+', cell[0]):
                c.emit(f'{label} distance', cell[1], f'{obj.name} teleports (dice:)', int(cell[0]),
                       int(dice) if dice and dice.isdigit() else dice, covers=numbers_in(cell))
            elif re.match(r'\d+% of the span', cell[0]):
                real = re.fullmatch(r'M(\d+)', dice or '')
                c.emit(f'{label} distance', cell[1], f'{obj.name} teleports (dice: M)',
                       int(re.match(r'(\d+)', cell[0])[1]), int(real[1]) if real else dice,
                       covers=numbers_in(cell))


def extract_energy_table():
    """The 200 entries of `extract_energy[]` in src/game-world.c."""
    source = gd.read_source('src/game-world.c') or ''
    body = re.search(r'extract_energy\[200\]\s*=\s*\{(.*?)\};', source, re.S)
    if not body:
        return []
    return [int(n) for n in re.findall(r'\b(\d+),', re.sub(r'/\*.*?\*/', '', body[1]))]


@extractor('escape table', minimum=18, volumes=(2,))
def escape_table(c):
    object_table_two(c, 'FACT (`src/effect-handler-general.c TELEPORT`', 'escape')


@extractor('teleport arithmetic', minimum=27, volumes=(2,))
def teleport_arithmetic(c):
    constants_, handler = constants(), gd.read_source('src/effect-handler-general.c') or ''
    phase = find_object('Phase Door', types=['scroll'])
    found = c.search(r'lands you (\d+) to (\d+) squares away', name='the Phase Door distance')
    if found:
        dis = int(phase.first('dice'))
        spread = dis // 4 - 1
        c.emit('teleport', found.start(), 'Phase Door landing distance, low', int(found[1]), dis - spread,
               covers=[found.span(1)])
        c.emit('teleport', found.start(), 'Phase Door landing distance, high', int(found[2]), dis + spread,
               covers=[found.span(2)])
        c.emit('source', found.start(), 'TELEPORT randomises the distance by randint0(dis / 4)', True,
               'randint0(dis / 4)' in handler)
    energy = extract_energy_table()
    dis = int(phase.first('dice'))
    first = c.search(r'a \+(\d+) monster has energy (\d+) to your (\d+)', name='the energy of a +10 monster')
    if first:
        c.emit('teleport', first.start(), f'energy at +{first[1]}', int(first[2]), energy[110 + int(first[1])],
               covers=[first.span(1), first.span(2)])
        c.emit('teleport', first.start(), 'energy at normal speed', int(first[3]), energy[110],
               covers=[first.span(3)])
    m = c.search(r'closes it in (\d+) of your turns, a \+(\d+) monster \(energy (\d+)\) in (\d+)',
                 name='the turns to close a phase')
    if m and first:
        def turns(speed):
            return -(-dis * energy[110] // energy[110 + speed])
        c.emit('teleport', m.start(), f'turns for a +{first[1]} monster to cross {dis} squares',
               int(m[1]), turns(int(first[1])), covers=[m.span(1)])
        c.emit('teleport', m.start(), f'turns for a +{m[2]} monster to cross {dis} squares',
               int(m[4]), turns(int(m[2])), covers=[m.span(2), m.span(4)])
        c.emit('teleport', m.start(), f'energy at +{m[2]}', int(m[3]), energy[110 + int(m[2])],
               covers=[m.span(3)])
    scroll = find_object('Teleportation', types=['scroll'])
    m = c.search(r'(\d+)% of the longer of your farthest vertical and farthest horizontal edge distance',
                 name='the Teleportation distance')
    if m:
        c.emit('teleport', m.start(), 'Teleportation distance percentage (dice: M)', int(m[1]),
               int(scroll.first('dice')[1:]), covers=[m.span(1)])
    m = c.search(r'full (\d+) x (\d+) level \(`constants`\) that is (\d+), then a random quarter either '
                 r'way: (\d+) to (\d+) squares', name='the middle-of-the-level teleport')
    if m:
        wid, hgt = constants_.get('world:dungeon-wid'), constants_.get('world:dungeon-hgt')
        c.emit('teleport', m.start(), 'level width (constants)', int(m[1]), wid, covers=[m.span(1)])
        c.emit('teleport', m.start(), 'level height (constants)', int(m[2]), hgt, covers=[m.span(2)])
        span = max(wid - wid // 2, wid // 2, hgt - hgt // 2, hgt // 2)
        dis = span * int(scroll.first('dice')[1:]) // 100
        c.emit('teleport', m.start(), 'teleport distance from the middle', int(m[3]), dis, covers=[m.span(3)])
        low, high = dis - (dis // 4 - 1), dis + (dis // 4 - 1)
        c.emit('teleport', m.start(), 'teleport distance range, low', int(m[4]), low, covers=[m.span(4)])
        c.emit('teleport', m.start(), 'teleport distance range, high', int(m[5]), high, covers=[m.span(5)])
        c.emit('source', m.start(), 'TELEPORT scales by the larger edge distance', True,
               'MAX(vertical, horizontal)' in handler and 'cave->height - start.y' in handler)
    m = c.search(r'\((\d+)\+d(\d+) charges\)', name='the staff charges')
    if m:
        staff = find_object('Teleportation', types=['staff'])
        c.emit('teleport', m.start(), 'Staff of Teleportation charges:', f'{m[1]}+d{m[2]}',
               staff.first('charges'), covers=[m.span(1), m.span(2)])
    m = c.search(r'drops you to (\d+) levels below your deepest: deepest DL(\d+), you land on DL(\d+)', name='Deep Descent from DL15')
    if m:
        skip = constants_.get('world:stair-skip')
        c.emit('teleport', m.start(), 'Deep Descent lands this far below your deepest', int(m[1]),
               4 // skip + 1, covers=[m.span(1)])
        c.emit('teleport', m.start(), 'Deep Descent from DL15 lands on DL20', int(m[3]),
               int(m[2]) + 4 // skip + 1, covers=[m.span(2), m.span(3)])
    m = c.search(r'goes up or down at random, even odds; it cannot go up from the town', name='Teleport Level')
    if m:
        c.emit('source', m.start(), 'TELEPORT_LEVEL is a coin flip when both ways are legal', True,
               'randint0(100) < 50' in handler)
        c.emit('source', m.start(), 'TELEPORT_LEVEL cannot go up in town', True,
               '|| !player->depth' in handler)
    m = c.search(r'a nexus resist saves you', name='the nexus resist')
    if m:
        c.emit('source', m.start(), 'a monster TELEPORT_LEVEL is resisted with nexus', True,
               'player_resists(player, ELEM_NEXUS)' in handler)
    m = c.search(r'anti-teleportation curse \((?P<types>[^)]*), `curse`\)', name='the anti-teleportation curse')
    if m:
        curse = next((e for e in gd.load('curse.txt')[0] if e.value == 'anti-teleportation'), None)
        real = set(curse.all('type')) if curse else set()
        said = set()
        for word in re.split(r',\s*| or ', m['types']):
            said |= {'armour': {'soft armor', 'hard armor', 'dragon armor'}}.get(word.strip(), {word.strip()})
        c.emit('curse', m.start(), 'anti-teleportation curse is on these item types', sorted(said), sorted(real))
        c.emit('curse', m.start(), 'anti-teleportation curse is the NO_TELEPORT flag', True,
               bool(curse and 'NO_TELEPORT' in curse.flags()))
        c.emit('source', m.start(), 'both teleports say "Teleportation forbidden!" under the curse', True,
               handler.count('Teleportation forbidden!') >= 3 and 'OF_NO_TELEPORT' in handler)
    m = c.search(r'the game learns the curse only when it takes effect \(`id-type:on effect`, `object_property`\)',
                 name='when the curse is learned')
    if m:
        ban = next((e for e in gd.load('object_property.txt')[0]
                    if e.first('code') == 'NO_TELEPORT'), None)
        c.emit('curse', m.start(), 'NO_TELEPORT is identified on effect (object_property.txt)', 'on effect',
               ban.first('id-type') if ban else None)
    m = c.search(r'only a teleport of (\d+) or less works', name='the no-teleport square rule')
    if m:
        c.emit('source', m.start(), 'a no-teleport square blocks a teleport longer than 10', True,
               f'((dis > {m[1]}) || (dis == 0))' in handler, covers=[m.span(1)])
    m = c.search(r'gauntlet level \(found from DL(\d+), `dungeon_profile`\)', name='the gauntlet level')
    if m:
        profile = next((e for e in gd.load('dungeon_profile.txt')[0] if e.value == 'gauntlet'), None)
        c.emit('teleport', m.start(), 'gauntlet min-level', int(m[1]),
               int(profile.first('min-level')) if profile else None, covers=[m.span(1)])
        generate = gd.read_source('src/gen-cave.c') or ''
        c.emit('source', m.start(), 'the gauntlet level is marked SQUARE_NO_TELEPORT', True,
               'SQUARE_NO_TELEPORT' in generate)


def handler_body(code):
    source = gd.read_source('src/project-player.c') or ''
    found = re.search(rf'static int project_player_handler_{code}\(.*?\n}}\n', source, re.S)
    return found.group(0) if found else ''


SIDE_EFFECTS = {'destroys pack items': 'inven_damage', 'poisons': 'TMD_POISONED',
                'blinds': 'TMD_BLIND', 'stuns': 'TMD_STUN', 'cuts': 'TMD_CUT'}


@extractor('breath elements', minimum=48, volumes=(2,))
def breath_elements(c):
    _, rows = table_cells(c, 'FACT: damage = the breather')
    by_name = projection_by_name()
    adjust = gd.read_source('src/project-player.c') or ''
    seen = set()
    for row in rows:
        for name in row[0][0].split(', '):
            element = by_name.get(name.lower())
            if element is None:
                c.emit('breath', row[0][1], f'{name} is a projection in projection.txt', True, False)
                continue
            seen.add(name.lower())
            for index, field_name in ((1, 'divisor'), (2, 'damage-cap')):
                cell = row[index]
                c.emit('breath element', cell[1], f'{element.value} {field_name}', int(cell[0]),
                       int(element.first(field_name)), covers=numbers_in(cell))
            note = row[3]
            body = handler_body(element.first('code'))
            for word, token in SIDE_EFFECTS.items():
                if word in note[0]:
                    c.emit('breath element', note[1], f'{element.value} breath: {word} ({token} in its handler)',
                           True, token in body)
            if 'halved' in note[0] and name.lower() == 'acid':
                c.emit('breath element', note[1], 'acid is halved when it eats a piece of armour (minus_ac)',
                       True, 'type == PROJ_ACID && p && minus_ac(p)' in adjust)
    used = {by_name[projection_name(code)].value for m in real_monsters() if in_range(m, 5, 24)
            for code in breath_codes(m)}
    c.emit('breath element', 0, 'every element a monster of DL5-24 breathes is in the table', [],
           sorted(used - seen))
    source = gd.read_source('src/mon-spell.c') or ''
    found = c.search(r'damage = the breather\'s current hit points / divisor, capped', name='the breath formula')
    if found:
        c.emit('source', found.start(), 'breath_dam: hp / divisor, capped by damage_cap', True,
               'dam = hp / element->divisor;' in source and 'if (dam > element->damage_cap)' in source)
    m = c.search(r'acid, lightning, fire, cold and poison are (\d+)/(\d+) per resist level; light, dark, '
                 r'sound and shards (\d+)/\((\d+\+\d+d\d+)\) per level', name='the resist factors')
    if m:
        for name in ('acid', 'lightning', 'fire', 'cold', 'poison'):
            p = by_name[name]
            c.emit('resist', m.start(), f'{name} resist is {m[1]}/{m[2]} per level',
                   (int(m[1]), int(m[2])), (int(p.first('numerator')), int(p.first('denominator'))),
                   covers=[m.span(1), m.span(2)])
        for name in ('light', 'dark', 'sound', 'shards'):
            p = by_name[name]
            c.emit('resist', m.start(), f'{name} resist is {m[3]}/({m[4]}) per level',
                   (int(m[3]), m[4]), (int(p.first('numerator')), p.first('denominator')),
                   covers=[m.span(3), m.span(4)])
    m = c.search(r'adds one level and no more than (\d+) count', name='the temporary resist cap')
    if m:
        calcs = gd.read_source('src/player-calcs.c') or ''
        cap = re.search(r'temp_resist\]\.res_level\s*<\s*(\d+)\)\s*\{\s*state->el_info\[.*?\]\.res_level\+\+',
                        calcs, re.S)
        c.emit('source', m.start(), 'a timed resist adds one level only below the cap (player-calcs.c)',
               int(m[1]), int(cap[1]) if cap else None, covers=[m.span(1)])
    m = c.search(r'potion alone is (\d+)/(\d+) and a permanent resist plus the potion is (\d+)/(\d+)',
                 name='one and two resist levels')
    if m:
        acid = by_name['acid']
        one = (int(acid.first('numerator')), int(acid.first('denominator')))
        c.emit('resist', m.start(), 'one level of 1/3 is 1/3, two are 1/9',
               (int(m[1]), int(m[2]), int(m[3]), int(m[4])), (one[0], one[1], one[0] ** 2, one[1] ** 2),
               covers=[m.span(i) for i in (1, 2, 3, 4)])
    m = c.search(r'is a (\d+)-degree cone \(`BREATH:\.\.\.:(\d+):(\d+)`\), full strength out to (\d+) squares '
                 r'and then (\d+)/\(distance \+ (\d+)\) of it: (\d+)% at (\d+) squares, (\d+)% at (\d+)',
                 name='the breath falloff')
    if m:
        spells = spell_table()
        params = {tuple(next(v for k, v, _ in spells[n].fields if k == 'effect').split(':')[2:4])
                  for n in spells if n.startswith('BR_')}
        c.emit('breath', m.start(), 'every BR_ spell is BREATH:X:radius:degrees', {(m[2], m[3])}, params,
               covers=[m.span(2), m.span(3)])
        c.emit('breath', m.start(), 'the cone is this many degrees', int(m[1]), int(m[3]), covers=[m.span(1)])
        diameter = 4 * 60 // int(m[1])
        c.emit('breath', m.start(), 'full strength out to diameter - 1 squares', int(m[4]), diameter - 1,
               covers=[m.span(4)])
        c.emit('breath', m.start(), 'then diameter / (distance + 1) of the strength', (int(m[5]), int(m[6])),
               (diameter, 1), covers=[m.span(5), m.span(6)])
        for share_at, dist_at in ((7, 8), (9, 10)):
            c.emit('breath', m.start(), f'strength at {m[dist_at]} squares (%)', int(m[share_at]),
                   round(100 * diameter / (int(m[dist_at]) + 1)), covers=[m.span(share_at), m.span(dist_at)])
        project = (gd.read_source('src/project.c') or '') + (gd.read_source('src/effect-handler-attack.c') or '')
        c.emit('source', m.start(), 'BREATH starts at diameter 4 and widens by 60 / degrees; project() '
               'divides by distance + 1', True,
               'int diameter_of_source = 4;' in project and 'diameter_of_source * 60 / degrees_of_arc' in project
               and '(diameter_of_source * dam) / (i + 1)' in project)
    m = c.search(r'doubled at the monster\'s preferred range', name='the doubled breath chance')
    if m:
        c.emit('source', m.start(), 'monster_can_cast doubles the chance at best_range', True,
               'chance *= 2;' in (gd.read_source('src/mon-attack.c') or '') and
               'tdist == mon->best_range' in (gd.read_source('src/mon-attack.c') or ''))
        header_text = re.sub(r'\s*#\s*', ' ', (gd.GAMEDATA / 'monster.txt').read_text())
        c.emit('docs', m.start(), 'monster.txt: innate-freq is the number of monster turns on average', True,
               'the number of monster turns, on average, before the monster will perform' in header_text)


def projection_name(code):
    return projection_by_code()[code].value.lower()


@extractor('breather table', minimum=115, volumes=(2,))
def breather_table(c):
    _, rows = table_cells(c, 'Every breather of DL5-20')
    table = monster_table_two()
    listed = set()
    for row in rows:
        name, depth, hp, element, breath, freq = row[:6]
        entry = find_row_monster(c, name, table)
        if entry is None:
            continue
        listed.add(entry.value)
        c.emit('breather', depth[1], f'{name[0]} depth', int(depth[0]), depth_of(entry), covers=numbers_in(depth))
        c.emit('breather', hp[1], f'{name[0]} hit-points', int(hp[0]), int(entry.first('hit-points')),
               covers=numbers_in(hp))
        said = sorted(plain(e) for e in element[0].split(', '))
        real = sorted(projection_name(code) for code in breath_codes(entry))
        c.emit('breather', element[1], f'{name[0]} breathes', said, real)
        damages = set()
        for code in breath_codes(entry):
            p = projection_by_code()[code]
            damages.add(min(int(entry.first('hit-points')) // int(p.first('divisor')), int(p.first('damage-cap'))))
        c.emit('breather', breath[1], f'{name[0]} breath at full hit points', int(breath[0]),
               damages.pop() if len(damages) == 1 else sorted(damages), covers=numbers_in(breath))
        real_freq = entry.first('innate-freq')
        c.emit('breather', freq[1], f'{name[0]} innate-freq (1 in N)', int(freq[0]),
               int(real_freq) if real_freq else None, covers=numbers_in(freq))
    real = {m.value for m in real_monsters() if in_range(m) and breath_codes(m)}
    c.emit('breather', 0, 'every breather of depth 5-20 is in the table', [], sorted(real - listed))
    c.emit('breather', 0, 'the table lists only breathers of depth 5-20', [], sorted(listed - real))
    found = c.search(r'each has (\d+d\d+) companions of its kind \(`friends`, `monster`\)',
                     name='hound companions')
    if found:
        hounds = [m for m in real_monsters() if in_range(m) and m.value.endswith(' hound')]
        have = {next((v.split(':')[1] for v in m.all('friends') if v.split(':')[2].lower() == 'same'), None)
                for m in hounds if breath_codes(m)}
        c.emit('breather', found.start(), 'every breathing hound has these companions', {found[1]}, have,
               covers=[found.span(1)])
    found = c.search(r'The largest breath in the range is the chimaera\'s (\d+); the baby dragons\' (\d+) to '
                     r'(\d+)', name='largest breath')
    if found:
        rows_by = {plain(r[0][0]): int(r[4][0]) for r in rows}
        c.emit('breather', found.start(), 'the largest breath in the table', int(found[1]),
               max(rows_by.values()), covers=[found.span(1)])
        c.emit('breather', found.start(), 'the chimaera has the largest breath', 'chimaera',
               max(rows_by, key=rows_by.get))
        babies = [v for k, v in rows_by.items() if k.startswith('baby ') and 'multi' not in k and 'gold' not in k]
        c.emit('breather', found.start(), 'baby dragons breathe this much, low', int(found[2]), min(babies),
               covers=[found.span(2)])
        c.emit('breather', found.start(), 'baby multi-hued dragon breathes this much, high', int(found[3]),
               rows_by['baby multi-hued dragon'], covers=[found.span(3)])


@extractor('summoner table', minimum=56, volumes=(2,))
def summoner_table(c):
    _, rows = table_cells(c, 'FACT, every summoner of DL5-20')
    table, spells = monster_table_two(), spell_table()
    listed = set()
    for row in rows:
        name, depth, speed, hp, freq, calls = row[:6]
        entry = find_row_monster(c, name, table)
        if entry is None:
            continue
        listed.add(entry.value)
        c.emit('summoner', depth[1], f'{name[0]} depth', int(depth[0]), depth_of(entry), covers=numbers_in(depth))
        c.emit('summoner', speed[1], f'{name[0]} speed', int(speed[0].lstrip('+')),
               int(entry.first('speed')) - 110, covers=numbers_in(speed))
        c.emit('summoner', hp[1], f'{name[0]} hit-points', int(hp[0]), int(entry.first('hit-points')),
               covers=numbers_in(hp))
        c.emit('summoner', freq[1], f'{name[0]} spell-freq (1 in N)', int(freq[0]),
               int(entry.first('spell-freq')) if entry.first('spell-freq') else None, covers=numbers_in(freq))
        said = sorted(re.findall(r'S_[A-Z_]+', calls[0]))
        c.emit('summoner', calls[1], f'{name[0]} summon spells', said,
               sorted(s for s in spell_names(entry) if s.startswith('S_')))
    real = {m.value for m in real_monsters() if in_range(m) and any(s.startswith('S_') for s in spell_names(m))}
    c.emit('summoner', 0, 'every summoner of depth 5-20 is in the table', [], sorted(real - listed))
    c.emit('summoner', 0, 'the table lists only summoners of depth 5-20', [], sorted(listed - real))
    handler = gd.read_source('src/effect-handler-general.c') or ''
    m = c.search(r'The `dice:` on each spell is the number of attempts: (?P<body>[^.]*)\.', name='summon attempts')
    if m:
        for k in re.finditer(r'`(S_[A-Z_]+)` (\d+)', m['body']):
            dice = next((v for key, v, _ in spells[k[1]].fields if key == 'dice'), None)
            at = m.start('body') + k.start(2)
            c.emit('summoner', at, f'{k[1]} dice: (attempts)', int(k[2]), int(dice) if dice else None,
                   covers=[(at, at + len(k[2]))])
    m = c.search(r'summoners have (\d+) to (\d+) hp and an oil flask averages about (\d+)', name='summoner hit points and oil')
    if m:
        hps = [int(x.first('hit-points')) for x in real_monsters() if x.value in listed]
        c.emit('summoner', m.start(), 'least hit points of a summoner in range', int(m[1]), min(hps), covers=[m.span(1)])
        c.emit('summoner', m.start(), 'most hit points of a summoner in range', int(m[2]), max(hps), covers=[m.span(2)])
        flask = find_object('Flask of oil', types=['flask'])
        n, sides = (int(x) for x in flask.first('attack').split(':')[0].split('d'))
        mult = (2 + int(flask.first('weight')) // 12) * (3 if 'EXPLODE' in flask.flags() else 1)
        c.emit('summoner', m.start(), 'a flask of oil averages (volume 1)', int(m[3]),
               round(n * (sides + 1) / 2 * mult), covers=[m.span(3)])
    m = c.search(r'stops when the sum reaches your depth x the summoner\'s own level, or the attempts run out',
                 name='the summon loop')
    if m:
        c.emit('source', m.start(), 'SUMMON adds temp * temp and stops at depth * rlev or summon_max', True,
               'val += temp * temp;' in handler and 'val < player->depth * rlev' in handler
               and 'attempts < summon_max' in handler)
    m = c.search(r'drawn up to level \(depth \+ summoner level\)/(\d+) \+ (\d+) and appears within (\d+) squares of '
                 r'the summoner', name='how strong a summoned monster is')
    if m:
        summon = gd.read_source('src/mon-summon.c') or ''
        c.emit('source', m.start(), 'summon_specific draws up to (depth + lev) / 2 + 5',
               (int(m[1]), int(m[2])), (int(m[1]), int(m[2]))
               if f'(player->depth + lev) / {m[1]} + {m[2]}' in summon else None,
               covers=[m.span(1), m.span(2)])
        c.emit('source', m.start(), 'summon_specific places within 4 squares of the summoner', int(m[3]),
               int(m[3]) if f'for (d = 1; d < {int(m[3]) + 1}; ++d)' in summon else None, covers=[m.span(3)])
        c.emit('source', m.start(), 'a monster summon is placed at the summoner (mon->grid)', True,
               'summon_specific(mon->grid, rlev + level_boost, summon_type' in handler)
    m = c.search(r'`S_KIN` calls monsters of the summoner\'s own base', name='kin')
    if m:
        c.emit('source', m.start(), 'S_KIN keeps only monsters of the summoner\'s base', True,
               'race->base == kin_base' in (gd.read_source('src/mon-summon.c') or ''))
    m = c.search(r'`S_ANIMAL` any animal', name='animal summons')
    if m:
        animal = next((e for e in gd.load('summon.txt')[0] if e.value == 'ANIMAL'), None)
        c.emit('docs', m.start(), 'summon.txt: ANIMAL is race-flag ANIMAL', 'ANIMAL',
               animal.first('race-flag') if animal else None)
    m = c.search(r'(\w+) of the (\w+) \(all but the priest and the druid\) have BLINK', name='blink summoners')
    if m:
        every = [x for x in real_monsters() if in_range(x) and any(s.startswith('S_') for s in spell_names(x))]
        with_blink = [x for x in every if 'BLINK' in spell_names(x)]
        without = sorted(plain(x.value) for x in every if 'BLINK' not in spell_names(x))
        c.emit('summoner', m.start(), 'summoners without BLINK', ['druid', 'priest'], without)
        words = {'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9}
        c.emit('summoner', m.start(), 'summoners with BLINK', words.get(m[1]), len(with_blink), covers=[m.span(1)])
        c.emit('summoner', m.start(), 'summoners in range', words.get(m[2]), len(every), covers=[m.span(2)])
    for m in c.finditer(r'(Orfax|Boldor) comes with (?P<list>[^.;]*)'):
        entry = table[plain(m[1])]
        friends = {v.split(':')[2].lower(): v.split(':')[1] for v in entry.all('friends')}
        for k in re.finditer(r'(\d+d\d+) ([a-z ]+?)s?(?= and |,| \(|$|\.)', m['list']):
            c.emit('summoner', m.start('list') + k.start(),
                   f'{m[1]} comes with {k[2]}: dice', k[1], friends.get(k[2].lower()),
                   covers=[(m.start('list') + k.start(1), m.start('list') + k.end(1))])


NOTE_WORDS = {
    'casts': lambda e: bool(spell_names(e)),
    'summons': lambda e: any(s.startswith('S_') for s in spell_names(e)),
    'steals gold': lambda e: any('EAT_GOLD' in b for b in e.all('blow')),
    'never moves': lambda e: 'NEVER_MOVE' in monster_flags(e),
    'paralyses': lambda e: any('PARALYZE' in v for _, v, _ in e.fields),
}


@extractor('unique table', minimum=88, volumes=(2,))
def unique_table(c):
    _, rows = table_cells(c, 'FACT, every unique in range')
    table = monster_table_two()
    listed = set()
    for row in rows:
        name, depth, speed, hp, per_turn, note = row[:6]
        entry = find_row_monster(c, name, table)
        if entry is None:
            continue
        listed.add(entry.value)
        c.emit('unique', depth[1], f'{name[0]} depth', int(depth[0]), depth_of(entry), covers=numbers_in(depth))
        c.emit('unique', speed[1], f'{name[0]} speed', int(speed[0].lstrip('+')),
               int(entry.first('speed')) - 110, covers=numbers_in(speed))
        c.emit('unique', hp[1], f'{name[0]} hit-points', int(hp[0]), int(entry.first('hit-points')),
               covers=numbers_in(hp))
        top = worst_round(entry)
        c.emit('unique', per_turn[1], f'{name[0]} worst melee per player turn', int(per_turn[0]),
               top * (1 + (int(entry.first('speed')) - 110) // 10), covers=numbers_in(per_turn))
        c.emit('unique', name[1], f'{name[0]} is a UNIQUE', True, 'UNIQUE' in entry.flags())
        for word, test in NOTE_WORDS.items():
            if word in note[0]:
                c.emit('unique', note[1], f'{name[0]}: {word}', True, bool(test(entry)))
        have = set()
        for key, value, _ in entry.fields:
            if key in ('spells', 'blow', 'flags'):
                have.update(re.findall(r'[A-Z][A-Z_0-9]+', value))
        for token in re.findall(r'\b[A-Z]{2,}(?:_[A-Z0-9]+)+\b', note[0]):
            c.emit('unique', note[1], f'{name[0]} has {token}', True, token in have)
    real = {m.value for m in real_monsters() if in_range(m) and 'UNIQUE' in m.flags()}
    c.emit('unique', 0, 'every unique of depth 5-20 is in the table', [], sorted(real - listed))
    c.emit('unique', 0, 'the table lists only uniques of depth 5-20', [], sorted(listed - real))


def book_table():
    """`{book name: (town or dungeon, kind cost)}` from class.txt (the first class
    that gives the book its `book-properties:` supplies the cost)."""
    found = {}
    for entry in gd.load('class.txt')[0]:
        name, kind = None, None
        for key, value, _ in entry.fields:
            if key == 'book':
                parts = value.split(':')
                name, kind = parts[2].strip('[]'), parts[1]
                found.setdefault(name, [kind, None])
            elif key == 'book-properties' and name and found[name][1] is None:
                found[name][1] = int(value.split(':')[0])
    return {k: tuple(v) for k, v in found.items()}


@extractor('class spells and books', minimum=110, volumes=(2,))
def class_books(c):
    classes = {e.value: e for e in gd.load('class.txt')[0]}
    books = book_table()
    seen = []
    for m in c.finditer(r'^\*\*(\w+)\*\*: (.*)$', re.M):
        cls, body, offset = m[1], m[2], m.start(2)
        entry = classes.get(cls)
        if entry is None:
            continue
        seen.append(cls)
        own = {}
        for key, value, _ in entry.fields:
            if key == 'book':
                own[value.split(':')[2].strip('[]')] = value.split(':')[1]
        claim_spells(c, cls, entry, body, offset)
        mentions = list(re.finditer(r'\[([^\]]+)\](?: \((?:(dungeon only)(?:, )?)?(?:kind cost (\d+))?\))?', body))
        for b in mentions:
            name = b[1]
            c.emit('spell book', offset + b.start(), f'{cls} has the book [{name}]', True, name in own)
            if b[2]:
                c.emit('spell book', offset + b.start(), f'[{name}] is a dungeon book', 'dungeon',
                       books.get(name, (None,))[0])
            if b[3]:
                c.emit('book cost', offset + b.start(3), f'[{name}] kind cost', int(b[3]),
                       books.get(name, (None, None))[1], covers=[(offset + b.start(3), offset + b.end(3))])
                if not b[2]:
                    c.emit('spell book', offset + b.start(), f'[{name}] is a town book', 'town',
                           books.get(name, (None,))[0])
        spells = class_spells(entry)
        names = {n.lower(): n for _, n, *_ in spells}
        pattern = re.compile(r'(?<![\w\[])(' + '|'.join(
            re.escape(n) for n in sorted(names, key=len, reverse=True)) + r')(?![\w\]])', re.I)
        for s in pattern.finditer(body):
            real = next(x for x in spells if x[1] == names[s[1].lower()])
            before = [b for b in mentions if b.start() < s.start()]
            c.emit('spell book', offset + s.start(), f'{cls} {real[1]} is in the book the line names',
                   before[-1][1] if before else None, real[0])
    c.emit('class', 0, 'the class paragraphs are the casters with town books', sorted(seen),
           sorted(e.value for e in classes.values() if e.has('magic')))
    m = c.search(r'[Tt]own books hold (?P<town>[^;]*); dungeon-only books hold (?P<dungeon>[^.]*)\.', name='teleport books')
    if m:
        for which, kind in (('town', 'town'), ('dungeon', 'dungeon')):
            for k in re.finditer(r'(Mage|Necromancer|Rogue|Priest) (Teleport Self|Shadow Shift|Portal)', m[which]):
                spell = [s for s in class_spells(classes[k[1]]) if s[1] == k[2]]
                c.emit('spell book', m.start(which) + k.start(), f'{k[1]} {k[2]} is in a {kind} book',
                       kind, books[spell[0][0]][0] if spell else 'no such spell')
    m = c.search(r'(?P<who>[A-Z]\w+(?:, [A-Z]\w+)* and [A-Z]\w+) have none', name='classes with no teleport')
    if m:
        for who in re.split(r', | and ', m['who']):
            teleports = [v for k, v, _ in classes[who].fields if k == 'effect' and v.startswith('TELEPORT')]
            c.emit('class flags', m.start(), f'{who} has no teleport spell', [], teleports)


@extractor('spell numbers', minimum=28, volumes=(2,))
def spell_numbers(c):
    classes = {e.value: e for e in gd.load('class.txt')[0]}
    source = gd.read_source('src/player-spell.c') or ''
    m = c.search(r'falls (\d+) per level above the spell\'s level, never below (\d+)% \(the floor can be '
                 r'higher for a low casting stat\) and never above (\d+)%', name='the spell failure rule')
    if m:
        c.emit('source', m.start(), 'spell_chance: 3 per level above the spell', int(m[1]),
               3 if 'chance -= 3 * (player->lev - spell->slevel);' in source else None, covers=[m.span(1)])
        c.emit('source', m.start(), 'spell_chance: floor of 5 percent', int(m[2]),
               5 if 'minfail < 5' in source else None, covers=[m.span(2)])
        c.emit('source', m.start(), 'spell_chance: cap of 50 percent', int(m[3]),
               50 if 'if (chance > 50) chance = 50;' in source else None, covers=[m.span(3)])
    m = c.search(r'Mage Resistance CL(\d+)', name='Mage Resistance in section 4')
    if m:
        c.emit('spell', m.start(), 'Mage Resistance level', int(m[1]),
               next(x for x in class_spells(classes['Mage']) if x[1] == 'Resistance')[2], covers=[m.span(1)])
    m = c.search(r'Teleport Self \((\d+)%\) is down to the (\d+)% floor at CL(\d+)', name='the Mage floor')
    if m:
        spell = next(s for s in class_spells(classes['Mage']) if s[1] == 'Teleport Self')
        c.emit('spell', m.start(), 'Mage Teleport Self base failure', int(m[1]), spell[4], covers=[m.span(1)])
        floor = 5
        level = next((cl for cl in range(spell[2], 51) if spell[4] - 3 * (cl - spell[2]) <= floor), None)
        c.emit('spell', m.start(), 'Mage Teleport Self reaches the floor at CL', int(m[3]), level,
               covers=[m.span(2), m.span(3)])
    m = c.search(r'moves you \(CL x (\d+)/(\d+)\)% of the span', name='Teleport Self distance')
    if m:
        mage = classes['Mage']
        index = next(i for i, (k, v, _) in enumerate(mage.fields) if k == 'spell' and v.startswith('Teleport Self'))
        expr = next(v for k, v, _ in mage.fields[index:index + 6] if k == 'expr')
        c.emit('spell', m.start(), 'Teleport Self distance is M:PLAYER_LEVEL * 9 / 5', f'M:PLAYER_LEVEL:* {m[1]} / {m[2]}',
               expr, covers=[m.span(1), m.span(2)])
        wid = constants().get('world:dungeon-wid', 198)
        for k in re.finditer(r'CL(\d+) is (\d+)%, about (\d+)', c.text):
            cl = int(k[1])
            pct = cl * int(m[1]) // int(m[2])
            c.emit('spell', k.start(), f'Teleport Self at CL{cl}: percent', int(k[2]), pct, covers=[k.span(1), k.span(2)])
            c.emit('spell', k.start(), f'Teleport Self at CL{cl}: squares from the middle', int(k[3]),
                   (wid // 2) * pct // 100, covers=[k.span(3)])
    m = c.search(r'First cast pays experience x spell level', name='the first-cast experience')
    if m:
        c.emit('source', m.start(), 'a first cast pays sexp * slevel', True,
               'player_exp_gain(player, e * spell->slevel)' in source)
        for k in re.finditer(r'(Mage|Druid|Priest|Necromancer|Rogue|Ranger|Paladin|Blackguard) '
                             r'([A-Z][A-Za-z\' ]+?) (\d+) x (\d+) = (\d+)', c.text[m.start():m.start() + 700]):
            at = m.start() + k.start()
            spell = [s for s in class_spells(classes[k[1]]) if s[1] == k[2]]
            exp_of = None
            for key, value, _ in classes[k[1]].fields:
                if key == 'spell' and value.split(':')[0] == k[2]:
                    exp_of = int(value.split(':')[4])
            c.emit('spell', at, f'{k[1]} {k[2]} experience (last field)', int(k[3]), exp_of,
                   covers=[(m.start() + k.start(3), m.start() + k.end(3))])
            c.emit('spell', at, f'{k[1]} {k[2]} level', int(k[4]), spell[0][2] if spell else None,
                   covers=[(m.start() + k.start(4), m.start() + k.end(4))])
            c.emit('spell', at, f'{k[1]} {k[2]} first cast pays', int(k[5]), int(k[3]) * int(k[4]),
                   covers=[(m.start() + k.start(5), m.start() + k.end(5))])
    m = c.search(r'CL(\d+) needs (\d+) x race exp / (\d+), CL(\d+) (\d+) and CL(\d+) (\d+)', name='level thresholds')
    if m:
        text = gd.read_source('src/player.c') or ''
        c.emit('source', m.start(), 'adjust_level divides by 100 after the race experience factor', int(m[3]),
               100 if 'p->expfact / 100L' in text else None, covers=[m.span(3)])
        table = [int(n) for n in re.findall(r'\b(\d+)L?,', text[text.index('player_exp[PY_MAX_LEVEL]'):][:900])]
        for level_at, exp_at in ((1, 2), (4, 5), (6, 7)):
            level = int(m[level_at])
            c.emit('source', m.start(), f'player_exp: experience for CL{level}', int(m[exp_at]), table[level - 2],
                   covers=[m.span(level_at), m.span(exp_at)])


@extractor('buy table', minimum=23, volumes=(2,))
def buy_table(c):
    object_table_two(c, 'Found from is the', 'buy')


@extractor('first appearances', minimum=3, volumes=(2,))
def first_appearances(c):
    """`**Breath** (from DL5)`: the shallowest monster that has the thing."""
    monsters = real_monsters()
    for word, test in (('Breath', lambda m: any(s.startswith('BR_') for s in spell_names(m))),
                       ('Summoning', lambda m: any(s.startswith('S_') for s in spell_names(m))),
                       ('HOLD', lambda m: 'HOLD' in spell_names(m))):
        found = c.search(rf'\*\*{word}\*\* \(from DL(\d+)\)', name=f'the {word} first depth')
        if found:
            c.emit('first appearance', found.start(), f'shallowest monster with {word}',
                   int(found[1]), min(depth_of(m) for m in monsters if test(m)), covers=[found.span(1)])


@extractor('hit points and free action', minimum=14, volumes=(2,))
def hit_points_and_free_action(c):
    birth = gd.read_source('src/player-birth.c') or ''
    races = {e.value: e for e in gd.load('p_race.txt')[0]}
    classes = {e.value: e for e in gd.load('class.txt')[0]}
    m = c.search(r'hit die \+ \(n-1\) x \(hit die \+ 1\)/2 plus CON \(`src/player-birth.c roll_hp`: each level rolls 1 to '
                 r'the hit die\)', name='the hit point average')
    if m:
        c.emit('source', m.start(), 'roll_hp rolls randint1(hitdie) per level', True,
               'randint1(player->hitdie)' in birth and 'player->player_hp[i-1] + j' in birth, covers=[m.span()])

    def average(hit_die, level):
        return hit_die + (level - 1) * (hit_die + 1) / 2

    for k in re.finditer(r'hit die (\d+) \((\w[\w-]*) (\w+)\) has (\d+) at CL(\d+)(?: and needs CL(\d+) for (\d+))?',
                         c.text):
        die = int(races[k[2]].first('hitdie')) + int(classes[k[3]].first('hitdie'))
        c.emit('hit points', k.start(), f'{k[2]} {k[3]} hit die', int(k[1]), die, covers=[k.span(1)])
        c.emit('hit points', k.start(), f'{k[2]} {k[3]} average hit points at CL{k[5]}', int(k[4]),
               int(average(die, int(k[5]))), covers=[k.span(4), k.span(5)])
        if k[6]:
            level = next(n for n in range(1, 51) if average(die, n) >= int(k[7]))
            c.emit('hit points', k.start(), f'{k[2]} {k[3]} reaches {k[7]} hit points at CL', int(k[6]), level,
                   covers=[k.span(6), k.span(7)])
    spells = spell_table()
    m = c.search(r'HOLD paralyses for (\d+\+\d+d\d+) turns', name='HOLD duration')
    if m:
        dice = next(v for k, v, _ in spells['HOLD'].fields if k == 'dice')
        c.emit('spell', m.start(), 'HOLD paralyses for (dice)', m[1], dice, covers=[m.span(1)])
    m = c.search(r'Free Action blocks it \(`fail:(\d+):FREE_ACT`', name='Free Action blocks HOLD')
    if m:
        timed = {e.value: e for e in gd.load('player_timed.txt')[0]}
        c.emit('spell', m.start(), 'PARALYZED fails with FREE_ACT (fail:N:FREE_ACT)', f'{m[1]}:FREE_ACT',
               timed['PARALYZED'].first('fail'), covers=[m.span(1)])
    m = c.search(r'The gate sits (\w+) levels after its own first anchor', name='the Free Action gap')
    if m:
        gates = chapter15_depth_gates()
        words = {'seven': 7, 'six': 6, 'eight': 8}
        first = min(d for n, d in gates[20][1] if n in ('illusionist', 'druid'))
        c.emit('gate', m.start(), 'levels between the Free Action gate and the first HOLD anchor',
               words.get(m[1]), 20 - first, covers=[m.span(1)])
    m = c.search(r'DL(\d+) is inside that window from DL(\d+)', name='the DEPTH-01 window')
    if m:
        c.emit('gate', m.start(), 'DEPTH-01 looks to d+5: the first depth that sees DL13', int(m[2]),
               int(m[1]) - 5, covers=[m.span(1), m.span(2)])
    m = c.search(r'ring \(found from DL(\d+), (\d+), `object`\) or an ego on gloves \(found from DL(\d+) to '
                 r'(\d+)\) or boots \((\d+) to (\d+)\) \(`ego_item`\)', name='where Free Action comes from')
    if m:
        ring = find_object('Free Action', types=['ring'])
        c.emit('gate', m.start(), 'Ring of Free Action found from', int(m[1]), alloc_min(ring), covers=[m.span(1)])
        c.emit('gate', m.start(), 'Ring of Free Action cost:', int(m[2]), int(ring.first('cost')), covers=[m.span(2)])
        egos = [e for e in gd.load('ego_item.txt')[0] if e.value == 'of Free Action']
        by_type = {e.first('type'): re.match(r'\d+:(\d+) to (\d+)', e.first('alloc')) for e in egos}
        c.emit('gate', m.start(), 'ego of Free Action on gloves: alloc', (int(m[3]), int(m[4])),
               (int(by_type['gloves'][1]), int(by_type['gloves'][2])), covers=[m.span(3), m.span(4)])
        c.emit('gate', m.start(), 'ego of Free Action on boots: alloc', (int(m[5]), int(m[6])),
               (int(by_type['boots'][1]), int(by_type['boots'][2])), covers=[m.span(5), m.span(6)])
        c.emit('gate', m.start(), 'no store sells Free Action', [], [
            (s['key'], t, n) for s in stores() for t, n in s['always'] + s['normal'] if 'Free Action' in n])


@extractor('town facts', minimum=25, volumes=(2,))
def town_facts(c):
    handler = gd.read_source('src/effect-handler-general.c') or ''
    util = gd.read_source('src/player-util.c') or ''
    m = c.search(r'(\d+)-(\d+) turns after reading', name='the recall delay')
    if m:
        k = re.search(r'word_recall = randint0\((\d+)\) \+ (\d+);', handler)
        c.emit('source', m.start(), 'Word of Recall delay (src/effect-handler-general.c)',
               (int(m[1]), int(m[2])), (int(k[2]), int(k[2]) + int(k[1]) - 1) if k else None,
               covers=[m.span(1), m.span(2)])
    m = c.search(r'it takes you to DL(\d+)\*\* \(`src/player-util.c player_set_recall_depth` makes it at least (\d+)\)',
                 name='recall from the town with no depth')
    if m:
        c.emit('source', m.start(), 'player_set_recall_depth: at least depth 1', (int(m[1]), int(m[2])),
               (1, 1) if 'p->recall_depth = MAX(p->recall_depth, 1);' in util else None, covers=[m.span(1), m.span(2)])
        c.emit('source', m.start(), 'RECALL has no "nothing happens" for an unvisited depth', True,
               'if (OPT(player, birth_no_recall) && !player->total_winner)' in handler)
        old = INSTRUCTIONS.read_text()
        c.emit('docs', m.start(), 'volume 1 says recall does nothing from the town', True,
               'it does nothing from the town' in old)
    m = c.search(r'(\d+) gold wasted', name='the recall scroll price')
    if m:
        c.emit('effect', m.start(), 'Word of Recall cost:', int(m[1]),
               int(find_object('Word of Recall', types=['scroll']).first('cost')), covers=[m.span(1)])
    m = c.search(r'\*\*y also sets your deepest depth to this one\*\*', name='recall y sets max depth')
    if m:
        c.emit('source', m.start(), 'recall y sets recall_depth and max_depth to the current depth', True,
               'player->recall_depth = player->max_depth = player->depth;' in handler)
    m = c.search(r'\((\d+) x depth / (\d+) \+ (\d+)\) x (\d+) with selling off: (?P<piles>[^.]*)\.', name='the gold formula')
    if m:
        source = gd.read_source('src/obj-make.c') or ''
        c.emit('source', m.start(), 'make_gold average is (16 * lev) / 10 + 16', (16, 10, 16),
               (int(m[1]), int(m[2]), int(m[3])) if f'int avg = ({m[1]} * lev)/{m[2]} + {m[3]};' in source else None,
               covers=[m.span(1), m.span(2), m.span(3)])
        c.emit('source', m.start(), 'make_gold multiplies by 5 under no_selling', int(m[4]),
               5 if 'if (OPT(player, birth_no_selling) && player->depth)' in source and 'value *= 5;' in source
               else None, covers=[m.span(4)])
        for k in re.finditer(r'(\d+) at DL(\d+)', m['piles']):
            lev = int(k[2])
            at = m.start('piles') + k.start()
            c.emit('source', at, f'gold pile average at DL{lev}', int(k[1]), ((16 * lev) // 10 + 16) * 5,
                   covers=[(m.start('piles') + k.start(1), m.start('piles') + k.end(1)),
                           (m.start('piles') + k.start(2), m.start('piles') + k.end(2))])
    m = c.search(r'a (\d+) staff is (\d+) / (\d+) = ([\d.]+) piles at DL(\d+)', name='the staff in piles')
    if m:
        staff = find_object('Teleportation', types=['staff'])
        avg = ((16 * int(m[5])) // 10 + 16) * 5
        c.emit('source', m.start(), 'Staff of Teleportation cost:', int(m[1]), int(staff.first('cost')),
               covers=[m.span(1), m.span(2)])
        c.emit('source', m.start(), 'a pile at that depth', int(m[3]), avg, covers=[m.span(3), m.span(5)])
        c.emit('source', m.start(), 'the staff in piles', m[4], f'{int(m[2]) / avg:.1f}', covers=[m.span(4)])
    m = c.search(r'CCW heals (\d+) and cures (?P<cures>[^;]*?) besides blindness', name='the CCW line')
    if m:
        potion = find_object('Cure Critical Wounds', types=['potion'])
        fields = [(k, v) for k, v, _ in potion.fields]
        heal = int(next(v for (k, v), (k2, v2) in zip(fields, fields[1:]) if k == 'effect' and v == 'HEAL_HP' and k2 == 'dice'
                        for v in [v2]))
        c.emit('effect', m.start(), 'CCW heals', int(m[1]), heal, covers=[m.span(1)])
        word = {'poison': 'POISONED', 'stun': 'STUN', 'amnesia': 'AMNESIA', 'confusion': 'CONFUSED', 'cuts': 'CUT'}
        said = {word[w] for w in re.split(r', | and ', m['cures'])}
        real = {v.split(':')[1] for k, v in fields if k == 'effect' and v.startswith('CURE:')} - {'BLIND'}
        c.emit('effect', m.start(), 'CCW cures (besides blindness)', sorted(said), sorted(real))
        c.emit('effect', m.start(), 'CCW cures blindness', True, ('effect', 'CURE:BLIND') in fields)
    m = c.search(r'stops dropping in the dungeon at DL(\d+)', name='Cure Light Wounds alloc')
    if m:
        clw = find_object('Cure Light Wounds', types=['potion'])
        top = re.match(r'\d+:\d+ to (\d+)', clw.first('alloc'))
        c.emit('effect', m.start(), 'Cure Light Wounds alloc maximum depth', int(m[1]), int(top[1]),
               covers=[m.span(1)])
    m = c.search(r'drained stats come back at your next level \(`src/player.c adjust_level`\)', name='stat restore')
    if m:
        player = gd.read_source('src/player.c') or ''
        body = player[player.index('static void adjust_level'):][:2200]
        c.emit('source', m.start(), 'adjust_level restores every stat at a level up', True,
               all(f'EF_RESTORE_STAT, source_none(), "0", STAT_{s}' in body for s in ('STR', 'INT', 'WIS', 'DEX', 'CON')))
    m = c.search(r'Summon Undead \(found from DL(\d+)\), Aggravate Monster \(found from DL(\d+)\) and the cost-(\d+) '
                 r'potions of Sleep and Salt Water, which paralyse', name='unknown scrolls and potions')
    if m:
        c.emit('effect', m.start(), 'Summon Undead found from', int(m[1]),
               alloc_min(find_object('Summon Undead', types=['scroll'])), covers=[m.span(1)])
        c.emit('effect', m.start(), 'Aggravate Monster found from', int(m[2]),
               alloc_min(find_object('Aggravate Monster', types=['scroll'])), covers=[m.span(2)])
        for name in ('Sleep', 'Salt Water'):
            potion = find_object(name, types=['potion'])
            c.emit('effect', m.start(), f'potion of {name} cost:', int(m[3]), int(potion.first('cost')),
                   covers=[m.span(3)])
            c.emit('effect', m.start(), f'potion of {name} paralyses', True,
                   any('PARALYZED' in v for k, v, _ in potion.fields if k == 'effect'))



def manual_says_two(c):
    rules = [
        (r'typical CL 8-22 and 18-32', 12, r'### Typical CL\s+8-22'),
        (r'typical CL 8-22 and 18-32', 12, r'### Typical CL\s+18-32'),
        (r'c15 `K_HP_RESERVE`, max\(20, 10%\)', 15, r'`K_HP_RESERVE` \| max\(20, 10% max hp\)'),
        (r'until about CL30 \(c13 13\.1\)', 13, r'until clvl ~30'),
        (r'c15 DEPTH-01 looks at monsters native to d-2 to d\+5', 15, r'd−2 … d\+5'),
        (r'c8 says this', 8, r'full strength out to 7'),
        (r"c15 15\.3's `D = 4`", 15, r'`D = 4`'),
        (r"FIGHT-04's `halves at 7`", 15, r'halves at 7'),
        (r'the chapter\'s "\+20" for him', 15, r'Bullroarer \(D5, \+20\)'),
        (r'down to under 3 Phase Door', 12, r'fewer than 3 Phase'),
                (r'c15 DEPTH-02 gives a minimum kit per depth', 15, r'DEPTH-02 — Mandatory kit gates'),
    ]
    chapters = {n: gd.read_chapter(n) or '' for n in gd.strategy_chapter_files()}
    for anchor, chapter, needle in rules:
        found = c.search(anchor, name=anchor, required=False)
        if not found:
            c.problem(f'the page no longer has {anchor!r}')
            continue
        c.emit('manual says', found.start(), f'chapter {chapter} contains {needle!r}', True,
               bool(re.search(needle, chapters[chapter])), end=found.end(), covers=[found.span()])


extractor('strategy manual quotations', minimum=11, volumes=(2,))(manual_says_two)


# -- how much of the page's numbers a check settles ---------------------------

NUMBER_TOKEN = re.compile(r'(?:(?<=CL)|(?<=DL)|(?<![A-Za-z_$#\d.]))(?:\d+d\d+|\d+(?:\.\d+)?)')


def structural_spans(text):
    """Numbers that name a place rather than state a fact: headings, the sources
    header, table headers, chapter and section references, rule ids."""
    spans = []
    for m in re.finditer(r'^(#.*|Sources, so any line can be checked\..*)$', text, re.M):
        spans.append(m.span())
    opening = re.search(r'^\*\*No run has reached.*$', text, re.M)        # the caveat: scope and narrative
    if opening:
        spans.append(opening.span())
    for m in re.finditer(r'^\|.*\|\s*\n\|[-| :]+\|', text, re.M):          # a table's header and rule
        spans.append(m.span())
    for pattern in (r'\bc\d+(?: \d+\.\d+(?:[-,] ?\d+\.\d+)*)?', r'\b[A-Z]{2,6}-\d\d[a-z]?(?:/\d\d)*\b',
                    r'\b[Ss]ections? \d+[a-z]?(?:-\d+)?\b', r'\b[Vv]olume \d\b', r'\(\d\)', r'\b1 in N\b',
                    r'\bDL\d+-\d+\b', r'^- \*\*[^*]+\*\*(?=[ .:(])'):
        spans += [m.span() for m in re.finditer(pattern, text, re.M)]
    return spans


def number_coverage(report, text):
    """`(covered, total, uncovered)`: every number on the page that is not
    structural, and the ones no claim says it settles."""
    ignore = structural_spans(text)
    covered = [span for claim in report.checked for span in claim.covers]

    def inside(a, b, spans):
        return any(a < e and s < b for s, e in spans)

    total, missing = 0, []
    for m in NUMBER_TOKEN.finditer(text):
        a, b = m.span()
        if inside(a, b, ignore):
            continue
        total += 1
        if not inside(a, b, covered):
            line = text.count('\n', 0, a) + 1
            missing.append((line, m[0], text[max(0, a - 25):b + 25].replace('\n', ' ')))
    return total - len(missing), total, missing


# -- running everything --------------------------------------------------------

def shortcuts_of(text):
    """`{'object': 'vendor/angband/lib/gamedata/object.txt', ...}` from a page's
    own `Sources, so any line can be checked.` header."""
    found = {}
    header = re.search(r'^Sources, so any line can be checked\..*$', text, re.M)
    for names, target in re.findall(r'((?:`\w+`/?)+) = `([^`]+)`', header.group(0) if header else ''):
        for name in re.findall(r'`(\w+)`', names):
            found[name] = target.replace('<name>', name)
    return found


def check(text=None, path=INSTRUCTIONS, volume=1):
    """Read the page and check every claim the grammars find. `volume` 2 reads
    `manuals/INSTRUCTIONS_2.md`, whose header leans on volume 1's shorthand."""
    if volume == 2 and path == INSTRUCTIONS:
        path = INSTRUCTIONS_2
    text = path.read_text() if text is None else text
    ctx = Ctx(text, volume)
    if volume == 2:
        ctx.shortcuts = shortcuts_of(INSTRUCTIONS.read_text())
    # citation shortcuts first: later extractors use them
    ordered = sorted(EXTRACTORS, key=lambda e: e[0] != 'citation shortcuts')
    for name, minimum, fn, volumes in ordered:
        if volume not in volumes:
            continue
        if isinstance(minimum, dict):
            minimum = minimum[volume]
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
