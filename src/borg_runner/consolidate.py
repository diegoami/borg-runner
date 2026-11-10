"""Turn notebooks into the page, and check that the page can be traced back.

A notebook is a log: what one player noticed, in the order it happened, in its
own words. That is the right shape for evidence and the wrong shape for
reading - nothing merges, nothing is contradicted, and the twentieth run would
inherit twenty transcripts.

So after every run the notebooks are consolidated into `manuals/INSTRUCTIONS.md`
itself: a line that runs have measured goes on the page where a player will
meet it, labelled OBSERVED, **naming the runs that saw it as `run#ask`**. That
citation is the whole discipline. The ask is in that run's promoted notebook
under `knowledge/` and in its decisions under `records/`, so every claim on
the page leads back to a screen, and this module is what checks that it does -
the writing is a model's job, the tracing is not.

Three rules, carried from the knowledge base this replaced:

- one run noticing something is a lead, and the line says so;
- a claim of "N runs" has to name N different runs;
- a later run that disagrees is written down, not deleted, because the
  disagreement is the interesting part.

Until 2026-11-10 the same discipline lived in `knowledge/LEARNED.md` (items
with ids, statuses and evidence) and `knowledge/MANUAL-GAPS.md` (cheat sheets
to paste into the manual). Both were removed once the page carried their
content: a reader had three documents to reconcile and the page was the only
one anybody read. They are in git history, and the notebooks they were built
from are untouched in `knowledge/`.
"""
import json
import re
from pathlib import Path

from . import pins, run as run_module

INSTRUCTIONS = pins.ROOT / 'manuals' / 'INSTRUCTIONS.md'
VOLUME_TWO = pins.ROOT / 'manuals' / 'INSTRUCTIONS_2.md'

# `sonnet-2#124`: the run, and the ask whose screen shows it.
REFERENCE = re.compile(r'\b(?P<run>[A-Za-z0-9][A-Za-z0-9_.-]*?)#(?P<ask>\d+)')
# "3 runs", "seen in 2 runs", "(2 runs: ...)".
COUNT = re.compile(r'\b(?P<count>\d+) runs\b')
OBSERVED = 'OBSERVED'


def notebooks(where=None):
    """The promoted notebooks, which are the evidence.

    A notebook is a *run's* notebook, so it is recognised by having a run of
    the same name - not by being any file in the directory. Globbing every
    `.md` here made MANUAL-GAPS.md count as a run with no asks, and evidence
    written `MANUAL-GAPS#1` would then have passed the check. A consolidation
    could have cited its own output as evidence.
    """
    where = Path(where) if where else run_module.KNOWLEDGE
    runs = recorded_runs()
    return sorted(path for path in where.glob('*.md') if path.stem in runs)


def recorded_runs():
    """Run name -> how many asks it made, from the records that exist.

    Both the archive and the working directory count, and `asks_made` is used
    where it is there: a death's tombstone is an unanswered ask, so a citation
    may legitimately name it.
    """
    counts = {}
    for where in (run_module.RECORDS, pins.ROOT / 'runs'):
        for record in where.glob('*/record.json'):
            try:
                body = json.loads(record.read_text())
            except ValueError:
                continue
            name = body.get('run') or record.parent.name
            asks = body.get('asks_made') or body.get('asks') or 0
            counts[name] = max(counts.get(name, 0), asks)
    return counts


# Kept under its old name for callers that read it.
def known_runs():
    return recorded_runs()


def chunks(text):
    """The page as the units a claim is made in: a bullet, or a paragraph.

    A bullet runs to the next bullet or blank line, because the page wraps its
    bullets over several lines and a citation often sits on the line after the
    claim it supports.
    """
    found, current, start = [], [], 1
    def flush():
        if any(line.strip() for line in current):
            found.append({'line': start, 'text': '\n'.join(current)})
    for number, line in enumerate(text.splitlines(), start=1):
        bullet = line.startswith('- ') or line.startswith('## ')
        if bullet or not line.strip():
            flush()
            current, start = ([line], number) if bullet else ([], number + 1)
            continue
        if not current:
            start = number
        current.append(line)
    flush()
    return found


