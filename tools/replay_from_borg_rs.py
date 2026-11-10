#!/usr/bin/env python3
"""Turn a borg-rs recording into one of this repository's replay pages.

borg-rs records a frame per command with the whole terminal in it - `cells` is
80x24 entries of (index, codepoint, attribute) - so a session played by a
person can be watched back exactly as a model's run can, with the same player.

The keys are recorded too, in `run/events.txt` rather than in the frames: a
row beginning `1` is a keypress whose fifth field is the keycode and whose
tenth is the input counter the frames carry. So the two are joined here and the
replay shows the keystroke beside the screen it produced.

    python tools/replay_from_borg_rs.py <recording dir> [--into page.html]
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from borg_runner import report as report_module       # noqa: E402


class Terminal:
    """The screen, kept between frames.

    A frame's `cells` is a **patch**, not a snapshot: of 6,105 frames here only
    62 carry `full: 1` and the whole screen, and the rest list just the cells
    that changed - mostly none at all. Painting each frame onto a blank grid,
    which is what this did first, renders every delta as an empty or
    half-empty screen.

    Colour is in the frame and dropped: a coloured page would need 1,920 spans
    a frame across more than a thousand frames.
    """

    def __init__(self, width=80, height=24):
        self.width, self.height = width, height
        self.rows = [[' '] * width for _ in range(height)]

    def apply(self, frame):
        if frame['width'] != self.width or frame['height'] != self.height:
            self.__init__(frame['width'], frame['height'])
        if frame.get('full'):
            self.rows = [[' '] * self.width for _ in range(self.height)]
        for index, code, _attr in frame['cells']:
            y, x = divmod(index, self.width)
            if y < self.height and x < self.width:
                self.rows[y][x] = chr(code) if 32 <= code < 127 else ' '
        return self.text()

    def text(self):
        return '\n'.join(''.join(row).rstrip() for row in self.rows)


# Angband's own names, from src/ui-event.h. The x11 frontend sends these
# rather than ASCII for the arrows, the keypad diagonals and Escape.
KEY_NAMES = {
    0x80: '↓', 0x81: '←', 0x82: '→', 0x83: '↑',
    0x94: '↖ Home', 0x95: '↗ PgUp', 0x96: '↙ End', 0x97: '↘ PgDn',
    0x9c: '⏎ Enter', 0x9d: 'Tab', 0x9e: 'Delete', 0x9f: 'Backspace',
    0x93: 'Help', 0x98: 'Insert', 0xE000: 'Escape', 0x00: '(none)',
}
STEP_KEYS = frozenset((0x80, 0x81, 0x82, 0x83, 0x94, 0x95, 0x96, 0x97))


def key_name(code):
    if 32 <= code < 127:
        return chr(code)
    return KEY_NAMES.get(code, f'0x{code:x}')


def keys_by_input(recording):
    """The keys the player pressed, by the input counter the frames carry.

    They are in `run/events.txt`, not in the frames: a row beginning `1` is a
    keypress and its fifth field is the keycode. The order is reliable; the
    *join* to a frame is not, and two attempts at one were wrong. The tenth
    field looked like the frames' `input` counter and is not - it has 43
    distinct values against the counter's 934 - and bisecting the counter put
    the same key on 563 of 570 screens.

    What is defensible is the order: 404 frames carry `phase: "input"`, which
    is the game taking a key, against 418 keys here. So keys are handed out in
    order at those frames, and the replay labels each screen with the key most
    recently taken. That is an **inference**, not a field in the recording, and
    the page says so.
    """
    pressed = []
    log = Path(recording) / 'run' / 'events.txt'
    if not log.exists():
        return pressed
    for line in log.read_text().splitlines():
        parts = line.split()
        if len(parts) > 10 and parts[0] == '1':
            try:
                pressed.append(int(parts[4]))
            except ValueError:
                continue
    return pressed


def messages_by_turn(recording):
    """The game's own messages, which stand in for a model's stated reason."""
    said = {}
    log = Path(recording) / 'run' / 'combat.jsonl'
    if not log.exists():
        return said
    for line in log.read_text().splitlines():
        if not line.strip():
            continue
        note = json.loads(line)
        if note.get('kind') == 'message' and note.get('text'):
            said.setdefault(note['turn'], []).append(note['text'])
    return said


def frames_of(recording):
    """One frame per *change* of screen: 6,105 ticks were 1,198 screens."""
    recording = Path(recording)
    said = messages_by_turn(recording)
    pressed = keys_by_input(recording)
    out, last, terminal = [], None, Terminal()
    code, taken = None, 0
    for line in gzip.open(recording / 'frames.jsonl.gz', 'rt'):
        frame = json.loads(line)
        screen = terminal.apply(frame)
        # The key is taken first: an `input` frame carries no cells at all,
        # so skipping unchanged screens before this never advanced the key and
        # left every frame unlabelled.
        if frame.get('phase') == 'input' and taken < len(pressed):
            code, taken = pressed[taken], taken + 1
        # Phases that are not a redraw still carry no cells, so the screen is
        # unchanged and the frame is not worth a step of its own.
        if screen == last:
            continue
        last = screen
        spoken = said.get(frame['turn']) or []
        out.append({
            'ask': len(out) + 1,
            'turn': frame['turn'],
            'depth': frame['depth'],
            'keys': key_name(code) if code is not None else '',
            # The key is matched by order on the frames that took one, which
            # is an inference; see keys_by_input.
            'goal': 'key by order',
            'reason': (f"{frame['hp']}/{frame['max_hp']} hit points, "
                       f"level {frame['level']}, {frame['gold']} gold"
                       + (' — ' + ' '.join(spoken) if spoken else '')),
            'notes': spoken,
            'screen': screen,
        })
    return out


def page(recording, into=None, standalone=True):
    recording = Path(recording)
    meta = json.loads((recording / 'recording.json').read_text())
    shown = frames_of(recording)
    last = shown[-1] if shown else {}
    data = {
        'run': recording,
        'asked': [], 'questions': {}, 'calls': {}, 'notes': {},
        'screens': {}, 'decisions': [], 'notebook': '',
        'manual': None, 'replay': None,
        'started': {'seed': meta.get('arguments'),
                    'character': meta.get('character'),
                    'build': {'game': 'borg-rs ' + (meta.get('frontend') or ''),
                              'commit': (meta.get('build_id') or {}).get('git_rev', ''),
                              'patch_sha256': (meta.get('build_id') or {})
                              .get('binary_sha256', '')}},
        'record': {'run': recording.name,
                   'outcome': 'played by a person',
                   'max_depth': max((f['depth'] or 0) for f in shown) if shown else 0,
                   'final_turn': last.get('turn'),
                   'asks': len(shown),
                   'cost': {'played_by': 'a person',
                            'model': 'none/human',
                            'seconds_per_decision':
                                round(meta.get('duration_seconds', 0)
                                      / max(len(shown), 1), 1)},
                   'died': False},
    }
    # The replay section only needs the frames; everything else on the page
    # reads from these two.
    report_module.frames = lambda _data, _shown=shown: _shown
    body = report_module.render(data, standalone=standalone)
    target = Path(into) if into else recording / 'replay.html'
    target.write_text(body)
    return target, len(shown)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording', type=Path)
    parser.add_argument('--into', type=Path)
    parser.add_argument('--artifact', action='store_true',
                        help='leave out the document skeleton')
    args = parser.parse_args(argv)
    where, count = page(args.recording, args.into, standalone=not args.artifact)
    print(f'{where} ({count} screens)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
