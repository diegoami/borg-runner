"""The run, the record, and the replay.

The fast tests work on a run directory made by hand, because the shape of the
directory is the contract; the slow one plays and replays a real game.
"""
import json
from pathlib import Path

import pytest

from borg_runner import replay, run as run_module


def a_run(tmp_path, asks=(('1', ' '), ('2', 'a'))):
    """A run directory of the shape the frontend writes."""
    run = tmp_path / 'r1'
    (run / run_module.ASK).mkdir(parents=True)
    (run / 'started.json').write_text(json.dumps({
        'schema': 'borg-runner/started@1', 'seed': 7, 'pid': 1,
        'character': 'r1', 'command': [], 'savefile': str(tmp_path / 'nosave'),
        'build': {'game': 'angband/angband', 'commit': 'x' * 40,
                  'patch_sha256': 'y' * 64}}))
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
    assert asked['ask'] == 1 and asked['turn'] == 10
    assert asked['screen'] == 'screen 1\n'
    assert asked['depth'] == 1 and asked['max_depth'] == 2
    assert asked['cursor'] == {'x': 4, 'y': 9}
    # A question written by an older build carries none of the standing.
    assert asked['level'] is None and asked['carried'] is None


def test_a_question_carries_the_characters_standing(tmp_path):
    """The game's own numbers: level, hit points, gold, and what it carries."""
    run = a_run(tmp_path)
    (run / run_module.ASK / 'question-1.txt').write_text(
        'ask 1\nturn 10\ndepth 1\nmax_depth 2\nlevel 6\nhp 98 98\n'
        'gold 146\ncarried 1200\ncursor 4 9\n')
    asked = run_module.question(run, 1)
    assert asked['level'] == 6
    assert asked['race'] is None, 'an older question carries no character'
    assert asked['hp'] == {'now': 98, 'max': 98}
    assert asked['gold'] == 146 and asked['carried'] == 1200
    run_module.answer(run, 1, ' ', reason='x')
    record = run_module.write_record(run, outcome='stopped')
    assert record['character_level'] == 6
    assert record['carried_value'] == 1200
    assert record['wealth'] == 1346, 'gold plus what is carried'


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


def test_a_note_gets_one_bullet_however_the_player_wrote_it(tmp_path):
    run = a_run(tmp_path)
    run_module.remember(run, '- already bulleted', ask=3)
    run_module.remember(run, 'not bulleted', ask=4)
    lines = (run / run_module.NOTEBOOK).read_text().splitlines()
    assert lines == ['- already bulleted (ask 3)', '- not bulleted (ask 4)']


def test_the_notebook_is_shown_but_never_corrected(tmp_path):
    """D4: a wrong belief is a result, so nothing here edits it."""
    run = a_run(tmp_path)
    run_module.remember(run, 'something false', ask=1)
    assert 'something false' in run_module.notebook(run)
    run_module.answer(run, 2, 'x', reason='later')
    assert 'something false' in run_module.notebook(run), 'it must survive'


def test_keeping_a_notebook_records_where_it_came_from(tmp_path):
    """Promotion into knowledge/ carries the seed, the build and the hashes."""
    run = a_run(tmp_path)
    run_module.remember(run, '`>` needs a down staircase', ask=2)
    run_module.write_record(run, outcome='stopped')
    kept = run_module.keep(run, into=tmp_path / 'kept.md', log=lambda *a: None)
    text = kept.read_text()
    assert 'seed: 7' in text and 'angband/angband' in text
    assert '`>` needs a down staircase' in text
    assert text.count('## The notes') == 1


def test_a_run_can_inherit_a_notebook(tmp_path):
    """T10's mechanism: the next run starts with the last one's notes."""
    source = tmp_path / 'inherited.md'
    source.write_text('- oil is thrown with v (ask 83)\n')
    run = tmp_path / 'fresh'
    (run / run_module.ASK).mkdir(parents=True)
    carried = run_module.inherit(run, source, log=lambda *a: None)
    assert 'oil is thrown' in run_module.notebook(run)
    assert carried['sha256'] and str(source) in carried['inherited_from']


