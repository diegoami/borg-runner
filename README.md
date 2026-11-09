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
   carries, what it has learned and what it is trying to do. The harness
   remembers nothing on its behalf.
2. **Record** — the seed, the build, and **every key**. That is the whole
   recording; it needs nothing else to be exact.
3. **Replay or take over** — play the keys back, stop at any turn, and hand
   the keyboard to a person in a real terminal.
4. **Report** — one page per run: what happened, what it believed at the time,
   and what it would do differently.

## Why the screen, and why keys

Both were decided by the owner on 2026-11-09 after a model played a full game
through borg-agent's primitive layer, and the layer turned out to be the thing
shaping the play:

- **Four of five commands it issued were a single `walk` step.** The cost of
  this game is traversal, and the game already answers it: Run (`.`) and the
  pathfinding commands walk many squares for one key, with the *game* deciding
  when to stop. A harness that walks for you cannot use them.
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
