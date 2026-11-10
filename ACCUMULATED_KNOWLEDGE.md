# ACCUMULATED KNOWLEDGE — what the runs found that no manual says

Edition 1, 2026-11-10. *(Revised the same day: the first draft repeated things
the manuals already say. See "What is deliberately not here".)*

**Who this is for.** [borg-reborn-rs](https://github.com/diegoami/borg-rs),
the Rust Borg being rebuilt, and anyone else outside this repository. The
process that produces it is [docs/EXPORT.md](docs/EXPORT.md); it is rewritten
from time to time, not after every run.

**What it contains, and why it is short.** The consumer can read the game's
own manual, the strategy manual and `lib/gamedata` itself, at leisure and in
full — a program has time a player in a 150-decision budget does not. So
nothing here is in those documents. What is here is the residue: **what ten
runs measured, what they corrected, and what had to be read out of the source
because no manual states it.**

**Not for the players.** A run here is denied exactly one thing: another run's
account of the seed it is playing. This file aggregates every report, so
handing it to a player would hand them a solution key for their own dungeon.
The prompts do not mention it.

**How to read a claim.** Each names its evidence:

| | |
|---|---|
| `sonnet-2#124` | run and ask: screens in `records/sonnet-2/`, the player's words in `knowledge/sonnet-2.md` |
| GAME SOURCE | read out of `vendor/angband` at the pin (4.2.6, `e473720ed88a`); true of the game, and **not in the manuals** |
| ONE RUN | one player, once. A lead |
| N RUNS | N different runs, independently |

## The corpus

Ten runs, 2,332 asks, 10,403 keypresses, deepest **depth 7**, two deaths. One
session was played by a person (`diego-1`), which is the control. Every
character was drawn, not chosen.

| run | model | character | depth | level | asks | turns | ended |
|---|---|---|---|---|---|---|---|
| [sonnet-1](records/sonnet-1/REPORT.md) | anthropic/claude-sonnet-5-5 | Half-Troll Warrior | 1 | 3 | 125 | 4,659 | alive, budget |
| [sonnet-2](records/sonnet-2/REPORT.md) | anthropic/claude-sonnet-5-5 | Half-Troll Warrior | 6 | 6 | 153 | 6,056 | alive, budget |
| [sonnet-2-again](records/sonnet-2-again/REPORT.md) | anthropic/claude-sonnet-5-5 | Half-Troll Warrior | **7** | 8 | 291 | 10,416 | alive, budget |
| [sonnet-3](records/sonnet-3/REPORT.md) | anthropic/claude-sonnet-5-5 | Human Mage | 1 | 1 | 47 | 1,348 | **died**, small kobold |
| [codex-1-tty](records/codex-1-tty/REPORT.md) | openai/gpt-5.6-luna | Dunadan Warrior | 1 | 1 | 66 | 1,860 | alive, in town |
| [qwen-flash-1](records/qwen-flash-1/REPORT.md) | alibaba-token-plan/qwen3.8-flash | High-Elf Druid | 0 | 1 | 73 | 570 | **died** in the town, scruffy little dog |
| [minimaxflash-1](records/minimaxflash-1/REPORT.md) | minimax/MiniMax-M3.1-Flash | High-Elf Druid | 1 | 1 | 148 | 7,433 | alive, budget |
| [minimaxflash-1-again](records/minimaxflash-1-again/REPORT.md) | minimax/MiniMax-M3 | High-Elf Druid | 2 | 4 | 401 | 10,898 | alive, budget |
| [minimaxflash-1.3](records/minimaxflash-1.3/REPORT.md) | minimax/MiniMax-M3 | High-Elf Druid | 1 | 4 | 610 | 17,281 | alive, budget |
| [diego-1](records/diego-1/REPORT.md) | a person | Kobold Priest | 1 | 2 | 418 | 4,741 | alive, saved |

Every row links a report, and every report links a replay that steps through
screen by screen: <https://diegoami.github.io/borg-runner/>.

---

## 1. Descent is the whole problem, and nothing in the manuals says how

Nine of ten runs ended at depth 0, 1 or 2. **Nothing killed them**: eight were
alive when they stopped, at or near full hit points. They were still on the
first level because they had not found the way off it.

- **Walking a depth-1 level costs on the order of 100 decisions and finds
  nothing.** 100 of `sonnet-1`'s 125 asks; 148 of `minimaxflash-1`'s; 174
  screens of depth 1 in `minimaxflash-1.3`; 4,290 of `diego-1`'s 4,741 game
  turns on one level (5 RUNS, one of them a person).
- **The person and the first model run are the same session.** 971 keypresses
  against 644, 4,741 turns against 4,659, both depth 1, neither found a way
  down. Three in five of the person's keypresses moved one square; the run
  command was used 32 times in 418 (`diego-1`).
- **The one run that changed this changed one thing**: it used the game's own
  routing to walk to a staircase it had seen (`sonnet-2-again#228`–`#230`, 11
  steps and 110 game turns in a single decision), and reached depth 7. The
  corpus' only other descent was a Deep Descent scroll found by luck
  (`sonnet-2#77`).
- **A player that writes its own router measures its own router.**
  `minimaxflash-1` spent 148 asks driving a 143-line breadth-first search it
  wrote, reached depth 1, and never tried the game's commands. Its next life
  used the game's and got further on fewer asks.

**For the consumer:** the manuals describe descent as the objective and say
nothing about its cost. Measure decisions-per-descent, not per turn. A policy
that spends 80% of its decisions on floor coverage has 20% left for everything
the manuals are about.

## 2. What the generator does, which decides whether searching can work

All GAME SOURCE, found because play could not answer it. None of it is in the
manuals.

- **Exactly one down staircase per level** (`gen-cave.c:1583`), placed on a
  square with three adjacent walls (`gen-util.c:620`), drawn **uniformly at
  random over the whole level** (`cave_find_get_grid`, `gen-util.c:202`).
  There is no exploitable prior: not "near the up staircase", not "in the
  largest room". Via `minimaxflash-1-again`.
- **A level is 198×66 with up to 50 rooms** (`constants.txt`,
  `dungeon_profile.txt` "classic" `params:11:50:200:2`), against a 66×22 view.
  Via `minimaxflash-1`. With the uniform placement above, this is the whole
  explanation of section 1.
- **A level is regenerated when you leave it.** The depth 1 a character
  returned to after a Word of Recall was demonstrably not the level it had
  left — different corridors, the up staircase elsewhere, and the game's own
  jump to a *known* down staircase found nothing, so the staircase it had used
  was not merely unseen but not remembered (ONE RUN, `minimaxflash-1.3#437`).
  A staircase found is not a staircase an heir inherits.
- **The game's own long walk crosses unknown ground.** `find_path`
  (`player-path.c:1069`) tries a known-only path and then falls back to one
  through unknown grids, and the targeting cursor is clamped to the level, not
  to the view — so a destination can be aimed at ground never seen. Measured
  at 170–440 game turns and 17–44 tiles **per decision**, against ten or
  twenty turns for the nearest-frontier command (ONE RUN,
  `minimaxflash-1.3`). Aim short and the destination lands inside a wall and
  nothing happens, with no message.
- **A reroll of the level is two or three decisions** (`<` then `>`; stairs
  are connected: 3 RUNS). Against a uniform placement, a fresh level is
  exactly as likely to be hard — which makes the comparison *decisions spent
  here* against *decisions spent anywhere*, and nobody has measured it.
- **Magic Mapping is `effect-yx:22:40`**, a window and not a level, 65 gold,
  and the one reading of one on depth 1 showed no staircase (GAME SOURCE +
  ONE RUN, `sonnet-2#47`).

## 3. Where the manuals are wrong, or silent

The corpus' direct corrections. Each cost a run something.

| the manuals say | what the runs found |
|---|---|
| the level feeling is a number to compare against a danger table (strategy manual c15) | the game prints `10 - mon_feeling`, so **the digit on screen is inverted** against that table: higher is worse (GAME SOURCE). A session was told *"naught but cobwebs"* and stayed 4,290 turns (`diego-1`) |
| `M` shows the whole-level map | it shows a scaled view of the **remembered region**: on one level a 7×3 blob while the main view had drawn a 13-wide room (2 RUNS, `minimaxflash-1#104`, `minimaxflash-1-again#181`). Eight decisions spent on it returned nothing |
| the Armoury's prices (c11 tables) | gear is priced by **power**, not by its `cost:` line (`src/obj-power.c: object_value_real`): Leather Shield 66, Studded Leather 150, far above the tables (2 RUNS, `sonnet-3#27`, `minimaxflash-1`) |
| Deep Descent is found from depth 1 (our own earlier distillate) | `object.txt` gives it `level:10` with `alloc:20:1 to 100`, and one *was* found and read on depth 1 (`sonnet-2#76`). Which field governs the depth is still unread (`obj-make.c`) |
| a shop's stock is the seed's stock (inferred by a run) | `store_maint()` runs once per game **day** and the shopkeeper shuffles (`store.c:1425`): "the Alchemist had no Magic Mapping this seed" was true of one day only, and a later visit found three at 65 gold under a different shopkeeper (ONE RUN, `minimaxflash-1-again#399`) |
| Word of Recall is not an escape (c15 ESC-04) | right, and the number behind it: the counter ticks in `process_world`, once per ten game turns, so 15+1d20 ticks is **150–340 game turns** — one run gave up after about forty (`qwen-flash-1`). Read in town before ever leaving it, it goes to depth 1, and arriving in town heals (GAME SOURCE + 2 RUNS) |
| the manuals list the mushroom patches | they do not say that the **grey mould is mobile** — no `NEVER_MOVE`, and it chases (GAME SOURCE + `minimaxflash-1-again#174`, `codex-1-tty`, which lost 5 of 21 hit points to spores without ever meleeing it) |

## 4. Numbers the manuals do not give

- **Armour class decides whether a thrown flask connects at all.**
  `hit_chance()` needs `to_hit ≥ AC × 2/3` to beat the flat 12% always-hit, so
  Grip (AC 36) could not be hurt at range 2 and died at range 1 at about 77%,
  while AC 1–4 targets (worm mass, mould, patch, mouse) are worth throwing at
  from anywhere (GAME SOURCE + ONE RUN, `minimaxflash-1-again`). One flask
  killed each depth-6 `p` human it met (`sonnet-2#124`, `#131`, `#145`).
- **A monster's hit dice are not its damage against you**: Grip's 1d4 bite did
  2–4 against AC 12 (ONE RUN). Armour eats most of a small die.
- **Spell points regenerate at about 0.023 per turn at character level 3**
  (`player_regen_mana`, `player-util.c:487`: `msp × 197 + 524` in 65536ths,
  doubled while resting). One spell point is roughly 22 turns of rest, and the
  Druid's only attack spell costs two: 20 turns of resting bought **nothing**
  (ONE RUN, `minimaxflash-1-again#363`). A class whose weapon arrives at CL3
  cannot pay for it at CL3.
- **A player-cast ball never hits its caster** (`PROJECT_PLAY` is not set:
  `effect-handler-attack.c:594`, `project.c:519`), so radius-2 poison is safe
  at point-blank — and **most depth-1 monsters have `IM_POIS`** and shrug it
  off anyway (GAME SOURCE + ONE RUN).
- **Confusion randomises every direction with 75% probability**
  (`player_confuse_dir`, `player-util.c:1353`) and blocks casting and running
  (`player-util.c:1103`, `cmd-cave.c:1503`). **Resting beside a spore monster
  never clears it** — it re-spores every turn (ONE RUN, `minimaxflash-1.3`). A
  Cure Light Wounds cuts it by 20 turns, and no run has ever drunk one for
  that.
- **Identifying by use pays `(kind level + your level / 2) / your level`,
  rounded down** (`src/obj-knowledge.c`): a whole character level at CL1,
  nothing by CL5 (GAME SOURCE + 2 RUNS). A bought item is already named and
  pays nothing (3 RUNS).
- **Every harmful consumable has `cost:0` in `object.txt` and every useful one
  has a price** (GAME SOURCE), so once a kind is identified its shop price is
  its triage. Selling pays **0 gold** for everything (`birth_no_selling`: 2
  RUNS), which makes the starting Word of Recall scroll not money.

## 5. What the players did with all this, which is the behavioural finding

- **Escapes bought are escapes unused.** Every run that bought Phase Door and
  Cure Light Wounds still held them at the end, and the run that died was
  holding six and five of them (3 RUNS). The purchase was right; reaching for
  it never happened.
- **The one escape that was used, worked.** Phase Door broke away from a
  +10-speed unique twice in one run, for one decision each
  (`minimaxflash-1-again#332`, `#345`).
- **The town is not free.** A street urchin took 8 of 26 gold and a cutpurse
  lifted a flask (`minimaxflash-1-again#394`); the next life of that character
  arrived with 3 gold and could not reach a shop at all, which made the
  previous life's own advice — buy the 65-gold Magic Mapping — unactionable
  (`minimaxflash-1.3`). The corpus' second death was in the town
  (`qwen-flash-1`).
- **A model can hold the knowledge and not play.** `qwen-flash-1` had the same
  pages and notes as the run that reached depth 7, and spent 29 of 73
  decisions on birth and shopping and the rest walking around the town until a
  dog killed it.

## 6. How the two deaths happened

Both at character level 1, both to a monster worth almost nothing, and
**neither is the kind of death a threshold rule prevents** — which is the part
worth carrying into a death analyser.

- **`sonnet-3`, Human Mage, 10 hit points, depth 1, turn 1,348, small
  kobold.** A wounded kobold was believed dead because its health bar went
  blank (it means *not in view*); then a gas trap confused the character; then
  it sent sixteen hold keys in one decision and died inside them. Five Cure
  Light Wounds and six Phase Door in the pack, unused. It had also chosen
  detection over Magic Missile as its single CL1 spell, so it had no attack
  but thrown oil.
  *The failure is state-tracking plus an uncancellable batch, not target
  selection.*
- **`qwen-flash-1`, High-Elf Druid, 12 hit points, depth 0, turn 570, scruffy
  little dog.** It never left the town.
  *The failure is that it never played.*

## 7. The classes, where play said something data does not

- **Warrior** (3 runs, the deepest): the only class past depth 2 here. Oil is
  the whole ranged game and that was enough to depth 7.
- **Druid** (4 runs, all seed 23): 13 hit points and a 1d1+1 whip at CL1 —
  five blows to kill a 10-hit-point worm — and the mana economy above makes
  its CL3 spell unpayable. It still reached CL4 and killed a depth-2 unique,
  with oil.
- **Mage** (1 run, died): one spell at CL1, and the choice of which decided
  whether it had an attack at all.
- **Priest** (1 run, the person): **no prayer before CL5 detects anything**,
  and prayers are given at random rather than chosen (`class.txt`), so a
  Priest has no magical route to a staircase — which, given section 1, is the
  class's real problem rather than its combat.
- **Blackguard and Necromancer have never been played.**

## 8. What this corpus cannot answer

Read these as open. A consumer's own evidence would be the first.

1. **Can depth 1's staircase be found by coverage?** No run has spent a full
   budget on the long aimed walk while checking every view for a `>`.
2. **Does Magic Mapping ever show a staircase?** One reading, nothing in
   radius.
3. **Explore or reroll?** Two or three decisions against perhaps a hundred,
   with a uniform prior either way. Unmeasured.
4. **What governs Deep Descent's depth**, `level:` or `alloc:`? One was found
   on depth 1 against `level:10`.
5. **Is depth 5–20 survivable by a player of this kind?** Nobody has been
   below depth 7; our own volume 2 is written entirely from game data.
6. **Do the strategy manual's numeric policies hold anywhere?** They are
   explicitly "a starting policy to be measured", and this corpus measured
   them at depth 0–2.

## What is deliberately not here

The consumer reads the manuals and the data itself, so this file leaves out:

- **anything the game's manual or the strategy manual says** — the command
  set, the spell lists, prices, kits, monster tables, the escape ladder;
- **anything in `lib/gamedata` that a reader can look up** — we quote a data
  file only where a run's conclusion depends on it;
- **what is only true of reading a text screen**: where a keypress is lost to
  a `-more-`, that menu letters are labels rather than positions, that the
  glyph under `@` is not drawn, that a blank health bar means *unseen*. Those
  are real and they are in `manuals/INSTRUCTIONS.md` for the players here;
  they are not knowledge about Angband, and a program with the game's own
  state does not have those problems. Where one of them caused a death it is
  in section 6, because the death is the point.

## What this repository is, in one paragraph

A language model plays Angband 4.2.6 from an 80×24 screen, one keypress at a
time, with no state extraction and no primitives: the screen is the state and
the keyboard is the action. A run is a seed plus its keys, so `replay`
reproduces it byte for byte and `carry-on` continues a stopped character;
every run's keys, decisions, notebook and report are in `records/`. The game
is built with `-DSUPPORT_BORG=OFF`, so nothing in the binary can play for the
model. What the runs establish is therefore about a *reading* player, which is
the one thing a Borg's own games cannot produce.
