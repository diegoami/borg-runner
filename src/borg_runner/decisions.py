"""Ask a decisions model which key to press.

A decisions model (TypeSafe's Jev, or anything else on the same endpoint)
does not write text: it is given a `state` and named typed questions, and it
answers each one. A `choice` question picks one option from a set.

So the question here is "which key?", and **the option set is the keyboard** -
the game's own command list, in the game's own words, out of the manual at the
pin, plus the letters a menu row can carry and the digits that are directions.
That matters for D2: enumerating the keyboard is not an opinion about how to
play, whereas enumerating *plans* would be. It is the whole difference between
this and a planner that asks a model to choose between its own ideas.

It is also cheap in a way a generative model is not. Measured 2026-11-09: one
decision cost $0.0000186, about two cents a thousand, so one key per round
trip is affordable and nothing has to be batched.
"""
import json
import os
import re
import urllib.error
import urllib.request

from . import autoplay, manual as manual_module, pins

ENDPOINT = 'https://openrouter.ai/api/alpha/decisions'
MODEL = '~typesafe/jev-latest'

# Keys that cannot be a JSON key legibly, and what the frontend is sent.
SPECIAL = {'enter': '\\n', 'escape': '\\e', 'tab': '\\t', 'space': ' '}

DIRECTIONS = {
    '1': 'move or attack south-west', '2': 'move or attack south',
    '3': 'move or attack south-east', '4': 'move or attack west',
    '5': 'stay where you are, or confirm the current target',
    '6': 'move or attack east', '7': 'move or attack north-west',
    '8': 'move or attack north', '9': 'move or attack north-east',
}

# The fallback, used only if no manual file is given. The real instructions
# live in manuals/<name>.md, because they are an input under test (D14).
INSTRUCTIONS = (
    'Which single key should be pressed next in this game of Angband 4.2.6? '
    'The state holds the screen exactly as the game drew it. The original '
    'keyset is in use, so the digits move.'
)


def commands_from_manual():
    """key -> what the manual calls it, for the original keyset."""
    manual = pins.clone('angband') / 'docs' / 'command.rst'
    if not manual.exists():
        return {}
    found = re.findall(r'^([A-Z][^(\n]{2,40})\(``([^`]+)``\)',
                       manual.read_text(), re.M)
    commands = {}
    for name, key in found:
        if len(key) == 1 and key not in commands:
            commands[key] = name.strip().lower()
    return commands


def options(manual=None):
    """The keyboard, as a choice set.

    Three layers, and the order is the point: the game's own name for a key
    out of docs/command.rst, then what the Jev manual adds about *when* it
    applies, then a generic description for every key the manual never
    mentions. Only the middle layer is ours, and it is versioned and hashed.
    """
    criteria = {}
    commands = commands_from_manual()
    described = (manual or {}).get('keys') or {}
    for key, name in sorted(commands.items()):
        criteria[key] = f'press {key}: {name}'
    for key, description in described.items():
        if key in criteria:
            criteria[key] += f'. {description}'
        else:
            criteria[key] = f'press {key}: {description}'
    for key, what in DIRECTIONS.items():
        criteria[key] = (f'press {key}: {what}'
                         + (f', or the menu row {key}' if key in commands else ''))
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        if letter not in criteria:
            criteria[letter] = (f'press {letter}: the menu row, item or spell '
                                f'labelled {letter}')
        else:
            criteria[letter] += f', or the item or menu row labelled {letter}'
    for name, keys in (('enter', 'select the highlighted row, or accept'),
                       ('escape', 'leave this prompt or menu, or step back'),
                       ('space', 'continue past a message or a -more- prompt'),
                       ('tab', 'move to the next field or page')):
        criteria[name] = f'press {name.title()}: {keys}'
    criteria['none_of_these'] = 'none of these keys is right here'
    return criteria


def keys_for(choice):
    """What the frontend is told to press, for a chosen option."""
    return SPECIAL.get(choice, choice)


