# Plan

One milestone at a time. A task is done when it runs, is tested, and the
document that describes it says what was *not* checked.

## Milestone 1: the loop

| # | Task | Status |
|---|---|---|
| T01 | Pin the tree, build it `--disable-borg`, keyed by commit and patch hash | **done** |
| T02 | `src/main-agent.c`: screen out, keys in, fed from a buffer | **done** |
| T03 | The run: start, ask, answer, stop, and the files a session answers | **done** |
| T04 | The record: seed, build identity, every key, every screen, the memory and reason | **done** |
| T05 | [docs/BRIEF.md](docs/BRIEF.md), the brief a session reads before it plays | **done** |

**Gate, met 2026-11-09:** a character is born from the screen (the letter
moves the menu highlight, `\n` selects), plays, saves and quits with exit 0,
and the recording — twelve asks, twenty-one keypresses — **replays
byte-identically**, `identical: true`. `2222` in one answer spent four keys
and moved the game from turn 1 to turn 41, so the key buffer earns its keep.

**Still only a smoke test:** nobody has played a real game through this yet.
The next thing is a session that plays until it dies.

**T01 and T02, checked 2026-11-09:** the binary has **zero** `borg` symbols
and no `inkey_hack`; the game runs `-magent -- -d<dir> -s<seed>`, writes the
splash screen verbatim, waits for `keys-1.txt`, and on a single space advances
to the birth menu — which the agent answers with keys, like a person, so there
is no birth automation to write. Not checked yet: that a full game replays to
identical screens (T06), and anything about X11 takeover (T07).

## Milestone 2: replay and take over

| # | Task | Status |
|---|---|---|
| T06 | `replay --run D` — feed the keys headless and compare every screen | **done** |
| T07 | `takeover --run D --at-turn N` — replay to the turn, save, open it in X11 | **done** |

**Gate, met 2026-11-09:** `takeover --at-turn 20` replays identically, stops,
saves, and prints the command that opens that savefile in X11. Takeover needs
no new C at all: the game saves on Ctrl-X, so the person opens the same
savefile and carries on. **Not tried by a person yet** — the X11 window has
not been opened from a takeover.

## Milestone 3: the report

| # | Task | Status |
|---|---|---|
| T08 | One page per run: the timeline, the screens, and **what the agent believed** beside what was true | **done** |
| T09 | The leads section: what it would do differently, with the turn and a test | todo |

**First real game, 2026-11-09.** A Sonnet agent played seed 7 from the screen:
**125 asks, 644 keypresses, 4,659 game turns, depth 1, character level 3,
alive.** It killed Fang at CL2 with two thrown flasks of oil in a corridor,
and never found a down staircase on either level it explored. It kept
**eleven notes**, one of which corrects an earlier note of its own with the
evidence that disproved it.

The next question is T10: give a second run that notebook and see whether it
gets deeper.

| # | Task | Status |
|---|---|---|
| T10 | Carry a notebook into a later run, and measure whether depth rises | **done** |
| T11 | Decide whether the game's own disturbance flushes the key buffer | todo, owner's call |

**T10, 2026-11-09.** Three runs, same frontend and manual. `sonnet-1` on seed
7 with nothing inherited reached depth 1 in 125 asks. `sonnet-2` on the same
seed, inheriting its notes, reached **depth 6** — but by reading an unknown
scroll that happened to be Deep Descent, which the inherited cheat sheet told
it to try. One scroll is not a result. `sonnet-3` on seed 11 inherited the same
notes, chose a Mage for the level-1 stair-detection spell, found the staircase
at once, and then **died on depth 1** to a small kobold. Depth rose, the cause
was luck, and the knowledge demonstrably changed how all three played.

**T11, the open question the death raised.** `sonnet-3` was confused by a gas
trap and then spent sixteen "hold" keys in a single ask while a wounded kobold
was next to it. It had no way to stop part way through, and died at ten hit
points.

The frontend currently ignores `TERM_XTRA_FLUSH` on purpose
(`patch/src/main-agent.c:214`): the game raises it when the player is
disturbed, and we keep the buffer so that nothing the agent asked for
disappears without record. Honouring it instead would mean **the game**
decides when a key string is abandoned — which is exactly D5's "the game's own
router", and it would have saved that character — but it would also change
what a recording means, so the three runs already kept would no longer replay
under the new build. That is the owner's call, not a session's.

## Not planned

- An API-key driver, or a cohort runner (D8).
- Any claim store, probe or knowledge base: those are borg-agent's.
- Any tuning of the Borg: this repository has no opinion about how to play.
