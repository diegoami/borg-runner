"""The commands. `python -m borg_runner <command>`."""
import argparse
import json
import sys
from pathlib import Path

from . import build, replay as replay_module, run as run_module


def cmd_build(args):
    out = build.prepare(args.output, force=args.force)
    print(build.binary(out))
    return 0


def cmd_play(args):
    """Start a game and leave it waiting for the first answer."""
    run = run_module.directory(args.name)
    if args.notebook:
        run_module.inherit(run, args.notebook)
    asked_for = {k: v for k, v in (('race', args.race), ('class', args.klass))
                 if v}
    process = run_module.start(run, args.seed, asked_for=asked_for, log=print)
    if not replay_module.wait_for(run, 1, process, timeout=60):
        run_module.stop(run, process)
        print('the game never asked for a key; see game.log', file=sys.stderr)
        return 1
    run_module.write_record(run, process, outcome='playing')
    print(run)
    print(f'answer with: python -m borg_runner answer 1 <keys> --run {run}')
    return 0


def show(run, number, with_memory=True):
    asked = run_module.question(run, number)
    where = asked.get('cursor')
    cursor = f'  cursor at {where["x"]},{where["y"]}' if where else ''
    print(f'=== ASK {asked["ask"]}  turn {asked["turn"]}  '
          f'depth {asked.get("depth")}{cursor} ===')
    print(asked['screen'].rstrip('\n'))
    book = run_module.notebook(run)
    if book:
        print('=== YOUR NOTEBOOK (yours; nothing here writes or corrects it) ===')
        print(book)
    memory = run_module.memory_now(run)
    if with_memory and memory:
        print('=== YOUR MEMORY (yours to keep; nothing here maintains it) ===')
        print(memory)
    print(f'=== answer: python -m borg_runner answer {number} <keys> --run {run} ===')


def cmd_wait(args):
    """Show the oldest unanswered question."""
    waiting = run_module.asked(args.run)
    if not waiting:
        print('nothing is waiting; the game may have ended (see record.json)')
        return 2
    show(args.run, waiting[0])
    return 0


def cmd_answer(args):
    """Send keys, then show whatever the game asks next."""
    run = Path(args.run)
    if not (run / run_module.ASK / f'question-{args.number}.txt').exists():
        print(f'there is no question {args.number} in {run}', file=sys.stderr)
        return 1
    keys = keys_from(args.keys)
    if keys != args.keys:
        print("note: a real newline in your keys became the escape \\n, which "
              "is what the game's prompts wait for; the frontend drops a "
              "trailing newline byte as a text editor's, not a key")
    run_module.answer(run, args.number, keys,
                      reason=args.reason, memory=args.memory)
    if args.note:
        run_module.remember(run, args.note, ask=args.number)
    import subprocess, time
    for _ in range(600):
        waiting = run_module.asked(run)
        if waiting:
            show(run, waiting[0])
            run_module.write_record(run, outcome='playing')
            return 0
        time.sleep(0.1)
    print('no new question within 60s; the game may have ended')
    run_module.write_record(run, outcome='ended')
    return 2


def keys_from(text):
    r"""The keys as the frontend reads them: \n is Enter and \e is Escape.

    A real newline byte is translated to the two-character escape, because the
    frontend drops a **trailing** one on purpose - it is the newline a text
    editor adds, not a key (`patch/src/main-agent.c`) - and a player that
    sends `$'...\n'` from a shell therefore loses its last Enter silently, with
    the prompt left open and every later key eaten by it. Measured, five asks
    (minimaxflash-2#72). Translating here keeps the recording canonical and
    costs nothing: the frontend turns the escape into KC_ENTER either way.
    """
    return text.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')


def cmd_replay(args):
    verdict = replay_module.replay(args.run, args.into or (run_module.RUNS /
                                   f'{Path(args.run).name}-replay'),
                                   frames=args.frames,
                                   stop_after=args.stop_after)
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0 if verdict['identical'] else 1


