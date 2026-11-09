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
    assert '[one](records/one/)' in table
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
    assert page.count('<option') == 3, 'one per model, plus all'


def test_a_replay_link_is_used_when_the_record_has_one(tmp_path):
    a_record(tmp_path, 'one', replay_url='https://claude.ai/artifact/abc')
    page = overview.page(overview.rows(tmp_path))
    assert 'https://claude.ai/artifact/abc' in page


def test_the_real_records_still_read(tmp_path):
    """Against the repository's own records/, whatever is in it."""
    found = overview.rows()
    for row in found:
        assert row['run'] and row['record'].startswith('records/')
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
