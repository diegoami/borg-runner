"""Every run in one table.

Reads `records/`, which is what git keeps, so the table is the whole history
and not whatever happens to be left in `runs/`. Two outputs: a Markdown table
for the repository, and a page that can be filtered by model - because the
interesting question across runs is which model, at which version, from which
provider, got how deep for how much.

A run's model is written `provider/model-version` (`anthropic/claude-sonnet-5-5`,
`typesafe/jev-1.14-20261014`), never a bare family name: two runs of "sonnet"
six months apart are not the same experiment.
"""
import argparse
import html
import json
import sys
from pathlib import Path

from . import run as run_module

COLUMNS = (
    ('run', 'run'),
    ('seed', 'seed'),
    ('model', 'model'),
    ('character', 'character'),
    ('max_depth', 'depth'),
    ('character_level', 'level'),
    ('wealth', 'wealth'),
    ('asks', 'asks'),
    ('keypresses', 'keys'),
    ('final_turn', 'turn'),
    ('outcome', 'outcome'),
    ('tokens', 'tokens'),
    ('inherited', 'inherited'),
    ('read_its_own_playbook', 'read its class'),
    ('own_tools', 'own tools'),
    ('replay', 'replay'),
)


def rows(where=None):
    """One row per archived run, newest record first by name."""
    where = Path(where) if where else run_module.RECORDS
    found = []
    for record_path in sorted(where.glob('*/record.json')):
        record = json.loads(record_path.read_text())
        def beside(name):
            path = record_path.parent / name
            return json.loads(path.read_text()) if path.exists() else {}

        started, carried = beside('started.json'), beside('inherited.json')
        cost = record.get('cost') or {}
        model = cost.get('model') or ', '.join(cost.get('models') or []) or None
        found.append({
            'run': record.get('run') or record_path.parent.name,
            'seed': record.get('seed'),
            'model': model,
            'character': record.get('character'),
            'max_depth': record.get('max_depth'),
            'character_level': record.get('character_level'),
            'gold': record.get('gold'),
            'carried_value': record.get('carried_value'),
            'wealth': record.get('wealth'),
            'asks': record.get('asks'),
            'keypresses': record.get('keypresses'),
            'final_turn': record.get('final_turn'),
            'outcome': (f"died: {record['killed_by']}" if record.get('died')
                        else record.get('outcome')),
            'tokens': cost.get('tokens'),
            'usd': cost.get('usd'),
            'played_by': cost.get('played_by'),
            'inherited': Path(carried.get('inherited_from') or '').name or None,
            'standing_from': record.get('standing_from'),
            'read_its_own_playbook': record.get('read_its_own_playbook'),
            'own_tools': len(record.get('own_tools') or []) or None,
            'read_before_playing': record.get('read_before_playing'),
            'notebook_lines': record.get('notebook_lines'),
            'replay_url': record.get('replay_url'),
            # Relative to OVERVIEW.md, which lives in records/ itself.
            # Writing records/<run>/ made every link on GitHub resolve to
            # records/records/<run>/ and 404.
            'record': f'{record_path.parent.name}/',
            'report': (f'{record_path.parent.name}/REPORT.md'
                       if (record_path.parent / 'REPORT.md').exists() else None),
            'replay': (f'{record_path.parent.name}/report.html'
                       if (record_path.parent / 'report.html').exists() else None),
            'seconds_per_decision': cost.get('seconds_per_decision'),
        })
    return found


def shown(value):
    if value is None:
        return '—'
    if isinstance(value, int) and not isinstance(value, bool):
        return f'{value:,}'
    return str(value)


def markdown(found):
    """The table for the repository. Links point at what git holds."""
    head = '| ' + ' | '.join(label for _, label in COLUMNS) + ' |'
    rule = '|' + '|'.join('---' for _ in COLUMNS) + '|'
    lines = [head, rule]
    for row in found:
        cells = []
        for key, _ in COLUMNS:
            if key == 'run':
                where = row.get('report') or row['record']
                cells.append(f"[{row['run']}]({where})")
            elif key == 'replay':
                # The served page first: it is public and it opens, where a
                # relative link shows markup on GitHub and the artifact link
                # is private to its owner.
                where = (f"{SITE}/records/{row['replay']}" if row.get('replay')
                         else row.get('replay_url'))
                cells.append(f'[watch]({where})' if where else '—')
            elif key == 'wealth' and row['wealth'] is not None:
                cells.append(f"{row['wealth']:,} "
                             f"({shown(row['gold'])} gold + "
                             f"{shown(row['carried_value'])} carried)")
            else:
                cells.append(shown(row.get(key)))
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


# The dashboard is three files with one source: the table a reader browses on
# GitHub, the page served at the Pages root, and the same page inside
# records/. One command writes all three, so a run finishing from any harness
# leaves the dashboard current instead of only the markdown.
PAGES = ('index.html', 'records/overview.html')
# A replay is an HTML page, and github.com renders .html as source - so a
# relative link to one works from the Pages site and shows markup when the
# markdown table is read on GitHub, which is where people actually read it.
# The markdown therefore links the served copy absolutely.
SITE = 'https://diegoami.github.io/borg-runner'