def cmd_takeover(args):
    verdict = replay_module.takeover(args.run, args.into or (run_module.RUNS /
                                     f'{Path(args.run).name}-takeover'),
                                     at_turn=args.at_turn)
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0 if verdict['savefile_written'] else 1


def cmd_autoplay(args):
    """Start a game and let a model play it through OpenCode."""
    from . import autoplay as autoplay_module

    run = run_module.directory(args.name)
    process = run_module.start(run, args.seed, log=print)
    if not replay_module.wait_for(run, 1, process, timeout=60):
        run_module.stop(run, process)
        print('the game never asked for a key; see game.log', file=sys.stderr)
        return 1
    try:
        answered = autoplay_module.autoplay(run, args.model, process=process,
                                            max_asks=args.max_asks, agent=args.agent,
                                            via=args.via, manual_name=args.manual,
                                            with_pages=args.manual_pages)
    finally:
        run_module.stop(run, process, log=print)
    record = run_module.write_record(run, process, outcome='autoplay')
    print(json.dumps({'run': str(run), 'asks_answered': answered,
                      'final_turn': record['final_turn'],
                      'keypresses': record['keypresses']}, indent=2))
    return 0 if answered else 1


def cmd_keep(args):
    """Promote a run's notebook into knowledge/."""
    print(run_module.keep(args.run, args.into))
    return 0


def cmd_report(args):
    from . import report as report_module

    if args.all:
        report_module.rebuild_all()
        return 0
    if not args.run:
        print('say which run, or --all', file=sys.stderr)
        return 1
    print(report_module.write(args.run, args.into))
    return 0


def cmd_playbook(args):
    """What this model family has written down for its own next session."""
    from . import playbooks

    if args.check:
        complaints = playbooks.check()
        for complaint in complaints:
            print(complaint, file=sys.stderr)
        denied = playbooks.disagreements()
        for row in denied:
            print(f'the game says otherwise: {row}', file=sys.stderr)
        print(f'{len(playbooks.families())} families, {len(complaints)} complaints, '
              f'{len(denied)} numbers the game denies')
        if denied:
            print('a family page is one player\'s account, but a spell\'s mana and '
                  'dice are facts: correct the line where it stands')
        return 1 if complaints or denied else 0
    if not args.family:
        found = playbooks.families()
        if not found:
            print('no playbooks yet; the first run of a family writes one')
            return 0
        for row in found:
            classes = ', '.join(row['classes']) or 'no class page yet'
            print(f"agents/{row['family']:<12} {row['lines']:>5} lines   {classes}")
        return 0
    if args.start:
        print(playbooks.start(args.family, run=args.start))
        return 0
    if args.append:
        if not args.from_run:
            print('say which run is writing: --from <run>', file=sys.stderr)
            return 1
        text = (sys.stdin.read() if args.append == '-'
                else Path(args.append).read_text())
        print(playbooks.append(args.family, text, args.from_run,
                               character_class=args.klass))
        return 0
    playing = playbooks.live_runs(mine=args.from_run)
    if playing:
        print(f"{len(playing)} runs are playing right now "
              f"({', '.join(playing)}). If any of them is a {args.family} run "
              f"it will write to these same pages when it stops, and a "
              f"whole-file rewrite would erase it. Add your part instead:")
        print(f'    python -m borg_runner playbook --family {args.family} '
              f'--append - --from <your run>   # your section, on stdin')
    kept = playbooks.sections(args.family, args.klass)
    if kept:
        print(f"{len(kept)} appended sections wait to be folded into the body: "
              + ', '.join(row['run'] for row in kept))
    missing = 0
    for row in playbooks.paths(args.family, args.klass):
        where = row['path'].relative_to(run_module.pins.ROOT)
        if row['exists']:
            print(f"{str(where):<28} {row['lines']:>5} lines   {row['what']}")
        else:
            missing += 1
            print(f"{str(where):<28}     - does not exist yet ({row['what']}): "
                  f'nobody of this family has written it, so you do')
    if not missing:
        return 0
    borrowed = playbooks.elsewhere(args.family, args.klass)
    for row in borrowed:
        where = row['path'].relative_to(run_module.pins.ROOT)
        print(f"{str(where):<28} {row['lines']:>5} lines   borrow: "
              f"{row['what']} - read it, do not edit it")
    if borrowed:
        print('another family has played this before you: read theirs, say in '
              'your first note that you did, and write your own when you stop '
              '- naming what you took and whether it held.')
    elif args.klass:
        print(f'no family has written about a {args.klass} yet; you are the '
              f'first, so the page is yours to write.')
    print('write what is missing when you stop, with the run it came from: '
          f'python -m borg_runner playbook --family {args.family} '
          f'--start <your run name>')
    return 0


