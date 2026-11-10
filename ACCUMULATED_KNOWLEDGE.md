# ACCUMULATED KNOWLEDGE — what the runs of this repository have established

Edition 1, 2026-11-10.

**Who this is for.** [borg-reborn-rs](https://github.com/diegoami/borg-rs),
the Rust Borg being rebuilt, and anyone else outside this repository who wants
what the runs learned without reading ten reports. It is an **export**: the
process that produces it is [docs/EXPORT.md](docs/EXPORT.md), and it is
rewritten from time to time, not after every run.

**Who this is not for: the players.** A run here reads
`manuals/INSTRUCTIONS.md` and its own model family's pages under `agents/`,
and is given one thing less than that — another run's account of the seed it
is playing. This file aggregates every report in the corpus, so handing it to
a player would hand them a solution key for their own dungeon. The prompts do
not mention it.

**How to read a claim.** Every one names its evidence:

| | |
|---|---|
| `sonnet-2#124` | run and ask: the screen is in `records/sonnet-2/` and the player's words in `knowledge/sonnet-2.md` |
| GAME SOURCE | read out of `vendor/angband` at the pin in `pins.json` (Angband 4.2.6, `e473720ed88a`); true of the game, not of a run |
| ONE RUN | one player saw it once. A lead, not a fact |
| N RUNS | N different runs saw it independently |

## The corpus

Ten runs, 2,332 asks, 10,403 keypresses, deepest **depth 7**, two deaths. One
session was played by a person (`diego-1`) on the same game, which is the
control. Every run drew its character rather than choosing it.

| run | model | character | depth | level | asks | turns | ended |
|---|---|---|---|---|---|---|---|
| [sonnet-1](records/sonnet-1/REPORT.md) | anthropic/claude-sonnet-5-5 | Half-Troll Warrior | 1 | 3 | 125 | 4,659 | alive, budget |
| [sonnet-2](records/sonnet-2/REPORT.md) | anthropic/claude-sonnet-5-5 | Half-Troll Warrior | 6 | 6 | 153 | 6,056 | alive, budget |
| [sonnet-2-again](records/sonnet-2-again/REPORT.md) | anthropic/claude-sonnet-5-5 | Half-Troll Warrior | **7** | 8 | 291 | 10,416 | alive, budget |
| [sonnet-3](records/sonnet-3/REPORT.md) | anthropic/claude-sonnet-5-5 | Human Mage | 1 | 1 | 47 | 1,348 | **died**, small kobold |
| [codex-1-tty](records/codex-1-tty/REPORT.md) | openai/gpt-5.6-luna | Dunadan Warrior | 1 | 1 | 66 | 1,860 | alive, in town |
| [qwen-flash-1](records/qwen-flash-1/REPORT.md) | alibaba-token-plan/qwen3.8-flash | High-Elf Druid | 0 | 1 | 73 | 570 | **died**, scruffy little dog, in the town |
| [minimaxflash-1](records/minimaxflash-1/REPORT.md) | minimax/MiniMax-M3.1-Flash | High-Elf Druid | 1 | 1 | 148 | 7,433 | alive, budget |
| [minimaxflash-1-again](records/minimaxflash-1-again/REPORT.md) | minimax/MiniMax-M3 | High-Elf Druid | 2 | 4 | 401 | 10,898 | alive, budget |
| [minimaxflash-1.3](records/minimaxflash-1.3/REPORT.md) | minimax/MiniMax-M3 | High-Elf Druid | 1 | 4 | 610 | 17,281 | alive, budget |
| [diego-1](records/diego-1/REPORT.md) | a person | Kobold Priest | 1 | 2 | 418 | 4,741 | alive, saved |

Every row links a report, and every report links a replay that can be stepped
through screen by screen. The dashboard is
<https://diegoami.github.io/borg-runner/>.

---

## 1. The cost of this game is traversal, not tactics

**This is the finding the corpus is for.** Nine of ten runs ended at depth 0,
1 or 2. Nothing killed them: eight were alive when they stopped, at full or
near-full hit points. They were still on the first level because they had not
found the way off it.

- **Walking a depth-1 level costs about 100 asks and finds nothing.** 100 of
  `sonnet-1`'s 125 asks, 148 of `minimaxflash-1`'s, 174 screens of
  `minimaxflash-1.3`'s depth 1, 4,290 of `diego-1`'s 4,741 game turns on one
  level (5 RUNS, and `diego-1` is a person doing the same thing).
- **Three in five of the human session's keypresses moved one square**
  (`diego-1`: 256 of 418 keys were single steps; the run command was used 32
  times). The model run that reached depth 7 is the one that stopped doing
  this.
- **The only deliberate descent in the corpus used the game's own
  pathfinding** (`sonnet-2-again#228`–`#230`): `l` then `>` jumps the cursor
  to a known down staircase, `g` walks the path — 11 steps and 110 game turns
  in one ask — then `>` takes it. The other descent in the corpus was a Deep
  Descent scroll read by luck (`sonnet-2#77`).
- **A run that writes its own pathfinder measures its own pathfinder.**
  `minimaxflash-1` spent 148 asks driving a 143-line breadth-first search it
  had written and never tried the game's commands (`minimaxflash-1`, its own
  report). Its next life used the game's and went further on fewer asks.

