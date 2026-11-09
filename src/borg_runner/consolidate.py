"""Turn notebooks into knowledge, and check that it is knowledge.

A notebook is a log: what one player noticed, in the order it happened, in its
own words. That is the right shape for evidence and the wrong shape for
knowledge - nothing merges, nothing is contradicted, and the twentieth run
would inherit twenty transcripts.

So after every run the notebooks are consolidated into one document, and every
item in it must be **filed against the manual**: under the key it concerns,
under the strategy rule it supports or contradicts, or explicitly as new
ground the manual does not cover. That is what makes it knowledge rather than
a log, and this module is what checks it - the writing is a model's job, the
discipline is not.

Three rules, carried from the knowledge base this feeds:

- an item enters as `hypothesis`. One run noticing something is not a fact;
- it becomes `confirmed` only when a *different* run's evidence agrees;
- a later run that disagrees makes it `contradicted`. It is never deleted,
  because the disagreement is the interesting part.
"""
import json
import re
from pathlib import Path

from . import manual as manual_module, pins, run as run_module

LEARNED = run_module.KNOWLEDGE / 'LEARNED.md'
STATUSES = ('hypothesis', 'confirmed', 'contradicted')

ITEM = re.compile(
    r'^- \[(?P<id>[A-Za-z0-9:_.-]+)\]\s+(?P<statement>.+?)\s*$')
FIELD = re.compile(r'^\s{2,}(?P<name>status|evidence|anchor|supersedes):\s*(?P<value>.+?)\s*$')
REFERENCE = re.compile(r'(?P<run>[A-Za-z0-9_-]+)#(?P<ask>\d+)')


def notebooks(where=None):
    """The promoted notebooks, which are the evidence."""
    where = Path(where) if where else run_module.KNOWLEDGE
    return sorted(p for p in where.glob('*.md')
                  if p.name not in ('LEARNED.md', 'README.md'))


def anchors(name=manual_module.DEFAULT):
    """Everything an item may be filed under, from the manual itself."""
    loaded = manual_module.load(name)
    found = {f'key:{key}' for key in loaded['keys']}
    found |= set(loaded['strategy'])
    found |= {f'goal:{goal}' for goal in loaded['goals']}
    found |= {f'state:{field}' for field in loaded['state_contract']}
    return found


def parse(path=LEARNED):
    """The items, as written. Nothing is inferred."""
    path = Path(path)
    if not path.exists():
        return []
    items, current = [], None
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        head = ITEM.match(line)
        if head:
            current = {'line': number, 'id': head.group('id'),
                       'statement': head.group('statement'),
                       'status': None, 'evidence': [], 'anchor': None,
                       'supersedes': None}
            items.append(current)
            continue
        field = FIELD.match(line)
        if field and current:
            name, value = field.group('name'), field.group('value')
            if name == 'evidence':
                current['evidence'] = [match.groupdict()
                                       for match in REFERENCE.finditer(value)]
                current['evidence_text'] = value
            else:
                current[name] = value
    return items


def known_runs():
    """Run name -> how many asks it had, from whatever records exist."""
    counts = {}
    for record in (pins.ROOT / 'runs').glob('*/record.json'):
        try:
            body = json.loads(record.read_text())
        except ValueError:
            continue
        counts[body.get('run') or record.parent.name] = body.get('asks') or 0
    for kept in notebooks():
        counts.setdefault(kept.stem, 0)
    return counts


def check(path=LEARNED, manual_name=manual_module.DEFAULT):
    """What is wrong with the consolidated document. Empty means it is sound.

    This is the mechanical half of "not just a log": an item that is filed
    nowhere, or cites nothing, or cites a run that does not exist, is not
    knowledge and is reported as a problem.
    """
    items = parse(path)
    if not items:
        return ['there are no items']
    allowed, runs, problems, seen = anchors(manual_name), known_runs(), [], {}
    for item in items:
        where = f"{item['id']} (line {item['line']})"
        if item['id'] in seen:
            problems.append(f'{where}: the id is already used on line {seen[item["id"]]}')
        seen[item['id']] = item['line']
        if item['status'] not in STATUSES:
            problems.append(f'{where}: status is {item["status"]!r}, '
                            f'not one of {", ".join(STATUSES)}')
        anchor = item['anchor']
        if not anchor:
            problems.append(f'{where}: no anchor, so it is filed against nothing')
        elif not anchor.startswith('new:') and anchor not in allowed:
            problems.append(f'{where}: anchor {anchor!r} is not in the manual '
                            f'and is not marked new:')
        if not item['evidence']:
            problems.append(f'{where}: no evidence of the form run#ask')
        for reference in item['evidence']:
            name, ask = reference['run'], int(reference['ask'])
            if name not in runs:
                problems.append(f'{where}: evidence names {name}, which is not a run')
            elif runs[name] and ask > runs[name]:
                problems.append(f'{where}: evidence {name}#{ask} is past '
                                f'{name}\'s {runs[name]} asks')
        if item['status'] == 'confirmed':
            witnesses = {reference['run'] for reference in item['evidence']}
            if len(witnesses) < 2:
                problems.append(f'{where}: confirmed on one run only '
                                f'({", ".join(sorted(witnesses)) or "none"}); '
                                f'a second run has to agree')
    return problems


def inputs(manual_name=manual_module.DEFAULT):
    """What a consolidating session is given, and nothing else."""
    return {
        'notebooks': [str(p) for p in notebooks()],
        'manual': str(manual_module.path(manual_name)),
        'anchors': sorted(anchors(manual_name)),
        'learned': str(LEARNED),
        'runs': known_runs(),
    }
