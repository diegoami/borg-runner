"""The per-family playbooks under agents/, and the prompts that use them.

A playbook is read before the first keypress and written after the last one,
so what these tests hold is the layout (which a tool can check) and the two
prompts' order (which is what went wrong with the write-ups: a step listed
after `archive` is a step that does not happen).
"""
import json
from pathlib import Path

import pytest

from borg_runner import pins, playbooks, run as run_module

from test_run import a_run


def a_playbook(tmp_path, family='minimax', text='# COMMON\n\nseen in sonnet-1.\n',
               name=playbooks.COMMON):
    (tmp_path / family).mkdir(parents=True, exist_ok=True)
    (tmp_path / family / name).write_text(text)
    return tmp_path


def test_the_repositorys_own_playbooks_are_well_formed():
    assert playbooks.check() == []


def test_a_family_keeps_a_common_page_and_a_page_per_class():
    minimax = [row for row in playbooks.families() if row['family'] == 'minimax']
    assert minimax, 'agents/minimax/ is the first playbook and should be listed'
    assert minimax[0]['common'] and 'Druid' in minimax[0]['classes']


def test_the_class_page_is_the_class_in_capitals():
    wanted = playbooks.paths('minimax', 'Druid')
    assert [path['path'].name for path in wanted] == ['COMMON.md', 'DRUID.md']
    assert all(path['exists'] and path['lines'] > 50 for path in wanted)


def test_a_family_that_has_never_played_has_nothing_to_read():
    wanted = playbooks.paths('nobody-yet', 'Warrior')
    assert [path['exists'] for path in wanted] == [False, False]


def test_a_playbook_that_cites_no_run_is_a_complaint(tmp_path):
    """The repository's claim is that anything in it can be checked."""
    a_playbook(tmp_path, text='# COMMON\n\nalways fight in corridors.\n')
    complaints = playbooks.check(tmp_path, known_runs=['sonnet-1'])
    assert any('names no run' in complaint for complaint in complaints)


def test_a_page_named_after_no_class_is_a_complaint(tmp_path):
    a_playbook(tmp_path)
    (tmp_path / 'minimax' / 'TACTICS.md').write_text('seen in sonnet-1.\n')
    complaints = playbooks.check(tmp_path, known_runs=['sonnet-1'])
    assert any('TACTICS.md' in c and 'no class' in c for c in complaints)


def test_a_family_without_a_common_page_is_a_complaint(tmp_path):
    a_playbook(tmp_path, name=playbooks.class_file('Druid'))
    complaints = playbooks.check(tmp_path, known_runs=['sonnet-1'])
    assert any('has no COMMON.md' in complaint for complaint in complaints)


def test_an_empty_page_is_a_complaint(tmp_path):
    a_playbook(tmp_path, text='   \n')
    assert any('is empty' in c for c in playbooks.check(tmp_path, known_runs=['x']))


def test_a_family_with_no_page_for_its_class_is_pointed_at_another(tmp_path):
    """The first run of a class has nothing of its own, and need not."""
    a_playbook(tmp_path, family='minimax', text='# COMMON\n\nfrom sonnet-1.\n')
    (tmp_path / 'minimax' / playbooks.class_file('Druid')).write_text(
        '# DRUID\n\nfrom sonnet-1.\n')
    a_playbook(tmp_path, family='codex', text='# COMMON\n\nfrom sonnet-1.\n')
    borrowed = playbooks.elsewhere('codex', 'Druid', where=tmp_path)
    assert [(row['family'], row['path'].name) for row in borrowed] == [
        ('minimax', 'DRUID.md')], 'only the page it lacks, and not its own'


def test_a_family_with_nothing_at_all_borrows_both(tmp_path):
    a_playbook(tmp_path, family='minimax', text='# COMMON\n\nfrom sonnet-1.\n')
    (tmp_path / 'minimax' / playbooks.class_file('Druid')).write_text('d\n')
    borrowed = playbooks.elsewhere('newcomer', 'Druid', where=tmp_path)
    assert [row['path'].name for row in borrowed] == ['COMMON.md', 'DRUID.md']


def test_a_family_that_has_its_own_pages_borrows_nothing(tmp_path):
    a_playbook(tmp_path, family='minimax', text='# COMMON\n\nfrom sonnet-1.\n')
    (tmp_path / 'minimax' / playbooks.class_file('Druid')).write_text('d\n')
    a_playbook(tmp_path, family='codex', text='# COMMON\n\nfrom sonnet-1.\n')
    (tmp_path / 'codex' / playbooks.class_file('Druid')).write_text('d\n')
    assert playbooks.elsewhere('codex', 'Druid', where=tmp_path) == []


def test_a_class_nobody_has_played_has_nothing_to_borrow(tmp_path):
    a_playbook(tmp_path, family='minimax', text='# COMMON\n\nfrom sonnet-1.\n')
    borrowed = playbooks.elsewhere('minimax', 'Blackguard', where=tmp_path)
    assert borrowed == [], 'its own COMMON exists and no other family has one'


