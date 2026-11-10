"""The table of every run. It reads records/, which is what git keeps."""
import json

from borg_runner import overview, run as run_module


def a_record(where, name, **fields):
    (where / name).mkdir(parents=True, exist_ok=True)
    body = {'run': name, 'seed': 7, 'max_depth': 1, 'asks': 10,
            'keypresses': 40, 'final_turn': 100, 'outcome': 'stopped',
            'died': False, 'character_level': 3, 'gold': 10,
            'carried_value': 713, 'wealth': 723,
            'cost': {'tokens': 1000, 'model': 'anthropic/claude-sonnet-5-5'}}
    body.update(fields)
    (where / name / 'record.json').write_text(json.dumps(body))
    return where / name


def test_a_row_per_archived_run(tmp_path):
    a_record(tmp_path, 'one')
    a_record(tmp_path, 'two', seed=11, died=True, killed_by='a small kobold')
    found = overview.rows(tmp_path)
    assert [row['run'] for row in found] == ['one', 'two']
    assert found[1]['outcome'] == 'died: a small kobold'
    assert found[0]['wealth'] == 723


def test_the_table_links_each_run_to_what_git_holds(tmp_path):
    a_record(tmp_path, 'one')
    table = overview.markdown(overview.rows(tmp_path))
    assert '[one](one/)' in table, 'relative to records/, where the table lives'
    assert '723 (10 gold + 713 carried)' in table


def test_the_page_embeds_its_rows_and_fetches_nothing(tmp_path):
    """The rows are data in the page; the first version left them out."""
    a_record(tmp_path, 'one')
    a_record(tmp_path, 'two', cost={'tokens': 5, 'model': 'typesafe/jev-1.14'})
    page = overview.page(overview.rows(tmp_path))
    assert page.count('"run":') == 2, 'the rows must be in the page'
    assert 'var runs = [' in page, 'RUNS must be substituted, not left literal'
    for forbidden in ('src=', '<link', '<img', '@import', 'url('):
        assert forbidden not in page, forbidden


def test_every_model_in_the_data_is_in_the_filter(tmp_path):
    a_record(tmp_path, 'one')
    a_record(tmp_path, 'two', cost={'tokens': 5, 'model': 'typesafe/jev-1.14'})
    page = overview.page(overview.rows(tmp_path))
    assert 'anthropic/claude-sonnet-5-5' in page
    assert 'typesafe/jev-1.14' in page
    model_filter = page.split('<select id="model">')[1].split('</select>')[0]
    assert model_filter.count('<option') == 3, 'one per model, plus all'


def test_the_page_filters_by_alive_status_agent_and_class(tmp_path):
    """The three cuts a reader asks for, in the order they ask them."""
    a_record(tmp_path, 'one', **{'class': 'Druid'})
    a_record(tmp_path, 'two', died=True, killed_by='a small kobold',
             **{'class': 'Mage'})
    page = overview.page(overview.rows(tmp_path))
    for field, want in (('alive', 'alive'), ('agent', 'sonnet'),
                         ('klass', 'Druid')):
        cut = page.split(f'<select id="{field}">')[1].split('</select>')[0]
        assert f'value="{want}"' in cut, f'{field} must offer {want}'
    assert 'died' in page.split('<select id="alive">')[1].split('</select>')[0]
    assert 'Mage' in page.split('<select id="klass">')[1].split('</select>')[0]


def test_the_markdown_leads_with_characters_not_runs(tmp_path):
    """OVERVIEW.md is where a reader looks first; it must answer "who are the
    characters", not only "what runs exist"."""
    a_record(tmp_path, 'one')
    a_record(tmp_path, 'two')
    (tmp_path / 'two' / 'started.json').write_text(
        json.dumps({'character': 'one'}))
    text = overview.write_markdown(
        overview.rows(tmp_path), into=tmp_path / 'OVERVIEW.md').read_text()
    assert text.startswith('# The characters, and every run')
    assert '## Characters' in text
    assert '[one](characters/one.html) - 2 lives' in text
    assert '## Single-life characters' in text
    assert '## Every run' in text


def test_the_markdown_offers_the_same_three_cuts(tmp_path):
    """A markdown file cannot filter itself, so it carries the views."""
    a_record(tmp_path, 'one', **{'class': 'Druid'})
    a_record(tmp_path, 'two', died=True, killed_by='a small kobold',
             **{'class': 'Mage'})
    text = overview.write_markdown(overview.rows(tmp_path),
                                   into=tmp_path / 'OVERVIEW.md').read_text()
    assert '[Alive](#alive)' in text and '[Died](#died)' in text
    assert '[Agent sonnet](#agent-sonnet)' in text
    assert '[Class Druid](#class-druid)' in text
    assert '### Class Mage' in text


