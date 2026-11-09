"""One run as a single self-contained HTML page.

No external request of any kind: no stylesheet, no script, no image, no font.
It opens from a `file://` URL and can be attached to anything, which is the
only way a run report is actually read.

The column that matters is the last one. Beside each key it shows **what the
player believed at the time** - its reason, and the note it wrote - so the
page can be read as "here is where it was wrong, and here is what it thought".

Run it as `python -m borg_runner.report --run runs/<name>`.
"""
import argparse
import html
import json
import sys
from pathlib import Path

from . import run as run_module

STYLE = """
:root { --ink:#1b1b1b; --dim:#6b6b6b; --line:#dcdcdc; --bg:#fbfbfa;
        --card:#ffffff; --screen-bg:#14161a; --screen-ink:#d7dae0;
        --flag:#8a4b00; }
* { box-sizing:border-box }
body { margin:0; background:var(--bg); color:var(--ink);
       font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif }
main { max-width:1100px; margin:0 auto; padding-block:24px 72px;
       padding-left:max(16px, env(safe-area-inset-left, 0px));
       padding-right:max(16px, env(safe-area-inset-right, 0px)) }
h1 { font-size:1.5rem; margin:0 0 4px }
.sub { color:var(--dim); margin:0 0 22px }
table.facts { border-collapse:collapse; margin:0 0 28px; width:100% }
table.facts td { border-bottom:1px solid var(--line); padding:6px 10px; vertical-align:top }
table.facts td:first-child { color:var(--dim); white-space:nowrap; width:1%; padding-right:22px }
h2 { font-size:1.1rem; margin:34px 0 10px; padding-bottom:6px; border-bottom:1px solid var(--line) }
.ask { border:1px solid var(--line); border-radius:8px; margin:0 0 14px; background:var(--card);
       overflow:hidden }
.ask > summary { cursor:pointer; padding:9px 12px; display:flex; gap:14px;
                 align-items:baseline; flex-wrap:wrap }
.ask > summary::-webkit-details-marker { display:none }
.n { color:var(--dim); font-variant-numeric:tabular-nums; min-width:3.2em }
.keys { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-weight:600 }
.why { color:var(--dim); flex:1 1 320px }
.where { color:var(--dim); font-variant-numeric:tabular-nums }
.body { padding:0 12px 12px }
pre.screen { background:var(--screen-bg); color:var(--screen-ink); padding:12px;
             border-radius:6px; overflow-x:auto; margin:6px 0 0;
             font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
             font-size:12.5px; line-height:1.25 }
.note { color:var(--flag); margin:8px 0 0 }
pre.book { background:var(--card); border:1px solid var(--line); border-radius:8px;
           padding:12px; white-space:pre-wrap; margin:0 }
.empty { color:var(--dim) }
.replay { border:1px solid var(--line); border-radius:8px; background:var(--card);
          padding:12px; margin:0 0 28px }
.replay pre { background:var(--screen-bg); color:var(--screen-ink); margin:0;
              padding:14px; border-radius:6px; overflow-x:auto; min-height:25em;
              font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
              font-size:13px; line-height:1.22; white-space:pre }
.bar { display:flex; gap:10px; align-items:center; margin:10px 0 0; flex-wrap:wrap }
.bar button { font:inherit; padding:5px 11px; border:1px solid var(--line);
              border-radius:6px; background:var(--bg); color:var(--ink); cursor:pointer }
.bar button:hover { border-color:var(--dim) }
.bar input[type=range] { flex:1 1 220px; min-width:140px }
.at { color:var(--dim); font-variant-numeric:tabular-nums; white-space:nowrap }
.said { margin:10px 0 0; min-height:3em }
.said .keys { font-size:1.05rem }
.said .why { color:var(--dim) }
@media (max-width:620px) { .replay pre { font-size:10.5px } }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --ink:#e8e8e6; --dim:#9a9a97; --line:#2f3136;
        --bg:#17181b; --screen-bg:#0c0d10; --flag:#e0a34a; --card:#1d1f23;
        color-scheme:dark }
}
:root[data-theme="dark"] { --ink:#e8e8e6; --dim:#9a9a97; --line:#2f3136;
        --bg:#17181b; --screen-bg:#0c0d10; --flag:#e0a34a; --card:#1d1f23;
        color-scheme:dark }
"""


