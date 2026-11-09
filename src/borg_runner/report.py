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
        --screen-bg:#14161a; --screen-ink:#d7dae0; --flag:#8a4b00; }
* { box-sizing:border-box }
body { margin:0; background:var(--bg); color:var(--ink);
       font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif }
main { max-width:1100px; margin:0 auto; padding:24px 16px 72px }
h1 { font-size:1.5rem; margin:0 0 4px }
.sub { color:var(--dim); margin:0 0 22px }
table.facts { border-collapse:collapse; margin:0 0 28px; width:100% }
table.facts td { border-bottom:1px solid var(--line); padding:6px 10px; vertical-align:top }
table.facts td:first-child { color:var(--dim); white-space:nowrap; width:1%; padding-right:22px }
h2 { font-size:1.1rem; margin:34px 0 10px; padding-bottom:6px; border-bottom:1px solid var(--line) }
.ask { border:1px solid var(--line); border-radius:8px; margin:0 0 14px; background:#fff;
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
pre.book { background:#fff; border:1px solid var(--line); border-radius:8px;
           padding:12px; white-space:pre-wrap; margin:0 }
.empty { color:var(--dim) }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --ink:#e8e8e6; --dim:#9a9a97; --line:#2f3136;
        --bg:#17181b; --screen-bg:#0c0d10; --flag:#e0a34a }
  :root:not([data-theme="light"]) .ask, :root:not([data-theme="light"]) pre.book
        { background:#1d1f23 }
}
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
    return {
        'run': run,
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
    spend = sum((((call.get('usage') or {}).get('tokens') or {}).get('cost') or 0)
                for call in data['calls'].values())
    if spend:
        rows.append(('model cost', f'${spend:.4f} over {len(data["calls"])} calls'))
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


def render(data):
    name = data['record'].get('run') or data['run'].name
    rows = ''.join(f'<tr><td>{html.escape(str(k))}</td>'
                   f'<td>{html.escape(str(v))}</td></tr>' for k, v in facts(data))
    book = data['notebook'].strip()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(name)}</title>
<style>{STYLE}</style></head>
<body><main>
<h1>{html.escape(name)}</h1>
<p class="sub">One game of Angband, played from the screen one keypress at a time.</p>
<table class="facts">{rows}</table>
<h2>What it kept</h2>
{f'<pre class="book">{html.escape(book)}</pre>' if book
 else '<p class="empty">the notebook is empty</p>'}
<h2>Every decision</h2>
{timeline(data)}
</main></body></html>
"""


def write(run, into=None):
    data = read(run)
    page = Path(into) if into else Path(run) / 'report.html'
    page.write_text(render(data))
    return page


def main(argv=None):
    parser = argparse.ArgumentParser(description='one run as a self-contained page')
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--into', type=Path)
    args = parser.parse_args(argv)
    print(write(args.run, args.into))
    return 0


if __name__ == '__main__':
    sys.exit(main())
