"""Start a game, record what it was asked and what it was told.

The game plays itself to a halt whenever it wants a key, so a "run" here is
only: a directory, a seed, a started process, and the files that accumulate
in it. Whoever answers - a session, or a replay - is somebody else's business
(see mind.py and replay.py).
"""
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

from . import build, pins

RUNS = pins.ROOT / 'runs'
# A run directory is scratch: git ignores it, and seed plus keys reproduce it
# exactly. The notebook is the one thing that is not reproducible, because it
# is what the player worked out, so it is promoted into knowledge/ and kept.
KNOWLEDGE = pins.ROOT / 'knowledge'
# What is kept in git for a run worth citing. The screens are left out on
# purpose: they are large and `replay` regenerates them byte for byte from the
# seed and the keys, which is the whole claim of D6. What cannot be
# regenerated is the seed, the keys, the reasons and the notes.
ASK = 'ask'
DECISIONS = 'decisions.jsonl'
KEYS = 'input.txt'
RECORD = 'record.json'
NOTEBOOK = 'notebook.md'
NOTEBOOK_LINES = 60
RECORDS = pins.ROOT / 'records'
STANDING = 'standing.json'
ARCHIVED = (RECORD, KEYS, DECISIONS, NOTEBOOK, 'REPORT.md', 'started.json',
            'inherited.json', 'manual.json', 'model-calls.jsonl', STANDING)

# Save and quit. The game writes its savefile and exits cleanly, which is
# both how a run ends and what `takeover` needs to exist (D7).
SAVE_AND_QUIT = '\x18'


def directory(name=None):
    path = RUNS / (name or f'run-{time.strftime("%Y%m%d-%H%M%S")}')
    path.mkdir(parents=True, exist_ok=True)
    (path / ASK).mkdir(exist_ok=True)
    (path / 'save').mkdir(exist_ok=True)
    return path


def inherit(run, notebook_path, log=print):
    """Start a run with somebody else's notes.

    This is the experiment the whole thing is for: if a run that inherits a
    notebook gets deeper than the run that wrote it, accumulated knowledge is
    worth something. The inherited file is recorded by hash, because from the
    moment it is carried forward it is an input under test, not a private
    memory.
    """
    source = Path(notebook_path)
    text = source.read_text()
    (Path(run) / NOTEBOOK).write_text(text)
    carried = {'inherited_from': str(source),
               'lines': len(text.splitlines()),
               'sha256': hashlib.sha256(text.encode()).hexdigest()}
    # Written down, not just logged: what a run started from is part of what
    # the run means, and the overview reads it.
    (Path(run) / 'inherited.json').write_text(
        json.dumps(carried, indent=2, sort_keys=True) + '\n')
    log(f'notebook: inherited {source.name}, {carried["lines"]} lines, '
        f'{carried["sha256"][:12]}')
    return carried


def keep(run, into=None, log=print):
    """Promote a run's notebook into knowledge/, with where it came from.

    Provenance is the whole point: a note is worth what its evidence is worth,
    and the evidence is the run - its seed, its build and its keys, all of
    which replay.
    """
    run = Path(run)
    book = run / NOTEBOOK
    if not book.exists() or not book.read_text().strip():
        raise FileNotFoundError(f'{run.name} kept no notes')
    record = json.loads((run / RECORD).read_text()) if (run / RECORD).exists() else {}
    started = json.loads((run / 'started.json').read_text()) if (run / 'started.json').exists() else {}
    build = started.get('build') or {}
    KNOWLEDGE.mkdir(exist_ok=True)
    target = Path(into) if into else KNOWLEDGE / f'{run.name}.md'
    header = [
        f'# Notes from {run.name}',
        '',
        'Written by the player during one game, in its own words, and promoted',
        'here unedited. Every line carries the ask that taught it; the run',
        'replays from its seed and keys, so any line can be checked.',
        '',
        f'- seed: {started.get("seed")}',
        f'- character: {started.get("character")}',
        f'- game: {build.get("game")} {str(build.get("commit"))[:12]}',
        f'- patch: {str(build.get("patch_sha256"))[:12]}',
        f'- reached: depth {record.get("max_depth")} in {record.get("asks")} asks, '
        f'{record.get("keypresses")} keypresses, turn {record.get("final_turn")}',
        f'- outcome: {record.get("outcome")}',
        f'- keys: {str(record.get("keys_sha256"))[:12]}',
        f'- notebook: {str(record.get("notebook_sha256"))[:12]}',
        '',
        '## The notes',
        '',
    ]
    target.write_text('\n'.join(header) + book.read_text().rstrip() + '\n')
    log(f'kept: {target}')
    return target