**For the consumer:** the C Borg already has the game's internal routing, so
this reads as a warning about *where the decisions go*, not about pathfinding
quality. A player that spends 80% of its decisions on floor coverage has 20%
left for everything the manuals are about. Measure asks-per-descent, not
asks-per-turn.

## 2. Finding the way down: what the generator actually does

Read out of the game rather than inferred from play, and it settles several
earlier guesses.

- **Exactly one down staircase per level**, allocated in `gen-cave.c:1583`,
  placed on a square with three adjacent walls (`gen-util.c:620`) drawn
  uniformly over the whole level (`cave_find_get_grid`, `gen-util.c:202`).
  GAME SOURCE, via `minimaxflash-1-again`. **There is no heuristic to
  exploit** — not "near the up staircase", not "in the biggest room".
- **A level is 198×66 with up to 50 rooms** (`constants.txt`,
  `dungeon_profile.txt` "classic" `params:11:50:200:2`) and the map window is
  66×22 at most. A level is roughly three screens wide and three tall. GAME
  SOURCE, via `minimaxflash-1`. This one fact explains every "I explored for
  ever and found nothing" report in the corpus.
- **The game's `>` jump finds only a staircase you have already seen**
  (`ui-target.c`, `path_nearest_known` with `square_isdownstairs`): it is a
  convenience, never a discovery (GAME SOURCE + `minimaxflash-1-again#284`,
  where the cursor did not move because nothing was known).
- **The staircase glyph is not drawn under the player.** Standing on one, the
  map draws `@` and only the status line names it (`minimaxflash-1-again#163`).
  A player scanning the map for `>` will never see the one it is standing on —
  and one run spent 148 asks beside a `>` its successor found with a single
  `l` (`minimaxflash-1-again#161`: *"You see a down staircase, 1 S, 1 W"*).
- **Aiming the cursor past the frontier beats the frontier.** In targeting
  mode the digit keys move the cursor one tile each, clamped only to the level
  bounds, and `g` falls back to a path through unknown grids when the
  destination is not known (`find_path`, `player-path.c:1069`). Measured at
  170–440 game turns and 17–44 tiles **per ask** against `lxg`'s ten or twenty
  turns (ONE RUN, `minimaxflash-1.3`, 31 `lxg` legs against seven long aims).
  Aim short and the destination lands in a wall and nothing happens, with no
  error message.
- **A reroll is two or three asks and gives a fresh level of the same depth**
  (`<` then `>`, stairs are connected: 3 RUNS, `sonnet-1#67`–`#70`,
  `sonnet-2-again#231`, `codex-1-tty`). Since the staircase is uniform on
  every level, a reroll is exactly as likely to be hard as the level it
  replaces — its value is that it costs two keys where a level costs a hundred
  asks.
- **Magic Mapping is 22×40, not the level** (`effect-yx:22:40`), 65 gold, and
  read once on depth 1 it showed no staircase (ONE RUN, `sonnet-2#47`).
  Whether it ever shows one is still open.
- **A level is regenerated when you leave it.** The depth 1 one character
  returned to after a Word of Recall was demonstrably a different level — no
  vein corridors, up staircase elsewhere, and the game's own jump to a *known*
  staircase found nothing (ONE RUN, `minimaxflash-1.3#437`). So a staircase
  found and used is not a staircase a successor inherits.