def read(run):
    """Everything the page needs, from the run directory as it stands."""
    run = Path(run)
    def load(name, default=None):
        path = run / name
        if not path.exists():
            return default
        return json.loads(path.read_text())

    taken = run_module.decisions(run)
    calls = {}
    path = run / 'model-calls.jsonl'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                call = json.loads(line)
                calls[call.get('ask')] = call
    screens = {}
    for entry in taken:
        screen = run / run_module.ASK / f'screen-{entry["ask"]}.txt'
        if screen.exists():
            screens[entry['ask']] = screen.read_text()
    notes = {}
    book = run / run_module.NOTEBOOK
    if book.exists():
        for line in book.read_text().splitlines():
            if '(ask ' in line:
                try:
                    at = int(line.rsplit('(ask ', 1)[1].split(')')[0])
                except (ValueError, IndexError):
                    continue
                notes.setdefault(at, []).append(line.lstrip('- ').strip())
    asked = run_module.questions(run)
    answered = {entry['ask'] for entry in taken}
    unanswered = {}
    for number in asked:
        if number not in answered:
            unanswered[number] = run_module.question(run, number)
    return {
        'run': run,
        'asked': asked,
        'questions': unanswered,
        'record': load(run_module.RECORD, {}),
        'started': load('started.json', {}),
        'manual': load('manual.json'),
        'replay': load('replay.json'),
        'decisions': taken,
        'calls': calls,
        'screens': screens,
        'notes': notes,
        'notebook': run_module.notebook(run, lines=10 ** 6),
    }


def facts(data):
    """The run in one table. Only what the files actually say."""
    record, started = data['record'], data['started']
    rows = [
        ('run', record.get('run') or data['run'].name),
        ('seed', started.get('seed')),
        ('character', started.get('character')),
        ('outcome', record.get('outcome')),
        ('killed by', record.get('killed_by')),
        ('deepest depth', record.get('max_depth')),
        ('final turn', record.get('final_turn')),
        ('asks', record.get('asks')),
        ('keypresses', record.get('keypresses')),
        ('notebook', f"{record.get('notebook_lines') or 0} lines"),
    ]
    build = started.get('build') or {}
    if build:
        rows.append(('game', f"{build.get('game')} {str(build.get('commit'))[:12]}"))
        rows.append(('patch', str(build.get('patch_sha256'))[:12]))
    if data['manual']:
        rows.append(('manual', f"{data['manual'].get('manual')} "
                               f"{str(data['manual'].get('sha256'))[:12]}"))
    if record.get('notebook_sha256'):
        rows.append(('notebook hash', record['notebook_sha256'][:12]))
    if data['replay']:
        rows.append(('replay', 'identical' if data['replay'].get('identical')
                               else 'DIFFERED'))
    cost = record.get('cost') or {}
    if cost.get('tokens'):
        shown = f"{cost['tokens']:,} tokens"
        if cost.get('tool_calls'):
            shown += f", {cost['tool_calls']} tool calls"
        if cost.get('usd'):
            shown += f", ${cost['usd']:.4f}"
        rows.append(('cost', shown))
    elif cost.get('usd'):
        rows.append(('cost', f"${cost['usd']:.4f} over "
                             f"{cost.get('model_calls')} model calls"))
    if cost.get('played_by') or cost.get('model') or cost.get('models'):
        rows.append(('played by', cost.get('played_by') or ''))
        rows.append(('model', cost.get('model')
                     or ', '.join(cost.get('models') or [])))
    return [(name, value) for name, value in rows if value not in (None, '')]