def write_all(found=None, log=print):
    """Every form of the table: the markdown and both pages."""
    found = found if found is not None else rows()
    written = [write_markdown(found)]
    for where in PAGES:
        written.append(write_page(found, into=run_module.pins.ROOT / where))
    for path in written:
        log(f'overview: {path}')
    return written


def write_markdown(found=None, into=None):
    found = found if found is not None else rows()
    into = Path(into) if into else run_module.RECORDS / 'OVERVIEW.md'
    body = [
        '# Every run',
        '',
        'Generated by `python -m borg_runner overview`; do not edit by hand.',
        '',
        '`wealth` is the gold plus the game\'s own `object_value()` of',
        'everything carried and worn, so a lucky dive and a well-equipped',
        'descent read differently. `inherited` names the notebook the run',
        'started from. A model is written provider/model-version, because two',
        'runs of the same family months apart are not the same experiment.',
        '',
        markdown(found),
        '',
    ]
    into.write_text('\n'.join(body))
    return into

PAGE_STYLE = """
:root { --ink:#1b1b1b; --dim:#6b6b6b; --line:#dcdcdc; --bg:#fbfbfa; --card:#fff;
        --good:#1f6b3a; --bad:#8a2b2b; --accent:#3a4a7a }
* { box-sizing:border-box }
body { background:var(--bg); color:var(--ink); margin:0;
       font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif }
main { max-width:1180px; margin:0 auto; padding-block:24px 72px;
       padding-left:max(16px, env(safe-area-inset-left, 0px));
       padding-right:max(16px, env(safe-area-inset-right, 0px)) }
h1 { font-size:1.5rem; margin:0 0 4px }
p.sub { color:var(--dim); margin:0 0 20px; max-width:62ch }
.controls { display:flex; gap:10px; align-items:center; flex-wrap:wrap;
            margin:0 0 16px }
.controls label { color:var(--dim) }
select, input[type=search] { font:inherit; padding:5px 8px; color:var(--ink);
       background:var(--card); border:1px solid var(--line); border-radius:6px }
.count { color:var(--dim); font-variant-numeric:tabular-nums }
.wrap { overflow-x:auto; border:1px solid var(--line); border-radius:8px;
        background:var(--card) }
table { border-collapse:collapse; width:100%; min-width:0 }
th, td { padding:8px 11px; text-align:left; border-bottom:1px solid var(--line);
         white-space:nowrap }
th { font-size:.82rem; letter-spacing:.04em; text-transform:uppercase;
     color:var(--dim); font-weight:600; cursor:pointer; user-select:none }
th[aria-sort] { color:var(--ink) }
tbody tr:last-child td { border-bottom:0 }
td.n { font-variant-numeric:tabular-nums; text-align:right }
td.model { font-size:.9rem; color:var(--dim) }
.died { color:var(--bad) }
.alive { color:var(--good) }
a { color:var(--accent) }
.note { color:var(--dim); font-size:.9rem; margin:14px 0 0; max-width:70ch }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --ink:#e8e8e6; --dim:#9a9a97; --line:#2f3136;
        --bg:#17181b; --card:#1d1f23; --good:#7bbf92; --bad:#e08c8c;
        --accent:#9bb0e8; color-scheme:dark }
}
:root[data-theme="dark"] { --ink:#e8e8e6; --dim:#9a9a97; --line:#2f3136;
        --bg:#17181b; --card:#1d1f23; --good:#7bbf92; --bad:#e08c8c;
        --accent:#9bb0e8; color-scheme:dark }
"""