def spend(run):
    """What the run cost, from the model calls it recorded.

    A run played by a session has no call log, so its cost is written in by
    whoever ran it (`record --tokens`); a run played through a provider sums
    its own.
    """
    path = Path(run) / 'model-calls.jsonl'
    if not path.exists():
        return None
    calls, tokens, usd, models, seconds = 0, 0, 0.0, set(), 0.0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        call = json.loads(line)
        calls += 1
        usage = (call.get('usage') or {}).get('tokens') or {}
        for field in ('total_tokens', 'input_tokens', 'output_tokens',
                      'input', 'output', 'reasoning'):
            value = usage.get(field)
            if isinstance(value, (int, float)):
                tokens += int(value) if field != 'total_tokens' else 0
                if field == 'total_tokens':
                    tokens += int(value)
        usd += usage.get('cost') or 0.0
        seconds += (call.get('usage') or {}).get('seconds') or 0.0
        served = (call.get('usage') or {}).get('served_model') or call.get('model')
        if served:
            models.add(served)
    return {'model_calls': calls, 'tokens': tokens or None,
            'usd': round(usd, 6) or None, 'models': sorted(models),
            'seconds_per_decision': (round(seconds / calls, 1)
                                     if calls and seconds else None)}


def archive(run, into=None, log=print):
    """Keep a run in git: the seed, the keys, the reasons and the notes.

    runs/ is scratch and ignored, which is right for the screens and wrong for
    everything else - the keys are the recording, and they were being thrown
    away.
    """
    run = Path(run)
    target = Path(into) if into else RECORDS / run.name
    target.mkdir(parents=True, exist_ok=True)

    # The report is derived - `replay` reproduces the screens from the keys
    # and `report` rebuilds the page - but it is kept here anyway, because it
    # is the only *public* form of a replay: the artifact links are private to
    # the owner's account, and the Pages site serves this.
    try:
        from . import report as report_module
        report_module.write(run, into=target / 'report.html')
    except Exception as problem:                      # a run with no screens
        log(f'archive: no report ({problem})')

    kept = []
    for name in ARCHIVED:
        source = run / name
        if source.exists() and source.stat().st_size:
            (target / name).write_bytes(source.read_bytes())
            kept.append(name)
    log(f'archived: {target} ({", ".join(kept)})')
    return target


def start(run, seed, out=None, character=None, resume=False, log=print):
    """Start the game in `run`, waiting for its first answer.

    It is given its own save directory so runs never share one.

    `character` is the name passed as `-u`, and it is **part of the game**:
    the birth prompt arrives with it already filled in, so a replay under a
    different name sees a different screen. It is recorded for that reason,
    and a replay reuses it rather than taking the new directory's name.
    """
    # The game is started in its own directory, so every path it is given
    # must be absolute or it will look for them beside the binary.
    run = Path(run).resolve()
    out = Path(out) if out else build.prepare(log=log)
    game = build.binary(out)
    if not game.exists():
        raise FileNotFoundError(f'no binary at {game}; build first')

    character = character or run.name
    # Runs are independent and may play at the same time - each has its own
    # directory, its own game process and its own notebook. The one thing they
    # share is the savefile, which is named after the character: starting a
    # second run of the same name would delete the first one's save out from
    # under it. Names are unique per run, so this only happens by mistake, and
    # it is cheap to refuse.
    for other in sorted(RUNS.glob('*/started.json')):
        if other.parent == run:
            continue
        try:
            already = json.loads(other.read_text())
        except ValueError:
            continue
        if already.get('character') != character:
            continue
        pid = already.get('pid')
        if pid and Path(f'/proc/{pid}').exists():
            raise RuntimeError(
                f'{other.parent.name} is already playing as {character!r} '
                f'(pid {pid}); two runs cannot share a savefile. Use another '
                f'--name.')

    save = savefile_of(out, character)
    if save.exists() and not resume:
        # The game loads a savefile of this name if one is there, so a replay
        # would resume at turn 41 instead of being born - which is exactly
        # what the first replay did. The run owns its savefile; the finished
        # run keeps a copy of its own under <run>/save.
        log(f'run: removing the previous savefile {save.name}')
        save.unlink()
    # No -dsave: the game ignores it for the savefile's own path and writes
    # into its build's lib/save regardless, so the character name is what
    # keeps runs apart, and `savefile_of` is where to look.
    command = [str(game), '-magent', f'-u{character}',
               '--', f'-d{run / ASK}', f'-s{seed}']
    handle = (run / 'game.log').open('w')
    process = subprocess.Popen(command, cwd=game.parent, stdin=subprocess.DEVNULL,
                               stdout=handle, stderr=subprocess.STDOUT)
    (run / 'started.json').write_text(json.dumps({
        'schema': 'borg-runner/started@1',
        'seed': seed,
        'character': character,
        'pid': process.pid,
        'command': command,
        'savefile': str(savefile_of(out, character)),
        'build': json.loads((out / 'build-identity.json').read_text()),
    }, indent=2, sort_keys=True) + '\n')
    log(f'run: {run} seed {seed} pid {process.pid}')
    return process


