# NOTES: what earlier runs found out

Three runs: seed 7 Half-Troll Warrior twice (alive, depth 1 at ask 125; alive, depth 6 at ask 153) and seed 11 Human Mage (died on depth 1 at character level 1, ask 48). Read after `manuals/INSTRUCTIONS.md`; where they disagree this file is what the game did. **(3 runs) / (2 runs)** = seen on separate runs; **(1 run)** = one run's word, a lead. Evidence for any line is in `knowledge/LEARNED.md` under the `[id]`; `MANUAL-GAPS.md` has the long cheat sheets. Gold, shop stock and depth-1 monsters are those two characters'.


## One inherited note now explained by the source

A run read Word of Recall in the town, watched the `Recall` marker sit for
about forty turns with no teleport, and wrote that it might be a dud. It is
not. `src/player-util.c` has "Players who haven't left town before go to level
1", so recall from town takes you to **depth 1** - and `src/game-world.c`
decrements the counter in `process_world`, which runs once every **ten game
turns**, so 15+1d20 ticks is **150-340 game turns**. The run gave up at about
a quarter of the minimum. Reading it in town is 125 gold spent on a slow trip
to depth 1, not a no-op.

This is what the note discipline is for: the run wrote what it saw and
hedged - "either it resolves at the next transition or..." - instead of
asserting, so the source could settle it later.

## Explore and descend with the game's own pathfinder

**`lxg` to explore, `l>g` to reach a known down staircase, `l<g` to go back up**
(2 runs: `sonnet-2-again` 156-230 found and used it; earlier runs' failure to
find any staircase is what made it worth looking for).

- Each must be alone in its ask: a key after `g` cuts the walk to one step, so
  `lxglxglxg` is three one-square hops, not three walks (1 run, measured both
  ways at asks 156-164).
- `>` in look mode with no staircase known does nothing and rings a bell.
- Taking the stairs is then `>` on its own, and a key sent after a level
  change is swallowed, so send `> ` with a trailing space (2 runs).
- Connected stairs make a reroll two asks: `< ` then `> ` gives a fresh level
  of the same depth. Reroll on a level feeling of 5 or more — the digit on
  screen is danger, higher is worse (1 run; chapter 15 has that digit the
  other way round).

**No run has ever found a down staircase by walking.** Four runs and ~350 asks
found none; the one deliberate descent used `l>g`, and the one other descent
was a Deep Descent scroll read by luck.

## Keys that did not do what the manual implied
- **A `-more-` swallows the next key** (3 runs): a command typed behind one loses its first key and the rest misreads. A space clears a `-more-` and is harmless otherwise (2 runs), so end strings with spaces (`va'   `). Stairs and Deep Descent each end in a `-more-`: a key after `>` in the same string is lost, `<>` left a run in town. [more-swallows-next-key, space-clears-more, level-change-more]
- **Menu letters are labels, not positions** (3 runs): store rows `a c f h j m n o q r u v y z`; pack `a b c d e f g i m ...` (skips `h j k l`); the **throw prompt has its own letters** (oil `a` there, `b` or `c` in the pack). Read them off the screen. [store-letters-fixed, pack-letters-skip, throw-menu-own-letters]
- **Buying**: `p`, row letter, quantity digits, Enter, any key but Esc; a whole purchase fits one ask, `ph10\ny ` for ten flasks (3 runs). "One purchase per ask" was an early wrong note. [purchase-in-one-ask]
- Bought scrolls and potions are **already named** in the pack, so using them pays no experience (3 runs). [bought-items-named]
- `va'` (throw, item, nearest) worked every time (3 runs). `v`, item, `5` to re-throw: unclear (1 run). [throw-closest-target, rethrow-target-5]
- **`l` with monsters on screen returned only "You are on an open floor"** (2 runs); both attacked or threw to learn what a letter was. Space to cycle, and `[`, were not tried. [look-returns-own-square]
- `,` holds a turn, `s` asks for a direction instead (1 run); Enter with no `-more-` opens the command menu (1 run). [hold-key-is-comma, enter-opens-menu]
- A digit string stops at the first wall and the rest does nothing; in caves `.` + digit stopped every 2-3 squares and `4444444444` went further (1 run each). [digit-string-stops-at-wall, digit-strings-beat-runs]