def test_keeping_refuses_a_run_that_learned_nothing(tmp_path):
    run = a_run(tmp_path)
    try:
        run_module.keep(run, into=tmp_path / 'x.md', log=lambda *a: None)
    except FileNotFoundError as problem:
        assert 'kept no notes' in str(problem)
    else:
        raise AssertionError('an empty notebook should not be promoted')


# The real screen from runs/sonnet-3, kept as a fixture: a hand-written box
# matched a regex that the game's own tombstone did not, because the game
# draws its menu to the right of the box.
TOMBSTONE = (Path(__file__).parent / 'tombstone.txt').read_text()


def test_a_death_is_read_from_the_games_own_tombstone(tmp_path):
    """The record must say the character died, and what killed it."""
    run = a_run(tmp_path)
    (run / run_module.ASK / 'screen-3.txt').write_text(TOMBSTONE)
    death = run_module.death_of(run)
    assert death == {'died': True, 'depth': 1, 'cause': 'a small kobold',
                     'tombstone': 'screen-3.txt'}


def test_a_run_that_died_is_recorded_as_died_whatever_it_was_told(tmp_path):
    run = a_run(tmp_path)
    (run / run_module.ASK / 'screen-3.txt').write_text(TOMBSTONE)
    record = run_module.write_record(run, outcome='stopped')
    assert record['outcome'] == 'died'
    assert record['killed_by'] == 'a small kobold'
    assert record['death_depth'] == 1


def test_a_living_run_has_no_death(tmp_path):
    run = a_run(tmp_path)
    assert run_module.death_of(run) is None
    assert run_module.write_record(run, outcome='stopped')['died'] is False


def test_the_record_says_which_race_and_class_the_game_drew(tmp_path):
    """The run presses * for both, so only the game knows what it got."""
    run = a_run(tmp_path)
    (run / run_module.ASK / 'question-1.txt').write_text(
        'ask 1\nturn 10\ndepth 0\nmax_depth 0\nlevel 1\ngold 146\n'
        'carried 100\nrace Half-Troll\nclass Warrior\ncursor 1 2\n')
    run_module.answer(run, 1, '*', reason='the game draws the race')
    record = run_module.write_record(run, outcome='stopped')
    assert record['race'] == 'Half-Troll'
    assert record['class'] == 'Warrior'
    assert record['character'] == 'Half-Troll Warrior'


def test_a_run_is_kept_in_git_without_its_screens(tmp_path):
    """The keys are the recording; the screens replay from them (D6)."""
    run = a_run(tmp_path)
    run_module.answer(run, 1, ' ', reason='past the splash')
    run_module.answer(run, 2, '2222', reason='four steps south')
    run_module.remember(run, 'something learned', ask=1)
    run_module.write_record(run, outcome='stopped')
    kept = run_module.archive(run, into=tmp_path / 'kept', log=lambda *a: None)
    names = sorted(p.name for p in kept.iterdir())
    assert 'input.txt' in names, 'the keys are the point'
    assert 'record.json' in names and 'decisions.jsonl' in names
    assert 'notebook.md' in names
    assert not any(name.startswith('screen-') for name in names)
    assert (kept / 'input.txt').read_text() == run_module.keys_sent(run)


def test_the_cost_of_a_run_is_recorded(tmp_path):
    """A session-played run has no call log, so its cost is written in."""
    run = a_run(tmp_path)
    record = run_module.write_record(
        run, outcome='stopped',
        cost={'tokens': 162466, 'tool_calls': 129, 'played_by': 'subagent'})
    assert record['cost']['tokens'] == 162466
    assert record['cost']['played_by'] == 'subagent'


