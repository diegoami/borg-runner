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
    print(f'=== ASK {asked["ask"]}  turn {asked["turn"]}{cursor} ===')
    print(asked['screen'].rstrip('\n'))
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


def cmd_record(args):
    print(json.dumps(run_module.write_record(args.run), indent=2, sort_keys=True))
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

    p = sub.add_parser('record', help='write the run record')
    p.add_argument('--run', required=True, type=Path)
    p.set_defaults(func=cmd_record)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    return args.func(args)
