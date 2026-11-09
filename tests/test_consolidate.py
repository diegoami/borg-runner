"""The consolidation's checks. The writing is a model's job; these are not."""
import json

from borg_runner import consolidate, run as run_module


def a_run_with_a_notebook(tmp_path, name, asks=10, notes='- a note (ask 2)\n'):
    (tmp_path / 'runs' / name).mkdir(parents=True, exist_ok=True)
    (tmp_path / 'runs' / name / 'record.json').write_text(
        json.dumps({'run': name, 'asks': asks, 'asks_made': asks}))
    (tmp_path / 'knowledge').mkdir(exist_ok=True)
    (tmp_path / 'knowledge' / f'{name}.md').write_text(notes)


def test_only_a_runs_notebook_counts_as_evidence(tmp_path, monkeypatch):
    """MANUAL-GAPS.md was counted as a run, so a consolidation could have
    cited its own output as evidence."""
    monkeypatch.setattr(consolidate.pins, 'ROOT', tmp_path)
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    a_run_with_a_notebook(tmp_path, 'one')
    (tmp_path / 'knowledge' / 'MANUAL-GAPS.md').write_text('# not a run\n')
    (tmp_path / 'knowledge' / 'LEARNED.md').write_text('# nor this\n')
    assert [p.name for p in consolidate.notebooks()] == ['one.md']
    assert sorted(consolidate.recorded_runs()) == ['one']


def written(tmp_path, body):
    path = tmp_path / 'LEARNED.md'
    path.write_text(body)
    return path


def test_an_item_filed_against_nothing_is_not_knowledge(tmp_path, monkeypatch):
    monkeypatch.setattr(consolidate.pins, 'ROOT', tmp_path)
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    a_run_with_a_notebook(tmp_path, 'one')
    path = written(tmp_path, '- [x] a claim\n  status: hypothesis\n'
                             '  evidence: one#2\n')
    problems = consolidate.check(path)
    assert any('no anchor' in problem for problem in problems)


def test_evidence_must_name_a_real_run_and_a_real_ask(tmp_path, monkeypatch):
    monkeypatch.setattr(consolidate.pins, 'ROOT', tmp_path)
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    a_run_with_a_notebook(tmp_path, 'one', asks=10)
    path = written(tmp_path, '- [x] a claim\n  anchor: new:thing\n'
                             '  status: hypothesis\n  evidence: two#2, one#999\n')
    problems = consolidate.check(path)
    assert any('two' in p and 'not a run' in p for p in problems)
    assert any('one#999' in p for p in problems)


def test_confirmed_needs_two_runs(tmp_path, monkeypatch):
    """One run noticing something is not a fact."""
    monkeypatch.setattr(consolidate.pins, 'ROOT', tmp_path)
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    a_run_with_a_notebook(tmp_path, 'one')
    a_run_with_a_notebook(tmp_path, 'two')
    one = written(tmp_path, '- [x] a claim\n  anchor: new:thing\n'
                            '  status: confirmed\n  evidence: one#2\n')
    assert any('confirmed on one run only' in p for p in consolidate.check(one))
    both = written(tmp_path, '- [x] a claim\n  anchor: new:thing\n'
                             '  status: confirmed\n  evidence: one#2, two#3\n')
    assert consolidate.check(both) == []


def test_the_real_document_passes_its_own_checks():
    assert consolidate.check() == []
