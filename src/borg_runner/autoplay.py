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
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import pins, run as run_module

OPENROUTER = 'https://openrouter.ai/api/v1/chat/completions'
# The variable is named here; its value is read from the environment at call
# time and never written to a record, a log or a reply.
KEY_ENV = 'OPENROUTER_API_KEY' 

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

Take the easy option at birth. Your character is drawn, not chosen: at the
race menu press "*" and at the class menu press "*". At the stat screen choose
point-based ("a") and accept the allocation the game has already filled in by
pressing Enter - it is the game's own recommendation. Do not move points
around: a character is made by how it is played, not by two points of
strength, and deliberating there has cost a run thousands of tokens and
got it nothing. The game's own birth screen offers it. Then read what
you need about the class you were given. A player who picks its class every
time produces notes that read as general when they are one class's notes.

Rules: change no setting and no option. Do not call anything a defect. If you
think a player could do better, say what would settle it.

You may add "note": "<one line>" to your answer for something the game taught
you that the manual did not say. Those notes are kept, printed back to you
with every later screen, and given to whoever plays next, so write the
evidence into them: what the screen said, and at which ask.

Play well. Go as deep as you can without throwing the character away."""


def keys_reference(limit=80):
    """The command list, out of the game's own manual at the pin.

    The OpenCode backend can attach the manual as a file; a direct API call
    cannot, so the keys have to be in the prompt. They are extracted rather
    than written out, so this says what the manual says - including
    `Path to nearest unknown grid (p)`, which is the cheapest way down.
    """
    manual = pins.clone('angband') / 'docs' / 'command.rst'
    if not manual.exists():
        return ''
    found = re.findall(r'^([A-Z][^(\n]{2,40})\(``([^`]+)``\)',
                       manual.read_text(), re.M)
    lines = [f'  {key:<4} {name.strip()}' for name, key in found[:limit]]
    return ('The commands, from docs/command.rst at the pinned game '
            f'({pins.commit("angband")[:12]}):\n' + '\n'.join(lines))


def first_message(screen, memory=None):
    text = [INSTRUCTIONS, '', 'The manual pages are attached; read what you need.',
            '', '=== SCREEN ===', screen]
    if memory:
        text += ['=== YOUR MEMORY ===', memory]
    return '\n'.join(text)


def later_message(screen, memory=None, book=None):
    text = ['=== SCREEN ===', screen]
    if memory:
        text += ['=== YOUR MEMORY (yours; nothing here maintains it) ===', memory]
    if book:
        text += ['=== YOUR NOTEBOOK (yours; nothing here writes or corrects it) ===',
                 book]
    text += ['', 'One JSON object: keys, reason, and memory or note if either '
                 'changed.']
    return '\n'.join(text)


def manual_files():
    """What is attached on the first ask, once, and then cached.

    The manual pages at the pin, and everything in knowledge/ - the filed
    knowledge and the cheat sheets earlier runs paid for. A model playing
    through a provider gets what a session playing here gets; it would be a
    poor comparison otherwise.
    """
    # The distillate, not the raw manuals: 23 KB that gets read against 66 KB
    # that gets skimmed. Three runs recorded what they opened and every one
    # read a section or two of command.rst and a fraction of chapter 15.
    wanted = [pins.ROOT / 'manuals' / 'INSTRUCTIONS.md']
    if not any(path.exists() for path in wanted):       # before the distillate
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
    began = time.monotonic()
    done = subprocess.run(command, capture_output=True, text=True,
                          timeout=timeout, cwd=cwd)
    seconds = round(time.monotonic() - began, 2)
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
    # The round trip, measured. A decision through OpenCode spawns a process,
    # which talks to its server, rebuilds the session and calls the provider
    # across the network; a subagent is one in-process call. The difference is
    # the backend, not the model, and it belongs in the record.
    usage['seconds'] = seconds
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


def call_openrouter(messages, model, timeout=300, key_env=KEY_ENV, url=OPENROUTER):
    """One OpenRouter call. The served model comes back, which matters for a
    router like jev: the record then says which model made each decision."""
    key = os.environ.get(key_env)
    if not key:
        return {'text': '', 'usage': {}, 'error': f'{key_env} is not set',
                'returncode': 1, 'stderr': ''}
    body = json.dumps({'model': model, 'messages': messages}).encode()
    request = urllib.request.Request(
        url, data=body,
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            payload = json.loads(answer.read())
    except urllib.error.HTTPError as problem:
        # The body may name the provider's complaint; it never carries the key.
        return {'text': '', 'usage': {}, 'returncode': problem.code, 'stderr': '',
                'error': f'HTTP {problem.code}: {problem.read()[:400].decode(errors="replace")}'}
    except Exception as problem:                      # network, timeout, JSON
        return {'text': '', 'usage': {}, 'error': repr(problem),
                'returncode': 1, 'stderr': ''}
    if 'error' in payload:
        return {'text': '', 'usage': {}, 'error': json.dumps(payload['error'])[:400],
                'returncode': 1, 'stderr': ''}
    choice = (payload.get('choices') or [{}])[0]
    return {'text': (choice.get('message') or {}).get('content') or '',
            'usage': {'tokens': payload.get('usage'), 'served_model': payload.get('model')},
            'error': None, 'returncode': 0, 'stderr': ''}


def messages_for(screen, memory, history):
    """System instructions, the recent past, and now.

    The agent's own memory is what carries continuity, not a transcript: a
    full history of 300 screens would cost more every ask and read worse.
    """
    system = INSTRUCTIONS + '\n\n' + keys_reference()
    messages = [{'role': 'system', 'content': system}]
    for past_screen, past_keys in history:
        messages.append({'role': 'user', 'content': '=== SCREEN ===\n' + past_screen})
        messages.append({'role': 'assistant', 'content': json.dumps({'keys': past_keys})})
    messages.append({'role': 'user', 'content': later_message(screen, memory)})
    return messages


def autoplay(run, model, process=None, max_asks=200, agent=None, via='opencode',
             history_depth=2, manual_name='jev-1', with_pages=False, log=print):
    """Answer this run's questions with a model until it stops or runs out.

    `via` picks the backend: `opencode` (a session, which holds the owner's
    credentials and can attach the manual), `openrouter` (a direct chat call),
    or `decisions` (a decisions model, which answers "which key?" over the
    keyboard - and which cannot keep a memory, because it never writes text).
    """
    """Answer this run's questions with a model until it stops or runs out."""
    from . import replay as replay_module

    run = Path(run)
    session = SESSION.format(run=re.sub(r'[^a-zA-Z0-9]', '', run.name))
    the_manual, pages, last_goal = None, {}, None
    if via == 'decisions':
        from . import decisions as decisions_module, manual as manual_module
        the_manual = manual_module.load(manual_name)
        pages = decisions_module.manual_pages() if with_pages else {}
        (run / 'manual.json').write_text(json.dumps(
            {'manual': the_manual['name'], 'sha256': the_manual['sha256'],
             'keys_described': sorted(the_manual['keys']),
             'goals': sorted(the_manual['goals']),
             'strategy_rules': sorted(the_manual['strategy']),
             'game_manual_pages': sorted(pages)}, indent=2, sort_keys=True) + '\n')
        log(f'manual: {the_manual["name"]} {the_manual["sha256"][:12]} '
            f'({len(the_manual["keys"])} keys described, '
            f'{len(pages)} manual pages in the state)')
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
            if via == 'decisions':
                from . import decisions as decisions_module
                past = run_module.decisions(run)
                previous = None
                if past:
                    before = (run / run_module.ASK /
                              f'screen-{past[-1]["ask"]}.txt')
                    previous = before.read_text() if before.exists() else None
                # Every key pressed while this screen stayed as it is.
                inert, here = [], asked['screen']
                for seen in reversed(past):
                    before = run / run_module.ASK / f'screen-{seen["ask"]}.txt'
                    if not before.exists() or before.read_text() != here:
                        break
                    inert.append(seen['keys'])
                state = decisions_module.state_for(
                    asked, memory,
                    last=past[-1]['keys'] if past else None,
                    changed=(previous != asked['screen']) if previous is not None else None,
                    inert=list(dict.fromkeys(reversed(inert))),
                    goal=last_goal)
                if pages:
                    state['the_games_own_manual'] = pages
                verdict = decisions_module.ask(state, model=model, manual=the_manual)
                result = {
                    'text': json.dumps({'keys': decisions_module.keys_for(verdict['choice']),
                                        'reason': f'{verdict.get("goal") or "-"}: '
                                                  f'{verdict["choice"]!r} at '
                                                  f'{verdict.get("confidence")}, '
                                                  f'weighed {verdict.get("top")}'})
                            if verdict.get('choice') else '',
                    'usage': {'tokens': verdict.get('usage'),
                              'served_model': verdict.get('served_model'),
                              'confidence': verdict.get('confidence'),
                              'top': verdict.get('top'),
                              'goal': verdict.get('goal')},
                    'error': verdict.get('error'), 'returncode': 0, 'stderr': ''}
            elif via == 'openrouter':
                past = run_module.decisions(run)[-history_depth:] if history_depth else []
                history = [(f'(ask {seen["ask"]}, turn {seen["turn"]})', seen['keys'])
                           for seen in past]
                result = call_openrouter(messages_for(screen, memory, history), model)
            else:
                book = run_module.notebook(run)
                result = call(
                    first_message(screen, memory) if first
                    else later_message(screen, memory, book=book),
                    model, session,
                    attach=manual_files() if first else (),
                    agent=agent, cwd=pins.ROOT)
            decision = decision_of(result['text'])
            calls.write(json.dumps({
                'ask': number, 'turn': asked['turn'], 'model': model,
                'via': via, 'session': session, 'usage': result['usage'],
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
            if decision.get('note'):
                run_module.remember(run, str(decision['note'])[:600], ask=number)
            answered += 1
            last_goal = (result['usage'] or {}).get('goal') or last_goal
            log(f'autoplay: ask {number} turn {asked["turn"]} '
                f'depth {asked.get("depth")}: '
                f'{decision["keys"]!r} - {decision.get("reason", "")[:70]}')
            if not replay_module.wait_for(run, number + 1, process, timeout=120):
                log('autoplay: the game asked nothing more')
                break
    finally:
        calls.close()
    return answered