**For the consumer:** descent is a search problem with no exploitable prior,
and the cheap moves are the game's own long-range walk and the two-key reroll.
A Borg that evaluates "explore this level more" against "reroll it" needs the
generator's uniformity in that comparison.

## 3. The screen is not the state

Where a text player is blind, which is where a borg with the game's variables
has an advantage worth naming.

- **A blank or `[----------]` health bar means not in view, not dead** (3
  RUNS). `sonnet-3` died of this: it threw one flask at a small kobold, the
  bar went blank, it treated the monster as gone, and the kobold came back
  seven turns later and killed it (`sonnet-3#43`–`#48`).
- **`[` is the cheapest information in the game**: *"You can see N
  monsters"* with glyph, name and exact relative position, one keypress, no
  turn. After a Detect Life cast it gains a second section for monsters out of
  sight (`minimaxflash-1-again#361`). `l` (look) by contrast opens on the
  player's own square and answered only *"You are on an open floor"* in two
  runs that needed to know what a letter was (2 RUNS, `sonnet-1#40`,
  `sonnet-2#58`).
- **In look mode the cursor snaps to the next interesting square along a
  direction**, enumerating a room in one ask with no turn cost (ONE RUN,
  `minimaxflash-1-again#185`–`#195`).
- **The remembered map can be wrong about walls**: a square drawn `.` was a
  wall, the walk stopped with *"There is a wall in the way!"*, and the square
  was then redrawn correctly (ONE RUN, `minimaxflash-1#43`). A planned path is
  a hint.
- **`M` shows a scaled view of the remembered region, not the level** (2 RUNS,
  `minimaxflash-1#104`, `minimaxflash-1-again#181`, where it drew a 7×3 blob
  while the main map showed a 13-wide room). Eight asks spent on it produced
  nothing.
- **The map window is drawn behind the sidebar**, so a row's glyphs start at
  different screen columns depending on sidebar text length; reading a glyph's
  column off a row is unreliable, and the targeting cursor is the only
  position that can be trusted (ONE RUN, `minimaxflash-1.3`).
- **The level feeling digit on screen is danger, and higher is worse** — the
  reverse of what the strategy manual's table implies, because the game prints
  `10 - mon_feeling` (GAME SOURCE). `diego-1` was told *"naught but cobwebs"*
  at turn 601 and stayed 4,290 turns.

## 4. Where a keypress is lost

A borg sends keys too. These are the places a key does not do what it looks
like it does.

- **A `-more-` swallows the next key** (3 RUNS: `sonnet-1#21`, `sonnet-2#16`,
  `sonnet-3#32`, and `qwen-flash-1` found it independently). A space clears
  one and is harmless otherwise.
- **A level change ends in a `-more-`**, so `>` needs a trailing space; `<>`
  in one ask left a run in the town (3 RUNS).
- **Look mode stays up and eats the first key of the next string**; the tell
  is a look description in the message line and a turn counter that does not
  move. Four asks lost (ONE RUN, `minimaxflash-1-again#221`–`#225`).
- **`g` leaves targeting mode, and the next key cancels the walk**, so
  `lxglxglxg` is three one-square hops, not three walks (2 RUNS, measured both
  ways at `sonnet-2-again#156`–`#164`).
- **Any keypress during a run cancels it** (*"Cancelled."*), including a
  trailing space (ONE RUN, `minimaxflash-1`).
- **Menu letters are labels, not positions**: store rows came up
  `a c f h j m n o q r u v y z`, the pack skips `h j k l`, and the throw
  prompt has letters of its own (3 RUNS).
- **Enter is carriage return, not `\n`**, for a numeric prompt: `R50` then
  `\n` left the prompt sitting with `50` in it (ONE RUN, `minimaxflash-1.3`).
- **While confused, blind, afraid or slowed, a batch of keys is a bet you
  cannot cancel.** `sonnet-3` sent sixteen hold keys in one ask while confused
  and died inside them. The game flushes input on a disturbance; whatever was
  sent is still in the buffer.

## 5. The item economy