def cmd_audit(args):
    """Did a finished run leave everything a finished run should leave?"""
    from . import audit as audit_module

    names = audit_module.archived() if args.all else [Path(args.run).name]
    worst = 0
    for name in names:
        rows = audit_module.audit(name)
        bad = [row for row in rows if not row['ok']]
        if args.all and not bad:
            print(f'{name}: all {len(rows)} checks pass')
            continue
        print(f'=== {name}: {len(rows) - len(bad)} of {len(rows)} checks pass')
        for row in rows:
            if row['ok'] and args.all:
                continue
            mark = 'ok  ' if row['ok'] else ('warn' if row['warn'] else 'MISS')
            print(f"  {mark}  {row['what']}")
            if not row['ok'] and row['fix']:
                print(f"        -> {row['fix']}")
        if any(not row['ok'] and not row['warn'] for row in rows):
            worst = 1
    return worst


def cmd_consolidate(args):
    """What the reports say that the page does not."""
    from . import consolidate as consolidate_module

    if args.inputs:
        print(json.dumps(consolidate_module.inputs(), indent=1, sort_keys=True))
        return 0
    if args.check:
        problems = consolidate_module.check()
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f'the page: {len(problems)} problems')
        return 1 if problems else 0
    for row in consolidate_module.themes():
        mark = 'on the page' if row['answered'] else 'NOT on the page'
        raised = ', '.join(row['raised_by']) or 'nobody yet'
        print(f"{row['slug']:<34} {len(row['raised_by']):>2} runs     "
              f"{mark:<15} {raised}")
    waiting = consolidate_module.unanswered()
    if waiting:
        print('\nthese recur and the page says nothing: '
              + ', '.join(row['slug'] for row in waiting))
        print('a theme that comes back is the page\'s fault, not the '
              'players\': docs/CONSOLIDATE.md')
    unread = consolidate_module.uncited()
    if unread:
        print(f"\nnot cited anywhere on the page yet: {', '.join(unread)}")
    return 0


def cmd_prompts(args):
    """A prompt may repeat the page; it may not be the only place a tip lives."""
    from . import prompts as prompts_module

    if args.inputs:
        print(json.dumps(prompts_module.inputs(), indent=1, sort_keys=True))
        return 0
    paths = [Path(name) for name in args.paths] or None
    problems = prompts_module.check(paths)
    for problem in problems:
        print(problem, file=sys.stderr)
    checked = paths if paths is not None else prompts_module.files()
    print(f'{len(checked)} prompts: {len(problems)} problems')
    if not problems:
        print('every labelled claim they make is anchored and on the page')
    return 1 if problems else 0


def cmd_tools(args):
    """The shared screen tools, and what runs have written."""
    from . import tools as tools_module

    if args.check:
        problems = tools_module.check()
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f'tools/screen: {len(problems)} problems')
        return 1 if problems else 0
    if args.adopt:
        if not args.from_run:
            print('say which run wrote it: --from <run>', file=sys.stderr)
            return 1
        print(tools_module.adopt(args.adopt, args.from_run, name=args.name))
        return 0
    for row in tools_module.shared():
        came = f"from {row['from_run']}" if row['from_run'] else 'for the library'
        print(f"tools/screen/{row['name']:<12} {row['lines']:>4} lines  "
              f"{came:<22} {row['summary']}")
    written = tools_module.by_runs()
    if written:
        print('\nwritten by runs, not in the library '
              '(adopt one with --adopt <path> --from <run>):')
        for row in written:
            where = '' if row['archived'] else '  (still playing)'
            print(f"  {row['run']}/{row['name']:<16} {row['lines']:>4} lines"
                  f"{where}")
    return 0


