# LEARNED: knowledge filed against the manual

One run so far (`sonnet-1`, seed 7, 125 asks, Half-Troll Warrior, depth 1,
character level 3), so **every item is a `hypothesis`**. Nothing is
`confirmed`: that needs a second run, and reading the source or the manual is
not a run. The notebook is the evidence; this file is the filing.

What the manual should have said, as text to paste, is in
[MANUAL-GAPS.md](MANUAL-GAPS.md). Every `new:` anchor below reappears there.

## Files read to produce this

Read in full:
- `docs/CONSOLIDATE.md` (the instructions)
- `knowledge/sonnet-1.md` (the only notebook; not edited)
- `manuals/jev-1.md` (the compressed manual the anchors come from)
- `src/borg_runner/consolidate.py` (what `check()` enforces)
- `runs/sonnet-1/REPORT.md` and `runs/sonnet-1/record.json`
- `runs/sonnet-1/decisions.jsonl` (what was sent at each ask, and why)
- the sonnet-1 screens at asks 21, 24, 25, 29, 40, 41-46, 56-58, 67, 69, 71,
  78, 80, 81, 83-87, 90, 101-105, 116-119 and 124, and the keys files `keys-16/20/21/44/57/101-104/117.txt`
  (a screen at ask N is what the player saw *before* sending keys N)

Read in part (searched for the topic, not read through):
- `vendor/angband/docs/command.rst`, `playing.rst`, `dungeon.rst`, `option.rst`
  (run, stairs, autoexplore, throw, targeting, flavors, selling and
  identification, `autoexplore_commands`, `birth_connect_stairs`);
  `docs/DESIGN.md` (the autoexplore line only); `guide.rst`, `attack.rst` and `birth.rst` were only searched for "identify",
  "flavor" and "unknown" and had nothing on it
- `vendor/strategy-manual`, `docs/c-manual/README.md` and chapters 6, 7, 10 and
  11 (identification, consumables, exploration, town), by search
- game data and source at the pin, for the numbers in MANUAL-GAPS:
  `lib/gamedata/object.txt` (every potion and scroll: level, allocation depth,
  cost, effect), `lib/gamedata/store.txt` (Alchemist stock),
  `lib/gamedata/monster.txt` (Fang), `src/obj-knowledge.c`
  (`object_learn_on_use`), `src/cmd-obj.c` (when it is called), `src/store.c`
  (what buying teaches), `src/ui-store.c` and `src/ui-menu.c` (menu letters),
  `src/effect-handler-general.c` (Deep Descent)

Not read: any run other than `sonnet-1`. The `jev-*`, `smoke*` and `auto1` runs
have records but no notebook, so they are not evidence for anything here.

Where the game's own manual already says something and the player learned it
the hard way, the statement says so.

## Items

### The shop and the menus

- [store-purchase-prompts] In a store, `p` then the item's letter, then the quantity digits and Enter, then any key at "[ESC, any other key to accept]" buys it, and keys chained after the first completed purchase were swallowed, so send one purchase per ask (the compressed manual says only "p = buy").
  anchor: key:p
  status: hypothesis
  evidence: sonnet-1#16, sonnet-1#21, sonnet-1#24, sonnet-1#25

- [store-letters-fixed] A store's rows are not lettered a, b, c: the run's Alchemist read a, c, f, h, j, m, n, o, q, r, u, v, y, z, so the letter has to be read off the screen and never counted.
  anchor: new:item-letters
  status: hypothesis
  evidence: sonnet-1#25

- [pack-letters-skip] Pack letters skip too: with eight items the list read a to g and then i, so `q`, `r`, `v` and `w` must be given the letter shown on the item list, not its position.
  anchor: new:item-letters
  status: hypothesis
  evidence: sonnet-1#57

