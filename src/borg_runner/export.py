"""The export: what the runs have established, for the repository's consumer.

Everything else here is for playing or for the next player. This is the one
document written **outward**: `ACCUMULATED_KNOWLEDGE.md` at the root, for
**borg-reborn-rs**, the Rust Borg being rebuilt, which plays this game without
reading a manual and cannot ask a run what it meant. So the export is a
distillation of the *reports* - what each player concluded, not its keystrokes
- with the evidence attached and the confidence stated.

Three things keep it honest, and this module checks the first two:

- **every claim names its source**: a run (`sonnet-2#124`, or the run's
  report), or a file in the game's own tree. A claim with neither is a
  superstition and has no business crossing a repository boundary;
- **a run it names must exist**;
- and the edition says what it read, so a reader can tell what the corpus was
  when it was written. The accumulation happens from time to time, not per
  run, so `missing()` is how a session sees what has arrived since.

**No player reads it.** Not a rule of taste: it aggregates every run's report,
including runs of the seed the player is on, which is the one thing a player
is not given (D9). `docs/EXPORT.md` is the process; the prompts do not mention
the file at all, and a test holds that.
"""
import json
import re
from pathlib import Path

from . import pins, run as run_module

ACCUMULATED = pins.ROOT / 'ACCUMULATED_KNOWLEDGE.md'
EDITION = re.compile(r'^Edition (?P<number>\d+), (?P<date>\d{4}-\d{2}-\d{2})',
                     re.MULTILINE)


def reports(where=None):
    """Every run that wrote one, which is what the export is made of."""
    where = Path(where) if where else run_module.RECORDS
    return sorted(path for path in where.glob('*/REPORT.md'))


def corpus(where=None):
    """The numbers the edition header has to agree with."""
    where = Path(where) if where else run_module.RECORDS
    runs, asks, keys, deepest, deaths = [], 0, 0, 0, 0
    for record_path in sorted(where.glob('*/record.json')):
        record = json.loads(record_path.read_text())
        name = record.get('run') or record_path.parent.name
        runs.append(name)
        asks += record.get('asks') or 0
        keys += record.get('keypresses') or 0
        deepest = max(deepest, record.get('max_depth') or 0)
        deaths += 1 if record.get('died') else 0
    return {'runs': runs, 'reports': [p.parent.name for p in reports(where)],
            'asks': asks, 'keypresses': keys, 'deepest': deepest,
            'deaths': deaths}


def names_in(text, among):
    """Which of these run names the text mentions, as whole names."""
    return sorted(name for name in among
                  if re.search(rf'(?<![A-Za-z0-9_.-]){re.escape(name)}'
                               rf'(?![A-Za-z0-9_.-])', text))


def missing(path=None, where=None):
    """Runs whose report the export has not read yet.

    Not an error: the accumulation is periodic by design. It is the list a
    session is handed when it comes to write the next edition.
    """
    path = Path(path) if path else ACCUMULATED
    if not path.exists():
        return [p.parent.name for p in reports(where)]
    text = path.read_text()
    wrote = [p.parent.name for p in reports(where)]
    return [name for name in wrote if name not in names_in(text, wrote)]


def check(path=None, where=None):
    """What is wrong with the export. Empty means it can be handed over.

    Staleness is not wrong - `missing()` says what is new, and the owner
    decides when to accumulate. What is wrong is an edition that cannot be
    placed in time, or a claim about a run that does not exist.
    """
    path = Path(path) if path else ACCUMULATED
    if not path.exists():
        return [f'{path.name} does not exist; see docs/EXPORT.md']
    text = path.read_text()
    problems = []
    if not EDITION.search(text):
        problems.append('no "Edition <n>, <yyyy-mm-dd>" line, so a reader '
                         'cannot tell what the corpus was when it was written')
    known = set(corpus(where)['runs'])
    cited = set(re.findall(r'(?<![A-Za-z0-9_.-])([a-z][a-z0-9]*(?:-[a-z0-9.]+)+)#\d+',
                           text))
    for name in sorted(cited - known):
        problems.append(f'cites {name}, which is not a run')
    for name, ask in re.findall(r'(?<![A-Za-z0-9_.-])([A-Za-z0-9][A-Za-z0-9_.-]*?)#(\d+)',
                                text):
        if name in known:
            asks = _asks_of(name, where)
            if asks and int(ask) > asks:
                problems.append(f'cites {name}#{ask}, past {name}\'s {asks} asks')
    if 'borg-reborn-rs' not in text:
        problems.append('does not say who it is for; the consumer is '
                        'borg-reborn-rs (docs/EXPORT.md)')
    return problems


def _asks_of(name, where=None):
    where = Path(where) if where else run_module.RECORDS
    record = where / name / 'record.json'
    if not record.exists():
        return 0
    body = json.loads(record.read_text())
    return body.get('asks_made') or body.get('asks') or 0


def inputs(where=None):
    """What a session writing the next edition is given, and nothing else."""
    from . import playbooks
    counted = corpus(where)
    return {
        'export': str(ACCUMULATED),
        'process': str(pins.ROOT / 'docs' / 'EXPORT.md'),
        'reports': [str(path) for path in reports(where)],
        'notebooks': [str(path) for path in
                      sorted(run_module.KNOWLEDGE.glob('*.md'))],
        'playbooks': [row['family'] for row in playbooks.families()],
        'corpus': counted,
        'not_yet_read': missing(where=where),
        'wrote_no_report': sorted(set(counted['runs']) - set(counted['reports'])),
    }