def test_a_provider_played_run_sums_its_own_cost(tmp_path):
    run = a_run(tmp_path)
    (run / 'model-calls.jsonl').write_text(
        '{"ask": 1, "model": "m", "usage": {"tokens": {"total_tokens": 100,'
        ' "cost": 0.001}, "served_model": "served/one"}}\n'
        '{"ask": 2, "model": "m", "usage": {"tokens": {"total_tokens": 50,'
        ' "cost": 0.002}, "served_model": "served/two"}}\n')
    spent = run_module.spend(run)
    assert spent['model_calls'] == 2
    assert spent['tokens'] == 150
    assert spent['usd'] == 0.003
    assert spent['models'] == ['served/one', 'served/two']


def test_the_tombstones_clock_is_not_a_difference():
    """The game prints the wall clock on the tomb; it is not game state."""
    from borg_runner import replay as replay_module
    first = 'RIP\n   on Mon Nov  9 20:09:29 2026   \n'
    again = 'RIP\n   on Tue Dec 25 03:00:00 2027   \n'
    assert first != again
    assert replay_module.comparable(first) == replay_module.comparable(again)


def test_a_real_difference_on_the_tomb_is_still_caught():
    from borg_runner import replay as replay_module
    kobold = 'by a small kobold.\n   on Mon Nov  9 20:09:29 2026   \n'
    naga = 'by a black naga.\n   on Mon Nov  9 20:09:29 2026   \n'
    assert replay_module.comparable(kobold) != replay_module.comparable(naga)


def test_the_reading_note_is_about_files_not_about_the_word_read(tmp_path):
    """The first attempt matched "read the letter from the list" in a note
    about shopping, and reported that as the run's reading."""
    run = a_run(tmp_path)
    run_module.remember(run, 'Store letters skip, so read the letter off the '
                             'screen rather than counting', ask=25)
    run_module.remember(run, 'Opened before play: docs/BRIEF.md, command.rst '
                             '(run/rest), strategy-manual ch14 Warrior', ask=1)
    note = run_module.reading_note(run)
    assert note.startswith('Opened before play')


def test_a_run_says_whether_it_read_the_playbook_for_the_class_it_drew(tmp_path):
    run = a_run(tmp_path)
    run_module.remember(run, 'Opened: docs/BRIEF.md, command.rst, '
                             'strategy-manual ch14 Warrior section', ask=1)
    note = run_module.reading_note(run)
    assert run_module.read_for_its_character(run, note, 'Warrior') is True
    assert run_module.read_for_its_character(run, note, 'Mage') is False
    assert run_module.read_for_its_character(run, note, None) is None


def test_a_record_does_not_lose_what_it_already_knew(tmp_path):
    """A standing recovered by replaying old keys must survive a rewrite."""
    run = a_run(tmp_path)
    run_module.answer(run, 1, ' ', reason='x')
    run_module.write_record(run, outcome='stopped')
    import json
    path = run / run_module.RECORD
    record = json.loads(path.read_text())
    record['character'] = 'Half-Troll Warrior'
    record['class'] = 'Warrior'
    record['standing_from'] = 'a replay of the archived keys'
    path.write_text(json.dumps(record))
    again = run_module.write_record(run, outcome='stopped')
    assert again['character'] == 'Half-Troll Warrior'
    assert again['standing_from'] == 'a replay of the archived keys'


def test_two_runs_of_the_same_character_are_refused(tmp_path, monkeypatch):
    """Runs may play at the same time; they may not share a savefile.

    Each run has its own directory, game process and notebook, so parallel
    runs are the normal case - but the savefile is named after the character,
    and a second run of the same name would delete the first one's save.
    """
    import os
    import pytest

    monkeypatch.setattr(run_module, 'RUNS', tmp_path)
    live = tmp_path / 'first'
    (live / run_module.ASK).mkdir(parents=True)
    (live / 'started.json').write_text(json.dumps(
        {'seed': 7, 'character': 'shared', 'pid': os.getpid(), 'build': {}}))
    second = tmp_path / 'second'
    (second / run_module.ASK).mkdir(parents=True)
    with pytest.raises(RuntimeError, match='already playing'):
        run_module.start(second, 7, character='shared', log=lambda *a: None)


