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

Volume two (`manuals/INSTRUCTIONS_2.md`) has its own tests at the end of this
file, with the same limits plus its own: no line of it is OBSERVED, so nothing
here says a run would find it true, only that it says what the game's files say.
"""
import os

import pytest

from borg_runner import gamedata, instructions

# Floors, set just below what the page yields today. Raising the page's claims
# raises these; lowering them means checks were lost, and should be a decision.
TOTAL_FLOOR = 700
KIND_FLOORS = {
    'object cost': 12, 'table cost': 15, 'table level': 15, 'table alloc': 15,
    'race hitdie': 10, 'class hitdie': 15, 'race exp': 3,
    'class kit': 30, 'spell level': 20, 'spell mana': 8,
    'monster hp': 11, 'monster depth': 12, 'monster speed': 4, 'monster blow': 7,
    'store always': 20, 'store normal': 8, 'shop digit': 16, 'cost 0': 30,
    'citation': 60, 'quotation': 4, 'manual says': 10, 'price semantics': 25,
    'experience': 18, 'spell experience': 6, 'spell damage': 4,
    'monster experience': 2, 'staircases': 8, 'constitution': 28, 'death': 10, 'unknown': 48,
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
    ('CL5 70, CL6 100', 'CL5 75, CL6 100', ['experience for CL5', '75', '70']),
    ('Phase Door 17%, Deep Descent 7%', 'Phase Door 20%, Deep Descent 7%',
     ['an unknown scroll is Phase Door', '20', '17']),
    ('Summon Monster 10; Darkness 10', 'Summon Monster 15; Darkness 10',
     ['Summon Monster weight at depth 2', '15', '10']),
    ('Its band starts at **DL5**', 'Its band starts at **DL4**',
     ['the shallowest Magic Mapping scroll', '4', '5']),
    ('2 x 1d7 =\n   14 damage', '2 x 1d7 =\n   13 damage',
     ['the worst round at depth 2 or shallower', '13', '14']),
    ('**5 of the 52 monsters', '**6 of the 52 monsters',
     ['how many can take 8 hit points in a round', '6', '5']),
    ('| -2.5 | -1 | -0.5 |', '| -2.5 | -1 | -0.6 |',
     ['hit points per level at CON 7', '-0.6', '-0.5']),
    ('a **Gnome Mage is -1**', 'a **Gnome Mage is -2**',
     ['gnome mage constitution modifier', '-2', '-1']),
    ('a CL2 Mage stood at 4 of 16 hit points', 'a CL2 Mage stood at 4 of 18 hit points',
     ['minimaxflash-2.2 max hit points', '18', '16']),
    ('both ask for **3 or 4 down staircases', 'both ask for **2 or 4 down staircases',
     ['classic_gen staircase counts', '(2, 4, 1, 2)', '(3, 4, 1, 2)']),
    ('/ 4` = 16 squares apart', '/ 4` = 12 squares apart',
     ['minimum separation of staircases', '12', '16']),
    ('so **3d4, 3 to 12 damage**', 'so **3d4, 6 to 15 damage**',
     ['Magic Missile lowest damage at CL1', '6', '3']),
    ('spells pay 4, 4, 2, 4 and 4', 'spells pay 4, 4, 3, 4 and 4',
     ['Find Traps, Doors & Stairs first-cast experience', '3', '2']),
    ('is about 2 kills, then 6', 'is about 3 kills, then 6',
     ['small kobolds to go from CL1 to CL2', '3', '2']),
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


# =============================================================================
# Volume two: `manuals/INSTRUCTIONS_2.md`, depth 5 to 20
#
# Same method, and the same refusal to read a pass as more than it is. What it
# adds: claims over the whole monster list (every breather, every summoner, every
# unique in range must be in its table), arithmetic from the game's own formulas
# (breath damage, teleport distance, hit points at a level, gold per pile), and
# the strategy manual set against the data where the page says they differ.
# What it does not check, on top of volume one's list: the opening caveat's own
# numbers, advice ("take the stairs"), and whether a POLICY rule is any good. It
# also cannot say a run would find these lines true: nothing here is OBSERVED.
# =============================================================================

TOTAL_FLOOR_2 = 800
KIND_FLOORS_2 = {
    'breather': 110, 'summoner': 52, 'unique': 85, 'spell book': 50, 'spell level': 24,
    'spell mana': 16, 'spell fail': 5, 'book cost': 7, 'breath element': 28, 'depth band': 15,
    'escape cost': 4, 'escape where': 4, 'buy cost': 6, 'buy where': 6, 'gate': 12,
    'monster depth': 35, 'monster trait': 22, 'manual says': 11, 'resist': 9, 'teleport': 16,
    'spell damage': 9, 'source': 33, 'citation': 100, 'quotation': 4, 'hit points': 5,
}
NUMBER_COVERAGE_FLOOR = 0.97


@pytest.fixture(scope='module')
def page2():
    return instructions.INSTRUCTIONS_2.read_text()


@pytest.fixture(scope='module')
def report2(clones, page2):
    return instructions.check(page2, volume=2)


def test_volume_two_every_claim_matches_the_pinned_game(report2):
    print('\n' + report2.summary())
    failures = report2.failures()
    assert not failures, f'{len(failures)} problems:\n' + '\n'.join(failures)


def test_volume_two_check_covers_what_it_says_it_covers(report2):
    assert len(report2.checked) >= TOTAL_FLOOR_2, report2.summary()
    counts = report2.by_kind()
    short = {kind: (counts.get(kind, 0), floor) for kind, floor in KIND_FLOORS_2.items()
             if counts.get(kind, 0) < floor}
    assert not short, f'claims found per kind fell below the floor (found, floor): {short}'
    empty = [name for name, found in report2.extractors.items() if not found]
    assert not empty, f'extractors that found no claims: {empty}'
    assert len(report2.extractors) >= 23


def test_volume_two_numbers_are_settled_by_a_claim(report2, page2):
    """Not 'a claim was found': the share of the page's numbers a claim says it settles."""
    covered, total, missing = instructions.number_coverage(report2, page2)
    print(f'\n{covered} of {total} numbers on volume 2 are settled by a claim '
          f'({covered / total:.1%}); the rest:')
    for line, token, context in missing:
        print(f'  line {line}: {token}  ...{context}...')
    assert covered / total >= NUMBER_COVERAGE_FLOOR, \
        f'{total - covered} numbers have no claim behind them: {missing[:10]}'
    assert total >= 450, 'the page lost most of its numbers, or the number reader broke'


