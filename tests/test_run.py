"""The run, the record, and the replay.

The fast tests work on a run directory made by hand, because the shape of the
directory is the contract; the slow one plays and replays a real game.
"""
import json

import pytest

from borg_runner import replay, run as run_module


def a_run(tmp_path, asks=(('1', ' '), ('2', 'a'))):
    """A run directory of the shape the frontend writes."""
    run = tmp_path / 'r1'
    (run / run_module.ASK).mkdir(parents=True)
    (run / 'started.json').write_text(json.dumps({
        'schema': 'borg-runner/started@1', 'seed': 7, 'pid': 1,
        'character': 'r1', 'command': [], 'savefile': str(tmp_path / 'nosave'),
        'build': {'commit': 'x' * 40}}))
    for number, _ in asks:
        (run / run_module.ASK / f'question-{number}.txt').write_text(
            f'ask {number}\nturn {int(number) * 10}\ndepth 1\nmax_depth 2\n'
            f'cursor 4 9\n')
        (run / run_module.ASK / f'screen-{number}.txt').write_text(f'screen {number}\n')
    return run


def test_a_question_carries_the_turn_the_cursor_and_the_screen(tmp_path):
    """The cursor is the menu highlight, which the screen cannot show."""
    run = a_run(tmp_path)
    asked = run_module.question(run, 1)
    assert asked == {'ask': 1, 'turn': 10, 'screen': 'screen 1\n',
                     'depth': 1, 'max_depth': 2, 'cursor': {'x': 4, 'y': 9}}


def test_answering_writes_the_keys_and_records_the_reason(tmp_path):
    run = a_run(tmp_path)
    run_module.answer(run, 1, '2222', reason='four steps south', memory='in town')
    assert (run / run_module.ASK / 'keys-1.txt').read_text() == '2222'
    entry, = run_module.decisions(run)
    assert entry == {'ask': 1, 'turn': 10, 'depth': 1, 'keys': '2222',
                     'reason': 'four steps south', 'memory': 'in town'}


def test_only_unanswered_asks_are_waiting(tmp_path):
    run = a_run(tmp_path)
    assert run_module.asked(run) == [1, 2]
    run_module.answer(run, 1, ' ')
    assert run_module.asked(run) == [2]


def test_the_memory_carried_forward_is_the_newest_one(tmp_path):
    """D4: the agent's memory goes back into the next prompt, unaltered."""
    run = a_run(tmp_path)
    run_module.answer(run, 1, ' ', memory='two flasks of oil')
    run_module.answer(run, 2, 'a', reason='no new memory')
    assert run_module.memory_now(run) == 'two flasks of oil'


def test_the_keys_are_the_whole_recording(tmp_path):
    """D6: seed plus keys, in order, and nothing else."""
    run = a_run(tmp_path)
    run_module.answer(run, 1, ' ')
    run_module.answer(run, 2, 'aa')
    assert run_module.keys_sent(run) == ' aa'
    record = run_module.write_record(run, outcome='stopped')
    assert record['keypresses'] == 3
    assert (run / run_module.KEYS).read_text() == ' aa'
    assert record['seed'] == 7


def test_a_replay_reads_the_keys_ask_by_ask(tmp_path):
    run = a_run(tmp_path)
    run_module.answer(run, 1, ' ', reason='splash')
    run_module.answer(run, 2, '2222', reason='south')
    assert replay.recorded_keys(run) == [' ', '2222']


@pytest.mark.slow
def test_a_game_is_born_played_recorded_and_replays_identically(tmp_path):
    """The gate for T03-T06. Builds the game; takes about a minute.

    Birth is played from the screen like a person would: the letter moves the
    menu highlight and `\\n` selects it.
    """
    run = run_module.directory(f'test-{tmp_path.name}')
    process = run_module.start(run, 7, log=lambda *a: None)
    plan = [' ', 'a', 'a', 'b', r'\n', r'\n', r'\n', 'y', ' ', '2222']
    try:
        for number, keys in enumerate(plan, start=1):
            assert replay.wait_for(run, number, process), f'no question {number}'
            run_module.answer(run, number, keys, reason='the test plays birth')
        assert replay.wait_for(run, 11, process)
        assert run_module.question(run, 11)['turn'] > 1, 'the game never started'
    finally:
        run_module.stop(run, process, log=lambda *a: None)
    record = run_module.write_record(run, process, outcome='stopped')
    assert record['final_turn'] > 1
    assert record['savefile_sha256'], 'the savefile is what takeover needs'

    verdict = replay.replay(run, run_module.RUNS / f'{run.name}-replay',
                            log=lambda *a: None)
    assert verdict['identical'], verdict['differences']
    assert verdict['asks_replayed'] == verdict['asks_recorded']
