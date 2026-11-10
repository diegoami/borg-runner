"""The page. It must open from a file:// URL with nothing else on the machine."""
import json
from pathlib import Path

from borg_runner import report, run as run_module

TOMBSTONE = (Path(__file__).parent / 'tombstone.txt').read_text()


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


# What would make the page fetch something. A bare "http" is not on the list
# on purpose: Angband's own splash screen prints rephial.org and angband.live,
# so those strings arrive as *game output* inside the replay's data and are no
# more a request than they are on the terminal.
# What would make the page *load* something. An <a href> is a navigation, not
# a fetch: the page renders fully offline whether or not the viewer clicks it,
# so an external href is checked separately below rather than banned here.
FETCHES = ('src=', '<link', '<img', '@import', 'url(',
           '<iframe', 'fetch(', 'XMLHttpRequest')
# The only places a link may point outside the page.
OURS = ('https://diegoami.github.io/borg-runner',
        'https://github.com/diegoami/borg-runner')


def test_the_page_fetches_nothing(tmp_path):
    """Self-contained means no network, not no script: the replay needs one."""
    page = report.render(report.read(a_run(tmp_path)))
    for forbidden in FETCHES:
        assert forbidden not in page, forbidden
    assert page.count('<script>') == 1, 'one inline script, and no other'


def test_the_only_links_out_are_to_this_project(tmp_path):
    """Navigation is allowed; an unexpected destination is not."""
    import re
    page = report.render(report.read(a_run(tmp_path)))
    for href in re.findall(r'href="([^"]+)"', page):
        if href.startswith('http'):
            assert href.startswith(OURS), href


def test_a_url_the_game_printed_is_data_and_not_a_request(tmp_path):
    """The real splash screen prints two URLs; they must stay inert."""
    run = a_run(tmp_path)
    (run / run_module.ASK / 'screen-1.txt').write_text(
        'Website: http://rephial.org/\nForums: https://angband.live/forums/\n')
    page = report.render(report.read(run))
    assert 'rephial.org' in page, 'the screen is shown as the game drew it'
    for forbidden in FETCHES:
        assert forbidden not in page, forbidden


def test_the_replay_has_a_frame_per_ask_with_what_it_faced_and_did(tmp_path):
    data = report.read(a_run(tmp_path))
    shown = report.frames(data)
    assert [f['ask'] for f in shown] == [1, 2]
    assert shown[1]['keys'] == '2222'
    assert 'line one' in shown[1]['screen']
    assert shown[1]['notes'], 'a note made at that ask belongs to that frame'


def test_the_screens_cannot_break_out_of_the_script(tmp_path):
    """A screen is the game's characters and a reason is a model's words."""
    run = a_run(tmp_path)
    (run / run_module.ASK / 'screen-1.txt').write_text('</script><b>no</b>\n')
    page = report.render(report.read(run))
    assert '</script><b>' not in page
    assert page.count('</script>') == 1


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


def test_an_artifact_page_leaves_the_skeleton_to_its_host(tmp_path):
    """A host that wraps the page must not be given a second <html>."""
    data = report.read(a_run(tmp_path))
    page = report.render(data, standalone=False)
    for forbidden in ('<!doctype', '<html', '<head', '<body'):
        assert forbidden not in page.lower(), forbidden
    assert page.lstrip().startswith('<title>'), 'the title must still be first'
    assert '<main>' in page and page.rstrip().endswith('</main>')


def test_the_standalone_page_is_a_whole_document(tmp_path):
    page = report.render(report.read(a_run(tmp_path)))
    assert page.startswith('<!doctype html>')
    assert page.rstrip().endswith('</html>')


def test_both_dark_blocks_exist_so_the_theme_toggle_wins_either_way(tmp_path):
    page = report.render(report.read(a_run(tmp_path)))
    assert ':root:not([data-theme="light"])' in page
    assert ':root[data-theme="dark"]' in page
    assert 'color-scheme:dark' in page


def test_the_replay_keeps_the_games_last_word(tmp_path):
    """A death run's tombstone is an *unanswered* ask.

    The first version built frames from the answered decisions only, so a
    replay stopped one frame before the death it was recorded to show.
    """
    run = a_run(tmp_path)
    (run / run_module.ASK / 'question-3.txt').write_text(
        'ask 3\nturn 1348\ndepth 1\nmax_depth 1\ncursor 0 0\n')
    (run / run_module.ASK / 'screen-3.txt').write_text(TOMBSTONE)
    run_module.write_record(run, outcome='stopped')
    shown = report.frames(report.read(run))
    assert [f['ask'] for f in shown] == [1, 2, 3]
    assert shown[-1]['turn'] == 1348
    assert shown[-1]['keys'] == '', 'the last ask was never answered'
    assert 'RIP' in shown[-1]['screen']
    assert 'dead' in shown[-1]['reason']


def test_the_record_reaches_the_turn_of_the_last_question(tmp_path):
    run = a_run(tmp_path)
    (run / run_module.ASK / 'question-3.txt').write_text(
        'ask 3\nturn 1348\ndepth 1\nmax_depth 1\ncursor 0 0\n')
    (run / run_module.ASK / 'screen-3.txt').write_text(TOMBSTONE)
    record = run_module.write_record(run, outcome='stopped')
    assert record['final_turn'] == 1348, 'not the last answered ask'
    assert record['asks_made'] == 3 and record['asks'] == 2
