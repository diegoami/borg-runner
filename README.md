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
Follow the prompt in /home/diego/projects/borg-runner/PLAYGAME.txt — RUNNAME=gnome-1, RACE=Gnome, CLASS=Mage
Follow the prompt in /home/diego/projects/borg-runner/CONTINUEGAME.txt — FROM=minimaxflash-1-again
```

[PLAYGAME.txt](PLAYGAME.txt) starts a new game: the reading, the loop, the
rules and what to run when it stops. Give it a `SEED` as well to play a
dungeon another run has played, or leave it out and it picks an unused one and
records which. Give it a `RACE` or a `CLASS` to test one deliberately — a
class no run has drawn, say — and the record marks the character as chosen
rather than drawn, and says whether the player managed to be born as asked.
Omitted, the character is drawn, which is the default for a reason: a model
left to choose picks the class it reasons best about every time, and its notes
then read as general when they are one class's. [CONTINUEGAME.txt](CONTINUEGAME.txt) carries a stopped run on
from where it left off, with that character's level, gear, wounds and notes —
and with **its own history**. A lineage is `<base>.<generation>` —
`rogue-1`, `rogue-1.2`, `rogue-1.3` — and `carry-on` picks the next name
itself, so nobody types `-again-again`. The base names the character for its
whole life. Its history: `borg_runner history --run X` lists every run
the character has lived through, oldest first, and the continuation is told to
read each of their write-ups. The notebook carries what a character learned;
the write-ups carry what it *did*, and nothing else records that.

**Runs do not interfere.** Each owns its directory, game process, seed,
character and notebook; several play at once, and that is how a claim gets a
second witness (D15). The names must differ, or the tool refuses and says
which run holds the name.

When a run stops it publishes itself — the prompts end with the five commands
that do it:

```sh
.venv/bin/python -m borg_runner stop --run runs/mine               # it saves and quits
.venv/bin/python -m borg_runner record --run runs/mine --played-by … --model …/…
.venv/bin/python -m borg_runner keep --run runs/mine        # its notes into knowledge/
.venv/bin/python -m borg_runner archive --run runs/mine     # keys, notes, and its replay page
.venv/bin/python -m borg_runner overview                    # the dashboard, all three files
git add records knowledge index.html && git commit -m … && git pull --rebase && git push
```

`archive` generates that run's replay; `overview` rebuilds
`records/OVERVIEW.md`, `index.html` and `records/overview.html` from the
records; the push is what puts it on the site. To rebuild every replay after
changing the page itself, `borg_runner report --all`.

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

One of the runs in `records/` was **played by a person** (`diego-1`, a Kobold
Priest), converted from a borg-rs recording by
[tools/replay_from_borg_rs.py](tools/replay_from_borg_rs.py) so that it sits in
the same table and the same viewer as the model runs. It is marked
`none/human` and its `source.json` says what it is and what it is not: a
different build, no seed-and-keys recording, so this repository cannot replay
it — the screens in its replay are the recording reconstructed. Comparing a
person with a model on the same game is the point of keeping it.

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
