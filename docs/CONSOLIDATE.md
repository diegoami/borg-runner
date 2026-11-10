# Consolidating notebooks into the page

A notebook is a **log**: what one player noticed, in order, in its own words.
That is the right shape for evidence and the wrong shape for reading. Your job
is to move what the runs have learned onto the page a player actually reads,
**with the runs that saw it named**, so that every claim there leads back to a
screen.

One output: [`manuals/INSTRUCTIONS.md`](../manuals/INSTRUCTIONS.md) (and
`INSTRUCTIONS_2.md` for depth 5 to 20, where no run has been).

Until 2026-11-10 there were two more — `knowledge/LEARNED.md`, an item store
with ids and statuses, and `knowledge/MANUAL-GAPS.md`, cheat sheets to paste
into the manual. They were removed once the page carried their content: a
reader had three documents to reconcile and the page was the only one anybody
read. They are in git history; the notebooks they were built from are
untouched in `knowledge/`.

## What a line on the page looks like

A claim that rests on play says so, and names its evidence as `run#ask`:

```
- **A `-more-` swallows the next key** (3 runs: sonnet-1#21, sonnet-2#16,
  sonnet-3#32). A command typed behind one loses its first key ...
```

The rules are checked by

```sh
python -c "from borg_runner import consolidate; print(consolidate.check())"
```

which must print `[]` when you are done:

- **A claim about play names at least one run**, as `run#ask`. The run must
  exist and the ask must be within its range. A line that says OBSERVED and
  names nothing is a superstition, and the check says so.
- **"N runs" has to name N different runs.** One run noticing something twice
  is one run. This is the old `confirmed` rule in its new place: two different
  runs, or say plainly that it is one run's word.
- **A later run that disagrees is written down, not deleted.** Put the
  disagreement on the page where the claim is — that is the interesting part,
  and a reader who meets the same thing needs to know it is contested.
- **Labels mean what they say**: FACT is in the game's data or source (name
  the file), OBSERVED is from runs (name them), POLICY is the strategy
  manual's advice to be tested, UNTESTED means nobody has tried it.

Before you add a line, check whether the page already says it. If the game's
own manual says it and a player still had to learn it the hard way, that is
worth a sentence where the key is explained, not a new section.

## Read what every run wrote, every time

Not occasionally. The same things come back: five runs treated the down
staircase as the only plan, four measured the level against the view, nine
lost keys to a prompt. **A theme that recurs and is not on the page is the
page's fault, not the players'.**

```sh
.venv/bin/python -m borg_runner consolidate
```

prints the recurring themes, how many runs raised each, and whether the page
answers it — counted from both the reports **and** the notebooks, because they
hold different things. A report says what the reading lacked; a notebook holds
the thing measured at the ask it was measured, and some of the best lines
never reach a report at all: that store letters shift only *after* the row you
bought, so buying the last row first keeps every earlier letter valid; that an
aim into unexplored ground can walk zero steps.

The theme list is in `consolidate.py` and is maintained by hand on purpose:
counting is mechanical, deciding that two runs mean the same thing is not. Add
a theme when a second run raises something the first one did; the patterns
that identify it are regular expressions over what a run wrote, and the
pattern that marks it answered is a phrase on the page.

`archive` prints the same thing for one run at the moment its report lands, so
the player and whoever reads the log both see which themes it raised and
whether the page already answers them.

## What belongs on the page, and what belongs to one family

A line on the page has to hold for any player. What one model family found out
about *itself* — how it reads the screen, what it keeps forgetting, what it
would do differently — goes in `agents/<family>/COMMON.md` and
`agents/<family>/<CLASS>.md`, which that family's own next session reads.
Those are not yours to edit unless you are that family.

## What you are given, and nothing else

```sh
cat knowledge/*.md       # the notebooks, as promoted by `keep`
python -c "from borg_runner import consolidate; import json; print(json.dumps(consolidate.inputs(), indent=1))"
```

`inputs()` also lists `not_yet_cited`: the notebooks the page does not mention
anywhere, which is where to start.

The real manuals, to check a claim against and to find what they omit:

```sh
vendor/angband/docs/command.rst   vendor/angband/docs/guide.rst
vendor/angband/docs/playing.rst   vendor/angband/docs/attack.rst
cd vendor/strategy-manual && git cat-file -p HEAD:docs/c-manual/README.md
```

The run records, for what a run actually reached: `records/<name>/record.json`
and `decisions.jsonl`, and the screens at `runs/<name>/ask/screen-<n>.txt`
when you want to see what a note was looking at.

## What you must not do

- Do not invent a line that no notebook supports. The check catches a citation
  that names no run; it cannot catch a citation that names the wrong ask, so
  read the ask you cite.
- Do not claim two runs on one run's word, including your own reading of the
  source or the manual. Reading is not a trial: that is a FACT line, with the
  file it came from.
- Do not edit a notebook in `knowledge/`. They are the evidence.
- Do not edit another family's playbook in `agents/`.