def test_a_finished_run_does_not_block_another(tmp_path, monkeypatch):
    """Only a *live* process holds the name."""
    monkeypatch.setattr(run_module, 'RUNS', tmp_path)
    done = tmp_path / 'done'
    (done / run_module.ASK).mkdir(parents=True)
    (done / 'started.json').write_text(json.dumps(
        {'seed': 7, 'character': 'shared', 'pid': 999999, 'build': {}}))
    # No exception: the pid is gone, so the name is free. The build is not
    # prepared here, so it fails later and for another reason.
    try:
        run_module.start(tmp_path / 'next', 7, character='shared',
                         out=tmp_path / 'nobuild', log=lambda *a: None)
    except RuntimeError as problem:
        assert 'already playing' not in str(problem)
    except FileNotFoundError:
        pass


def test_status_does_not_call_a_dead_character_playing(tmp_path, monkeypatch):
    """The game outlives the character: it draws the tombstone and waits."""
    import os

    monkeypatch.setattr(run_module, 'RUNS', tmp_path)
    run = a_run(tmp_path)
    run_module.answer(run, 1, ' ', reason='x')
    (run / 'started.json').write_text(json.dumps(
        {'seed': 7, 'character': 'r1', 'pid': os.getpid(), 'build': {}}))
    (run / run_module.ASK / 'screen-2.txt').write_text(TOMBSTONE)
    run_module.write_record(run, outcome='stopped')
    row, = [r for r in run_module.status(tmp_path) if r['run'] == 'r1']
    assert row['state'] == 'dead at the tomb'
    assert row['playing'] is True, 'the process really is alive'


def test_status_reports_how_far_a_run_has_got(tmp_path, monkeypatch):
    monkeypatch.setattr(run_module, 'RUNS', tmp_path)
    run = a_run(tmp_path)
    run_module.answer(run, 1, ' ', reason='x')
    run_module.remember(run, 'something', ask=1)
    (run / 'started.json').write_text(json.dumps(
        {'seed': 7, 'character': 'r1', 'pid': 999999, 'build': {}}))
    row, = [r for r in run_module.status(tmp_path) if r['run'] == 'r1']
    # "stopped" alone would not say whether anything survives.
    assert row['state'] == 'stopped, not saved'
    assert row['saved'] is False
    assert row['can_carry_on'] is True, 'its keys replay, which is enough'
    assert (row['answered'], row['asked']) == (1, 2)
    assert row['notes'] == 1


def test_carrying_a_run_on_does_not_replay_the_quit(tmp_path):
    """The keys that ended a run are not keys that played it.

    Carrying sonnet-2 on first handed over a game sitting at "Saving game...
    done. Press Return", because the replay faithfully re-executed the
    save-and-quit the session had sent.
    """
    from borg_runner import replay as replay_module
    run = a_run(tmp_path, asks=(('1', ' '), ('2', 'a'), ('3', 'x')))
    (run / run_module.ASK / 'question-3.txt').write_text(
        'ask 3\nturn 30\ndepth 1\nmax_depth 1\ncursor 0 0\n')
    (run / run_module.ASK / 'screen-3.txt').write_text('still playing\n')
    run_module.answer(run, 1, '2222', reason='four steps south')
    run_module.answer(run, 2, run_module.SAVE_AND_QUIT,
                      reason='the run was stopped')
    run_module.answer(run, 3, '\\e', reason='accept the save')
    assert replay_module.recorded_keys(run) == ['2222', '\x18', '\\e']
    assert replay_module.recorded_keys(run, played_only=True) == ['2222']
