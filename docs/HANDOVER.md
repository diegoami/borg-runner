# Handover

**Written 2026-11-10 (second session of the day), for the next session,
whichever model and whichever harness that is.** Read
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
session needs lives in a conversation, and that is a rule now, not an accident.

**If you are here to play rather than to maintain**, this file is not yours:
read `PLAYGAME.txt` (or `CONTINUEGAME.txt`), `manuals/INSTRUCTIONS.md` and
your own `agents/<family>/` pages, and nothing else from this repository.
A player's judgement has to be independent of the maintainer's (D9). Note the
prompts changed today: **a run now starts in a worktree on a branch of its
own** - see "The worktree model" below.

## Where the work stands

- **18 runs archived** in `records/`, one played by a person (`diego-1`).
  Deepest: depth 7 (`sonnet-2.2`). **Six deaths**, none of them a big
  hit: three low-CON characters, the Warrior that stood still beside its
  Word of Recall, the Druid that met crows with no escape in its pack, and
  the Warrior that walked a 60-key chain into a breeder pack.
- **The dashboard** is <https://diegoami.github.io/borg-runner/>, rebuilt by
  `overview` on the main checkout and published by pushing `main`. It leads
  with **characters**, not runs: multi-life characters have a page under
  `records/characters/`, single-life ones link their replay.
- **450 fast tests** (`pytest -q`). The slow ones build and play the game
  (`pytest -q -m slow`); CI does not run them.
- **One run is playing**: `mmf-mage.3` (the mage carry-on) in
  `/home/diego/projects/mmf-mage.2-next`, depth 1. It was started before
  the flush rule below, so it plays on with the buffer kept (D17).
- **Every death report shows the death.** The reports of all six dead runs
  carry the frames the game drew *between* the asks; `minimaxflash-3`'s
  scrubber plays the spider killing it.

## The worktree model (new today)

**A run plays in a worktree on a branch of its own** (`git worktree add`,
`run/<name>`), builds there, and finishes by committing `records/`,
`knowledge/` and its `agents/` section on the branch and pushing it. It does
**not** rebuild the dashboard and does **not** merge. The reasons: a run
never shares a working tree with another run or with maintainer work, and
two runs never race for the same files at commit time.

**Merging run branches is maintainer work, done when nothing is playing:**

```sh
git merge run/<name>                 # agents/ and knowledge/ merge=union
.venv/bin/python -m borg_runner overview
git add records/OVERVIEW.md records/overview.html index.html
git commit -m "overview: <run>" && git push
```

`agents/**/*.md` and `knowledge/*.md` carry `.gitattributes merge=union`, so
two runs of one family that appended sections both survive the merge. The
**append rule keeps its teeth**: players append sections, never rewrite;
folding sections into the page bodies is still a nothing-is-playing task.

## The one structure to understand: where knowledge lives

| Where | What it is | Who reads it |
|---|---|---|
| `manuals/INSTRUCTIONS.md` (+ `_2` for depth 5-20) | **the page**: the game's manual and a strategy manual distilled, with what runs found folded in, every line labelled FACT / OBSERVED / POLICY / UNTESTED and sourced | every player, before its first keypress |
| `knowledge/<run>.md` + `records/<run>/` | the **evidence**: each run's own notebook, decisions, keys and replay | a consolidating session; a player only for a line it wants to check |
| `agents/<family>/COMMON.md` and `<CLASS>.md` | the **playbook**: one model family's own account, written for its own next session | that family only |
| `ACCUMULATED_KNOWLEDGE.md` | the **export**, outward to borg-reborn-rs; nothing the manuals already say. **Edition 5** covers all 18 runs. `ACCUMULATED_BEHAVIOUR.md` is its companion: who is worth imitating, by character level and net worth, lineage first. The owner calls this the reason the repository exists - its correctness outranks everything else here | the consumer, not players |
| `prompts/` | the **briefs** worth running twice. A brief is an objective added to `PLAYGAME.txt`, never a replacement | one player each |

**A tip lives on the page, not in a prompt.** `borg_runner prompts` enforces
it: a labelled claim in a prompt must carry an anchor and that anchor must be
on the page; a quoted page section must still exist; a brief must name the
template it extends.

## Every check, and what each one refuses

```sh
.venv/bin/python -m pytest -q                         # 450, includes the page check
.venv/bin/python -m borg_runner prompts               # nothing is said only in a prompt
.venv/bin/python -m borg_runner playbook --check      # layout, and spell numbers vs class.txt
.venv/bin/python -m borg_runner consolidate --check   # every claim on the page names a real run#ask
.venv/bin/python -m borg_runner consolidate           # the recurring themes, and whether the page answers them
.venv/bin/python -m borg_runner export --check        # the export cites real runs and names its consumer
.venv/bin/python -m borg_runner tools --check         # a shared tool parses and says where it came from
.venv/bin/python -m borg_runner audit --all           # what every archived run left behind
```

The page check (`borg_runner.instructions`, driven by
`tests/test_instructions.py`) parses claims out of the page's own sentences
and looks them up in `vendor/` at the pin - **775+ claims on volume one**,
with floors per kind and doctored rows that prove it can fail. It caught
three errors in this session alone, and its grammar had to follow two of
this session's legitimate page edits (the lock-arithmetic phrasing, and an
obsolete rule that pinned volume 2 to volume 1's wrong Recall cell). **When
a page edit is right and the check fails, read the failure twice: it may be
the grammar that is stale, not the page.**

## The two things that changed the game today

