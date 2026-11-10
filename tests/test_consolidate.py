"""The consolidation's checks: can every claim on the page be traced to a run?

The writing is a model's job; these are not. Until 2026-11-10 the same checks
ran over `knowledge/LEARNED.md`, an item store with ids, statuses and
evidence. The page now carries the claims and the citations, so the checks
read the page.
"""
import json

import pytest

from borg_runner import consolidate, run as run_module


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(consolidate.pins, 'ROOT', tmp_path)
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    monkeypatch.setattr(consolidate, 'VOLUME_TWO', tmp_path / 'two.md')
    (tmp_path / 'two.md').write_text('# volume 2\n')
    return tmp_path


def a_run_with_a_notebook(tmp_path, name, asks=10, notes='- a note (ask 2)\n'):
    (tmp_path / 'runs' / name).mkdir(parents=True, exist_ok=True)
    (tmp_path / 'runs' / name / 'record.json').write_text(
        json.dumps({'run': name, 'asks': asks, 'asks_made': asks}))
    (tmp_path / 'knowledge').mkdir(exist_ok=True)
    (tmp_path / 'knowledge' / f'{name}.md').write_text(notes)


def a_page(tmp_path, body):
    path = tmp_path / 'PAGE.md'
    path.write_text(body)
    return path


def test_only_a_runs_notebook_counts_as_evidence(repo):
    """MANUAL-GAPS.md was counted as a run, so a consolidation could have
    cited its own output as evidence."""
    a_run_with_a_notebook(repo, 'one')
    (repo / 'knowledge' / 'MANUAL-GAPS.md').write_text('# not a run\n')
    assert [p.name for p in consolidate.notebooks()] == ['one.md']
    assert sorted(consolidate.recorded_runs()) == ['one']


def test_a_claim_about_play_that_names_no_run_is_a_superstition(repo):
    a_run_with_a_notebook(repo, 'one')
    page = a_page(repo, '- **A space clears a -more-** (OBSERVED), so send one.\n')
    assert any('names no run' in problem for problem in consolidate.check(page))


def test_a_citation_must_name_a_real_run_and_a_real_ask(repo):
    a_run_with_a_notebook(repo, 'one', asks=10)
    page = a_page(repo, '- **A claim** (two#2, one#999).\n')
    problems = consolidate.check(page)
    assert any('two' in p and 'not a run' in p for p in problems)
    assert any('one#999' in p for p in problems)


def test_a_count_of_runs_must_name_that_many_runs(repo):
    """One run noticing something twice is not two runs."""
    a_run_with_a_notebook(repo, 'one')
    a_run_with_a_notebook(repo, 'two')
    page = a_page(repo, '- **A claim** (3 runs: one#2, one#3, two#4).\n')
    assert any('claims 3 runs and names 2' in p for p in consolidate.check(page))
    enough = a_page(repo, '- **A claim** (2 runs: one#2, two#4).\n')
    assert consolidate.check(enough) == []


def test_a_claim_is_read_with_the_lines_it_wraps_onto(repo):
    """The page wraps its bullets, and the citation often sits a line below."""
    a_run_with_a_notebook(repo, 'one')
    page = a_page(repo, '- **A claim** that takes a while to state and so\n'
                        '  carries its evidence on the next line (one#2).\n')
    assert consolidate.check(page) == []


def test_the_page_says_which_notebooks_have_not_been_looked_at(repo):
    a_run_with_a_notebook(repo, 'one')
    a_run_with_a_notebook(repo, 'two')
    page = a_page(repo, '- **A claim** (one#2).\n')
    assert consolidate.uncited(page) == ['two']


def test_the_real_page_passes_its_own_checks():
    assert consolidate.check() == []


def test_the_real_page_cites_runs_that_exist():
    cited = {reference['run'] for claim in consolidate.claims()
             for reference in claim['cited']}
    assert cited, 'the page should rest on runs somewhere'
    assert cited <= set(consolidate.recorded_runs())
