"""The page. It must open from a file:// URL with nothing else on the machine."""
import json

from borg_runner import report, run as run_module


def a_run(tmp_path):
    run = tmp_path / 'r'
    (run / run_module.ASK).mkdir(parents=True)
    (run / 'started.json').write_text(json.dumps({
        'seed': 7, 'character': 'r', 'savefile': str(tmp_path / 'nosave'),
        'build': {'game': 'angband/angband', 'commit': 'e' * 40,
                  'patch_sha256': 'a' * 64}}))
    for number in (1, 2):
        (run / run_module.ASK / f'question-{number}.txt').write_text(
            f'ask {number}\nturn {number}\ndepth {number - 1}\nmax_depth 1\ncursor 1 2\n')
        (run / run_module.ASK / f'screen-{number}.txt').write_text(
            f'line one <b>{number}</b>\n@ here\n')
    run_module.answer(run, 1, ' ', reason='past the splash')
    run_module.answer(run, 2, '2222', reason='four steps south')
    run_module.remember(run, '`>` only works on a down staircase', ask=2)
    run_module.write_record(run, outcome='stopped')
    return run


def test_the_page_asks_nothing_of_the_network(tmp_path):
    page = report.render(report.read(a_run(tmp_path)))
    for forbidden in ('src=', 'href=', 'http://', 'https://', '<script'):
        assert forbidden not in page, forbidden


def test_the_page_shows_the_keys_the_reason_and_the_screen(tmp_path):
    page = report.render(report.read(a_run(tmp_path)))
    assert "'2222'" in page
    assert 'four steps south' in page
    assert 'line one' in page
    assert '&lt;b&gt;' in page, 'the screen must be escaped, not rendered'


def test_the_page_shows_the_notebook_and_which_ask_taught_it(tmp_path):
    """The point of the run is what it kept."""
    run = a_run(tmp_path)
    data = report.read(run)
    assert data['notes'][2], 'the note is attached to the ask that taught it'
    page = report.render(data)
    assert 'down staircase' in page
    assert 'What it kept' in page


def test_the_facts_come_only_from_the_files(tmp_path):
    data = report.read(a_run(tmp_path))
    named = dict(report.facts(data))
    assert named['seed'] == 7
    assert named['deepest depth'] == 1
    assert named['keypresses'] == 5
    assert 'angband/angband' in named['game']


def test_a_run_with_nothing_in_it_still_renders(tmp_path):
    run = tmp_path / 'empty'
    (run / run_module.ASK).mkdir(parents=True)
    (run / 'started.json').write_text('{"seed": 1}')
    page = report.render(report.read(run))
    assert 'no decisions were taken' in page


def test_it_writes_the_page_beside_the_run(tmp_path):
    run = a_run(tmp_path)
    page = report.write(run)
    assert page == run / 'report.html'
    assert page.read_text().startswith('<!doctype html>')
