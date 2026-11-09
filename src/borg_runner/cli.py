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
    process = run_module.start(run, args.seed, log=print)
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
    run_module.answer(run, args.number, keys_from(args.keys),
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
    r"""The keys as the frontend reads them: \n is Enter and \e is Escape."""
    return text


def cmd_replay(args):
    verdict = replay_module.replay(args.run, args.into or (run_module.RUNS /
                                   f'{Path(args.run).name}-replay'),
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

    print(report_module.write(args.run, args.into))
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
    print(json.dumps(run_module.write_record(args.run, cost=cost),
                     indent=2, sort_keys=True))
    return 0


def cmd_carry_on(args):
    """Replay a run's keys into a fresh run and leave it playing."""
    from . import replay as replay_module

    into = run_module.RUNS / (args.name or f'{Path(args.run).name}-again')
    verdict = replay_module.carry_on(args.run, into)
    print(json.dumps({'run': str(into), 'identical': verdict['identical'],
                      'waiting_at_ask': verdict['asks_replayed'] + 1,
                      'turn': verdict['turn_reached']}, indent=2))
    return 0 if verdict['identical'] else 1


def cmd_status(args):
    """Where every run stands, finished or not."""
    standing = run_module.status()
    if not standing:
        print('no runs yet')
        return 0
    print(f"{'run':<22} {'state':<17} {'asks':>9} {'depth':>5} {'turn':>6} "
          f"{'s/ask':>6} {'notes':>5}  character / outcome")
    for row in standing:
        state = row['state']
        asks = f"{row['answered']}/{row['asked']}"
        print(f"{row['run']:<22} {state:<17} {asks:>9} "
              f"{str(row['depth'] if row['depth'] is not None else '-'):>5} "
              f"{str(row['turn'] or '-'):>6} "
              f"{str(row['seconds_per_decision'] or '-'):>6} "
              f"{row['notes']:>5}  "
              f"{row['character'] or '-'}"
              f"{'  ' + row['outcome'] if row['outcome'] else ''}")
    return 0


def cmd_overview(args):
    from . import overview as overview_module

    print(overview_module.write_markdown(into=args.into))
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
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--into', type=Path)
    p.set_defaults(func=cmd_report)

    p = sub.add_parser('record', help='write the run record')
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--tokens', type=int,
                   help='what the run cost, for a run a session played')
    p.add_argument('--tool-calls', type=int)
    p.add_argument('--played-by', help='session, subagent, opencode, openrouter')
    p.add_argument('--model')
    p.set_defaults(func=cmd_record)

    p = sub.add_parser('carry-on', help="continue where another run stopped")
    p.add_argument('--run', required=True, type=Path, help='the run to continue')
    p.add_argument('--name', help='the new run (default: <run>-again)')
    p.set_defaults(func=cmd_carry_on)

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
