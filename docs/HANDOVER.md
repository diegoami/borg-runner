# Handover

**Written 2026-11-10 by the session that did the work below. It is for the
next session, whichever model and whichever harness that is.** Read
[AGENTS.md](../AGENTS.md) first (it says which of the two jobs you are here
for), then this file, then [PLAN.md](../PLAN.md) and
[docs/DESIGN.md](DESIGN.md).

Nothing below assumes what you are. Where a step needs a convention of your
own - how you run a shell command, how your commits are attributed, whether
you have a browser - follow yours; the repository cares about the files you
leave, not the tool that wrote them. The one thing it does assume is that you
can run `.venv/bin/python` from the repository root, which AGENTS.md sets up
in four commands.

Everything described here is **in the repository and pushed**. Nothing a
session needs lives in a conversation, and that is a rule now, not an accident:
see "A tip lives on the page" below.

**If you are here to play rather than to maintain**, this file is not yours:
read `PLAYGAME.txt` (or `CONTINUEGAME.txt`), `manuals/INSTRUCTIONS.md` and
your own `agents/<family>/` pages, and nothing else from this repository.
A player's judgement has to be independent of the maintainer's (D9).

## Where the work stands

The frontend works and is not where the open questions are. What is open is
**knowledge**: what a player is told before its first keypress, and whether
that changes how it plays.

- **13 runs archived** in `records/`, one of them played by a person
  (`diego-1`). Deepest: depth 7 (`sonnet-2-again`). Three deaths, all of them
  characters below zero on constitution, none of them to a big hit.
- **The dashboard** is <https://diegoami.github.io/borg-runner/>, rebuilt by
  `overview` and published by pushing `main`.
- **430 fast tests** (`pytest -q`). The slow ones build and play the game
  (`pytest -q -m slow`), and CI does not run them today - an offer the owner
  has not taken up.
- One run is **still playing** as this is written: `minimaxflash-3`, a Human
  Warrior, the first Warrior of the minimax line. See "What is waiting".

## The one structure to understand: where knowledge lives

Four places, and nothing else:

| Where | What it is | Who reads it |
|---|---|---|
| `manuals/INSTRUCTIONS.md` (+ `_2` for depth 5-20) | **the page**: the game's manual and a strategy manual distilled, with what runs found folded in, every line labelled FACT / OBSERVED / POLICY / UNTESTED and sourced | every player, before its first keypress |
| `knowledge/<run>.md` + `records/<run>/` | the **evidence**: each run's own notebook, decisions, keys and replay | a consolidating session; a player only for a line it wants to check |
| `agents/<family>/COMMON.md` and `<CLASS>.md` | the **playbook**: one model family's own account, written for its own next session | that family only |
| `ACCUMULATED_KNOWLEDGE.md` | the **export**, outward to borg-reborn-rs; nothing the manuals already say | the consumer of this repository, not players |

And one more, added today: `prompts/` keeps the **briefs** worth running
twice. A brief is an objective added to `PLAYGAME.txt`, never a replacement
for it.

**A tip lives on the page, not in a prompt.** A prompt is handed to one player
and thrown away; the page is read by everyone, for ever. `borg_runner prompts`
enforces it: a labelled claim in a prompt must carry an anchor (a source
citation or a `run#ask`) and that anchor must be on the page too; a quoted page
section must still exist; a brief must name the template it extends. This
exists because a brief written for one mage carried the experience ladder, the
kill arithmetic and a corrected spell damage, and nothing else did.

## Every check, and what each one refuses

Run all of these before you commit anything that touches the page, the
prompts or the playbooks:

```sh
.venv/bin/python -m pytest -q                         # 430, includes the page check
.venv/bin/python -m borg_runner prompts               # nothing is said only in a prompt
.venv/bin/python -m borg_runner playbook --check      # layout, and spell numbers vs class.txt
.venv/bin/python -m borg_runner consolidate --check   # every claim on the page names a real run#ask
.venv/bin/python -m borg_runner consolidate           # the recurring themes, and whether the page answers them
.venv/bin/python -m borg_runner export --check        # the export cites real runs and names its consumer
.venv/bin/python -m borg_runner tools --check         # a shared tool parses and says where it came from
.venv/bin/python -m borg_runner audit --all           # what every archived run left behind
```

The page check (`borg_runner.instructions`, driven by
`tests/test_instructions.py`) is the strongest tool here: **656 claims on
volume one, each parsed out of the page's own sentences and looked up in
`vendor/` at the pin**, with floors per kind so a check cannot quietly
disappear, and doctored rows that prove it can fail. It caught three of this
session's own errors - a staircase rule that counted diagonals, a citation
written in a form it mistook for an option, and a spell's damage bonus that
does not exist.

## What this session changed, and why