def timeline(data):
    """One block per ask: what was pressed, why, and the screen it faced."""
    out = []
    for entry in data['decisions']:
        at = entry['ask']
        call = data['calls'].get(at) or {}
        usage = call.get('usage') or {}
        served = usage.get('served_model')
        where = f"turn {entry.get('turn')}"
        if entry.get('depth') is not None:
            where += f" · depth {entry['depth']}"
        extra = ''
        if usage.get('goal'):
            extra = f" · goal {html.escape(str(usage['goal']))}"
        if served:
            extra += f" · {html.escape(str(served))}"
        notes = ''.join(
            f'<p class="note">note: {html.escape(note)}</p>'
            for note in data['notes'].get(at, []))
        screen = data['screens'].get(at)
        out.append(
            f'<details class="ask"><summary>'
            f'<span class="n">{at}</span>'
            f'<span class="keys">'
            f'{html.escape(repr(entry.get("keys", "")), quote=False)}</span>'
            f'<span class="why">{html.escape(entry.get("reason") or "")}</span>'
            f'<span class="where">{where}{extra}</span>'
            f'</summary><div class="body">'
            + (f'<pre class="screen">{html.escape(screen)}</pre>' if screen else '')
            + notes
            + '</div></details>')
    return '\n'.join(out) or '<p class="empty">no decisions were taken</p>'


def frames(data):
    """One frame per ask: the screen the player faced, and what it then did."""
    out = []
    for entry in data['decisions']:
        at = entry['ask']
        call = data['calls'].get(at) or {}
        out.append({
            'ask': at,
            'turn': entry.get('turn'),
            'depth': entry.get('depth'),
            'keys': entry.get('keys', ''),
            'reason': entry.get('reason') or '',
            'goal': (call.get('usage') or {}).get('goal') or '',
            'notes': data['notes'].get(at, []),
            'screen': data['screens'].get(at, ''),
        })
    # The game's last word. It asked once more and the run ended there, so
    # this frame has no keys - and on a death it is the tombstone, which is
    # the one frame a replay must not drop.
    answered = {entry['ask'] for entry in data['decisions']}
    for number in data['asked']:
        if number in answered:
            continue
        asked = data['questions'].get(number) or {}
        out.append({
            'ask': number,
            'turn': asked.get('turn'),
            'depth': asked.get('depth'),
            'keys': '',
            'reason': ('the game asked again and the run ended here'
                       if not data['record'].get('died')
                       else 'the game asked again; the character was dead'),
            'goal': '',
            'notes': data['notes'].get(number, []),
            'screen': asked.get('screen', ''),
        })
    return out


REPLAY = r"""
<section class="replay">
  <pre id="screen">(no screens were recorded)</pre>
  <div class="bar">
    <button id="back" title="left arrow">&#9664; step</button>
    <button id="play" title="space">&#9654; play</button>
    <button id="next" title="right arrow">step &#9654;</button>
    <input id="scrub" type="range" min="0" value="0" step="1">
    <span class="at" id="at"></span>
  </div>
  <p class="said"><span class="keys" id="keys"></span>
     <span class="why" id="why"></span></p>
</section>
<script>
(function () {
  var frames = FRAMES, at = 0, timer = null;
  var screen = document.getElementById('screen'), scrub = document.getElementById('scrub');
  var where = document.getElementById('at'), keys = document.getElementById('keys');
  var why = document.getElementById('why'), play = document.getElementById('play');
  if (!frames.length) { return; }
  scrub.max = frames.length - 1;
  function show(i) {
    at = Math.max(0, Math.min(frames.length - 1, i));
    var f = frames[at];
    screen.textContent = f.screen || '(this ask recorded no screen)';
    scrub.value = at;
    where.textContent = 'ask ' + f.ask + ' of ' + frames[frames.length - 1].ask +
      '  ·  turn ' + f.turn + (f.depth === null ? '' : '  ·  depth ' + f.depth) +
      (f.goal ? '  ·  ' + f.goal : '');
    keys.textContent = f.keys ? JSON.stringify(f.keys) + ' — ' : '';
    why.textContent = (f.reason || '') +
      (f.notes.length ? '   ⚑ ' + f.notes.join('  ⚑ ') : '');
  }
  function stop() {
    if (timer) { clearInterval(timer); timer = null; play.innerHTML = '&#9654; play'; }
  }
  function start() {
    if (timer) { stop(); return; }
    play.innerHTML = '&#10074;&#10074; pause';
    timer = setInterval(function () {
      if (at >= frames.length - 1) { stop(); return; }
      show(at + 1);
    }, 700);
  }
  document.getElementById('next').onclick = function () { stop(); show(at + 1); };
  document.getElementById('back').onclick = function () { stop(); show(at - 1); };
  play.onclick = start;
  scrub.oninput = function () { stop(); show(parseInt(scrub.value, 10)); };
  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight') { stop(); show(at + 1); }
    else if (e.key === 'ArrowLeft') { stop(); show(at - 1); }
    else if (e.key === ' ' && e.target === document.body) { e.preventDefault(); start(); }
  });
  show(0);
})();
</script>
"""