**One answer per ask.** `minimaxflash-3`'s decisions log answered asks 27 and
56 twice (a session re-answer appended much later); the game had consumed the
first answers, and every replay diverged from the record at exactly that
point. `minimaxflash-2.2` had the same at ask 329. Now: `answer` refuses a
second answer; `recorded_keys` and the record's key stream (input.txt) take
the played (first) answer and name the rest in `duplicate_answers`; the audit
warns on a
re-answered log; a replay regenerates its scratch directory; the splash's git
describe is not a screen difference (build identity lives in the record's
hashes). All 18 runs replay `identical: true` under this.

**The frame dump.** The frontend used to write the screen only when the key
buffer emptied, so everything the game showed while spending a buffered
string - which is where deaths happen - was recorded nowhere. With `-f<dir>`
it writes `frame-<ask>-<n>.txt` at every input event; `play` and `autoplay`
turn it on for every new run, `replay --frames` recovers it for old ones,
and the report's scrubber splices the frames into their ask (collapsing
unchanged runs). The slow test replays a game with the dump on and off and
diffs every ask byte for byte.

## What this session changed, in short

1. The page consolidated `mmf-mage.2` (rest out the Recall timer; gold is
   picked up by stepping but an object takes `g`; a level's monsters are
   few, asleep and distant).
2. A consistency pass over every player-facing document (PR #2): the export
   first (its edition-3 header, corpus table and tallies now agree), then
   the page (the early sections no longer teach the retracted one-staircase
   model; lock arithmetic; the real rest-to-full keys; Recall-from-town is
   DL1; the birth Scroll of Word of Recall is named), then seven stale
   numbers in `agents/minimax/`, corrected where they stand with the date on
   each. One proposed fix was **rejected with proof** (walking onto a shop
   does open it - `player_handle_post_move`; the review's grep had missed
   the cross-file call).
3. Record integrity and the frame dump (PR #4), above.
4. `archive` reconciles scripts a player wrote **loose in the run directory**
   into `tools/` (a druid wrote its walk-planner beside the record, and only
   `tools/` was archived); the audit warns when one is left behind.
5. The worktree prompts, above.
6. The export was **edition 4** at that point; it is **edition 5** now.
7. **T11, decided and built: the game ends a key string** (D17, below).
8. `mmx-war-1` and `mmx-pri-1` merged, both replay `identical: true`
   (141/141 and 149/149 asks, 0 differences) and both audit clean (20/20 and
   19/19); their worktrees are removed.
9. **The two shared tools that were worth adopting**:
   `tools/screen/open.py` (unseen ground per direction) and
   `tools/screen/route.py` (a route from an explicit start, and the rubble
   correction), both from `minimaxflash-3`. The beam-search planners, the
   sweep and the `where` helper were read and left in their records: they
   hold a routing or depth-1 tactic the library is not supposed to have.
10. **Edition 5 of the export** and **edition 2 of the companion**; the
    dashboard and `records/OVERVIEW.md` lead with characters.
11. The `-again` runs renamed to the lineage convention
    (`minimaxflash-1.2`, `sonnet-2.2`).
12. **The throw mystery solved.** `mmx-war-1`'s four wasted decisions were
    not a throw bug: it answered the `[` monster list with `v` `a` `'`, the
    list ate `v`, `a` ran Aim a wand, and `'` only set a target. The page
    now names the monster list in its "a key is swallowed" rule, and the
    export's row says what the frames show.

## T11: the flush rule, and why old runs still replay

The game flushes input when it disturbs the player (`disturb()` raises
`EVENT_INPUT_FLUSH`). The frontend used to keep the rest of the buffer, so
every key an agent sent was spent and recorded - and two characters died
inside a string they could not stop (T11, D17). It now honours the flush:
the rest is dropped and the agent is asked again.

A recording is replayed under the rule it was made under. The started and
record files carry `flush: honour|keep`; a run with no field was made
before 2026-11-10 and is `keep`. `-k` on the frontend restores the old
behaviour for its replay, so the corpus stays byte-for-byte reproducible.
A carried-on character keeps the rule it was born under. **Verified:** both
new runs replay identically under the new build with `-k`.

## What is waiting, in order

1. **`mmf-mage.3` is still playing** (depth 1). Let it finish, merge
   `run/mmf-mage.3`, then rebuild the dashboard on main. It plays under the
   old flush rule, by design.
2. **The coverage measurement nobody has made** (ACCUMULATED section 8,
   question 2): how much of a level a sweep actually remembers, counted off
   `minimaxflash-1.4`'s replay rather than believed.
3. **Offered and not taken up**: CI for `pytest -m slow`, and an Angband MCP
   server.

## Rules that are not obvious and have each cost something

- **The frontend holds no tactics** (D2). A grep of `patch/src/main-agent.c`
  for `hit_point`, `danger`, `monster`, `inventory`, `spell` is a test; keep
  even comments free of them.
- **No API keys, no provider config** (D8). The session is the player.
- **A player may read its own history, never another run's transcript of its
  own seed** (D9).
- **An ask is answered once.** The game pressed the first answer; a second
  one can only poison the record. `answer` refuses it; the notebook is where
  a better plan goes.
- **`playbook --append` for players, always; folding is for a session with
  nothing playing.** The branches union-merge; rewrites do not.
- **Use explicit git paths, never `git add -A`.**
- **Attribution**: at most the single `Co-Authored-By:` line your own
  harness tells you to add, and no other AI attribution.

## The two prompts, which are the product

`PLAYGAME.txt` (new game) and `CONTINUEGAME.txt` (carry one on) are what a
harness is handed, with `{RUNNAME}`, `{SEED}` and `{AGENT}` substituted;
`docs/BRIEF.md` is the same thing at length. They now open with the worktree
setup, carry the five finish commands (record, stop, keep, archive, commit
on the branch), and end with `audit`. If you change them, run
`borg_runner prompts`.