1. **The page gained the arithmetic of levelling** (section 1): the
   experience ladder from `player_exp[]`, the kill award
   `mexp x monster level / your level` with its consequence (forty depth-1
   kills for a Human's CL5, most of them for the last level), and what pays
   nothing at all.
2. **"Depth is not the objective" gained the town-and-depth-1 shuttle**, named
   and priced, UNTESTED as a route to a character level.
3. **Section 8 gained the real staircase facts**: `classic_gen` and
   `modified_gen`, the only profiles at depth 1, both ask for **3 or 4 down
   staircases and 1 or 2 up**, on squares with three orthogonal walls, 16
   apart. `minimaxflash-1.4` had swept two thirds of a level for one
   staircase it believed was unique, and found none.
4. **"Constitution sets how fast you may dive"** replaced a draft written as a
   band of hit points, which "fitted nobody" (the owner's correction). CON is
   a rate - `player_hp[level-1] + adj_con_mhp x level / 100` - so the rule is
   a **pace**: gate each descent on the worst round of the depth you are
   entering (14 at depth 2 or shallower), descend one depth at a time, take
   more levels between descents when CON is low. Six class entries and both
   prompts point at it.
5. **`borg_runner prompts`** and `prompts/mage-shuttle-to-level-5.txt`.
6. **`playbook --check` now reads a family page's spell mana and dice against
   `class.txt`**, which caught `agents/minimax/MAGE.md` giving Magic Missile a
   `+3` it does not have. Corrected where it stood, with a note.
7. **`reading_note` reads a carried-on run's own notes**, not the notebook it
   inherited: `minimaxflash-1.4`'s record claimed it had read nothing for its
   class while its own note named both playbook pages.
8. **`borg_runner audit`** (added just before this session's work): what a
   finished run should have left, as 18-19 checks. Both prompts end with it.

## What is waiting, in order

1. **`minimaxflash-3` is still playing.** When it stops: `audit --run
   minimaxflash-3`, and check whether it wrote a WARRIOR.md page
   in agents/minimax/ (it would be the first Warrior page of that family).
2. **Reconcile the playbooks.** `playbook --family minimax` says *2 appended
   sections wait to be folded into the body* (`minimaxflash-2.2`,
   `minimaxflash-1.4`, plus whatever the Warrior adds). Folding is for a
   session with **nothing playing**: fold each `## From <run>` section into
   the body where it belongs, keep every run citation, correct lines that
   later runs disproved rather than contradicting them further down, then
   `playbook --check`. Three sessions of one family wrote these pages at once
   today under `playbook --append`'s lock, which is why they are appended and
   not folded.
3. **Export edition 3.** `ACCUMULATED_KNOWLEDGE.md` is at edition 2 and owes
   three runs: `minimaxflash-2.2`, `minimaxflash-1.4` and `minimaxflash-3`.
   `docs/EXPORT.md` is the process; the rule that matters is that nothing the
   manuals already say belongs in it.
4. **Start the next run.** The owner's next one is a **fresh Gnome Mage**,
   played from the **plain `PLAYGAME.txt`** with `AGENT` set to whatever
   family is playing - no brief, because the constitution rule is on the page
   now and in the prompt. Two older runs
   (`minimaxflash-1.4`'s lineage and anything else) may be carried on with
   `CONTINUEGAME.txt`.
5. **T11 is the owner's call**, not a session's: whether the frontend should
   honour `TERM_XTRA_FLUSH`. See PLAN.md - it would have saved `sonnet-3` and
   it would change what every existing recording replays to.

## Rules that are not obvious and have each cost something

- **The frontend holds no tactics, no thresholds, no opinion about how to
  play** (D2). If you are writing `if hit points below`, it belongs in the
  page or the prompt, not in the code.
- **No API keys, no provider config, no budget here** (D8). The session is the
  player.
- **A player may read its own history, never another run's transcript of its
  own seed** (D9).
- **`playbook --append`, never a rewrite, while any run is playing.** Several
  runs of one family write the same pages; the last whole-file write wins and
  erases the others. The lock and `.gitattributes merge=union` are there for
  exactly this.
- **Never commit or stash a file a live session is editing**, and use explicit
  git paths - never `git add -A`. A `git add -A` from one session swept
  another's unfinished work into a commit today.
- **A rebase can refuse** while live sessions hold unstaged `agents/` files.
  Push without pulling when you are only ahead; do not stash their work.
- **Attribution**: a commit carries at most the single `Co-Authored-By:` line
  your own harness tells you to add, naming whatever model you are, and no
  other AI attribution - no "generated with" footer in a commit message.
  `git log` shows the shape; follow your harness's line, not the last
  session's.

## The two prompts, which are the product

`PLAYGAME.txt` (new game) and `CONTINUEGAME.txt` (carry one on) are what a
harness is handed, with `{RUNNAME}`, `{SEED}` and `{AGENT}` substituted;
`docs/BRIEF.md` is the same thing at length. They now carry, besides the
procedure: that the player starts on the town's staircase, that depth is
recorded and not scored, that levelling has a price list, that constitution
sets the pace of descent, the tools library, the append rule, and `audit` as
the last step. If you change them, run `borg_runner prompts`.
