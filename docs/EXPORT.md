# Exporting what the runs established

Everything else in this repository is written **inward**: the distilled page a
player reads, the notebooks it leaves, the playbook its model family keeps.
This is the one document written **outward**.

[`ACCUMULATED_KNOWLEDGE.md`](../ACCUMULATED_KNOWLEDGE.md), at the root, is for
**borg-reborn-rs** — the Rust Borg being rebuilt — and for anyone else outside
this repository who wants what the runs learned without reading ten reports.
It is a distillation of the **reports**: what each player concluded, with the
evidence attached and the confidence stated.

It is rewritten **from time to time**, not after every run. A single run
rarely changes what the corpus knows, and an export rewritten per run would be
a changelog instead of a summary. The owner decides when; `borg_runner export`
says what has arrived since the last edition.

## No player reads it

Not a matter of taste. A run is given the distilled manual and its own
family's pages, and is denied exactly one thing: **another run's account of
the seed it is playing** (D9). This file aggregates every report in the
corpus, so handing it to a player hands them a solution key for their own
dungeon — where this seed's staircase was, which scroll on the floor was Deep
Descent.

So: neither prompt mentions the file, nothing in `manuals/` links it, and a
test holds both. It also means the export may say things a player's page may
not: it is read by a program in another repository, not by someone about to
press a key here.

## The process

```sh
.venv/bin/python -m borg_runner export            # what is new, and the corpus
.venv/bin/python -m borg_runner export --check    # what is wrong with it
.venv/bin/python -m borg_runner export --inputs   # exactly what to read, as JSON
```

1. **Read what `--inputs` lists**, and nothing else: every
   `records/<run>/REPORT.md`, the records beside them for the numbers, the
   notebooks in `knowledge/` where a report's claim needs its original words,
   and the game's own tree at the pin when a report's explanation has to be
   checked. `not_yet_read` is where to start — the reports no edition has
   mentioned yet.
2. **Write the next edition** of `ACCUMULATED_KNOWLEDGE.md`, in full. An
   edition is a rewrite, not an append: a reader outside this repository
   should be able to read it top to bottom and stop.
3. **Run the check**, which must print `[]`.
4. **Commit it with the corpus it was written from** — the edition number, the
   date, and the run count are in its header, so a consumer can tell what it
   had seen.

## What an edition must contain

- **An edition line**: `Edition <n>, <yyyy-mm-dd>`. The check fails without
  one, because a consumer that cannot date the document cannot tell whether it
  predates the runs it cares about.
- **Who it is for**, naming borg-reborn-rs, and the warning that players do
  not read it.
- **The corpus**: every run, with model, character, depth, level, asks, turns
  and how it ended, each row linking its report. The numbers come from the
  records, not from the reports, which is why `export` prints them.
- **A provenance on every claim**, in one of four forms:

  | | |
  |---|---|
  | `run#ask` | the screen is in `records/<run>/`, the player's words in `knowledge/<run>.md` |
  | GAME SOURCE | read out of `vendor/angband` at the pin; true of the game, not of a run |
  | ONE RUN | one player, once. A lead |
  | N RUNS | N different runs, independently |

- **What the corpus cannot answer**, with what would settle each. An export
  that reads as if the questions are closed is worse than no export: the
  consumer cannot see where its own evidence would be the first.

## What it must not contain

- **Anything the manuals already say.** This is the rule that decides most of
  the document's length, and the first draft of edition 1 broke it. The
  consumer reads the game's own manual, the strategy manual and
  `lib/gamedata` itself — at leisure and in full, which a player inside a
  150-decision budget cannot. So the command set, the spell lists, prices,
  kits, monster tables and the escape ladder are **not** knowledge this
  repository produces. What is left is the residue: what the runs measured,
  what they corrected in the manuals, and what had to be read out of the
  source because no manual states it. A data file is quoted only where a
  run's conclusion depends on it.
- **What is only true of reading a text screen.** Where a keypress is lost to
  a `-more-`, that menu letters are labels and not positions, that the glyph
  under `@` is not drawn, that a blank health bar means *unseen*: all real,
  all in `manuals/INSTRUCTIONS.md` for the players here, and none of it
  knowledge about Angband. A consumer with the game's own state does not have
  those problems. The exception is a death: when one of them killed a run, the
  death is the finding and it stays.
- **A claim with no provenance.** The check catches a citation that names no
  run; it cannot catch a claim with no citation at all, so that is on the
  writer.
- **A one-run claim dressed as a fact.** The corpus is ten runs. Most of what
  it knows, it knows once.
- **This repository's own machinery.** How the frontend writes `question-<n>.txt`
  is not knowledge about Angband; the consumer does not run this frontend.
- **Advice phrased as a threshold.** "Leave below 40% hit points" is a policy
  this repository has not measured and has no business exporting (D2). What
  the export carries is what happened, with the numbers.

## What the check actually checks

`borg_runner export --check`, or `export.check()`:

- the file exists and carries an edition line;
- every `run#ask` names a run that exists, and an ask inside that run's range;
- the consumer is named.

Staleness is deliberately **not** a failure: `missing()` lists the reports no
edition has read, and that is information, not an error. CI does not fail
because a run finished this morning.

## Where this sits

| | |
|---|---|
| `manuals/INSTRUCTIONS.md` | inward: what a player reads before its first keypress |
| `agents/<family>/` | inward: what one model family tells its own next session |
| `knowledge/<run>.md`, `records/<run>/` | the evidence: notebooks, keys, decisions, replays |
| `ACCUMULATED_KNOWLEDGE.md` | **outward**: what the corpus establishes, for the consumer |

[docs/CONSOLIDATE.md](CONSOLIDATE.md) is the inward counterpart of this
document: notebooks into the page. The two are separate because they have
different readers, different rules and different cadences — a consolidation
follows a batch of runs, an export follows a batch of consolidations.