def test_a_first_run_can_start_its_familys_page(tmp_path):
    page = playbooks.start('newmodel', run='newmodel-1', where=tmp_path)
    assert page.name == playbooks.COMMON and 'newmodel-1' in page.read_text()
    # It never overwrites: the family's own words survive a second call.
    page.write_text('# COMMON\n\nmine, from newmodel-1.\n')
    assert 'mine' in playbooks.start('newmodel', where=tmp_path).read_text()


def test_the_record_says_which_family_playbook_the_run_used(tmp_path):
    run = a_run(tmp_path)
    record = run_module.write_record(run, playbook='minimax')
    assert record['playbook'] == 'minimax'
    # And a later rewrite does not lose it, as the standing once was lost.
    assert run_module.write_record(run)['playbook'] == 'minimax'


def test_archive_says_whether_the_run_wrote_back(tmp_path, monkeypatch):
    run = a_run(tmp_path)
    monkeypatch.setattr(playbooks, 'AGENTS', tmp_path / 'agents')
    a_playbook(tmp_path / 'agents', family='fam',
               text='# COMMON\n\nseen in r1.\n')
    run_module.write_record(run, playbook='fam')
    # started.json is written before the playbook here, so the page counts as
    # written during the run.
    assert 'wrote back to agents/fam/' in run_module._playbook_note(run)

    stale = tmp_path / 'agents' / 'fam' / playbooks.COMMON
    import os
    old = (run / 'started.json').stat().st_mtime - 10
    os.utime(stale, (old, old))
    assert 'wrote nothing back' in run_module._playbook_note(run)


def test_a_run_that_names_no_family_is_told_so(tmp_path):
    run = a_run(tmp_path)
    run_module.write_record(run)
    assert 'names no playbook' in run_module._playbook_note(run)


PROMPTS = ('PLAYGAME.txt', 'CONTINUEGAME.txt')


@pytest.mark.parametrize('name', PROMPTS)
def test_both_prompts_send_the_player_to_its_own_directory(name):
    text = (pins.ROOT / name).read_text()
    assert '{AGENT}' in text, 'the prompt must name which agent is playing'
    assert 'agents/{AGENT}/COMMON.md' in text
    assert 'playbook --family {AGENT}' in text
    assert '--playbook {AGENT}' in text, 'the record must carry the family'
    assert 'git add records/{RUNNAME} knowledge/{RUNNAME}.md agents/{AGENT}' \
        in text, 'the commit must include the playbook the run just wrote'


@pytest.mark.parametrize('name', PROMPTS)
def test_both_prompts_say_a_missing_page_can_be_borrowed(name):
    """A family's first run of a class should not start from nothing."""
    # As prose: both prompts wrap, so a sentence spans lines.
    prose = ' '.join((pins.ROOT / name).read_text().split())
    assert "another family's page for the same class" in prose
    assert 'never edit theirs' in prose


@pytest.mark.parametrize('name', PROMPTS)
def test_the_writing_comes_before_the_finishing_commands(name):
    """The lesson of the lost report: a step after `archive` does not happen."""
    text = (pins.ROOT / name).read_text()
    report = text.index('WRITE IT UP FIRST')
    playbook = text.index('WRITE BACK TO agents/{AGENT}/')
    commands = text.index('borg_runner record --run')
    assert report < playbook < commands


# The three documents the knowledge layer shed on 2026-11-10, once the page
# carried their content. `records/` and `knowledge/` keep their own words,
# and consolidate.py and docs/CONSOLIDATE.md say what was removed and why.
GONE = ('NOTES.md', 'LEARNED.md', 'MANUAL-GAPS.md')
READING = ('PLAYGAME.txt', 'CONTINUEGAME.txt', 'README.md', 'AGENTS.md',
           'docs/BRIEF.md', 'agents/README.md', 'manuals/INSTRUCTIONS.md',
           'manuals/INSTRUCTIONS_2.md')


@pytest.mark.parametrize('name', PROMPTS)
def test_both_prompts_say_the_town_staircase_is_under_you(name):
    """Four runs walked the town looking for what they stood on."""
    prose = ' '.join((pins.ROOT / name).read_text().split())
    assert 'town_gen_layout' in prose
    assert 'l>g' in prose


@pytest.mark.parametrize('name', READING)
def test_nothing_a_player_reads_points_at_a_file_that_is_gone(name):
    text = (pins.ROOT / name).read_text()
    stale = [gone for gone in GONE if gone in text]
    assert not stale, f'{name} still sends a reader to {stale}'


def test_the_knowledge_directory_is_now_evidence_only():
    """One file per run and nothing else: no distillate to keep in step."""
    from borg_runner import consolidate
    runs = consolidate.recorded_runs()
    kept = sorted(path.name for path in run_module.KNOWLEDGE.glob('*.md')
                  if path.stem not in runs)
    assert not kept, f'{kept} are in knowledge/ and are not a run notebook'


