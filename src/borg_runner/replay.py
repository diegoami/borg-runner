"""Replay a recording, and take a game over from one.

Replay is the same loop with the keys read from the record instead of asked
for, which is what makes the claim in D6 checkable: if seed plus keys is the
whole of the recording, the screens come back identical.
"""
import json
import time
from pathlib import Path

from . import run as run_module

SCREENS = 'replay-screens'


def recorded_keys(original):
    """The keys of the original run, ask by ask."""
    return [entry['keys'] for entry in run_module.decisions(original)]


def replay(original, into, out=None, seed=None, stop_after=None, log=print):
    """Play the recorded keys again and compare every screen.

    `stop_after` stops once that game turn is reached, which is how a takeover
    gets to the position it wants.
    """
    original, into = Path(original).resolve(), Path(into).resolve()
    record = json.loads((original / run_module.RECORD).read_text())
    keys = recorded_keys(original)
    fresh = run_module.directory(into.name) if into.parent == run_module.RUNS else into
    fresh.mkdir(parents=True, exist_ok=True)
    (fresh / run_module.ASK).mkdir(exist_ok=True)
    (fresh / 'save').mkdir(exist_ok=True)

    started = json.loads((original / 'started.json').read_text())
    process = run_module.start(
        fresh, seed if seed is not None else record['seed'], out=out,
        # the original's character name, because the game shows it (D6)
        character=started.get('character', original.name), log=log)
    differences, replayed, reached = [], 0, 0
    try:
        for number, press in enumerate(keys, start=1):
            if not wait_for(fresh, number, process):
                break
            asked = run_module.question(fresh, number)
            reached = asked['turn']
            before = original / run_module.ASK / f'screen-{number}.txt'
            if before.exists() and before.read_text() != asked['screen']:
                differences.append({'ask': number, 'turn': asked['turn']})
            replayed += 1
            if stop_after is not None and asked['turn'] >= stop_after:
                log(f'replay: reached turn {asked["turn"]}, stopping')
                break
            run_module.answer(fresh, number, press,
                              reason='replayed from ' + original.name)
    finally:
        run_module.stop(fresh, process, log=log)

    verdict = {
        'schema': 'borg-runner/replay@1',
        'original': original.name,
        'replay': fresh.name,
        'asks_replayed': replayed,
        'asks_recorded': len(keys),
        'turn_reached': reached,
        'identical': not differences and replayed > 0,
        'differences': differences[:20],
        'stopped_after_turn': stop_after,
    }
    (fresh / 'replay.json').write_text(json.dumps(verdict, indent=2, sort_keys=True) + '\n')
    run_module.write_record(fresh, outcome='replay')
    return verdict


def wait_for(run, number, process, timeout=60):
    """Wait until the frontend has asked question `number`."""
    deadline = time.monotonic() + timeout
    question = Path(run) / run_module.ASK / f'question-{number}.txt'
    while not question.exists():
        if not run_module.alive(process):
            return False
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)
    return True


def takeover(original, into, at_turn, out=None, log=print):
    """Replay to a turn, save, and say how to open the savefile in X11.

    No new C: the game saves on Ctrl-X, so the person opens the same savefile
    with the X11 frontend and carries on from exactly where the agent was
    (D7, D11).
    """
    from . import build

    verdict = replay(original, into, out=out, stop_after=at_turn, log=log)
    fresh = Path(into)
    out = Path(out) if out else build.prepare(log=lambda *a: None)
    started = json.loads((fresh / 'started.json').read_text())
    save = Path(started['savefile'])
    command = [str(build.binary(out)), '-mx11', f'-u{started["character"]}']
    verdict['savefile'] = str(save)
    verdict['savefile_written'] = save.exists()
    verdict['takeover_command'] = ' '.join(command)
    (fresh / 'takeover.json').write_text(json.dumps(verdict, indent=2, sort_keys=True) + '\n')
    log('takeover: ' + verdict['takeover_command'])
    return verdict