def cmd_export(args):
    """The hand-over to the consumer: what the corpus establishes."""
    from . import export as export_module

    if args.inputs:
        print(json.dumps(export_module.inputs(), indent=1, sort_keys=True))
        return 0
    if args.check:
        problems = export_module.check()
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f'{export_module.ACCUMULATED.name}: {len(problems)} problems')
        return 1 if problems else 0
    counted = export_module.corpus()
    print(f"corpus: {len(counted['runs'])} runs, {counted['asks']:,} asks, "
          f"{counted['keypresses']:,} keypresses, deepest depth "
          f"{counted['deepest']}, {counted['deaths']} deaths")
    silent = sorted(set(counted['runs']) - set(counted['reports']))
    if silent:
        print(f"wrote no report, so nothing to export: {', '.join(silent)}")
    waiting = export_module.missing()
    if waiting:
        print(f"not read by any edition yet: {', '.join(waiting)}")
        print(f'write the next edition of {export_module.ACCUMULATED.name}; '
              f'the process is docs/EXPORT.md')
    else:
        print(f'{export_module.ACCUMULATED.name} has read every report')
    return 0


def cmd_record(args):
    cost = None
    if args.tokens or args.played_by or args.model:
        cost = {'tokens': args.tokens, 'played_by': args.played_by,
                'model': args.model, 'tool_calls': args.tool_calls}
        cost = {name: value for name, value in cost.items() if value}
    if args.model and '/' not in args.model:
        print('a model is written provider/model-version, for example '
              'anthropic/claude-sonnet-5-5', file=sys.stderr)
        return 1
    print(json.dumps(run_module.write_record(args.run, cost=cost,
                                             playbook=args.playbook),
                     indent=2, sort_keys=True))
    return 0


def cmd_carry_on(args):
    """Replay a run's keys into a fresh run and leave it playing."""
    from . import replay as replay_module

    into = run_module.RUNS / (args.name
                              or run_module.next_generation(Path(args.run).name))
    verdict = replay_module.carry_on(args.run, into)
    print(json.dumps({'run': str(into), 'identical': verdict['identical'],
                      'waiting_at_ask': verdict['asks_replayed'] + 1,
                      'turn': verdict['turn_reached']}, indent=2))
    return 0 if verdict['identical'] else 1


def cmd_history(args):
    """The runs this character has been through, oldest first."""
    past = run_module.ancestry(args.run)
    for step in past:
        print(f"{step['run']}")
        for what in ('report', 'notebook'):
            if step[what]:
                print(f"    {what:<9} {step[what]}")
    if len(past) == 1:
        print('    (this character has not been carried on from anything)')
    return 0


def cmd_stop(args):
    """End a run's game cleanly, so it saves and does not linger."""
    process = run_module.started_process(args.run)
    if process is None:
        print(f'{Path(args.run).name}: no game of its own is running')
    else:
        run_module.stop(args.run, process)
    record = run_module.write_record(args.run, outcome=args.outcome)
    print(json.dumps({k: record.get(k) for k in
                      ('run', 'asks', 'keypresses', 'final_turn', 'max_depth',
                       'character', 'character_level', 'wealth', 'outcome',
                       'killed_by')}, indent=2))
    return 0


def cmd_status(args):
    """Where every run stands, finished or not."""
    standing = run_module.status()
    if not standing:
        print('no runs yet')
        return 0
    print(f"{'run':<22} {'state':<17} {'asks':>9} {'deep':>4} {'now':>4} {'turn':>6} "
          f"{'s/ask':>6} {'notes':>5}  character / outcome")
    for row in standing:
        state = row['state']
        asks = f"{row['answered']}/{row['asked']}"
        print(f"{row['run']:<22} {state:<17} {asks:>9} "
              f"{str(row['depth'] if row['depth'] is not None else '-'):>4} "
              f"{str(row['depth_now'] if row['depth_now'] is not None else '-'):>4} "
              f"{str(row['turn'] or '-'):>6} "
              f"{str(row['seconds_per_decision'] or '-'):>6} "
              f"{row['notes']:>5}  "
              f"{row['character'] or '-'}"
              f"{'  ' + row['outcome'] if row['outcome'] else ''}")
    return 0


