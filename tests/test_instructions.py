"""`manuals/INSTRUCTIONS.md` is checked against the pinned game.

Every factual line of the page names its source. This test makes the name
true: it parses the page's claims (`borg_runner.instructions`), looks each one
up in `vendor/angband` and `vendor/strategy-manual` at the commits in
`pins.json`, and fails with the page's line number, the claimed value and the
real one. It also fails when a citation names a file, field, option, rule or
section that does not exist at the pin, which is how a claim rots when the pin
moves. The run prints how many claims it found and checked
(`pytest -s tests/test_instructions.py`).

What it checks, by kind: race and class hit dice, race experience, object
`cost:`/`level:`/`alloc:`, whether a price is a `cost:` line at all (gear, torches
and wands are priced by power or charges and are never compared with `cost:` as a
shop price), store stock and shop digits, class kits, blows, armour allowance,
first-spell levels, spell levels, mana and failure, class flags, monster
depth/hit points/speed/blows/worst melee, trap damage, effect numbers (Phase
Door, Cure Light Wounds, Magic Mapping, the flask), a handful of source
constants (recall and Deep Descent delays, `start-gold`, torch fuel, option
defaults, the level-feeling inversion), rule ids and section numbers of the
strategy chapters, quotations, and document section titles.

What it does NOT check, and so what a pass does not mean:

* **Prose.** Advice, POLICY rules, "why" columns and every strategy sentence are
  not tested. A POLICY line is only checked for the numbers it quotes from
  chapter 15 and for the rule id existing; whether the rule is good, or is what
  the chapter means, is not.
* **OBSERVED evidence.** Run names, ask numbers and what a run did (`sonnet-2-again`
  asks 156-230, "one run paid 65") are not in the game data.
* **Keys and the screen.** What `lxg`, `l>g`, `h`, `v`, `R` and the rest do, and what
  the 80x24 screen shows, comes from the build's own patch and the docs; no
  command or screen claim is checked, only the docs' section titles.
* **Dice and effects beyond the listed ones.** Spell damage (Magic Missile 3d4),
  Bless's +5 AC, the Necromancer's 25% unlight penalty, shape-change effects,
  monster spells, what a monster is "up to" other than melee.
* **Derived or dynamic numbers.** Starting gold per class, hit points at CL1 with
  CON, experience per kill, blows per turn, anything that needs the running game.
* **Ammunition and shop prices of gear.** They come from `object_value_real`
  over computed power and store markup, not from a data file. The page labels
  the one such number (arrows) UNTESTED and the test only checks the label is
  still there.
* **Shapes the grammars do not know.** A claim written in a form no extractor
  matches is not found, so not checked. Each extractor has a minimum count and the
  whole run has a floor, which catches a rewrite that stops grammars matching,
  but not one number quietly rephrased.
* **That the pin is right.** The page is checked against `pins.json`; if the
  pin is wrong for the build in use, so is this.
"""
import os

import pytest

from borg_runner import gamedata, instructions

# Floors, set just below what the page yields today. Raising the page's claims
# raises these; lowering them means checks were lost, and should be a decision.
TOTAL_FLOOR = 480
KIND_FLOORS = {
    'object cost': 12, 'table cost': 15, 'table level': 15, 'table alloc': 15,
    'race hitdie': 10, 'class hitdie': 15, 'race exp': 3,
    'class kit': 30, 'spell level': 20, 'spell mana': 8,
    'monster hp': 11, 'monster depth': 12, 'monster speed': 4, 'monster blow': 7,
    'store always': 20, 'store normal': 8, 'shop digit': 16, 'cost 0': 30,
    'citation': 60, 'quotation': 4, 'manual says': 10, 'price semantics': 25,
}


