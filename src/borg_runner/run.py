"""Start a game, record what it was asked and what it was told.

The game plays itself to a halt whenever it wants a key, so a "run" here is
only: a directory, a seed, a started process, and the files that accumulate
in it. Whoever answers - a session, or a replay - is somebody else's business
(see mind.py and replay.py).
"""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

from . import build, pins

RUNS = pins.ROOT / 'runs'
ASK = 'ask'
DECISIONS = 'decisions.jsonl'
KEYS = 'input.txt'
RECORD = 'record.json'

# Save and quit. The game writes its savefile and exits cleanly, which is
# both how a run ends and what `takeover` needs to exist (D7).
SAVE_AND_QUIT = '\x18'


def directory(name=None):
    path = RUNS / (name or f'run-{time.strftime("%Y%m%d-%H%M%S")}')
    path.mkdir(parents=True, exist_ok=True)
    (path / ASK).mkdir(exist_ok=True)
    (path / 'save').mkdir(exist_ok=True)
    return path


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
    return {'ask': number, 'turn': int(fields.get('turn', 0)), 'screen': screen,
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
    entry = {'ask': number, 'turn': question(run, number)['turn'],
             'keys': keys, 'reason': reason}
    if memory is not None:
        entry['memory'] = memory
    with (run / DECISIONS).open('a') as log:
        log.write(json.dumps(entry, sort_keys=True) + '\n')
    return target


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


def write_record(run, process=None, outcome=None):
    """What the run was, in one file, with the keys beside it.

    The savefile is copied in, because the build tree's `lib/save` is scratch
    space that the next run of the same character clears.
    """
    run = Path(run)
    started = json.loads((run / 'started.json').read_text())
    live = Path(started['savefile'])
    if live.exists():
        (run / 'save').mkdir(exist_ok=True)
        kept = run / 'save' / live.name
        if not kept.exists() or kept.read_bytes() != live.read_bytes():
            kept.write_bytes(live.read_bytes())
    keys = keys_sent(run)
    (run / KEYS).write_text(keys)
    screens = sorted((run / ASK).glob('screen-*.txt'))
    taken = decisions(run)
    record = {
        'schema': 'borg-runner/run-record@1',
        'run': run.name,
        'seed': started['seed'],
        'build': started['build'],
        'asks': len(taken),
        'keypresses': len(keys),
        'final_turn': taken[-1]['turn'] if taken else 0,
        'screens': len(screens),
        'keys_sha256': hashlib.sha256(keys.encode()).hexdigest(),
        'screens_sha256': hashlib.sha256(
            b''.join(p.read_bytes() for p in screens)).hexdigest(),
        'savefile_sha256': (hashlib.sha256(live.read_bytes()).hexdigest()
                            if live.exists() else None),
        'outcome': outcome or ('playing' if alive(process) else 'ended'),
        'exit_code': process.poll() if process else None,
    }
    (run / RECORD).write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    return record