def state_for(asked, memory, last=None, changed=None, inert=(), goal=None):
    """What the model is told. The screen, and the player's own short memory.

    `inert` is the keys already pressed at this very screen that changed
    nothing. A person remembers trying them; a decisions model cannot, because
    it never writes anything down - it only re-reports a distribution over the
    same options, so it will press the same wrong key until the run ends. That
    is not a tactic we are supplying, it is the player's memory of their own
    last few keystrokes.
    """
    state = {'screen': asked['screen'], 'turn': asked['turn'],
             'depth_in_levels': asked.get('depth'), 'deepest_reached': asked.get('max_depth')}
    if inert:
        state['keys_already_pressed_here_that_changed_nothing'] = list(inert)
    if asked.get('cursor'):
        state['cursor'] = f'{asked["cursor"]["x"]},{asked["cursor"]["y"]}'
    if memory:
        state['memory_the_player_kept'] = memory
    if goal:
        state['the_goal_you_chose_last_time'] = goal
    if last:
        state['the_key_just_pressed'] = last
    if changed is not None:
        # What a person sees and the screen alone cannot say: whether the last
        # key did anything. Without it a model presses Enter for ever.
        state['the_screen_changed_after_it'] = changed
    return state


GOAL_INSTRUCTIONS = (
    'What is this character trying to do right now? You keep nothing between '
    'questions, so your answer here is handed back to you next time as '
    '`the_goal_you_chose_last_time`: it is your own memory of your intention. '
    'Hold a goal while it is still the right one rather than changing it every '
    'turn, and change it when the screen says the situation has.')


def instructions_from(manual):
    """The instructions and the compressed strategy, as one block.

    The strategy is sent with every question because the model cannot keep it
    - and it is sent as rules with their ids, so a lead can argue with a named
    rule rather than with a vibe.
    """
    text = (manual or {}).get('instructions') or INSTRUCTIONS
    strategy = (manual or {}).get('strategy') or {}
    if strategy:
        text += ('\n\nWhat is known about playing this game well, compressed '
                 'from the strategy manual. These are a starting policy to be '
                 'measured, not truths:\n'
                 + '\n'.join(f'- {rule}: {what}' for rule, what in sorted(strategy.items())))
    return text


def questions_for(criteria, manual):
    """Which key, and what for. Both are the model's own answers.

    We only carry the goal forward, which is the whole of the memory a
    decisions model can have, since it never writes anything down.
    """
    questions = {'key': {'type': 'choice',
                         'instructions': instructions_from(manual),
                         'criteria': (criteria if criteria is not None
                                      else options(manual))}}
    goals = (manual or {}).get('goals') or {}
    if goals:
        questions['goal'] = {
            'type': 'choice', 'instructions': GOAL_INSTRUCTIONS,
            'criteria': {name: f'{name}: {what}' for name, what in goals.items()},
        }
    return questions


def manual_pages(names=('command.rst',)):
    """Pinned manual pages, to put in the state.

    Jev reads nothing, so the only way it can have the manual is for the
    manual to be part of the question. At $0.042 a million input tokens this
    costs about a dollar a game, which makes "does the manual help a model
    that only scores options?" a measurable question rather than an opinion.
    """
    pages = {}
    for name in names:
        page = pins.clone('angband') / 'docs' / name
        if page.exists():
            pages[name] = page.read_text()
    return pages


def ask(state, model=MODEL, criteria=None, timeout=180, manual=None,
        key_env=autoplay.KEY_ENV, url=ENDPOINT):
    """One decision. Returns the chosen key, the whole distribution and cost."""
    key = os.environ.get(key_env)
    if not key:
        return {'choice': None, 'error': f'{key_env} is not set'}
    body = json.dumps({
        'model': model,
        'state': state,
        'questions': questions_for(criteria, manual),
    }).encode()
    request = urllib.request.Request(
        url, data=body,
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            payload = json.loads(answer.read())
    except urllib.error.HTTPError as problem:
        return {'choice': None,
                'error': f'HTTP {problem.code}: {problem.read()[:400].decode(errors="replace")}'}
    except Exception as problem:
        return {'choice': None, 'error': repr(problem)}
    if 'error' in payload:
        return {'choice': None, 'error': json.dumps(payload['error'])[:400]}
    answers = payload.get('answers') or {}
    answered = answers.get('key') or {}
    probabilities = answered.get('probabilities') or {}
    return {
        'choice': answered.get('choice'),
        'goal': (answers.get('goal') or {}).get('choice'),
        'confidence': answered.get('confidence'),
        # The three it weighed most. The whole distribution is the interesting
        # part of a decisions model and it is recorded, not just the pick.
        'top': sorted(probabilities.items(), key=lambda pair: -pair[1])[:3],
        'served_model': payload.get('model'),
        'usage': payload.get('usage'),
        'error': None,
    }
