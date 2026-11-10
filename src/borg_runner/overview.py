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
    ('wrote_up', 'wrote up'),
    ('playbook', 'playbook'),
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
            # The character the game was played as, from started.json: the
            # lineage key. Lives of one character share it (minimaxflash-1,
            # minimaxflash-1.2, ...), so characters - not runs - can head the
            # page.
            'lineage': started.get('character') or record.get('run')
                       or record_path.parent.name,
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
            'wrote_up': 'yes' if (record_path.parent / 'REPORT.md').exists() else 'NO',
            # The model family whose agents/<family>/ pages this run read and
            # wrote back to: the other half of what a run leaves behind.
            'playbook': record.get('playbook'),
            'replay': (f'{record_path.parent.name}/report.html'
                       if (record_path.parent / 'report.html').exists() else None),
            'seconds_per_decision': cost.get('seconds_per_decision'),
            # The three things a reader most wants to cut the table by.
            'alive': 'died' if record.get('died') else 'alive',
            'class': record.get('class'),
        })
    for row in found:
        row['agent'] = agent_of(row)
    return found


def shown(value):
    if value is None:
        return '—'
    if isinstance(value, int) and not isinstance(value, bool):
        return f'{value:,}'
    return str(value)


# The agent is a model FAMILY, not a provider and not a version — `minimax`,
# not `minimax/MiniMax-M3` (agents/README.md). A run that names the playbook
# it read is that family by definition; the rest are read off the model,
# because a filter that only worked for one family would not be a filter.
FAMILIES = (
    ('minimax', ('minimax',)),
    ('sonnet', ('sonnet',)),
    ('codex', ('gpt-', 'codex')),
    ('qwen', ('qwen',)),
    ('glm', ('glm',)),
    ('jev', ('jev',)),
    ('human', ('human',)),
)


def agent_of(row):
    """The model family that played this run."""
    if row.get('playbook'):
        return row['playbook']
    model = (row.get('model') or '').lower()
    for family, marks in FAMILIES:
        if any(mark in model for mark in marks):
            return family
    return (row.get('model') or '').split('/')[0] or None


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


def filter_views(found):
    """The same rows, cut three ways: alive status, then agent, then class.

    A markdown file cannot filter itself, so the filter is a set of views of
    the same table, each with an anchor, and an index of them. The order is
    the order a reader asks the questions in: did the character live, which
    agent played it, and what class it was.
    """
    views = []
    for status, label in (('alive', 'Alive'), ('died', 'Died')):
        cut = [row for row in found if row.get('alive') == status]
        if cut:
            views.append((f'{status}', label, f'{status}', cut))
    for agent in sorted({row['agent'] for row in found if row.get('agent')}):
        cut = [row for row in found if row.get('agent') == agent]
        views.append((f'agent-{agent}', f'Agent {agent}', f'agent-{agent}', cut))
    for klass in sorted({row['class'] for row in found if row.get('class')}):
        cut = [row for row in found if row.get('class') == klass]
        # GitHub's anchors are lower-cased, so the anchor of "Class Druid"
        # is #class-druid even though the heading reads Druid.
        views.append((f'class-{klass.lower()}', f'Class {klass}',
                      f'class-{klass.lower()}', cut))
    return views


def filter_markdown(found):
    """The index of the views, and the views themselves."""
    views = filter_views(found)
    lines = ['## Filters', '']
    lines.append('The table above is every run. These are the same rows cut '
                 'three ways, in the order the questions are usually asked: '
                 '**did the character live**, then **which agent played it**, '
                 'then **what class it was**.')
    lines.append('')
    for title, keys in (('Alive status', ('alive', 'died')),
                        ('Agent', tuple(v[2] for v in views
                                        if v[2].startswith('agent-'))),
                        ('Class', tuple(v[2] for v in views
                                        if v[2].startswith('class-')))):
        links = []
        for _, label, anchor, cut in views:
            if anchor in keys:
                links.append(f"[{label}](#{anchor}) ({len(cut)})")
        if links:
            lines.append(f'- **{title}**: ' + ', '.join(links))
    lines.append('')
    for _, label, anchor, cut in views:
        lines.append(f'### {label}')
        lines.append('')
        lines.append(markdown(cut))
        lines.append('')
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


def characters(found):
    """The runs grouped by character (the lineage key), each with its lives
    in order and its best numbers. A character with one recording gets no
    page of its own - the sections treat it differently."""
    by_name = {}
    for row in found:
        by_name.setdefault(row['lineage'], []).append(row)
    out = []
    for name, lives in sorted(by_name.items()):
        lives = sorted(lives, key=lambda row: row['run'])
        out.append({
            'name': name,
            'lives': lives,
            'best_level': max((row['character_level'] or 0) for row in lives),
            'best_wealth': max((row['wealth'] or 0) for row in lives),
            'deaths': sum(1 for row in lives if (row['outcome'] or '').startswith('died')),
        })
    return out


