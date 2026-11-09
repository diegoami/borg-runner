# LEARNED: knowledge filed against the manual

Second consolidation. Three runs now: `sonnet-1` (seed 7, Half-Troll Warrior,
nothing inherited, 125 asks, depth 1, character level 3, alive), `sonnet-2`
(seed 7, the same character, inheriting sonnet-1's notes, 153 asks, **depth 6**,
character level 6, alive) and `sonnet-3` (**seed 11, Human Mage**, inheriting
the same notes, 47 asks, died on depth 1 at character level 1, killed by a
small kobold). `confirmed` is reachable now, and is used only where **two
different runs** show the same thing on their own notes, decisions or screens;
reading the source or the manual is not a trial and promotes nothing. Items
that only the source supports are `hypothesis` and say so.

This is a revision of the first consolidation, not a restart: **every id that
existed is still here, with the same id and the same sentence**; what changed
is `status`, `evidence`, and a `note:` line where a later run says more. New
ids were added; `supersedes:` says where one replaces another. The first
version is in git history.

What the manual should have said, as text to paste, is in
[MANUAL-GAPS.md](MANUAL-GAPS.md). Every `new:` anchor below reappears there.
What killed `sonnet-3`, and what would have prevented it, is the section
"What killed a character" after the items.

## Files read to produce this

Read in full:
- `docs/CONSOLIDATE.md` (the instructions)
- `knowledge/LEARNED.md` and `knowledge/MANUAL-GAPS.md` as the first
  consolidation left them (the files being revised)
- `knowledge/sonnet-1.md`, `knowledge/sonnet-2.md`, `knowledge/sonnet-3.md`
  (the three notebooks; not edited). `sonnet-2.md` and `sonnet-3.md` each begin
  with a copy of `sonnet-1.md`, which was their inheritance; only the lines
  after it are that run's own, and the items below cite that run's own asks
- `manuals/jev-1.md` (the compressed manual the anchors come from)
- `src/borg_runner/consolidate.py` (what `check()` enforces)
- `records/sonnet-2/REPORT.md`, `records/sonnet-3/REPORT.md`,
  `runs/sonnet-1/REPORT.md`, and `runs/sonnet-{1,2,3}/record.json`
- `runs/sonnet-2/decisions.jsonl` and `runs/sonnet-3/decisions.jsonl` (what was
  sent at each ask, and why), and `runs/sonnet-1/decisions.jsonl` for asks 12-27
  and 38-42 and 67-72
- the screens, `runs/<name>/ask/screen-<n>.txt` (**a screen at ask N is what
  the player saw before sending keys N**, so a result shows on screen N+1; the
  evidence below cites the ask whose screen shows the thing). sonnet-3:
  asks 9-16, 22-27, 30-36 and every screen from 38 to 48, the tombstone;
  sonnet-2: asks 13-17, 19-28, 39-41, 47-50, 56-71, 76-80, 82-83, 91-94, 107-112,
  118-121, 124-125, 131-133, 140-152 and a HP/level/NXT trace over 56-80 and
  79-152; sonnet-1: asks 15-25, 40-42, 57, 67-70, 117-119 and 124.
  Also a search of every screen of the three runs for the status line
  "Down staircase" (it occurs only in the town, see `dl1-no-stairs-100-asks`)

Read in part (searched for the topic, not read through):
- the game data and source at the pin, for what a claim rests on and for the
  numbers in the sheets: `lib/gamedata/object.txt` (Magic Mapping, Deep
  Descent, Cure Light Wounds), `lib/gamedata/class.txt` (the Mage's first
  spells), `lib/gamedata/monster.txt` (small kobold),
  `src/effect-handler-general.c` (`MAP_AREA`)
- `patch/src/main-agent.c` (the frontend: how a string of keys is buffered and
  what happens to the buffer when the game flushes input), for the harness lead
  in `batch-uninterruptible`
- the first consolidation's reading of `vendor/angband/docs/`,
  `vendor/strategy-manual` and the rest was **not repeated**; items from it
  keep the evidence they had

Not read: the `jev-*`, `smoke*`, `auto1` and `stairs` runs. They have records
but no notebook, so they are not evidence for anything here.

## Which notes travel and which are seed-specific

`sonnet-1` and `sonnet-2` are the same character on the same seed (a Half-Troll
Warrior, 146 gold, 23 hit points at character level 1). `sonnet-3` is a different
seed and a different character (a Human Mage, 334 gold, 10 hit points, 2 spell
points). Nothing a Warrior did on seed 7 says anything about a Mage. So:

- **General** (what the game's code does, whoever plays): store and pack letter
  skipping, the buying prompts, what a `-more-` does to the next key, the throw
  menu and `'`, arrival on stairs and the three-ask reroll, how first-use
  experience falls with character level, that a bought item is named in the
  pack, that selling pays 0 gold, what `l` returns, that a hold key is `,`.
- **Seed or character specific; do not generalise**:
  - the gold arithmetic. 146 gold buying 15 oil, a cloak, 3 Phase Door and 2
    Cure Light Wounds with 10 left (`magic-mapping-unaffordable`, and the
    "Gold" paragraph of the first Sheet 5) is the Warrior's. The Mage had 334
    and bought 20 oil, a cloak, a torch, 6 Phase Door, 5 Cure Light Wounds and a
    66-gold Leather Shield, and could have afforded Magic Mapping with change
    (`start-gold-differs`);
  - the stock and its prices: the Alchemist held 4 Magic Mapping on seed 7 and 2
    on seed 11, and no Cure Serious Wounds on seed 11; the General Store lists oil under
    `h` on seed 7 and under `j` on seed 11 (the letters skip the same way, which
    row has which letter does not); the Armoury (Leather Shield 66, Studded
    Leather 150) is one shopkeeper's markup (`armoury-prices-high`). Oil (3),
    cloak (6), torch (6), Phase Door (15), Cure Light Wounds (20) and Magic
    Mapping (65) were the same price on both seeds, so those are list prices;
  - the fights. Fang and Grip (Farmer Maggot's dogs) on DL1 were both met on
    seed 7 and never on seed 11 (`fang-corridor-oil`, `dl1-dog-pack-levels`);
    surviving DL6 at character level 4 with 68 hit points is a Half-Troll
    Warrior's, not a 10-hit-point Mage's (`dl6-at-cl4-survivable`);
  - the Deep Descent scroll was found on one level of one run; levels differ
    between runs of the same seed because the random state depends on the keys
    (`deep-descent-paid-in-asks`);
  - everything under `new:spells`, and the death itself, which is a 10-hit-point
    character's (`mage-ten-hp`).

Advice travelled between runs, and that is part of the evidence. `sonnet-2`
bought Magic Mapping because the first version of Sheet 5 recommended it, and
read an unknown scroll at once because Sheet 1 said to: the first cost 65 gold
and showed nothing, the second took it to depth 6. `sonnet-3` followed Sheet 2's
"one purchase per ask" for two asks before finding it was not needed.

Where the game's own manual already says something and the player learned it
the hard way, the statement says so.

## Items

### The shop and the menus

- [store-purchase-prompts] In a store, `p` then the item's letter, then the quantity digits and Enter, then any key at "[ESC, any other key to accept]" buys it, and keys chained after the first completed purchase were swallowed, so send one purchase per ask (the compressed manual says only "p = buy").
  anchor: key:p
  status: contradicted
  evidence: sonnet-1#16, sonnet-1#21, sonnet-1#24, sonnet-1#25, sonnet-2#20, sonnet-2#22, sonnet-3#16
  note: the key sequence is right (it is `store-purchase-sequence` below, seen in all three runs). "Send one purchase per ask" is wrong: sonnet-2 bought a potion with `pa\ny ` and ten flasks with `ph10\ny ` in one ask each, and sonnet-3 twenty flasks with `pj20\ny`. What was swallowed in sonnet-1 (ask 20, `po3\nypa2\ny`) was the first key after the first purchase's `-more-`; see `more-swallows-next-key`. Reconciled by `purchase-in-one-ask`.

- [store-purchase-sequence] In a store a purchase is `p`, the row letter, the quantity (digits then Enter; the prompt shows 1 as its default), then any key but Escape at "[ESC, any other key to accept]"; Escape cancels.
  anchor: key:p
  status: confirmed
  evidence: sonnet-1#16, sonnet-1#24, sonnet-2#16, sonnet-2#17, sonnet-3#17

- [purchase-in-one-ask] A whole purchase is one ask when the confirming key is the last of the string and nothing is waiting on screen: `pa\ny ` (one Cure Light Wounds), `ph10\ny ` (ten flasks of oil), `pj20\ny` (twenty).
  anchor: key:p
  status: confirmed
  evidence: sonnet-2#20, sonnet-2#22, sonnet-3#16
  supersedes: store-purchase-prompts

- [more-swallows-next-key] A key sent while a `-more-` is on screen is consumed by it, so a command typed after one loses its first key and the rest runs misaligned: sonnet-1's second chained purchase arrived as "Buy how many? (max 2) y", sonnet-2's `po2\n` after a purchase left an unanswered "Buy how many?", and sonnet-3's ` mac` after a staircase ran `aim` and `close`.
  anchor: new:dismissing-more
  status: confirmed
  evidence: sonnet-1#21, sonnet-2#16, sonnet-3#32

- [space-clears-more] A space is harmless when no `-more-` is up and clears one when it is: a space after the last key (`pa\ny `, `va'   `) or at the start of the next string (` pa5\ny`, ` i`) kept a purchase or a throw to one ask where it had been two or three, one space per `-more-`.
  anchor: new:dismissing-more
  status: confirmed
  evidence: sonnet-2#20, sonnet-2#61, sonnet-3#24, sonnet-3#25

- [level-change-more] After a staircase and after a Deep Descent a `-more-` ("You enter a maze of down staircases") is on screen, so any key sent in the same ask after the stairs key is lost: sonnet-2's `<> ` left it in the town, which made a reroll three asks (`<`, `>`, space); sonnet-2 called this a flush, the screens show a `-more-`.
  anchor: key:<
  status: confirmed
  evidence: sonnet-1#68, sonnet-2#24, sonnet-2#26, sonnet-2#27, sonnet-3#31

- [store-letters-fixed] A store's rows are not lettered a, b, c: the run's Alchemist read a, c, f, h, j, m, n, o, q, r, u, v, y, z, so the letter has to be read off the screen and never counted.
  anchor: new:item-letters
  status: confirmed
  evidence: sonnet-1#25, sonnet-2#13, sonnet-3#22
  note: the letters skip the same way in every store seen (General Store: a c f h j m n o q r u; Armoury: a c f h j m). Which item has which letter changes with the stock: oil was `h` in the seed-7 General Store and `j` in the seed-11 one.

- [pack-letters-skip] Pack letters skip too: with eight items the list read a to g and then i, so `q`, `r`, `v` and `w` must be given the letter shown on the item list, not its position.
  anchor: new:item-letters
  status: confirmed
  evidence: sonnet-1#57, sonnet-2#119
  note: sonnet-2's nine items read a b c d e f g i m (h, j, k, l skipped), as the first Sheet 2 had predicted from the source.

- [throw-menu-own-letters] The throw prompt lists only throwing items under letters of its own, so flasks of oil were `a` there while `b` or `c` in the pack: send `v` then the letter from that prompt, not the pack's letter (sonnet-2's `vb'` was wrong, `a'` right).
  anchor: key:v
  status: confirmed
  evidence: sonnet-2#40, sonnet-3#41

- [bought-items-named] An item bought in a store is named in the pack even though the purchase message says "Scrolls titled ..." or "Misty Potions": the shop row loses its {unseen} and the pack lists "Scrolls of Phase Door", so only objects found on the floor are unknown.
  anchor: new:unidentified-objects
  status: confirmed
  evidence: sonnet-1#57, sonnet-2#19, sonnet-2#47, sonnet-3#25
  note: sonnet-3 noted it. The others are read off their screens (sonnet-2's Phase Door row loses {unseen} between asks 17 and 19; its read menu at ask 47 names Phase Door and Magic Mapping; sonnet-1's pack at ask 57 names its bought Cure Light Wounds and Phase Door).

- [selling-pays-nothing] Selling to a store pays 0 gold for everything offered ("Give which item? ... 0 au"), so the Word of Recall scroll in the starting kit cannot be turned into gold.
  anchor: key:s
  status: confirmed
  evidence: sonnet-2#13, sonnet-3#26
  note: sonnet-3 noted it; sonnet-2 pressed `s` at ask 12 to find out and its screen at ask 13 shows 0 au on both rows, though it wrote nothing down.

- [enter-opens-menu] Enter in the dungeon, with no `-more-` waiting, opens a command menu rather than clearing anything, so a `-more-` is dismissed with space or Escape (the compressed manual's "any key clears it" holds only while a `-more-` is actually on screen).
  anchor: new:dismissing-more
  status: hypothesis
  evidence: sonnet-1#103, sonnet-1#104

### Throwing

- [throw-closest-target] `v`, the item's letter, then `'` throws at the nearest visible monster; the game's own manual (playing.rst, "Targeting") says exactly this and the compressed manual's "then a target" leaves the key out, so the player had to read it off the prompt.
  anchor: key:v
  status: confirmed
  evidence: sonnet-1#83, sonnet-2#62, sonnet-3#42
  note: both later runs used `va'` and it worked every time they sent it (sonnet-2 about a dozen throws, sonnet-3 once); the prompt text "'" for closest" is on sonnet-2's screen at ask 62.

- [rethrow-target-5] After one throw has set a target, the direction prompt offers `5`, so `v`, the item letter, `5` throws at the same monster again; the compressed manual's line for `5` ("confirm the current target") already covers this and the player found it only when the prompt said so.
  anchor: key:5
  status: hypothesis
  evidence: sonnet-1#104
  note: not seen in the later runs. sonnet-2's `va5   ` (ask 61) was followed by an open "Direction?" prompt, and sonnet-3's ` va5` (ask 42) left no message on screen; in both the target may already have been dead or out of view, so neither supports nor contradicts it.

- [fang-corridor-oil] Fang, Farmer Maggot's Dog, killed at character level 2 in a corridor with two thrown flasks of oil and then melee, cost about 11 of 31 HP and took the character from level 2 to 3.
  anchor: OIL-01
  status: hypothesis
  evidence: sonnet-1#84, sonnet-1#90

- [dl1-dog-pack-levels] A pack of wild dogs and Grip, Farmer Maggot's Dog, met in a lit room on depth 1, took a level-1 Warrior with 23 hit points to 12 and then from character level 1 to 4 in one fight (oil first, then melee in the open).
  anchor: FIGHT-01
  status: hypothesis
  evidence: sonnet-2#60, sonnet-2#65, sonnet-2#68, sonnet-2#69
  note: with `fang-corridor-oil` this is two seed-7 runs in which a fast Maggot's dog on DL1 paid levels. Different dogs and different fights, so not the same item; both are the Warrior's.

- [oil-one-shots-p] Thrown oil killed the `p` humans on depth 6 (apprentice, gallant, tamer) in a single flask each.
  anchor: OIL-01
  status: hypothesis
  evidence: sonnet-2#124, sonnet-2#131, sonnet-2#145
  note: the player's claim (notebook, asks 131 and 145). The screens do not show it: the trailing spaces of `va'   ` clear the messages, so the line that says "slain" is gone by the next screen.

### Stairs, and the cost of finding one

- [arrival-staircase] After going down you stand on an up staircase, and after going up from depth 1 you stand in the town on its down staircase; the compressed manual already says the first of these, and the second is what makes the reroll below possible.
  anchor: key:<
  status: confirmed
  evidence: sonnet-1#29, sonnet-1#69, sonnet-2#25, sonnet-2#26

- [reroll-costs-three-asks] Taking `<` from depth 1 and then `>` in the town gives a fresh depth 1 for three asks (arrive in town, press `>`, dismiss the `-more-`).
  anchor: key:<
  status: confirmed
  evidence: sonnet-1#67, sonnet-1#68, sonnet-1#69, sonnet-2#25, sonnet-2#26, sonnet-2#27
  note: sonnet-2 tried to do it in one ask (`<> `) and could not (`level-change-more`).

- [reroll-pays] A reroll of a level that looks like a slow cave shortens the search for a down staircase (the player's own bet when it rerolled at ask 67).
  anchor: STAIR-01
  status: contradicted
  evidence: sonnet-1#67, sonnet-1#78

- [reroll-different-level] After `<` then `>` the new depth 1 began with the same kind of corridor at the same spot and looked like the old one, but its layout was different (a door south, a worm north) and it was no quicker to find a staircase in; the player's own correction.
  anchor: STAIR-01
  status: hypothesis
  evidence: sonnet-1#71, sonnet-1#78
  supersedes: reroll-pays

- [dl1-no-stairs-100-asks] Walking two depth-1 levels for about 100 asks found no down staircase, so finding `>` cost far more asks than the shopping or the fights did; in this run that was the whole of the descending problem.
  anchor: goal:descend
  status: confirmed
  evidence: sonnet-1#67, sonnet-1#124, sonnet-2#78, sonnet-2#151
  note: sonnet-2 walked 51 asks on its first depth-1 level (asks 28-78) and 73 on depth 6 (asks 80-152) and found no `>` on either. Across all three runs no screen at depth 1 or deeper shows "Down staircase" on the status line; the only stairs ever taken down were the town's, and the only descent below depth 1 was a scroll (`deep-descent-observed`).

- [magic-mapping-unaffordable] Following TOWN-01's order (escapes, a heal, oil) on 146 gold left 10 gold, and the Alchemist's 65-gold Scroll of Magic Mapping was out of reach; the player judged that a mapping scroll, not more oil, was what the run lacked, which no run has tested.
  anchor: TOWN-01
  status: contradicted
  evidence: sonnet-1#25, sonnet-1#124, sonnet-2#47, sonnet-2#48
  note: the arithmetic is true on seed 7 and the judgment was tested by sonnet-2, which bought Magic Mapping, read it on depth 1, and saw no staircase. See `magic-mapping-no-stairs`; the 146-gold figure is the Warrior's (`start-gold-differs`).

- [magic-mapping-no-stairs] A Scroll of Magic Mapping bought for 65 gold and read on depth 1 showed no staircase of either kind on the part of the map the player looked at (the screen and the sector north of it), so it cost 65 of 146 gold and a quarter of the Warrior's shopping for nothing it could use.
  anchor: TOWN-01
  status: hypothesis
  evidence: sonnet-2#47, sonnet-2#48, sonnet-2#49, sonnet-2#50
  supersedes: magic-mapping-unaffordable
  note: one scroll, one level. The player inspected about 33 columns each side and the rows from 5 north to 15 south on screen, then the sector north; the game maps 40 columns each side and 22 rows each way (GAME DATA, `object.txt` `effect-yx:22:40`), so a strip about seven rows south and seven columns each side was not looked at. It says "no stairs found in what was looked at", not "no stairs in range".

- [stairs-spell-shows-stairs] A Mage's first-level spell Find Traps, Doors and Stairs (`mac`, 1 mana, 14% failure) cast on arrival at depth 1 drew a `>` about 13 columns west and 6 rows south of the arrival staircase and nothing between them, and the corridor the player then ran led north, away from it.
  anchor: new:stair-detection
  status: hypothesis
  evidence: sonnet-3#34, sonnet-3#35, sonnet-3#36
  note: whether a detected `>` is cheaper to reach than blind exploring is not shown, the run died 12 asks later. The spell's box is the same size as Magic Mapping's (22 rows, 40 columns, GAME DATA, `class.txt`), so the two differ in cost (a spell point against 65 gold) and in what they find, not in reach.

- [locate-scrolls-map] `L` (locate) scrolls the map a sector at a time ("Map sector [3,0], which is your sector. Direction?") and is how a mapped area larger than the screen is read; Escape leaves it.
  anchor: new:map-view
  status: hypothesis
  evidence: sonnet-2#48, sonnet-2#49, sonnet-2#50

- [dl6-no-stairs-explored] On depth 6 (arrived by scroll, so on no staircase) 73 asks of exploring found neither kind of staircase, and about 14 of them (asks 126-139) went into a closed cave pocket.
  anchor: STAIR-01
  status: hypothesis
  evidence: sonnet-2#80, sonnet-2#126, sonnet-2#139, sonnet-2#152

### Deep Descent: observed once

- [deep-descent-observed] An unknown scroll picked up on depth 1 and read at once at full health (68 of 68) was Deep Descent: "The air around you starts to swirl...", a "Descent" mark on the status bar, two more asks of walking, "The floor opens beneath you!" and depth 6 (300 ft); the arrival was not on a staircase, and reading it paid 3 experience at character level 4.
  anchor: new:unidentified-objects
  status: hypothesis
  evidence: sonnet-2#76, sonnet-2#77, sonnet-2#78, sonnet-2#79, sonnet-2#80
  note: this is what one scroll supports: it exists on depth 1, it fires after a few turns (game turn 2707 to 2751, about four to five player turns, during which the player picked up gold), it lands on a new level, and the 3 experience (NXT 14 to 11) is what the first-use formula gives for a level-10 kind at character level 4. It does not support a rate, a safe depth, or what "5 below" counts from (below).

- [deep-descent-five-below] From depth 1 the scroll took the character to depth 6, which agrees with "five levels below the deepest level reached" and cannot tell it from "five below the current level" because the two were both 1.
  anchor: new:unidentified-objects
  status: hypothesis
  evidence: sonnet-2#79, sonnet-2#80
  note: the notebook says "confirmed DL1 -> DL6" and the report "5 below max depth"; one read on a level that was also the deepest cannot confirm which. Only the source (`player->max_depth`, first Sheet 5) distinguishes them. Not promoted.

- [deep-descent-paid-in-asks] The one Deep Descent read took the Warrior five levels in four asks (read, two of walking, the fall) and no gold, where about 100 asks (sonnet-1) and 51 asks (sonnet-2, depth 1) of walking had found no `>`; but it was one of four unknown scrolls read across the runs that read any (sonnet-1: Blessing, Light; sonnet-2: Deep Descent, and Blessing on depth 6), so it is one lucky draw and no rate.
  anchor: goal:descend
  status: hypothesis
  evidence: sonnet-1#45, sonnet-1#118, sonnet-2#76, sonnet-2#150
  note: it was found in a cave "east of the big room" of one level of one run. The levels differ run to run with the same seed, so reading unknown scrolls early is a way to buy a draw, not a way to reach depth 6. The inherited Sheet 1 said to read unknowns early; sonnet-2 did and got this, sonnet-3 had no scroll to read.

- [deep-descent-no-stairs-arrival] A Deep Descent arrival is not on a staircase, so there is no `<` under the character to leave by or to reroll with (STAIR-01's "leave by the staircase you arrived on" has nothing to leave by); sonnet-2 had to explore a depth-6 cave pocket on foot.
  anchor: STAIR-01
  status: hypothesis
  evidence: sonnet-2#80, sonnet-2#139
  note: the status bar reads "Open floor" at arrival, and the notebook and report both say it.

- [dl6-at-cl4-survivable] A Half-Troll Warrior arriving on depth 6 at character level 4 with 68 hit points survived 73 asks there (lowest hit points shown on a screen 61 of 68, at ask 88 against a black naga), reached character level 6 with 98, and fought the `p` groups from doorways with oil.
  anchor: DEPTH-01
  status: hypothesis
  evidence: sonnet-2#80, sonnet-2#88, sonnet-2#152
  note: one character, one class with large hit dice, alive at ask 152 and not beyond. It says a Warrior at character level 4 can live on depth 6, not that depth 6 is safe, and nothing about a Mage.

### Moving

- [runs-stop-at-openings] A run (`.` and a direction) stops at every side opening, treasure vein and door, which is what the game's own manual says ("until you have to make a choice"), but in a cave it meant a run per two or three squares.
  anchor: key:.
  status: hypothesis
  evidence: sonnet-1#62, sonnet-1#63, sonnet-1#64, sonnet-1#65, sonnet-1#66

- [digit-strings-beat-runs] In caves and rooms a plain string of eight to ten digit steps such as `4444444444` moved further per ask than `.4`, against the compressed manual's "far cheaper than stepping".
  anchor: key:.
  status: hypothesis
  evidence: sonnet-1#96, sonnet-1#114

- [digit-string-stops-at-wall] A string of digit steps stops at a wall ("There is a wall in the way!") and the rest of it does nothing: sonnet-2's `666666666` on depth 6 moved the character six squares and ended against a wall, so long strings in caves are partly wasted.
  anchor: key:.
  status: hypothesis
  evidence: sonnet-2#82, sonnet-2#83
  note: qualifies `digit-strings-beat-runs` rather than contradicting it; sonnet-2 went on using strings in rooms and corridors (a 16-step string at ask 55 ran in full).

### Unidentified objects

- [unknown-scrolls-harmless] Two unknown scrolls read on depth 1 were harmless, Blessing at ask 45 and Light at ask 118, and each was identified by being read.
  anchor: new:unidentified-objects
  status: hypothesis
  evidence: sonnet-1#45, sonnet-1#118
  note: true of those two. sonnet-2's first unknown scroll on depth 1 was Deep Descent, which hurt nothing but is not "nothing happens" (`deep-descent-observed`).

- [unknown-potion-level] An unknown potion drunk on depth 1 at character level 1 turned out to be Boldness, was identified by drinking it, and took the character to level 2 because the first use of an unknown kind awards experience.
  anchor: new:unidentified-objects
  status: hypothesis
  evidence: sonnet-1#57, sonnet-1#58

- [first-use-xp-shrinks] The experience for identifying by use is small and gets smaller as the character levels: Blessing at character level 1 moved the "NXT" counter from 7 to 6, and Light at level 3 moved it not at all (3 to 3); read off the screens, the notebook only says that it counts.
  anchor: new:unidentified-objects
  status: confirmed
  evidence: sonnet-1#45, sonnet-1#118, sonnet-1#58, sonnet-2#77, sonnet-2#110, sonnet-2#151
  note: sonnet-2's first uses, read off its screens: Deep Descent at character level 4 moved NXT 14 to 11 (3), Cure Serious Wounds at level 5 moved it 31 to 30 (1), Blessing at level 6 moved it not at all (14 to 14). All three agree with the formula in Sheet 1.

- [test-unknowns-when-safe] An unknown potion drunk at full health with nothing in view cost one turn and paid a character level, where ESC-01 saves unknown potions for the last rung of an emergency; testing them early when nothing is hunting you looks cheaper than keeping them as a gamble.
  anchor: ESC-01
  status: hypothesis
  evidence: sonnet-1#57, sonnet-1#58, sonnet-1#45, sonnet-1#118
  note: holds at character level 1 and for scrolls (sonnet-2's early scroll read gave Deep Descent). For potions at higher levels see `unknown-potion-wastes-heal`.

- [unknown-potion-wastes-heal] At character level 5 and full health (89 of 89) an unknown Clear Potion drunk "to test it" was a Cure Serious Wounds: a heal spent for about 1 experience, which the player listed among the decisions it would take back ("worth drinking only when hurt or at CL1-2").
  anchor: ESC-01
  status: hypothesis
  evidence: sonnet-2#109, sonnet-2#110
  note: qualifies `test-unknowns-when-safe`; on depth 6 sonnet-2 also drank two other unknowns at full health (Neutralize Poison, and a Pink Potion that was Heroism), neither of which did any harm.

### The first purchases, the escapes, and a Mage's start

- [escapes-bought-unused] The escapes and heal TOWN-01 buys first (Phase Door and Cure Light Wounds) were still in the pack unused after 119 asks (sonnet-1: 3 Phase Door and 2 Cure Light Wounds) and 150 asks (sonnet-2: 2 Phase Door and a Cure Light Wounds), so TOWN-01's order is untested in both runs that lived.
  anchor: TOWN-01
  status: confirmed
  evidence: sonnet-1#119, sonnet-2#119, sonnet-2#150
  note: not a reason to stop buying them, since neither run was ever in an emergency that the oil did not answer; the one run that was in one (`sonnet-3`) did not use them either (`confused-clw-unused`).

- [start-gold-differs] The starting gold is not the same for every character: 146 for the Half-Troll Warrior on seed 7 (sonnet-1 and sonnet-2), 334 for the Human Mage on seed 11 (sonnet-3), which makes every gold figure in the sheets one character's.
  anchor: TOWN-01
  status: hypothesis
  evidence: sonnet-2#13, sonnet-3#14
  note: whether it is the class, the race or the seed that sets it is not shown; the brief's "Mage about 322" was close.

- [armoury-prices-high] The Armoury on seed 11 priced a Leather Shield [8] at 66 gold, Small Metal Shield at 36 and Studded Leather at 150, with nothing cheap for the body, far above the strategy manual's figures (the player's report: Soft Leather Armour 84, Leather Boots about 34); the Mage spent 66 of 334 gold on the shield and was left with 6.
  anchor: TOWN-01
  status: hypothesis
  evidence: sonnet-3#27, sonnet-3#28
  note: one shopkeeper's markup on one seed; not a rule.

- [mage-study-cast-keys] A new Mage learns a first-level spell with `G`, then the book's letter, then the spell's letter, and casts it with `m`, the book, the spell (`mac` for the third spell of the first book).
  anchor: new:spells
  status: hypothesis
  evidence: sonnet-3#9, sonnet-3#10, sonnet-3#11, sonnet-3#12, sonnet-3#13
  note: the first book's list at level 1 is Magic Missile, Light Room, Find Traps Doors & Stairs (1, 2 and 1 mana), with 2 spell points available.

- [spell-first-cast-xp] The first cast of a spell paid experience, 2 at character level 1 (the NXT counter went from 10 to 8); a second cast of the same spell paid none.
  anchor: new:spells
  status: hypothesis
  evidence: sonnet-3#13, sonnet-3#14, sonnet-3#34

- [mage-one-spell-no-attack] Choosing Find Traps, Doors & Stairs as the one spell a level-1 Mage learned left it with no spell attack (2 spell points, 1 mana a cast, all spent on detection), so thrown oil was its only attack, and the player named that choice among those it would take back.
  anchor: new:spells
  status: hypothesis
  evidence: sonnet-3#11, sonnet-3#12, sonnet-3#34
  note: the Mage's alternatives were visible on the study screen (Magic Missile, 16% failure, 1 mana).

### Looking, hitting, and what is on screen

- [look-returns-own-square] `l` (look) with monsters drawn on the map returned only "You are on an open floor, 0 N, 0 E." in both runs that tried it, so it did not name a `c`, an `a`, a `C` or a `p` that was on screen; the player attacked or threw to find out.
  anchor: new:looking
  status: confirmed
  evidence: sonnet-1#40, sonnet-2#58, sonnet-2#112
  note: both players wrote it in their reports ("could not see": sonnet-1 section 4, sonnet-2 section 4). Why `l` skips them was not found; sonnet-3 proposed the monster list `[` and never tried it.

- [thief-steals-gold] A cutpurse `p` that touched the character stole gold and vanished ("There is a puff of smoke!"): 35 of 126 gold, 126 to 91, between asks 140 and 143.
  anchor: FIGHT-01
  status: hypothesis
  evidence: sonnet-2#140, sonnet-2#143

### Disabled with something near (sonnet-3's death; see "What killed a character")

- [unseen-is-not-dead] A monster that has left view is not dead: after one flask hit a small kobold its health bar went to `[----------]` and it was not on screen, the NXT counter stayed 8 (a small kobold is worth 5 experience at level 1, GAME DATA), and the player walked on as if it were gone; no experience gain means no kill.
  anchor: FIGHT-01
  status: hypothesis
  evidence: sonnet-3#42, sonnet-3#43, sonnet-3#44

- [gas-trap-confusion] Walking into a gas trap on depth 1 confused a 10-hit-point Mage ("You are surrounded by a gas of scintillating colours! You are confused!"), and the confusion was still on after ten more turns.
  anchor: new:traps
  status: hypothesis
  evidence: sonnet-3#45, sonnet-3#47

- [hold-key-is-comma] In this keyset `,` holds a turn (ten `,` moved the game turn from 1182 to 1282), while `s` is not a hold: it asked "Direction or <click>?"; the compressed manual's `5` for staying still was not tried in the run.
  anchor: key:5
  status: hypothesis
  evidence: sonnet-3#46, sonnet-3#47

- [blind-batch-while-disabled] While confused, with a monster that was not known to be dead somewhere near, the player sent ten and then sixteen hold keys in single asks; during the second the kobold arrived and the character died, from full hit points (10 of 10 on the screen at ask 47) to dead inside one ask (game turn 1282 to 1348, about seven player turns of the sixteen).
  anchor: new:key-batches
  status: hypothesis
  evidence: sonnet-3#46, sonnet-3#47
  note: a batch cannot be interrupted by what the screen would have shown. The first batch of ten (ask 46) survived, which is how the second was chosen.

- [confused-clw-unused] The Mage held 5 Potions of Cure Light Wounds and 6 Scrolls of Phase Door when it died; a potion can be drunk while confused and Cure Light Wounds reduces confusion by 20 turns and heals 20 (GAME DATA, `object.txt`: `HEAL_HP 20`, `TIMED_DEC:CONFUSED 20`), but a scroll cannot be read while confused, so only the potion was available, and it was not drunk.
  anchor: ESC-01
  status: hypothesis
  evidence: sonnet-3#38, sonnet-3#47
  note: the pack is on screen at ask 38 (5 Cure Light Wounds, 6 Phase Door). That the potion would have cured the confusion is the source's word, not a trial; sonnet-3's own report marks it "unverified".

- [mage-ten-hp] A level-1 Human Mage has 10 hit points and a small kobold hits for 1d5 (GAME DATA, `monster.txt`), so one kobold's few hits are the whole character; the Warrior's 23 hit points at the same level went to 12 in the dog fight and it lived.
  anchor: FIGHT-01
  status: hypothesis
  evidence: sonnet-3#40, sonnet-3#47
  note: class-specific. The kobold was adjacent in a corridor at ask 40 and the player threw oil point-blank rather than reading Phase Door first, which its report lists among the decisions it would take back.

- [batch-uninterruptible] Nothing in the harness stops a batch once it is sent: the frontend deliberately keeps its key buffer when the game flushes input after a disturbance (`main-agent.c`, `TERM_XTRA_FLUSH`, whose comment says dropping keys "silently would make a key disappear without record"), and there is no limit on the keys in one ask, so a character at 10 hit points could spend sixteen keys with a monster closing and no chance to answer it.
  anchor: new:key-batches
  status: hypothesis
  evidence: sonnet-3#47, sonnet-3#46
  note: **a lead about the harness, not about the player.** The evidence is the run (a batch of sixteen ran to the end, or to death); the mechanism is my reading of the patch, which is not a trial. In a terminal a monster coming into view flushes typed-ahead keys; here the flush is ignored by design. Not every drop is covered: sonnet-2 lost keys after a staircase and sonnet-3 after a `-more-`, so the buffer is not inert, and I did not trace why. A cap, or a stop when hit points fall or a monster appears, is a design decision for the owner (D3 says a string of keys is one round trip on purpose).

## What killed a character

This is the thing the repository exists to produce: one death, read to the end,
with what would have prevented it. One death, so every line is a lead
(`hypothesis`), not a rule.

**The death.** `sonnet-3`, a Human Mage on seed 11, died on depth 1 at character
level 1 with 10 hit points, killed by a small kobold, at game turn 1348, ask 48
(the tombstone; 47 asks were answered).

**How it went**, with the screens that show it:
1. Ask 40: a small kobold is adjacent, north, in a corridor. The player throws
   oil point-blank (asks 41, 42). The first flask hits; the kobold, 8 hit points,
   does not die.
2. Ask 43: the kobold is not on screen, the health bar reads `[----------]` and
   NXT is still 8. The player reads that as "gone" and runs north (asks 43, 44).
   A kobold is worth 5 experience at level 1 (GAME DATA): a kill would have
   moved NXT from 8 to 3. It did not move. (`unseen-is-not-dead`)
3. Ask 45: a gas trap; confused, status bar "Confused ... Gas trap".
   (`gas-trap-confusion`) The player sends ten `s`, which only opens a
   direction prompt.
4. Ask 46: ten `,` holds, to wait the confusion out. They run. HP 10 of 10,
   still confused, no kobold on screen at ask 47. (`hold-key-is-comma`)
5. Ask 47: sixteen `,` in one ask. Between its start (turn 1282) and the
   tombstone (turn 1348) about seven turns pass and the kobold arrives and kills
   a full-health 10-hit-point character; the remaining keys are unread.
   (`blind-batch-while-disabled`)

**What would have prevented it**, in the order it could have been stopped:
- *Do not count the kill until the screen says so* (ask 43). "Slain" in the
  message line, or NXT moving, is a kill; a blank or dashed health bar is
  "not in view". A wounded monster in a corridor that left view is near, and the
  corridor mouth was the place to wait with a flask ready, which is what the
  player's own report says it should have done. (`unseen-is-not-dead`,
  FIGHT-01)
- *Do not spend a batch while disabled* (ask 46, 47). One or two keys per ask
  while confused, blind or otherwise unable to answer, so that the next screen
  can show what changed. The manual says to send several keys at once as "the
  whole economy"; it never says when not to. (`blind-batch-while-disabled`,
  Sheet 6)
- *Use what was in the pack* (ask 46, 47). Five Potions of Cure Light Wounds,
  which can be drunk while confused and, by the game data, shorten confusion
  and heal 20 hit points; Phase Door cannot be read while confused, so the
  potion was the only escape left in the pack. ESC-01's ladder is written for
  staircases, Phase Door and Teleport, and has no rung for "disabled with
  something coming". (`confused-clw-unused`, ESC-01) *Untested: no run has
  drunk one while confused.*
- *Do not melee-range a 10-hit-point character's opening* (ask 40). With 10 hit
  points two or three kobold hits are the whole character; Phase Door and then oil
  from range was the player's own correction. (`mage-ten-hp`)
- *Know one's spells* (ask 11). With Magic Missile instead of Find Stairs the
  Mage would have had a second attack; with Find Stairs it had a map and no way
  to reach the `>` it showed. (`mage-one-spell-no-attack`, `stairs-spell-shows-stairs`)

**What is a lead about this harness, not about the player.** A character with
10 hit points should not be able to spend sixteen keys blind in one ask. Three
separate things stack here, and only one of them was the player's:
1. the player chose a long batch (player);
2. the frontend does not stop a batch when the game flushes input after a
   disturbance. `patch/src/main-agent.c` ignores `TERM_XTRA_FLUSH` on purpose,
   on the ground that a dropped key would vanish unrecorded; in a terminal a
   monster coming into view cancels typed-ahead keys, here it cannot
   (harness; `batch-uninterruptible`);
3. the brief tells the player to "send several keys at once" with no limit and no
   warning about when not to (manual, and `docs/BRIEF.md`).
Candidate changes, none tried: cap the keys per ask by the character's hit
points; or stop the batch, and record the unread remainder, when hit points fall
or a monster appears (that keeps D3's "no key disappears without record" while
letting the screen interrupt); or say it in the manual (Sheet 6). Whether this
was **the** cause cannot be shown from one death: the player's wrong belief that
the kobold was gone (step 2) put it in that position, and a 23-hit-point Warrior
could have survived the same batch. `takeover --at-turn 1012` and a replay with
`[` or a single `,` per ask is the test `sonnet-3` proposed.

**What the other two runs say about deaths.** Neither died, so they have none.
The nearest calls were `sonnet-2`'s 12 of 23 hit points against the dog pack
(ask 65) and 61 of 68 against a black naga on depth 6 (ask 88); neither involved
being unable to act.

## Count

55 items: 19 carried over from the first consolidation (ids and sentences
unchanged) and 36 new. By status: **17 `confirmed`, 3 `contradicted`, 35
`hypothesis`**.

- `confirmed` (two or more different runs): `store-purchase-sequence`,
  `purchase-in-one-ask`, `more-swallows-next-key`, `space-clears-more`,
  `level-change-more`, `store-letters-fixed`, `pack-letters-skip`,
  `throw-menu-own-letters`, `bought-items-named`, `selling-pays-nothing`,
  `throw-closest-target`, `arrival-staircase`, `reroll-costs-three-asks`,
  `dl1-no-stairs-100-asks`, `first-use-xp-shrinks`, `escapes-bought-unused`,
  `look-returns-own-square`. Of the 17, 7 are promotions of a first-version
  item (`store-letters-fixed`, `pack-letters-skip`, `throw-closest-target`,
  `arrival-staircase`, `reroll-costs-three-asks`, `dl1-no-stairs-100-asks`,
  `first-use-xp-shrinks`) and 10 are new items. In 7 of the 17 at least one run's side is
  read off its screens or its report rather than written in its notebook
  (`store-letters-fixed`, `pack-letters-skip`, `bought-items-named`,
  `selling-pays-nothing`, `escapes-bought-unused`, `look-returns-own-square`,
  `first-use-xp-shrinks`); the screens were read, not inferred, and the `note:`
  says which. A stricter reader may want those seven to wait for a second
  note.
- `contradicted`: `reroll-pays` (by the player's own correction, as before),
  `store-purchase-prompts` (by sonnet-2 and sonnet-3: one purchase per ask is
  not needed) and `magic-mapping-unaffordable` (by sonnet-2: the Magic Mapping
  it judged missing was bought and showed no stairs).
- Still `hypothesis` after three runs, on one run's word: everything about
  Deep Descent (`deep-descent-*`), the Mage's spells and death, the DL6 notes,
  Fang and the dog pack, `enter-opens-menu`, `rethrow-target-5`, the walking
  items.

Anchors: 14 on command keys (`p` 3, `<` 3, `.` 3, `v` 2, `5` 2, `s` 1), 19 on strategy rules
(TOWN-01 5, FIGHT-01 4, STAIR-01 4, ESC-01 3, OIL-01 2, DEPTH-01 1), 2 on a goal
(`goal:descend`), 0 on state fields, 20 `new:` (`unidentified-objects` 6,
`dismissing-more` 3, `spells` 3, `item-letters` 2, `key-batches` 2,
`stair-detection`, `map-view`, `looking`, `traps` 1 each).
