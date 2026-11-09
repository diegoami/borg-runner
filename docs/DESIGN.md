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

## D2. A frontend of our own, and no change to the game

Angband asks its *frontend* for input — `main-x11.c`, `main-gcu.c` and
`main-test.c` are the ones it ships. So we add one more, `src/main-agent.c`,
and the game's own code is untouched. There is nothing between the agent and
the keyboard: no process driving the game, no translation layer, nothing with
a view about how to play.

It hangs on `TERM_XTRA_EVENT`, which is the game saying "I want a key". If our
key buffer still has keys, it presses the next one. If it is empty, it writes
the screen and waits.

The three upstream files the patch edits are `CMakeLists.txt`, `src/main.c` and
`src/main.h`, and all three only to compile and register the frontend.

**Measured, not assumed** (2026-11-09): the binary built this way contains
**zero** symbols matching `borg`, and no `inkey_hack` at all — `ALLOW_BORG` is
what defines it, so with the Borg off the Borg's own hook does not exist. The
seed is set through the game's public `Rand_state_init()` from the frontend, so
even reproducibility needs no patch to the game.

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

That memory is **the agent's own note, carried in the prompt**. Nothing here
maintains it, corrects it or parses the screen to check it. Two reasons:

1. a wrong belief about one's own inventory is a real failure mode of a player,
   and if the frontend fixes it silently we can never see it;
2. anything the frontend maintains is a thing the frontend has an opinion
   about, and this one is meant to have none.

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

## D10. The exchange is plain files in the run directory

Per ask, numbered by the ask so a question and its answer always pair up:

| File | What |
|---|---|
| `screen-<n>.txt` | the screen, 24 lines, as the game drew it |
| `question-<n>.txt` | the ask number, the turn, and where to put the answer |
| `keys-<n>.txt` | **the answer**: every byte is a key to press |

The question also carries `cursor x y`. A person sees a menu's highlight as
reverse video; the screen dump is characters only, so without the cursor the
agent cannot tell which item is selected. Four escapes exist in the answer for
keys that cannot be typed into a file — `\n` Enter, `\e` Escape, `\t` Tab,
`\\` a backslash. Nothing else is interpreted.

`\n` is `KC_ENTER`, **not** carriage return. Angband's own prompts wait for
`KC_ENTER` (0x9c); a footer saying "Press Return" ignores 0x0d. The key buffer
therefore holds keycodes, not bytes.

Files rather than a pipe, for three reasons: a session answers one with a
single tool call; the run directory *is* the archive, with no separate
recording step; and a replay is a diff of screens rather than a re-enactment.

The frontend waits for its answer with no timeout. The agent's thinking time is
not the game's business, and a run that waits is better than a run that invents
a key; limits belong to whoever started the run.

## D11. One binary, two frontends

`-magent` is headless and is what plays and replays. For taking over, the same
binary is built with **X11** (`-mx11`), so the game opens a window in the
position the agent left it.

*Noted honestly:* ncurses (`-mgcu`) was the first choice, so a takeover could
happen in any terminal, including over SSH. This machine has no
`libncurses-dev`, and installing it needs the owner. X11 works today because
borg-agent's tests already need `libx11-dev`, and WSLg displays it.

## D12. A run owns its savefile, and the character name is part of the game

Both of these were found by replaying a run and getting a different game.

- **The savefile.** Angband loads a savefile of the character's name if one is
  there, so the first replay resumed at turn 41 instead of being born. A run
  therefore deletes any savefile of its name before it starts, and copies its
  own into `<run>/save` when it finishes. The build tree's `lib/save` is
  scratch space. (`-dsave=` is accepted by the game and then ignored for the
  savefile's own path, so it is not used.)
- **The name.** It is passed as `-u` and the birth prompt arrives with it
  already filled in, so it *shows on the screen*. A replay reuses the
  original's name rather than its own directory's, or the screens differ at
  birth. It is recorded for that reason.

## What running it taught, 2026-11-09

Each of these was a bug or a blind spot found by playing, not by reading:

| What | Why it mattered |
|---|---|
| the cursor was invisible | the agent could not tell which menu item was highlighted, so birth was unplayable |
| `\n` was carriage return | "Saving game... done. Press Return" sat there for ever; the game wanted `KC_ENTER` |
| stopping terminated the game | it was killed while waiting to be asked, so the savefile — the one thing takeover needs — was never written |
| the savefile was inherited | the replay resumed instead of being born, and reported every screen as different |
| the run name reached the screen | a replay under another name differed at the name prompt |

All five are the same shape: **the screen and the keyboard are the only
contract, and anything we assume about them has to be checked against the
game.** That is the argument for keeping this frontend as small as it is.

## What this repository is not

- not a Borg, and not a tuning of one: it holds no thresholds and no policy;
- not a benchmark: one run is an anecdote, and it says so;
- not a home for claims — those live in borg-agent, with its lifecycle and its
  rule that a model never promotes its own.
