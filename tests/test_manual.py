"""The Jev manual. It is an input under test, so its shape is tested."""
from borg_runner import decisions, manual


def test_the_manual_parses_into_its_four_parts():
    loaded = manual.load()
    assert loaded['instructions'].startswith('Which single key')
    for part in ('keys', 'goals', 'strategy', 'state_contract'):
        assert loaded[part], f'{part} is empty'
    assert len(loaded['sha256']) == 64


def test_the_manual_says_what_the_state_contains():
    """D10's contract, written where the model's own instructions are."""
    contract = manual.load()['state_contract']
    for field in ('screen', 'depth_in_levels', 'cursor',
                  'keys_already_pressed_here_that_changed_nothing',
                  'the_goal_you_chose_last_time'):
        assert field in contract, field


def test_the_strategy_keeps_the_rule_ids_it_was_compressed_from():
    """So a lead can argue with a named rule rather than with a vibe."""
    strategy = manual.load()['strategy']
    assert 'ESC-01' in strategy and 'DEPTH-01' in strategy
    assert 'staircase' in strategy['ESC-01']


def test_the_goal_question_is_asked_and_is_the_models_own_memory():
    loaded = manual.load()
    questions = decisions.questions_for(None, loaded)
    assert sorted(questions) == ['goal', 'key']
    assert questions['goal']['type'] == 'choice'
    assert 'descend' in questions['goal']['criteria']
    assert 'your own memory' in questions['goal']['instructions']


def test_the_strategy_reaches_the_key_question():
    text = decisions.instructions_from(manual.load())
    assert 'ESC-01' in text
    assert 'measured, not truths' in text


def test_a_described_key_keeps_the_games_own_name_first():
    """Three layers, and only the middle one is ours."""
    options = decisions.options(manual.load())
    assert options['>'].startswith('press >: go down staircase')
    assert 'Only while standing on one' in options['>']


def test_the_goal_is_carried_into_the_next_state():
    state = decisions.state_for({'screen': 's', 'turn': 1, 'depth': 1, 'max_depth': 1},
                                None, goal='descend', inert=['<', '>'])
    assert state['the_goal_you_chose_last_time'] == 'descend'
    assert state['keys_already_pressed_here_that_changed_nothing'] == ['<', '>']
    assert state['depth_in_levels'] == 1