def test_a_replay_link_is_used_when_the_record_has_one(tmp_path):
    a_record(tmp_path, 'one', replay_url='https://claude.ai/artifact/abc')
    page = overview.page(overview.rows(tmp_path))
    assert 'https://claude.ai/artifact/abc' in page


def test_the_real_records_still_read(tmp_path):
    """Against the repository's own records/, whatever is in it."""
    found = overview.rows()
    for row in found:
        assert row['run'] and row['record'].endswith('/')
        if row['model']:
            assert '/' in row['model'], 'a model names its provider'


def test_the_character_is_part_of_a_row(tmp_path):
    """Race and class come from the game, because the run draws them at random
    and only the game knows what was drawn."""
    a_record(tmp_path, 'one', character='Half-Troll Warrior',
             race='Half-Troll', **{'class': 'Warrior'})
    found = overview.rows(tmp_path)
    assert found[0]['character'] == 'Half-Troll Warrior'
    assert 'character' in [label for _, label in overview.COLUMNS]
    assert 'Half-Troll Warrior' in overview.page(found)


def test_the_links_are_relative_to_where_the_table_lives(tmp_path):
    """OVERVIEW.md sits inside records/, so a records/<run>/ link resolves to
    records/records/<run>/ and 404s on GitHub."""
    run = a_record(tmp_path, 'one')
    (run / 'REPORT.md').write_text('# what happened\n')
    table = overview.markdown(overview.rows(tmp_path))
    assert '[one](one/REPORT.md)' in table
    assert 'records/one' not in table


def test_a_run_without_a_write_up_links_to_its_directory(tmp_path):
    a_record(tmp_path, 'bare')
    table = overview.markdown(overview.rows(tmp_path))
    assert '[bare](bare/)' in table


def test_the_table_links_to_the_published_replay(tmp_path):
    a_record(tmp_path, 'one', replay_url='https://claude.ai/artifact/abc')
    table = overview.markdown(overview.rows(tmp_path))
    assert '[watch](https://claude.ai/artifact/abc)' in table


def test_the_page_links_the_local_replay_not_only_the_artifact(tmp_path):
    """Every run has a local report.html; only some have a published artifact.

    The markdown table preferred the local page and the HTML page did not, so
    runs without an artifact appeared as plain text on the site.
    """
    run = a_record(tmp_path, 'one')
    (run / 'report.html').write_text('<title>x</title>')
    (run / 'REPORT.md').write_text('# what happened\n')
    found = overview.rows(tmp_path)
    assert found[0]['replay'] == 'one/report.html'
    page = overview.page(found)
    assert 'one/report.html' in page
    assert 'one/REPORT.md' in page, 'and what it wrote'


def test_a_run_with_no_replay_page_is_still_listed(tmp_path):
    a_record(tmp_path, 'bare')
    page = overview.page(overview.rows(tmp_path))
    assert 'bare' in page


def test_the_markdown_links_a_replay_that_opens(tmp_path):
    """github.com renders .html as source, so a relative link to a replay
    shows markup to anyone reading OVERVIEW.md on GitHub - which is where it
    is read."""
    run = a_record(tmp_path, 'one')
    (run / 'report.html').write_text('<title>x</title>')
    table = overview.markdown(overview.rows(tmp_path))
    assert f'[watch]({overview.SITE}/records/one/report.html)' in table


def test_the_page_keeps_its_links_relative(tmp_path):
    """The page is served from the site, so relative is right there."""
    run = a_record(tmp_path, 'one')
    (run / 'report.html').write_text('<title>x</title>')
    page = overview.page(overview.rows(tmp_path))
    assert '"one/report.html"' in page


def test_a_run_that_wrote_no_report_is_visible(tmp_path):
    """Both prompts ask for one; three of the first ten runs skipped it and
    nothing noticed, so what they found stayed out of the repository."""
    silent = a_record(tmp_path, 'silent')
    spoke = a_record(tmp_path, 'spoke')
    (spoke / 'REPORT.md').write_text('# what happened\n')
    found = {row['run']: row['wrote_up'] for row in overview.rows(tmp_path)}
    assert found == {'silent': 'NO', 'spoke': 'yes'}
    assert 'wrote up' in [label for _, label in overview.COLUMNS]
