# borg-runner

**A language model plays Angband from the screen, one key at a time, and the
run is recorded so it can be replayed or taken over by a person.**

It exists to produce something that does not exist yet: **deaths and descents
of a player that reads the manual.** Angband's built-in Borg has a knowledge
problem that is hard to study from its own games — with its munchkin start off
it stops descending, and with it on its deaths are of a mode nobody wants to
keep. A model that reads the manual descends, dies, and can say why.

Those runs are the input for [borg-agent](https://github.com/diegoami/borg-agent)'s
death analyser and, through it, for the Rust
[borg-rs](https://github.com/diegoami/borg-rs).

## Running one

Two files are the entry points. Hand either to any harness — Codex, a Claude
session, a terminal — as one line, with the placeholders filled in:

```
Follow the prompt in /home/diego/projects/borg-runner/PLAYGAME.txt — RUNNAME=codex-1
Follow the prompt in /home/diego/projects/borg-runner/CONTINUEGAME.txt — FROM=sonnet-2-again
```

[PLAYGAME.txt](PLAYGAME.txt) starts a new game: the reading, the loop, the
rules and what to run when it stops. Give it a `SEED` as well to play a
dungeon another run has played, or leave it out and it picks an unused one and
records which. [CONTINUEGAME.txt](CONTINUEGAME.txt) carries a stopped run on
from where it left off, with that character's level, gear, wounds and notes.

**Runs do not interfere.** Each owns its directory, game process, seed,
character and notebook; several play at once, and that is how a claim gets a
second witness (D15). The names must differ, or the tool refuses and says
which run holds the name.

While they play, from anywhere:

```sh
.venv/bin/python -m borg_runner status     # depth, asks, pace, dead or alive
.venv/bin/python -m borg_runner overview   # the table of every archived run
```

The table is also a page: **<https://diegoami.github.io/borg-runner/>**, where
each run links to a replay you can step through, screen by screen.

By hand, the whole of it is:

```sh
.venv/bin/python -m borg_runner play --seed 7 --name mine
.venv/bin/python -m borg_runner wait --run runs/mine
.venv/bin/python -m borg_runner answer 1 ' ' --run runs/mine --reason "past the splash"
```

## The loop

```
          the game asks for a key
                    │
          the screen, 80x24, verbatim      ← nothing is parsed for the agent
                    │
             the agent decides             ← the manual, and its own memory
                    │
          a string of keys, and its        → recorded
          updated memory of the world
                    │
    the keys are fed until the game asks again
```

Four parts, and nothing else:

1. **Play** — the agent sees the screen and sends keys. It reads the game's
   manual and a strategy manual, and it keeps its **own** memory of what it
   carries, what it has learned and what it is trying to do. Nothing here
   remembers anything on its behalf.
2. **Record** — the seed, the build, and **every key**. That is the whole
   recording; it needs nothing else to be exact.
3. **Replay or take over** — play the keys back, stop at any turn, and hand
   the keyboard to a person in a real terminal.
4. **Report** — one page per run: what happened, what it believed at the time,
   and what it would do differently.

Two things are **kept in git**, and the run directory is not one of them:
`records/` holds each run's seed, **every key**, the reasons and the notes —
everything that cannot be regenerated. The screens are left out because
`replay` reproduces them byte for byte from the seed and the keys, which is
the whole claim of D6. And `knowledge/`. A run directory is scratch — git
ignores it, and the seed plus the keys reproduce it exactly. The **notebook**
is the only part that is not reproducible, because it is what the player
worked out, so `keep` promotes it into `knowledge/` with its provenance: the
seed, the build, the depth reached and the hashes. A later run starts from it
with `play --notebook`, and then the question is whether it gets deeper.

## Why the screen, and why keys

Both were decided by the owner on 2026-11-09 after a model played a full game
through borg-agent's primitive layer, and the layer turned out to be the thing
shaping the play:

- **Four of five commands it issued were a single `walk` step.** The cost of
  this game is traversal, and the game already answers it: Run (`.`) and the
  pathfinding commands walk many squares for one key, with the *game* deciding
  when to stop. Anything that walks for you cannot use them.
- **29% of that run was lost to one tie** broken by the direction order of our
  breadth-first search — our bug, reported as if it were gameplay.
- Monster health and sleep came through as `null`, the level feeling arrived as
  prose rather than the `LF:` digit the strategy manual asks for, and there was
  **no `fire` command at all**, so a launcher was unreachable. On the screen
  all three are simply there, and `f` is simply a key.

So: no primitives, no executor, no observation schema. The screen is the state,
the keyboard is the action, and every judgement belongs to the model.

## Status

**Being set up (2026-11-09).** See [PLAN.md](PLAN.md) for what exists.
