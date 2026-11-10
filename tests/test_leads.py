"""The leads a player wrote, and the two things picked out of them.

The parser reads free prose, so it is tested against prose: the names the
players gave the leads section, the names they gave the test, and the shapes
their asks and turns are written in.
"""
from borg_runner import leads


def a_writeup(body):
    return f'# a run\n\n## What happened\n\nit played.\n\n{body}\n'


def test_the_leads_section_is_found_by_its_name():
    """The players wrote the heading in their own words."""
    for heading in ('## 5. Leads',
                    '## Leads, with what would settle each',
                    '## Manual gaps and leads',
                    '## What I would change'):
        text = a_writeup(f'{heading}\n\n- one lead\n')
        assert leads.section(text).strip() == '- one lead', heading


def test_the_leads_section_ends_at_the_next_heading():
    text = a_writeup('## Leads\n\n- one lead\n\n## End state\n\nalive.\n')
    assert 'End state' not in leads.section(text)
    assert 'alive' not in leads.section(text)


def test_a_run_that_wrote_no_leads_has_none():
    text = a_writeup('## What happened\n\nit died in the town.\n')
    assert leads.parse(text) == []


def test_the_decisions_to_take_back_are_not_the_leads():
    """They are what went wrong, not what is open."""
    text = a_writeup('## The decisions I would take back\n\n1. wasted an ask\n')
    assert leads.parse(text) == []


def test_each_list_item_is_a_lead():
    text = a_writeup('## Leads\n\n1. first\n2. second\n- third\n')
    assert [lead['claim'] for lead in leads.parse(text)] == [
        'first', 'second', 'third']


def test_a_lead_that_wraps_is_one_lead():
    text = a_writeup('## Leads\n\n1. **A question that is long\n'
                     '   and wraps over two lines.**\n')
    found = leads.parse(text)
    assert len(found) == 1
    assert found[0]['claim'] == '**A question that is long and wraps over two lines.**'


def test_the_claim_is_the_players_own_emphasis():
    text = a_writeup('## Leads\n\n- **Is the staircase findable?** The level is big.\n')
    assert leads.parse(text)[0]['claim'] == '**Is the staircase findable?**'


def test_the_claim_is_the_first_clause_when_there_is_no_emphasis():
    text = a_writeup('## Leads\n\n- A claim that ends here. And the evidence.\n')
    lead = leads.parse(text)[0]
    assert lead['claim'] == 'A claim that ends here.'
    assert lead['evidence'] == 'And the evidence.'


def test_the_test_is_picked_out_under_the_names_the_players_gave_it():
    """Six names, one thing: what would settle it."""
    for name in ('Test:', 'What would settle it:', 'To settle it:',
                 'To confirm empirically:', 'test by'):
        text = a_writeup(f'## Leads\n\n- A claim. {name} a run that measures it.\n')
        assert leads.parse(text)[0]['test'] == name + ' a run that measures it.', name


def test_a_test_that_is_itself_a_clause_is_the_clause():
    text = a_writeup('## Leads\n\n- A claim. Test with more seeds.\n')
    assert leads.parse(text)[0]['test'] == 'Test with more seeds.'


def test_a_test_that_opens_its_clause_runs_to_the_end_of_the_sentence():
    text = a_writeup('## Leads\n\n- A claim. Test: do it at turn 800; compare the '
                     'asks. Not shown yet: whether it was cheaper.\n')
    lead = leads.parse(text)[0]
    assert lead['test'] == ('Test: do it at turn 800; compare the asks.')
    assert lead['evidence'] == 'Not shown yet: whether it was cheaper.'


def test_a_test_that_names_itself_inside_a_clause_is_the_whole_clause():
    """`would settle it` is the end of a sentence, not a test by itself."""
    text = a_writeup('## Leads\n\n- A claim. A run that scans every map, and '
                     'reports where it was, would settle it.\n')
    assert leads.parse(text)[0]['test'] == (
        'A run that scans every map, and reports where it was, would settle it.')


def test_a_lead_that_names_no_test_has_none():
    text = a_writeup('## Leads\n\n- A claim with no test in it.\n')
    assert leads.parse(text)[0]['test'] is None


def test_the_asks_a_lead_names_are_the_ranges_it_wrote():
    text = a_writeup('## Leads\n\n- A claim (asks 67-70) and (ask 76).\n')
    assert leads.parse(text)[0]['asks'] == [(67, 70), (76, 76)]


def test_a_thousand_separator_is_one_number():
    """`turn 1,701` is one turn and not two."""
    text = a_writeup('## Leads\n\n- A claim at turn 1,701.\n')
    assert leads.parse(text)[0]['turns'] == [1701]


def test_turns_written_as_a_list_are_all_of_them():
    text = a_writeup('## Leads\n\n- A claim, at turns 690, 850, and 1360.\n')
    assert leads.parse(text)[0]['turns'] == [690, 850, 1360]


def test_the_ask_is_the_anchor_and_resolves_to_its_turn():
    """An ask is a place in this run; the record says what turn it was."""
    lead = {'asks': [(67, 70)], 'turns': []}
    place = leads.where(lead, {67: 2023, 70: 2033})
    assert place['asks'] == [67, 68, 69, 70]
    assert place['turns'] == [2023, 2033]


def test_a_turn_in_prose_is_shown_only_when_there_is_no_ask():
    """`do it at turn ~800` is where the test should run, not where the
    evidence is."""
    lead = {'asks': [], 'turns': [800]}
    assert leads.where(lead, {})['turns'] == [800]
    lead = {'asks': [(43, 43)], 'turns': [800]}
    assert leads.where(lead, {43: 1234})['turns'] == [1234]


def test_an_ask_the_run_never_made_resolves_to_nothing():
    lead = {'asks': [(999, 999)], 'turns': []}
    place = leads.where(lead, {1: 10})
    assert place['asks'] == [999]
    assert place['turns'] == []


def test_the_players_words_are_not_changed():
    """The page shows what was written, not a tidied version of it."""
    text = a_writeup('## Leads\n\n- **Claim.** Evidence: it was. Test: try it.\n')
    lead = leads.parse(text)[0]
    assert lead['claim'] == '**Claim.**'
    assert lead['evidence'] == 'Evidence: it was.'
    assert lead['test'] == 'Test: try it.'
