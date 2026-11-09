"""The model driver. No model is called here; the parsing is what breaks."""
from borg_runner import autoplay


def test_a_fenced_json_reply_is_read():
    answer = autoplay.decision_of('Thinking...\n```json\n'
                                  '{"keys": "2222", "reason": "south"}\n```\n')
    assert answer == {'keys': '2222', 'reason': 'south'}


def test_a_bare_json_reply_is_read():
    assert autoplay.decision_of('{"keys":" ","reason":"splash"}')['keys'] == ' '


def test_a_reply_with_no_object_is_refused():
    """Better to stop the run than to press a key nobody chose."""
    assert autoplay.decision_of('I would walk south.') is None
    assert autoplay.decision_of('') is None
    assert autoplay.decision_of('{"reason": "no keys here"}') is None


def test_the_session_id_starts_with_ses():
    """OpenCode refuses any other shape, with 'Expected a string starting with ses'."""
    assert autoplay.SESSION.format(run='x').startswith('ses')


def test_the_instructions_tell_the_model_the_escapes_and_nothing_tactical():
    text = autoplay.INSTRUCTIONS
    for escape in ('\\n', '\\e', '\\t'):
        assert escape in text
    assert 'KC_ENTER' in text, 'the model must know Return is not 0x0d'
    for opinion in ('if hit points', 'always flee', 'never fight'):
        assert opinion not in text.lower(), 'the driver holds no tactics (D2)'


def test_the_first_message_carries_the_screen_and_the_memory():
    first = autoplay.first_message('SCREEN HERE', memory='two flasks')
    assert 'SCREEN HERE' in first and 'two flasks' in first
    assert autoplay.INSTRUCTIONS in first
    later = autoplay.later_message('NEXT SCREEN', memory='one flask')
    assert autoplay.INSTRUCTIONS not in later, 'the instructions are sent once'
    assert 'NEXT SCREEN' in later and 'one flask' in later
