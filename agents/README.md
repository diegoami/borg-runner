# agents/ — what each model family has learned, in its own words

`manuals/INSTRUCTIONS.md` is the repository's memory: the manuals distilled,
with what runs measured folded in as **OBSERVED** lines that name the runs
that saw each one as `run#ask`. Nothing in it belongs to anybody.

This directory is the other kind of memory. **One directory per model family,
written by that family for its own next session.**

```
agents/<family>/COMMON.md      what any run of that family should know
agents/<family>/<CLASS>.md     the part that is only true of one class
```

`<family>` is a model family, not a provider and not a version — `minimax`,
not `minimax/MiniMax-M2.7`. The point is continuity between sessions of the
same model, which a version bump does not break. `<CLASS>` is one of the
game's own nine classes in capitals: `DRUID.md`, `WARRIOR.md`. A class page is
written once there is enough to say; a family with one life of one character
has a `COMMON.md` and nothing else.

Both prompts name it. Whoever starts a run passes `AGENT=<family>` along with
the run name, the run reads these pages before its first keypress, and writes
back to them before the finishing commands — the same order as the write-up,
and for the same reason: a step after `archive` is a step that does not
happen.

```sh
.venv/bin/python -m borg_runner playbook                          # every family
.venv/bin/python -m borg_runner playbook --family minimax --class Druid
.venv/bin/python -m borg_runner playbook --family sonnet --start sonnet-4
.venv/bin/python -m borg_runner playbook --check                  # the layout
```

A run says which family's pages it used with `record --playbook <family>`, so
the record carries it; `archive` then says whether the run wrote anything back
or left the next session where it started.

## What belongs here, and what does not

| | |
|---|---|
| `manuals/INSTRUCTIONS.md` | the manuals distilled, plus what runs measured as OBSERVED lines. Has to hold for any player. |
| `knowledge/<run>.md` and `records/<run>/` | the evidence under those lines: that run's own notebook, its decisions and its replay. |
| `agents/<family>/` | one family's own account: what it measured, what cost it asks, what it got wrong. |

So a line like *"a down staircase is `>` and `l>g` walks to one"* belongs in
INSTRUCTIONS, where any player benefits from it. A line like *"I keep losing track of
what I am carrying because I will not spend an ask on `i`"* belongs here: it is
true of one player and useless as a general claim.

Three rules for writing one:

- **Fold it in; it is not a log.** A page a session cannot read whole is a
  page it will skim. A line that turned out to be wrong gets corrected where
  it stands rather than contradicted further down.
- **Name the runs.** Every claim says which run it came from, so a reader can
  check it against `records/`. `playbook --check` fails a page that cites no
  run at all.
- **Write only your own.** Another family's directory is open to read —
  knowledge is not private here, and it is worth opening when you inherit
  their character — but editing it would put words in another player's mouth,
  and each page says in its first lines whose experience it is.

## When several runs of one family play at once

They all write these same pages, and the last whole-file rewrite erases the
others — the same failure that once destroyed a run's own report here. So a
run adds its part instead of rewriting:

```sh
python -m borg_runner playbook --family minimax --append - --from minimaxflash-3 <<'MD'
## What I measured

...
MD
```

`append` takes an exclusive lock, re-reads the page inside it, and puts the
text under `## From \`<run>\`, <date>`, so two runs finishing in the same
second both survive. `.gitattributes` gives these pages `merge=union`, so two
commits of two appends merge rather than stopping a rebase. And
`playbook --family <family>` says how many games are in progress before you
write, plus how many appended sections are waiting.

**Folding those sections into the body is separate work**, for a session with
nothing playing: that is where a page stays readable whole, which is the only
property that makes it worth reading at all.

## Borrowing, when your family has nothing yet

A family's first run of a class has no page of its own, and should not start
from nothing: the same class may already have been played by somebody else.
`playbook --family <yours> --class <class>` answers a missing page with every
other family's page for it —

```sh
$ python -m borg_runner playbook --family codex --class Druid
agents/codex/COMMON.md           - does not exist yet …
agents/codex/DRUID.md            - does not exist yet …
agents/minimax/COMMON.md     380 lines   borrow: everything that family has learned
agents/minimax/DRUID.md      315 lines   borrow: their page for the Druid
```

— and says so when no family has written about that class at all, which means
the run is the first and the page is its own to write. A borrowed page is read
the way one player reads another: its numbers are its own. What a run takes
from one, and whether it held, goes in **its own** pages when it stops,
naming where it came from.

## What is here now

`minimax/` — four lives: three of one High-Elf Druid on seed 23
(`minimaxflash-1`, `minimaxflash-1-again`, `minimaxflash-1.3`) and one of a
Gnome Mage on seed 41 (`minimaxflash-2`), written by the player of those runs:
[COMMON.md](minimax/COMMON.md), [DRUID.md](minimax/DRUID.md) and
[MAGE.md](minimax/MAGE.md).