## Finding the way down is where the asks go
- About 100 of 125 asks (run 1), then 51 on depth 1 and 73 on depth 6 (run 2), found **no `>`** (2 runs). Nobody ever took a dungeon down staircase: depth 1 came from the town stairs, depth 6 from one scroll. [dl1-no-stairs-100-asks]
- A reroll (`<` to town, `>`, Space) costs **3 asks** (2 runs) and was no quicker to finish (1 run). [reroll-costs-three-asks, reroll-different-level]
- **Magic Mapping (65 g) did not help**: read on depth 1 it showed no staircase in the part of the map looked at (1 run), a quarter of the Warrior's gold. Untested elsewhere. [magic-mapping-no-stairs]
- The Mage's Find Stairs spell drew a `>` 13 columns west, 6 rows south on arrival; the corridor the player took led away; it died 12 asks later (1 run). [stairs-spell-shows-stairs]
- **Deep Descent (1 run, 1 scroll)**: an unknown scroll found on depth 1, read at 68/68 as a CL4 Warrior: "The air around you starts to swirl...", about 4-5 turns, depth 6 on no staircase, 4 asks in all. One of 4 unknown scrolls read in all runs: a lucky draw, not a rate. Depth 6: the Warrior lived 73 asks fighting from doorways with oil and found no `>` there either. [deep-descent-observed, dl6-at-cl4-survivable]

## Unknown potions and scrolls
- First use pays experience that shrinks fast (2 runs): Blessing at CL1 moved NXT 7 to 6; Light at CL3 nothing; Deep Descent at CL4 3 points; Cure Serious Wounds at CL5 1; Blessing at CL6 nothing. An unknown potion at CL1 (Boldness) gave level 2. [first-use-xp-shrinks]
- Tried, all harmless: Blessing x2, Light, Deep Descent; Boldness, Neutralize Poison, Heroism. Luck: the data also has Sleep, Blindness, Confusion, Poison, Slowness, Summon Monster, Darkness, Aggravate Monster (DL5+) as early unknowns.
- A CL5 Warrior drank an unknown potion at 89/89 and wasted a Cure Serious Wounds: at CL1-3 drink them for the experience, later only when hurt. [unknown-potion-wastes-heal]

## Fights
- Fang killed at CL2 in a corridor with two flasks then melee: 11 of 31 HP, CL2 to CL3. A dog pack plus Grip in a lit room took a CL1 Warrior from 23 to 12 HP and to CL4 (1 run each, Warrior). [fang-corridor-oil, dl1-dog-pack-levels]
- **A monster out of view is not dead.** Dead is "slain" in the message line or `NXT` moving; a blank or `[----------]` health bar means unseen. [unseen-is-not-dead]
- A flask "hit" an 8-HP small kobold and it lived (1 run), though the source gives 9-36 per hit: unreconciled, read the message for a miss. Thrown point-blank at 10 HP there was no margin: Phase Door first. [unseen-is-not-dead, mage-ten-hp]

## What killed the Mage (1 run)
10 HP, depth 1: a wounded kobold believed gone; a **gas trap confused** the Mage (still confused ten turns later); then **sixteen hold keys in one ask**; about seven turns in the kobold arrived and killed a full-health character with five Cure Light Wounds in the pack. [blind-batch-while-disabled, gas-trap-confusion]
- **Confused, blind, afraid, slowed or otherwise unable to answer: one or two keys per ask, never a string of waits.** The keys of an ask are sent without looking at the screen and the harness keeps the buffer when the game flushes input on a disturbance. [batch-uninterruptible]
- Confused you can still quaff and cannot read. By the data Cure Light Wounds cuts confusion by 20 turns and heals 20; no run has drunk one in an emergency. [confused-clw-unused]

## Shops and gold
- Starting gold: **146** (Half-Troll Warrior), **334** (Human Mage). [start-gold-differs]
- General Store and Alchemist prices matched across seeds (oil 3, Cure Light Wounds 20, Phase Door 15, Magic Mapping 65); stock did not (Magic Mapping 4 then 2). The General Store sold Torch 6, Cloak 6, Shovel 66, Pick 176 against `object.txt` costs 2, 3, 10, 300: gear is priced by power. Armoury (seed 11): Leather Shield 66, Studded Leather 150, far above the strategy manual's table; read the price first. [armoury-prices-high]
- The strategy manual's shopping order (escapes, heal, oil) is **untested**: in 119 and 150 asks no run used a Phase Door or Cure Light Wounds in an emergency, and the Mage died holding 6 and 5. [escapes-bought-unused]

## A Mage's first steps (1 run)
At CL1 the game said "You can learn 1 more spell" (`Study (1)`): `G`, book, spell; cast `m`, book, spell (`mac`). First cast paid 2 experience, a repeat nothing. The Mage took Find Stairs and so had no spell attack (oil only); its report lists that as a choice to take back, with Magic Missile on the same screen. Untested which is better. [mage-study-cast-keys, spell-first-cast-xp, mage-one-spell-no-attack]