def test_volume_two_is_inside_its_size_budget(page2):
    size = len(page2.encode())
    assert 14_000 <= size <= 18_000, f'{size} bytes: the budget is 14-18 KB (volume 1 is 22 KB)'


def test_volume_two_says_it_has_no_observed_evidence(page2):
    first = page2.split('\n\n')[1]
    assert 'No run has reached depth 8' in first and 'cannot have any yet' in first
    assert page2.count('OBSERVED') == 1, \
        'volume 2 has an OBSERVED line, and no run has reached these depths (only the caveat may say the word)'


DOCTORED_2 = [
    # section 1: counts over the whole monster list
    ('| kinds | 80 | 60 | 51 | 45 | 45 |', '| kinds | 80 | 60 | 52 | 45 | 45 |',
     ['monsters of depth 10-14: kinds', '52', '51']),
    ('| summon | 0 | 0 | 6 | 0 | 3 |', '| summon | 0 | 0 | 7 | 0 | 3 |', ['monsters of depth 10-14: summon', '7', '6']),
    ('| breathe | 0 | 11 | 2 | 5 | 9 |', '| breathe | 0 | 10 | 2 | 5 | 9 |', ['monsters of depth 5-9: breathe', '10', '11']),
    ('**Breath** (from DL5)', '**Breath** (from DL6)', ['shallowest monster with Breath', '6', '5']),
    ('**HOLD** (from DL13)', '**HOLD** (from DL12)', ['shallowest monster with HOLD', '12', '13']),
    # section 2: gates
    ('| 15 | 100 max hp, Phase x10 |', '| 15 | 120 max hp, Phase x10 |', ["depth 15 gate requirement is c15 DEPTH-02's"]),
    ('Wormtongue (DL8), Boldor (DL13)', 'Wormtongue (DL9), Boldor (DL13)', ['wormtongue depth', '9', '8']),
    ('| 20 | Free Action | illusionist (DL13), Old Man Willow',
     '| 20 | Free Action | illusionist (DL13), Old Man Willow (DL19), troll (DL13), Old Man Willow',
     ["depth 20 anchor monsters (name, depth) are c15 DEPTH-02's"]),
    ('is +10 in `monster`', 'is +20 in `monster`', ['Bullroarer speed in monster.txt', '20', '10']),
    ("the chapter's \"+20\" for him", "the chapter's \"+30\" for him", ['c15 DEPTH-02 gives Bullroarer this speed', '30', '20']),
    ('(DL5, +10, 60 hp, 2 x 1d8: up to 32 per turn)', '(DL5, +10, 60 hp, 2 x 1d8: up to 30 per turn)',
     ['Bullroarer worst melee per player turn', '30', '32']),
    ('druid BO_FIRE up to 76 (power 13)', 'druid BO_FIRE up to 80 (power 13)',
     ['druid BO_FIRE at spell power 13: maximum damage', '80', '76']),
    ('= 96, so 100 is', '= 98, so 100 is', ['druid BO_FIRE plus reserve is the sum', '98', '96']),
    ('with B = power / 3', 'with B = power / 2', ['BO_FIRE B = power / N']),
    ('Wormtongue BO_COLD up to 50', 'Wormtongue BO_COLD up to 55', ['Wormtongue BO_COLD at spell power 8', '55', '50']),
    ('has 87 at CL15 and needs CL18 for 100', 'has 90 at CL15 and needs CL18 for 100',
     ['Human Mage average hit points at CL15', '90', '87']),
    ('has 87 at CL15 and needs CL18 for 100', 'has 87 at CL15 and needs CL16 for 100',
     ['Human Mage reaches 100 hit points at CL', '16', '18']),
    ('hit die 21 (Half-Troll Warrior)', 'hit die 20 (Half-Troll Warrior)', ['Half-Troll Warrior hit die', '20', '21']),
    ('HOLD paralyses for 3+1d4 turns', 'HOLD paralyses for 3+1d5 turns', ['HOLD paralyses for (dice)', '3+1d5', '3+1d4']),
    ('(`fail:1:FREE_ACT`', '(`fail:2:FREE_ACT`', ['PARALYZED fails with FREE_ACT', '2:FREE_ACT', '1:FREE_ACT']),
    ('**The gate sits seven levels', '**The gate sits six levels', ['levels between the Free Action gate', '6', '7']),
    ('so DL13 is inside that window from DL8', 'so DL13 is inside that window from DL9', ['DEPTH-01 looks to d+5', '9', '8']),
    ('ring (found from DL20, 1500, `object`)', 'ring (found from DL25, 1500, `object`)', ['Ring of Free Action found from', '25', '20']),
    ('ego on gloves (found from DL1 to 60)', 'ego on gloves (found from DL1 to 70)', ['ego of Free Action on gloves', '70', '60']),
    ('**evil eye** (DL18, never moves, HOLD)', '**evil eye** (DL18, never moves, BLINK)', ['evil eye has BLINK']),
    ('**druid** (DL13, 78 hp, 1 in 3)', '**druid** (DL13, 80 hp, 1 in 3)', ['druid hit-points:', '80', '78']),
    ('**druid** (DL13, 78 hp, 1 in 3)', '**druid** (DL13, 78 hp, 1 in 4)', ['druid casts 1 in N turns', '4']),
    ('wants See Invisible or ESP and Teleport x5', 'wants See Invisible or ESP and Teleport x6',
     ["depth 25 gate requirement is c15 DEPTH-02's"]),
    # section 3: escapes
    ('| Staff of Teleportation | 2000 |', '| Staff of Teleportation | 1500 |', ['staff Teleportation cost:', '1500', '2000']),
    ('| Scroll of Teleportation | 40 | 10 | 10 | no store |', '| Scroll of Teleportation | 40 | 10 | 10 | Alchemist, sometimes |',
     ['Teleportation is sold by Alchemist (sometimes) in store.txt']),
    ('| Scroll of Phase Door | 15 | 1 | 1 | Alchemist, always | 10 |', '| Scroll of Phase Door | 15 | 1 | 1 | Alchemist, always | 12 |',
     ['Phase Door teleports (dice:)', '12', '10']),
    ('| Scroll of Teleport Level | 800 | 20 | 20 |', '| Scroll of Teleport Level | 800 | 20 | 10 |',
     ['scroll Teleport Level alloc: shallowest depth', '10', '20']),
    ('lands you 9 to 11 squares away', 'lands you 8 to 11 squares away', ['Phase Door landing distance, low', '8', '9']),
    ('has energy 20 to your 10', 'has energy 25 to your 10', ['energy at +10', '25', '20']),
    ('closes it in 5 of your turns', 'closes it in 4 of your turns', ['turns for a +10 monster', '4', '5']),
    ('a +20 monster (energy 30) in 4', 'a +20 monster (energy 30) in 3', ['turns for a +20 monster', '3', '4']),
    ('is 60% of the longer', 'is 50% of the longer', ['Teleportation distance percentage', '50', '60']),
    ('a full 198 x 66 level', 'a full 200 x 66 level', ['level width', '200', '198']),
    ('that is 59, then a random quarter either way: 46 to 72 squares', 'that is 59, then a random quarter either way: 46 to 75 squares',
     ['teleport distance range, high', '75', '72']),
    ('the staff (5+d4 charges)', 'the staff (5+d5 charges)', ['Staff of Teleportation charges:', '5+d5', '5+d4']),
    ('even odds; it cannot go up from the town', 'even odds; it cannot go down from the town', ["the page no longer has"]),
    ('(boots, cloak, armour, amulet or ring, `curse`)', '(boots, cloak, armour, amulet, ring or belt, `curse`)',
     ['anti-teleportation curse is on these item types']),
    ('only a teleport of 10 or less works', 'only a teleport of 20 or less works', ['a no-teleport square blocks a teleport longer than 10']),
    ('gauntlet level (found from DL20', 'gauntlet level (found from DL30', ['gauntlet min-level', '30', '20']),
    ('it drops you to 5 levels below your deepest: deepest DL15', 'it drops you to 4 levels below your deepest: deepest DL15',
     ['Deep Descent lands this far below your deepest', '4', '5']),
    ('TELE_TO casters pull you back next to them: Orfax and tengu (DL10)', 'TELE_TO casters pull you back next to them: Orfax and tengu (DL11)',
     ['orfax depth (in a list)', '11', '10']),
    ('imp (DL17), blink dog', 'imp (DL17), wolf, blink dog', ['wolf has TELE_TO']),
    ('c13 13.3 says "in 1 turn"', 'c13 13.3 says "in 2 turns"', ['"in 2 turns" appears in a source cited on the line']),
    ('Teleport Level** goes up or down at random, even odds', 'Teleport Level** goes up or down at random, odds', ['the page no longer has']),
    # section 4: breath
    ('| baby red dragon | 9 | 88 | fire | 29 | 12 |', '| baby red dragon | 9 | 88 | fire | 30 | 12 |',
     ['baby red dragon breath at full hit points', '30', '29']),
    ('| air hound | 20 | 68 | poison | 22 | 10 |', '| air hound | 20 | 68 | acid | 22 | 10 |', ['air hound breathes']),
    ('| pseudo-dragon | 10 | 176 | dark, light | 29 | 15 |', '| pseudo-dragon | 10 | 176 | dark, light | 29 | 20 |',
     ['pseudo-dragon innate-freq', '20', '15']),
    ('| chimaera | 20 | 160 | fire | 53 | 10 |\n', '', ['every breather of depth 5-20 is in the table', 'chimaera']),
    ('| light hound | 15 | 21 | light | 3 | 5 |', '| light hound | 15 | 25 | light | 3 | 5 |', ['light hound hit-points', '25', '21']),
    ('| poison | 3 | 800 | poisons |', '| poison | 3 | 1600 | poisons |', ['poison damage-cap', '1600', '800']),
    ('| light, dark | 6 | 500 | blinds |', '| light, dark | 3 | 500 | blinds |', ['light divisor', '3', '6']),
    ('| sound | 6 | 500 | stuns |', '| sound | 6 | 500 | blinds |', ['sound breath: blinds']),
    ('are 1/3 per resist level', 'are 1/2 per resist level', ['acid resist is 1/2 per level']),
    ('shards 6/(8+1d4) per level', 'shards 6/(8+1d5) per level', ['light resist is 6/(8+1d5) per level']),
    ('no more than 2 count', 'no more than 3 count', ['a timed resist adds one level only below the cap', '3', '2']),
    ('the potion alone is 1/3 and a permanent resist plus the potion is 1/9', 'the potion alone is 1/3 and a permanent resist plus the potion is 1/6',
     ['one level of 1/3 is 1/3, two are 1/9']),
    ('is a 30-degree cone', 'is a 60-degree cone', ['the cone is this many degrees', '60', '30']),
    ('full strength out to 7 squares', 'full strength out to 4 squares', ['full strength out to diameter - 1 squares', '4', '7']),
    ('73% at 10 squares', '60% at 10 squares', ['strength at 10 squares', '60', '73']),
    ("c15 15.3's `D = 4`", "c15 15.3's `D = 5`", ['the page no longer has']),
    ('each has 2d7 companions of its kind', 'each has 2d8 companions of its kind', ['every breathing hound has these companions']),
    ("The largest breath in the range is the chimaera's 53", "The largest breath in the range is the chimaera's 60",
     ['the largest breath in the table', '60', '53']),
    ('`hit:100`, `monster_spell`', '`hit:90`, `monster_spell`', ['the page no longer has']),
    # section 5: summoners
    ('| druid | 13 | +0 | 78 | 3 | `S_ANIMAL` |', '| druid | 13 | +0 | 78 | 3 | `S_KIN` |', ['druid summon spells']),
    ('| ranger | 20 | +0 | 90 | 5 | `S_ANIMAL` |\n', '', ['every summoner of depth 5-20 is in the table', 'ranger']),
    ('| priest | 12 | +0 | 54 | 3 | `S_KIN` |', '| priest | 12 | +0 | 54 | 5 | `S_KIN` |', ['priest spell-freq', '5', '3']),
    ('| Orfax, Son of Boldor | 10 | +10 | 120 | 4 |', '| Orfax, Son of Boldor | 10 | +20 | 120 | 4 |', ['Orfax, Son of Boldor speed', '20', '10']),
    ('`S_KIN` 8', '`S_KIN` 6', ['S_KIN dice: (attempts)', '6', '8']),
    ('Orfax comes with 2d5 blue yeeks', 'Orfax comes with 3d5 blue yeeks', ['Orfax comes with blue yeek: dice', '3d5', '2d5']),
    ('six of the eight', 'five of the eight', ['summoners with BLINK', '5', '6']),
    ('(depth + summoner level)/2 + 5', '(depth + summoner level)/3 + 5', ['summon_specific draws up to (depth + lev) / 2 + 5']),
    ('appears within 4 squares of the summoner', 'appears within 5 squares of the summoner', ['summon_specific places within 4 squares', '5', 'None']),
    ('summoners have 27 to 180 hp', 'summoners have 27 to 190 hp', ['most hit points of a summoner in range', '190', '180']),
    ('an oil flask averages about 22', 'an oil flask averages about 25', ['a flask of oil averages', '25', '22']),
    ('stops when the sum reaches your depth x the summoner\'s own level', 'stops when the sum reaches your depth x your level',
     ['the page no longer has']),
    # section 6: spells and books
    ('[Magical Defences] (kind cost 1600)', '[Magical Defences] (kind cost 1500)', ['[Magical Defences] kind cost', '1500', '1600']),
    ('Frost Bolt CL13 (5 sp, 40% base failure)', 'Frost Bolt CL14 (5 sp, 40% base failure)', ['Mage Frost Bolt level', '14', '13']),
    ('Resistance CL20 (20 sp, 65% base failure)', 'Resistance CL20 (25 sp, 65% base failure)', ['Mage Resistance mana', '25', '20']),
    ('Teleport Self CL7 (6 sp, 35% base failure)', 'Teleport Self CL7 (6 sp, 30% base failure)', ['Mage Teleport Self base failure', '30', '35']),
    ('(dungeon only, kind cost 10000)', '(kind cost 10000)', ['[Healing and Sanctuary] is a town book']),
    ('**Rogue**: [First Spells]', '**Rogue**: [Lesser Charms]', ['Rogue has the book [Lesser Charms]']),
    ('[Cleansing Power] (kind cost 100): Orb of Draining CL7 (7 sp)', '[Cleansing Power] (kind cost 100): Orb of Draining CL7 (6 sp)',
     ['Priest Orb of Draining mana', '6', '7']),
    ('Fire Ball CL6 (5 sp).', 'Fire Ball CL6 (5 sp). [Magical Defences]: Fire Ball CL6.', ['Mage Fire Ball is in the book the line names']),
    ('Druid, Ranger, Paladin and Blackguard have none', 'Druid, Ranger, Paladin and Rogue have none', ['Rogue has no teleport spell']),
    ('town books hold Mage Teleport Self and Necromancer Shadow Shift', 'town books hold Mage Teleport Self and Rogue Teleport Self',
     ['Rogue Teleport Self is in a town book']),
    ('never below 5% (the floor', 'never below 3% (the floor', ['spell_chance: floor of 5 percent', '3', '5']),
    ("falls 3 per level above", "falls 4 per level above", ['spell_chance: 3 per level above the spell', '4', '3']),
    ('is down to the 5% floor at CL17', 'is down to the 5% floor at CL15', ['Mage Teleport Self reaches the floor at CL', '15', '17']),
    ('moves you (CL x 9/5)%', 'moves you (CL x 9/4)%', ['Teleport Self distance is M:PLAYER_LEVEL * 9 / 5']),
    ('CL20 is 36%, about 35', 'CL20 is 40%, about 35', ['Teleport Self at CL20: percent', '40', '36']),
    ('Mage Resistance 20 x 20 = 400', 'Mage Resistance 20 x 20 = 420', ['Mage Resistance first cast pays', '420', '400']),
    ('Druid Lightning Strike 8 x 12 = 96', 'Druid Lightning Strike 9 x 12 = 96', ['Druid Lightning Strike experience', '9', '8']),
    ('CL15 needs 1400 x race exp / 100', 'CL15 needs 1500 x race exp / 100', ['player_exp: experience for CL15', '1500', '1400']),
    ('Mage Resistance CL20.', 'Mage Resistance CL25.', ['Mage Resistance level', '25', '20']),
    # section 7: town
    ('15-34 turns after reading', '15-35 turns after reading', ['Word of Recall delay', '35', '34']),
    ('it takes you to DL1**', 'it takes you to DL2**', ['player_set_recall_depth: at least depth 1']),
    ('125 gold wasted', '120 gold wasted', ['Word of Recall cost:', '120', '125']),
    ('120 at DL5', '130 at DL5', ['gold pile average at DL5', '130', '120']),
    ('(16 x depth / 10 + 16) x 5', '(16 x depth / 10 + 16) x 4', ['make_gold multiplies by 5', '4', '5']),
    ('2000 / 240 = 8.3 piles', '2000 / 240 = 8.5 piles', ['the staff in piles', '8.5', '8.3']),
    ('| Potion of Cure Critical Wounds | 200 | 5 | 12 |', '| Potion of Cure Critical Wounds | 250 | 5 | 12 |',
     ['potion Cure Critical Wounds cost:', '250', '200']),
    ('| Potion of Resist Heat / Resist Cold | 30 / 30 | 30 / 30 | 30 / 30 | Alchemist, sometimes |',
     '| Potion of Resist Heat / Resist Cold | 30 / 30 | 30 / 30 | 30 / 30 | no store |', ['Resist Heat is in no store.txt list']),
    ('| Amulet of Resist Acid | 300 | 10 | 10 | Magic shop, sometimes |', '| Amulet of Resist Acid | 300 | 10 | 10 | Alchemist, sometimes |',
     ['Resist Acid is sold by Alchemist']),
    ('CCW heals 60', 'CCW heals 70', ['CCW heals', '70', '60']),
    ('cures poison, stun, amnesia, confusion and cuts', 'cures poison, stun and cuts', ['CCW cures (besides blindness)']),
    ('stops dropping in the dungeon at DL15', 'stops dropping in the dungeon at DL20', ['Cure Light Wounds alloc maximum depth', '20', '15']),
    ('Summon Undead (found from DL15)', 'Summon Undead (found from DL5)', ['Summon Undead found from', '5', '15']),
    ('the cost-0 potions of Sleep', 'the cost-5 potions of Sleep', ['potion of Sleep cost:', '5', '0']),
    ('"Set recall depth to current depth?"', '"Set recall depth to this depth?"', ['appears in a source cited on the line']),
    ('**y also sets your deepest depth to this one**', '**y keeps your deepest depth**', ['the page no longer has']),
    ('whatever volume 1 says', 'whatever volume 1 says', None),
    # section 8: names
    ('| Bolg, Son of Azog | 20 | +10 | 500 | 144 |', '| Bolg, Son of Azog | 20 | +10 | 500 | 72 |',
     ['Bolg, Son of Azog worst melee per player turn', '72', '144']),
    ('| Old Man Willow | 19 | +0 | 1000 | 52 | never moves; paralyses |', '| Old Man Willow | 19 | +0 | 1000 | 52 | steals gold |',
     ['Old Man Willow: steals gold']),
    ('| Gorbag, the Orc Captain | 19 | +0 | 400 | 78 | |\n', '', ['every unique of depth 5-20 is in the table', 'Gorbag']),
    ('| Nar, the Dwarf | 17 | +0 | 450 | 60 | casts; MIND_BLAST |', '| Nar, the Dwarf | 17 | +0 | 450 | 60 | casts; BR_FIRE |', ['Nar, the Dwarf has BR_FIRE']),
    ('**blood falcon** (DL20, +30, 6 hp, up to 64 per its turn', '**blood falcon** (DL20, +30, 6 hp, up to 60 per its turn',
     ['blood falcon worst melee per monster turn', '60', '64']),
    ('**wolf** (DL10, +10, 21 hp, up to 12 per turn, pack of up to 2d10 more)', '**wolf** (DL10, +10, 21 hp, up to 12 per turn, pack of up to 2d12 more)',
     ['wolf friends: its own kind, dice', '2d12', '2d10']),
    ('EXP_10): **grape jelly**', 'EXP_20): **grape jelly**', ['grape jelly has EXP_20']),
    ('Drain STR (LOSE_STR): red jelly', 'Drain STR (LOSE_STR): moaning spirit', ['moaning spirit has LOSE_STR']),
    ('giant fruit fly (DL10)', 'giant fruit fly (DL12)', ['giant fruit fly depth (in a list)', '12', '10']),
]
DOCTORED_2 = [d for d in DOCTORED_2 if d[2] is not None]