def replay_section(data):
    """The player, with every screen embedded. Nothing is fetched."""
    payload = json.dumps(frames(data))
    # The screens are the game's own characters and the reasons are a model's
    # words; neither may be allowed to close the script element.
    payload = payload.replace('</', '<\\/')
    return REPLAY.replace('FRAMES', payload)


def render(data, standalone=True):
    """The page. `standalone=False` leaves out the document skeleton, which is
    what an artifact host supplies itself."""
    name = data['record'].get('run') or data['run'].name
    rows = ''.join(f'<tr><td>{html.escape(str(k))}</td>'
                   f'<td>{html.escape(str(v))}</td></tr>' for k, v in facts(data))
    book = data['notebook'].strip()
    head = (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            if standalone else '')
    opens = '</head>\n<body>' if standalone else ''
    closes = '</main></body></html>\n' if standalone else '</main>\n'
    return f"""{head}<title>{html.escape(name)} replay</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>{STYLE}</style>{opens}<main>
<h1>{html.escape(name)}</h1>
<p class="sub">One game of Angband, played from the screen one keypress at a time.</p>
<table class="facts">{rows}</table>
<h2>Replay</h2>
<p class="sub">Every screen the player faced, in order. Arrow keys step, space
plays; the line underneath is the keys it sent and why.</p>
{replay_section(data)}
<h2>What it kept</h2>
{f'<pre class="book">{html.escape(book)}</pre>' if book
 else '<p class="empty">the notebook is empty</p>'}
<h2>Every decision</h2>
{timeline(data)}
{closes}"""


def write(run, into=None, standalone=True):
    data = read(run)
    page = Path(into) if into else Path(run) / 'report.html'
    page.write_text(render(data, standalone=standalone))
    return page


def rebuild_all(log=print):
    """Regenerate every archived run's replay page.

    `archive` writes a run's replay when the run ends, so this is for after
    the page itself changes - a new column, a fixed bug - rather than for
    normal use. A run whose working directory is gone needs its keys replayed
    first, because the screens are not archived; it is said rather than
    guessed at.
    """
    done, missing = [], []
    for record in sorted((run_module.RECORDS).glob('*/record.json')):
        name = record.parent.name
        live = run_module.RUNS / name
        if not (live / run_module.ASK).is_dir() or not any(
                (live / run_module.ASK).glob('screen-*.txt')):
            missing.append(name)
            continue
        page = write(live, into=record.parent / 'report.html')
        done.append(name)
        log(f'replay: {page}')
    for name in missing:
        log(f'replay: {name} has no screens left; '
            f'replay its keys first (borg_runner replay --run records/{name})')
    return done, missing


def main(argv=None):
    parser = argparse.ArgumentParser(description='one run as a self-contained page')
    parser.add_argument('--run', type=Path)
    parser.add_argument('--into', type=Path)
    parser.add_argument('--all', action='store_true',
                        help="regenerate every archived run's replay page")
    parser.add_argument('--artifact', action='store_true',
                        help='leave out the document skeleton, for a host that '
                             'supplies its own')
    args = parser.parse_args(argv)
    if args.all:
        rebuild_all()
        return 0
    print(write(args.run, args.into, standalone=not args.artifact))
    return 0


if __name__ == '__main__':
    sys.exit(main())