def claims(path=INSTRUCTIONS):
    """Every chunk of the page that rests on a run rather than on the game."""
    text = Path(path).read_text()
    found = []
    for chunk in chunks(text):
        cited = [match.groupdict() for match in REFERENCE.finditer(chunk['text'])]
        counted = [int(match.group('count')) for match in COUNT.finditer(chunk['text'])]
        if cited or counted or OBSERVED in chunk['text']:
            found.append({**chunk, 'cited': cited, 'counted': counted})
    return found


def check(path=INSTRUCTIONS):
    """What on the page cannot be traced to a run. Empty means it can.

    The header and the one caveat that only *describe* the labels are not
    claims, so a chunk that names no run and counts none is only a problem
    when it says OBSERVED.
    """
    runs = recorded_runs()
    if not runs:
        return ['there are no runs to check against']
    problems = []
    for claim in claims(path):
        where = f"line {claim['line']}"
        first = claim['text'].strip().splitlines()[0][:60]
        named = set()
        for reference in claim['cited']:
            name, ask = reference['run'], int(reference['ask'])
            if name not in runs:
                problems.append(f'{where}: {first}... cites {name}, '
                                f'which is not a run')
                continue
            named.add(name)
            if runs[name] and ask > runs[name]:
                problems.append(f'{where}: {first}... cites {name}#{ask}, '
                                f"past {name}'s {runs[name]} asks")
        if not claim['cited'] and OBSERVED in claim['text']:
            problems.append(f'{where}: {first}... says {OBSERVED} and names no '
                            f'run; a claim about play is traceable or it is a '
                            f'superstition')
        for count in claim['counted']:
            if claim['cited'] and len(named) < count:
                problems.append(
                    f'{where}: {first}... claims {count} runs and names '
                    f'{len(named) or "none"} ({", ".join(sorted(named)) or "-"})')
    return problems


# The themes that keep coming back. Reports raise the same handful of things
# again and again - four runs in a row lost asks to not knowing they were
# standing on a staircase - and a theme that recurs and is not on the page is
# the page's fault, not the players'. Each theme is identified in a report by
# any of `raised`, and counted as answered when the page matches any of
# `answered`. Hand-maintained on purpose: the counting is mechanical, deciding
# that two reports mean the same thing is not.
THEMES = (
    {'slug': 'the-game-walks-for-you',
     'raised': (r'\blxg\b', r'\bl>g\b', r'find_path', r'pathfind'),
     'answered': (r'game pathfinds',)},
    {'slug': 'you-start-on-a-staircase',
     'raised': (r'town .{0,40}down stair', r'start(?:ing)? on (?:it|the stair)',
                r'standing on it'),
     'answered': (r"standing on the town's down staircase",)},
    {'slug': 'the-tile-under-you-is-not-drawn',
     'raised': (r'not drawn under', r'no `?>`? (?:glyph )?(?:was )?drawn',
                r'only the status line', r'staircase .{0,30}standing on'),
     'answered': (r'staircase under you is never drawn',)},
    {'slug': 'the-level-is-bigger-than-the-view',
     'raised': (r'\b198\b', r'three screens', r'five screens'),
     'answered': (r'198x66', r'198 x 66')},
    {'slug': 'you-cannot-see-where-you-are',
     'raised': (r'absolute position', r'absolute coordinates',
                r'where on the level', r'did not know whether I was at'),
     'answered': (r'and you do not need to',)},
    {'slug': 'the-town-is-hard-to-cross',
     'raised': (r'navigat\w+ (?:the )?town', r'town without finding a shop',
                r'walked \d+ tiles through a town', r'store .{0,20}door'),
     'answered': (r'Town stores are the digits',)},
    {'slug': 'a-prompt-eats-the-next-key',
     'raised': (r'swallow', r'ate the rest', r'eats the next', r'-more-'),
     'answered': (r'swallows the next key',)},
    {'slug': 'spell-points-cost-turns',
     'raised': (r'regen_mana', r'spell point.{0,40}rest', r'turns of rest'),
     'answered': (r'player_regen_mana',)},
    {'slug': 'depth-is-the-only-plan',
     'raised': (r'never (?:saw|found) a `?>`?', r'staircase hunt',
                r"trying to find (?:the|depth \d+.s) down stair",
                r'no down staircase'),
     'answered': (r'Experience is the objective, not depth',)},
    {'slug': 'armour-class-decides-the-fight',
     'raised': (r'hit_chance', r'AC 24', r'2 ?[x*/] ?AC', r'to-hit'),
     'answered': (r'hit_chance',)},
)


