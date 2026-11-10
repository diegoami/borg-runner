"""The leads a player wrote: what it would do differently, and what would settle it.

A run's write-up ends with its leads - the questions the run could not answer
with the asks it had, each with the evidence and what would settle it. It is
the most valuable thing a run produces, and the page did not show it: the
report page had the notebook (what it kept) and the timeline (what it did),
and linked the write-up to GitHub, so the leads were a click and a scroll away
from the replay they belong to.

So they are read here, out of the player's own `REPORT.md`, and put on the
page beside the replay. Two things are added to what the player wrote, and
both are mechanical:

- **the turn.** A lead names where it happened - "asks 67-70", "ask 43-44" -
  and an ask is a number, not a place in the game. The run's own decisions
  say what turn each ask happened at, so an ask is resolved to the turn it
  was: the number `takeover --at-turn` wants, and the one the replay's
  scrubber counts in. A turn named in prose is shown only when the lead names
  no ask, because a turn in prose is often a hypothetical - "do it at turn
  ~800" is where the test should be *run*, not where the evidence is.

- **the test.** The prompts ask for it ("your leads - each with the evidence
  and what would settle it") and the players wrote it under half a dozen
  names, so it is picked out of the prose and shown beside the claim.

Nothing here is an opinion about how to play. The words are the player's; the
only judgement is which heading holds the leads and which clause holds the
test, and both are left visible when they are not found.
"""
import re

# A heading: `## 5. Leads`, `## Leads, with what would settle each`.
HEADING = re.compile(r'^(?P<marks>#{1,6})\s+(?P<title>.*?)\s*$')
# The heading that holds the leads. "Leads" is the word the prompts use;
# "would change" is how the one human run named the same thing. "The
# decisions I would take back" is a different section - what went wrong, not
# what is open - and it is deliberately not matched.
LEADS = re.compile(r'\bleads?\b|\bwould change\b', re.IGNORECASE)

# A list item: `- `, `* `, `1. `.
ITEM = re.compile(r'^(?:[-*+]|\d+[.)])\s+(?P<text>.*)$')

# The claim, when the lead opens with the player's own emphasis.
EMPHASIS = re.compile(r'^(?P<claim>\*\*.+?\*\*|\*.+?\*)\s*', re.DOTALL)
# "Lead: " - how the one report that used the word wrote it.
PREFIX = re.compile(r'^\s*lead[:\s-]+', re.IGNORECASE)

# A sentence ends at a full stop; a clause also ends at a semicolon. A colon
# ends neither: "Read every unknown scroll the moment it is picked up on
# DL1-2: Deep Descent was 1 of the first 2 scrolls" is one claim, and cutting
# it at the colon would keep only the instruction.
SENTENCE = re.compile(r'\.(?=\s|$)')
CLAUSE = re.compile(r'[.;](?=\s|$)')

# The test, under the names the players gave it.
TEST = re.compile(r'\btests?\b|\bwhat would settle\b|\bto settle\b|\bwould settle\b'
                  r'|\bsettling it\b|\bto confirm\b', re.IGNORECASE)
# A colon right after the name, with at most one short word in between: "Test:",
# "What would settle it:", "To confirm empirically:".
COLON = re.compile(r'\s*(?:[a-z]{1,12})?\s*:')

# A number, with the thousands separator the players used: `1,701` is one
# number and not two.
NUMBER = r'\d{1,3}(?:,\d{3})+|\d+'
NUMBERS = re.compile(NUMBER)
# `ask 43`, `asks 67-70`, `ask-43`.
ASK = re.compile(rf'\basks?[-–—]?\s*(?P<first>{NUMBER})'
                 rf'(?:\s*[-–—]\s*(?P<last>{NUMBER}))?')
# `turn 701`, `turns 690, 850, and 1360`, `turn ~800`.
TURN = re.compile(rf'\bturns?[-–—]?\s*(?P<first>~?{NUMBER})'
                  rf'(?:\s*[-–—]\s*(?P<last>{NUMBER}))?'
                  rf'(?P<rest>(?:\s*,\s*(?:and\s+)?(?:{NUMBER}))*)')


def section(text):
    """The lines under the heading that holds the leads, or nothing.

    The heading is found by its name rather than by its place, because the
    players wrote it in their own words: "## 5. Leads", "## Leads, with what
    would settle each", "## Manual gaps and leads", and the one human run
    wrote "## What I would change".
    """
    lines = text.splitlines()
    start, level = None, 0
    for number, line in enumerate(lines):
        heading = HEADING.match(line)
        if not heading:
            continue
        if start is None:
            if LEADS.search(heading.group('title')):
                start, level = number + 1, len(heading.group('marks'))
            continue
        if len(heading.group('marks')) <= level:
            return '\n'.join(lines[start:number])
    if start is None:
        return ''
    return '\n'.join(lines[start:])


