"""The pins are the one thing every other part depends on."""
import re

from borg_runner import pins


def test_every_pin_names_a_repository_and_a_full_commit():
    for name, entry in pins.load().items():
        assert entry['repository'].count('/') == 1, name
        assert re.fullmatch(r'[0-9a-f]{40}', entry['commit']), name
        assert entry['role'].strip(), f'{name} does not say what it is for'


def test_the_game_is_pinned_at_plain_angband_426():
    """D1: the game is upstream 4.2.6, not a Borg fork.

    borg-agent pins the same commit as `original`, which is what makes a run
    here and a Borg run the same game.
    """
    game = pins.pin('angband')
    assert game['repository'] == 'angband/angband'
    assert game['version'] == '4.2.6'
    assert game['commit'] == 'e473720ed88a0f0c7ca66815cef3000eb4a38bc3'


def test_the_manual_is_pinned_because_the_player_must_read_it():
    """D9: the agent reads the manual, and it reads it at a commit."""
    assert 'docs/command.rst' in pins.pin('angband')['manual']
    assert pins.pin('strategy-manual')['path'].endswith('/')


def test_an_unknown_pin_says_what_there_is():
    try:
        pins.pin('nonesuch')
    except KeyError as problem:
        assert 'angband' in str(problem)
    else:
        raise AssertionError('an unknown pin should raise')