@pytest.fixture(scope='module')
def clones():
    problems = gamedata.clones_at_their_pins()
    if any('not cloned' in p for p in problems):
        if os.environ.get('BORG_RUNNER_REQUIRE_VENDOR'):
            # A skip reads as a pass. Where this test is the only thing
            # standing between the page and silent drift - in CI - a missing
            # clone has to fail instead.
            raise AssertionError(
                'the pinned clones are missing and BORG_RUNNER_REQUIRE_VENDOR '
                'is set: run scripts/setup.sh')
        pytest.skip('run scripts/setup.sh first')
    assert not problems, '; '.join(problems) + ' - run scripts/setup.sh'


@pytest.fixture(scope='module')
def page():
    return instructions.INSTRUCTIONS.read_text()


@pytest.fixture(scope='module')
def report(clones, page):
    return instructions.check(page)


def test_every_claim_on_the_page_matches_the_pinned_game(report):
    print('\n' + report.summary())
    failures = report.failures()
    assert not failures, f'{len(failures)} problems:\n' + '\n'.join(failures)


def test_the_check_covers_what_it_says_it_covers(report):
    """A pass over two claims would read as a guarantee: keep a floor."""
    assert len(report.checked) >= TOTAL_FLOOR, report.summary()
    counts = report.by_kind()
    short = {kind: (counts.get(kind, 0), floor) for kind, floor in KIND_FLOORS.items()
             if counts.get(kind, 0) < floor}
    assert not short, f'claims found per kind fell below the floor (found, floor): {short}'
    assert report.unverifiable, 'the labelled unverifiable numbers disappeared'


def test_every_extractor_found_something(report):
    """A grammar that matches nothing is a check that silently stopped."""
    empty = [name for name, found in report.extractors.items() if not found]
    assert not empty, f'extractors that found no claims: {empty}'
    assert len(report.extractors) >= 17


# -- the check itself must be able to fail ----------------------------------
# Each row doctors one thing on the page and says what the failure must name.

DOCTORED = [
    ('Hobbit 7;', 'Hobbit 8;', ['Hobbit hit die', "8", "7"]),
    ('Flask of oil 3, Ration 3', 'Flask of oil 4, Ration 3', ['Flask of oil cost:', '4', '3']),
    ('Cure Serious Wounds 70,', 'Cure Serious Wounds 75,', ['Cure Serious Wounds cost:', '75', '70']),
    ('Human 100, Half-Troll 120', 'Human 100, Half-Troll 125', ['Half-Troll exp', '125', '120']),
    ('| Scroll of Phase Door | 15 | 1 | 1 |', '| Scroll of Phase Door | 16 | 1 | 1 |',
     ['Phase Door cost:', '16', '15']),
    ('| Scroll of Deep Descent | 250 | 10 | 1 |', '| Scroll of Deep Descent | 250 | 10 | 10 |',
     ['Deep Descent alloc', '10', '1']),
    ('11 hp, never moves', '12 hp, never moves', ['floating eye hit-points', '12', '11']),
    ('large kobold (DL5)', 'large kobold (DL6)', ['large kobold depth', '6', '5']),
    ('(up to 32 per turn)', '(up to 30 per turn)', ['Bullroarer'.lower(), '30', '32']),
    ('(DL3, +20, invisible)', '(DL3, +30, invisible)', ['smeagol speed', '30', '20']),
    ('Fire Ball CL6', 'Fire Ball CL7', ['Mage Fire Ball level', '7', '6']),
    ('**Mage** (s2): hit die 0', '**Mage** (s2): hit die 1', ['Mage hit die', '1', '0']),
    ('**Priest** (s4)', '**Priest** (s5)', ['Priest is c14 section 5', '5', '4']),
    ('Kit: Mace (blessed', 'Kit: Flail (blessed', ['Priest starts with Flail']),
    ('fear-proof only from CL30', 'fear-proof only from CL25', ['BRAVERY_25']),
    ('`trap` gives it 2d8', '`trap` gives it 3d8', ['trap door dice', '3d8', '2d8']),
    ('Alchemist: Cure Light Wounds,', 'Alchemist: Cure Light Wounds, Healing,',
     ['Alchemist always has Healing']),
    ('staves of Teleportation', 'staves of Haste', ['Magic shop sometimes has staff Haste']),
    ('(15-34 turns delay)', '(15-35 turns delay)', ['Word of Recall delay', '35', '34']),
    ('Daggers and Spears are `THROWING` too (x3 and x6', 'Daggers and Spears are `THROWING` too (x3 and x5',
     ['Spear throw multiplier', '5', '6']),
    ('1d4 x3 (throwing weight multiplier) x3 (EXPLODE) = **9 to 36',
     '1d4 x3 (throwing weight multiplier) x3 (EXPLODE) = **9 to 40', ['flask of oil damage high', '40', '36']),
    ('**1** General', '**2** General', ['General is number 2', '2', '1']),
    ('`src/ui-target.c` agrees', '`src/ui-targets.c` agrees', ['src/ui-targets.c exists']),
    ('`src/generate.c calc_mon_feeling`', '`src/generate.c calc_mon_feelings`',
     ["contains 'calc_mon_feelings'"]),
    ('`race` = `vendor/angband/lib/gamedata/p_race.txt`', '`race` = `vendor/angband/lib/gamedata/race.txt`',
     ['race.txt exists']),
    ('not by the `cost:` line', 'not by the `price:` line', ['field `price` exists']),
    ('(c15 ESC-04)', '(c15 ESC-77)', ['rule ESC-77']),
    ('(c15 TOWN-01, c4 4.11)', '(c15 TOWN-01, c4 4.99)', ['c4 has a section 4.99']),
    ('"A note on speed"', '"A note on haste"', ['A note on haste']),
    ('not as truths"', 'not truths"', ['starting policy to be measured, not truths']),
    ('`playing`, Disturb:', '`playing`, Disturbance:', ["'Disturbance'"]),
    ('`birth_no_selling` is on', '`birth_no_sellin` is on', ['birth_no_sellin']),
    ('Level 2 needs `10 x XP-mod%`', 'Level 2 needs `12 x XP-mod%`', ['player_exp', '12', '10']),
]


