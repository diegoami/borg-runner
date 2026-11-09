# Design

Every decision here is the owner's, taken on 2026-11-09, and each says what it
rules out. Where something is still open it says so rather than guessing.

## D1. The game is plain Angband 4.2.6, built without the Borg

The pinned tree is `angband/angband` at `e473720` — upstream 4.2.6, the same
commit borg-agent calls its `original` pin, so a run here and a Borg run are
playing the same game.

It is configured `--disable-borg`. That is not decoration: `ALLOW_BORG` is what
defines `inkey_hack` in `src/ui-input.c:130`, the hook the Borg steals the
keyboard with. With the Borg out, **no Borg code is in the binary**, no
`borg.txt` is read, and no munchkin or lunal setting exists on our path. When
this repository says a model played the game, there is nothing else in the
process that could have played it.

*Ruled out:* attaching to the Borg's hook, which is what borg-agent does. It is
the proven path and it was rejected on purpose — the point is a player with no
Borg in it.

## D2. Our own hook, and the headless frontend

One patch, applied to the pinned tree at build time and kept in `patch/`:

- a hook of our own in `src/ui-input.c`, outside the `ALLOW_BORG` guard, called
  from `inkey_ex()` exactly where the Borg's was;
- the frontend is `main-test.c` (`-mtest`), which borg-agent already builds
  headless, so the terminal exists as a grid in memory with no display.

The hook does three things and holds no opinions: write the screen, read keys,
feed them one at a time. **It never decides anything**, which is what keeps a
finding about the game from being a finding about us.

## D3. The round trip is screen out, keys in

When the game wants a key and our key buffer is empty, the hook writes:

- the **screen, 80x24, verbatim** — the character line, the map, the messages,
  any prompt, exactly as a person would see it;
- the turn and the depth, read from the screen like everything else;
- nothing else. No parsed map, no monster list, no inventory, no status flags.

The answer is **a string of keys** and, optionally, the agent's updated memory.
The keys are fed from a buffer, so a multi-key command (`v` then an item letter
then a target) is one round trip, not three.

*Ruled out:* a structured observation. borg-agent has one (`observation@1`) and
it is good; it also decides for the model what matters, and the run on
2026-11-09 showed that is where the bias enters.

## D4. The memory is the agent's, and it lives in the prompt

The agent presses `i` once and **remembers** the inventory. It presses `e` and
`b` once and remembers those. Thereafter it assumes an item is still there
unless it burnt, dropped, used or lost it — and when it is unsure, it spends a
keypress to look rather than guessing.

That memory is **the agent's own note, carried in the prompt**. The harness
does not maintain it, does not correct it and does not parse the screen to
check it. Two reasons:

1. a wrong belief about one's own inventory is a real failure mode of a player,
   and if the harness fixes it silently we can never see it;
2. anything the harness maintains is a thing the harness has an opinion about.

Mechanically: each answer may carry a `memory` field; the newest one is put in
the next prompt. It is recorded with the run, so the report can show **what the
agent believed at the time** beside what was actually true — which is where the
sharpest leads come from.

*Open:* whether the memory is rewritten whole each time or edited. Rewriting is
simpler and costs output tokens; editing is cheaper and drifts. Start with
"send it only when it changes" and measure.

## D5. Keypresses are the budget, and the game's own commands are the economy

A run is capped in **keypresses**, not game turns, because keypresses are what
a decision costs. The economy comes from the game, not from us:

| The agent presses | The game does |
|---|---|
| `.` + direction (Run) | walks until a choice or a disturbance — *its* rule |
| `R` `&` `\n` (Rest) | rests until healed or disturbed; one key, hundreds of turns |
| `p`, `<`, `>` under Autoexplore | pathfinds; the route is the game's |
| `v` + item + target | a thrown flask, resolved in one |

Measured on 2026-11-09: a rest was **940 game turns for one command**, and a
level that cost 66 single steps had a 12-step route. The lever is real.

## D6. The record is the seed and the keys

A run records the seed, the build identity (commit, patch hash, binary hash),
every key in order, every screen, and the agent's memory and stated reason per
decision. **Seed plus keys is the whole of determinism** — the same tree and
the same keys give the same game, byte for byte. That is also the format
better-borg-c's death corpus ships as `input.txt`, so a run here can be
replayed by their tools and ours.

## D7. Replay, and handing over to a person

Two modes over the same recording:

- **replay** — feed the keys, headless, and compare; this is the regression
  test that a run is exact;
- **take over** — build the same tree with a real terminal, feed the keys up to
  a chosen turn, then **release the keyboard to the person**. The game is in
  precisely the position the agent was in, with the same character and the same
  level, and the person plays on.

That is the point of recording keys rather than a transcript.

## D8. A Claude Code session is the mind, and there are no keys

No API keys, no provider configuration, no budget. The session that opens this
repository *is* the player: it reads the brief, reads the manuals, and answers
the question files. A model API driver is **not** planned; if cohorts are
wanted later, that is a decision to take then, with its cost stated.

*Consequence, stated plainly:* this repository cannot play unattended, in CI or
in a cohort of a thousand runs. It trades that for needing no secrets at all.

## D9. What the agent may read

The game's own manual at the pin (`docs/*.rst`, `lib/help/`), and the strategy
manual at its pin — seventeen chapters, ten appendices generated from
`lib/gamedata`, and a copy of the user manual. Chapter 15 says of itself that
its rules are "a starting policy to be measured, not truths", and that is how
they are treated here: following one and being hurt by it is a result.

It may **not** read another run's conclusions before playing. A fresh session
per run is the point — its judgement at a position has to be independent, or
the comparison with the Borg is worthless.

## What this repository is not

- not a Borg, and not a tuning of one: it holds no thresholds and no policy;
- not a benchmark: one run is an anecdote, and it says so;
- not a home for claims — those live in borg-agent, with its lifecycle and its
  rule that a model never promotes its own.
