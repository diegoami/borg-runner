"""Check the prompts: a prompt may repeat the page, never replace it.

A prompt is handed to one player and then thrown away. The page
(`manuals/INSTRUCTIONS.md`) is read by every player before its first keypress,
for ever. So a tip that lives only in a prompt is a tip the next player never
sees - and the owner noticed it happening: a brief written for one mage carried
the experience ladder, the kill arithmetic and a correction to a spell's
damage, none of which were anywhere a later mage would look.

The rule is therefore: **a prompt may repeat what the page says, and must not
be the only place something is said.** This module turns that into a check
over `PLAYGAME.txt`, `CONTINUEGAME.txt` and every brief in `prompts/`:

* a paragraph that marks a claim `FACT,` / `OBSERVED,` / `POLICY:` must carry
  an anchor - a source citation or a `run#ask` - and every anchor it carries
  must appear on the page as well;
* every source citation anywhere in a prompt (`src/...`, a gamedata file, a
  function) must appear on the page;
* every `run#ask` anywhere in a prompt must appear on the page;
* a double-quoted phrase used to point at the page must be findable there,
  so a renamed section is caught instead of sending a reader to nothing;
* a brief in `prompts/` says which template it is added to, because a brief
  replaces an objective and never the procedure;
* a prompt must name the page and the family playbook directory it expects to
  be read.

What it cannot check: whether the page's version of a tip is as clear as the
prompt's, or whether a sentence with no label and no number is knowledge. It
catches the failure that has actually happened - a cited, labelled fact with
nowhere to live - and nothing subtler.
"""
import re

from borg_runner import pins

TEMPLATES = ('PLAYGAME.txt', 'CONTINUEGAME.txt')
BRIEFS = pins.ROOT / 'prompts'
PAGE = pins.ROOT / 'manuals' / 'INSTRUCTIONS.md'
PAGE_2 = pins.ROOT / 'manuals' / 'INSTRUCTIONS_2.md'

# `FACT,` `(OBSERVED` `POLICY:` - the label used to mark a claim, not to explain
# what the labels mean (`**FACT** is in the game's data` is a definition).
CLAIM_LABEL = re.compile(r'(?:^|[\s(*])\*{0,2}(FACT|OBSERVED|POLICY|UNTESTED)\*{0,2}[,:)]')
RUN_ASK = re.compile(r'\b([a-z][\w.-]*-[\w.]*#\d+|[a-z][\w.]*\d#\d+)\b')
CITATION = re.compile(r'`([^`\n]*(?:src/[\w./-]+|\b\w+\.txt\b|\w+\(\))[^`\n]*)`')
QUOTED = re.compile(r'"([^"\n]{12,})"')
IDENTIFIER = re.compile(r'[\w./-]*(?:src/[\w./-]+|\w+\.txt|\w+)\(\)|src/[\w./-]+|\b\w+\.txt\b')

# Quoted phrases that are not page references: keys, examples, messages the
# game prints, commit lines. A prompt quoting the game is quoting the screen.
# The harness's own files are not claims about the game: a prompt names them
# because the player has to use them, and the page never mentions them.
HARNESS = ('runs/', 'records/', 'knowledge/', 'agents/', 'tools/', 'manuals/',
           'input.txt', 'record.json', 'decisions.jsonl', 'notebook.md',
           'replay.json', 'history.json', 'source.json', 'started.json',
           'index.html', 'pins.json', 'keys.txt', 'screen-')

NOT_A_PAGE_REFERENCE = ('{RUNNAME}', 'I see no', 'one line', 'a trick worth',
                        'something new', '<depth', 'MD')


def files():
    """Every prompt this repository keeps, templates first."""
    found = [pins.ROOT / name for name in TEMPLATES]
    if BRIEFS.is_dir():
        found += sorted(path for path in BRIEFS.glob('*.txt'))
        found += sorted(path for path in BRIEFS.glob('*.md'))
    return [path for path in found if path.is_file()]


def page_text():
    """Both volumes of the page, as one string to search."""
    text = PAGE.read_text() if PAGE.is_file() else ''
    if PAGE_2.is_file():
        text += '\n' + PAGE_2.read_text()
    return text


def paragraphs(text):
    """(line number, paragraph) for every blank-line-separated block."""
    found, line, current, start = [], 1, [], 1
    for raw in text.splitlines():
        if raw.strip():
            if not current:
                start = line
            current.append(raw)
        elif current:
            found.append((start, '\n'.join(current)))
            current = []
        line += 1
    if current:
        found.append((start, '\n'.join(current)))
    return found


def anchors(text):
    """The citations a piece of prompt leans on: sources and `run#ask` pairs.
    The harness's own files are not citations about the game."""
    sources = {found[1].strip() for found in CITATION.finditer(text)
               if not any(part in found[1] for part in HARNESS)}
    return sorted(sources | {found[1] for found in RUN_ASK.finditer(text)})


def on_the_page(anchor, page):
    """Is the anchor on the page? A source citation matches on its identifiers,
    so `src/gen-cave.c town_gen_layout()` is found however the page words it."""
    if anchor in page:
        return True
    parts = IDENTIFIER.findall(anchor)
    return bool(parts) and all(part.rstrip('()') in page for part in parts)


def check(paths=None):
    """What is wrong, as sentences. Empty means every prompt only repeats the
    page."""
    page = page_text()
    problems = []
    for path in (paths if paths is not None else files()):
        name = path.name
        text = path.read_text()
        if 'manuals/INSTRUCTIONS.md' not in text:
            problems.append(f'{name}: does not send the player to '
                            f'manuals/INSTRUCTIONS.md')
        if 'agents/' not in text:
            problems.append(f'{name}: does not send the player to its family '
                            f'playbook in agents/')
        if path.parent == BRIEFS and not any(t in text for t in TEMPLATES):
            problems.append(f'{name}: a brief is an objective added to '
                            f'{TEMPLATES[0]} or {TEMPLATES[1]}, and must say '
                            f'which of them it is added to')
        for line, block in paragraphs(text):
            found = anchors(block)
            labels = CLAIM_LABEL.findall(block)
            if labels and not found:
                problems.append(
                    f'{name}:{line}: a {labels[0]} claim with no anchor - a '
                    f'labelled claim in a prompt must cite the source or the '
                    f'run that settles it, and that citation must be on the page')
            for anchor in found:
                if not on_the_page(anchor, page):
                    problems.append(
                        f'{name}:{line}: cites {anchor} which is nowhere in '
                        f'manuals/INSTRUCTIONS.md - put it on the page first, '
                        f'then the prompt can repeat it')
            for quote in QUOTED.findall(block):
                if any(skip in quote for skip in NOT_A_PAGE_REFERENCE):
                    continue
                if 'INSTRUCTIONS' not in block and 'page' not in block.lower():
                    continue
                if quote not in page:
                    problems.append(
                        f'{name}:{line}: points at "{quote}" on the page, which '
                        f'does not say that any more')
    return problems


def inputs():
    """What the check reads, for a report."""
    return {'prompts': [str(path.relative_to(pins.ROOT)) for path in files()],
            'page': str(PAGE.relative_to(pins.ROOT))}