def savefile_of(out, character):
    """Where the game writes the save for `character`."""
    return Path(out) / 'build' / 'game' / 'lib' / 'save' / character


def asked(run):
    """The asks that have a question and no answer yet, oldest first."""
    ask = Path(run) / ASK
    waiting = []
    for question in ask.glob('question-*.txt'):
        number = int(question.stem.split('-')[-1])
        if not (ask / f'keys-{number}.txt').exists():
            waiting.append(number)
    return sorted(waiting)


def question(run, number):
    """One question, as the frontend wrote it, plus its screen."""
    ask = Path(run) / ASK
    fields = {}
    for line in (ask / f'question-{number}.txt').read_text().splitlines():
        name, _, value = line.partition(' ')
        fields[name] = value
    screen = (ask / f'screen-{number}.txt').read_text()
    cursor = fields.get('cursor', '').split()
    hp = fields.get('hp', '').split()
    def number_of(name, default=None):
        try:
            return int(fields[name])
        except (KeyError, ValueError):
            return default
    return {'ask': number, 'turn': int(fields.get('turn', 0)), 'screen': screen,
            'depth': int(fields.get('depth', -1)),
            'max_depth': int(fields.get('max_depth', -1)),
            'level': number_of('level'),
            'gold': number_of('gold'),
            'carried': number_of('carried'),
            'race': fields.get('race') or None,
            'class': fields.get('class') or None,
            'hp': {'now': int(hp[0]), 'max': int(hp[1])} if len(hp) == 2 else None,
            'cursor': {'x': int(cursor[0]), 'y': int(cursor[1])} if len(cursor) == 2 else None}


def answer(run, number, keys, reason='', memory=None):
    """Write the keys, and record what they were for.

    The frontend only ever reads the keys. The reason and the memory are
    recorded here, beside them, because what the agent *believed* at the time
    is the most useful column in the report (D4).
    """
    run = Path(run)
    target = run / ASK / f'keys-{number}.txt'
    part = run / ASK / f'.keys-{number}.part'
    part.write_text(keys)
    part.rename(target)                      # the frontend polls for existence
    asked = question(run, number)
    entry = {'ask': number, 'turn': asked['turn'], 'depth': asked['depth'],
             'keys': keys, 'reason': reason}
    if memory is not None:
        entry['memory'] = memory
    with (run / DECISIONS).open('a') as log:
        log.write(json.dumps(entry, sort_keys=True) + '\n')
    return target


# The tombstone, which is the only place the game states the cause. It is
# drawn inside a box, so the bars are stripped before matching:
#     |        Killed on Level 1        |
#     |       by a small kobold.        |
TOMB = re.compile(r'Killed on Level\s+(?P<depth>\d+)\s+by\s+(?P<cause>[^.]+)\.')


