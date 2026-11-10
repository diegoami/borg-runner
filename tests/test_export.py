"""The export: the one document written outward, and the line players must not cross.

What the check holds is narrow on purpose (an edition line, citations that
name real runs and real asks, the consumer named). What these tests also hold
is the boundary: no player is ever pointed at the export, because it
aggregates every run's report - including of the seed the player is on.
"""
import json

import pytest

from borg_runner import export, pins


def a_record(tmp_path, name, asks=10, depth=1, died=False, report=True):
    where = tmp_path / 'records' / name
    where.mkdir(parents=True, exist_ok=True)
    (where / 'record.json').write_text(json.dumps({
        'run': name, 'asks': asks, 'asks_made': asks, 'keypresses': asks * 4,
        'max_depth': depth, 'died': died}))
    if report:
        (where / 'REPORT.md').write_text(f'# {name}\n')
    return where


def test_the_corpus_comes_from_the_records_not_the_reports(tmp_path):
    a_record(tmp_path, 'one', asks=10, depth=2)
    a_record(tmp_path, 'two', asks=5, depth=7, died=True)
    counted = export.corpus(tmp_path / 'records')
    assert counted['runs'] == ['one', 'two'] and counted['asks'] == 15
    assert counted['deepest'] == 7 and counted['deaths'] == 1


def test_a_run_that_wrote_no_report_has_nothing_to_export(tmp_path):
    a_record(tmp_path, 'one')
    a_record(tmp_path, 'silent', report=False)
    counted = export.corpus(tmp_path / 'records')
    assert counted['reports'] == ['one'] and counted['runs'] == ['one', 'silent']


def an_edition(tmp_path, body):
    path = tmp_path / 'EXPORT_UNDER_TEST.md'
    path.write_text(body)
    return path


HEAD = '# knowledge\n\nEdition 2, 2026-11-10.\n\nFor borg-reborn-rs.\n\n'


def test_an_edition_must_be_datable(tmp_path):
    a_record(tmp_path, 'one')
    path = an_edition(tmp_path, '# knowledge\n\nFor borg-reborn-rs.\n')
    problems = export.check(path, tmp_path / 'records')
    assert any('Edition' in problem for problem in problems)


def test_an_edition_must_say_who_it_is_for(tmp_path):
    a_record(tmp_path, 'one')
    path = an_edition(tmp_path, '# knowledge\n\nEdition 1, 2026-11-10.\n')
    assert any('who it is for' in p for p in export.check(path, tmp_path / 'records'))


def test_a_citation_must_name_a_real_run_and_a_real_ask(tmp_path):
    a_record(tmp_path, 'one', asks=10)
    path = an_edition(tmp_path, HEAD + 'A claim (two-run#3) and (one#999).\n')
    problems = export.check(path, tmp_path / 'records')
    assert any('two-run' in p and 'not a run' in p for p in problems)
    assert any('one#999' in p for p in problems)


def test_a_sound_edition_has_no_problems(tmp_path):
    a_record(tmp_path, 'one', asks=10)
    path = an_edition(tmp_path, HEAD + 'A claim (one#3).\n')
    assert export.check(path, tmp_path / 'records') == []


def test_staleness_is_information_and_not_an_error(tmp_path):
    """The accumulation is periodic by design; CI must not fail for it."""
    a_record(tmp_path, 'one')
    a_record(tmp_path, 'later')
    path = an_edition(tmp_path, HEAD + 'A claim (one#3).\n')
    assert export.missing(path, tmp_path / 'records') == ['later']
    assert export.check(path, tmp_path / 'records') == []


def test_the_real_edition_is_sound_and_has_read_every_report():
    assert export.check() == []
    assert export.missing() == [], \
        'reports have arrived since the last edition; see docs/EXPORT.md'


NOT_FOR_PLAYERS = ('PLAYGAME.txt', 'CONTINUEGAME.txt', 'docs/BRIEF.md',
                   'manuals/INSTRUCTIONS.md', 'manuals/INSTRUCTIONS_2.md',
                   'agents/README.md')


@pytest.mark.parametrize('name', NOT_FOR_PLAYERS)
def test_nothing_a_player_reads_points_at_the_export(name):
    """It aggregates every report, including of the seed being played (D9)."""
    assert 'ACCUMULATED_KNOWLEDGE' not in (pins.ROOT / name).read_text()


def test_the_export_says_why_it_leaves_the_manuals_out():
    """The consumer can read the manuals itself; the export is the residue."""
    text = export.ACCUMULATED.read_text()
    assert 'What is deliberately not here' in text
    assert 'strategy manual' in text
    process = (pins.ROOT / 'docs' / 'EXPORT.md').read_text()
    assert 'Anything the manuals already say' in process


def test_the_export_says_itself_that_players_do_not_read_it():
    text = export.ACCUMULATED.read_text()
    assert 'not for' in text.lower() and 'solution key' in text
    assert 'docs/EXPORT.md' in text, 'it should point at its own process'
