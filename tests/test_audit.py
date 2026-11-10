"""The audit: did a finished run leave what a finished run should leave?

Three of the first eleven runs left something out - a report written after
`archive`, a record with no model, a playbook rewritten over somebody else's -
and each was found by reading the directory days later. These tests are so
that reading it is a command instead of a habit.
"""
import hashlib
import json

from borg_runner import audit, run as run_module


def a_finished_run(tmp_path, name='good', **record):
    kept = tmp_path / 'records' / name
    kept.mkdir(parents=True, exist_ok=True)
    keys = 'abc \n'
    body = {'run': name, 'asks': 12, 'character': 'Half-Troll Warrior',
            'outcome': 'ended', 'playbook': 'fam',
            'keys_sha256': hashlib.sha256(keys.encode()).hexdigest(),
            'cost': {'model': 'anthropic/claude-sonnet-5-5',
                     'played_by': 'session'}}
    body.update(record)
    (kept / 'record.json').write_text(json.dumps(body))
    (kept / 'input.txt').write_text(keys)
    for name_ in ('decisions.jsonl', 'notebook.md', 'REPORT.md',
                  'report.html', 'started.json'):
        (kept / name_).write_text('x\n')
    return kept


def misses(name, tmp_path):
    return [row['what'] for row in audit.audit(name, tmp_path / 'records')
            if not row['ok'] and not row['warn']]


def test_a_complete_run_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    a_finished_run(tmp_path)
    assert misses('good', tmp_path) == []


def test_a_run_that_wrote_no_report_is_caught(tmp_path, monkeypatch):
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    kept = a_finished_run(tmp_path)
    (kept / 'REPORT.md').unlink()
    assert any('REPORT.md' in what for what in misses('good', tmp_path))


def test_a_bare_model_name_is_caught(tmp_path, monkeypatch):
    """Two runs of one family months apart are not the same experiment."""
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    a_finished_run(tmp_path, cost={'model': 'sonnet', 'played_by': 'session'})
    assert any('provider/version' in what for what in misses('good', tmp_path))


def test_a_run_still_playing_is_caught(tmp_path, monkeypatch):
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    a_finished_run(tmp_path, outcome='playing')
    assert any('outcome is settled' in what for what in misses('good', tmp_path))


def test_keys_that_do_not_match_their_hash_are_caught(tmp_path, monkeypatch):
    """The keys plus the seed are the recording; a stale hash hides an edit."""
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    kept = a_finished_run(tmp_path)
    (kept / 'input.txt').write_text('something else\n')
    assert any('match the hash' in what for what in misses('good', tmp_path))


def test_a_death_must_name_its_cause(tmp_path, monkeypatch):
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    a_finished_run(tmp_path, died=True, outcome='died')
    assert any('names its cause' in what for what in misses('good', tmp_path))


def test_a_converted_session_is_audited_for_what_it_is(tmp_path, monkeypatch):
    """A person's session recorded elsewhere has no seed, keys or decisions."""
    monkeypatch.setattr(run_module, 'KNOWLEDGE', tmp_path / 'knowledge')
    monkeypatch.setattr(run_module, 'RECORDS', tmp_path / 'records')
    kept = a_finished_run(tmp_path, name='person')
    (kept / 'source.json').write_text('{"what": "a borg-rs recording"}')
    for gone in ('input.txt', 'decisions.jsonl', 'notebook.md', 'started.json'):
        (kept / gone).unlink()
    assert misses('person', tmp_path) == []


def test_every_archived_run_of_this_repository_passes():
    """The real thing, which is the point of having it."""
    for name in audit.archived():
        assert audit.failures(name) == [], name