def death_of(run, look_at=6):
    """How the character died, from the game's own tombstone, or None.

    A run that ends in a death is the thing this repository exists to
    produce, so the record has to say so rather than leaving the outcome as
    "playing" because nobody asked.
    """
    ask = Path(run) / ASK
    screens = sorted(ask.glob('screen-*.txt'),
                     key=lambda path: int(path.stem.split('-')[-1]))
    for screen in reversed(screens[-look_at:]):
        text = screen.read_text()
        if 'RIP' not in text:
            continue
        # The tomb is a box with the game's own menu drawn to its right, so
        # each line's content is what lies between the first two bars; the
        # rest is scenery. Taking the whole line matched the fixture and not
        # the game.
        inside = []
        for line in text.splitlines():
            parts = line.split('|')
            inside.append(parts[1] if len(parts) > 2 else line.strip(' |'))
        found = TOMB.search(' '.join(' '.join(inside).split()))
        if found:
            return {'died': True, 'depth': int(found.group('depth')),
                    'cause': found.group('cause').strip(),
                    'tombstone': screen.name}
        return {'died': True, 'depth': None, 'cause': None,
                'tombstone': screen.name}
    return None


def questions(run):
    """Every ask the game made, answered or not.

    The last ask is usually unanswered - the game asked once more and the run
    ended - and on a death that unanswered ask is the tombstone. Counting only
    answered asks stopped the record and the replay one frame short of the
    death itself.
    """
    ask = Path(run) / ASK
    return sorted(int(path.stem.split('-')[-1])
                  for path in ask.glob('question-*.txt'))


def reading_note(run):
    """The first note, which the brief requires to list what was opened.

    Nothing else records whether a player read anything, and a run's own
    final report is written afterwards and has been generous with itself: one
    report claimed three strategy chapters its contemporaneous note did not.
    """
    # A note *about files*, not merely a note containing the word "read":
    # the first attempt matched "read the letter from the list" in a note
    # about shopping.
    names = ('.md', '.rst', 'docs/', 'knowledge/', 'manuals/', 'vendor/')
    for line in notebook(run, lines=10 ** 6).splitlines():
        said = line.lstrip('- ').strip()
        if said and any(name in said for name in names):
            return said
    return None


def read_for_its_character(run, note=None, character_class=None):
    """Whether the reading note names the class the game drew.

    The character is drawn at random, so the playbook that matters is not
    knowable in advance - which is exactly why a run has to say it read the
    one it got, rather than the one it would have chosen.
    """
    note = note if note is not None else reading_note(run)
    if not note or not character_class:
        return None
    return character_class.lower() in note.lower()


def notebook(run, lines=NOTEBOOK_LINES):
    """The player's own notes, as the player left them.

    Nothing here writes to this file except `remember`, and nothing here ever
    edits or corrects it: a trick the player got wrong is a thing we want to
    see, not hide (D4). The player may rewrite it to prune, which is why only
    the last lines are shown - a notebook that grows without bound would
    crowd out the screen.
    """
    path = Path(run) / NOTEBOOK
    if not path.exists():
        return ''
    kept = path.read_text().splitlines()
    return '\n'.join(kept[-lines:])


def remember(run, note, ask=None):
    """Append a note. The player's words, with the ask that taught it."""
    path = Path(run) / NOTEBOOK
    # The player may or may not write its own bullet; one is enough.
    said = note.strip().lstrip('-').strip()
    line = f'- {said}' + (f' (ask {ask})' if ask is not None else '')
    with path.open('a') as book:
        book.write(line + '\n')
    return path


def decisions(run):
    path = Path(run) / DECISIONS
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def memory_now(run):
    """The newest memory the agent wrote, which goes back in the next prompt."""
    for entry in reversed(decisions(run)):
        if entry.get('memory') is not None:
            return entry['memory']
    return None


def keys_sent(run):
    """Every key, in order: the whole of the recording (D6)."""
    return ''.join(entry['keys'] for entry in decisions(run))


def alive(process):
    return process is not None and process.poll() is None


def stop(run, process, log=print, patience=20.0):
    """Ask the game to save and quit, and wait for it.

    The game can only be told anything when it asks, so this waits to be
    asked before answering - the first version terminated the process while
    it was still waiting for a key, and the savefile was never written, which
    is the one thing `takeover` needs to exist.

    A quit may be confirmed, or interrupted by "you have unsaved..." style
    prompts, so it answers a few asks rather than one.
    """
    if not alive(process):
        return
    deadline = time.monotonic() + patience
    answered = 0
    while alive(process) and time.monotonic() < deadline and answered < 5:
        waiting = asked(run)
        if not waiting:
            time.sleep(0.1)
            continue
        # Ctrl-X saves and quits; the "Saving game... done. Press Return
        # (or Escape)." footer that follows takes Escape, not Return.
        keys = SAVE_AND_QUIT if answered == 0 else '\\e'
        answer(run, waiting[0], keys, reason='the run was stopped')
        answered += 1
        for _ in range(int(patience * 10)):
            if not alive(process) or asked(run):
                break
            time.sleep(0.1)
    if alive(process):
        log('run: the game did not stop when asked; terminating')
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    else:
        log('run: the game saved and quit')