def written_by_runs(where=None):
    """Every run's own words: its report, and its notebook as `keep` left it.

    Both, because they hold different things. A report is where a player says
    what the reading lacked; a notebook is where it wrote down the thing it
    measured at the ask it measured it - the store letters that only shift
    *after* the row you bought, the aim that walked zero steps - and those
    lines never reach a report at all. A theme counted from reports only
    would have missed most of what the notebooks know.
    """
    from . import run as run_module
    where = Path(where) if where else run_module.RECORDS
    found = {}
    for report in sorted(where.glob('*/REPORT.md')):
        found.setdefault(report.parent.name, []).append(report)
    for book in sorted(run_module.KNOWLEDGE.glob('*.md')):
        found.setdefault(book.stem, []).append(book)
    return found


def themes(path=INSTRUCTIONS, where=None):
    """Which recurring themes the runs raise, and whether the page answers.

    The loop this serves: after every run, read what it wrote - the report and
    the notebook - and when a theme comes back, put it on the page. A theme
    that recurs and is not there is the page's fault, not the players'.
    """
    page = Path(path).read_text()
    wrote = written_by_runs(where)
    rows = []
    for theme in THEMES:
        raised = []
        for name, paths in sorted(wrote.items()):
            text = '\n'.join(each.read_text() for each in paths)
            if any(re.search(pattern, text, re.IGNORECASE)
                   for pattern in theme['raised']):
                raised.append(name)
        rows.append({'slug': theme['slug'], 'raised_by': raised,
                     'answered': any(re.search(pattern, page, re.IGNORECASE)
                                     for pattern in theme['answered'])})
    return rows


def unanswered(path=INSTRUCTIONS, where=None, recurring=2):
    """Themes several reports raise that the page says nothing about."""
    return [row for row in themes(path, where)
            if len(row['raised_by']) >= recurring and not row['answered']]


def uncited(path=INSTRUCTIONS):
    """Notebooks the page never cites: the input for the next consolidation.

    Not a problem - most runs repeat what the page already says. It is the
    list of runs whose evidence has not been looked at yet.
    """
    text = Path(path).read_text() + VOLUME_TWO.read_text()
    def cited(name):
        # A whole name, so `sonnet-2` is not found inside `sonnet-2.2`.
        return re.search(rf'(?<![A-Za-z0-9_.-]){re.escape(name)}'
                         rf'(?![A-Za-z0-9_.-])', text)
    return [book.stem for book in notebooks() if not cited(book.stem)]


def inputs():
    """What a consolidating session is given, and nothing else."""
    from . import playbooks
    return {
        'notebooks': [str(path) for path in notebooks()],
        'page': str(INSTRUCTIONS),
        'volume_two': str(VOLUME_TWO),
        'playbooks': [row['family'] for row in playbooks.families()],
        'not_yet_cited': uncited(),
        'themes': themes(),
        'unanswered_themes': [row['slug'] for row in unanswered()],
        'runs': recorded_runs(),
    }