PAGE_SCRIPT = r"""
<script>
(function () {
  var runs = RUNS;
  var body = document.getElementById('body'), count = document.getElementById('count');
  var model = document.getElementById('model'), find = document.getElementById('find');
  var sortKey = 'run', ascending = true;
  var numeric = {seed:1, max_depth:1, character_level:1, wealth:1, asks:1,
                 keypresses:1, final_turn:1, tokens:1};
  function cell(row, key) {
    var v = row[key];
    if (v === null || v === undefined) { return '—'; }
    if (numeric[key]) { return Number(v).toLocaleString(); }
    return String(v);
  }
  function escaped(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function draw() {
    var wanted = model.value, text = find.value.toLowerCase();
    var shown = runs.filter(function (r) {
      if (wanted !== 'all' && (r.model || '') !== wanted) { return false; }
      if (!text) { return true; }
      return JSON.stringify(r).toLowerCase().indexOf(text) !== -1;
    });
    shown.sort(function (a, b) {
      var x = a[sortKey], y = b[sortKey];
      if (x === null || x === undefined) { return 1; }
      if (y === null || y === undefined) { return -1; }
      if (numeric[sortKey]) { x = Number(x); y = Number(y); }
      else { x = String(x); y = String(y); }
      return (x < y ? -1 : x > y ? 1 : 0) * (ascending ? 1 : -1);
    });
    body.innerHTML = shown.map(function (r) {
        // The local replay page first: it is served from this site and anyone
      // can open it, where the artifact link is private to its owner. The
      // markdown table did this and the page did not, so every run without a
      // published artifact sat here as plain text.
      var page = r.replay || r.replay_url;
      var name = page
        ? '<a href="' + escaped(page) + '">' + escaped(r.run) + '</a>'
        : escaped(r.run);
      var notes = r.report
        ? ' <a href="' + escaped(r.report) + '" title="what the run wrote">&#9998;</a>'
        : '';
      var wealth = r.wealth === null ? '—'
        : Number(r.wealth).toLocaleString() + ' <span class="count">('
          + cell(r, 'gold') + ' + ' + cell(r, 'carried_value') + ')</span>';
      var ended = r.outcome && r.outcome.indexOf('died') === 0
        ? '<span class="died">' + escaped(r.outcome) + '</span>'
        : '<span class="alive">' + escaped(r.outcome || '—') + '</span>';
      return '<tr>'
        + '<td>' + name + notes + '</td>'
        + '<td class="n">' + cell(r, 'seed') + '</td>'
        + '<td class="model">' + escaped(r.model || '—') + '</td>'
        + '<td>' + escaped(r.character || '-') + '</td>'
        + '<td class="n">' + cell(r, 'max_depth') + '</td>'
        + '<td class="n">' + cell(r, 'character_level') + '</td>'
        + '<td class="n">' + wealth + '</td>'
        + '<td class="n">' + cell(r, 'asks') + '</td>'
        + '<td class="n">' + cell(r, 'keypresses') + '</td>'
        + '<td class="n">' + cell(r, 'final_turn') + '</td>'
        + '<td>' + ended + '</td>'
        + '<td class="n">' + cell(r, 'tokens') + '</td>'
        + '<td class="model">' + escaped(r.inherited || '—') + '</td>'
        + '</tr>';
    }).join('');
    count.textContent = shown.length + ' of ' + runs.length + ' runs';
  }
  Array.prototype.forEach.call(document.querySelectorAll('th[data-key]'), function (th) {
    th.onclick = function () {
      var key = th.getAttribute('data-key');
      ascending = (key === sortKey) ? !ascending : true;
      sortKey = key;
      Array.prototype.forEach.call(document.querySelectorAll('th[data-key]'),
        function (other) { other.removeAttribute('aria-sort'); });
      th.setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
      draw();
    };
  });
  model.onchange = draw;
  find.oninput = draw;
  draw();
})();
</script>
"""

HEADINGS = (('run', 'run'), ('seed', 'seed'), ('model', 'model'),
            ('character', 'character'), ('max_depth', 'depth'), ('character_level', 'level'),
            ('wealth', 'wealth'), ('asks', 'asks'), ('keypresses', 'keys'),
            ('final_turn', 'turn'), ('outcome', 'outcome'),
            ('tokens', 'tokens'), ('inherited', 'inherited'))


def page(found=None, standalone=True):
    """The table as a page: filter by model, search, sort, and open a replay."""
    found = found if found is not None else rows()
    models = sorted({row['model'] for row in found if row['model']})
    options = ''.join(f'<option value="{html.escape(name)}">{html.escape(name)}</option>'
                      for name in models)
    heads = ''.join(f'<th data-key="{key}">{html.escape(label)}</th>'
                    for key, label in HEADINGS)
    head = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            if standalone else '')
    opens = '</head>\n<body>' if standalone else ''
    closes = '</main></body></html>\n' if standalone else '</main>\n'
    # The rows are the page's data; nothing is fetched. They may not close
    # the script element, and they carry run names and outcomes, so they are
    # escaped as JSON rather than interpolated as HTML.
    script = PAGE_SCRIPT.replace('RUNS', json.dumps(found).replace('</', '<\\/'))
    return f"""{head}<title>Borg runner runs</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>{PAGE_STYLE}</style>{opens}<main>
<h1>Every run</h1>
<p class="sub">One game of Angband each, played from the screen one keypress at
a time. <strong>Click a run to watch its replay</strong>, screen by screen, or
the pencil for what it wrote. <strong>Wealth</strong> is gold plus the game's own valuation of
everything carried and worn, so a lucky dive reads differently from a
well-equipped descent. <strong>Inherited</strong> names the notebook the run
started from. Click a column to sort.</p>
<div class="controls">
  <label for="model">Model</label>
  <select id="model"><option value="all">all models</option>{options}</select>
  <label for="find">Find</label>
  <input id="find" type="search" placeholder="seed, outcome, notebook…">
  <span class="count" id="count"></span>
</div>
<div class="wrap"><table><thead><tr>{heads}</tr></thead>
<tbody id="body"></tbody></table></div>
<p class="note">A model is written provider/model-version. Two runs of the same
family months apart are not the same experiment, so the version is part of the
identity and the filter.</p>
{script}{closes}"""


def write_page(found=None, into=None, standalone=True):
    into = Path(into) if into else run_module.RECORDS / 'overview.html'
    into.write_text(page(found, standalone=standalone))
    return into
