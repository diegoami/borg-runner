# Plan

One milestone at a time. A task is done when it runs, is tested, and the
document that describes it says what was *not* checked.

## Milestone 1: the loop

| # | Task | Status |
|---|---|---|
| T01 | Pin the tree, build it `--disable-borg`, keyed by commit and patch hash | **done** |
| T02 | `src/main-agent.c`: screen out, keys in, fed from a buffer | **done** |
| T03 | The run: seed, cap in keypresses, the question/answer files a session answers | todo |
| T04 | The record: seed, build identity, every key, every screen, the agent's memory and reason | todo |
| T05 | The brief a session reads before it plays, and the manuals' pins | todo |

**Gate:** a session plays a game from birth to a death or a cap, and the
recording replays to the same screens.

**T01 and T02, checked 2026-11-09:** the binary has **zero** `borg` symbols
and no `inkey_hack`; the game runs `-magent -- -d<dir> -s<seed>`, writes the
splash screen verbatim, waits for `keys-1.txt`, and on a single space advances
to the birth menu — which the agent answers with keys, like a person, so there
is no birth automation to write. Not checked yet: that a full game replays to
identical screens (T06), and anything about X11 takeover (T07).

## Milestone 2: replay and take over

| # | Task | Status |
|---|---|---|
| T06 | `replay --run D` — feed the keys headless and compare every screen | todo |
| T07 | `takeover --run D --at-turn N` — a real terminal, the keys to turn N, then the keyboard | todo |

## Milestone 3: the report

| # | Task | Status |
|---|---|---|
| T08 | One page per run: the timeline, the screens, and **what the agent believed** beside what was true | todo |
| T09 | The leads section: what it would do differently, with the turn and a test | todo |

## Not planned

- An API-key driver, or a cohort runner (D8).
- Any claim store, probe or knowledge base: those are borg-agent's.
- Any tuning of the Borg: this repository has no opinion about how to play.