def line_of(page, text):
    assert page.count(text) == 1, f'{text!r} must occur once on the page, it occurs {page.count(text)} times'
    return page.count('\n', 0, page.index(text)) + 1


@pytest.mark.parametrize('old,new,fragments', DOCTORED, ids=[d[0][:40] for d in DOCTORED])
def test_a_wrong_claim_is_reported_with_its_line_and_both_values(clones, page, old, new, fragments):
    line = line_of(page, old)
    failures = instructions.check(page.replace(old, new)).failures()
    wanted = [f for f in failures if all(fragment in f for fragment in fragments)]
    assert wanted, f'doctoring {old!r} was not reported as {fragments}; failures: {failures}'
    assert any(f.startswith(f'line {line}') or f.startswith(f'line {line + 1}') for f in wanted), \
        f'expected a message for line {line}, got {wanted}'


def test_gear_priced_by_power_is_never_checked_against_cost(clones, page):
    """The page says weapons, armour, torches and ammo are priced by power;
    listing one as a `cost:` price must be an error, not a comparison."""
    failures = instructions.check(page.replace(', Blessing 15.', ', Wooden Torch 2.')).failures()
    assert any('Wooden Torch' in f and 'priced by its `cost:` line' in f for f in failures), failures
    assert not any('Wooden Torch cost:' in f for f in failures)


def test_a_rewrite_that_defeats_a_grammar_fails_instead_of_checking_nothing(clones, page):
    failures = instructions.check(page.replace('Prices. FACT', 'Costs. FACT')).failures()
    assert any(f.startswith('grammar:') and 'Prices line' in f for f in failures), failures
    failures = instructions.check(page.replace('Early dangers,', 'Dangers,')).failures()
    assert any(f.startswith('grammar:') for f in failures), failures


def test_an_unlabelled_unverifiable_number_is_reported(clones, page):
    failures = instructions.check(page.replace('believed about 1 g each: UNTESTED', 'about 1 g each')).failures()
    assert any(f.startswith('grammar:') for f in failures), failures