- [enter-opens-menu] Enter in the dungeon, with no `-more-` waiting, opens a command menu rather than clearing anything, so a `-more-` is dismissed with space or Escape (the compressed manual's "any key clears it" holds only while a `-more-` is actually on screen).
  anchor: new:dismissing-more
  status: hypothesis
  evidence: sonnet-1#103, sonnet-1#104

### Throwing

- [throw-closest-target] `v`, the item's letter, then `'` throws at the nearest visible monster; the game's own manual (playing.rst, "Targeting") says exactly this and the compressed manual's "then a target" leaves the key out, so the player had to read it off the prompt.
  anchor: key:v
  status: hypothesis
  evidence: sonnet-1#83

- [rethrow-target-5] After one throw has set a target, the direction prompt offers `5`, so `v`, the item letter, `5` throws at the same monster again; the compressed manual's line for `5` ("confirm the current target") already covers this and the player found it only when the prompt said so.
  anchor: key:5
  status: hypothesis
  evidence: sonnet-1#104

- [fang-corridor-oil] Fang, Farmer Maggot's Dog, killed at character level 2 in a corridor with two thrown flasks of oil and then melee, cost about 11 of 31 HP and took the character from level 2 to 3.
  anchor: OIL-01
  status: hypothesis
  evidence: sonnet-1#84, sonnet-1#90

### Stairs, and the cost of finding one

- [arrival-staircase] After going down you stand on an up staircase, and after going up from depth 1 you stand in the town on its down staircase; the compressed manual already says the first of these, and the second is what makes the reroll below possible.
  anchor: key:<
  status: hypothesis
  evidence: sonnet-1#29, sonnet-1#69

- [reroll-costs-three-asks] Taking `<` from depth 1 and then `>` in the town gives a fresh depth 1 for three asks (arrive in town, press `>`, dismiss the `-more-`).
  anchor: key:<
  status: hypothesis
  evidence: sonnet-1#67, sonnet-1#68, sonnet-1#69

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
  status: hypothesis
  evidence: sonnet-1#67, sonnet-1#124

- [magic-mapping-unaffordable] Following TOWN-01's order (escapes, a heal, oil) on 146 gold left 10 gold, and the Alchemist's 65-gold Scroll of Magic Mapping was out of reach; the player judged that a mapping scroll, not more oil, was what the run lacked, which no run has tested.
  anchor: TOWN-01
  status: hypothesis
  evidence: sonnet-1#25, sonnet-1#124

### Moving

- [runs-stop-at-openings] A run (`.` and a direction) stops at every side opening, treasure vein and door, which is what the game's own manual says ("until you have to make a choice"), but in a cave it meant a run per two or three squares.
  anchor: key:.
  status: hypothesis
  evidence: sonnet-1#62, sonnet-1#63, sonnet-1#64, sonnet-1#65, sonnet-1#66

- [digit-strings-beat-runs] In caves and rooms a plain string of eight to ten digit steps such as `4444444444` moved further per ask than `.4`, against the compressed manual's "far cheaper than stepping".
  anchor: key:.
  status: hypothesis
  evidence: sonnet-1#96, sonnet-1#114

### Unidentified objects

- [unknown-scrolls-harmless] Two unknown scrolls read on depth 1 were harmless, Blessing at ask 45 and Light at ask 118, and each was identified by being read.
  anchor: new:unidentified-objects
  status: hypothesis
  evidence: sonnet-1#45, sonnet-1#118

- [unknown-potion-level] An unknown potion drunk on depth 1 at character level 1 turned out to be Boldness, was identified by drinking it, and took the character to level 2 because the first use of an unknown kind awards experience.
  anchor: new:unidentified-objects
  status: hypothesis
  evidence: sonnet-1#57, sonnet-1#58

- [first-use-xp-shrinks] The experience for identifying by use is small and gets smaller as the character levels: Blessing at character level 1 moved the "NXT" counter from 7 to 6, and Light at level 3 moved it not at all (3 to 3); read off the screens, the notebook only says that it counts.
  anchor: new:unidentified-objects
  status: hypothesis
  evidence: sonnet-1#45, sonnet-1#118, sonnet-1#58

- [test-unknowns-when-safe] An unknown potion drunk at full health with nothing in view cost one turn and paid a character level, where ESC-01 saves unknown potions for the last rung of an emergency; testing them early when nothing is hunting you looks cheaper than keeping them as a gamble.
  anchor: ESC-01
  status: hypothesis
  evidence: sonnet-1#57, sonnet-1#58, sonnet-1#45, sonnet-1#118

## Count

19 items: 18 `hypothesis`, 1 `contradicted` (`reroll-pays`, by the player's own
later correction, which `reroll-different-level` supersedes), 0 `confirmed`.
Anchors: 7 on command keys (`p`, `v`, `5`, `<` twice, `.` twice), 5 on strategy
rules (OIL-01, STAIR-01 twice, ESC-01, TOWN-01), 1 on a goal (`goal:descend`),
0 on state fields, 6 `new:` (`item-letters` 2, `dismissing-more` 1,
`unidentified-objects` 3).