def items(text):
    """The leads of a section, each with the lines that continue it.

    A lead is a list item, and its wrapped lines belong to it. A list wins
    over a paragraph: a section that has bullets is a list of leads with an
    introduction, and the introduction is not a lead.
    """
    bullets, paragraphs = [], []
    current, kind = None, None
    for line in text.splitlines():
        if not line.strip():
            current, kind = None, None
            continue
        bullet = ITEM.match(line)
        if bullet:
            current = [bullet.group('text')]
            bullets.append(current)
            kind = 'bullet'
        elif line[:1] in (' ', '\t') and current is not None:
            current.append(line.strip())
        elif kind == 'paragraph' and current is not None:
            current.append(line.strip())
        else:
            current = [line.strip()]
            paragraphs.append(current)
            kind = 'paragraph'
    chosen = bullets if bullets else paragraphs
    return [' '.join(part.strip() for part in entry).strip() for entry in chosen]


def claim_of(item):
    """The claim, and where it ends in the item.

    The claim is the player's own emphasis when the lead opens with one -
    every report that wrote its leads that way marked the question - and the
    first clause otherwise.
    """
    emphasis = EMPHASIS.match(item)
    if emphasis:
        claim = emphasis.group('claim')
        end = emphasis.end()
    else:
        clause = CLAUSE.search(item)
        end = clause.end() if clause else len(item)
        claim = item[:end]
    return PREFIX.sub('', claim).strip().rstrip(' ;'), end


def test_of(item):
    """The test, and the span of the item it occupies.

    The prompts ask for "the evidence and what would settle it", and the
    players wrote the second under half a dozen names. Where the name opens
    its clause the test is that clause - and when a colon follows it, it runs
    to the end of the sentence, because the sentence is the test. Where the
    name sits inside a clause the whole clause is the test, since the name
    alone says nothing: "would settle it" is the end of a sentence, not a
    test.

    The player's own wording is kept, name and all, so the page shows what
    was written rather than a tidied version of it.
    """
    found = TEST.search(item)
    if not found:
        return None, (0, 0)
    boundary = max((match.end() for match in CLAUSE.finditer(item, 0, found.start())),
                   default=0)
    sentence = SENTENCE.search(item, found.end())
    sentence_end = sentence.end() if sentence else len(item)
    clause = CLAUSE.search(item, found.end())
    clause_end = clause.end() if clause else len(item)
    if item[boundary:found.start()].strip():
        # The name is inside a clause of its own, so the clause is the test.
        span = (boundary, clause_end)
    elif COLON.match(item, found.end()):
        # The name opens its clause and a colon follows it, so the test runs
        # to the end of the sentence.
        span = (found.start(), sentence_end)
    else:
        span = (found.start(), clause_end)
    return item[span[0]:span[1]].strip(), span


def asks_in(text):
    """The asks a lead names, as the ranges it wrote them."""
    found = []
    for match in ASK.finditer(text):
        first = int(match.group('first').replace(',', ''))
        last = match.group('last')
        found.append((first, int(last.replace(',', '')) if last else first))
    return found


def turns_in(text):
    """The turns a lead names, as the numbers it wrote them."""
    found = []
    for match in TURN.finditer(text):
        first = match.group('first').replace(',', '').lstrip('~')
        found.append(int(first))
        last = match.group('last')
        if last:
            found.append(int(last.replace(',', '')))
        found.extend(int(number.replace(',', ''))
                     for number in NUMBERS.findall(match.group('rest')))
    return found


def parse(text):
    """The leads of a write-up, each with its claim, evidence and test.

    Nothing is invented: a lead that names no test has none, and the
    evidence is whatever was written between the claim and the test. The
    test is looked for after the claim, because a claim that happens to use
    the word - "a claim with no test in it" - is not a test of itself.
    """
    found = []
    for item in items(section(text)):
        claim, claim_end = claim_of(item)
        rest = item[claim_end:]
        test, (start, end) = test_of(rest)
        evidence = (rest[:start] + rest[end:]) if test else rest
        found.append({
            'claim': claim,
            'evidence': ' '.join(evidence.split()).lstrip(': '),
            'test': test,
            'asks': asks_in(item),
            'turns': turns_in(item),
        })
    return found


def where(lead, turns):
    """The place in the run the lead points at.

    The asks are the anchor: an ask is a place in *this* run, and the run's
    own decisions say what turn it was at. A turn named in prose is shown
    only when the lead names no ask, because a turn in prose is often a
    hypothetical - where the test should be run, not where the evidence is.
    """
    asks = []
    for first, last in lead['asks']:
        asks.extend(range(first, last + 1))
    if asks:
        known = [turns[ask] for ask in asks if ask in turns]
        return {'asks': asks, 'turns': known, 'ranges': lead['asks']}
    return {'asks': [], 'turns': lead['turns'], 'ranges': []}