def character_page(character, base='../'):
    """One page for a multi-life character: the lives in order, each with
    its numbers and its replay. It is written under records/characters/, so
    the replays are one directory up."""
    rows = []
    for row in character['lives']:
        outcome = row['outcome'] or '?'
        rows.append(
            f"<li><strong>{html.escape(row['run'])}</strong> - CL {row['character_level']}, "
            f"worth {row['wealth']}, depth {row['max_depth']}, {html.escape(outcome)} "
            f"(<a href=\"{base}{row['run']}/report.html\">replay</a> · "
            f"<a href=\"https://github.com/diegoami/borg-runner/blob/main/records/{row['run']}/REPORT.md\">report</a>)</li>")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(character['name'])}</title>
<style>{PAGE_STYLE}</style></head><body><main>
<h1>{html.escape(character['name'])}</h1>
<p class="sub">{len(character['lives'])} lives of one character, in order.
Best: character level {character['best_level']}, worth {character['best_wealth']}.
The whole set of characters is on the <a href="../overview.html">overview</a>;
who is worth imitating and why is in
<a href="https://github.com/diegoami/borg-runner/blob/main/ACCUMULATED_BEHAVIOUR.md">ACCUMULATED_BEHAVIOUR.md</a>.</p>
<ul>{''.join(rows)}</ul>
</main></body></html>
"""


def write_all(found=None, log=print):
    """Every form of the table: the markdown, both pages, and a page per
    multi-life character."""
    found = found if found is not None else rows()
    written = [write_markdown(found)]
    for where in PAGES:
        written.append(write_page(found, into=run_module.pins.ROOT / where))
    characters_dir = run_module.RECORDS / 'characters'
    characters_dir.mkdir(exist_ok=True)
    for character in characters(found):
        if len(character['lives']) < 2:
            continue        # one recording: a page of its own is overkill
        path = characters_dir / f"{character['name']}.html"
        path.write_text(character_page(character))
        written.append(path)
    for path in written:
        log(f'overview: {path}')
    return written


def characters_markdown(found):
    """The characters, before the runs: who the runs belong to.

    A markdown reader gets the same two sections the page has - multi-life
    characters, each with a page under `characters/`, and single-life
    characters, whose one link is the run itself.
    """
    cast = characters(found)

    def by_results(character):
        return (-character['best_level'], -character['best_wealth'])

    multi = sorted((c for c in cast if len(c['lives']) > 1), key=by_results)
    single = sorted((c for c in cast if len(c['lives']) == 1), key=by_results)
    lines = ['## Characters', '',
             'The runs below belong to characters; a character can live '
             "several lives, and the lives inherit each other's notes. These "
             'have more than one recording, and each has a page listing them '
             'in order.', '']
    for character in multi:
        died = f", {character['deaths']} died" if character['deaths'] else ''
        lines.append(
            f"- [{character['name']}](characters/{character['name']}.html) - "
            f"{len(character['lives'])} lives, best character level "
            f"{character['best_level']}, worth "
            f"{character['best_wealth']:,}{died}")
    lines += ['', '## Single-life characters', '',
              'One recording each, so no page of their own - the link is the '
              'run.', '']
    for character in single:
        row = character['lives'][0]
        lines.append(
            f"- [{row['run']}]({row['run']}/) - character level "
            f"{character['best_level']}, worth "
            f"{character['best_wealth']:,}, {row['outcome'] or '?'}")
    return '\n'.join(lines)


def write_markdown(found=None, into=None):
    found = found if found is not None else rows()
    into = Path(into) if into else run_module.RECORDS / 'OVERVIEW.md'
    body = [
        '# The characters, and every run',
        '',
        'Generated by `python -m borg_runner overview`; do not edit by hand.',
        '',
        characters_markdown(found),
        '',
        '## Every run',
        '',
        '`wealth` is the gold plus the game\'s own `object_value()` of',
        'everything carried and worn, so a lucky dive and a well-equipped',
        'descent read differently. `inherited` names the notebook the run',
        'started from. A model is written provider/model-version, because two',
        'runs of the same family months apart are not the same experiment.',
        '',
        '**To cut the table, see [Filters](#filters)** — alive status first,',
        'then the agent, then the character class.',
        '',
        markdown(found),
        '',
        filter_markdown(found),
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
  var alive = document.getElementById('alive'), agent = document.getElementById('agent');
  var klass = document.getElementById('klass');
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
    var wantedAlive = alive.value, wantedAgent = agent.value, wantedClass = klass.value;
    var shown = runs.filter(function (r) {
      if (wantedAlive !== 'all' && (r.alive || '') !== wantedAlive) { return false; }
      if (wantedAgent !== 'all' && (r.agent || '') !== wantedAgent) { return false; }
      if (wantedClass !== 'all' && (r.class || '') !== wantedClass) { return false; }
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
        + '<td class="model">' + (r.playbook
            ? '<a href="https://github.com/diegoami/borg-runner/tree/main/agents/'
              + escaped(r.playbook) + '">' + escaped(r.playbook) + '</a>'
            : '—') + '</td>'
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
  alive.onchange = draw;
  agent.onchange = draw;
  klass.onchange = draw;
  find.oninput = draw;
  draw();
})();
</script>
"""