def recover_standing(run, from_replay, log=print):
    """Keep a standing recovered by replaying an older run's keys.

    A run played under a build that did not report the character's level,
    gold or gear can only have those recovered by replaying its keys. Written
    into the run as `standing.json`, it survives every later rewrite of the
    record - which three hand-made backfills did not.
    """
    replayed = json.loads((Path(from_replay) / RECORD).read_text())
    kept = {field: replayed.get(field)
            for field in ('race', 'class', 'character', 'character_level',
                          'max_character_level', 'gold', 'carried_value',
                          'wealth', 'hp')
            if replayed.get(field) is not None}
    kept['standing_from'] = (f'{Path(from_replay).name}, a replay of this '
                             f"run's archived keys")
    (Path(run) / STANDING).write_text(
        json.dumps(kept, indent=2, sort_keys=True) + '\n')
    log(f'standing: recovered {len(kept) - 1} fields from {Path(from_replay).name}')
    return kept


def _standing(run, asked_at):
    """How the character stood, at the end and at its best.

    The value carried is the game's own `object_value()` over the whole gear
    list, so a run says not only how deep it went but how well equipped it was
    when it got there - which is what tells a lucky dive from a good one.
    """
    recovered = Path(run) / STANDING
    seen = [question(run, number) for number in asked_at] if asked_at else []
    seen = [asked for asked in seen if asked.get('level') not in (None, -1)]
    if not seen:
        empty = {'character_level': None, 'gold': None, 'carried_value': None,
                 'wealth': None, 'race': None, 'class': None,
                 'character': None, 'standing_from': None}
        if recovered.exists():
            empty.update(json.loads(recovered.read_text()))
        return empty
    last = seen[-1]
    # The *last* ask that names a race, not the first: before birth finishes
    # the player struct holds the menu's defaults, which are the last race and
    # class in the lists, so taking the first ask labelled every run a Kobold
    # Blackguard.
    born = next((asked for asked in reversed(seen)
                 if asked.get('race') and asked['race'] != '?'), last)
    return {
        'race': born.get('race'),
        'class': born.get('class'),
        'character': (f"{born.get('race')} {born.get('class')}"
                      if born.get('race') and born.get('race') != '?' else None),
        'character_level': last['level'],
        'max_character_level': max(asked['level'] for asked in seen),
        'gold': last.get('gold'),
        'carried_value': last.get('carried'),
        # What the character was worth all told, the way a player counts it.
        'wealth': (last.get('gold') or 0) + (last.get('carried') or 0),
        'hp': last.get('hp'),
    }