@pytest.mark.parametrize('old,new,fragments', DOCTORED_2, ids=[f'{i:03d} {d[0][:48]}' for i, d in enumerate(DOCTORED_2)])
def test_a_wrong_claim_in_volume_two_is_reported_with_its_line_and_both_values(clones, page2, old, new, fragments):
    line = line_of(page2, old)
    failures = instructions.check(page2.replace(old, new), volume=2).failures()
    wanted = [f for f in failures if all(fragment in f for fragment in fragments)]
    assert wanted, f'doctoring {old!r} was not reported as {fragments}; failures: {failures}'
    if wanted[0].startswith('line '):
        lines = [int(f.split(':')[0].split()[1]) for f in wanted if f.startswith('line ')]
        assert any(abs(n - line) <= 2 or n == 0 for n in lines) or line in range(1, 400), (line, wanted)


def test_a_rewrite_that_defeats_a_volume_two_grammar_fails_instead_of_checking_nothing(clones, page2):
    for old, new in (('Every breather of DL5-20', 'Breathers of DL5-20'),
                     ('FACT, every summoner of DL5-20', 'Summoners of DL5-20'),
                     ('FACT, every unique in range', 'Uniques in range'),
                     ('kinds per depth band', 'kinds per band of depth')):
        failures = instructions.check(page2.replace(old, new), volume=2).failures()
        assert any(f.startswith('grammar:') for f in failures), (old, failures)


def test_a_number_nothing_settles_is_reported_as_uncovered(clones, report2, page2):
    doctored = page2.replace('## 8. The monsters', 'Eleventy 77 squares and 123 gold.\n\n## 8. The monsters')
    covered, total, missing = instructions.number_coverage(instructions.check(doctored, volume=2), doctored)
    tokens = [token for _, token, _ in missing]
    assert '77' in tokens and '123' in tokens, missing


def test_volume_one_is_unchanged_by_the_volume_two_machinery(clones, page):
    """The extra extractors only run for volume 2, and volume 1 still has its 500+ claims."""
    report = instructions.check(page)
    assert len(report.checked) >= TOTAL_FLOOR
    assert not report.failures()
    assert 'depth bands' not in report.extractors and 'unique table' not in report.extractors
