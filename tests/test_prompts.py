"""The prompts may repeat the page and may not replace it.

What this file pins down is one rule: a tip that a player needs lives on
`manuals/INSTRUCTIONS.md`, where every player reads it, and a prompt - handed
to one player and then thrown away - may only point at it or repeat it. The
check is `borg_runner.prompts`, and each test below doctors one prompt to show
the check can fail, because a check that cannot fail is not a check.
"""
import pytest

from borg_runner import prompts

GOOD = """Play one game, from manuals/INSTRUCTIONS.md and agents/{AGENT}/.

The town puts you on the down staircase. FACT,
`src/gen-cave.c town_gen_layout()` sets it on the player's own square.
"""


def write(tmp_path, text, name='PROMPT.txt'):
    path = tmp_path / name
    path.write_text(text)
    return [path]


def test_the_repositorys_own_prompts_say_nothing_the_page_does_not():
    assert prompts.check() == []


def test_the_prompts_checked_are_the_templates_and_every_brief():
    names = [path.name for path in prompts.files()]
    assert names[:2] == ['PLAYGAME.txt', 'CONTINUEGAME.txt']
    assert all(path.is_file() for path in prompts.files())


def test_a_clean_prompt_passes(tmp_path):
    assert prompts.check(write(tmp_path, GOOD)) == []


def test_a_labelled_claim_with_no_anchor_is_caught(tmp_path):
    text = GOOD + '\nOBSERVED: a mage should always buy oil before descending.\n'
    problems = prompts.check(write(tmp_path, text))
    assert any('OBSERVED claim with no anchor' in p for p in problems), problems


def test_a_citation_that_is_not_on_the_page_is_caught(tmp_path):
    text = GOOD + '\nFACT, `src/cave-map.c invented_function()` does the rest.\n'
    problems = prompts.check(write(tmp_path, text))
    assert any('invented_function' in p and 'nowhere in' in p
               for p in problems), problems


def test_a_run_citation_that_is_not_on_the_page_is_caught(tmp_path):
    text = GOOD + '\nOBSERVED, nosuchrun-9#404: the shops close on a Tuesday.\n'
    problems = prompts.check(write(tmp_path, text))
    assert any('nosuchrun-9#404' in p for p in problems), problems


def test_the_harness_own_files_are_not_claims_about_the_game(tmp_path):
    text = GOOD + '\nYour keys end up in `input.txt`, and `runs/x/ask/screen-1.txt`\nis the screen. FACT, `src/gen-cave.c town_gen_layout()`.\n'
    assert prompts.check(write(tmp_path, text)) == []


def test_pointing_at_a_section_the_page_no_longer_has_is_caught(tmp_path):
    text = GOOD + '\nIt is in manuals/INSTRUCTIONS.md under "The one thing that was deleted".\n'
    problems = prompts.check(write(tmp_path, text))
    assert any('does not say that any more' in p for p in problems), problems


def test_pointing_at_a_section_the_page_does_have_passes(tmp_path):
    text = GOOD + '\nIt is in manuals/INSTRUCTIONS.md under "The one thing to take from this page".\n'
    assert prompts.check(write(tmp_path, text)) == []


@pytest.mark.parametrize('missing, fragment', [
    ('manuals/INSTRUCTIONS.md', 'does not send the player to manuals'),
    ('agents/{AGENT}/', 'playbook in agents/'),
])
def test_a_prompt_that_does_not_send_the_player_to_read_is_caught(
        tmp_path, missing, fragment):
    problems = prompts.check(write(tmp_path, GOOD.replace(missing, 'nowhere')))
    assert any(fragment in p for p in problems), problems


def test_a_brief_must_say_which_template_it_is_added_to(tmp_path, monkeypatch):
    monkeypatch.setattr(prompts, 'BRIEFS', tmp_path)
    assert prompts.check(write(tmp_path, GOOD)) != []
    assert prompts.check(write(tmp_path, GOOD + '\nAdd this to PLAYGAME.txt.\n')) == []


def test_the_mage_shuttle_brief_is_kept_in_the_repository():
    """The brief that started this: an objective worth running again is a file."""
    names = [path.name for path in prompts.files()]
    assert 'mage-shuttle-to-level-5.txt' in names
