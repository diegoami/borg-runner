# Consolidating notebooks into knowledge

A notebook is a **log**: what one player noticed, in order, in its own words.
That is the right shape for evidence and the wrong shape for knowledge. Your
job is to turn the logs into one document in which every item is **filed
against the manual**, and to say **what the manual should have said**.

Two outputs, and the second is the point.

## 1. `knowledge/LEARNED.md` — the filed knowledge

One item per line, with its fields indented beneath it:

```
- [id] the statement, in one sentence, as a thing a player can act on
  anchor: key:> | OIL-01 | goal:descend | state:cursor | new:<a short slug>
  status: hypothesis | confirmed | contradicted
  evidence: sonnet-1#83, sonnet-1#104
  supersedes: <id>            (only when it replaces an earlier item)
```

The rules are checked by `python -c "from borg_runner import consolidate;
print(consolidate.check())"`, which must print `[]` when you are done:

- **`anchor` must be something the manual actually has** — a command key
  (`key:v`), a strategy rule (`OIL-01`, `ESC-01`, `DEPTH-01`, `STAIR-01`,
  `FIGHT-01`, `REST-01`, `TOWN-01`, `ANTI-11`), a goal (`goal:descend`) or a
  state field (`state:cursor`) — **or** `new:<slug>` when the manual does not
  cover this ground at all. Filing against nothing is not knowledge.
- **`evidence` is `run#ask`**, at least one, and the run must exist and the
  ask must be within its range. A line with no evidence is a superstition.
- **`status` starts at `hypothesis`.** You may write `confirmed` only when
  **two different runs** show it. One run noticing something is not a fact.
- A later run that disagrees makes the item `contradicted`. **Never delete
  it** — the disagreement is the interesting part, and the player's own
  correction in `sonnet-1` is an example of exactly that.
- Say in the document's own header **which files you read** to do this work.

Before you file an item, check whether the manual already says it. If the
game's own manual says it and the player had to learn it the hard way, that is
worth knowing too: anchor it to the key, and note in the statement that the
manual does say so.

## 2. `knowledge/MANUAL-GAPS.md` — what the manual should say

For every `new:` item, and for every place where a player lost keys or hit
points to something the manual does not explain, write **the text you would
add to the manual**, ready to paste. Keep it in the manual's own voice:
descriptive, with the condition under which it applies.

Group these as cheat sheets a player would want before the first key. The
owner's own example, and a real gap in `sonnet-1`: **unidentified objects —
what identifying by use costs, when it is safe to drink or read something
unknown, and what it is worth.** That run drank an unknown potion, gained a
character level from first-use identification, and read two unknown scrolls
safely on depth 1; none of that is in the compressed manual, and a player who
knew it would spend its early gold differently.

Say for each one **why it is worth the space**: which run lost what by not
knowing it.

## What you are given, and nothing else

```sh
cat knowledge/*.md                                   # the notebooks, as promoted
cat manuals/jev-1.md                                 # the compressed manual
python -c "from borg_runner import consolidate; import json; print(json.dumps(consolidate.inputs(), indent=1))"
```

The real manuals, to check a claim against and to find what they omit:

```sh
vendor/angband/docs/command.rst   vendor/angband/docs/guide.rst
vendor/angband/docs/playing.rst   vendor/angband/docs/attack.rst
cd vendor/strategy-manual && git cat-file -p HEAD:docs/c-manual/README.md
```

The run records, for what a run actually reached:
`runs/<name>/record.json`, and the screens at `runs/<name>/ask/screen-<n>.txt`
when you want to see what a note was looking at.

## What you must not do

- Do not invent an item that no notebook supports.
- Do not promote anything to `confirmed` on one run's word, including your own
  reading of the source or the manual. Reading is not a trial.
- Do not edit a notebook in `knowledge/`. They are the evidence.
