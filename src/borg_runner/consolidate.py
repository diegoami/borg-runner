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


def uncited(path=INSTRUCTIONS):
    """Notebooks the page never cites: the input for the next consolidation.

    Not a problem - most runs repeat what the page already says. It is the
    list of runs whose evidence has not been looked at yet.
    """
    text = Path(path).read_text() + VOLUME_TWO.read_text()
    def cited(name):
        # A whole name, so `sonnet-2` is not found inside `sonnet-2-again`.
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
        'runs': recorded_runs(),
    }
