# Plan

One milestone at a time. A task is done when it runs, is tested, and the
document that describes it says what was *not* checked.

## Milestone 1: the loop

| # | Task | Status |
|---|---|---|
| T01 | Pin the tree, build it `--disable-borg` with `-mtest`, prove the build is reproducible | todo |
| T02 | The hook: screen out, keys in, fed from a buffer (`patch/`) | todo |
| T03 | The run: seed, cap in keypresses, the question/answer files a session answers | todo |
| T04 | The record: seed, build identity, every key, every screen, the agent's memory and reason | todo |
| T05 | The brief a session reads before it plays, and the manuals' pins | todo |

**Gate:** a session plays a game from birth to a death or a cap, and the
recording replays to the same screens.

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