HEADINGS = (('run', 'run'), ('seed', 'seed'), ('model', 'model'),
            ('character', 'character'), ('max_depth', 'depth'), ('character_level', 'level'),
            ('wealth', 'wealth'), ('asks', 'asks'), ('keypresses', 'keys'),
            ('final_turn', 'turn'), ('outcome', 'outcome'),
            ('tokens', 'tokens'), ('inherited', 'inherited'),
            ('playbook', 'playbook'))


def page(found=None, standalone=True, base=''):
    """The table as a page: filter by model, search, sort, and open a replay.

    `base` is the path prefix for the replay links the "start here" block
    points at: the same page is written at the repository root and under
    records/, and only one of those has records/ in front of it."""
    found = found if found is not None else rows()
    models = sorted({row['model'] for row in found if row['model']})
    options = ''.join(f'<option value="{html.escape(name)}">{html.escape(name)}</option>'
                      for name in models)
    # The three cuts a reader asks for most, in the order they ask them:
    # did the character live, which agent played it, what class it was.
    alive_options = ''.join(
        f'<option value="{value}">{label}</option>'
        for value, label in (('alive', 'alive'), ('died', 'died'))
        if any(row.get('alive') == value for row in found))
    agent_options = ''.join(
        f'<option value="{html.escape(name)}">{html.escape(name)}</option>'
        for name in sorted({row['agent'] for row in found if row.get('agent')}))
    class_options = ''.join(
        f'<option value="{html.escape(name)}">{html.escape(name)}</option>'
        for name in sorted({row['class'] for row in found if row.get('class')}))
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
    # The page leads with characters, not runs: multi-life characters get a
    # page each under records/characters/, single-life characters link their
    # one replay directly.
    cast = characters(found)
    multi = [c for c in cast if len(c['lives']) > 1]
    single = [c for c in cast if len(c['lives']) == 1]
    def by_results(character):
        return (-character['best_level'], -character['best_wealth'])
    multi_html = ''.join(
        f'<li><a href="{base}characters/{html.escape(c["name"])}.html">'
        f'<strong>{html.escape(c["name"])}</strong></a> - '
        f'{len(c["lives"])} lives, best CL {c["best_level"]}, '
        f'worth {c["best_wealth"]}'
        + (f', {c["deaths"]} died' if c['deaths'] else '') + '</li>'
        for c in sorted(multi, key=by_results))
    single_html = ''.join(
        f'<li><a href="{base}{html.escape(c["lives"][0]["run"])}/report.html">'
        f'<strong>{html.escape(c["lives"][0]["run"])}</strong></a> - '
        f'CL {c["best_level"]}, worth {c["best_wealth"]}, '
        f'{html.escape(c["lives"][0]["outcome"] or "?")}</li>'
        for c in sorted(single, key=by_results))
    character_sections = (
        '<h2>Characters</h2>\n'
        '<p class="sub">The runs above belong to characters; a character can '
        'live several lives, and the lives inherit each other\'s notes. '
        'These have more than one recording - each has its own page.</p>\n'
        f'<ul>{multi_html}</ul>\n'
        '<h2>Single-life characters</h2>\n'
        '<p class="sub">One recording each, so no page of their own - the '
        'link is the replay.</p>\n'
        f'<ul>{single_html}</ul>\n')
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
<p class="sub"><strong>Start here:</strong> the characters worth imitating are
the ones that levelled and got rich - character level and net worth, with
depth as context and never the score.
<a href="https://github.com/diegoami/borg-runner/blob/main/ACCUMULATED_BEHAVIOUR.md">ACCUMULATED_BEHAVIOUR.md</a>
says who they are and what they did.</p>
{character_sections}
<div class="controls">
  <label for="alive">Alive</label>
  <select id="alive"><option value="all">all</option>{alive_options}</select>
  <label for="agent">Agent</label>
  <select id="agent"><option value="all">all agents</option>{agent_options}</select>
  <label for="klass">Class</label>
  <select id="klass"><option value="all">all classes</option>{class_options}</select>
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
    base = 'records/' if into.name == 'index.html' else ''
    into.write_text(page(found, standalone=standalone, base=base))
    return into