- **Selling pays nothing.** `birth_no_selling` is on: a store offers 0 gold
  for anything (2 RUNS, `sonnet-2#13`, `sonnet-3#26`). Gold is the only loot.
  The Word of Recall scroll in a starting kit is not money.
- **Every harmful consumable has `cost:0` in `object.txt`, and every useful
  one has a price** (GAME SOURCE). Once a kind is identified, its shop price
  tells you which group it is in. This is the whole of item triage at these
  depths.
- **Gear is priced by its power, not by its `cost:` line**
  (`src/obj-power.c: object_value_real`), so a shop screen is the only
  authority: the Armoury had Leather Shield 66 and Studded Leather 150 against
  strategy-manual figures far below (2 RUNS, `sonnet-3#27`, `minimaxflash-1`).
- **An unknown kind pays experience the first time it is used**,
  `(kind level + your level / 2) / your level` rounded down
  (`src/obj-knowledge.c`): a whole character level at CL1, nothing by CL5 (2
  RUNS). A bought item is already named and pays nothing (3 RUNS).
- **Bought armour is not worn for you.** `Cur AC 0` until `w` and the pack
  letter (ONE RUN, `minimaxflash-1`).
- **The Alchemist restocks daily and the shopkeeper rotates**
  (`store_maint()`, `store.c:1425`). "The Alchemist had no Magic Mapping this
  seed" was true of one day: a later visit found three at 65 gold under a
  different shopkeeper (ONE RUN, `minimaxflash-1-again#399`).
- **The town steals.** A filthy street urchin took 8 of 26 gold and a cutpurse
  lifted a flask of oil (`minimaxflash-1-again#394`); the next life arrived
  with 3 gold and could not reach a shop at all (`minimaxflash-1.3`). The
  town is also where the corpus' second death happened (`qwen-flash-1`, killed
  by a scruffy little dog at depth 0).
- **Escapes bought are escapes unused**: Phase Door and Cure Light Wounds were
  still in the pack at the end of every run that bought them, and `sonnet-3`
  died holding six and five of them (3 RUNS). Carrying them was right; not
  reaching for them was the error.

## 6. Fighting, as measured

- **A flask of oil is 9–36 damage (about 22), range 10, and every class has
  it**: 1d4 × 3 (throwing weight) × 3 (EXPLODE), and fire-resistant monsters
  take it too (GAME SOURCE). It one-shotted each depth-6 `p` human
  (`sonnet-2#124`, `#131`, `#145`) and killed Fang at CL2 for 20 of 31 hit
  points (`sonnet-1#84`–`#90`).
- **Armour class decides whether oil can hit at all.** `hit_chance()` needs
  `to_hit ≥ AC × 2/3` to beat the flat 12% always-hit, so Grip (AC 36) could
  not be hurt at range 2 and was killed at range 1 at about 77% (ONE RUN,
  `minimaxflash-1-again`). Low-AC targets (worm mass, mould, mushroom patch,
  mouse: AC 1–4) are what oil is for at range.
- **A monster's hit dice are not its damage against you**: Grip's 1d4 bite did
  2–4 against AC 12 (ONE RUN).
- **Stationary monsters are the depth-1 killers**: the floating eye paralyses
  if you stand next to it and never moves; the grey mushroom patch confuses
  and the yellow one terrifies, and in both cases the `1d4` is the *duration*,
  not damage. The **grey mould is not stationary** — it has no `NEVER_MOVE`
  and it chases (GAME SOURCE + `minimaxflash-1-again#174`, `codex-1-tty`,
  which lost 5 of 21 hit points to spores without melee).
- **Confusion is the most crippling condition**: it blocks casting, blocks
  running and exploring, and randomises every direction with 75% probability
  (`player_confuse_dir`, `player-util.c:1353`). Resting beside a spore monster
  never clears it, because it re-spores every turn (ONE RUN,
  `minimaxflash-1.3`). A Cure Light Wounds cuts it by 20 turns, and no run has
  ever drunk one for that purpose.
- **Phase Door is the move that worked**: one ask, ten squares, no delay, and
  it broke away from a +10-speed unique twice (`minimaxflash-1-again#332`,
  `#345`).