def test_two_runs_appending_at_once_both_survive(tmp_path):
    """Three sessions of one family play at once and all write this page."""
    a_playbook(tmp_path, family='fam', text='# COMMON\n\nfrom sonnet-1.\n')
    playbooks.append('fam', 'I measured A.', 'run-a', where=tmp_path)
    playbooks.append('fam', 'I measured B.', 'run-b', where=tmp_path)
    text = (tmp_path / 'fam' / playbooks.COMMON).read_text()
    assert 'from sonnet-1.' in text, 'what was there is kept'
    assert 'I measured A.' in text and 'I measured B.' in text
    assert text.index('I measured A.') < text.index('I measured B.')
    kept = playbooks.sections('fam', where=tmp_path)
    assert [row['run'] for row in kept] == ['run-a', 'run-b']


def test_appending_to_a_family_with_no_page_starts_one(tmp_path):
    page = playbooks.append('newcomer', 'first.', 'newcomer-1', where=tmp_path)
    assert page.name == playbooks.COMMON
    assert 'newcomer-1' in page.read_text() and 'first.' in page.read_text()


def test_a_class_page_takes_appends_too(tmp_path):
    a_playbook(tmp_path, family='fam', text='# COMMON\n\nfrom sonnet-1.\n')
    page = playbooks.append('fam', 'mage things.', 'run-c',
                            character_class='Mage', where=tmp_path)
    assert page.name == 'MAGE.md'
    assert playbooks.sections('fam', 'Mage', where=tmp_path)[0]['run'] == 'run-c'


def test_the_lock_file_is_not_part_of_the_repository(tmp_path):
    playbooks.append('fam', 'x.', 'run-a', where=tmp_path)
    locks = list((tmp_path / 'fam').glob('.*.lock'))
    assert locks, 'the append takes a lock beside the page'
    ignored = (pins.ROOT / '.gitignore').read_text()
    assert 'agents/**/.*.lock' in ignored


def test_concurrent_appends_merge_instead_of_conflicting():
    """Two runs committing appends must not stop each other's rebase."""
    attributes = (pins.ROOT / '.gitattributes').read_text()
    assert 'agents/**/*.md merge=union' in attributes


@pytest.mark.parametrize('name', PROMPTS)
def test_both_prompts_say_to_append_when_others_are_playing(name):
    prose = ' '.join((pins.ROOT / name).read_text().split())
    assert 'append - do not rewrite' in prose
    assert '--append - --from' in prose


# -- a family page may be wrong about the game, and that is checkable ---------

def test_a_wrong_spell_bonus_in_a_family_page_is_caught(tmp_path):
    """MAGE.md read Magic Missile's `$Dd4` as `3d4+3`, and the wrong number
    travelled into a brief written for the next mage before anyone noticed."""
    page = tmp_path / 'minimax' / 'MAGE.md'
    page.parent.mkdir(parents=True)
    page.write_text('Magic Missile (CL1, 1 SP, 3d4+3, never resisted) is the best.\n')
    rows = playbooks.disagreements(tmp_path)
    assert len(rows) == 1, rows
    assert 'Magic Missile has no damage bonus' in rows[0]
    assert '$Dd4' in rows[0] and '3d4+3' in rows[0]


def test_the_right_dice_and_mana_are_not_caught(tmp_path):
    page = tmp_path / 'minimax' / 'MAGE.md'
    page.parent.mkdir(parents=True)
    page.write_text('Magic Missile (CL1, 1 SP, 3d4, never resisted) is the best.\n'
                    'Phase Door (CL2, 2 SP, ten squares of escape).\n')
    assert playbooks.disagreements(tmp_path) == []


def test_a_wrong_mana_cost_is_caught(tmp_path):
    page = tmp_path / 'minimax' / 'MAGE.md'
    page.parent.mkdir(parents=True)
    page.write_text('Magic Missile costs 3 SP, which is why it is never worth it.\n')
    rows = playbooks.disagreements(tmp_path)
    assert any('1 mana' in row and 'says 3' in row for row in rows), rows


def test_a_table_row_and_a_mana_pool_are_not_read_as_a_spell_cost(tmp_path):
    """`| Stinking Cloud | 3 | 2 | 27% |` is columns, and `had 4 spell points`
    is a pool: neither is a claim about what a spell costs."""
    page = tmp_path / 'minimax' / 'DRUID.md'
    page.parent.mkdir(parents=True)
    page.write_text('| Spell | CL | SP | Fail | Worth |\n'
                    '| Stinking Cloud | 3 | 2 | 27% | Your gun |\n\n'
                    'I studied Stinking Cloud and had 4 spell points at depth 2.\n')
    assert playbooks.disagreements(tmp_path) == []


def test_the_repositorys_own_family_pages_agree_with_the_game():
    assert playbooks.disagreements() == []
