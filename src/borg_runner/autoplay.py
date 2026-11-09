"""Play a run with a model, through OpenCode.

OpenCode already holds the owner's provider credentials, so this repository
still has no key, no base URL and no HTTP client of its own (D8 stands; D13
says how). One OpenCode session per run, which matters more than it sounds:
the session is stateful *and* prompt-cached between invocations - measured at
532 fresh input tokens against 12,576 read from cache on a third call - so the
manuals are sent once and each later decision costs only the new screen.

The model answers with one JSON object. Everything it says about why, and
everything it chooses to remember, is recorded beside its keys.
"""
import json
import re
import subprocess
import time
from pathlib import Path

from . import pins, run as run_module

CALLS = 'model-calls.jsonl'
# Session ids must start with "ses"; OpenCode refuses anything else.
SESSION = 'ses_borgrunner_{run}'

INSTRUCTIONS = """You are playing Angband 4.2.6. You see the screen the game
draws, 24 lines of it, and you answer with keys. Nothing is parsed for you and
nothing is remembered for you.

Answer with one JSON object and no other text:

{"keys": "<the keys to press>", "reason": "<one line>", "memory": "<what you
want to remember, or omit to keep the last one>"}

Keys: every character you put in "keys" is a key the game receives. Four
escapes exist for keys that cannot be typed:

  \\n  Enter (the game's own KC_ENTER; a prompt saying "Press Return" needs this)
  \\e  Escape
  \\t  Tab
  \\\\  a literal backslash

Send several keys at once when you know what you want - "2222" walks four
steps south in one turn of this conversation. Use the game's own multi-turn
commands rather than one step at a time: "." and a direction runs along a
corridor until the game stops you, "R&\\n" rests until healed or disturbed,
"v" then an item letter then a target throws.

The header of each screen says `cursor at x,y`. In a menu that is the
highlight: Angband's birth menus move it when you press a letter and select
on \\n, so "b" then "\\n" picks the second item.

Your memory is yours. Press "i" once and remember your inventory; press "e"
for equipment and "b" for a spell book. After that assume what you carry is
still there unless you used it, dropped it, or something burnt or stole it -
and when you are unsure, spend a keypress and look. Nothing will correct you,
deliberately: believing you still have a Phase Door when you do not is a real
mistake and we want to see it, not hide it.

Rules: change no setting and no option. Do not call anything a defect. If you
think a player could do better, say what would settle it.

Play well. Go as deep as you can without throwing the character away."""


def first_message(screen, memory=None):
    text = [INSTRUCTIONS, '', 'The manual pages are attached; read what you need.',
            '', '=== SCREEN ===', screen]
    if memory:
        text += ['=== YOUR MEMORY ===', memory]
    return '\n'.join(text)


def later_message(screen, memory=None):
    text = ['=== SCREEN ===', screen]
    if memory:
        text += ['=== YOUR MEMORY (yours; nothing here maintains it) ===', memory]
    text += ['', 'One JSON object: keys, reason, and memory if it changed.']
    return '\n'.join(text)


def manual_files():
    """The pages worth attaching once, at the pin. Everything else is lookup."""
    game = pins.clone('angband')
    wanted = [game / 'docs' / 'command.rst', game / 'docs' / 'guide.rst']
    return [path for path in wanted if path.exists()]


def call(message, model, session, attach=(), agent=None, timeout=600, cwd=None):
    """One OpenCode run, returning its text and what it cost."""
    command = ['opencode', 'run', '-m', model, '--session', session,
               '--archived', '--format', 'json']
    if agent:
        command += ['--agent', agent]
    for path in attach:
        command += ['--file', str(path)]
    command.append(message)
    done = subprocess.run(command, capture_output=True, text=True,
                          timeout=timeout, cwd=cwd)
    text, usage, problem = [], {}, None
    for line in done.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.get('type')
        part = event.get('part') or {}
        if kind == 'text' and part.get('text'):
            text.append(part['text'])
        elif kind == 'step_finish':
            usage = {'tokens': part.get('tokens'), 'cost': part.get('cost')}
        elif kind == 'error':
            problem = (event.get('error') or {}).get('message')
    return {'text': '\n'.join(text), 'usage': usage, 'error': problem,
            'returncode': done.returncode, 'stderr': done.stderr[-2000:]}


def decision_of(text):
    """The JSON object out of a reply, however it was wrapped."""
    if not text:
        return None
    fenced = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        brace = re.search(r'\{.*\}', text, re.S)
        candidate = brace.group(0) if brace else None
    if candidate is None:
        return None
    try:
        answer = json.loads(candidate)
    except ValueError:
        return None
    return answer if isinstance(answer, dict) and 'keys' in answer else None


def autoplay(run, model, process=None, max_asks=200, agent=None, log=print):
    """Answer this run's questions with a model until it stops or runs out."""
    from . import replay as replay_module

    run = Path(run)
    session = SESSION.format(run=re.sub(r'[^a-zA-Z0-9]', '', run.name))
    calls = (run / CALLS).open('a')
    answered = 0
    try:
        while answered < max_asks:
            waiting = run_module.asked(run)
            if not waiting:
                if process is not None and not run_module.alive(process):
                    log('autoplay: the game has ended')
                    break
                time.sleep(0.2)
                continue
            number = waiting[0]
            asked = run_module.question(run, number)
            memory = run_module.memory_now(run)
            screen = f'ask {number}, turn {asked["turn"]}'
            if asked.get('cursor'):
                screen += f', cursor at {asked["cursor"]["x"]},{asked["cursor"]["y"]}'
            screen += '\n' + asked['screen']

            first = answered == 0
            result = call(
                first_message(screen, memory) if first else later_message(screen, memory),
                model, session,
                attach=manual_files() if first else (),
                agent=agent, cwd=pins.ROOT)
            decision = decision_of(result['text'])
            calls.write(json.dumps({
                'ask': number, 'turn': asked['turn'], 'model': model,
                'session': session, 'usage': result['usage'],
                'error': result['error'], 'parsed': decision is not None,
                'reply': result['text'][:4000],
            }, sort_keys=True) + '\n')
            calls.flush()

            if decision is None:
                log(f'autoplay: ask {number}: no JSON object in the reply; stopping')
                log((result['error'] or result['text'] or result['stderr'])[:300])
                break
            run_module.answer(run, number, str(decision['keys']),
                              reason=str(decision.get('reason', ''))[:300],
                              memory=decision.get('memory'))
            answered += 1
            log(f'autoplay: ask {number} turn {asked["turn"]}: '
                f'{decision["keys"]!r} - {decision.get("reason", "")[:70]}')
            if not replay_module.wait_for(run, number + 1, process, timeout=120):
                log('autoplay: the game asked nothing more')
                break
    finally:
        calls.close()
    return answered