def write_record(run, process=None, outcome=None, cost=None):
    """What the run was, in one file, with the keys beside it.

    The savefile is copied in, because the build tree's `lib/save` is scratch
    space that the next run of the same character clears.
    """
    run = Path(run)
    started = json.loads((run / 'started.json').read_text())
    # A record may be written for a run started by an older version, or by a
    # test; a missing savefile is not a reason to fail.
    live = Path(started.get('savefile') or (run / 'no-savefile'))
    if live.exists():
        (run / 'save').mkdir(exist_ok=True)
        kept = run / 'save' / live.name
        if not kept.exists() or kept.read_bytes() != live.read_bytes():
            kept.write_bytes(live.read_bytes())
    keys = keys_sent(run)
    (run / KEYS).write_text(keys)
    screens = sorted((run / ASK).glob('screen-*.txt'))
    taken = decisions(run)
    asked_at = questions(run)
    death = death_of(run)
    if death:
        outcome = 'died'
    record = {
        'schema': 'borg-runner/run-record@1',
        'run': run.name,
        'seed': started['seed'],
        'build': started['build'],
        'asks': len(taken),
        'keypresses': len(keys),
        # The furthest turn the game reached, which is the last *question*:
        # on a death the fatal keys are answered and the tombstone is not.
        'final_turn': (question(run, asked_at[-1])['turn'] if asked_at
                       else (taken[-1]['turn'] if taken else 0)),
        'asks_made': len(asked_at),
        'max_depth': max([(entry.get('depth') or 0) for entry in taken]
                         + [(question(run, number)['depth'] or 0)
                            for number in asked_at]) if asked_at or taken else 0,
        'screens': len(screens),
        'notebook_lines': len(notebook(run, lines=10**6).splitlines()),
        'notebook_sha256': (hashlib.sha256(
            (run / NOTEBOOK).read_bytes()).hexdigest()
            if (run / NOTEBOOK).exists() else None),
        'keys_sha256': hashlib.sha256(keys.encode()).hexdigest(),
        'screens_sha256': hashlib.sha256(
            b''.join(p.read_bytes() for p in screens)).hexdigest(),
        'savefile_sha256': (hashlib.sha256(live.read_bytes()).hexdigest()
                            if live.exists() else None),
        'outcome': outcome or ('playing' if alive(process) else 'ended'),
        'cost': cost or spend(run),
        **_standing(run, asked_at),
        'died': bool(death),
        'killed_by': (death or {}).get('cause'),
        'death_depth': (death or {}).get('depth'),
        'exit_code': process.poll() if process else None,
    }
    # A record must not lose what it already knew. The standing of a run
    # played under an older build can only be recovered by replaying its
    # keys, and recomputing from its own questions yields nothing - so a
    # value already there survives a later rewrite, and `standing_from` says
    # where it came from.
    if (run / RECORD).exists():
        before = json.loads((run / RECORD).read_text())
        for field in ('race', 'class', 'character', 'character_level',
                      'max_character_level', 'gold', 'carried_value',
                      'wealth', 'hp', 'standing_from', 'replay_url', 'cost'):
            if record.get(field) is None and before.get(field) is not None:
                record[field] = before[field]
    # Last, because it is checked against the class the record ends up with,
    # which for an older run is the one recovered by replaying its keys.
    note = reading_note(run)
    record['read_before_playing'] = note
    record['read_its_own_playbook'] = read_for_its_character(
        run, note=note, character_class=record.get('class'))
    (run / RECORD).write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    return record


def live(run):
    """Whether this run's game process is still there."""
    started = Path(run) / 'started.json'
    if not started.exists():
        return None
    try:
        pid = json.loads(started.read_text()).get('pid')
    except ValueError:
        return None
    return bool(pid) and Path(f'/proc/{pid}').exists()


def status(where=None):
    """Where every run stands, finished or not.

    Answers the question a person actually has while a run is playing - how
    far has it got, is it still going, and when will it stop - without having
    to read a log or ask anyone.
    """
    where = Path(where) if where else RUNS
    out = []
    for started in sorted(where.glob('*/started.json')):
        run = started.parent
        taken = decisions(run)
        asked_at = questions(run)
        record = {}
        if (run / RECORD).exists():
            try:
                record = json.loads((run / RECORD).read_text())
            except ValueError:
                record = {}
        seconds = []
        calls = run / 'model-calls.jsonl'
        if calls.exists():
            for line in calls.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    took = (json.loads(line).get('usage') or {}).get('seconds')
                except ValueError:
                    continue
                if took:
                    seconds.append(took)
        pace = round(sorted(seconds)[len(seconds) // 2], 1) if seconds else None
        last = question(run, asked_at[-1]) if asked_at else {}
        # A dead character's game is still running: it draws the tombstone and
        # waits for a key. Reporting that as "playing" is a lie the status
        # line should not tell.
        running = live(run)
        state = ('dead at the tomb' if record.get('died') and running
                 else 'dead' if record.get('died')
                 else 'playing' if running
                 else 'stopped' if running is False else '?')
        out.append({
            'run': run.name,
            'state': state,
            'playing': running,
            'answered': len(taken),
            'asked': len(asked_at),
            'turn': last.get('turn'),
            'depth': last.get('depth'),
            'character': record.get('character') or last.get('race'),
            'outcome': ('died: ' + str(record.get('killed_by'))
                        if record.get('died') else record.get('outcome')),
            'seconds_per_decision': pace,
            'notes': len(notebook(run, lines=10 ** 6).splitlines()),
        })
    return out