- **Word of Recall is not an escape and is a free heal.** The counter is
  decremented in `process_world`, once every ten game turns, so 15+1d20 ticks
  is **150–340 game turns** (GAME SOURCE): one run gave up on it after about
  forty (`qwen-flash-1`). Read in town before ever leaving it, it goes to
  depth 1 (`player_set_recall_depth`). Arriving in town healed 28/33 to 33/33.

## 7. How the two deaths happened

Both at character level 1, both to a monster worth almost nothing.

- **`sonnet-3`, Human Mage, 10 hit points, depth 1, turn 1,348, small
  kobold.** A wounded kobold believed dead (blank health bar), then a gas trap
  that confused the character, then sixteen hold keys in one ask. It had five
  Cure Light Wounds and six Phase Door in the pack and used neither. It had
  also chosen Find Traps/Doors/Stairs as its one CL1 spell, so it had no spell
  attack at all.
- **`qwen-flash-1`, High-Elf Druid, 12 hit points, depth 0, turn 570, scruffy
  little dog.** It never left the town: 29 of 73 asks on birth and shopping,
  the rest walking around the town. It had the same manuals and notes as the
  run that reached depth 7.

**For the consumer:** neither death is a tactical failure of the kind a
threshold rule prevents. One was a *state-tracking* failure (an unseen monster
believed dead) compounded by an uncancellable batch; the other was never
playing at all. A death analyser that looks for "fought something too strong"
would find nothing in either.

## 8. The classes, as played

- **Warrior** (3 runs, the deepest): hit die 9, no spells, and oil is the
  whole ranged game. The only class to pass depth 2 in this corpus.
- **Druid** (4 runs, all on seed 23): 13 hit points at CL1 with a 1d1+1 whip —
  five blows to kill a 10-hit-point worm. No teleport spell ever. Spell points
  regenerate at about 0.023/turn at CL3 (`player_regen_mana`,
  `player-util.c:487`), so **one spell point is about 22 turns of rest and
  Stinking Cloud costs two**: the class's only weapon arrives at CL3 and
  cannot be paid for. Stinking Cloud cannot hit its caster (no `PROJECT_PLAY`:
  `effect-handler-attack.c:594`), but most depth-1 monsters have `IM_POIS` and
  shrug it off.
- **Mage** (1 run, died): 10 hit points, one spell at CL1. Picking detection
  over Magic Missile left it with no attack but oil.
- **Priest** (1 run, the person): no prayer before CL5 detects anything, and
  prayers are given at random rather than chosen (`class.txt`), so a Priest
  has no magical way to find a staircase.
- **Blackguard and Necromancer have never been played.**

## 9. What this corpus cannot answer

Open, with what would settle each. These are the gaps a consumer should not
read as answered.

1. **Can depth 1's staircase be found by coverage?** No run has spent a full
   budget on the long-aim cursor walk while scanning every map for `>`.
2. **Does Magic Mapping show a staircase?** One reading, no staircase in
   radius (`sonnet-2#47`). 65 gold against a 22×40 window.
3. **Is a reroll better than finishing a level?** Two or three asks against
   perhaps a hundred, with a uniform prior either way. Nobody has measured
   asks-to-descent under the two policies.
4. **How common is a Deep Descent scroll, and at what depth?** `object.txt`
   says `level:10` with `alloc:20:1 to 100`; one was found and read on depth 1
   (`sonnet-2#76`). The allocation code in `obj-make.c` would settle which
   field governs.
5. **Is depth 5–20 survivable by a player of this kind?** `INSTRUCTIONS_2.md`
   covers it entirely from game data, because **no run has been below depth
   7**.
6. **Does anything below depth 2 behave as the strategy manual's policies
   assume?** Its rules are explicitly "a starting policy to be measured", and
   this corpus measured them at depth 0–2 only.

## 10. What this repository is, in one paragraph

A language model plays Angband 4.2.6 from an 80×24 screen, one keypress at a
time, with no state extraction and no primitives: the screen is the state and
the keyboard is the action. A run is a seed plus its keys, so `replay`
reproduces it byte for byte and `carry-on` continues a stopped character;
every run's keys, decisions, notebook and report are in `records/`. The game
is built with `-DSUPPORT_BORG=OFF`, so there is no Borg in the binary and
nothing in it can play for the model. What the runs establish is therefore
about a *reading* player, which is the one thing a Borg's own games cannot
produce.