def cmd_overview(args):
    from . import overview as overview_module

    if args.into:
        print(overview_module.write_markdown(into=args.into))
    else:
        overview_module.write_all()
    return 0


def cmd_archive(args):
    """Keep a run in git: the seed, the keys, the reasons and the notes."""
    print(run_module.archive(args.run, args.into))
    return 0


def parser():
    top = argparse.ArgumentParser(prog='borg_runner', description=__doc__)
    sub = top.add_subparsers(dest='command', required=True)

    p = sub.add_parser('build', help='build the pinned game with our frontend')
    p.add_argument('--output', type=Path)
    p.add_argument('--force', action='store_true')
    p.set_defaults(func=cmd_build)

    p = sub.add_parser('play', help='start a game and wait for the first answer')
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--name')
    p.add_argument('--notebook', type=Path,
                   help='start with these notes, from knowledge/ or another run')
    p.add_argument('--race', help='be born this race instead of drawing one; '
                                  'recorded, so a chosen character is visible')
    p.add_argument('--class', dest='klass', help='likewise for the class')
    p.set_defaults(func=cmd_play)

    p = sub.add_parser('wait', help='show the question waiting now')
    p.add_argument('--run', required=True, type=Path)
    p.set_defaults(func=cmd_wait)

    p = sub.add_parser('answer', help='send keys and show the next screen')
    p.add_argument('number', type=int)
    p.add_argument('keys')
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--reason', default='', help='one line, recorded with the keys')
    p.add_argument('--memory', help='your memory of the world, carried into the next prompt')
    p.add_argument('--note', help='a trick worth keeping, appended to your notebook '
                                  'and shown with every later screen')
    p.set_defaults(func=cmd_answer)

    p = sub.add_parser('replay', help='play a recording again and compare screens')
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--into', type=Path)
    p.add_argument('--stop-after', type=int, help='stop once this game turn is reached')
    p.add_argument('--frames', action='store_true',
                   help='also dump the screen at every input event '
                        '(frame-<ask>-<n>.txt), not just at the asks')
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser('takeover', help='replay to a turn, save, and hand over in X11')
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--at-turn', type=int, required=True)
    p.add_argument('--into', type=Path)
    p.set_defaults(func=cmd_takeover)

    p = sub.add_parser('autoplay', help='let a model play, through OpenCode')
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--model', required=True,
                   help='as OpenCode names it, e.g. openrouter/typesafe/jev-router')
    p.add_argument('--name')
    p.add_argument('--agent')
    p.add_argument('--max-asks', type=int, default=200)
    p.add_argument('--via', choices=('opencode', 'openrouter', 'decisions'),
                   default='opencode',
                   help='opencode holds the credential; openrouter calls the API '
                        'directly and reads OPENROUTER_API_KEY from the environment')
    p.add_argument('--manual', default='jev-1',
                   help='the manual in manuals/, for the decisions backend')
    p.add_argument('--manual-pages', action='store_true',
                   help="also put the game's own manual pages in the state")
    p.set_defaults(func=cmd_autoplay)

    p = sub.add_parser('keep', help="promote a run's notebook into knowledge/")
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--into', type=Path)
    p.set_defaults(func=cmd_keep)

    p = sub.add_parser('report', help='one run as a self-contained HTML page')
    p.add_argument('--run', type=Path)
    p.add_argument('--into', type=Path)
    p.add_argument('--all', action='store_true',
                   help="regenerate every archived run's replay page")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser('record', help='write the run record')
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--tokens', type=int,
                   help='what the run cost, for a run a session played')
    p.add_argument('--tool-calls', type=int)
    p.add_argument('--played-by', help='session, subagent, opencode, openrouter')
    p.add_argument('--model')
    p.add_argument('--playbook',
                   help='the model family whose playbook you read and wrote '
                        'back to, e.g. minimax for agents/minimax/')
    p.set_defaults(func=cmd_record)

    p = sub.add_parser('playbook',
                       help="a model family's own notes, for its next session")
    p.add_argument('--family', help='the model family, e.g. minimax')
    p.add_argument('--class', dest='klass',
                   help='also the page for this class, e.g. Druid')
    p.add_argument('--start', metavar='RUN',
                   help="create the family's COMMON.md if it has none, "
                        'naming the run that writes it')
    p.add_argument('--append', metavar='FILE',
                   help="add a section to the family's page without rewriting "
                        "it; FILE may be - for standard input")
    p.add_argument('--from', dest='from_run', metavar='RUN',
                   help='the run writing the section, which heads it')
    p.add_argument('--check', action='store_true',
                   help='check the layout of every playbook')
    p.set_defaults(func=cmd_playbook)

    p = sub.add_parser('audit',
                       help='did a finished run leave what it should leave?')
    p.add_argument('--run', type=Path, help='the run, or its name')
    p.add_argument('--all', action='store_true', help='every archived run')
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser('consolidate',
                       help='the recurring themes in the reports, and whether '
                            'the page answers them')
    p.add_argument('--check', action='store_true',
                   help='every claim on the page names a run that exists')
    p.add_argument('--inputs', action='store_true',
                   help='what a consolidating session is given, as JSON')
    p.set_defaults(func=cmd_consolidate)

    p = sub.add_parser('prompts',
                       help='check the prompts: nothing may be said only there')
    p.add_argument('paths', nargs='*', metavar='FILE',
                   help='prompts to check instead of the repository\'s own '
                        '(use before handing a new brief to a player)')
    p.add_argument('--check', action='store_true',
                   help='the default, and the only thing this does')
    p.add_argument('--inputs', action='store_true',
                   help='what it reads, as JSON')
    p.set_defaults(func=cmd_prompts)

    p = sub.add_parser('tools',
                       help='the shared screen tools runs may use and add to')
    p.add_argument('--adopt', metavar='PATH',
                   help="copy a run's tool into tools/screen/")
    p.add_argument('--from', dest='from_run', metavar='RUN',
                   help='the run that wrote it, which the header records')
    p.add_argument('--name', help='the name it takes in the library')
    p.add_argument('--check', action='store_true',
                   help='every tool parses, says where it came from, and does '
                        'not import borg_runner')
    p.set_defaults(func=cmd_tools)

    p = sub.add_parser('export',
                       help='the hand-over to the consumer (borg-reborn-rs)')
    p.add_argument('--check', action='store_true',
                   help='what is wrong with the current edition')
    p.add_argument('--inputs', action='store_true',
                   help='exactly what to read to write the next edition')
    p.set_defaults(func=cmd_export)

    p = sub.add_parser('carry-on', help="continue where another run stopped")
    p.add_argument('--run', required=True, type=Path, help='the run to continue')
    p.add_argument('--name',
                   help='the new run (default: the next generation of this '
                        'character, <base>.<n>)')
    p.set_defaults(func=cmd_carry_on)

    p = sub.add_parser('history', help="the runs this character has been through")
    p.add_argument('--run', required=True, type=Path)
    p.set_defaults(func=cmd_history)

    p = sub.add_parser('stop', help="end a run's game cleanly")
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--outcome', default='stopped')
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser('status', help='where every run stands, finished or not')
    p.set_defaults(func=cmd_status)

    p = sub.add_parser('overview', help='the table of every archived run')
    p.add_argument('--into', type=Path)
    p.set_defaults(func=cmd_overview)

    p = sub.add_parser('archive', help='keep a run in git under records/')
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--into', type=Path)
    p.set_defaults(func=cmd_archive)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    return args.func(args)
